# ICP Coder

An AI-powered Motoko programming assistant that brings intelligent code suggestions, context-aware completions, and instant documentation access directly into your IDE. Built with Retrieval-Augmented Generation (RAG), ChromaDB vector store, and LLM integration (Gemini/OpenAI/Claude).

## ✨ Features

- 🔍 **Smart Context Retrieval** - Search through 40+ Motoko code samples and official documentation
- 🤖 **AI Code Generation** - Generate Motoko code with LLM assistance (Gemini/OpenAI/Claude)
- ⚡ **RAG-Powered** - Combines vector similarity search with intelligent code generation
- 🎯 **IDE Integration** - Works seamlessly with Cursor, Claude Desktop, and MCP-compatible editors
- 🔒 **User Authentication** - Secure API key management for multi-user environments
- 🌐 **Production Ready** - Hosted backend available at `https://icp-coder.q3labs.io`

## 🚀 Quick Start (Production)

Get up and running in 3 minutes using our hosted backend.

### Step 1: Get an API Key

Visit our Swagger UI to register and generate your API key:

1. Open: **<https://icp-coder.q3labs.io/swagger/index.html>**
2. Register via `/api/v1/auth/register` endpoint
3. Login via `/api/v1/auth/login` endpoint  
4. Generate your API key from `/api/v1/keys` endpoint
5. **Save your API key** - you'll need it in the next step

### Step 2: Configure MCP Server in Cursor

Add this configuration to your Cursor MCP settings file (`~/.cursor/mcp.json`):

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

Replace `your-api-key-here` with the API key from Step 1.

### Step 3: Restart Cursor

**Completely restart Cursor** (not just reload) for the changes to take effect.

### Available MCP Tools

Once configured, you'll have access to:

1. **`get_motoko_context`** - Retrieves relevant Motoko code snippets and documentation
   - Search through curated examples and official docs
   - Get contextual code samples for your queries

2. **`generate_motoko_code`** - Generates complete Motoko code
   - AI-powered code generation using RAG context
   - Supports custom temperature and token limits

**Example queries:**

- "How do I create a stable variable in Motoko?"
- "Generate a canister for user profile management with CRUD operations"
- "Show me examples of using HashMap in Motoko"

## 🔧 Troubleshooting

### MCP Tools Not Showing

If tools don't appear after restarting Cursor, try global installation:

```bash
npm install -g @q3labs/icp-coder
```

Update config to use the global command:

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

### Node.js Version

The MCP server requires Node.js 22+. Check your version:

```bash
node --version
```

---

## 💡 How It Works

```
┌─────────────┐
│   Cursor    │  Your IDE with MCP support
└──────┬──────┘
       │ MCP Protocol
┌──────▼──────────────┐
│ @q3labs/icp-coder   │  MCP Server (npm package)
└──────┬──────────────┘
       │ HTTPS/REST API
┌──────▼──────────────┐
│  Backend Server     │  Go API + Python RAG Pipeline
│  ChromaDB Store     │  Vector embeddings + LLM
└─────────────────────┘
```

**Workflow:**

1. **Query** - You ask a question about Motoko in Cursor
2. **Context Retrieval** - MCP server searches ChromaDB for relevant code samples
3. **LLM Generation** - Retrieved context is combined with your prompt via LLM
4. **Response** - Smart, context-aware code suggestions returned to your IDE

### RAG Pipeline

<img width="1410" height="926" alt="Untitled-2025-07-18-1340" src="https://github.com/user-attachments/assets/19c42a00-8b9f-44d7-8ea1-ebde2861f4d0" />

### MCP Server Overview

ICP Coder is built around a Model Context Protocol (MCP) server that streams Motoko-specific context directly into your IDE. The service:

- Serves Motoko knowledge over MCP protocol
- Retrieves embeddings from ChromaDB populated with documentation and sample projects
- Orchestrates LLM providers (Gemini/OpenAI/Claude) with retrieved snippets for smart code generation

---

## 🛠️ Local Setup

Want to run your own backend? Follow these instructions to set up the full stack locally.

