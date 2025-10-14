# CQT Token (Motoko / DFX)

Fungible token canister in Motoko with a simple guessing game that mints a prize on a correct guess.

## Requirements

- DFX (0.15+ recommended)
- Internet Computer SDK

## Project Layout

- `dfx.json`: Project configuration
- `src/cqt/main.mo`: Motoko canister implementing token and game

## Quickstart (PowerShell)

```powershell
# 1) Start a local replica
dfx start --background

# 2) (Optional) Use a dedicated identity
dfx identity new owner --storage-mode=plaintext 2>$null | Out-Null
dfx identity use owner

# 3) Get the owner principal
$OWNER = dfx identity get-principal

# 4) Deploy canister (actor class requires owner as init argument)
dfx deploy cqt --argument "(principal \"$OWNER\")"

# 5) Check metadata
dfx canister call cqt name
dfx canister call cqt symbol
dfx canister call cqt decimals

# 6) Mint tokens to owner (must be called by owner)
dfx canister call cqt mint "(principal \"$OWNER\", 100000000)"

# 7) Check balance
dfx canister call cqt balanceOf "(principal \"$OWNER\")"

# 8) Create another identity and transfer
dfx identity new alice --storage-mode=plaintext 2>$null | Out-Null
$ALICE = dfx --identity alice identity get-principal
dfx canister call cqt transfer "(principal \"$ALICE\", 5000)"

dfx --identity alice canister call cqt balanceOf "(principal \"$ALICE\")"

# 9) Play the guessing game (guess in [0, 10))
dfx --identity alice canister call cqt guessAndWin '(3, 10)'
```

## Canister Interface

- `name() -> text`
- `symbol() -> text`
- `decimals() -> nat8`
- `totalSupply() -> nat`
- `balanceOf(principal) -> nat`
- `transfer(to: principal, amount: nat) -> bool`
- `mint(to: principal, amount: nat) -> bool` (owner only)
- `randomNat(maxExclusive: nat) -> nat`
- `guessAndWin(guess: nat, maxExclusive: nat) -> record { roll; won; prize }`

## Notes

- Randomness uses a simple nonce + time + caller hash suitable for local/dev. For production, consider using the management canister `raw_rand` pattern.
- The canister is an `actor class`; deployment requires passing the `owner` principal as an argument.

## Upgrade

```powershell
# Redeploy with upgrade (preserves state)
dfx deploy cqt --mode upgrade --argument "(principal \"$OWNER\")"

# Stop replica when done
dfx stop
```
