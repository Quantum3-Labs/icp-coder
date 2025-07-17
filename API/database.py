import sqlite3
import hashlib
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Tuple
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "motoko_coder.db")

def init_database():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Create api_keys table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_api_key(length: int = 32) -> str:
    """Generate a random API key."""
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

def create_user(username: str, password: str, email: Optional[str] = None) -> Tuple[bool, str]:
    """Create a new user. Returns (success, message)."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return False, "Username already exists"
        
        # Hash password and create user
        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
            (username, password_hash, email)
        )
        
        conn.commit()
        conn.close()
        return True, "User created successfully"
        
    except Exception as e:
        return False, f"Error creating user: {str(e)}"

def authenticate_user(username: str, password: str) -> Tuple[bool, Optional[int], str]:
    """Authenticate a user. Returns (success, user_id, message)."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        cursor.execute(
            "SELECT id FROM users WHERE username = ? AND password_hash = ? AND is_active = 1",
            (username, password_hash)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return True, result[0], "Authentication successful"
        else:
            return False, None, "Invalid username or password"
            
    except Exception as e:
        return False, None, f"Authentication error: {str(e)}"

def create_api_key(user_id: int, name: Optional[str] = None) -> Tuple[bool, Optional[str], str]:
    """Create a new API key for a user. Returns (success, api_key, message)."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Generate unique API key
        while True:
            api_key = generate_api_key()
            cursor.execute("SELECT id FROM api_keys WHERE api_key = ?", (api_key,))
            if not cursor.fetchone():
                break
        
        # Insert API key
        cursor.execute(
            "INSERT INTO api_keys (user_id, api_key, name) VALUES (?, ?, ?)",
            (user_id, api_key, name or f"API Key {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        )
        
        conn.commit()
        conn.close()
        return True, api_key, "API key created successfully"
        
    except Exception as e:
        return False, None, f"Error creating API key: {str(e)}"

def validate_api_key(api_key: str) -> Tuple[bool, Optional[int], str]:
    """Validate an API key. Returns (valid, user_id, message)."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT user_id FROM api_keys WHERE api_key = ? AND is_active = 1",
            (api_key,)
        )
        
        result = cursor.fetchone()
        if result:
            # Update last_used timestamp
            cursor.execute(
                "UPDATE api_keys SET last_used = CURRENT_TIMESTAMP WHERE api_key = ?",
                (api_key,)
            )
            conn.commit()
            conn.close()
            return True, result[0], "API key is valid"
        else:
            conn.close()
            return False, None, "Invalid API key"
            
    except Exception as e:
        return False, None, f"Validation error: {str(e)}"

def get_user_api_keys(user_id: int) -> list:
    """Get all API keys for a user."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, api_key, name, created_at, last_used FROM api_keys WHERE user_id = ? AND is_active = 1",
            (user_id,)
        )
        
        keys = []
        for row in cursor.fetchall():
            keys.append({
                "id": row[0],
                "api_key": row[1],
                "name": row[2],
                "created_at": row[3],
                "last_used": row[4]
            })
        
        conn.close()
        return keys
        
    except Exception as e:
        return []

def revoke_api_key(user_id: int, api_key_id: int) -> Tuple[bool, str]:
    """Revoke an API key. Returns (success, message)."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE api_keys SET is_active = 0 WHERE id = ? AND user_id = ?",
            (api_key_id, user_id)
        )
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return True, "API key revoked successfully"
        else:
            conn.close()
            return False, "API key not found or not owned by user"
            
    except Exception as e:
        return False, f"Error revoking API key: {str(e)}"

# Initialize database when module is imported
init_database() 