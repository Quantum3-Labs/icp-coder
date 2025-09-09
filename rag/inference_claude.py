import os
import requests
from typing import Any, Dict, Tuple, Optional
from rag.inference_base import BaseInferenceStrategy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ClaudeStrategy(BaseInferenceStrategy):
    """Anthropic Claude inference strategy - self-configuring"""

    def __init__(self):
        api_key = os.getenv("CLAUDE_API_KEY")
        if not api_key:
            raise ValueError("CLAUDE_API_KEY not found in environment variables")
        
        model_name = "claude-3-opus-20240229"
        
        config = {
            "max_tokens": 512,
            "anthropic_version": "2023-06-01"
        }
        
        super().__init__(api_key, model_name, config)
        
        self.base_url = "https://api.anthropic.com/v1/messages"

    def make_api_call(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Claude-specific API call implementation"""
        try:
            query = request_data.get("query", "")
            
            # Retrieve context using inherited method
            retrieved_data = self.retrieve_context(query)
            
            # Build prompt with context
            prompt = self.build_context_prompt(retrieved_data, query)
            
            # Make Claude API call
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": self.config["anthropic_version"],
                "content-type": "application/json"
            }
            data = {
                "model": self.model_name,
                "max_tokens": self.config["max_tokens"],
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            resp = requests.post(self.base_url, headers=headers, json=data)
            
            if resp.ok:
                answer = resp.json()["content"][0]["text"]
                return {
                    "response": answer,
                    "model": self.model_name,
                    "token_info": f"Max tokens: {self.config['max_tokens']}",
                    "retrieved_context": {
                        "doc_count": len(retrieved_data.get("doc_docs", [])),
                        "code_count": len(retrieved_data.get("code_docs", []))
                    }
                }
            else:
                return {
                    "error": f"Claude API error: {resp.text}",
                    "model": self.model_name
                }
            
        except Exception as e:
            return {
                "error": f"Claude API call failed: {str(e)}",
                "model": self.model_name
            }

    def prepare_request_data(self, prompt: str) -> Dict[str, Any]:
        """Prepare request data for Claude API call"""
        return {
            "query": prompt,
            "model": self.model_name,
            "config": self.config
        }