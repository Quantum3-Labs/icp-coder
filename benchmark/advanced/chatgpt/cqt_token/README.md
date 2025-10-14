# CQT Token (Motoko)

Fungible token Motoko canister implementing `CQT` with `mint`, `transfer`, balances, and a randomness-based guessing game that mints a reward on win.

## Prerequisites

- dfx 0.27.x
- macOS/Linux shell

## Quickstart

```bash
cd cqt_token
dfx start --background
dfx deploy
```

Check basic metadata:

```bash
dfx canister call cqt_token_backend name
dfx canister call cqt_token_backend symbol
dfx canister call cqt_token_backend decimals
dfx canister call cqt_token_backend totalSupply
```

## Identities

```bash
# current principal
dfx identity get-principal

# optional: create a second identity
dfx identity new bob --storage-mode=plaintext
dfx identity use bob
dfx identity get-principal
dfx identity use default
```

## Token functions

```bash
# Mint tokens (demo: open mint, anyone can mint)
ME=$(dfx identity get-principal)
dfx canister call cqt_token_backend mint "(principal \"$ME\", 1000:nat)"

# Check balances
dfx canister call cqt_token_backend balanceOf "(principal \"$ME\")"

# Transfer
BOB=$(dfx identity use bob >/dev/null; dfx identity get-principal; dfx identity use default >/dev/null;)
dfx canister call cqt_token_backend transfer "(principal \"$BOB\", 200:nat)"
dfx canister call cqt_token_backend balanceOf "(principal \"$BOB\")"
```

## Randomness and Game

```bash
# Generate bounded random number in [0, 100)
dfx canister call cqt_token_backend generateRandomNumber '(100:nat)'

# Guess-to-win: reward 10 CQT if guess matches winning number
dfx canister call cqt_token_backend guessToWin '(42:nat, 100:nat)'
```

Notes:

- Randomness uses the management canister `raw_rand` via `mo:base/Random.blob()` and derives a 64-bit value from returned bytes, then takes modulo bound.
- `mint` is intentionally unrestricted for demo; restrict in production.

## Files

- `src/cqt_token_backend/main.mo`: token and game logic
- `dfx.json`: canister config
