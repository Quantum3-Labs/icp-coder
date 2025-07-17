# Motoko Coder MCP Server Specification

## Overview

The Motoko Coder MCP (Model Context Protocol) Server provides RAG (Retrieval-Augmented Generation) context retrieval for Cursor and VS Code. Unlike the full API server that generates code, this MCP server focuses solely on providing relevant Motoko code context to enhance the LLMs in these editors.

## Purpose

- **Enhance LLM Context**: Provide relevant Motoko code samples to Cursor/VS Code LLMs
- **RAG Integration**: Use the same vector database and embedding model as the main system
- **Lightweight**: Single endpoint focused on context retrieval only
- **MCP Compliance**: Follows the Model Context Protocol standard

## Server Details

- **Name**: `motoko-coder-mcp`
- **Version**: `1.0.0`
- **Protocol**: MCP (Model Context Protocol) v2024-11-05
- **Communication**: JSON-RPC over stdin/stdout
- **Language**: Python 3.9+

## Single Endpoint: `get_motoko_context`

### Description
Retrieves relevant Motoko code context based on user queries using semantic search.

### Input Schema
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "User's question or code request about Motoko"
    },
    "max_results": {
      "type": "integer",
      "description": "Maximum number of relevant code samples to return (default: 5)",
      "default": 5
    }
  },
  "required": ["query"]
}
```

### Example Request
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "get_motoko_context",
    "arguments": {
      "query": "How do I write a counter canister in Motoko?",
      "max_results": 3
    }
  }
}
```

### Response Format
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\n  \"success\": true,\n  \"query\": \"How do I write a counter canister in Motoko?\",\n  \"context_count\": 3,\n  \"context\": [\n    {\n      \"index\": 1,\n      \"filename\": \"Main.mo\",\n      \"project\": \"counter\",\n      \"file_type\": \"motoko\",\n      \"has_toml\": true,\n      \"content\": \"actor Counter {\n  private stable var count : Nat = 0;\n  \n  public shared query func get() : async Nat {\n    count\n  };\n  \n  public shared func inc() : async () {\n    count += 1;\n  };\n}...\",\n      \"full_path\": \"counter/src/Main.mo\"\n    },\n    {\n      \"index\": 2,\n      \"filename\": \"mops.toml\",\n      \"project\": \"counter\",\n      \"file_type\": \"toml\",\n      \"has_toml\": true,\n      \"content\": \"[package]\nname = \"counter\"\nversion = \"0.1.0\"\n...\",\n      \"full_path\": \"counter/mops.toml\"\n    }\n  ],\n  \"message\": \"Retrieved 3 relevant Motoko code samples\"\n}"
      }
    ]
  }
}
```

## Context Response Structure

Each context item contains:

- **index**: Sequential number (1-based)
- **filename**: Name of the file
- **project**: Project directory name
- **file_type**: Either "motoko" or "toml"
- **has_toml**: Boolean indicating if project has TOML configuration
- **content**: File content (truncated to 1000 characters if longer)
- **full_path**: Relative path from motoko_code_samples directory

## Integration with Cursor

### 1. Install MCP Server
```bash
# Clone the repository and install dependencies
git clone <your-repo>
cd ICP_Coder
pip install -r requirements.txt
```

### 2. Configure Cursor MCP
In Cursor Settings → MCP Tools, add:

```json
{
  "mcpServers": {
    "motoko coder": {
      "command": "python",
      "args": ["API/mcp_server.py"],
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

### 3. Create Cursor Rule
In Cursor Settings → Rules, create a new rule:

```markdown
# Motoko Development with RAG Context

## Introduction
This rule enables Motoko development with enhanced context from the Motoko Coder RAG system.

## Usage
- When working with Motoko code, the MCP server will automatically provide relevant context
- Use the `get_motoko_context` tool to retrieve specific Motoko code examples
- Context includes both code files and TOML configurations

## Best Practices
- Ask specific questions about Motoko patterns and implementations
- The system provides real code examples from the motoko_code_samples collection
- Use the context to understand project structure and dependencies
```

## Integration with VS Code

### 1. Install MCP Extension
Install the MCP extension for VS Code.

### 2. Configure MCP Server
Add to VS Code settings:

```json
{
  "mcp.servers": {
    "motoko-coder": {
      "command": "python",
      "args": ["API/mcp_server.py"],
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

## Usage Examples

### Example 1: Basic Context Retrieval
```json
{
  "query": "How to implement a simple counter canister?",
  "max_results": 2
}
```

### Example 2: Project-Specific Query
```json
{
  "query": "Show me examples of DAO implementations in Motoko",
  "max_results": 5
}
```

### Example 3: Configuration Query
```json
{
  "query": "What are common dependencies in Motoko projects?",
  "max_results": 3
}
```

## Technical Implementation

### Dependencies
- **ChromaDB**: Vector database for similarity search
- **SentenceTransformer**: all-MiniLM-L6-v2 for embeddings
- **asyncio**: Async I/O for MCP protocol handling

### Data Flow
1. **Query Input**: User question via MCP protocol
2. **Embedding**: Convert query to vector using SentenceTransformer
3. **Search**: Find similar documents in ChromaDB
4. **Format**: Structure response with metadata and content
5. **Return**: JSON response via MCP protocol

### Error Handling
- Invalid queries return error responses
- Database connection issues are handled gracefully
- Malformed requests return appropriate error codes

## Benefits

1. **Enhanced LLM Context**: Provides real Motoko code examples
2. **Project Awareness**: Includes TOML configurations and project structure
3. **Semantic Search**: Finds relevant code based on meaning, not just keywords
4. **Lightweight**: Focused on context retrieval only
5. **Standard Protocol**: Uses MCP for easy integration

## Limitations

- **Context Only**: Does not generate code, only provides context
- **Local Database**: Requires ChromaDB to be populated with code samples
- **Single Tool**: Only provides one endpoint (get_motoko_context)
- **Content Truncation**: Long files are truncated to 1000 characters

## Future Enhancements

- **Multiple Tools**: Add more specialized context retrieval tools
- **Filtering Options**: Add filters for file types, projects, etc.
- **Full Content**: Option to retrieve full file contents
- **Caching**: Implement response caching for better performance 