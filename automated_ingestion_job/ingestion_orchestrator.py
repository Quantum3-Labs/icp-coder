"""
Ingestion Orchestrator for coordinating the complete ChromaDB re-initialization pipeline.
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from chromadb_manager import ChromaDBManager


class IngestionOrchestrator:
    def __init__(self, config_path: str = "config.json"):
        """Initialize Ingestion Orchestrator with configuration."""
        self.config = self._load_config(config_path)

        # Calculate project root dynamically - it's always 1 level up from automated_ingestion_job directory
        job_dir = Path(__file__).parent
        self.project_root = job_dir.parent

        self.chromadb_manager = ChromaDBManager(config_path)

        # Paths to scripts
        self.clone_repos_script = self.project_root / "clone_motoko_repos.py"
        self.clone_docs_script = self.project_root / "clone_motoko_docs.py"
        self.ingest_samples_script = (
            self.project_root / "ingest" / "motoko_samples_ingester.py"
        )
        self.ingest_docs_script = (
            self.project_root / "ingest" / "motoko_docs_ingester.py"
        )

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file."""
        try:
            # Handle relative path from job directory
            if not os.path.isabs(config_path):
                # If running from job directory, use current directory
                if os.path.basename(os.getcwd()) == "job":
                    config_path = "config.json"
                # Otherwise assume running from project root

            with open(config_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in configuration file: {config_path}")

    def _run_script(self, script_path: Path, description: str) -> bool:
        """
        Run a Python script and handle the result.

        Args:
            script_path: Path to the script to run
            description: Description for logging

        Returns:
            bool: True if script executed successfully, False otherwise
        """
        if not script_path.exists():
            print(f"ERROR: Script not found: {script_path}")
            return False

        try:

            # Run the script from project root directory
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=self.config.get("git", {}).get("clone_timeout", 300),
            )

            if result.returncode == 0:
                return True
            else:
                print(
                    f"ERROR: {description} failed with return code {result.returncode}"
                )
                if result.stderr:
                    print(f"Error output: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print(
                f"ERROR: {description} timed out after {self.config.get('git', {}).get('clone_timeout', 300)} seconds"
            )
            return False
        except Exception as e:
            print(f"ERROR: Exception during {description}: {e}")
            return False

    def perform_complete_reinit(self) -> bool:
        """
        Perform complete re-initialization of ChromaDB.
        Always executes regardless of repository state.

        Returns:
            bool: True if entire process was successful, False otherwise
        """

        # Step 1: Clean up ChromaDB
        if not self.chromadb_manager.full_cleanup_and_reset():
            print("ERROR: ChromaDB cleanup failed")
            return False

        # Step 2: Clone Motoko repositories
        if not self._run_script(self.clone_repos_script, "Motoko repositories cloning"):
            print("ERROR: Failed to clone Motoko repositories")
            return False

        # Step 3: Clone Motoko documentation
        if not self._run_script(self.clone_docs_script, "Motoko documentation cloning"):
            print("ERROR: Failed to clone Motoko documentation")
            return False

        # Step 4: Ingest code samples
        if not self._run_script(self.ingest_samples_script, "Code samples ingestion"):
            print("ERROR: Failed to ingest code samples")
            return False

        # Step 5: Ingest documentation
        if not self._run_script(self.ingest_docs_script, "Documentation ingestion"):
            print("ERROR: Failed to ingest documentation")
            return False

        return True

    def validate_environment(self) -> bool:
        """
        Validate that all required scripts and directories exist.

        Returns:
            bool: True if environment is valid, False otherwise
        """

        required_scripts = [
            (self.clone_repos_script, "Clone Motoko repos script"),
            (self.clone_docs_script, "Clone Motoko docs script"),
            (self.ingest_samples_script, "Ingest samples script"),
            (self.ingest_docs_script, "Ingest docs script"),
        ]

        missing_scripts = []
        for script_path, description in required_scripts:
            if not script_path.exists():
                missing_scripts.append((script_path, description))

        if missing_scripts:
            print(f"ERROR: {len(missing_scripts)} required scripts are missing")
            return False

        return True


if __name__ == "__main__":
    orchestrator = IngestionOrchestrator()

    # Validate environment first
    if not orchestrator.validate_environment():
        exit(1)

    # Perform complete re-initialization
    success = orchestrator.perform_complete_reinit()

    if not success:
        exit(1)
