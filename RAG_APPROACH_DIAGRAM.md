# RAG Approach for Motoko Coder

## Core RAG Architecture

```mermaid
graph LR
    %% User Input
    A[User Query<br/>"How to write a counter canister?"] --> B
    
    %% Query Processing
    B[Query Embedding<br/>SentenceTransformer<br/>all-MiniLM-L6-v2] --> C
    
    %% Vector Search
    C[Vector Similarity Search<br/>ChromaDB] --> D
    
    %% Context Retrieval
    D[Retrieve Relevant<br/>Motoko Code Samples<br/>+ TOML Configs] --> E
    
    %% Context Assembly
    E[Build Context<br/>"Context: [retrieved code samples]<br/>Request: [user query]"] --> F
    
    %% LLM Generation
    F[Gemini 2.5 Flash<br/>Generate Response] --> G
    
    %% Final Output
    G[Generated Answer<br/>with Motoko Code Examples]
    
    %% Knowledge Base
    H[Knowledge Base<br/>ChromaDB Collection<br/>- Motoko Code Samples<br/>- TOML Configurations<br/>- Project Metadata] --> C
    
    %% Styling
    classDef input fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    classDef process fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px
    classDef retrieval fill:#e8f5e8,stroke:#388e3c,stroke-width:3px
    classDef generation fill:#fff3e0,stroke:#f57c00,stroke-width:3px
    classDef output fill:#fce4ec,stroke:#c2185b,stroke-width:3px
    classDef knowledge fill:#e0f2f1,stroke:#00695c,stroke-width:3px
    
    class A input
    class B,C,D,E process
    class H knowledge
    class F generation
    class G output
```

## Detailed RAG Flow

```mermaid
flowchart TD
    %% Start
    Start([User asks Motoko question]) --> Query
    
    %% Query Processing
    Query[Extract user question] --> Embed
    Embed[Generate embedding<br/>using SentenceTransformer] --> Search
    
    %% Retrieval Phase
    Search[Search ChromaDB<br/>for similar code samples] --> Filter
    Filter[Filter by relevance<br/>and project context] --> Context
    
    %% Context Building
    Context[Assemble context from<br/>- Motoko code files<br/>- TOML configurations<br/>- Project metadata] --> Prompt
    
    %% Generation Phase
    Prompt[Create prompt:<br/>Context + User Question] --> LLM
    LLM[Gemini 2.5 Flash<br/>generates response] --> Response
    
    %% Output
    Response[Return structured answer<br/>with code examples] --> End([User receives answer])
    
    %% Knowledge Base
    KB[Knowledge Base<br/>ChromaDB Collection] --> Search
    
    %% Styling
    classDef startEnd fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px
    classDef process fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef retrieval fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    classDef generation fill:#fce4ec,stroke:#ad1457,stroke-width:2px
    classDef knowledge fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    
    class Start,End startEnd
    class Query,Embed,Filter,Context,Prompt,Response process
    class Search retrieval
    class LLM generation
    class KB knowledge
```

## RAG Components Breakdown

### **1. Retrieval Phase**
```mermaid
graph TB
    subgraph "Retrieval Components"
        A1[User Query]
        A2[Query Embedding<br/>384-dimensional vector]
        A3[Vector Similarity Search<br/>Cosine similarity]
        A4[Top-K Retrieval<br/>Most relevant documents]
    end
    
    subgraph "Knowledge Base"
        B1[Motoko Code Files<br/>*.mo]
        B2[TOML Configurations<br/>*.toml]
        B3[Project Metadata<br/>file paths, structure]
        B4[Embeddings<br/>pre-computed vectors]
    end
    
    A1 --> A2
    A2 --> A3
    A3 --> A4
    A4 --> B1
    A4 --> B2
    A4 --> B3
    A4 --> B4
    
    classDef retrieval fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef knowledge fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    
    class A1,A2,A3,A4 retrieval
    class B1,B2,B3,B4 knowledge
```

### **2. Generation Phase**
```mermaid
graph TB
    subgraph "Context Assembly"
        C1[Retrieved Documents]
        C2[Metadata Information]
        C3[User Query]
        C4[Structured Prompt]
    end
    
    subgraph "LLM Generation"
        D1[Gemini 2.5 Flash]
        D2[Temperature: 0.7]
        D3[Max Tokens: 4096]
        D4[Top-p: 0.9]
    end
    
    subgraph "Response Format"
        E1[Code Examples]
        E2[Explanations]
        E3[Best Practices]
        E4[Project Structure]
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
    
    classDef context fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef llm fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef response fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    
    class C1,C2,C3,C4 context
    class D1,D2,D3,D4 llm
    class E1,E2,E3,E4 response
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