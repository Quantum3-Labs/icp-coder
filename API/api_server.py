import os
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
import uvicorn
import sys
import os

# Add project root to path first
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from API.models import conversation
from API.chains import context_injection
from API.enum import separation
from API.repository import conversation_repo
from API import database

from tool.tool_factory import ToolFactory
from tool.get_motoko_context import GetMotokoContext
from tool.generate_motoko_code import GenerateMotokoCode

# Load environment variables
load_dotenv()

# Model configuration
MODEL_NAME = "models/gemini-2.5-flash"

# Tool factory setup
ToolFactory.register("get_motoko_context", GetMotokoContext)
ToolFactory.register("generate_motoko_code", GenerateMotokoCode)

chain = context_injection.ContextInjectionHandler()
conversation_repo.init_schema()


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


app = FastAPI(title="ICP-Coder", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.post("/v1/chat/completions")
async def chat_completions(
    request: Request, body: ChatCompletionRequest, x_api_key: str = Header(None)
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

    # Use tool
    code_generator = ToolFactory.create("generate_motoko_code")
    result_blocks = code_generator.action({"query": query})

    # Extract response from tool result
    answer = (
        result_blocks[0].text
        if result_blocks and hasattr(result_blocks[0], "text")
        else "Error generating response"
    )

    # Handle conversation management
    convo = conversation.Conversation()
    if body.conversation_id is not None:
        convo = conversation_repo.load_conversation(body.conversation_id)

    convo.set_user_id(user_id)
    convo.set_new_message(query)
    final_convo = chain.handle(convo)

    print(answer)
    final_convo.add_turn("user", query)
    # Handle response splitting if separation marker exists
    if separation.Separation.SEPRATION.value in answer:
        response_content = answer.split(separation.Separation.SEPRATION.value, 1)[
            1
        ].strip()
    else:
        response_content = answer

    final_convo.add_turn("system", response_content)
    final_convo.set_new_message(query)
    conversation_repo.save_conversation(final_convo)

    # OpenAI-compatible response
    response = {
        "id": "chatcmpl-motoko-001",
        "object": "chat.completion",
        "created": int(__import__("time").time()),
        "model": body.model or MODEL_NAME,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": (
                        answer.split(separation.Separation.SEPRATION.value, 1)[
                            0
                        ].strip()
                        if separation.Separation.SEPRATION.value in answer
                        else answer
                    ),
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
        },
        "conversation_id": final_convo.id,
    }

    return JSONResponse(content=response)


@app.get("/")
def root():
    return {
        "motoko_coder": "Motoko RAG API is running.",
        "version": "1.0.0",
        "endpoint": "/v1/chat/completions",
        "authentication": "x-api-key header required",
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
