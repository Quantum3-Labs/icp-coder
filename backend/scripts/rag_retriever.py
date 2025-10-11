#!/usr/bin/env python3
"""
RAG Retriever Script for Go Backend

This script interfaces with ChromaDB to retrieve relevant Motoko context from both
code samples and documentation. It reads JSON input from stdin and outputs JSON
results to stdout.

Input format:
{
  "query": "How to create an actor in Motoko?",
  "n_results": 5,
  "docs_results": 8
}

Output format:
{
  "code_contexts": ["actor MyActor { ... }", "..."],
  "code_metadata": [{"filename": "hello.mo", "rel_path": "hello_world/hello.mo"}, ...],
  "code_distances": [0.12, ...],
  "docs_contexts": ["Actors are the fundamental unit...", "..."],
  "docs_metadata": [{"source_file": "fundamentals/actors.md", "chunk_title": "Actors overview"}, ...],
  "docs_distances": [0.21, ...]
}
"""

import sys
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Disable ChromaDB telemetry to avoid version compatibility issues
os.environ["ANONYMIZED_TELEMETRY"] = "False"

try:
    import chromadb
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    error_msg = {
        "error": f"Missing required Python packages: {str(e)}. Please install chromadb and sentence-transformers."
    }
    print(json.dumps(error_msg), file=sys.stderr)
    sys.exit(1)


_MODEL: Optional[SentenceTransformer] = None


def get_chromadb_path() -> str:
    """Get the ChromaDB path from environment or use default."""
    chromadb_path = os.getenv("CHROMADB_PATH")
    if chromadb_path:
        return chromadb_path

    script_dir = Path(__file__).parent
    default_path = script_dir.parent / "data" / "chromadb"
    return str(default_path)


def get_sentence_transformer() -> SentenceTransformer:
    """Return a cached instance of the embedding model."""
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _MODEL


def query_collection(
    collection: Any,
    query_embedding: List[float],
    limit: int,
) -> Tuple[List[str], List[Dict[str, object]], List[float]]:
    """Query a ChromaDB collection and normalise the response."""
    results = collection.query(query_embeddings=[query_embedding], n_results=limit)

    documents = results.get("documents", [[]])[0] if results else []
    metadatas = results.get("metadatas", [[]])[0] if results else []
    distances = results.get("distances", [[]])[0] if results else []

    return documents, metadatas, distances


def retrieve_context(query: str, n_results: int = 5, docs_results: Optional[int] = None):
    """
    Retrieve relevant Motoko code context from ChromaDB

    Args:
        query: The user's query string
        n_results: Number of results to return

    Returns:
        Dictionary with contexts and metadata
    """
    try:
        # Initialize ChromaDB client
        chromadb_path = get_chromadb_path()

        if not os.path.exists(chromadb_path):
            return {
                "error": f"ChromaDB path does not exist: {chromadb_path}. Please run ingestion first."
            }

        client = chromadb.PersistentClient(path=chromadb_path)

        try:
            code_collection = client.get_collection(name="motoko_code_samples")
        except Exception:
            return {
                "error": "Collection 'motoko_code_samples' not found. Please run code ingestion first."
            }

        docs_collection = None
        docs_warning = None
        try:
            docs_collection = client.get_collection(name="motoko_docs")
        except Exception:
            docs_warning = "Collection 'motoko_docs' not found. Documentation results will be empty."

        model = get_sentence_transformer()
        query_embedding = model.encode(query).tolist()

        code_docs, code_metas, code_distances = query_collection(code_collection, query_embedding, n_results)

        docs_limit = docs_results if isinstance(docs_results, int) and docs_results > 0 else n_results
        doc_docs: List[str] = []
        doc_metas: List[Dict[str, object]] = []
        doc_distances: List[float] = []

        if docs_collection is not None:
            doc_docs, doc_metas, doc_distances = query_collection(docs_collection, query_embedding, docs_limit)

        response: Dict[str, object] = {
            "code_contexts": code_docs,
            "code_metadata": code_metas,
            "code_distances": code_distances,
            "docs_contexts": doc_docs,
            "docs_metadata": doc_metas,
            "docs_distances": doc_distances,
        }

        if docs_warning:
            response["warning"] = docs_warning

        return response

    except Exception as e:
        return {
            "error": f"Error during retrieval: {str(e)}"
        }


def main():
    """Main entry point - reads from stdin, writes to stdout"""
    try:
        # Read input from stdin
        input_data = sys.stdin.read()

        if not input_data.strip():
            error_response = {"error": "No input data provided"}
            print(json.dumps(error_response))
            sys.exit(1)

        # Parse JSON input
        try:
            request = json.loads(input_data)
        except json.JSONDecodeError as e:
            error_response = {"error": f"Invalid JSON input: {str(e)}"}
            print(json.dumps(error_response))
            sys.exit(1)

        # Validate required fields
        if "query" not in request:
            error_response = {"error": "Missing required field: query"}
            print(json.dumps(error_response))
            sys.exit(1)

        query = request["query"]
        n_results = request.get("n_results", 5)
        docs_results = request.get("docs_results")

        # Validate n_results
        if not isinstance(n_results, int) or n_results < 1 or n_results > 20:
            error_response = {"error": "n_results must be an integer between 1 and 20"}
            print(json.dumps(error_response))
            sys.exit(1)

        if docs_results is not None:
            if not isinstance(docs_results, int) or docs_results < 1 or docs_results > 20:
                error_response = {"error": "docs_results must be an integer between 1 and 20"}
                print(json.dumps(error_response))
                sys.exit(1)

        # Retrieve context
        result = retrieve_context(query, n_results, docs_results)

        # Output result as JSON
        print(json.dumps(result))

        # Exit with error code if there was an error
        if "error" in result:
            sys.exit(1)

    except Exception as e:
        error_response = {"error": f"Unexpected error: {str(e)}"}
        print(json.dumps(error_response), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
