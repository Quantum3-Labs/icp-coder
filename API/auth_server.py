from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from . import database
from datetime import datetime

app = FastAPI(title="Motoko Coder Auth API", version="1.0.0")
security = HTTPBasic()

# Pydantic models
class UserRegistration(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class ApiKeyCreate(BaseModel):
    name: Optional[str] = None

class ApiKeyResponse(BaseModel):
    id: int
    api_key: str
    name: str
    created_at: str
    last_used: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    created_at: str

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Get current user from basic auth credentials."""
    success, user_id, message = database.authenticate_user(
        credentials.username, credentials.password
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user_id

@app.post("/register", response_model=dict)
async def register_user(user_data: UserRegistration):
    """Register a new user."""
    success, message = database.create_user(
        user_data.username, user_data.password, user_data.email
    )
    
    if success:
        return {"success": True, "message": message}
    else:
        raise HTTPException(status_code=400, detail=message)

@app.post("/login", response_model=dict)
async def login_user(user_data: UserLogin):
    """Login user and return user info."""
    success, user_id, message = database.authenticate_user(
        user_data.username, user_data.password
    )
    
    if success:
        return {
            "success": True,
            "message": message,
            "user_id": user_id,
            "username": user_data.username
        }
    else:
        raise HTTPException(status_code=401, detail=message)

@app.post("/api-keys", response_model=dict)
async def create_api_key(
    api_key_data: ApiKeyCreate,
    current_user_id: int = Depends(get_current_user)
):
    """Create a new API key for the authenticated user."""
    success, api_key, message = database.create_api_key(
        current_user_id, api_key_data.name
    )
    
    if success:
        return {
            "success": True,
            "message": message,
            "api_key": api_key,
            "name": api_key_data.name or f"API Key {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        }
    else:
        raise HTTPException(status_code=400, detail=message)

@app.get("/api-keys", response_model=List[ApiKeyResponse])
async def list_api_keys(current_user_id: int = Depends(get_current_user)):
    """List all API keys for the authenticated user."""
    api_keys = database.get_user_api_keys(current_user_id)
    return api_keys

@app.delete("/api-keys/{api_key_id}")
async def revoke_api_key(
    api_key_id: int,
    current_user_id: int = Depends(get_current_user)
):
    """Revoke an API key."""
    success, message = database.revoke_api_key(current_user_id, api_key_id)
    
    if success:
        return {"success": True, "message": message}
    else:
        raise HTTPException(status_code=400, detail=message)

@app.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user_id: int = Depends(get_current_user)):
    """Get user profile information."""
    # This would need to be implemented in database.py
    # For now, return basic info
    return {
        "id": current_user_id,
        "username": "user",  # Would need to fetch from DB
        "email": None,
        "created_at": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Motoko Coder Authentication API",
        "version": "1.0.0",
        "endpoints": {
            "register": "/register",
            "login": "/login",
            "create_api_key": "/api-keys",
            "list_api_keys": "/api-keys",
            "revoke_api_key": "/api-keys/{id}",
            "profile": "/profile"
        }
    } 