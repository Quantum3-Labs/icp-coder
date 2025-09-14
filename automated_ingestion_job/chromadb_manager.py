"""
ChromaDB Manager for cleaning up and resetting the vector database.
"""

import os
import shutil
import json
from pathlib import Path


class ChromaDBManager:
    def __init__(self, config_path: str = "job/config.json"):
        """Initialize ChromaDB Manager with configuration."""
        self.config = self._load_config(config_path)

        # Calculate project root dynamically - it's always 1 level up from automation directory
        automation_dir = Path(__file__).parent
        self.project_root = automation_dir.parent

        self.chromadb_path = (
            self.project_root / self.config["directories"]["chromadb_data"]
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

    def delete_all_data(self) -> bool:
        """
        Remove entire chromadb_data directory.

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            if self.chromadb_path.exists():
                print(f"Deleting ChromaDB directory: {self.chromadb_path}")
                shutil.rmtree(self.chromadb_path)
                print("ChromaDB directory deleted successfully")
                return True
            else:
                print(f"ChromaDB directory does not exist: {self.chromadb_path}")
                return True
        except Exception as e:
            print(f"Error deleting ChromaDB directory: {e}")
            return False

    def verify_cleanup(self) -> bool:
        """
        Verify that ChromaDB directory has been cleaned up.

        Returns:
            bool: True if directory doesn't exist or is empty, False otherwise
        """
        if not self.chromadb_path.exists():
            print("ChromaDB directory successfully removed")
            return True

        # Check if directory is empty
        try:
            items = list(self.chromadb_path.iterdir())
            if not items:
                print("ChromaDB directory exists but is empty")
                return True
            else:
                print(f"ChromaDB directory not clean, contains {len(items)} items")
                return False
        except Exception as e:
            print(f"Error verifying cleanup: {e}")
            return False

    def create_fresh_directory(self) -> bool:
        """
        Create fresh ChromaDB directory structure.

        Returns:
            bool: True if creation was successful, False otherwise
        """
        try:
            self.chromadb_path.mkdir(parents=True, exist_ok=True)
            print(f"Created fresh ChromaDB directory: {self.chromadb_path}")
            return True
        except Exception as e:
            print(f"Error creating ChromaDB directory: {e}")
            return False

    def full_cleanup_and_reset(self) -> bool:
        """
        Perform complete cleanup and reset of ChromaDB.

        Returns:
            bool: True if entire process was successful, False otherwise
        """
        print("Starting full ChromaDB cleanup and reset...")

        # Step 1: Delete all data
        if not self.delete_all_data():
            return False

        # Step 2: Verify cleanup
        if not self.verify_cleanup():
            return False

        # Step 3: Create fresh directory
        if not self.create_fresh_directory():
            return False

        print("Full ChromaDB cleanup and reset completed successfully")
        return True


if __name__ == "__main__":
    """Test the ChromaDB manager functionality."""
    manager = ChromaDBManager()
    success = manager.full_cleanup_and_reset()

    if success:
        print("ChromaDB manager test completed successfully")
    else:
        print("ChromaDB manager test failed")
        exit(1)
