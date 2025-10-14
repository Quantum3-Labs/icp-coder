# Motoko Fungible Token Benchmark

This repository captures two separate build runs of the same instructions for creating a CQT token canister in Motoko with the DFX toolchain. The goal is to compare a workflow that used the `motoko-coder` MCP server for code generation against a workflow that relied on ChatGPT alone.

## Prompt

```
Create a Motoko project using dfx tool to build the following:
- Create a token with name CQT
- Function: 
    - transfer, mint (only the owner can mint)
    - generate random number function
    - guessing game: if user pick the same number as the generated one, the user will win some amount of token

Rules:
- Must meet all requirements above
- Handle any possible errors
- Adhere to the motoko documentation for best practice/syntax

Use motoko-coder MCP server to help you with development (this line is only for icp-coder version)

```

## Review

- ICP-Coder version follows the rule "Only the owner can mint" while ChatGPT version allow everyone
- Both implements the all functions as instructed
- ICP-Coder implement check and early returns for efficiency in method. Example: main.mo(45-52): `if (caller != owner) { return false }`
- ICP-Code use stable var for critical data ensuring persistence across upgrades while ChatGPT data is transient and will be lost on upgrades
- ICP-Coder has fallback mechanism on `randomness` if the first mechanism fail
- ICP-Coder use named constants while ChatGPT has magic numbers (not defined as constants)
