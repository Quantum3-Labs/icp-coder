import os
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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

def answer_with_openai(query, context):
    openai.api_key = OPENAI_API_KEY
    prompt = f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "You are a Motoko expert."},
                  {"role": "user", "content": prompt}],
        max_tokens=512
    )
    return response.choices[0].message["content"].strip()

def main():
    query = input("Enter your Motoko-related question: ")
    docs, metadatas = retrieve_context(query)
    context = "\n---\n".join(docs)
    print("\nRetrieved context:")
    for i, (doc, meta) in enumerate(zip(docs, metadatas)):
        print(f"[{i+1}] {meta['filename']} ({meta['folders']}):\n{doc[:200]}...\n")
    print("\n---\n")
    print("OpenAI response:")
    print(answer_with_openai(query, context))

if __name__ == "__main__":
    main() 