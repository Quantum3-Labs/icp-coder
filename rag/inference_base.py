from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import json
import sqlite3
from datetime import datetime
import os
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ChromaDB setup
CHROMA_DIR = os.path.join(os.getcwd(), "chromadb_data")
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
code_collection = chroma_client.get_or_create_collection("motoko_code_samples")
docs_collection = chroma_client.get_or_create_collection("motoko_docs")

# Embedding function for retrieval
embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

class BaseInferenceStrategy(ABC):
    """Abstract base class for AI inference strategies"""
    
    def __init__(self, api_key: str, model_name: str, config: Dict[str, Any] = None):
        self.api_key = api_key
        self.model_name = model_name
        self.config = config or {}
        self.db_connection = None
    
    def get_name(self) -> str:
        return self.__class__.__name__.replace('Strategy', '')
    
    @abstractmethod
    def make_api_call(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Abstract method for making API calls - implemented differently by each provider"""
        pass
    
    def retrieve_context(self, query: str, code_results: int = 5, docs_results: int = 8) -> Dict[str, Any]:
        """Retrieve context from both code samples and documentation."""
        query_emb = embedding_fn([query])[0]

        # Retrieve from code samples
        code_results_data = code_collection.query(
            query_embeddings=[query_emb], n_results=code_results
        )
        code_docs = code_results_data.get("documents", [[]])[0]
        code_metas = code_results_data.get("metadatas", [[]])[0]
        code_distances = code_results_data.get("distances", [[]])[0]

        # Retrieve from documentation
        docs_results_data = docs_collection.query(
            query_embeddings=[query_emb], n_results=docs_results
        )
        doc_docs = docs_results_data.get("documents", [[]])[0]
        doc_metas = docs_results_data.get("metadatas", [[]])[0]
        doc_distances = docs_results_data.get("distances", [[]])[0]

        return {
            "code_docs": code_docs,
            "code_metas": code_metas,
            "code_distances": code_distances,
            "doc_docs": doc_docs,
            "doc_metas": doc_metas,
            "doc_distances": doc_distances,
        }

    def build_context_prompt(self, retrieved_data: Dict[str, Any], query: str, system_message: str = None) -> str:
        """Build a comprehensive context prompt from retrieved data."""
        context_parts = []

        # Add documentation context
        if retrieved_data["doc_docs"]:
            context_parts.append("=== MOTOKO DOCUMENTATION ===")
            doc_results = list(
                zip(
                    retrieved_data["doc_docs"],
                    retrieved_data["doc_metas"],
                    retrieved_data["doc_distances"],
                )
            )
            doc_results.sort(key=lambda x: x[2])  # Sort by distance (lower = more relevant)

            for i, (doc, meta, distance) in enumerate(doc_results[:5]):  # Top 5 docs
                similarity = 1 - distance if distance <= 1 else 0
                context_parts.append(
                    f"[DOC {i+1}] {meta.get('chunk_title', 'Untitled')} (Relevance: {similarity:.3f})"
                )
                context_parts.append(f"Source: {meta.get('source_file', 'Unknown')}")
                if meta.get("parent_context"):
                    context_parts.append(f"Context: {meta.get('parent_context')}")
                context_parts.append(doc)
                context_parts.append("")

        # Add code examples context
        if retrieved_data["code_docs"]:
            context_parts.append("=== MOTOKO CODE EXAMPLES ===")
            code_results = list(
                zip(
                    retrieved_data["code_docs"],
                    retrieved_data["code_metas"],
                    retrieved_data["code_distances"],
                )
            )
            code_results.sort(key=lambda x: x[2])  # Sort by distance

            for i, (code, meta, distance) in enumerate(
                code_results[:3]
            ):  # Top 3 code examples
                similarity = 1 - distance if distance <= 1 else 0
                context_parts.append(
                    f"[CODE {i+1}] {meta.get('filename', 'Unknown')} (Relevance: {similarity:.3f})"
                )
                context_parts.append(f"Path: {meta.get('rel_path', 'Unknown')}")
                context_parts.append(code)
                context_parts.append("")

        context = "\n".join(context_parts)

        # Use provided system message or default
        default_system_message = """You are an expert Motoko programmer and teacher. Use the provided documentation and code examples to answer the user's question accurately and comprehensively."""

        system_msg = system_message or default_system_message

        # Create the full prompt
        prompt = f"""{system_msg}

{context}

User Question: {query}

Instructions:
- Provide a clear, accurate answer based on the documentation and code examples above
- Include relevant code snippets when helpful
- Reference the documentation sources when appropriate
- If the question can't be fully answered from the provided context, mention what additional information might be needed

Answer:"""

        return prompt

    def prepare_request_data(self, prompt: str) -> Dict[str, Any]:
        """Prepare request data for API call - can be overridden by subclasses"""
        return {
            "query": prompt,
            "model": self.model_name,
            "config": self.config
        }

    def process(self, prompt: str) -> Dict[str, Any]:
        """Main method that orchestrates the inference process"""
        try:
            request_data = self.prepare_request_data(prompt)
            
            response = self.make_api_call(request_data)
            
            return response
            
        except Exception as e:
            raise

# Context class for managing different inference strategies
class InferenceContext:
    def __init__(self, strategy: BaseInferenceStrategy):
        self._strategy = strategy
    
    def generate_response(self, prompt: str) -> Dict[str, Any]:
        return self._strategy.process(prompt)
    
    def retrieve_context(self, query: str, code_results: int = 5, docs_results: int = 8) -> Dict[str, Any]:
        """Retrieve context without calling any generation strategy"""
        return self._strategy.retrieve_context(query, code_results, docs_results)