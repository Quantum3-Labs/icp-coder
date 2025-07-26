import os
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from .database import validate_api_key

# Load environment variables
load_dotenv()

# ChromaDB setup
CHROMA_DIR = os.path.join(os.getcwd(), "chromadb_data")
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = chroma_client.get_or_create_collection("motoko_code_samples")
embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

app = FastAPI(title="ICP_Coder", version="1.0.0")

class MCPContextRequest(BaseModel):
    query: str
    api_key: str
    max_results: Optional[int] = 5

@app.post("/v1/mcp/context")
async def get_motoko_context(
    body: MCPContextRequest
):
    # Log the query received from the LLM
    print("Query received from LLM:", body.query)
    
    # Validate API key
    valid, user_id, message = validate_api_key(body.api_key)
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid API key")
    try:
        # Generate query embedding
        query_emb = embedding_fn([body.query])[0]
        # Search for relevant documents
        results = collection.query(
            query_embeddings=[query_emb],
            n_results=body.max_results
        )
        docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        # Format context
        context_parts = []
        for i, (doc, meta) in enumerate(zip(docs, metadatas)):
            context_part = {
                "index": i + 1,
                "filename": meta.get("filename", "unknown"),
                "project": meta.get("folders", "unknown"),
                "file_type": meta.get("file_type", "unknown"),
                "has_toml": meta.get("has_toml", False),
                "content": doc[:1000] + "..." if len(doc) > 1000 else doc,
                "full_path": meta.get("rel_path", "unknown")
            }
            context_parts.append(context_part)
        response = {
            "success": True,
            "query": body.query,
            "context_count": len(context_parts),
            "context": context_parts,
            "message": f"Retrieved {len(context_parts)} relevant Motoko code samples"
        }
        # Log the context retrieved
        print("Context retrieved:", response)
        return JSONResponse(content=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve Motoko context: {str(e)}")

@app.get("/")
def root():
    return {
        "motoko_coder": "Motoko MCP API is running.",
        "version": "1.0.0",
        "endpoint": "/v1/mcp/context",
        "authentication": "api_key in POST body required"
    }