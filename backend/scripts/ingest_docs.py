#!/usr/bin/env python3
"""
Enhanced Documentation Ingestion Script for Go Backend

This script combines sophisticated chunking from the original with JSON progress reporting.
Outputs newline-delimited JSON progress messages to stdout.
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple

# Disable ChromaDB telemetry to avoid version compatibility issues
os.environ["ANONYMIZED_TELEMETRY"] = "False"

try:
    from sentence_transformers import SentenceTransformer
    import chromadb
except ImportError as e:
    error_msg = {"type": "error", "message": f"Missing packages: {str(e)}"}
    print(json.dumps(error_msg), file=sys.stderr)
    sys.exit(1)


# Get paths
BACKEND_DIR = Path(__file__).parent.parent
DOCS_DIR = BACKEND_DIR / "data" / "motoko_official_docs"


def get_chromadb_path():
    """Get ChromaDB path from environment or use backend default"""
    chromadb_path = os.getenv("CHROMADB_PATH")
    if chromadb_path:
        return chromadb_path
    return str(Path(__file__).parent.parent / "data" / "chromadb")


def get_embedding(model, text: str) -> list:
    """Generate embedding for text"""
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


def get_file_metadata(file_path: str, base_dir: Path, frontmatter: Dict) -> Dict:
    """Extract metadata from file path and frontmatter."""
    rel_path = os.path.relpath(file_path, base_dir)
    parts = Path(rel_path).parts

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


def find_doc_files(docs_dir: Path) -> List[str]:
    """Find all markdown documentation files."""
    doc_files = []
    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.endswith(('.md', '.mdx')):
                file_path = os.path.join(root, file)
                doc_files.append(file_path)
    return doc_files


def ingest_docs():
    """Main ingestion function with progress reporting"""
    # Check if docs directory exists
    if not DOCS_DIR.exists():
        print(json.dumps({
            "type": "error",
            "message": f"Documentation directory not found: {DOCS_DIR}"
        }), file=sys.stderr)
        sys.exit(1)

    # Initialize ChromaDB
    chromadb_path = get_chromadb_path()
    os.makedirs(chromadb_path, exist_ok=True)

    try:
        chroma_client = chromadb.PersistentClient(path=chromadb_path)
        collection = chroma_client.get_or_create_collection("motoko_docs")
    except Exception as e:
        print(json.dumps({
            "type": "error",
            "message": f"Failed to initialize ChromaDB: {str(e)}"
        }), file=sys.stderr)
        sys.exit(1)

    # Load embedding model
    print(json.dumps({"type": "info", "message": "Loading embedding model..."}), flush=True)
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Find documentation files
    doc_files = find_doc_files(DOCS_DIR)

    if not doc_files:
        print(json.dumps({
            "type": "error",
            "message": "No documentation files found"
        }), file=sys.stderr)
        sys.exit(1)

    # Report start
    print(json.dumps({"type": "start", "total": len(doc_files)}), flush=True)

    docs, embeddings, metadatas, ids = [], [], [], []
    chunk_id = 0

    # Process each file
    for i, file_path in enumerate(doc_files, 1):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_content = f.read()

            if not raw_content.strip():
                continue

            # Extract frontmatter
            frontmatter, content = extract_frontmatter(raw_content)

            # Parse headers
            headers = parse_headers(content)

            # Get file metadata
            file_metadata = get_file_metadata(file_path, DOCS_DIR, frontmatter)

            # Chunk content with sophisticated logic
            chunks = chunk_content(content, headers, file_path, frontmatter)

            # Process chunks
            for chunk in chunks:
                if len(chunk['content'].strip()) < 50:
                    continue

                # Create comprehensive metadata
                metadata = file_metadata.copy()
                metadata.update({
                    'chunk_title': chunk['title'],
                    'parent_context': chunk['parent_context'],
                    'section_type': chunk['section_type'],
                    'chunk_size': len(chunk['content']),
                    'context_headers': ", ".join(chunk['headers']) if chunk['headers'] else ""
                })

                # Ensure valid types
                for key, value in metadata.items():
                    if isinstance(value, list):
                        metadata[key] = ", ".join(str(v) for v in value)
                    elif not isinstance(value, (str, int, float, bool)) or value is None:
                        metadata[key] = str(value) if value is not None else ""

                embedding = get_embedding(model, chunk['content'])

                docs.append(chunk['content'])
                embeddings.append(embedding)
                metadatas.append(metadata)
                ids.append(f"motoko_docs_{chunk_id}")
                chunk_id += 1

            # Report progress every 5 files
            if i % 5 == 0 or i == 1:
                print(json.dumps({
                    "type": "progress",
                    "current": i,
                    "total": len(doc_files),
                    "message": f"Processing {os.path.basename(file_path)} ({len(chunks)} chunks)"
                }), flush=True)

        except Exception as e:
            print(json.dumps({
                "type": "warning",
                "message": f"Error processing {file_path}: {str(e)}"
            }), flush=True)

    # Store in ChromaDB
    if docs:
        print(json.dumps({
            "type": "info",
            "message": f"Storing {len(docs)} chunks in ChromaDB..."
        }), flush=True)

        try:
            collection.add(
                documents=docs,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
        except Exception as e:
            print(json.dumps({
                "type": "error",
                "message": f"Failed to store in ChromaDB: {str(e)}"
            }), file=sys.stderr)
            sys.exit(1)

    # Report completion
    print(json.dumps({
        "type": "complete",
        "total_processed": len(docs),
        "files_processed": len(doc_files)
    }), flush=True)


if __name__ == "__main__":
    try:
        ingest_docs()
    except Exception as e:
        print(json.dumps({"type": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)
