# Motoko Coder RAG Pipeline

## Complete System Architecture

```mermaid
graph TB
    %% Data Sources
    subgraph "Data Sources"
        A1[motoko_code_samples/]
        A2[*.mo files]
        A3[*.toml files]
        A4[Project Structure]
    end

    %% Ingestion Process
    subgraph "Ingestion Pipeline"
        B1[motoko_samples_ingester.py]
        B2[SentenceTransformer<br/>all-MiniLM-L6-v2]
        B3[Embedding Generation]
        B4[Metadata Extraction]
        B5[ChromaDB Storage]
    end

    %% Database & Storage
    subgraph "Vector Database"
        C1[ChromaDB Collection<br/>motoko_code_samples]
        C2[Documents]
        C3[Embeddings]
        C4[Metadata]
        C5[IDs]
    end

    %% API System
    subgraph "API System"
        D1[Auth Server<br/>Port 8001]
        D2[User Registration]
        D3[API Key Management]
        D4[RAG API Server<br/>Port 8000]
        D5[OpenAI-Compatible<br/>Endpoint]
    end

    %% User Authentication
    subgraph "User Management"
        E1[SQLite Database]
        E2[Users Table]
        E3[API Keys Table]
        E4[Authentication]
    end

    %% Inference Process
    subgraph "RAG Inference"
        F1[User Query]
        F2[Query Embedding]
        F3[Vector Similarity Search]
        F4[Context Retrieval]
        F5[Gemini 2.5 Flash]
        F6[Response Generation]
    end

    %% Client Integration
    subgraph "Client Integration"
        G1[Cursor/VS Code]
        G2[curl/HTTP Client]
        G3[Python Client]
        G4[MCP Integration]
    end

    %% Connections - Data Flow
    A1 --> B1
    A2 --> B1
    A3 --> B1
    A4 --> B1

    B1 --> B2
    B2 --> B3
    B1 --> B4
    B3 --> B5
    B4 --> B5
    B5 --> C1

    C1 --> C2
    C1 --> C3
    C1 --> C4
    C1 --> C5

    %% API Connections
    D1 --> D2
    D1 --> D3
    D2 --> E1
    D3 --> E1
    E1 --> E2
    E1 --> E3
    E3 --> D4
    D4 --> D5

    %% Inference Flow
    F1 --> D5
    D5 --> F2
    F2 --> F3
    F3 --> C1
    C1 --> F4
    F4 --> F5
    F5 --> F6
    F6 --> D5

    %% Client Connections
    G1 --> D5
    G2 --> D5
    G3 --> D5
    G4 --> D5

    %% Styling
    classDef dataSource fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef ingestion fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef database fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef api fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef auth fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef inference fill:#f1f8e9,stroke:#33691e,stroke-width:2px
    classDef client fill:#e0f2f1,stroke:#004d40,stroke-width:2px

    class A1,A2,A3,A4 dataSource
    class B1,B2,B3,B4,B5 ingestion
    class C1,C2,C3,C4,C5 database
    class D1,D2,D3,D4,D5 api
    class E1,E2,E3,E4 auth
    class F1,F2,F3,F4,F5,F6 inference
    class G1,G2,G3,G4 client
```

## Detailed Process Flow

### 1. **Data Ingestion Phase**
```mermaid
sequenceDiagram
    participant I as Ingester
    participant ST as SentenceTransformer
    participant CD as ChromaDB
    participant FS as File System

    I->>FS: Scan motoko_code_samples/
    FS->>I: Return .mo and .toml files
    I->>I: Extract metadata (folders, filename, has_toml)
    
    loop For each file
        I->>I: Read file content
        I->>ST: Generate embedding
        ST->>I: Return vector
        I->>CD: Store document + embedding + metadata
    end
    
    CD->>I: Confirm storage
```

### 2. **User Authentication & API Key Management**
```mermaid
sequenceDiagram
    participant U as User
    participant AS as Auth Server
    participant DB as SQLite DB
    participant RAS as RAG API Server

    U->>AS: Register/Login
    AS->>DB: Store/Validate credentials
    DB->>AS: Return user_id
    
    U->>AS: Create API Key
    AS->>DB: Generate & store API key
    DB->>AS: Return API key
    AS->>U: Return API key
    
    U->>RAS: Request with API key
    RAS->>DB: Validate API key
    DB->>RAS: Confirm valid
```

### 3. **RAG Inference Process**
```mermaid
sequenceDiagram
    participant C as Client
    participant RAS as RAG API Server
    participant CD as ChromaDB
    participant G as Gemini API
    participant ST as SentenceTransformer

    C->>RAS: POST /v1/chat/completions
    RAS->>RAS: Validate API key
    
    RAS->>ST: Embed user query
    ST->>RAS: Return query vector
    
    RAS->>CD: Vector similarity search
    CD->>RAS: Return relevant documents
    
    RAS->>RAS: Build context from documents
    RAS->>G: Send context + query
    G->>RAS: Return generated response
    
    RAS->>C: Return OpenAI-compatible response
```

## Key Components Explained

### **Data Sources**
- **Motoko Code Samples**: Collection of `.mo` files from various projects
- **TOML Configuration**: Project dependency files (`mops.toml`, `dfx.json`)
- **Project Structure**: Directory organization and metadata

### **Ingestion Pipeline**
- **File Discovery**: Recursively finds all `.mo` and `.toml` files
- **Embedding Generation**: Uses SentenceTransformer for vector embeddings
- **Metadata Extraction**: Captures file paths, project structure, and TOML presence
- **Database Storage**: Stores in ChromaDB with proper indexing

### **Vector Database (ChromaDB)**
- **Documents**: Raw file contents (Motoko code + TOML configs)
- **Embeddings**: 384-dimensional vectors from SentenceTransformer
- **Metadata**: File paths, project info, file types, TOML indicators
- **IDs**: Unique identifiers for each document

### **API System**
- **Authentication Server**: User registration, login, API key management
- **RAG API Server**: OpenAI-compatible endpoint for code generation
- **Database Integration**: SQLite for user management, ChromaDB for vectors

### **RAG Inference**
- **Query Processing**: User questions about Motoko development
- **Vector Search**: Semantic similarity search in ChromaDB
- **Context Assembly**: Relevant code samples and configurations
- **LLM Generation**: Gemini 2.5 Flash generates responses
- **Response Format**: OpenAI-compatible JSON structure

### **Client Integration**
- **Cursor/VS Code**: Direct integration as OpenAI endpoint
- **HTTP Clients**: curl, Python requests, etc.
- **MCP Support**: Model Context Protocol integration
- **Custom Clients**: Any OpenAI-compatible client

## Benefits of This Architecture

1. **Comprehensive Context**: Includes both code and configuration files
2. **Scalable**: Can handle large numbers of code samples
3. **Secure**: User authentication and API key management
4. **Compatible**: Works with existing OpenAI-based tools
5. **Flexible**: Supports multiple client types and integration methods 