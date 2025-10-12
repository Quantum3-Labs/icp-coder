#!/usr/bin/env python3
"""
Documentation Cloning Script for Go Backend

This script clones the official Motoko documentation and reports progress.
Outputs newline-delimited JSON progress messages to stdout.
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

# Configuration
DOC_REPO_URL = "https://github.com/dfinity/motoko.git"
TEMP_CLONE_DIR = "temp_motoko_clone"
DOC_SOURCE_PATH = "doc/md"

# Get backend directory (1 level up from backend/scripts)
BACKEND_DIR = Path(__file__).parent.parent
TARGET_DIR = BACKEND_DIR / "data" / "motoko_official_docs"


def count_doc_files(directory):
    """Count markdown files in directory"""
    if not os.path.exists(directory):
        return 0

    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.md', '.mdx')):
                count += 1
    return count


def clone_documentation():
    """Clone Motoko documentation with progress reporting"""
    temp_clone_path = BACKEND_DIR / TEMP_CLONE_DIR

    # Report start
    print(json.dumps({
        "type": "start",
        "total": 6,  # Number of steps
        "message": "Starting documentation clone"
    }), flush=True)

    step = 0

    # Step 1: Clean up existing temp directory
    step += 1
    print(json.dumps({
        "type": "progress",
        "current": step,
        "total": 6,
        "message": "Cleaning up temp directory"
    }), flush=True)

    if temp_clone_path.exists():
        try:
            shutil.rmtree(temp_clone_path)
        except Exception as e:
            print(json.dumps({
                "type": "warning",
                "message": f"Failed to remove temp directory: {str(e)}"
            }), flush=True)

    # Step 2: Clean up existing docs directory
    step += 1
    print(json.dumps({
        "type": "progress",
        "current": step,
        "total": 6,
        "message": "Cleaning up existing docs directory"
    }), flush=True)

    if TARGET_DIR.exists():
        try:
            shutil.rmtree(TARGET_DIR)
        except Exception as e:
            print(json.dumps({
                "type": "error",
                "message": f"Failed to remove existing docs: {str(e)}"
            }), file=sys.stderr)
            sys.exit(1)

    # Step 3: Clone repository
    step += 1
    print(json.dumps({
        "type": "progress",
        "current": step,
        "total": 6,
        "message": "Cloning Motoko repository"
    }), flush=True)

    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", DOC_REPO_URL, str(temp_clone_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=120
        )
    except subprocess.TimeoutExpired:
        print(json.dumps({
            "type": "error",
            "message": "Timeout cloning repository"
        }), file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(json.dumps({
            "type": "error",
            "message": f"Failed to clone repository: {e.stderr.decode() if e.stderr else str(e)}"
        }), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({
            "type": "error",
            "message": f"Error cloning repository: {str(e)}"
        }), file=sys.stderr)
        sys.exit(1)

    # Step 4: Verify documentation path exists
    step += 1
    print(json.dumps({
        "type": "progress",
        "current": step,
        "total": 6,
        "message": "Verifying documentation path"
    }), flush=True)

    source_doc_path = temp_clone_path / DOC_SOURCE_PATH
    if not source_doc_path.exists():
        print(json.dumps({
            "type": "error",
            "message": f"Documentation path not found: {source_doc_path}"
        }), file=sys.stderr)
        # Clean up
        if temp_clone_path.exists():
            shutil.rmtree(temp_clone_path, ignore_errors=True)
        sys.exit(1)

    # Step 5: Copy documentation
    step += 1
    print(json.dumps({
        "type": "progress",
        "current": step,
        "total": 6,
        "message": "Copying documentation files"
    }), flush=True)

    try:
        shutil.copytree(source_doc_path, TARGET_DIR)
    except Exception as e:
        print(json.dumps({
            "type": "error",
            "message": f"Failed to copy documentation: {str(e)}"
        }), file=sys.stderr)
        if temp_clone_path.exists():
            shutil.rmtree(temp_clone_path, ignore_errors=True)
        sys.exit(1)

    # Remove old directory if it exists
    old_dir = TARGET_DIR / "old"
    if old_dir.exists():
        print(json.dumps({
            "type": "info",
            "message": "Removing old documentation directory"
        }), flush=True)
        try:
            shutil.rmtree(old_dir)
        except Exception as e:
            print(json.dumps({
                "type": "warning",
                "message": f"Failed to remove old directory: {str(e)}"
            }), flush=True)

    # Count documentation files
    doc_count = count_doc_files(TARGET_DIR)
    print(json.dumps({
        "type": "info",
        "message": f"Copied {doc_count} documentation files"
    }), flush=True)

    # Step 6: Clean up temp directory
    step += 1
    print(json.dumps({
        "type": "progress",
        "current": step,
        "total": 6,
        "message": "Cleaning up temp files"
    }), flush=True)

    try:
        if temp_clone_path.exists():
            shutil.rmtree(temp_clone_path)
    except Exception as e:
        print(json.dumps({
            "type": "warning",
            "message": f"Failed to clean up temp directory: {str(e)}"
        }), flush=True)

    # Report completion
    print(json.dumps({
        "type": "complete",
        "total_processed": doc_count,
        "message": "Documentation cloning completed"
    }), flush=True)


if __name__ == "__main__":
    try:
        clone_documentation()
    except Exception as e:
        print(json.dumps({
            "type": "error",
            "message": str(e)
        }), file=sys.stderr)
        sys.exit(1)
