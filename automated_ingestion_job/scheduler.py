"""
APScheduler-based ChromaDB Re-initialization Scheduler.
Cross-platform Python scheduler using Advanced Python Scheduler (APScheduler).
"""

import os
import sys
import json
import signal
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ingestion_orchestrator import IngestionOrchestrator


class ChromaDBScheduler:
    def __init__(self, config_path: str = "config.json"):
        """Initialize the ChromaDB scheduler."""
        self.config_path = config_path
        self.config = self._load_config()

        # Calculate project root dynamically
        job_dir = Path(__file__).parent
        self.project_root = job_dir.parent

        # Initialize scheduler with thread pool executor
        executors = {
            "default": ThreadPoolExecutor(
                max_workers=1
            )  # Only one re-init job at a time
        }

        self.scheduler = BlockingScheduler(
            executors=executors,
            timezone="UTC",  # Use UTC for consistency across platforms
        )

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _load_config(self) -> dict:
        """Load configuration from JSON file."""
        config_file = Path(__file__).parent / self.config_path

        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in configuration file: {config_file}")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.stop()
        sys.exit(0)

    def reinit_job(self):
        """
        Job function that performs ChromaDB re-initialization.
        This is called by APScheduler according to the schedule.
        """
        job_start = datetime.now()

        try:
            # Initialize orchestrator
            orchestrator = IngestionOrchestrator()

            # Validate environment
            if not orchestrator.validate_environment():
                return

            # Perform complete re-initialization
            orchestrator.perform_complete_reinit()

        except Exception as e:
            job_end = datetime.now()
            duration = job_end - job_start

            # Re-raise the exception for APScheduler to handle
            raise

    def add_reinit_job(self):
        """Add the re-initialization job to the scheduler."""
        # Parse cron schedule from config
        cron_schedule = self.config["cron"]["schedule"]

        # Parse cron format: "minute hour day month day_of_week"
        # Example: "0 2 * * *" = daily at 2 AM
        cron_parts = cron_schedule.split()
        if len(cron_parts) != 5:
            raise ValueError(f"Invalid cron schedule format: {cron_schedule}")

        minute, hour, day, month, day_of_week = cron_parts

        # Create cron trigger
        trigger = CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            timezone="UTC",
        )

        # Add job to scheduler
        job = self.scheduler.add_job(
            func=self.reinit_job,
            trigger=trigger,
            id="chromadb_reinit",
            name="ChromaDB Re-initialization",
            max_instances=1,  # Prevent overlapping executions
            coalesce=True,  # If missed, run once when scheduler starts
            misfire_grace_time=3600,  # Allow 1 hour grace time for missed jobs
        )

    def start(self):
        """Start the scheduler."""
        try:
            self.add_reinit_job()

            # Start the scheduler (this blocks the main thread)
            self.scheduler.start()

        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            raise

    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()


def main():
    """Main entry point for the scheduler."""
    print("ChromaDB Re-initialization Scheduler (APScheduler)")
    print("=" * 60)

    try:
        # Initialize and start scheduler
        scheduler = ChromaDBScheduler()
        scheduler.start()

    except FileNotFoundError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nScheduler stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Scheduler failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
