import os
import requests
from typing import Any, Dict, Tuple, Optional
from rag.inference_base import BaseInferenceStrategy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import the Gemini SDK
try:
    import google.generativeai as genai
    GEMINI_SDK_AVAILABLE = True
except ImportError:
    GEMINI_SDK_AVAILABLE = False

class GeminiStrategy(BaseInferenceStrategy):
    """Google Gemini inference strategy - self-configuring"""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        model_name = "models/gemini-2.5-flash"
        
        # Default Gemini configuration
        config = {
            "generation_config": {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 64,
                "max_output_tokens": 8192,
            },
            "use_sdk": True
        }
        
        super().__init__(api_key, model_name, config)
        
        self.generation_config = self.config["generation_config"]
        self.use_sdk = GEMINI_SDK_AVAILABLE and self.config.get("use_sdk", True)

    def count_tokens_gemini_sdk(self, model, prompt: str) -> Optional[int]:
        """Use the Gemini SDK to count tokens"""
        try:
            return model.count_tokens(prompt).total_tokens
        except Exception:
            return None

    def answer_with_gemini_sdk(self, query: str, retrieved_data: Dict[str, Any]) -> Tuple[str, Optional[int]]:
        """Generate answer using Gemini SDK"""
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model_name, generation_config=self.generation_config)
        prompt = self.build_context_prompt(retrieved_data, query)
        num_tokens = self.count_tokens_gemini_sdk(model, prompt)
        response = model.generate_content(prompt)
        return response.text, num_tokens

    def answer_with_gemini_rest(self, query: str, retrieved_data: Dict[str, Any]) -> Tuple[str, Optional[int]]:
        """Generate answer using Gemini REST API"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}
        prompt = self.build_context_prompt(retrieved_data, query)
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": self.generation_config,
        }
        resp = requests.post(url, headers=headers, params=params, json=data)
        if resp.ok:
            # Gemini REST API does not return token count directly
            answer = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            return answer, None
        else:
            return f"Gemini API error: {resp.text}", None

    def make_api_call(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Gemini-specific API call implementation"""
        try:
            query = request_data.get("query", "")
            
            # Retrieve context using inherited method
            retrieved_data = self.retrieve_context(query)
            
            # Generate response
            if self.use_sdk and GEMINI_SDK_AVAILABLE:
                answer, num_tokens = self.answer_with_gemini_sdk(query, retrieved_data)
                token_info = f"Token count: {num_tokens}" if num_tokens else "Token count: SDK available"
            else:
                answer, _ = self.answer_with_gemini_rest(query, retrieved_data)
                token_info = "Token count: Not available (using REST API)"
            
            return {
                "response": answer,
                "model": self.model_name,
                "token_info": token_info,
                "retrieved_context": {
                    "doc_count": len(retrieved_data.get("doc_docs", [])),
                    "code_count": len(retrieved_data.get("code_docs", []))
                }
            }
            
        except Exception as e:
            return {
                "error": f"Gemini API call failed: {str(e)}",
                "model": self.model_name
            }

    def prepare_request_data(self, prompt: str) -> Dict[str, Any]:
        """Prepare request data for Gemini API call"""
        return {
            "query": prompt,
            "model": self.model_name,
            "config": self.generation_config
        }