# ICP Coder MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that provides Motoko programming assistance through Retrieval-Augmented Generation (RAG). This server integrates with IDEs like [Cursor](https://cursor.sh), [Claude Desktop](https://claude.ai/download), and other MCP-compatible tools to deliver context-aware code suggestions and generation for the [Internet Computer](https://internetcomputer.org).

## Features

- **Context Retrieval**: Search through 40+ Motoko code samples and official documentation
- **Code Generation**: Generate Motoko code with LLM assistance (Gemini/OpenAI/Claude)
- **RAG-Powered**: Combines vector similarity search with LLM generation
- **IDE Integration**: Works seamlessly with Cursor, Claude Desktop, and MCP-compatible editors
- **Type-Safe**: Built with TypeScript and Zod validation

## Getting an API Key

Before using this MCP server, you need to obtain an API key from the ICP Coder backend.

**For detailed setup instructions**, including how to:
- Run the backend server (locally or use production)
- Register an account
- Generate your API key

Please refer to the [main repository README](https://github.com/Quantum3-Labs/icp-coder#readme) for complete setup instructions.

**Quick summary:**
1. Access the Swagger UI at `https://icp-coder.q3labs.io/swagger/index.html` (or your backend URL)
2. Register a new account
3. Login with your credentials
4. Generate an API key from the `/api/v1/keys` endpoint
5. Save the API key for use in your IDE configuration below

## Cursor Config

```json
{
  "mcpServers": {
    "icp-coder": {
      "command": "npx",
      "args": [
        "-y",
        "@quantum3labs/icp-coder"
      ],
      "env": {
        "API_KEY": "your-api-key-here",
        "BACKEND_URL": "https://icp-coder.q3labs.io"
      }
    }
  }
}
```

## Available Tools

### 1. `get_motoko_context`

Retrieves relevant Motoko code snippets and documentation from the RAG system.

### 2. `generate_motoko_code`

MIT License - see [LICENSE](https://github.com/Quantum3-Labs/icp-coder/blob/main/LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/Quantum3-Labs/icp-coder/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Quantum3-Labs/icp-coder/discussions)
- **Documentation**: [Project README](https://github.com/Quantum3-Labs/icp-coder#readme)
