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

def get_metadata(file_path, base_dir):
    rel_path = os.path.relpath(file_path, base_dir)
    parts = rel_path.split(os.sep)
    folders = parts[:-1]
    filename = parts[-1]
    return {
        "folders": "/".join(folders),  # Convert list to string
        "filename": filename,
        "rel_path": rel_path
    }

def find_mo_files(samples_dir):
    mo_files = []
    for root, _, files in os.walk(samples_dir):
        for file in files:
            if file.endswith(".mo"):
                mo_files.append(os.path.join(root, file))
    return mo_files

def main():
    chroma_dir = os.path.join(os.getcwd(), "chromadb_data")
    chroma_client = chromadb.PersistentClient(path=chroma_dir)
    collection = chroma_client.get_or_create_collection("motoko_code_samples")

    # Find all .mo files first
    mo_files = find_mo_files(SAMPLES_DIR)
    print(f"Found {len(mo_files)} .mo files.")

    docs, embeddings, metadatas, ids = [], [], [], []
    i = 0
    # Use tqdm for progress bar
    for file_path in tqdm(mo_files, desc="Processing .mo files", unit="file"):
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        meta = get_metadata(file_path, SAMPLES_DIR)
        emb = get_embedding(code)
        docs.append(code)
        embeddings.append(emb)
        metadatas.append(meta)
        ids.append(f"motoko_sample_{i}")
        print(f"Metadata for embedding {i}: {meta}")
        i += 1

    print(f"Storing {len(docs)} Motoko code samples in ChromaDB...")
    collection.add(
        documents=docs,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )
    print("Done!")

if __name__ == "__main__":
    main()