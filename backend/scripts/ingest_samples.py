#!/usr/bin/env python3
"""
Code Samples Ingestion Script for Go Backend

This script ingests Motoko code samples into ChromaDB and reports progress.
Outputs newline-delimited JSON progress messages to stdout.
"""

import os
import sys
import json
from pathlib import Path

# Disable ChromaDB telemetry to avoid version compatibility issues
os.environ["ANONYMIZED_TELEMETRY"] = "False"

try:
    from sentence_transformers import SentenceTransformer
    import chromadb
except ImportError as e:
    error_msg = {"type": "error", "message": f"Missing packages: {str(e)}"}
    print(json.dumps(error_msg), file=sys.stderr)
    sys.exit(1)


# Get paths
BACKEND_DIR = Path(__file__).parent.parent
SAMPLES_DIR = BACKEND_DIR / "data" / "motoko_code_samples"


def get_chromadb_path():
    """Get ChromaDB path from environment or use backend default"""
    chromadb_path = os.getenv("CHROMADB_PATH")
    if chromadb_path:
        return chromadb_path
    # Default to backend data directory
    return str(Path(__file__).parent.parent / "data" / "chromadb")


def get_embedding(model, text: str) -> list:
    """Generate embedding for text"""
    return model.encode(text).tolist()


def get_metadata(file_path, base_dir, has_toml=False, has_dfx=False):
    """Extract metadata from file path"""
    rel_path = os.path.relpath(file_path, base_dir)
    parts = rel_path.split(os.sep)
    folders = parts[:-1]
    filename = parts[-1]

    if filename.endswith(".mo"):
        file_type = "motoko"
    elif filename == "mops.toml":
        file_type = "mops"
    elif filename == "dfx.json":
        file_type = "dfx"
    else:
        file_type = Path(filename).suffix.lstrip(".") or "unknown"

    return {
        "folders": "/".join(folders),
        "filename": filename,
        "rel_path": rel_path,
        "file_type": file_type,
        "has_toml": has_toml,
        "has_dfx": has_dfx
    }


