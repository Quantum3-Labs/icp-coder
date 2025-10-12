# Backend Python Scripts

This directory contains Python scripts used by the Go backend for RAG operations and data ingestion.

## Scripts

### 1. `rag_retriever.py`
**Purpose**: Retrieves relevant Motoko code and documentation context from ChromaDB for RAG operations.

**Input** (via stdin):
```json
{
  "query": "How to create an actor in Motoko?",
  "n_results": 5,
  "docs_results": 8
}
```

**Output** (via stdout):
```json
{
  "code_contexts": ["actor MyActor { ... }", "..."],
  "code_metadata": [{"filename": "hello.mo", "rel_path": "hello_world/hello.mo"}, ...],
  "code_distances": [0.12, ...],
  "docs_contexts": ["Actors are the fundamental unit...", "..."],
  "docs_metadata": [{"source_file": "fundamentals/actors.md", "chunk_title": "Actors overview"}, ...],
  "docs_distances": [0.21, ...]
}
```

**Usage**:
- Called by the Go RAG service via subprocess
- Reads from stdin, writes to stdout
- Uses ChromaDB for vector similarity search
- Optional `docs_results` parameter controls documentation retrieval count (defaults to `n_results`)

**Manual Testing**:
```bash
cd backend

# Test with a query (requires ChromaDB data to exist)
echo '{"query": "How to create an actor in Motoko?", "n_results": 3, "docs_results": 6}' | python3 scripts/rag_retriever.py

# Test with different queries
echo '{"query": "HashMap usage examples", "n_results": 5}' | python3 scripts/rag_retriever.py

# Windows PowerShell
'{"query": "How to use async functions?", "n_results": 3, "docs_results": 6}' | python3 scripts/rag_retriever.py
```

**Prerequisites**:
- ChromaDB data must exist (run `make ingest` first)
- Python packages installed: `chromadb`, `sentence-transformers`

---

### 2. `clone_repos.py`
**Purpose**: Clones Motoko sample repositories from GitHub.

**Features**:
- Clones 40+ Motoko repositories
- Skips already cloned repos
- Shallow clones (--depth 1) for efficiency
- Timeout protection (60s per repo)

**Output Format** (JSON progress messages):
```json
{"type": "start", "total": 42}
{"type": "progress", "current": 1, "total": 42, "message": "Processing candid-spaces"}
{"type": "complete", "total_processed": 42, "cloned": 30, "skipped": 10, "failed": 2}
```

**Target Directory**: `backend/data/motoko_code_samples/`

---

### 3. `clone_docs.py`
**Purpose**: Clones the official Motoko documentation from GitHub.

**Features**:
- Clones from https://github.com/dfinity/motoko.git
- Extracts documentation from `doc/md` directory
- Shallow clone (--depth 1) for efficiency
- Timeout protection (120s)
- Removes old/deprecated docs

**Output Format** (JSON progress messages):
```json
{"type": "start", "total": 6, "message": "Starting documentation clone"}
{"type": "progress", "current": 3, "total": 6, "message": "Cloning Motoko repository"}
{"type": "info", "message": "Copied 120 documentation files"}
{"type": "complete", "total_processed": 120, "message": "Documentation cloning completed"}
```

**Target Directory**: `backend/data/motoko_official_docs/`

---

### 4. `ingest_samples.py`
**Purpose**: Ingests Motoko code samples (.mo files and mops.toml) into ChromaDB.

**Process**:
1. Scans `backend/data/motoko_code_samples/` directory
2. Processes .mo files and mops.toml files
3. Generates embeddings using SentenceTransformer (all-MiniLM-L6-v2)
4. Stores in ChromaDB collection: `motoko_code_samples`

**Output Format** (JSON progress messages):
```json
{"type": "start", "total": 850}
{"type": "progress", "current": 10, "total": 850, "message": "Processing hello.mo"}
{"type": "complete", "total_processed": 850}
```

**ChromaDB Collection**: `motoko_code_samples`

---

### 5. `ingest_docs.py`
**Purpose**: Ingests Motoko documentation (.md and .mdx files) into ChromaDB.

**Process**:
1. Scans `backend/data/motoko_official_docs/` directory
2. Extracts frontmatter from markdown files
3. Chunks content intelligently (by paragraphs, ~1500 chars)
4. Generates embeddings
5. Stores in ChromaDB collection: `motoko_docs`

**Output Format** (JSON progress messages):
```json
{"type": "start", "total": 120}
{"type": "progress", "current": 5, "total": 120, "message": "Processing base-intro.md"}
{"type": "complete", "total_processed": 450}
```

**ChromaDB Collection**: `motoko_docs`

---

## Environment Variables

All scripts respect these environment variables:

- `CHROMADB_PATH` - Path to ChromaDB storage (default: `backend/data/chromadb`)
- `PYTHON_EXECUTABLE` - Python executable to use (default: `python3`)

## Backend Data Structure

All data is stored in the `backend/data/` directory for self-contained organization:

```
backend/
├── data/
│   ├── chromadb/                    # ChromaDB vector database
│   ├── motoko_code_samples/         # Cloned Motoko repositories
│   ├── motoko_official_docs/        # Cloned official documentation
│   └── motoko_coder.db              # SQLite database (users, API keys, jobs)
├── scripts/
│   ├── clone_repos.py               # Clones to data/motoko_code_samples/
│   ├── clone_docs.py                # Clones to data/motoko_official_docs/
│   ├── ingest_samples.py            # Reads from data/motoko_code_samples/
│   ├── ingest_docs.py               # Reads from data/motoko_official_docs/
│   └── rag_retriever.py             # Queries data/chromadb/
└── bin/                             # Compiled binaries
```

## ChromaDB Path

By default, all scripts use the ChromaDB instance at:
```
backend/data/chromadb/
```

This can be overridden by setting the `CHROMADB_PATH` environment variable.

## Requirements

Install required Python packages:
```bash
pip install chromadb sentence-transformers tqdm
```

## Usage from Go Backend

These scripts are invoked by the Go backend via subprocess:

```go
cmd := exec.Command("python3", "./scripts/clone_repos.py")
cmd.Stdout = stdout
cmd.Stderr = stderr
err := cmd.Run()
```

The Go backend parses the JSON progress messages to track job status and update the database.

## Manual Usage

You can also run these scripts manually for testing:

```bash
# Clone code repositories
cd backend
python3 scripts/clone_repos.py

# Clone documentation
python3 scripts/clone_docs.py

# Ingest code samples
python3 scripts/ingest_samples.py

# Ingest documentation
python3 scripts/ingest_docs.py

# Test RAG retrieval
echo '{"query": "How to create an actor?", "n_results": 5}' | python3 scripts/rag_retriever.py
```

## Progress Output Format

All ingestion scripts output newline-delimited JSON for progress tracking:

- `{"type": "start", "total": N}` - Job started with N items
- `{"type": "progress", "current": X, "total": N, "message": "..."}` - Progress update
- `{"type": "info", "message": "..."}` - Informational message
- `{"type": "warning", "message": "..."}` - Warning (non-fatal)
- `{"type": "error", "message": "..."}` - Error (fatal)
- `{"type": "complete", "total_processed": N}` - Job completed

This format allows the Go backend to parse and display real-time progress to users.
