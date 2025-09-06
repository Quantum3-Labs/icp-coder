import os
import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ChromaDB setup
CHROMA_DIR = os.path.join(os.getcwd(), "chromadb_data")
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)

# Get docs collection only
try:
    docs_collection = chroma_client.get_collection("motoko_docs")
except:
    docs_collection = None

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text: str) -> list:
    return model.encode(text).tolist()

def retrieve_from_collection(collection, query, n_results=5):
    """Retrieve results from a specific collection."""
    if not collection:
        return [], [], []
    
    try:
        query_embedding = get_embedding(query)
        results = collection.query(
            query_embeddings=[query_embedding], 
            n_results=n_results
        )
        docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        return docs, metadatas, distances
    except Exception as e:
        print(f"Error querying collection: {e}")
        return [], [], []

def retrieve_docs(query, docs_results=8):
    """Retrieve from documentation collection."""
    print(f"\nQuery: '{query}'")
    print("=" * 80)
    
    # Retrieve from documentation
    doc_docs, doc_metas, doc_distances = retrieve_from_collection(docs_collection, query, docs_results)
    
    # Combine results and sort by similarity score (high to low)
    results = list(zip(doc_docs, doc_metas, doc_distances))
    results.sort(key=lambda x: 1 - x[2] if x[2] <= 1 else 0, reverse=True)
    
    print(f"\nDOCUMENTATION RESULTS ({len(doc_docs)} found, sorted by relevance):")
    print("-" * 50)
    for i, (doc, meta, distance) in enumerate(results):
        # Convert distance to similarity score (lower distance = higher similarity)
        similarity_score = 1 - distance if distance <= 1 else 0
        print(f"[DOC {i+1}] {meta.get('chunk_title', 'Untitled')} (Score: {similarity_score:.3f})")
        print(f"Source: {meta.get('source_file', 'Unknown')}")
        print(f"Category: {meta.get('doc_category', 'general')}")
        print(f"Section: {meta.get('section_type', 'documentation')}")
        if meta.get('parent_context'):
            print(f"Context: {meta.get('parent_context')}")
        print(f"Distance: {distance:.4f}")
        print(f"Content: {doc[:200]}...")
        print()
    
    return doc_docs, doc_metas, doc_distances

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python test_docs_retrieval.py '<query>'")
        print("Example: python test_docs_retrieval.py 'How do I create an array in Motoko?'")
        sys.exit(1)
    
    query = sys.argv[1]
    
    if not docs_collection:
        print("Error: motoko_docs collection not found")
        sys.exit(1)
    
    # Show collection stats
    try:
        docs_count = docs_collection.count()
        print(f"Documentation collection: {docs_count} items")
    except:
        print("Documentation collection: count unavailable")
    
    # Run query
    retrieve_docs(query)