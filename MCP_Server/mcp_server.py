#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Server for Motoko Coder
Provides RAG-powered context retrieval and Gemini-powered code generation for Cursor IDE
"""

import os
import json
import sys
import time
from typing import Dict, Any, List, Optional
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from dotenv import load_dotenv

# Try to import Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  Gemini SDK not available. Install with: pip install google-generativeai", file=sys.stderr)

# Load environment variables
load_dotenv()

# ChromaDB Setup - using relative path from API directory
CHROMA_DIR = "chromadb_data"
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# Gemini setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_AVAILABLE and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel("models/gemini-2.0-flash-exp")
    print(f"✅ Gemini model loaded: gemini-2.0-flash-exp", file=sys.stderr)
else:
    gemini_model = None
    print("⚠️  Gemini not configured. Set GEMINI_API_KEY environment variable.", file=sys.stderr)

try:
    collection = chroma_client.get_collection(
        name="motoko_code_samples", 
        embedding_function=embedding_fn
    )
    print(f"✅ ChromaDB collection loaded with {collection.count()} Motoko samples", file=sys.stderr)
except Exception as e:
    print(f"❌ Error accessing ChromaDB collection: {e}", file=sys.stderr)
    print("💡 Make sure to run the ingestion script first: python ingest/motoko_samples_ingester.py", file=sys.stderr)
    sys.exit(1)

class MCPServer:
    def __init__(self):
        self.tools = {
            "get_motoko_context": {
                "name": "get_motoko_context",
                "description": "Retrieve relevant Motoko code context for the given query using RAG",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The query or code context to search for relevant Motoko examples"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of context results to return (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            "generate_motoko_code": {
                "name": "generate_motoko_code",
                "description": "Generate Motoko code using Gemini with RAG context retrieval",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The user's request for Motoko code generation"
                        },
                        "max_context_results": {
                            "type": "integer",
                            "description": "Maximum number of context results to retrieve (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    
    def send_response(self, id: str, result: Any = None, error: Any = None):
        """Send a JSON-RPC response"""
        response = {
            "jsonrpc": "2.0",
            "id": id
        }
        
        if error:
            response["error"] = error
        else:
            response["result"] = result
        
        print(json.dumps(response))
        sys.stdout.flush()
    
    def handle_initialize(self, request_id: str, params: Dict[str, Any]):
        """Handle MCP initialize request"""
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "motoko-coder-mcp",
                "version": "1.0.0",
                "description": "MCP server for Motoko code generation with RAG context retrieval"
            }
        }
        self.send_response(request_id, result)
    
    def handle_tools_list(self, request_id: str):
        """Handle tools/list request"""
        tools_list = list(self.tools.values())
        self.send_response(request_id, {"tools": tools_list})
    
    def retrieve_motoko_context(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant Motoko code context using RAG"""
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
            
            # Format context results
            context_results = []
            for i, (doc, meta) in enumerate(zip(docs, metadatas)):
                context_result = {
                    "index": i + 1,
                    "filename": meta.get("filename", "unknown"),
                    "project": meta.get("folders", "unknown"),
                    "file_type": meta.get("file_type", "unknown"),
                    "has_toml": meta.get("has_toml", False),
                    "content": doc[:2000] + "..." if len(doc) > 2000 else doc,
                    "full_path": meta.get("rel_path", "unknown")
                }
                context_results.append(context_result)
            
            return context_results
        except Exception as e:
            print(f"❌ Error retrieving context: {e}", file=sys.stderr)
            return []
    
    def generate_code_with_gemini(self, query: str, context_results: List[Dict[str, Any]]) -> str:
        """Generate Motoko code using Gemini with RAG context"""
        if not gemini_model:
            return "❌ Gemini is not configured. Please set the GEMINI_API_KEY environment variable."
        
        try:
            # Format context for Gemini
            context_text = ""
            if context_results:
                context_text = "Here are relevant Motoko code examples:\n\n"
                for ctx in context_results:
                    context_text += f"**{ctx['filename']}** ({ctx['project']}):\n```motoko\n{ctx['content']}\n```\n\n"
            else:
                context_text = "No specific context found, but I'll help you with Motoko code generation.\n\n"
            
            # Create prompt for Gemini
            prompt = f"""You are an expert Motoko developer. Use the following context to help generate high-quality Motoko code.

{context_text}

User Request: {query}

Please provide:
1. A clear explanation of the solution
2. Complete, compilable Motoko code
3. Any important notes about the implementation

Focus on writing idiomatic Motoko code that follows best practices."""

            # Generate response with Gemini
            response = gemini_model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            print(f"❌ Error generating code with Gemini: {e}", file=sys.stderr)
            return f"❌ Error generating code: {str(e)}"
    
    def handle_tools_call(self, request_id: str, params: Dict[str, Any]):
        """Handle tools/call request"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "get_motoko_context":
            try:
                query = arguments.get("query", "")
                max_results = arguments.get("max_results", 5)
                
                if not query:
                    self.send_response(request_id, error={
                        "code": -32602,
                        "message": "Query parameter is required"
                    })
                    return
                
                # Retrieve context
                context_results = self.retrieve_motoko_context(query, max_results)
                
                # Format response for Cursor
                formatted_context = f"Retrieved {len(context_results)} relevant Motoko code samples for: '{query}'\n\n"
                for ctx in context_results:
                    formatted_context += f"**{ctx['filename']}** ({ctx['project']}):\n```motoko\n{ctx['content']}\n```\n\n"
                
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": formatted_context.strip()
                        }
                    ]
                }
                
                self.send_response(request_id, result)
                
            except Exception as e:
                print(f"❌ Error in get_motoko_context: {e}", file=sys.stderr)
                self.send_response(request_id, error={
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                })
        
        elif tool_name == "generate_motoko_code":
            try:
                query = arguments.get("query", "")
                max_context_results = arguments.get("max_context_results", 5)
                
                if not query:
                    self.send_response(request_id, error={
                        "code": -32602,
                        "message": "Query parameter is required"
                    })
                    return
                
                # Retrieve context first
                context_results = self.retrieve_motoko_context(query, max_context_results)
                
                # Generate code with Gemini
                generated_code = self.generate_code_with_gemini(query, context_results)
                
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": generated_code
                        }
                    ]
                }
                
                self.send_response(request_id, result)
                
            except Exception as e:
                print(f"❌ Error in generate_motoko_code: {e}", file=sys.stderr)
                self.send_response(request_id, error={
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                })
        
        else:
            self.send_response(request_id, error={
                "code": -32601,
                "message": f"Method '{tool_name}' not found"
            })
    
    def handle_notification(self, method: str, params: Dict[str, Any]):
        """Handle notifications (no response needed)"""
        if method == "notifications/initialized":
            print(f"🎉 MCP Server initialized successfully", file=sys.stderr)
    
    def run(self):
        """Main server loop - reads from stdin, writes to stdout"""
        print("🚀 Motoko Coder MCP Server starting...", file=sys.stderr)
        print(f"📚 ChromaDB: {collection.count()} Motoko samples available", file=sys.stderr)
        if gemini_model:
            print(f"🤖 Gemini: Ready for code generation", file=sys.stderr)
        else:
            print(f"⚠️  Gemini: Not configured", file=sys.stderr)
        
        while True:
            try:
                line = input()
                if not line.strip():
                    continue
                
                request = json.loads(line)
                request_id = request.get("id")
                method = request.get("method")
                params = request.get("params", {})
                
                print(f"📨 Received: {method}", file=sys.stderr)
                
                if method == "initialize":
                    self.handle_initialize(request_id, params)
                elif method == "tools/list":
                    self.handle_tools_list(request_id)
                elif method == "tools/call":
                    self.handle_tools_call(request_id, params)
                elif method.startswith("notifications/"):
                    self.handle_notification(method, params)
                else:
                    if request_id:
                        self.send_response(request_id, error={
                            "code": -32601,
                            "message": f"Method '{method}' not found"
                        })
                
            except EOFError:
                print("👋 Client disconnected", file=sys.stderr)
                break
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON: {e}", file=sys.stderr)
                continue
            except Exception as e:
                print(f"❌ Error: {e}", file=sys.stderr)
                continue

if __name__ == "__main__":
    server = MCPServer()
    server.run()