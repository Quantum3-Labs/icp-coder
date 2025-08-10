# Motoko Coder MCP Server

A clean, simple MCP (Model Context Protocol) server that provides RAG-powered context retrieval and Gemini-powered code generation for Motoko development in Cursor IDE.

## Features

- **RAG Context Retrieval**: Uses sentence transformers to find relevant Motoko code examples
- **Gemini Code Generation**: Generates high-quality Motoko code using retrieved context
- **MCP Protocol**: Follows the Model Context Protocol for seamless Cursor integration
- **Simple Setup**: No complex API servers or authentication - just pure MCP functionality

## Prerequisites

1. **Python Environment**: Python 3.8+ with virtual environment
2. **ChromaDB Data**: Must have ingested Motoko code samples
3. **Gemini API Key**: For code generation (optional but recommended)

## Installation

1. **Install Dependencies**:
   ```bash
   pip install chromadb sentence-transformers google-generativeai python-dotenv
   ```

2. **Set Environment Variables**:
   ```bash
   # Create .env file in project root
   echo "GEMINI_API_KEY=your_gemini_api_key_here" > .env
   ```

3. **Ensure ChromaDB Data**:
   ```bash
   # Run the ingestion script first
   python ingest/motoko_samples_ingester.py
   ```

## Cursor IDE Setup

### Option 1: Direct Configuration

1. Open Cursor IDE
2. Go to **Settings** (Cmd/Ctrl + ,)
3. Search for "MCP" or "Model Context Protocol"
4. Add this configuration:

```json
{
  "mcpServers": {
    "motoko-coder": {
      "command": "python",
      "args": ["/path/to/your/ICP_Coder/API/mcp_server.py"],
      "env": {
        "PYTHONPATH": "/path/to/your/ICP_Coder"
      }
    }
  }
}
```

**Replace `/path/to/your/ICP_Coder` with your actual project path.**

### Option 2: Configuration File

1. Copy the `mcp_config.json` file to your Cursor configuration directory
2. In Cursor settings, specify the path to your MCP config file:

```json
{
  "mcp.configPath": "/path/to/your/ICP_Coder/API/mcp_config.json"
}
```

## Available Tools

### 1. `get_motoko_context`

Retrieves relevant Motoko code examples based on a query.

**Input**:
- `query` (string): What you're looking for
- `max_results` (integer, optional): Number of results (default: 5)

**Use Case**: When you need to see examples of similar Motoko code patterns.

### 2. `generate_motoko_code`

Generates complete Motoko code using Gemini with RAG context.

**Input**:
- `query` (string): Your code generation request
- `max_context_results` (integer, optional): Context examples to use (default: 5)

**Use Case**: When you want to generate new Motoko code with context-aware assistance.

## Testing

Run the test script to verify everything works:

```bash
cd API
python test_mcp.py
```

## Usage in Cursor

1. **Restart Cursor** after adding the MCP server
2. **Open a Motoko file** (`.mo` extension)
3. **Use Cursor's AI features** - the MCP server will automatically provide:
   - Context-aware code completions
   - Relevant Motoko examples
   - Enhanced code generation

## How It Works

1. **User Query**: You ask for help with Motoko code
2. **Context Retrieval**: Server searches ChromaDB for relevant examples
3. **Gemini Generation**: Uses retrieved context to generate better code
4. **Response**: Returns context and/or generated code to Cursor

## Troubleshooting

### Issue: "ChromaDB collection not found"
**Solution**: Run the ingestion script first:
```bash
python ingest/motoko_samples_ingester.py
```

### Issue: "Gemini not configured"
**Solution**: Set your Gemini API key in the `.env` file:
```bash
echo "GEMINI_API_KEY=your_key_here" > .env
```

### Issue: MCP server not starting
**Solution**: Check Python path and dependencies:
```bash
cd API
python -c "import chromadb, google.generativeai; print('Dependencies OK')"
```

### Issue: Cursor not recognizing tools
**Solution**: 
1. Restart Cursor IDE
2. Check the MCP configuration syntax
3. Verify the Python path is correct

## Architecture

```
User Query → MCP Server → RAG Context Retrieval → Gemini Code Generation → Response
                ↓
            ChromaDB (Motoko samples)
                ↓
        Sentence Transformer Embeddings
```

## Development

The server is built with simplicity in mind:
- **Single file**: `mcp_server.py` contains everything
- **No external dependencies**: Just ChromaDB and Gemini
- **MCP compliant**: Follows the Model Context Protocol specification
- **Error handling**: Graceful fallbacks and clear error messages

## Next Steps

1. **Test the setup** with the provided test script
2. **Configure Cursor** using one of the setup options
3. **Start coding** with enhanced Motoko assistance
4. **Customize prompts** in the `generate_code_with_gemini` method if needed

---

**Your Motoko development experience in Cursor is now enhanced with RAG-powered context and Gemini code generation!** 🚀 