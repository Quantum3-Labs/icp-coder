# ICP Coder

A Retrieval-Augmented Generation (RAG) pipeline for Motoko code search and code generation, powered by ChromaDB, local embeddings, and Google Gemini.

**Project Demo (National Round)**: <https://app.screencastify.com/watch/fGhZUe1zzkabRKVxm1wj>

## MCP Server Overview

ICP Coder is built around an MCP (Model Context Protocol) server that streams Motoko-specific context directly into tools such as Cursor, Claude Desktop, and other MCP-compatible clients. The service sits on top of a local ChromaDB vector store and handles retrieval, formatting, and generation so your editor can deliver context-aware completions in real time.

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
- **Node.js 22+** - MCP server (mcp_server)
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
# Edit .env file and add your configuration (LLM API key (currently supporting Gemini, Claude, OpenAI), database settings, etc.)
make up
```

Set `PUBLIC_BACKEND_URL` to the URL where the backend is reachable. Use `http://localhost:8080` for local development and `https://icp-coder.q3labs.io` (or your production domain) when deploying so the Swagger UI points to the correct host.

**Important**:

- Only set one LLM provider and its key at a time.
- Make sure to update the values in `.env` with your actual credentials before running `make up`.

### 2. Generate API Key

Once the backend is running, navigate to the Swagger UI to register an account and generate an API key:

1. Open your browser and go to: **<http://localhost:8080/swagger/index.html>** (or `https://icp-coder.q3labs.io/swagger/index.html` for production)
2. Register a new account using the `/api/v1/auth/register` endpoint
3. Login with your credentials using the `/api/v1/auth/login` endpoint
4. Generate an API key from the `/api/v1/keys` endpoint
5. Save the API key for use in your IDE configuration below

### 3. Configure MCP Server in Cursor

The ICP Coder MCP server is available as an npm package `@q3labs/icp-coder`. This is the **recommended way** to use the MCP server.

Add the following configuration to your Cursor MCP settings file (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "icp-coder": {
      "command": "npx",
      "args": [
        "-y",
        "@q3labs/icp-coder"
      ],
      "env": {
        "API_KEY": "your-api-key-here",
        "BACKEND_URL": "https://icp-coder.q3labs.io"
      }
    }
  }
}
```

**Important:**

- Replace `your-api-key-here` with the API key you generated in step 2
- Use `https://icp-coder.q3labs.io` for production (recommended)
- Use `http://localhost:8080` if running the backend locally

After adding the configuration, **completely restart Cursor** for the changes to take effect.

#### Available MCP Tools

Once configured, the following tools will be available in Cursor:

1. **`get_motoko_context`** - Retrieves relevant Motoko code snippets and documentation from the RAG system
2. **`generate_motoko_code`** - Generates Motoko code using backend RAG context and the configured LLM provider

---

### Alternative Setup Options

<details>
<summary><b>Using Local Development Version</b> (for contributors)</summary>

If you're developing the MCP server locally, first build it:

```bash
cd mcp_server
npm install
npm run build
```

Then configure Cursor to use the built files from your `mcp_server` directory:

```json
{
  "mcpServers": {
    "icp-coder": {
      "command": "node",
      "args": [
        "/absolute/path/to/icp-coder/mcp_server/dist/index.js"
      ],
      "env": {
        "API_KEY": "your-api-key-here",
        "BACKEND_URL": "http://localhost:8080"
      }
    }
  }
}
```

Replace `/absolute/path/to/icp-coder/` with your actual project path.

</details>

<details>
<summary><b>Troubleshooting: MCP Tool Not Working</b></summary>

If the MCP server shows "No tools, prompts, or resources" after restarting Cursor, try installing the package globally:

```bash
npm install -g @q3labs/icp-coder
```

Then update your config to use the global installation:

```json
{
  "mcpServers": {
    "icp-coder": {
      "command": "icp-coder",
      "args": [],
      "env": {
        "API_KEY": "your-api-key-here",
        "BACKEND_URL": "https://icp-coder.q3labs.io"
      }
    }
  }
}
```

</details>

## Development Mode

For active development with live reload and debugging:

```bash
cd backend

# Use development environment
cp .env.dev.example .env.dev
# Edit .env.dev and add your API keys

# Start with live reload (uses Air)
make dev

# View logs
make dev-logs

# Stop
make dev-down
```

**Development features:**

- Automatic rebuild on code changes using Air
- Debug mode with verbose logging
- Source code mounted as volume for instant changes
- Swagger docs auto-generated on every build

See `backend/Makefile` for all development commands (`make dev-*`).

## How It Works

1. **User Query**: You ask for help with Motoko code, mentioning the MCP tool you want to use.
2. **Context Retrieval**: The server searches ChromaDB for relevant examples.
3. **Gemini Generation**: Gemini combines the retrieved context with your prompt to draft better code.
4. **Response**: The MCP server returns context snippets and/or generated code back to Cursor.

## Optional Interfaces

### Chat Completion API

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

## Integrations

[IC-Vibe-Coding-Template-Motoko](https://github.com/pt-icp-hub/IC-Vibe-Coding-Template-Motoko) can be enhanced by feeding it Motoko Coder's RAG context. After setting up this project, follow the installation instructions in that repository to wire in the MCP server and improve code suggestions.

## Project Structure

```
icp-coder/
├── backend/                        # Go backend server
│   ├── cmd/
│   │   └── server/
│   │       └── main.go            # Main entry point
│   ├── internal/
│   │   ├── api/
│   │   │   ├── handlers/          # HTTP request handlers
│   │   │   ├── middleware/        # CORS, auth middleware
│   │   │   └── router.go          # API routing
│   │   ├── auth/                  # Authentication service
│   │   ├── codegen/               # Code generation with LLM providers
│   │   ├── database/              # Database connection & queries
│   │   └── rag/                   # RAG service & Python client
│   ├── scripts/                   # Python ingestion scripts
│   ├── docs/                      # API documentation
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── Makefile
│   ├── go.mod
│   └── requirements.txt           # Python dependencies for scripts
├── mcp_server/                    # MCP (Model Context Protocol) server
│   ├── src/
│   │   ├── tools/
│   │   │   ├── generate-motoko-code.tool.ts
│   │   │   └── get-motoko-context.tool.ts
│   │   └── index.ts              # MCP server entry point
│   ├── package.json
│   └── tsconfig.json
├── RAG_PIPELINE_DIAGRAM.md
├── RAG_APPROACH_DIAGRAM.md
└── README.md
```

## High Level Architecture

<img width="1499" height="1051" alt="image" src="https://github.com/user-attachments/assets/506d2404-58f2-4789-b60b-8c535d1e2179" />

## Documentation

- **High-Level Architecture**: `ARCHITECTURE_DIAGRAM.md`
- **System Architecture**: `RAG_PIPELINE_DIAGRAM.md`
- **RAG Approach**: `RAG_APPROACH_DIAGRAM.md`
