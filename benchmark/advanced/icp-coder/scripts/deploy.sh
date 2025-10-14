#!/usr/bin/env bash
set -euo pipefail

# Source dfx environment if available
if [ -f "$HOME/.local/share/dfxvm/env" ]; then
  # shellcheck disable=SC1091
  . "$HOME/.local/share/dfxvm/env"
fi

cd /mnt/e/partime/benchmark-project

dfx --version || true

# Start local replica
dfx start --background || true

# Use default identity to obtain owner principal
OWNER=$(dfx identity get-principal)
echo "OWNER=$OWNER"

# Deploy the canister with init argument (actor class)
dfx deploy cqt --argument "(principal \"$OWNER\")"

# Basic sanity checks
dfx canister call cqt name
dfx canister call cqt totalSupply


