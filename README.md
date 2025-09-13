# Motoko Coder

A Retrieval-Augmented Generation (RAG) pipeline for Motoko code search and code generation, powered by ChromaDB, local embeddings, and Google Gemini.

**Project Demo (National Round)**: https://app.screencastify.com/watch/fGhZUe1zzkabRKVxm1wj

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

**IMPORTANT**: All commands must be run from the project root directory to ensure correct ChromaDB access. The system uses a single ChromaDB instance located at `chromadb_data/` in the project root.

### 1. Fetch Motoko Data Sources
**Important**: Run these steps in the following order to populate the ChromaDB with all necessary data.

#### A. Clone Official Motoko Documentation
```bash
python clone_motoko_docs.py
```

#### B. Clone Motoko Project Samples
Run the following script to automatically clone a large set of Motoko project samples into the `motoko_code_samples/` directory:
```bash
python clone_motoko_repos.py
```
This will download many Motoko repositories and add them to `.gitignore` automatically.

### 2. Ingest Data into ChromaDB
**Important**: Run these ingestion scripts in order after completing step 1. All scripts must be run from the project root directory.

#### A. Ingest Motoko Documentation (if available)
```bash
python ingest/motoko_docs_ingester.py
```

#### B. Ingest Motoko Code Samples
This will index all `.mo` and `mops.toml` files in `motoko_code_samples/` and store their embeddings and metadata in ChromaDB.
```bash
python ingest/motoko_samples_ingester.py
```

### 3. Start the API System
```bash
# Terminal 1: Authentication server (port 8001)
set PYTHONPATH=.
python -m uvicorn API.auth_server:app --reload --port 8001

# Terminal 2: RAG API server (port 8000)
set PYTHONPATH=.
python -m uvicorn API.api_server:app --reload --port 8000

# Terminal 3: MCP HTTP server (port 3000)
set PYTHONPATH=.
python MCP_Server/server.py --port 3000
```

### 4. Test the System
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
├── MCP_Server/                   # MCP Server implementation
│   └── server.py                 # MCP HTTP server (port 3000)
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

### MCP HTTP Server (Port 3000)
- MCP (Model Context Protocol) server providing tools for Motoko code context and generation
- Tools available: `get_motoko_context`, `generate_motoko_code`
- Access via MCP-compatible clients (Cursor, Claude Desktop, etc.)

## Integration with Cursor/VS Code

### As OpenAI-Compatible Endpoint
1. In Cursor/VS Code, go to your LLM extension settings
2. Set the "OpenAI Base URL" to: `http://localhost:8000/v1/chat/completions`
3. Set the API key to your generated API key

### As MCP Server with Cursor
1. Start the MCP server:
   ```bash
   python MCP_Server/server.py --port 3000
   ```

2. Configure Cursor to use the MCP server by adding this to your Cursor MCP configuration:
   ```json
   {
     "mcpServers": {
       "motoko-coder": {
         "url": "http://localhost:3000/mcp"
       }
     }
   }
   ```

3. Once configured, Cursor will have access to these MCP tools:
   - `get_motoko_context`: Retrieves relevant Motoko code examples
   - `generate_motoko_code`: Generates complete Motoko code with RAG context

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

### MCP Server Usage
Once configured with Cursor or other MCP clients, you can:
- Ask Motoko-related questions and get context-aware responses
- Request code generation with relevant examples from the knowledge base
- Get help with Motoko patterns and best practices

Example MCP server commands:
```bash
# Start with default port 3000
python MCP_Server/server.py

# Start with custom port
python MCP_Server/server.py --port 3001

# Enable debug logging
python MCP_Server/server.py --log-level DEBUG
```

## Environment Variables

Create a `.env` file in your project root:
```env
# Required: Google Gemini API key for the RAG functionality
GEMINI_API_KEY=your-gemini-api-key-here
```

## Integration with Other Tools

### IC-Vibe-Coding-Template-Motoko

[IC-Vibe-Coding-Template-Motoko](https://github.com/pt-icp-hub/IC-Vibe-Coding-Template-Motoko) can be enhanced by integrating with icp-coder, which provides advanced context retrieval for more accurate Motoko code generation. icp-coder's RAG pipeline can supply relevant code samples and patterns to improve the template's functionality.

To integrate, once you have setup icp-coder, follow the installation instructions in the [IC-Vibe-Coding-Template-Motoko repository](https://github.com/pt-icp-hub/IC-Vibe-Coding-Template-Motoko)

This integration expands the available context for code generation, resulting in more comprehensive and accurate Motoko code suggestions.

## Documentation

- **System Architecture**: See `RAG_PIPELINE_DIAGRAM.md`
- **RAG Approach**: See `RAG_APPROACH_DIAGRAM.md`
- **API Documentation**: See `API/README.md`
- **MCP Specification**: See `API/MCP_SPECIFICATION.md`

---

**Now you can build Motoko code assistants with Python, ChromaDB, Gemini, and advanced RAG workflows!**
