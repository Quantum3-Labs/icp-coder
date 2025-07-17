#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Server for Motoko Coder
Provides RAG context retrieval for Cursor and VS Code LLM enhancement
"""

import json
import asyncio
import sys
from typing import Dict, List, Any, Optional
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import os
from database import validate_api_key

# ChromaDB setup
CHROMA_DIR = os.path.join(os.getcwd(), "chromadb_data")
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = chroma_client.get_or_create_collection("motoko_code_samples")
embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

class MotokoCoderMCPServer:
    """MCP Server for Motoko Coder RAG context retrieval."""
    
    def __init__(self):
        self.server_name = "motoko-coder-mcp"
        self.version = "1.0.0"
        self.capabilities = {
            "tools": {
                "listChanged": False,
                "listRequired": False
            }
        }
    
    def get_motoko_context(self, query: str, api_key: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Retrieve relevant Motoko code context based on user query, with API key validation.
        """
        # Validate API key
        valid, user_id, message = validate_api_key(api_key)
        if not valid:
            return {
                "success": False,
                "error": "Invalid API key",
                "message": message
            }
        try:
            # Generate query embedding
            query_emb = embedding_fn([query])[0]
            # Search for relevant documents
            results = collection.query(
                query_embeddings=[query_emb], 
                n_results=max_results
            )
            docs = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            # Format context for MCP
            context_parts = []
            for i, (doc, meta) in enumerate(zip(docs, metadatas)):
                context_part = {
                    "index": i + 1,
                    "filename": meta.get("filename", "unknown"),
                    "project": meta.get("folders", "unknown"),
                    "file_type": meta.get("file_type", "unknown"),
                    "has_toml": meta.get("has_toml", False),
                    "content": doc[:1000] + "..." if len(doc) > 1000 else doc,
                    "full_path": meta.get("rel_path", "unknown")
                }
                context_parts.append(context_part)
            return {
                "success": True,
                "query": query,
                "context_count": len(context_parts),
                "context": context_parts,
                "message": f"Retrieved {len(context_parts)} relevant Motoko code samples"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to retrieve Motoko context"
            }
    
    async def handle_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP protocol requests."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": self.capabilities,
                    "serverInfo": {
                        "name": self.server_name,
                        "version": self.version
                    }
                }
            }
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "get_motoko_context",
                            "description": "Retrieve relevant Motoko code context based on user query (API key required)",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "User's question or code request about Motoko"
                                    },
                                    "api_key": {
                                        "type": "string",
                                        "description": "API key for authentication"
                                    },
                                    "max_results": {
                                        "type": "integer",
                                        "description": "Maximum number of relevant code samples to return (default: 5)",
                                        "default": 5
                                    }
                                },
                                "required": ["query", "api_key"]
                            }
                        }
                    ]
                }
            }
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            if tool_name == "get_motoko_context":
                query = arguments.get("query", "")
                api_key = arguments.get("api_key", "")
                max_results = arguments.get("max_results", 5)
                result = self.get_motoko_context(query, api_key, max_results)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method '{tool_name}' not found"
                    }
                }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method '{method}' not found"
                }
            }

async def main():
    """Main MCP server loop."""
    server = MotokoCoderMCPServer()
    # Read from stdin, write to stdout (MCP protocol)
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
    writer = asyncio.StreamWriter(
        asyncio.get_event_loop().connect_write_pipe(
            lambda: asyncio.StreamReaderProtocol(asyncio.StreamReader()),
            sys.stdout
        ).transport,
        None,
        None
    )
    while True:
        try:
            # Read request from stdin
            line = await reader.readline()
            if not line:
                break
            request = json.loads(line.decode().strip())
            response = await server.handle_mcp_request(request)
            # Write response to stdout
            writer.write((json.dumps(response) + "\n").encode())
            await writer.drain()
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            writer.write((json.dumps(error_response) + "\n").encode())
            await writer.drain()

if __name__ == "__main__":
    asyncio.run(main()) 