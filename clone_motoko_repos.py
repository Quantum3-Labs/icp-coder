import os
import subprocess
from tqdm import tqdm

# Folder for cloned repos
TARGET_DIR = "motoko_code_samples"
GITIGNORE_FILE = ".gitignore"

# List of GitHub repository URLs
repo_urls = [
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
    "https://github.com/ununhexium/idea-motoko-plugin",
    "https://github.com/dfinity/motoko-playground",
    "https://github.com/matthewhammer/ic-mini-terminal",
    "https://github.com/matthewhammer/motoko-bigtest",
    "https://github.com/ByronBecker/motoko-color",
    "https://github.com/kritzcreek/motoko-matchers",
    "https://github.com/kritzcreek/ic101",
    "https://github.com/enzoh/chronosphere",
    "https://github.com/matthewhammer/motoko-adapton",
    "https://github.com/enzoh/motoko-qr",
    "https://github.com/nomeata/motoko-scc",
    "https://github.com/chenyan2002/motoko-splay",
    "https://github.com/crusso/mo-parsec",
    "https://github.com/aviate-labs/parser-combinators.mo",
    "https://github.com/aviate-labs/sorted.mo",
    "https://github.com/herumi/ecdsa-motoko",
    "https://github.com/flyq/ecdsa_poc",
    "https://github.com/av1ctor/evm-txs.mo",
    "https://github.com/av1ctor/libsecp256k1.mo",
    "https://github.com/tgalal/motoko-bitcoin",
    "https://github.com/enzoh/motoko-crc",
    "https://github.com/aviate-labs/hash.mo",
    "https://github.com/timohanke/motoko-sha2",
    "https://github.com/enzoh/motoko-sha",
    "https://github.com/aviate-labs/crypto.mo",
    "https://github.com/flyq/motoko-sha224",
    "https://github.com/aviate-labs/rand.mo",
    "https://github.com/aviate-labs/array.mo",
    "https://github.com/dfinity/motoko-base",
    "https://github.com/matthewhammer/motoko-sequence",
    "https://github.com/aviate-labs/bimap.mo",
    "https://github.com/matthewhammer/motoko-crud",
    "https://github.com/edjcase/motoko_datetime",
    "https://github.com/nomeata/motoko-merkle-tree",
    "https://github.com/aviate-labs/queue.mo",
    "https://github.com/mix-labs/StableMap",
    "https://github.com/sardariuss/MotokoStableBTree",
    "https://github.com/kritzcreek/motoko-text-map",
    "https://github.com/ninegua/mutable-queue.mo",
    "https://github.com/aviate-labs/principal.mo",
    "https://github.com/canscale/StableHeapBTreeMap",
    "https://github.com/canscale/StableBuffer",
    "https://github.com/aviate-labs/stable.mo",
    "https://github.com/canscale/StableHashMap",
    "https://github.com/canscale/LinkedList",
    "https://github.com/canscale/StableRBTree",
    "https://github.com/aviate-labs/json.mo",
    "https://github.com/canscale/lexicographic-encoding",
    "https://github.com/flyq/motoko-base32",
    "https://github.com/edjcase/motoko_candid",
    "https://github.com/edjcase/motoko_cbor",
    "https://github.com/aviate-labs/encoding.mo",
    "https://github.com/enzoh/motoko-hex",
    "https://github.com/kritzcreek/motoko-json",
    "https://github.com/aviate-labs/uuid.mo",
    "https://github.com/edjcase/motoko_xml",
    "https://github.com/matthewhammer/motoko-graph",
    "https://github.com/matthewhammer/motoko-redraw",
    "https://github.com/aviate-labs/svg.mo",
    "https://github.com/ninegua/ic-logger",
    "https://github.com/kritzcreek/motoko-pretty",
    "https://github.com/vporton/passport-client-dfinity",
    "https://github.com/Expeera/IC-PayPortal",
    "https://github.com/aviate-labs/asset-storage.mo",
    "https://github.com/aviate-labs/graphql.mo",
    "https://github.com/kritzcreek/motoko-library-template",
    "https://github.com/aviate-labs/fmt.mo",
    "https://github.com/kritzcreek/motoko-regex",
    "https://github.com/demali-876/motoko_regex_engine",
    "https://github.com/tomijaga/http-parser.mo",
    "https://github.com/aviate-labs/io.mo",
    "https://github.com/aviate-labs/package-set",
    "https://github.com/dfinity/vessel-package-set",
    "https://github.com/motoko-bootcamp/education",
    "https://github.com/ic123-xyz/awesome-motoko",
    "https://github.com/Blocks-Editor/blocks",
    "https://github.com/dfinity/motoko-dev-server",
    "https://github.com/dfinity/prettier-plugin-motoko",
    "https://github.com/dfinity/motoko",
    "https://github.com/nomeata/ic-certification",
    "https://github.com/krpeacock/server",
    "https://github.com/ldclabs/ic-tee"
]

# Ensure the target folder exists
os.makedirs(TARGET_DIR, exist_ok=True)

# Load current .gitignore entries
ignored_paths = set()
if os.path.exists(GITIGNORE_FILE):
    with open(GITIGNORE_FILE, "r") as f:
        ignored_paths = set(line.strip() for line in f if line.strip())

# Open .gitignore to append new paths
with open(GITIGNORE_FILE, "a") as ignore_file:
    for url in tqdm(repo_urls, desc="Processing Repositories", unit="repo"):
        repo_name = url.split("/")[-1].replace(".git", "")
        repo_path = os.path.join(TARGET_DIR, repo_name)

        # Add to .gitignore if not already there
        ignore_entry = f"{TARGET_DIR}/{repo_name}"
        if ignore_entry not in ignored_paths:
            ignore_file.write(f"{ignore_entry}\n")

        # Skip if already cloned
        if os.path.exists(repo_path):
            continue

        # Try cloning
        try:
            subprocess.run(["git", "clone", url, repo_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            tqdm.write(f"❌ Failed to clone {url}")

print("\n✅ Done cloning all repositories.")
