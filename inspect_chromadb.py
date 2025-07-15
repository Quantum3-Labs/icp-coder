import chromadb
from chromadb.config import Settings
import os

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chromadb_data")

def get_dir_size_mb(path):
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total += os.path.getsize(fp)
    return total / (1024 * 1024)

def main():
    print(f"Connecting to ChromaDB at: {CHROMA_DIR}")
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collections = client.list_collections()
    print(f"Found {len(collections)} collections: {[c.name for c in collections]}")
    print("-" * 40)
    for col in collections:
        collection = client.get_collection(col.name)
        count = collection.count()
        print(f"Collection: {col.name}")
        print(f"  Number of documents: {count}")
        if count > 0:
            # Get a sample of 1
            results = collection.get(limit=1)
            print(f"  Example document: {results['documents'][0][:200]}...")  # Print first 200 chars
            print(f"  Example metadata: {results['metadatas'][0]}")
            print(f"  Example id: {results['ids'][0]}")
        print("-" * 40)
    size_mb = get_dir_size_mb(CHROMA_DIR)
    print(f"ChromaDB directory size: {size_mb:.2f} MB")

if __name__ == "__main__":
    main()