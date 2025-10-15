# RAG Approach for Motoko Coder

## Core RAG Architecture

```mermaid
graph LR
    IDE["IDE / API Client<br/>(Cursor, Claude, HTTP)"] --> MCP["MCP Server<br/>(Node.js)"]
    MCP -->|REST + API key| GoAPI["Go Backend<br/>(Gin)"]
    GoAPI -->|Subprocess JSON| PyRetriever["Python rag_retriever.py"]
    PyRetriever --> Embed["SentenceTransformer<br/>all-MiniLM-L6-v2"]
    Embed --> Chroma["ChromaDB<br/>motoko_code_samples + motoko_docs"]
    Chroma --> PyRetriever
    PyRetriever --> Context["Code & Docs Context<br/>with metadata + warning"]
    Context --> GoAPI
    GoAPI --> Provider["Codegen Services<br/>(Gemini / OpenAI / Claude)"]
    Provider --> Response["Motoko-focused Response<br/>code + explanation"]
    Response --> MCP --> IDE
```

## Detailed RAG Flow

```mermaid
flowchart TD
    Start([User asks Motoko question]) --> Intake["MCP server forwards request"]
    Intake --> Auth["Go backend authenticates API key / Basic Auth"]
    Auth --> Dispatch["Go RAG handler normalises request"]
    Dispatch --> Subprocess["Invoke Python rag_retriever.py"]
    Subprocess --> Embedding["Compute embeddings (all-MiniLM-L6-v2)"]
    Embedding --> Retrieval["Query ChromaDB code + docs collections"]
    Retrieval --> Merge["Return contexts + metadata + warnings"]
    Merge --> Format["Go backend formats Markdown context block"]
    Format --> ProviderSelect["Select codegen provider from env"]
    ProviderSelect --> LLM["Call Gemini / OpenAI / Claude"]
    LLM --> Assemble["Assemble response payload (code, explanation, context)"]
    Assemble --> End([MCP server delivers result to user])
    Chroma[(ChromaDB)] --> Retrieval
    DataCache[(data/ repo cache)] --> Subprocess
```

## RAG Components Breakdown

### **1. Retrieval Phase**
```mermaid
graph TB
    subgraph "Retrieval Components"
        A1["Normalised Query"]
        A2["SentenceTransformer<br/>384-dim embedding"]
        A3["Similarity Search<br/>ChromaDB client"]
        A4["Top-K Selection<br/>code + docs"]
    end
    subgraph "Knowledge Base"
        B1["Motoko Code Snippets<br/>*.mo"]
        B2["Documentation Chunks<br/>*.md / *.mdx"]
        B3["Metadata<br/>paths, project folders, chunk titles"]
        B4["Vector Store<br/>motoko_code_samples + motoko_docs"]
    end
    A1 --> A2
    A2 --> A3
    A3 --> A4
    A4 --> B1
    A4 --> B2
    A4 --> B3
    A4 --> B4
```

### **2. Generation Phase**
```mermaid
graph TB
    subgraph "Context Assembly"
        C1["Code contexts<br/>with distances"]
        C2["Docs contexts<br/>with warnings"]
        C3["Original user query"]
        C4["Markdown formatted context"]
    end
    subgraph "Code Generation"
        D1["Provider factory<br/>(Gemini / OpenAI / Claude)"]
        D2["Runtime options<br/>temperature, max tokens"]
    end
    subgraph "Response Format"
        E1["Generated Motoko code"]
        E2["Explanation / reasoning"]
        E3["Returned context block"]
        E4["Error / warning messages"]
    end
    C1 --> C4
    C2 --> C4
    C3 --> D1
    C4 --> D1
    D1 --> D2
    D1 --> E1
    D1 --> E2
    C4 --> E3
    D1 --> E4
```

## Key RAG Features

### **Enhanced Retrieval**
- **Code + Docs Coverage**: Retrieves Motoko `.mo` files and Markdown documentation chunks.
- **Metadata Enrichment**: Includes file paths, folders, warnings, and distance scores.
- **Semantic Search**: Embeddings powered by SentenceTransformer `all-MiniLM-L6-v2`.
- **Python Bridge**: Dedicated script encapsulates ChromaDB access and health checks.

### **Context Assembly**
- **Markdown Context Block**: Go backend returns a structured context payload for downstream tools.
- **Configurable Fan-out**: `n_results` validated across API and MCP tooling.
- **Warning Propagation**: Missing collections or ingest issues surface as warnings.
- **Reusable Service Layer**: Go RAG service exposes retrieval to both generation and retrieval endpoints.

### **Generation Quality**
- **Multi-provider Support**: Gemini, OpenAI, or Claude selected at runtime via env vars.
- **Parameter Handling**: Temperature and token limits forwarded from client requests.
- **Streaming-ready**: Go handlers structure responses for API and MCP clients.
- **Error Transparency**: Provider errors bubbled back with contextual messaging.

### **Benefits of This RAG Approach**

1. **Accurate Code Generation**: Responses stay grounded in retrieved Motoko code and docs.
2. **Project Awareness**: Metadata preserves folder structure and documentation context.
3. **Up-to-date Knowledge**: Ingestion scripts can refresh samples and docs on demand.
4. **Flexible Providers**: Swap LLM vendors without changing clients.
5. **Operational Visibility**: Warnings, logging, and health checks simplify troubleshooting.
