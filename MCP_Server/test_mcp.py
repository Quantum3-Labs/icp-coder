#!/usr/bin/env python3
"""
Simple test script for the Motoko Coder MCP Server
"""

import json
import subprocess
import sys
import time

def test_mcp_server():
    """Test the MCP server with basic commands"""
    
    print("🧪 Testing Motoko Coder MCP Server...")
    
    # Start the MCP server
    try:
        process = subprocess.Popen(
            ["python", "mcp_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="."
        )
        
        # Wait a moment for server to start
        time.sleep(2)
        
        # Test 1: Initialize
        print("\n📝 Test 1: Initialize")
        init_request = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "initialize",
            "params": {}
        }
        
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        print(f"Response: {response.strip()}")
        
        # Test 2: List tools
        print("\n📝 Test 2: List tools")
        tools_request = {
            "jsonrpc": "2.0",
            "id": "2",
            "method": "tools/list",
            "params": {}
        }
        
        process.stdin.write(json.dumps(tools_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        print(f"Response: {response.strip()}")
        
        # Test 3: Get Motoko context
        print("\n📝 Test 3: Get Motoko context")
        context_request = {
            "jsonrpc": "2.0",
            "id": "3",
            "method": "tools/call",
            "params": {
                "name": "get_motoko_context",
                "arguments": {
                    "query": "counter canister",
                    "max_results": 2
                }
            }
        }
        
        process.stdin.write(json.dumps(context_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        print(f"Response: {response.strip()}")
        
        # Test 4: Generate Motoko code
        print("\n📝 Test 4: Generate Motoko code")
        code_request = {
            "jsonrpc": "2.0",
            "id": "4",
            "method": "tools/call",
            "params": {
                "name": "generate_motoko_code",
                "arguments": {
                    "query": "Create a simple counter canister",
                    "max_context_results": 3
                }
            }
        }
        
        process.stdin.write(json.dumps(code_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        print(f"Response: {response.strip()}")
        
        # Clean up
        process.terminate()
        process.wait()
        
        print("\n✅ MCP Server tests completed!")
        
    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")
        if 'process' in locals():
            process.terminate()
        sys.exit(1)

if __name__ == "__main__":
    test_mcp_server() 