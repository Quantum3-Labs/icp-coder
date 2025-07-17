# Motoko Coder API System

This directory contains the complete API system for Motoko Coder, including user authentication, API key management, and the RAG-powered Motoko code generation API.

## Architecture

The system consists of two main services:

1. **Authentication Server** (`auth_server.py`) - Handles user registration, login, and API key management
2. **RAG API Server** (`api_server.py`) - Provides the Motoko code generation endpoint

## Files Overview

- `database.py` - SQLite database operations for users and API keys
- `auth_server.py` - FastAPI server for user authentication and API key management
- `api_server.py` - FastAPI server for Motoko RAG API (OpenAI-compatible)
- `client_example.py` - Example client demonstrating the complete workflow
- `motoko_coder.db` - SQLite database (created automatically)

## Quick Start

### 1. Start the Authentication Server

```bash
python -m uvicorn API.auth_server:app --reload --port 8001
```

### 2. Start the RAG API Server

```bash
python -m uvicorn API.api_server:app --reload --port 8000
```

### 3. Run the Example Client

```bash
python API/client_example.py
```

## API Endpoints

### Authentication Server (Port 8001)

#### User Management
- `POST /register` - Register a new user
- `POST /login` - Login user
- `GET /profile` - Get user profile (requires authentication)

#### API Key Management
- `POST /api-keys` - Create a new API key (requires authentication)
- `GET /api-keys` - List user's API keys (requires authentication)
- `DELETE /api-keys/{id}` - Revoke an API key (requires authentication)

### RAG API Server (Port 8000)

#### Motoko Code Generation
- `POST /v1/chat/completions` - Generate Motoko code (requires API key)

## Usage Examples

### 1. Register a New User

```bash
curl -X POST "http://localhost:8001/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "secure_password",
    "email": "john@example.com"
  }'
```

### 2. Create an API Key

```bash
curl -X POST "http://localhost:8001/api-keys" \
  -H "Content-Type: application/json" \
  -u "john_doe:secure_password" \
  -d '{
    "name": "My Cursor API Key"
  }'
```

### 3. Use the Motoko RAG API

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_GENERATED_API_KEY" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "How do I write a counter canister in Motoko?"
      }
    ]
  }'
```

## Integration with Cursor/VS Code

### As OpenAI-Compatible Endpoint

1. In Cursor/VS Code, go to your LLM extension settings
2. Set the "OpenAI Base URL" to: `http://localhost:8000/v1/chat/completions`
3. Set the API key to your generated API key

### As Model Context Protocol (MCP)

1. In Cursor, go to **Settings → MCP Tools**
2. Add the configuration:
```json
{
  "mcpServers": {
    "motoko coder": {
      "command": "python",
      "args": ["-m", "uvicorn", "API.api_server:app", "--reload"],
      "env": {
        "GEMINI_API_KEY": "your-gemini-api-key"
      }
    }
  }
}
```

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);
```

### API Keys Table
```sql
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    api_key TEXT UNIQUE NOT NULL,
    name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

## Security Features

- **Password Hashing**: Passwords are hashed using SHA-256
- **API Key Generation**: Secure random API keys (32 characters)
- **Authentication**: Basic auth for user operations, API key for RAG API
- **Key Revocation**: Users can revoke their API keys
- **Usage Tracking**: Last used timestamp for API keys

## Environment Variables

Create a `.env` file in your project root:

```env
# Required: Google Gemini API key for the RAG functionality
GEMINI_API_KEY=your-gemini-api-key-here
```

## Development

### Adding New Features

1. **Database**: Add new functions to `database.py`
2. **Auth Server**: Add new endpoints to `auth_server.py`
3. **RAG API**: Modify `api_server.py` for new functionality

### Testing

Use the `client_example.py` script to test the complete workflow:
1. User registration
2. Login
3. API key creation
4. RAG API usage

## Troubleshooting

### Common Issues

1. **Port already in use**: Change the port numbers in the uvicorn commands
2. **Database errors**: Delete `motoko_coder.db` to reset the database
3. **API key not working**: Ensure the key is active and not revoked

### Logs

Both servers provide detailed logs. Check the terminal output for error messages and debugging information. 