import os
import re
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from tqdm import tqdm

# Directory containing documentation files
DOCS_DIR = "motoko_official_docs"

# Load the local embedding model once
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text: str) -> list:
    """Generate embedding for given text."""
    return model.encode(text).tolist()

def extract_frontmatter(content: str) -> Tuple[Dict, str]:
    """Extract YAML frontmatter and return metadata and content."""
    frontmatter = {}
    if content.startswith('---'):
        try:
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter_text = parts[1].strip()
                content = parts[2].strip()
                # Simple YAML parsing for common fields
                for line in frontmatter_text.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        if key == 'sidebar_position':
                            try:
                                frontmatter[key] = int(value)
                            except:
                                frontmatter[key] = value
                        else:
                            frontmatter[key] = value
        except:
            pass
    return frontmatter, content

def parse_headers(content: str) -> List[Dict]:
    """Parse markdown headers and return hierarchy information."""
    headers = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if line.strip().startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            if level <= 4:  # Only consider up to h4
                title = line.strip('#').strip()
                headers.append({
                    'level': level,
                    'title': title,
                    'line_number': i
                })
    return headers

def get_parent_context(headers: List[Dict], current_index: int) -> str:
    """Get parent section titles for context."""
    if current_index == 0:
        return ""
    
    current_level = headers[current_index]['level']
    parents = []
    
    # Look backwards for parent headers
    for i in range(current_index - 1, -1, -1):
        if headers[i]['level'] < current_level:
            parents.insert(0, headers[i]['title'])
            current_level = headers[i]['level']
            if current_level == 1:  # Stop at h1
                break
    
    return " > ".join(parents) if parents else ""

def chunk_content(content: str, headers: List[Dict], file_path: str, frontmatter: Dict) -> List[Dict]:
    """Chunk content based on headers while preserving context."""
    chunks = []
    lines = content.split('\n')
    
    if not headers:
        # No headers found, treat as single chunk
        chunk_content = content.strip()
        if chunk_content:
            chunks.append({
                'content': chunk_content,
                'title': os.path.basename(file_path),
                'parent_context': '',
                'section_type': 'document',
                'headers': []
            })
        return chunks
    
    for i, header in enumerate(headers):
        start_line = header['line_number']
        
        # Find end line (next header of same or higher level)
        end_line = len(lines)
        for j in range(i + 1, len(headers)):
            if headers[j]['level'] <= header['level']:
                end_line = headers[j]['line_number']
                break
        
        # Extract section content
        section_lines = lines[start_line:end_line]
        section_content = '\n'.join(section_lines).strip()
        
        if not section_content or len(section_content) < 50:
            continue
        
        # Get parent context
        parent_context = get_parent_context(headers, i)
        
        # Determine section type based on content
        section_type = classify_section(section_content)
        
        # Split large sections if needed
        if len(section_content) > 2000:  # Roughly 400-500 tokens
            sub_chunks = split_large_section(section_content, header['title'], parent_context, section_type)
            chunks.extend(sub_chunks)
        else:
            chunks.append({
                'content': section_content,
                'title': header['title'],
                'parent_context': parent_context,
                'section_type': section_type,
                'headers': [h['title'] for h in headers[max(0, i-2):i+3]]  # Context headers
            })
    
    return chunks

def classify_section(content: str) -> str:
    """Classify section type based on content patterns."""
    content_lower = content.lower()
    
    if '```motoko' in content or 'func ' in content:
        return 'api_reference'
    elif 'example' in content_lower or 'tutorial' in content_lower:
        return 'tutorial'
    elif 'install' in content_lower or 'setup' in content_lower:
        return 'setup'
    elif 'error' in content_lower or 'warning' in content_lower:
        return 'troubleshooting'
    elif re.search(r'function\s+`\w+`', content):
        return 'api_reference'
    else:
        return 'documentation'

def split_large_section(content: str, title: str, parent_context: str, section_type: str) -> List[Dict]:
    """Split large sections into smaller chunks while preserving meaning."""
    chunks = []
    
    # Try to split on subheadings first
    subsection_pattern = r'\n(#{3,6}[^\n]+)\n'
    parts = re.split(subsection_pattern, content)
    
    if len(parts) > 1:
        # Has subsections
        current_chunk = parts[0]  # Content before first subsection
        
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                subsection_title = parts[i].strip('#').strip()
                subsection_content = parts[i + 1]
                
                chunk_content = f"{parts[i]}\n{subsection_content}"
                if len(current_chunk.strip()) > 0:
                    chunk_content = current_chunk + "\n" + chunk_content
                
                if len(chunk_content) > 2500:  # Still too large
                    # Split by paragraphs
                    para_chunks = split_by_paragraphs(chunk_content, f"{title} - {subsection_title}", parent_context, section_type)
                    chunks.extend(para_chunks)
                else:
                    chunks.append({
                        'content': chunk_content.strip(),
                        'title': f"{title} - {subsection_title}",
                        'parent_context': parent_context,
                        'section_type': section_type,
                        'headers': []
                    })
                current_chunk = ""
    else:
        # No subsections, split by paragraphs
        chunks = split_by_paragraphs(content, title, parent_context, section_type)
    
    return chunks

