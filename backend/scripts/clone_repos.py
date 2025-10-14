#!/usr/bin/env python3
"""
Repository Cloning Script for Go Backend

This script clones Motoko repositories and reports progress to the Go backend.
Outputs newline-delimited JSON progress messages to stdout.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# Get backend directory (1 level up from backend/scripts)
BACKEND_DIR = Path(__file__).parent.parent
TARGET_DIR = BACKEND_DIR / "data" / "motoko_code_samples"

# Repository URLs (same as clone_motoko_repos.py)
REPO_URLS = [
    "https://github.com/matthewhammer/candid-spaces",
    "https://github.com/ninegua/tipjar",
    "https://github.com/PrimLabs/iCAN",
    "https://github.com/ninegua/ic-blackhole",
    "https://github.com/ORIGYN-SA/motoko_top_up_canister",
    "https://github.com/Appic-Solutions/Auto_Investment",
    "https://github.com/Toniq-Labs/extendable-token",
    "https://github.com/aviate-labs/ext.std",
    "https://github.com/sonicdex/icrc-1-public",
    "https://github.com/PanIndustrial-Org/icrc30.mo",
    "https://github.com/PanIndustrial-Org/icrc3.mo",
    "https://github.com/noku-team/icrc7_motoko",
    "https://github.com/PanIndustrial-Org/icrc7.mo",
    "https://github.com/PanIndustrial-Org/icrc_nft.mo",
    "https://github.com/rocklabs-io/ic-nft",
    "https://github.com/rocklabs-io/ic-token",
    "https://github.com/enzoh/motoko-token",
    "https://github.com/DepartureLabsIC/non-fungible-token",
    "https://github.com/rocklabs-io/token-faucet",
    "https://github.com/BrownFi/BrownFi-AMM-ICP",
    "https://github.com/ninegua/reversi",
    "https://github.com/DepartureLabsIC/revo",
    "https://github.com/enzoh/superheroes",
    "https://github.com/lokaverse/loka_canister",
    "https://github.com/kezzyNgotho/Hackathon202409AI",
    "https://github.com/Talentum-id/formify",
    "https://github.com/dfinity/linkedup",
    "https://github.com/johnxiaohe/ICP-Spark",
    "https://github.com/PrimLabs/Bucket",
    "https://github.com/gabrielnic/motoko-cdn",
    "https://github.com/enzoh/motoko-dht",
    "https://github.com/DepartureLabsIC/motoko-document-db",
    "https://github.com/PrimLabs/ICSP",
    "https://github.com/matthewhammer/cleansheets",
    "https://github.com/cosmasken/ic-payroll",
    "https://github.com/nomeata/motoko-certified-http",
    "https://github.com/DepartureLabsIC/relay",
    "https://github.com/bix-tech/secure-guard-escrow",
    "https://github.com/dfinity/sdk",
    "https://github.com/dfinity/vessel",
    "https://github.com/dfinity/motoko-base",
]


def clone_repositories():
    """Clone all repositories with progress reporting"""
    # Ensure target directory exists
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    total = len(REPO_URLS)

    # Report start
    print(json.dumps({"type": "start", "total": total}), flush=True)

    cloned = 0
    skipped = 0
    failed = 0

    for i, url in enumerate(REPO_URLS, 1):
        repo_name = url.split("/")[-1].replace(".git", "")
        repo_path = TARGET_DIR / repo_name

        # Report progress
        print(json.dumps({
            "type": "progress",
            "current": i,
            "total": total,
            "message": f"Processing {repo_name}"
        }), flush=True)

        # Skip if already exists
        if repo_path.exists():
            skipped += 1
            continue

        # Try to clone
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", url, str(repo_path)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=60
            )
            cloned += 1
        except subprocess.TimeoutExpired:
            print(json.dumps({
                "type": "warning",
                "message": f"Timeout cloning {repo_name}"
            }), flush=True)
            failed += 1
        except subprocess.CalledProcessError:
            print(json.dumps({
                "type": "warning",
                "message": f"Failed to clone {repo_name}"
            }), flush=True)
            failed += 1
        except Exception as e:
            print(json.dumps({
                "type": "warning",
                "message": f"Error cloning {repo_name}: {str(e)}"
            }), flush=True)
            failed += 1

    # Report completion
    print(json.dumps({
        "type": "complete",
        "total_processed": total,
        "cloned": cloned,
        "skipped": skipped,
        "failed": failed
    }), flush=True)


if __name__ == "__main__":
    try:
        clone_repositories()
    except Exception as e:
        print(json.dumps({"type": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)
