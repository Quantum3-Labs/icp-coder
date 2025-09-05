import os
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import google.generativeai as genai
import uvicorn
from .models import conversation
from .chains import context_injection
from .enum import separation
from .repository import conversation_repo
from . import database

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# ChromaDB setup
CHROMA_DIR = os.path.join(os.getcwd(), "chromadb_data")
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = chroma_client.get_or_create_collection("motoko_code_samples")
embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

GENERATION_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 64,
    "max_output_tokens": 4096,
}
MODEL_NAME = "models/gemini-2.5-flash"
chain = context_injection.ContextInjectionHandler()
conversation_repo.init_schema()
def retrieve_context(query, n_results=10):
    query_emb = embedding_fn([query])[0]
    results = collection.query(query_embeddings=[query_emb], n_results=n_results)
    docs = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    return docs, metadatas

def answer_with_gemini_sdk(query, context):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        MODEL_NAME,
        generation_config=GENERATION_CONFIG
    )
    prompt = f"Context:\n{context}\n\nRequest: {query}\nAnswer:"
    response = model.generate_content(prompt)
    return response.text

# OpenAI-compatible request/response models
class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    stream: Optional[bool] = None
    stop: Optional[Any] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    conversation_id: Optional[int] = None
app = FastAPI(title="Motoko Coder RAG API", version="1.0.0")


@app.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    body: ChatCompletionRequest,
    x_api_key: str = Header(None)
):
    # API key validation using database
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    
    valid, user_id, message = database.validate_api_key(x_api_key)
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Get user query (last user message)
    user_messages = [m for m in body.messages if m.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user message found.")
    query = user_messages[-1].content

    # Retrieve context and answer
    docs, metadatas = retrieve_context(query)
    context = "\n---\n".join(docs)
    convo = conversation.Conversation()
    if(body.conversation_id is not None):
        convo = conversation_repo.load_conversation(body.conversation_id)

    convo.set_user_id(user_id)
    convo.set_new_message(query)
    final_convo = chain.handle(convo)
    answer = answer_with_gemini_sdk(final_convo.build_conversation_history(), context)
    print(answer)
    final_convo.add_turn("user", query)
    final_convo.add_turn("system", answer.split(separation.Separation.SEPRATION.value, 1)[1].strip())
    final_convo.set_new_message(query)
    conversation_repo.save_conversation(final_convo)

    # OpenAI-compatible response
    response = {
        "id": "chatcmpl-motoko-001",
        "object": "chat.completion",
        "created": int(__import__('time').time()),
        "model": body.model or MODEL_NAME,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": answer.split(separation.Separation.SEPRATION.value, 1)[0].strip()
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None
        },
        "conversation_id": final_convo.id
    }

    return JSONResponse(content=response)

@app.get("/")
def root():
    return {
        "motoko_coder": "Motoko RAG API is running.",
        "version": "1.0.0",
        "endpoint": "/v1/chat/completions",
        "authentication": "x-api-key header required"
    }
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


