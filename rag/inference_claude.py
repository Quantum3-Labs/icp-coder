import os
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

# ChromaDB setup
CHROMA_DIR = os.path.join(os.getcwd(), "chromadb_data")
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = chroma_client.get_or_create_collection("motoko_code_samples")

# Embedding function for retrieval
embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

def retrieve_context(query, n_results=3):
    query_emb = embedding_fn([query])[0]
    results = collection.query(query_embeddings=[query_emb], n_results=n_results)
    docs = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    return docs, metadatas

def answer_with_claude(query, context):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    data = {
        "model": "claude-3-opus-20240229",
        "max_tokens": 512,
        "messages": [
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"}
        ]
    }
    resp = requests.post(url, headers=headers, json=data)
    if resp.ok:
        return resp.json()["content"][0]["text"]
    else:
        return f"Claude API error: {resp.text}"

def main():
    query = input("Enter your Motoko-related question: ")
    docs, metadatas = retrieve_context(query)
    context = "\n---\n".join(docs)
    print("\nRetrieved context:")
    for i, (doc, meta) in enumerate(zip(docs, metadatas)):
        print(f"[{i+1}] {meta['filename']} ({meta['folders']}):\n{doc[:200]}...\n")
    print("\n---\n")
    print("Claude response:")
    print(answer_with_claude(query, context))

if __name__ == "__main__":
    main() 