# mcp_server.py
import os
import json
import time
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ChromaDB Setup
CHROMA_DIR = os.path.join(os.getcwd(), "chromadb_data")
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

try:
    collection = chroma_client.get_collection(
        name="motoko_code_samples", 
        embedding_function=embedding_fn
    )
    print(f"✅ ChromaDB collection loaded with {collection.count()} Motoko samples")
except Exception as e:
    print(f"❌ Error accessing ChromaDB collection: {e}")
    exit(1)

# Gemini 2.5 Flash Setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ Gemini API key not found in environment variables")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)
print("🔌 Connected to Gemini API")

# Gemini model configuration
GEMINI_MODEL = "models/gemini-2.5-flash"
GEMINI_CONFIG = {
    "temperature": 0.7,
    "max_output_tokens": 8192,
    "top_p": 0.95,
    "top_k": 40
}

def generate_completion_with_context(prompt: str, max_contexts=3) -> str:
    """Generate completion using Gemini with RAG context"""
    try:
        # Retrieve relevant context from ChromaDB
        results = collection.query(
            query_texts=[prompt],
            n_results=max_contexts
        )
        
        # Extract documents and format context
        context_docs = results['documents'][0] if results['documents'] else []
        context = "\n\n".join([f"// Reference {i+1}:\n{doc}" for i, doc in enumerate(context_docs)])
        
        # Create the full prompt
        full_prompt = f"""
        You are an expert Motoko developer. Below are relevant code snippets:
        
        {context}
        
        Provide a concise code completion for:
        {prompt}
        
        Return ONLY the completion code without explanations.
        """
        
        # Call Gemini API
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(**GEMINI_CONFIG)
        )
        
        # Clean up Gemini response
        completion_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if completion_text.startswith("```motoko"):
            completion_text = re.sub(r'^```motoko\s*', '', completion_text, flags=re.IGNORECASE)
            completion_text = re.sub(r'\s*```\s*$', '', completion_text)
        
        return completion_text
    
    except Exception as e:
        print(f"⚠️ Error generating completion: {e}")
        return ""

class MCPHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_OPTIONS(self):
        self._set_headers()
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            json_data = json.loads(post_data)
        except json.JSONDecodeError:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
            return
        
        # Handle different MCP endpoints
        if self.path == '/v1/initialize':
            print("🔧 Received initialize request")
            self._handle_initialize()
        elif self.path == '/v1/completions':
            self._handle_completions(json_data)
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())
    
    def _handle_initialize(self):
        """Handle Copilot initialization request"""
        response = {
            "result": {
                "name": "Motoko Assistant",
                "version": "1.0",
                "capabilities": {
                    "completions": True,
                    "completionsInline": True,
                    "dynamicRegistration": True
                }
            }
        }
        self._set_headers()
        self.wfile.write(json.dumps(response).encode())
        print("⚡ Initialized successfully")
    
    def _handle_completions(self, data):
        """Handle completion requests"""
        start_time = time.time()
        # Extract Copilot request data
        prompt = data.get('prompt', '')
        language_id = data.get('languageId', '')
        
        # Only process Motoko code
        if language_id.lower() != 'motoko':
            self._set_headers()
            self.wfile.write(json.dumps({"completions": []}).encode())
            return
        
        # Generate completion with RAG context
        completion_text = generate_completion_with_context(prompt)
        
        if not completion_text:
            self._set_headers()
            self.wfile.write(json.dumps({"completions": []}).encode())
            return
        
        # Format completion for MCP
        completions = [{
            "text": completion_text,
            "displayText": self._format_display_text(completion_text),
            "uuid": self._generate_uuid(),
        }]
        
        latency = int((time.time() - start_time) * 1000)
        print(f"⏱️ Processed completion in {latency}ms | Prompt: {prompt[:50]}...")
        
        self._set_headers()
        self.wfile.write(json.dumps({"completions": completions}).encode())
    
    def _format_display_text(self, text: str) -> str:
        """Extract the first line for display purposes"""
        return text.split('\n')[0][:50] + "..." if len(text) > 50 else text
    
    def _generate_uuid(self) -> str:
        """Generate a simple UUID for completion items"""
        return f"uuid-{int(time.time() * 1000)}"

def run_server(port=9000):
    server = HTTPServer(('localhost', port), MCPHandler)
    print(f"\n⚡ MCP Server running on http://localhost:{port}")
    print("🚀 Ready for Copilot integration")
    print("🔧 Endpoints:")
    print(f"  - POST /v1/initialize")
    print(f"  - POST /v1/completions")
    server.serve_forever()

if __name__ == '__main__':
    run_server()