# ICP Coder Architecture

This diagram shows how the IDE integrations, Go backend, Python retrieval layer, storage, and external services work together inside ICP Coder.

```mermaid
graph TD
    IDE["IDE Clients<br/>(Cursor, Claude, etc.)"]

    subgraph MCP_Server["MCP Server (Node.js / MCP)"]
        tools["Tools<br/>get_motoko_context<br/>generate_motoko_code"]
    end

    subgraph Go_Backend["Go Backend (Gin REST API)"]
        router["Router & Middleware"]
        auth["Auth & API Keys"]
        rag["RAG Service<br/>(Python client)"]
        codegen["Codegen Services<br/>(Gemini / OpenAI / Claude)"]
    end

    subgraph Python_Layer["Python Scripts"]
        retriever["rag_retriever.py"]
        ingest["clone_*/ingest_* scripts"]
    end

    subgraph Data["Persistent Storage"]
        sqlite[("SQLite motoko_coder.db")]
        chroma[("ChromaDB Collections")]
        cache[("data/ repo cache")]
    end

    subgraph External["External Dependencies"]
        repos["Motoko sample repos"]
        docs["Motoko docs"]
        providers["LLM Providers"]
    end

    IDE -->|Model Context Protocol| tools
    tools -->|HTTP + API key| router
    router --> auth
    auth --> sqlite
    router --> rag
    rag -->|Subprocess| retriever
    retriever --> chroma
    ingest --> chroma
    ingest --> cache
    repos -->|git clone| cache
    docs -->|git clone| cache
    rag --> codegen
    codegen --> providers
    router --> codegen
    retriever --> rag
    tools -->|Responses| IDE
```

**Legend**
- Solid arrows indicate the primary request flow or data movement.
- Subgraphs group components that run within the same runtime or concern.
- Storage nodes with rounded corners represent persistent state managed by the system.