def split_by_paragraphs(content: str, title: str, parent_context: str, section_type: str) -> List[Dict]:
    """Split content by paragraphs when no other structure is available."""
    chunks = []
    paragraphs = content.split('\n\n')
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # Check if adding this paragraph would exceed limit
        if len(current_chunk + para) > 1500 and current_chunk:
            chunks.append({
                'content': current_chunk.strip(),
                'title': title,
                'parent_context': parent_context,
                'section_type': section_type,
                'headers': []
            })
            current_chunk = para
        else:
            current_chunk += ("\n\n" if current_chunk else "") + para
    
    # Add remaining content
    if current_chunk.strip():
        chunks.append({
            'content': current_chunk.strip(),
            'title': title,
            'parent_context': parent_context,
            'section_type': section_type,
            'headers': []
        })
    
    return chunks

def get_file_metadata(file_path: str, base_dir: str, frontmatter: Dict) -> Dict:
    """Extract metadata from file path and frontmatter."""
    rel_path = os.path.relpath(file_path, base_dir)
    parts = rel_path.split(os.sep)
    
    metadata = {
        "source_file": rel_path,
        "filename": os.path.basename(file_path),
        "directory": "/".join(parts[:-1]) if len(parts) > 1 else "",
        "file_type": "documentation",
        "content_type": "motoko_docs"
    }
    
    # Add frontmatter data
    metadata.update(frontmatter)
    
    # Infer document category from path
    if "base/" in rel_path:
        metadata["doc_category"] = "base_library"
    elif "fundamentals/" in rel_path:
        metadata["doc_category"] = "fundamentals"
    elif "examples/" in rel_path:
        metadata["doc_category"] = "examples"
    elif "reference/" in rel_path:
        metadata["doc_category"] = "reference"
    elif rel_path.endswith("language-manual.md"):
        metadata["doc_category"] = "language_reference"
    else:
        metadata["doc_category"] = "general"
    
    return metadata

def find_doc_files(docs_dir: str) -> List[str]:
    """Find all markdown documentation files."""
    doc_files = []
    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.endswith(('.md', '.mdx')):
                file_path = os.path.join(root, file)
                doc_files.append(file_path)
    return doc_files

def main():
    """Main ingestion function."""
    chroma_dir = os.path.join(os.getcwd(), "chromadb_data")
    chroma_client = chromadb.PersistentClient(path=chroma_dir)
    
    # Create or get collection for documentation
    collection = chroma_client.get_or_create_collection("motoko_docs")
    
    # Find all documentation files
    doc_files = find_doc_files(DOCS_DIR)
    print(f"Found {len(doc_files)} documentation files.")
    
    docs, embeddings, metadatas, ids = [], [], [], []
    chunk_id = 0
    
    # Process each documentation file
    for file_path in tqdm(doc_files, desc="Processing documentation files", unit="file"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_content = f.read()
            
            if not raw_content.strip():
                continue
            
            # Extract frontmatter and content
            frontmatter, content = extract_frontmatter(raw_content)
            
            # Parse headers
            headers = parse_headers(content)
            
            # Get file metadata
            file_metadata = get_file_metadata(file_path, DOCS_DIR, frontmatter)
            
            # Chunk the content
            chunks = chunk_content(content, headers, file_path, frontmatter)
            
            # Process each chunk
            for chunk in chunks:
                chunk_text = chunk['content']
                if len(chunk_text.strip()) < 50:  # Skip very small chunks
                    continue
                
                # Create comprehensive metadata
                metadata = file_metadata.copy()
                metadata.update({
                    'chunk_title': chunk['title'],
                    'parent_context': chunk['parent_context'],
                    'section_type': chunk['section_type'],
                    'chunk_size': len(chunk_text),
                    'context_headers': ", ".join(chunk['headers']) if chunk['headers'] else ""
                })
                
                # Ensure all metadata values are valid types for ChromaDB
                for key, value in metadata.items():
                    if isinstance(value, list):
                        metadata[key] = ", ".join(str(v) for v in value)
                    elif not isinstance(value, (str, int, float, bool)) or value is None:
                        metadata[key] = str(value) if value is not None else ""
                
                # Generate embedding
                embedding = get_embedding(chunk_text)
                
                # Store
                docs.append(chunk_text)
                embeddings.append(embedding)
                metadatas.append(metadata)
                ids.append(f"motoko_docs_{chunk_id}")
                
                print(f"Processed chunk {chunk_id}: {chunk['title'][:60]}...")
                chunk_id += 1
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue
    
    # Store in ChromaDB
    if docs:
        print(f"Storing {len(docs)} documentation chunks in ChromaDB...")
        collection.add(
            documents=docs,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        print("Documentation ingestion completed!")
    else:
        print("No documentation chunks to store.")

if __name__ == "__main__":
    main()