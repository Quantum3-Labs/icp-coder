# RAG Approach for Motoko Coder

## Core RAG Architecture

```mermaid
graph LR
    A["User Query: How to write a counter canister?"] --> B
    B["Query Embedding: SentenceTransformer all-MiniLM-L6-v2"] --> C
    C["Vector Similarity Search: ChromaDB"] --> D
    D["Retrieve Relevant Motoko Code Samples and TOML Configs"] --> E
    E["Build Context: [retrieved code samples], Request: [user query]"] --> F
    F["Gemini 2.5 Flash: Generate Response"] --> G
    G["Generated Answer with Motoko Code Examples"]
    H["Knowledge Base: ChromaDB Collection, Motoko Code Samples, TOML Configurations, Project Metadata"] --> C
    %% Styling removed for GitHub compatibility
```

## Detailed RAG Flow

```mermaid
flowchart TD
    Start([User asks Motoko question]) --> Query
    Query["Extract user question"] --> Embed
    Embed["Generate embedding using SentenceTransformer"] --> Search
    Search["Search ChromaDB for similar code samples"] --> Filter
    Filter["Filter by relevance and project context"] --> Context
    Context["Assemble context from Motoko code files, TOML configurations, Project metadata"] --> Prompt
    Prompt["Create prompt: Context + User Question"] --> LLM
    LLM["Gemini 2.5 Flash generates response"] --> Response
    Response["Return structured answer with code examples"] --> End([User receives answer])
    KB["Knowledge Base: ChromaDB Collection"] --> Search
    %% Styling removed for GitHub compatibility
```

## RAG Components Breakdown

### **1. Retrieval Phase**
```mermaid
graph TB
    subgraph "Retrieval Components"
        A1["User Query"]
        A2["Query Embedding: 384-dimensional vector"]
        A3["Vector Similarity Search: Cosine similarity"]
        A4["Top-K Retrieval: Most relevant documents"]
    end
    subgraph "Knowledge Base"
        B1["Motoko Code Files: *.mo"]
        B2["TOML Configurations: *.toml"]
        B3["Project Metadata: file paths, structure"]
        B4["Embeddings: pre-computed vectors"]
    end
    A1 --> A2
    A2 --> A3
    A3 --> A4
    A4 --> B1
    A4 --> B2
    A4 --> B3
    A4 --> B4
    %% Styling removed for GitHub compatibility
```

### **2. Generation Phase**
```mermaid
graph TB
    subgraph "Context Assembly"
        C1["Retrieved Documents"]
        C2["Metadata Information"]
        C3["User Query"]
        C4["Structured Prompt"]
    end
    subgraph "LLM Generation"
        D1["Gemini 2.5 Flash"]
        D2["Temperature: 0.7"]
        D3["Max Tokens: 4096"]
        D4["Top-p: 0.9"]
    end
    subgraph "Response Format"
        E1["Code Examples"]
        E2["Explanations"]
        E3["Best Practices"]
        E4["Project Structure"]
    end
    C1 --> C4
    C2 --> C4
    C3 --> C4
    C4 --> D1
    D1 --> D2
    D1 --> D3
    D1 --> D4
    D1 --> E1
    D1 --> E2
    D1 --> E3
    D1 --> E4
    %% Styling removed for GitHub compatibility
```

## Key RAG Features

### **Enhanced Retrieval**
- **Dual File Types**: Both `.mo` and `.toml` files for complete context
- **Project Awareness**: Understands project structure and dependencies
- **Metadata Enrichment**: File paths, project info, TOML presence indicators
- **Semantic Search**: Uses SentenceTransformer for understanding code meaning

### **Context Assembly**
- **Multi-file Context**: Combines relevant code samples and configurations
- **Structured Prompts**: Clear separation between context and user query
- **Project Metadata**: Includes file locations and project structure info

### **Generation Quality**
- **Gemini 2.5 Flash**: Latest model for high-quality code generation
- **Temperature Control**: Balanced creativity and accuracy
- **Token Management**: Optimized for code generation tasks
- **OpenAI Compatibility**: Standard response format for easy integration

### **Benefits of This RAG Approach**

1. **Accurate Code Generation**: Grounded in real Motoko examples
2. **Project Context**: Understands dependencies and configurations
3. **Up-to-date Knowledge**: Based on current Motoko code samples
4. **Scalable**: Can handle large codebases efficiently
5. **Maintainable**: Easy to update with new code samples 