def find_project_files(samples_dir):
    """Find all .mo files, mops.toml files, and dfx.json files"""
    mo_files = []
    mops_toml_files = []
    dfx_json_files = []
    project_toml_map = {}
    project_dfx_map = {}

    for root, _, files in os.walk(samples_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith(".mo"):
                mo_files.append(file_path)
            elif file == "mops.toml":
                mops_toml_files.append(file_path)
                project_dir = os.path.dirname(file_path)
                project_toml_map[project_dir] = file_path
            elif file == "dfx.json":
                dfx_json_files.append(file_path)
                project_dir = os.path.dirname(file_path)
                project_dfx_map[project_dir] = file_path

    return mo_files, mops_toml_files, dfx_json_files, project_toml_map, project_dfx_map


def ingest_samples():
    """Main ingestion function with progress reporting"""
    # Check if samples directory exists
    if not SAMPLES_DIR.exists():
        print(json.dumps({
            "type": "error",
            "message": f"Samples directory not found: {SAMPLES_DIR}"
        }), file=sys.stderr)
        sys.exit(1)

    # Initialize ChromaDB
    chromadb_path = get_chromadb_path()
    os.makedirs(chromadb_path, exist_ok=True)

    try:
        chroma_client = chromadb.PersistentClient(path=chromadb_path)
        collection = chroma_client.get_or_create_collection("motoko_code_samples")
    except Exception as e:
        print(json.dumps({
            "type": "error",
            "message": f"Failed to initialize ChromaDB: {str(e)}"
        }), file=sys.stderr)
        sys.exit(1)

    # Load embedding model
    print(json.dumps({"type": "info", "message": "Loading embedding model..."}), flush=True)
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Find files
    (
        mo_files,
        mops_toml_files,
        dfx_json_files,
        project_toml_map,
        project_dfx_map
    ) = find_project_files(SAMPLES_DIR)
    total_files = len(mo_files) + len(mops_toml_files) + len(dfx_json_files)

    if total_files == 0:
        print(json.dumps({
            "type": "error",
            "message": "No files found to ingest"
        }), file=sys.stderr)
        sys.exit(1)

    # Report start
    print(json.dumps({"type": "start", "total": total_files}), flush=True)

    docs, embeddings, metadatas, ids = [], [], [], []
    current = 0

    # Process .mo files
    for file_path in mo_files:
        current += 1

        try:
            project_dir = os.path.dirname(file_path)
            has_toml = project_dir in project_toml_map
            has_dfx = project_dir in project_dfx_map

            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()

            if not code.strip():
                continue

            meta = get_metadata(file_path, SAMPLES_DIR, has_toml, has_dfx)
            emb = get_embedding(model, code)

            docs.append(code)
            embeddings.append(emb)
            metadatas.append(meta)
            ids.append(f"motoko_sample_{current}")

            # Report progress every 10 files
            if current % 10 == 0 or current == 1:
                print(json.dumps({
                    "type": "progress",
                    "current": current,
                    "total": total_files,
                    "message": f"Processing {os.path.basename(file_path)}"
                }), flush=True)

        except Exception as e:
            print(json.dumps({
                "type": "warning",
                "message": f"Error processing {file_path}: {str(e)}"
            }), flush=True)

    # Process dfx.json files
    for file_path in dfx_json_files:
        current += 1

        try:
            project_dir = os.path.dirname(file_path)
            has_toml = project_dir in project_toml_map

            with open(file_path, "r", encoding="utf-8") as f:
                dfx_content = f.read()

            if not dfx_content.strip():
                continue

            meta = get_metadata(
                file_path,
                SAMPLES_DIR,
                has_toml=has_toml,
                has_dfx=True
            )
            emb = get_embedding(model, dfx_content)

            docs.append(dfx_content)
            embeddings.append(emb)
            metadatas.append(meta)
            ids.append(f"dfx_sample_{current}")

            if current % 10 == 0:
                print(json.dumps({
                    "type": "progress",
                    "current": current,
                    "total": total_files,
                    "message": f"Processing {os.path.basename(file_path)}"
                }), flush=True)

        except Exception as e:
            print(json.dumps({
                "type": "warning",
                "message": f"Error processing {file_path}: {str(e)}"
            }), flush=True)

    # Process mops.toml files
    for file_path in mops_toml_files:
        current += 1

        try:
            project_dir = os.path.dirname(file_path)
            has_dfx = project_dir in project_dfx_map

            with open(file_path, "r", encoding="utf-8") as f:
                toml_content = f.read()

            if not toml_content.strip():
                continue

            meta = get_metadata(
                file_path,
                SAMPLES_DIR,
                has_toml=True,
                has_dfx=has_dfx
            )
            emb = get_embedding(model, toml_content)

            docs.append(toml_content)
            embeddings.append(emb)
            metadatas.append(meta)
            ids.append(f"toml_sample_{current}")

            if current % 10 == 0:
                print(json.dumps({
                    "type": "progress",
                    "current": current,
                    "total": total_files,
                    "message": f"Processing {os.path.basename(file_path)}"
                }), flush=True)

        except Exception as e:
            print(json.dumps({
                "type": "warning",
                "message": f"Error processing {file_path}: {str(e)}"
            }), flush=True)

    # Store in ChromaDB
    if docs:
        print(json.dumps({
            "type": "info",
            "message": f"Storing {len(docs)} documents in ChromaDB..."
        }), flush=True)

        try:
            collection.add(
                documents=docs,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
        except Exception as e:
            print(json.dumps({
                "type": "error",
                "message": f"Failed to store in ChromaDB: {str(e)}"
            }), file=sys.stderr)
            sys.exit(1)

    # Report completion
    print(json.dumps({
        "type": "complete",
        "total_processed": len(docs)
    }), flush=True)


if __name__ == "__main__":
    try:
        ingest_samples()
    except Exception as e:
        print(json.dumps({"type": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)
