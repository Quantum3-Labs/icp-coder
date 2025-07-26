# Motoko Coder (Python Edition)

A Retrieval-Augmented Generation (RAG) pipeline for Motoko code search and code generation, powered by ChromaDB, local embeddings, and Google Gemini.

Project Overview: https://www.loom.com/share/6dd2dfd054ff4e79a4f3bf4f61b0dc0f?sid=4ba1aff0-cf25-4fd4-8717-30c0dcf8e4dc

## RAG Pipeline

<img width="1410" height="926" alt="Untitled-2025-07-18-1340" src="https://github.com/user-attachments/assets/19c42a00-8b9f-44d7-8ea1-ebde2861f4d0" />


## Features
- Ingests and indexes all Motoko code samples from the `motoko_code_samples/` directory
- Generates vector embeddings using a local SentenceTransformer model (`all-MiniLM-L6-v2`)
- Stores and retrieves code samples and metadata with ChromaDB
- Retrieval-Augmented Generation (RAG) pipeline for Motoko code search and question answering
- Supports Google Gemini (via SDK or REST API) for code-related Q&A
- Complete API system with user authentication and API key management
- MCP (Model Context Protocol) server for Cursor/VS Code integration (supports both process and HTTP modes)

## Requirements
- Python 3.11+
- [ChromaDB](https://www.trychroma.com/)
- [sentence-transformers](https://www.sbert.net/)
- [tqdm](https://tqdm.github.io/) (for progress bars)
- [python-dotenv](https://pypi.org/project/python-dotenv/) (for loading environment variables)
- Google Gemini API key (set `GEMINI_API_KEY` in a `.env` file)

## Setup
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
# Create a .env file with your Gemini API key:
echo GEMINI_API_KEY=your-gemini-key > .env
```

## Quick Start

### 1. Fetch Motoko Project Samples
Run the following script to automatically clone a large set of Motoko project samples into the `motoko_code_samples/` directory:
```bash
python clone_motoko_repos.py
```
This will download many Motoko repositories and add them to `.gitignore` automatically.

### 2. Ingest Motoko Code Samples
This will index all `.mo` and `mops.toml` files in `motoko_code_samples/` and store their embeddings and metadata in ChromaDB.
```bash
python ingest/motoko_samples_ingester.py
```

### 2. Start the API System
```bash
# Terminal 1: Authentication server (port 8001)
set PYTHONPATH=.
python -m uvicorn API.auth_server:app --reload --port 8001

# Terminal 2: RAG API server (port 8000)
set PYTHONPATH=.
python -m uvicorn API.api_server:app --reload --port 8000

# Terminal 3: MCP HTTP server (port 9000)
set PYTHONPATH=.
python -m uvicorn API.mcp_api_server:app --reload --port 9000
```

### 3. Test the System
```bash
# Run the example client
python API/client_example.py

# Or test the RAG inference directly
python rag/inference_gemini.py
```

## Project Structure
```
ICP_Coder/
├── API/                          # Complete API system
│   ├── api_server.py             # RAG API server (OpenAI-compatible)
│   ├── auth_server.py            # User authentication server
│   ├── database.py               # SQLite database operations
│   ├── mcp_server.py             # MCP process server (stdin/stdout)
│   ├── mcp_api_server.py         # MCP HTTP server (FastAPI, port 9000)
│   ├── client_example.py         # Example client
│   └── README.md                 # API documentation
├── ingest/
│   └── motoko_samples_ingester.py # Code samples ingestion
├── rag/
│   └── inference_gemini.py       # Direct RAG inference
├── motoko_code_samples/          # Motoko code samples collection
├── chromadb_data/                # Vector database (auto-created)
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── RAG_PIPELINE_DIAGRAM.md       # System architecture diagram
└── RAG_APPROACH_DIAGRAM.md       # RAG approach diagram
```

## API Endpoints

### Authentication Server (Port 8001)
- `POST /register` - Register a new user
- `POST /login` - Login user
- `POST /api-keys` - Create API key (requires authentication)
- `GET /api-keys` - List user's API keys (requires authentication)
- `DELETE /api-keys/{id}` - Revoke API key (requires authentication)

### RAG API Server (Port 8000)
- `POST /v1/chat/completions` - Generate Motoko code (requires API key)

### MCP HTTP Server (Port 9000)
- `POST /v1/mcp/context` - Retrieve relevant Motoko code context for RAG (requires API key)
  - **Request body:**
    ```json
    {
      "query": "How do I write a counter canister in Motoko?",
      "api_key": "YOUR_API_KEY",
      "max_results": 5
    }
    ```
  - **Response:** JSON with context snippets, metadata, and status.

## Integration with Cursor/VS Code

### As OpenAI-Compatible Endpoint
1. In Cursor/VS Code, go to your LLM extension settings
2. Set the "OpenAI Base URL" to: `http://localhost:8000/v1/chat/completions`
3. Set the API key to your generated API key

### As MCP HTTP Server
Add to your MCP config (e.g., `mcp.config.json`):
```json
{
  "inputs": [
    {
      "id": "motoko_api_key",
      "type": "secret",
      "description": "Your Motoko Coder API Key for RAG context"
    }
  ],
  "servers": {
    "motoko coder": {
      "type": "http",
      "url": "http://localhost:9000/v1/mcp/context",
      "method": "POST",
      "headers": {
        "Content-Type": "application/json"
      },
      "body": {
        "query": "${input.query}",
        "api_key": "${inputs.motoko_api_key}",
        "max_results": 5
      }
    }
  }
}
```
- This will prompt you for your API key and send it with every context request.

## Usage Examples

### Direct RAG Inference
```bash
python rag/inference_gemini.py
# Enter your Motoko question when prompted
```

### API Usage
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "messages": [
      {"role": "user", "content": "How do I write a counter canister in Motoko?"}
    ]
  }'
```

### MCP HTTP Usage
```bash
curl -X POST http://localhost:9000/v1/mcp/context \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I write a counter canister in Motoko?",
    "api_key": "YOUR_API_KEY",
    "max_results": 5
  }'
```

## Environment Variables

Create a `.env` file in your project root:
```env
# Required: Google Gemini API key for the RAG functionality
GEMINI_API_KEY=your-gemini-api-key-here
```

## Documentation

- **System Architecture**: See `RAG_PIPELINE_DIAGRAM.md`
- **RAG Approach**: See `RAG_APPROACH_DIAGRAM.md`
- **API Documentation**: See `API/README.md`
- **MCP Specification**: See `API/MCP_SPECIFICATION.md`

---

**Now you can build Motoko code assistants with Python, ChromaDB, Gemini, and advanced RAG workflows!**
