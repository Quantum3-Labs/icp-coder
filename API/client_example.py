#!/usr/bin/env python3
"""
Example client for Motoko Coder API
Demonstrates user registration, API key creation, and usage
"""

import requests
import json
from getpass import getpass

# Configuration
AUTH_BASE_URL = "http://localhost:8001"  # Auth server
API_BASE_URL = "http://localhost:8000"   # RAG API server

def register_user():
    """Register a new user."""
    print("=== User Registration ===")
    username = input("Enter username: ")
    password = getpass("Enter password: ")
    email = input("Enter email (optional): ")
    
    data = {
        "username": username,
        "password": password,
        "email": email if email else None
    }
    
    try:
        response = requests.post(f"{AUTH_BASE_URL}/register", json=data)
        result = response.json()
        
        if response.status_code == 200 and result.get("success"):
            print(f"✅ {result['message']}")
            return username, password
        else:
            print(f"❌ {result.get('detail', 'Registration failed')}")
            return None, None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None

def login_user(username, password):
    """Login user."""
    print(f"\n=== Login as {username} ===")
    
    data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(f"{AUTH_BASE_URL}/login", json=data)
        result = response.json()
        
        if response.status_code == 200 and result.get("success"):
            print(f"✅ {result['message']}")
            return result.get("user_id")
        else:
            print(f"❌ {result.get('detail', 'Login failed')}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def create_api_key(user_id, username, password):
    """Create a new API key."""
    print(f"\n=== Create API Key ===")
    key_name = input("Enter API key name (optional): ")
    
    data = {"name": key_name} if key_name else {}
    
    try:
        response = requests.post(
            f"{AUTH_BASE_URL}/api-keys",
            json=data,
            auth=(username, password)
        )
        result = response.json()
        
        if response.status_code == 200 and result.get("success"):
            print(f"✅ {result['message']}")
            print(f"🔑 API Key: {result['api_key']}")
            return result['api_key']
        else:
            print(f"❌ {result.get('detail', 'API key creation failed')}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def list_api_keys(username, password):
    """List user's API keys."""
    print(f"\n=== Your API Keys ===")
    
    try:
        response = requests.get(
            f"{AUTH_BASE_URL}/api-keys",
            auth=(username, password)
        )
        
        if response.status_code == 200:
            keys = response.json()
            if keys:
                for i, key in enumerate(keys, 1):
                    print(f"{i}. {key['name']}")
                    print(f"   Key: {key['api_key']}")
                    print(f"   Created: {key['created_at']}")
                    if key['last_used']:
                        print(f"   Last used: {key['last_used']}")
                    print()
            else:
                print("No API keys found.")
        else:
            print(f"❌ Failed to list API keys: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_motoko_api(api_key):
    """Test the Motoko RAG API with the provided API key."""
    print(f"\n=== Test Motoko RAG API ===")
    
    # Example Motoko question
    question = "How do I write a simple counter canister in Motoko?"
    print(f"Question: {question}")
    
    data = {
        "messages": [
            {
                "role": "user",
                "content": question
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/v1/chat/completions",
            json=data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result['choices'][0]['message']['content']
            print(f"\n✅ Answer:\n{answer}")
        else:
            print(f"❌ API Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function to demonstrate the complete workflow."""
    print("🚀 Motoko Coder API Client Example")
    print("=" * 50)
    
    # Step 1: Register or login
    choice = input("Do you want to (1) register a new user or (2) use existing credentials? [1/2]: ")
    
    if choice == "1":
        username, password = register_user()
        if not username:
            return
    else:
        username = input("Enter username: ")
        password = getpass("Enter password: ")
    
    # Step 2: Login
    user_id = login_user(username, password)
    if not user_id:
        return
    
    # Step 3: Create API key
    api_key = create_api_key(user_id, username, password)
    if not api_key:
        return
    
    # Step 4: List API keys
    list_api_keys(username, password)
    
    # Step 5: Test the API
    test_motoko_api(api_key)
    
    print(f"\n🎉 Setup complete! You can now use this API key in Cursor, VS Code, or any other client.")
    print(f"API Key: {api_key}")
    print(f"API Endpoint: {API_BASE_URL}/v1/chat/completions")

if __name__ == "__main__":
    main() 