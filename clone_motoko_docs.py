#!/usr/bin/env python3

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Configuration
DOC_REPO_URL = "https://github.com/dfinity/motoko.git"
TEMP_CLONE_DIR = "temp_motoko_clone"
TARGET_DIR = "motoko_official_docs"
DOC_SOURCE_PATH = "doc/md"

def run_command(cmd, cwd=None):
    """Run a shell command and return success status."""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Command failed: {cmd}")
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Command execution failed: {e}")
        return False

def count_doc_files(directory):
    """Count markdown files in directory."""
    if not os.path.exists(directory):
        return 0
    
    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.md', '.mdx')):
                count += 1
    return count

def main():
    print("Cloning Motoko Official Documentation")
    print("=" * 52)
    
    # Clean up existing directories
    if os.path.exists(TEMP_CLONE_DIR):
        print(f"Removing existing temp directory: {TEMP_CLONE_DIR}")
        shutil.rmtree(TEMP_CLONE_DIR)
    
    if os.path.exists(TARGET_DIR):
        print(f"Removing existing docs directory: {TARGET_DIR}")
        shutil.rmtree(TARGET_DIR)
    
    # Clone the repository
    print("Cloning Motoko repository...")
    clone_cmd = f"git clone --depth 1 {DOC_REPO_URL} {TEMP_CLONE_DIR}"
    if not run_command(clone_cmd):
        print("Failed to clone repository")
        return 1
    
    print("Repository cloned successfully")
    
    # Check if documentation path exists
    source_doc_path = os.path.join(TEMP_CLONE_DIR, DOC_SOURCE_PATH)
    if not os.path.exists(source_doc_path):
        print(f"Documentation path not found: {source_doc_path}")
        shutil.rmtree(TEMP_CLONE_DIR, ignore_errors=True)
        return 1
    
    # Copy documentation to target directory
    print(f"Copying documentation from {source_doc_path} to {TARGET_DIR}")
    try:
        shutil.copytree(source_doc_path, TARGET_DIR)
    except Exception as e:
        print(f"Failed to copy documentation: {e}")
        shutil.rmtree(TEMP_CLONE_DIR, ignore_errors=True)
        return 1
    
    # Remove the old directory if it exists
    old_dir = os.path.join(TARGET_DIR, "old")
    if os.path.exists(old_dir):
        print(f"Removing old documentation directory: {old_dir}")
        shutil.rmtree(old_dir)
        print("Old directory removed successfully")
    
    # Count documentation files
    doc_count = count_doc_files(TARGET_DIR)
    print(f"Successfully copied {doc_count} documentation files to {TARGET_DIR}")
    
    # Clean up temp directory
    print(f"Cleaning up temp directory: {TEMP_CLONE_DIR}")
    try:
        shutil.rmtree(TEMP_CLONE_DIR)
        if not os.path.exists(TEMP_CLONE_DIR):
            print("Temp directory cleaned up successfully")
        else:
            print("Warning: Failed to remove temp directory")
    except Exception as e:
        print(f"Warning: Failed to remove temp directory: {e}")
    
    print("\nDocumentation cloning completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())