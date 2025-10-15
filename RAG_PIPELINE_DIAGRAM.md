# Motoko Coder RAG Pipeline

## Complete System Architecture

```mermaid
graph TB
    subgraph "Source Repositories"
        samples["Motoko sample repos (git)"]
        docs["Motoko docs repo (git)"]
    end

    subgraph "Ingestion Scripts"
        cloneRepos["clone_repos.py"]
        cloneDocs["clone_docs.py"]
        ingestSamples["ingest_samples.py"]
        ingestDocs["ingest_docs.py"]
    end

    subgraph "Data Storage"
        repoCache["data/ repository cache"]
        chroma["ChromaDB collections\nmotoko_code_samples + motoko_docs"]
        sqlite["SQLite motoko_coder.db"]
    end

    subgraph "Runtime Services"
        goBackend["Go backend\nGin REST API (port 8080)"]
        pythonRetriever["Python rag_retriever.py\n(subprocess)"]
        providers["Codegen providers\nGemini / OpenAI / Claude"]
    end

    subgraph "Clients"
        mcpServer["MCP server\nNode.js"]
        httpClients["HTTP clients\nSwagger, curl, IDE"]
    end

    samples --> cloneRepos --> repoCache
    docs --> cloneDocs --> repoCache
    repoCache --> ingestSamples --> chroma
    repoCache --> ingestDocs --> chroma
    goBackend -. startup orchestration .-> cloneRepos
    goBackend -. startup orchestration .-> cloneDocs
    goBackend -. startup orchestration .-> ingestSamples
    goBackend -. startup orchestration .-> ingestDocs
    goBackend --> sqlite
    goBackend -->|subprocess| pythonRetriever
    pythonRetriever --> chroma
    goBackend --> providers
    mcpServer -->|REST + API key| goBackend
    httpClients --> goBackend
    goBackend --> mcpServer
    goBackend --> httpClients
```

## Detailed Process Flow

### 1. **Data Ingestion Phase**
```mermaid
sequenceDiagram
    participant Main as "Go server (main.go)"
    participant CloneRepos as "clone_repos.py"
    participant CloneDocs as "clone_docs.py"
    participant IngestSamples as "ingest_samples.py"
    participant IngestDocs as "ingest_docs.py"
    participant FS as "data/ directory"
    participant Chroma as "ChromaDB"

    Main->>FS: Check data/ and ChromaDB state
    alt Not initialised
        Main->>CloneRepos: Execute
        CloneRepos->>FS: Clone Motoko sample repositories
        Main->>CloneDocs: Execute
        CloneDocs->>FS: Clone documentation repositories
        Main->>IngestSamples: Execute
        IngestSamples->>Chroma: Upsert code samples + metadata
        Main->>IngestDocs: Execute
        IngestDocs->>Chroma: Upsert documentation chunks + metadata
    else Already initialised
        Main-->>FS: Skip ingestion scripts
    end
    Chroma-->>Main: Ingestion complete
```

### 2. **User Authentication & API Key Management**
```mermaid
sequenceDiagram
    participant User as "User"
    participant Backend as "Go backend (Gin)"
    participant DB as "SQLite"

    User->>Backend: POST /api/v1/auth/register
    Backend->>DB: Insert user + hashed password
    DB-->>Backend: User created
    Backend-->>User: Registration success

    User->>Backend: POST /api/v1/auth/login
    Backend->>DB: Verify credentials
    DB-->>Backend: User record
    Backend-->>User: Login success (Basic Auth session)

    User->>Backend: POST /api/v1/auth/keys
    Backend->>DB: Store hashed API key + prefix
    DB-->>Backend: Key persisted
    Backend-->>User: Return new API key (mk_...)

    User->>Backend: Authenticated request with x-api-key
    Backend->>DB: Validate API key hash and status
    DB-->>Backend: API key valid
```

### 3. **RAG Inference Process**
```mermaid
sequenceDiagram
    participant Client as "Client (MCP / HTTP)"
    participant Backend as "Go backend"
    participant Retriever as "Python rag_retriever.py"
    participant Chroma as "ChromaDB"
    participant Provider as "Codegen provider"

    Client->>Backend: Request (retrieve / generate)
    Backend->>Backend: Validate API key / Basic Auth
    Backend->>Retriever: Invoke with JSON payload
    Retriever->>Chroma: Query code + docs collections
    Chroma-->>Retriever: Return contexts + metadata
    Retriever-->>Backend: Send formatted response JSON
    alt Generate code
        Backend->>Provider: Call selected provider with query + contexts
        Provider-->>Backend: Generated code + explanation
    end
    Backend-->>Client: Response (context, code, warnings)
```

## Key Components Explained

### **Data Sources**
- **Motoko Sample Repositories**: Cloned into `data/` via `clone_repos.py`
- **Official Documentation**: Cloned into `data/` via `clone_docs.py`
- **Environment Configuration**: `.env` values drive script paths, database location, and provider choice

### **Ingestion Pipeline**
- **Repository Cloning**: Python scripts mirror upstream code and docs on first run
- **Sample Ingestion**: `ingest_samples.py` parses `.mo` files and `mops.toml`, capturing metadata such as folder hierarchy and TOML presence
- **Documentation Ingestion**: `ingest_docs.py` chunks Markdown content with titles, indices, and source metadata
- **Embedding Generation**: SentenceTransformer `all-MiniLM-L6-v2` creates 384-dimensional vectors stored in ChromaDB

### **Vector Database (ChromaDB)**
- **Collections**: `motoko_code_samples` and `motoko_docs`
- **Documents**: Raw code snippets, TOML manifests, and documentation chunks
- **Metadata**: File paths, folder arrays, chunk titles, warning flags
- **Distances**: Cosine similarity scores returned to the Go backend for ranking

### **API System**
- **Unified Go Service**: Exposes `/api/v1/auth`, `/api/v1/rag`, and `/v1/chat/completions` on port 8080
- **Middleware**: Basic Auth for ingestion endpoints, API key authentication for RAG and chat routes
- **SQLite Database**: Stores users, API keys, and ingestion job metadata
- **Auto-initialisation**: `main.go` triggers cloning and ingestion scripts when `data/` is empty

### **RAG Inference**
- **Query Normalisation**: Go handler validates payload and defaults `n_results`
- **Python Bridge**: Backend executes `rag_retriever.py` with stdin/stdout JSON to retrieve contexts
- **Context Formatting**: Responses include Markdown-ready sections for code and docs plus warnings when applicable
- **Code Generation**: Provider factory selects Gemini, OpenAI, or Claude based on `CODEGEN_PROVIDER`

### **Client Integration**
- **Node MCP Server**: Tools `get_motoko_context` and `generate_motoko_code` consume the Go API
- **Swagger / HTTP Clients**: Developers can test via Swagger UI or standard REST clients
- **OpenAI-Compatible SDKs**: `/v1/chat/completions` mirrors the OpenAI API for easy adoption
- **Automation**: Make targets orchestrate Docker containers, ingestion, and cleanup

## Benefits of This Architecture

1. **Full Motoko Coverage**: Combines sample code, manifests, and official documentation for grounded answers
2. **Self-Initialising**: Backend bootstraps data ingestion automatically while supporting manual control via Make
3. **Security Built-In**: Basic Auth for privileged operations and hashed API keys for user access
4. **Provider Flexibility**: Swap between Gemini, OpenAI, and Claude without client changes
5. **MCP Ready**: Seamless IDE integration through the Node MCP server alongside standard REST workflows
