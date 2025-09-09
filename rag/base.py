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


def retrieve_context(query, code_results=5, docs_results=8):
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


def build_context_prompt(retrieved_data, query, system_message=None):
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
