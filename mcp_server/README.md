# ICP Coder MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that provides **AI-powered Motoko programming assistance** through Retrieval-Augmented Generation (RAG). Get intelligent code suggestions, context-aware completions, and instant access to Motoko documentation directly in your IDE.

## ✨ Features

- 🔍 **Smart Context Retrieval** - Search through 40+ Motoko code samples and official documentation
- 🤖 **AI Code Generation** - Generate Motoko code with LLM assistance (Gemini/OpenAI/Claude)
- ⚡ **RAG-Powered** - Combines vector similarity search with LLM generation for accurate results
- 🎯 **IDE Integration** - Works seamlessly with Cursor, Claude Desktop, and MCP-compatible editors
- 🔒 **Type-Safe** - Built with TypeScript and Zod validation
- 🌐 **Production Ready** - Backed by a robust Go backend with ChromaDB vector store

## 🚀 Quick Start

### Step 1: Get an API Key

You need an API key from the ICP Coder backend to use this MCP server.

1. Visit the Swagger UI: **<https://icp-coder.q3labs.io/swagger/index.html>**
2. Register a new account via `/api/v1/auth/register` endpoint
3. Login using `/api/v1/auth/login` endpoint
4. Generate your API key from `/api/v1/keys` endpoint
5. **Save this key** - you'll need it for the next step

### Step 2: Configure in Cursor

Add this configuration to your Cursor MCP settings file at `~/.cursor/mcp.json`:

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

- Replace `your-api-key-here` with your actual API key from Step 1
- Use `https://icp-coder.q3labs.io` for production (recommended)
- Use `http://localhost:8080` if you're running the backend locally

### Step 3: Restart Cursor

**Completely restart Cursor** (not just reload) for the changes to take effect.

## 🛠️ Available Tools

Once configured, you'll have access to these MCP tools in Cursor:

### `get_motoko_context`

Retrieves relevant Motoko code snippets and documentation from the RAG system based on your query.

**Parameters:**

- `query` (required) - What you're looking for
- `n_results` (optional) - Number of matches to return (1-5, default: 5)

**Example usage:**

```
"How do I create a stable variable in Motoko?"
```

### `generate_motoko_code`

Generates Motoko code using backend RAG context combined with LLM generation.

**Parameters:**

- `query` (required) - Your code generation request
- `temperature` (optional) - Controls creativity (0-2, default varies by provider)
- `max_tokens` (optional) - Maximum tokens to generate

**Example usage:**

```
"Generate a Motoko canister for managing user profiles with CRUD operations"
```

## 🔧 Troubleshooting

### MCP Tools Not Showing Up

If the MCP server shows "No tools, prompts, or resources" after restarting Cursor:

1. **Try global installation:**

   ```bash
   npm install -g @q3labs/icp-coder
   ```

2. **Update your config:**

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

This package requires **Node.js 22.0.0 or higher**. Check your version:

```bash
node --version
```

## 📚 How It Works

1. **You ask a question** about Motoko in your IDE
2. **Context retrieval** searches the ChromaDB vector store for relevant code examples and documentation
3. **LLM generation** combines the retrieved context with your prompt
4. **Smart response** returns context-aware code suggestions directly in Cursor

```
┌─────────────┐
│   Cursor    │  Your IDE
└──────┬──────┘
       │ MCP Protocol
┌──────▼──────┐
│ ICP Coder   │  MCP Server (this package)
│ MCP Server  │
└──────┬──────┘
       │ HTTP/REST
┌──────▼──────┐
│  Backend    │  Go API + Python RAG
│  ChromaDB   │  Vector Store + LLM
└─────────────┘
```

## 🌟 Use Cases

- **Learning Motoko** - Get instant examples and documentation
- **Building Canisters** - Generate boilerplate code for common patterns
- **Debugging** - Find similar code examples to solve issues
- **Best Practices** - Learn from 40+ curated Motoko samples

## 📖 Documentation

For complete documentation including:

- Backend setup and local development
- Contributing guidelines
- Architecture diagrams
- Advanced configuration

Visit the **[main repository](https://github.com/Quantum3-Labs/icp-coder#readme)**.

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/Quantum3-Labs/icp-coder/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Quantum3-Labs/icp-coder/discussions)
- **Repository**: [Quantum3-Labs/icp-coder](https://github.com/Quantum3-Labs/icp-coder)

## 📄 License

MIT License - see [LICENSE](https://github.com/Quantum3-Labs/icp-coder/blob/main/LICENSE) file for details.

---

Built with ❤️ by [Quantum3 Labs](https://github.com/Quantum3-Labs) for the Internet Computer ecosystem.
