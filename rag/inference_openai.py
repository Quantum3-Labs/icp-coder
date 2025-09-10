import os
import openai
from typing import Any, Dict, Tuple, Optional
from rag.inference_base import BaseInferenceStrategy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OpenAIStrategy(BaseInferenceStrategy):
    """OpenAI inference strategy - self-configuring"""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        model_name = "gpt-3.5-turbo"
        
        config = {
            "max_tokens": 512,
            "system_message": "You are a Motoko expert."
        }
        
        super().__init__(api_key, model_name, config)

    def make_api_call(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """OpenAI-specific API call implementation"""
        try:
            query = request_data.get("query", "")
            
            # Retrieve context using inherited method
            retrieved_data = self.retrieve_context(query)
            
            # Build prompt with context
            prompt = self.build_context_prompt(retrieved_data, query)
            
            # Set API key
            openai.api_key = self.api_key
            
            # Make OpenAI API call
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.config["system_message"]},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config["max_tokens"]
            )
            
            answer = response.choices[0].message["content"].strip()
            
            return {
                "response": answer,
                "model": self.model_name,
                "token_info": f"Max tokens: {self.config['max_tokens']}",
                "retrieved_context": {
                    "doc_count": len(retrieved_data.get("doc_docs", [])),
                    "code_count": len(retrieved_data.get("code_docs", []))
                }
            }
            
        except Exception as e:
            return {
                "error": f"OpenAI API call failed: {str(e)}",
                "model": self.model_name
            }

    def prepare_request_data(self, prompt: str) -> Dict[str, Any]:
        """Prepare request data for OpenAI API call"""
        return {
            "query": prompt,
            "model": self.model_name,
            "config": self.config
        }