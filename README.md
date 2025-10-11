# Motoko Coder

A Retrieval-Augmented Generation (RAG) pipeline for Motoko code search and code generation, powered by ChromaDB, local embeddings, and Google Gemini.

**Project Demo (National Round)**: https://app.screencastify.com/watch/fGhZUe1zzkabRKVxm1wj

## MCP Server Overview

Motoko Coder is built around an MCP (Model Context Protocol) server that streams Motoko-specific context directly into tools such as Cursor, Claude Desktop, and other MCP-compatible clients. The service sits on top of a local ChromaDB vector store and handles retrieval, formatting, and generation so your editor can deliver context-aware completions in real time.

- Serve Motoko knowledge over HTTP or process-based MCP transports
- Retrieve embeddings from ChromaDB populated with documentation and sample projects
- Generate new Motoko code by orchestrating Google Gemini with retrieved snippets

## RAG Pipeline

<img width="1410" height="926" alt="Untitled-2025-07-18-1340" src="https://github.com/user-attachments/assets/19c42a00-8b9f-44d7-8ea1-ebde2861f4d0" />

## Features
- Ingests and indexes all Motoko code samples from the `motoko_code_samples/` directory
- Generates vector embeddings using the local SentenceTransformer model (`all-MiniLM-L6-v2`)
- End-to-end RAG workflow for Motoko code search and question answering
- Complete MCP server that exposes retrieval and generation tools (process and HTTP modes)
- REST API layer with user authentication and key management
- Supports Google Gemini (SDK or REST API) for code-focused prompts
- ChromaDB-backed storage for metadata and vector search

## Prerequisites

### Required Software
- **Go 1.24+** - Backend API server (if run directly)
- **Python 3.11+** - RAG pipeline and embedding generation (if run directly)
- **Node.js 22+** - MCP server (node_mcp_server)
- **Docker & Docker Compose** - Containerized deployment
- **Make** - Build automation (pre-installed on Linux/Mac, [install on Windows](https://gnuwin32.sourceforge.net/packages/make.htm))

### Python Dependencies
- [ChromaDB](https://www.trychroma.com/) - Vector database for embeddings
- [sentence-transformers](https://www.sbert.net/) - Local embedding models
- [tqdm](https://tqdm.github.io/) - Progress bars during ingestion
- [python-dotenv](https://pypi.org/project/python-dotenv/) - Environment variable management

### API Keys
- **Google Gemini API key** (required for code generation)
- Optional: OpenAI API key or Claude API key (alternative providers)

### System Requirements
- **~10GB of free storage** (local deployment with full dataset)

## Setup

### 1. RAG Backend Setup

Navigate to the backend directory, create an environment file, and start the Go API server:

```bash
cd backend
cp .env.example .env
# Edit .env file and add your configuration (API keys, database settings, etc.)
make up
cd ..
```

**Important**: Make sure to update the values in `.env` with your actual credentials before running `make up`.

### 2. Node MCP Server Setup

Navigate to the node_mcp_server directory and build the TypeScript server:

```bash
cd node_mcp_server
npm install
npm run build
cd ..
```

### 3. Generate API Key

Once the backend is running, navigate to the Swagger UI to register an account and generate an API key:

1. Open your browser and go to: **http://localhost:8080/swagger/index.html**
2. Register a new account
3. Login with your credentials
4. Generate an API key (save this for the next step)

### 4. Configure MCP Server in Cursor

Add the following configuration to your Cursor MCP settings:

```json
{
  "mcpServers": {
    "icp-coder": {
      "command": "node",
      "args": [
        "ABSOLUTE_PATH_TO_dist/index.js"
      ],
      "env": {
        "API_KEY": "YOUR_API_FROM_STEP_3",
        "BACKEND_URL": "http://localhost:8080"
      }
    }
  }
}
```

## How It Works

1. **User Query**: You ask for help with Motoko code, mentioning the MCP tool you want to use.
2. **Context Retrieval**: The server searches ChromaDB for relevant examples.
3. **Gemini Generation**: Gemini combines the retrieved context with your prompt to draft better code.
4. **Response**: The MCP server returns context snippets and/or generated code back to Cursor.

## Optional Interfaces

### REST API Server

The REST API mirrors the MCP functionality and can be used by external services. Run these processes in separate terminals:

```bash
# Terminal 1: Authentication server (port 8001)
set PYTHONPATH=.
python -m uvicorn API.auth_server:app --reload --port 8001

# Terminal 2: RAG API server (port 8000)
set PYTHONPATH=.
python -m uvicorn API.api_server:app --reload --port 8000
```

### Test Chat Completion API

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "messages": [
      {"role": "user", "content": "How do I write a counter canister in Motoko?"}
    ]
  }'
```

With optional parameters:

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "model": "gemini-2.0-flash-exp",
    "messages": [
      {"role": "user", "content": "How do I write a counter canister in Motoko?"}
    ],
    "temperature": 0.7,
    "max_tokens": 2000,
    "conversation_id": 123
  }'
```

### Direct CLI Inference

Run the standalone script to experiment with Gemini-powered RAG outside of MCP clients:

```bash
python rag/inference_gemini.py
```

## Integrations

[IC-Vibe-Coding-Template-Motoko](https://github.com/pt-icp-hub/IC-Vibe-Coding-Template-Motoko) can be enhanced by feeding it Motoko Coder's RAG context. After setting up this project, follow the installation instructions in that repository to wire in the MCP server and improve code suggestions.

## Project Structure

```
ICP_Coder/
|-- API/
|   |-- api_server.py
|   |-- auth_server.py
|   |-- client_example.py
|   |-- database.py
|   |-- mcp_api_server.py
|   |-- mcp_server.py
|   `-- README.md
|-- MCP_Server/
|   `-- server.py
|-- automated_ingestion_job/
|   `-- scheduler.py
|-- ingest/
|   |-- motoko_docs_ingester.py
|   `-- motoko_samples_ingester.py
|-- motoko_code_samples/
|-- rag/
|   |-- inference_base.py
|   `-- inference_gemini.py
|-- chromadb_data/
|-- requirements.txt
|-- RAG_PIPELINE_DIAGRAM.md
|-- RAG_APPROACH_DIAGRAM.md
`-- README.md
```

## Documentation

- **System Architecture**: `RAG_PIPELINE_DIAGRAM.md`
- **RAG Approach**: `RAG_APPROACH_DIAGRAM.md`
- **API Documentation**: `API/README.md`
- **MCP Specification**: `API/MCP_SPECIFICATION.md`
