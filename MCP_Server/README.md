# Motoko Coder MCP Server

A clean, simple MCP (Model Context Protocol) server that provides RAG-powered context retrieval and Gemini-powered code generation for Motoko development in Cursor IDE.

## Features

- **RAG Context Retrieval**: Uses sentence transformers to find relevant Motoko code examples
- **Gemini Code Generation**: Generates high-quality Motoko code using retrieved context
- **MCP Protocol**: Follows the Model Context Protocol for seamless Cursor integration

## Prerequisites

1. **Python Environment**: Python 3.8+ with virtual environment
2. **ChromaDB Data**: Must have ingested Motoko code samples
3. **Gemini API Key**: Required for code generation used in `generate_motoko_code`
4. **API Key from ICP_Coder**: Required for authentication to use the MCP server
## Installation

1. **Install Dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
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

4. **Start Authentication server**
   ``` bash
   # Terminal 1: Authentication server (port 8001)
   set PYTHONPATH=.
   python -m uvicorn API.auth_server:app --reload --port 8001
   ```
5. **Register a new account**
```bash
curl -X POST 'http://localhost:8001/register' \
-H "Content-Type: application/json" \
-d '{"username": "your_username", "password": "your_password", "email":"your_email@gmail.com}'
```
6. **Register a new account**
- Request:
```bash
curl -X POST 'http://localhost:8001/login' \
-H "Content-Type: application/json" \
-d '{"username": "your_username", "password": "your_password"'
```
- Response:
```json
{
   "success": true,
   "message": "Authentication successful",
   "user_id": 4,
   "username": "your_username",
   "access_token": "YOUR_ACCESS_TOKEN",
   "token_type": "bearer"
}
```
7. **Get API key**
- Request:
```bash
curl -X POST 'http://localhost:8001/api-keys' \
-H "Content-Type: application/json" \
-H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \ 
-d '{"name": "your_api_key_name"'} #Copy your access token from step 6
```
- Response:
```json
{
   "success": true,
   "message": "API key created successfully",
   "api_key": "YOUR_API_KEY",
   "name": "your_api_key_name"
}
```
## Cursor IDE Setup

### Configuration File

1. Go to cursor setting, in the `MCP & Integrations` section. Add `New MCP Server`
2. Copy `mcp_server_config_example.json` to `mcp.json` in Cursor to set up the new MCP server.
3. Replace `YOUR_API_KEY` with the API key generated in the installation step above.

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

## Available Tools

### 1. `get_motoko_context`

Retrieves relevant Motoko code examples based on a query.

**Use Case**: When you need to see examples of similar Motoko code patterns.

### 2. `generate_motoko_code`

Generates complete Motoko code using Gemini with RAG context.

**Use Case**: When you want to generate new Motoko code with context-aware assistance.

## Usage in Cursor

1. **Restart Cursor** after adding the MCP server
2. **Open a Motoko file** (`.mo` extension)
3. **Use Cursor's AI features** - the MCP server will automatically provide:
   - Context-aware code completions
   - Relevant Motoko examples
   - Enhanced code generation

## How It Works

1. **User Query**: You ask for help with Motoko code, mentioning the MCP tool you want to use.
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
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Issue: Cursor not recognizing tools
**Solution**: 
1. Restart Cursor IDE
2. Check the MCP server
3. Verify that your api key is correct

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
- **Single file**: `server.py` contains everything
- **No external dependencies**: Just ChromaDB and Gemini
- **MCP compliant**: Follows the Model Context Protocol specification
- **Error handling**: Graceful fallbacks and clear error messages

## Next Steps

1. **Test the setup** with the provided test script
2. **Configure Cursor** using one of the setup options
3. **Start coding** with enhanced Motoko assistance
4. **Customize prompts** in the `generate_code_with_gemini` tool if needed

---

**Your Motoko development experience in Cursor is now enhanced with RAG-powered context and Gemini code generation!** 🚀 