# RAG Inference Pipeline

This directory contains scripts for Retrieval-Augmented Generation (RAG) using Motoko code samples and supports inference with OpenAI, Gemini, and Claude LLMs.

## Setup

1. **Install dependencies:**

```bash
pip install -r ../requirements.txt
pip install python-dotenv openai requests
```

2. **Create a `.env` file in the project root:**

```
OPENAI_API_KEY=your-openai-key-here
GEMINI_API_KEY=your-gemini-key-here
CLAUDE_API_KEY=your-claude-key-here
```

3. **Ensure you have a ChromaDB database built from Motoko samples.**
   - Use the `ingest/ingest_motoko_samples.py` script to populate `chromadb_data`.

## Usage

Run the inference script:

```bash
python rag/inference.py
```

You will be prompted for a Motoko-related question. The script will:
- Retrieve relevant Motoko code samples from ChromaDB.
- Query OpenAI, Gemini, and Claude LLMs with the context.
- Print the responses from each LLM.

## Notes
- Make sure your API keys are valid and have sufficient quota.
- The script uses the `all-MiniLM-L6-v2` embedding model for retrieval.
- For Gemini and Claude, you may need to check their latest API docs for any changes in endpoints or payloads. 