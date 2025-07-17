import os
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from tqdm import tqdm  # Add tqdm for progress bar

# Directory containing .mo files
SAMPLES_DIR = "motoko_code_samples"

# Load the local embedding model once
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text: str) -> list:
    return model.encode(text).tolist()

def get_metadata(file_path, base_dir, has_toml=False):
    rel_path = os.path.relpath(file_path, base_dir)
    parts = rel_path.split(os.sep)
    folders = parts[:-1]
    filename = parts[-1]
    metadata = {
        "folders": "/".join(folders),  # Convert list to string
        "filename": filename,
        "rel_path": rel_path,
        "file_type": "motoko" if filename.endswith(".mo") else "toml"
    }
    
    # Add .toml indicator if a .toml file is present in the project
    if has_toml:
        metadata["has_toml"] = True
    else:
        metadata["has_toml"] = False
        
    return metadata

def find_project_files(samples_dir):
    """Find all .mo and .toml files in the samples directory."""
    mo_files = []
    toml_files = []
    project_toml_map = {}  # Map project directories to their .toml files
    
    for root, _, files in os.walk(samples_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith(".mo"):
                mo_files.append(file_path)
            elif file.endswith(".toml"):
                toml_files.append(file_path)
                # Store the project directory (parent of the .toml file)
                project_dir = os.path.dirname(file_path)
                project_toml_map[project_dir] = file_path
    
    return mo_files, toml_files, project_toml_map

def main():
    chroma_dir = os.path.join(os.getcwd(), "chromadb_data")
    chroma_client = chromadb.PersistentClient(path=chroma_dir)
    collection = chroma_client.get_or_create_collection("motoko_code_samples")

    # Find all .mo and .toml files
    mo_files, toml_files, project_toml_map = find_project_files(SAMPLES_DIR)
    print(f"Found {len(mo_files)} .mo files and {len(toml_files)} .toml files.")

    docs, embeddings, metadatas, ids = [], [], [], []
    i = 0
    
    # Process .mo files first
    print("Processing .mo files...")
    for file_path in tqdm(mo_files, desc="Processing .mo files", unit="file"):
        # Check if this .mo file's project has a .toml file
        project_dir = os.path.dirname(file_path)
        has_toml = project_dir in project_toml_map
        
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        meta = get_metadata(file_path, SAMPLES_DIR, has_toml)
        emb = get_embedding(code)
        docs.append(code)
        embeddings.append(emb)
        metadatas.append(meta)
        ids.append(f"motoko_sample_{i}")
        print(f"Metadata for embedding {i}: {meta}")
        i += 1
    
    # Process .toml files
    print("Processing .toml files...")
    for file_path in tqdm(toml_files, desc="Processing .toml files", unit="file"):
        with open(file_path, "r", encoding="utf-8") as f:
            toml_content = f.read()
        meta = get_metadata(file_path, SAMPLES_DIR, has_toml=True)
        emb = get_embedding(toml_content)
        docs.append(toml_content)
        embeddings.append(emb)
        metadatas.append(meta)
        ids.append(f"toml_sample_{i}")
        print(f"Metadata for embedding {i}: {meta}")
        i += 1

    print(f"Storing {len(docs)} total files (Motoko + TOML) in ChromaDB...")
    collection.add(
        documents=docs,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )
    print("Done!")

if __name__ == "__main__":
    main()