### Prerequisites

#### Required Software

- **Node.js 22+** - MCP server (for production usage via npm)
- **Go 1.24+** - Backend API server (for local setup)
- **Python 3.11+** - RAG pipeline and embedding generation
- **Docker & Docker Compose** - Containerized deployment (recommended)
- **Make** - Build automation

#### API Keys

You'll need at least one LLM provider API key:

- **Google Gemini** (recommended)
- **OpenAI** (alternative)
- **Claude** (alternative)

#### System Requirements

- **~10GB of free storage** for the full dataset and embeddings

### Setup Steps

#### 1. Backend Setup

Clone the repository and set up the backend:

```bash
git clone https://github.com/Quantum3-Labs/icp-coder.git
cd icp-coder/backend
```

Create your environment file:

```bash
cp .env.example .env
```

Edit `.env` and configure:

- Your LLM API key (Gemini/OpenAI/Claude - choose one)
- Database settings
- `PUBLIC_BACKEND_URL` (use `http://localhost:8080` for local)

**Important**: Only set one LLM provider and its key at a time.

Start the backend:

```bash
make up
```

The backend will be available at `http://localhost:8080`.

#### 2. Generate API Key

Once the backend is running:

1. Open: **<http://localhost:8080/swagger/index.html>**
2. Register via `/api/v1/auth/register`
3. Login via `/api/v1/auth/login`
4. Generate your API key from `/api/v1/keys`

#### 3. Configure MCP Server

Update your `~/.cursor/mcp.json` to point to your local backend:

```json
{
  "mcpServers": {
    "icp-coder": {
      "command": "npx",
      "args": ["-y", "@q3labs/icp-coder"],
      "env": {
        "API_KEY": "your-api-key-here",
        "BACKEND_URL": "http://localhost:8080"
      }
    }
  }
}
```

Restart Cursor completely.

### Development Mode

For active development with live reload:

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

### Using Local MCP Server Development Version

For MCP server development:

```bash
cd mcp_server
npm install
npm run build
```

Update `~/.cursor/mcp.json` to use local files:

```json
{
  "mcpServers": {
    "icp-coder": {
      "command": "node",
      "args": ["/absolute/path/to/icp-coder/mcp_server/dist/index.js"],
      "env": {
        "API_KEY": "your-api-key-here",
        "BACKEND_URL": "http://localhost:8080"
      }
    }
  }
}
```

---

## 📡 Optional Interfaces

### Chat Completion API

You can also use the backend directly via REST API:

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

## 🔗 Integrations

[IC-Vibe-Coding-Template-Motoko](https://github.com/pt-icp-hub/IC-Vibe-Coding-Template-Motoko) can be enhanced with ICP Coder's RAG context. Follow the installation instructions in that repository to integrate.

## 📁 Project Structure

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
│   ├── docs/                      # Swagger API documentation
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── Makefile
│   ├── go.mod
│   └── requirements.txt           # Python dependencies
├── mcp_server/                    # MCP (Model Context Protocol) server
│   ├── src/
│   │   ├── tools/
│   │   │   ├── generate-motoko-code.tool.ts
│   │   │   └── get-motoko-context.tool.ts
│   │   └── index.ts              # MCP server entry point
│   ├── package.json              # Published as @q3labs/icp-coder
│   └── tsconfig.json
├── RAG_PIPELINE_DIAGRAM.md
├── RAG_APPROACH_DIAGRAM.md
└── README.md
```

## 📚 Documentation

- **High-Level Architecture**: [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)
- **RAG Pipeline Details**: [RAG_PIPELINE_DIAGRAM.md](RAG_PIPELINE_DIAGRAM.md)
- **RAG Approach**: [RAG_APPROACH_DIAGRAM.md](RAG_APPROACH_DIAGRAM.md)
- **API Documentation**: <https://icp-coder.q3labs.io/swagger/index.html>

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

Built with ❤️ by [Quantum3 Labs](https://github.com/Quantum3-Labs) for the Internet Computer ecosystem.
