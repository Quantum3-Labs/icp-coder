"""
Re-initialization Task - Entry point for scheduled ChromaDB re-initialization.
This script is called by the cron job to perform the complete re-initialization.
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ingestion_orchestrator import IngestionOrchestrator


def main():
    """Main entry point for scheduled re-initialization task."""
    start_time = datetime.now()
    print(
        f"ChromaDB Re-initialization started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    try:
        # Initialize orchestrator
        orchestrator = IngestionOrchestrator()

        # Validate environment
        if not orchestrator.validate_environment():
            print("ERROR: Environment validation failed")
            return 1

        # Perform complete re-initialization
        success = orchestrator.perform_complete_reinit()

        end_time = datetime.now()
        duration = end_time - start_time

        if success:
            print(
                f"Re-initialization completed successfully at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            print(f"Total duration: {duration}")
            return 0
        else:
            print(
                f"Re-initialization failed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            print(f"Duration before failure: {duration}")
            return 1

    except KeyboardInterrupt:
        end_time = datetime.now()
        duration = end_time - start_time
        print(
            f"\nRe-initialization interrupted by user at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print(f"Duration before interruption: {duration}")
        return 1

    except Exception as e:
        end_time = datetime.now()
        duration = end_time - start_time
        print(f"ERROR: Unexpected exception during re-initialization: {e}")
        print(f"Failed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration before failure: {duration}")
        return 1


if __name__ == "__main__":
    """Execute the re-initialization task."""
    exit_code = main()
    sys.exit(exit_code)
