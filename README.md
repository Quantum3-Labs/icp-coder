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
- Python 3.11+
- [ChromaDB](https://www.trychroma.com/)
- [sentence-transformers](https://www.sbert.net/)
- [tqdm](https://tqdm.github.io/) (for progress bars)
- [python-dotenv](https://pypi.org/project/python-dotenv/) (for loading environment variables)
- Google Gemini API key

## Setup

Run all commands from the project root so the shared ChromaDB instance at `chromadb_data/` is detected correctly.

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the project root with your Gemini credentials:

```env
GEMINI_API_KEY=your-gemini-api-key-here
SECRET_KEY=change-me
```

## Prepare the Knowledge Base

Populate the vector store before starting the MCP server.

1. **Clone official Motoko documentation**
   ```bash
   python clone_motoko_docs.py
   ```

2. **Clone Motoko project samples**
   ```bash
   python clone_motoko_repos.py
   ```
   This script downloads a curated collection into `motoko_code_samples/` and updates `.gitignore` automatically.

3. **Ingest Motoko documentation**
   ```bash
   python ingest/motoko_docs_ingester.py
   ```

4. **Ingest Motoko code samples**
   ```bash
   python ingest/motoko_samples_ingester.py
   ```
   All `.mo` and `mops.toml` files are embedded and stored in ChromaDB.

## Generate an API Key

The MCP server uses the authentication service to guard access. Create an API key before connecting external clients.

1. Start the authentication API (runs alongside the MCP server):
   ```bash
   set PYTHONPATH=.
   python -m uvicorn API.auth_server:app --reload --port 8001
   ```

2. Register a user (once per install):
   ```bash
   curl -X POST http://localhost:8001/register \
     -H "Content-Type: application/json" \
     -d '{
       "username": "motoko",
       "password": "s3cret",
       "email": "you@example.com"
     }'
   ```

3. Log in to receive a bearer token:
   ```bash
   curl -X POST http://localhost:8001/login \
     -H "Content-Type: application/json" \
     -d '{
       "username": "motoko",
       "password": "s3cret"
     }'
   ```
   Copy the `access_token` from the response.

4. Create an API key (supply the bearer token from the previous step):
   ```bash
   curl -X POST http://localhost:8001/api-keys \
     -H "Authorization: Bearer ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Cursor"
     }'
   ```
   The response includes an api_key value--use it in your MCP client configuration.

## Run the MCP Server

With the knowledge base prepared, launch the MCP server to make the retrieval tools available:

```bash
set PYTHONPATH=.
python MCP_Server/server.py --port 3000
```

Key options:
- `--port`: choose a different HTTP port (default `3000`)
- `--log-level`: adjust logging (`DEBUG`, `INFO`, etc.)

If the port is already in use, stop the conflicting service or supply an alternative port.

## Connect from Cursor/VS Code

1. Start the MCP server (see above).
2. In Cursor/VS Code, open the LLM or MCP configuration.
3. Add the Motoko Coder MCP endpoint (replace `YOUR_API_KEY` with one generated below):
   ```json
   {
     "mcpServers": {
       "motoko-coder": {
         "url": "http://localhost:3000/mcp",
         "headers": {
           "API_KEY": "YOUR_API_KEY"
         }
       }
     }
   }
   ```
4. Restart the client if required. Available tools:
   - `get_motoko_context`: retrieves relevant Motoko examples
   - `generate_motoko_code`: generates Motoko code with RAG context

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

### Test the API

Example client:

```bash
python API/client_example.py
```

Direct cURL request:

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

### Direct CLI Inference

Run the standalone script to experiment with Gemini-powered RAG outside of MCP clients:

```bash
python rag/inference_gemini.py
```

## Data Refresh Automation

The `automated_ingestion_job` scheduler refreshes the ChromaDB database on the 1st of every month at 02:00 UTC. It reclones repositories and rebuilds embeddings to keep suggestions current.

```bash
python automated_ingestion_job/scheduler.py
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

---

Build Motoko code assistants with Python, ChromaDB, Gemini, and a first-class MCP workflow.
