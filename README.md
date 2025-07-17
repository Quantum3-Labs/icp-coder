# Motoko Coder (Python Edition)

A Retrieval-Augmented Generation (RAG) pipeline for Motoko code search and code generation, powered by ChromaDB, local embeddings, and Google Gemini.

## Features
- Ingests and indexes all Motoko code samples from the `motoko_code_samples/` directory
- Generates vector embeddings using a local SentenceTransformer model (`all-MiniLM-L6-v2`)
- Stores and retrieves code samples and metadata with ChromaDB
- Retrieval-Augmented Generation (RAG) pipeline for Motoko code search and question answering
- Supports Google Gemini (via SDK or REST API) for code-related Q&A
- Complete API system with user authentication and API key management
- MCP (Model Context Protocol) server for Cursor/VS Code integration

## Requirements
- Python 3.11- [ChromaDB](https://www.trychroma.com/)
- [sentence-transformers](https://www.sbert.net/)
-tqdm](https://tqdm.github.io/) (for progress bars)
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

### 1. Ingest Motoko Code Samples
This will index all `.mo` and `.toml` files in `motoko_code_samples/` and store their embeddings and metadata in ChromaDB.
```bash
python ingest/motoko_samples_ingester.py
```

### 2. Start the API System
```bash
# Terminal1: Authentication server (port 8001)
python -m uvicorn API.auth_server:app --reload --port 8001
# Terminal2: RAG API server (port 8000)
python -m uvicorn API.api_server:app --reload --port 8000
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
│   ├── mcp_server.py             # MCP server for Cursor/VS Code
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

### MCP Server
- `get_motoko_context` - Retrieve relevant Motoko code context

## Integration with Cursor/VS Code

### As OpenAI-Compatible Endpoint
1. SetOpenAI Base URL" to: `http://localhost:8001chat/completions`
2. Use your generated API key

### As MCP Server
Configure in Cursor/VS Code MCP settings:
```json[object Object]mcpServers: {
    motoko coder": [object Object]      command:python",
     args: [API/mcp_server.py"],
      env:[object Object]       PYTHONPATH:."
      }
    }
  }
}
```

## Usage Examples

### Direct RAG Inference
```bash
python rag/inference_gemini.py
# Enter your Motoko question when prompted
```

### API Usage
```bash
curl -X POST http://localhost:8001/chat/completions" \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d {messages":     {"role": user,content:How do I write a counter canister in Motoko?"}
    ]
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

**Now you can build Motoko code assistants with Python, ChromaDB, and Gemini!**
