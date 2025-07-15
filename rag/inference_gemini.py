import os
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from dotenv import load_dotenv
import requests
import textwrap

# Try to import the Gemini SDK
try:
    import google.generativeai as genai
    GEMINI_SDK_AVAILABLE = True
except ImportError:
    GEMINI_SDK_AVAILABLE = False

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ChromaDB setup
CHROMA_DIR = os.path.join(os.getcwd(), "chromadb_data")
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = chroma_client.get_or_create_collection("motoko_code_samples")

# Embedding function for retrieval
embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# Gemini inference parameters
GENERATION_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 64,
    "max_output_tokens": 8192,
}
MODEL_NAME = "models/gemini-2.5-flash"  # Gemini Flash 2.5

def retrieve_context(query, n_results=10):
    query_emb = embedding_fn([query])[0]
    results = collection.query(query_embeddings=[query_emb], n_results=n_results)
    docs = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    return docs, metadatas

def count_tokens_gemini_sdk(model, prompt):
    # Use the Gemini SDK to count tokens
    try:
        return model.count_tokens(prompt).total_tokens
    except Exception:
        return None

def answer_with_gemini_sdk(query, context):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        MODEL_NAME,
        generation_config=GENERATION_CONFIG
    )
    prompt = f"Context:\n{context}\n\n Request: {query}\nAnswer:"
    num_tokens = count_tokens_gemini_sdk(model, prompt)
    response = model.generate_content(prompt)
    return response.text, num_tokens

def answer_with_gemini_rest(query, context):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    prompt = f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": GENERATION_CONFIG
    }
    resp = requests.post(url, headers=headers, params=params, json=data)
    if resp.ok:
        # Gemini REST API does not return token count directly
        answer = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        return answer, None
    else:
        return f"Gemini API error: {resp.text}", None

def main():
    query = input("Enter your Motoko-related question: ")
    docs, metadatas = retrieve_context(query)
    context = "\n---\n".join(docs)
    print("\nRetrieved context:")
    for i, (doc, meta) in enumerate(zip(docs, metadatas)):
        print(f"[{i+1}] {meta['filename']} ({meta['folders']}):\n{doc[:200]}...\n")
    print("\n---\n")
    print(f"Gemini model: {MODEL_NAME}")
    print(f"Generation config: {GENERATION_CONFIG}")
    print("\nGemini response:")
    if GEMINI_SDK_AVAILABLE:
        answer, num_tokens = answer_with_gemini_sdk(query, context)
        if num_tokens is not None:
            print(f"[Token count for prompt: {num_tokens}]")
    else:
        answer, _ = answer_with_gemini_rest(query, context)
        print("[Token count not available: Gemini SDK not installed]")
    print(answer)

if __name__ == "__main__":
    main() 