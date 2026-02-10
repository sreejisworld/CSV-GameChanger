"""
URS File Monitor for CSV-GameChanger.

Uses the watchdog library to monitor the output/urs/ folder for
file modifications. When a URS Markdown file is modified, it
automatically triggers the TestGenerator and VTM generation
pipeline to refresh the Trustme Traceability Matrix.

Usage:
    python scripts/monitor_changes.py

:requirement: URS-10.1 - System shall monitor URS output directory
              and refresh the Traceability Matrix on changes.
"""
import sys
import time
import logging
from pathlib import Path
from datetime import datetime, timezone

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.generate_vtm import generate_vtm


# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
URS_DIR = PROJECT_ROOT / "output" / "urs"

# Logging setup
LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            PROJECT_ROOT / "monitor_changes.log",
            encoding="utf-8",
        ),
    ],
)

logger = logging.getLogger("urs_monitor")

# Debounce interval in seconds to avoid duplicate triggers
DEBOUNCE_SECONDS = 5


class URSChangeHandler(FileSystemEventHandler):
    """
    Watchdog event handler for URS file modifications.

    Monitors .md files in the output/urs/ directory and triggers
    the VTM regeneration pipeline when changes are detected.

    :requirement: URS-10.1 - System shall monitor URS output
                  directory and refresh the Traceability Matrix
                  on changes.
    """

    def __init__(self) -> None:
        """Initialize the handler with a debounce tracker."""
        super().__init__()
        self._last_trigger: float = 0.0

    def on_modified(self, event: FileModifiedEvent) -> None:
        """
        Handle file modification events.

        Filters for .md files and debounces rapid successive
        events before triggering VTM regeneration.

        :param event: The file system event.
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        if file_path.suffix.lower() != ".md":
            return

        # Debounce: ignore events within the cooldown window
        now = time.time()
        if now - self._last_trigger < DEBOUNCE_SECONDS:
            return
        self._last_trigger = now

        filename = file_path.name

        logger.info(
            "Change detected in %s..."
            "Updating Trustme Traceability Matrix...",
            filename,
        )

        self._refresh_vtm()

    def _refresh_vtm(self) -> None:
        """
        Trigger the VTM generation pipeline.

        Calls generate_vtm() which internally uses the
        TestGenerator agent to produce test scripts and
        writes the updated Trustme_Traceability_Matrix.csv.

        :requirement: URS-10.2 - System shall regenerate the
                      Traceability Matrix when URS files change.
        """
        try:
            result = generate_vtm(verbose=True)

            if result["status"] == "success":
                logger.info(
                    "Trustme Traceability Matrix updated "
                    "successfully. Rows: %s, Requirements: %s",
                    result["traceability_rows"],
                    result["requirements_processed"],
                )
            else:
                logger.error(
                    "VTM generation failed: %s",
                    result.get("message", "Unknown error"),
                )
        except Exception as e:
            logger.error(
                "Error refreshing Traceability Matrix: %s",
                e,
            )


def main() -> None:
    """
    Start the URS file monitor.

    Creates the output/urs/ directory if it does not exist,
    initializes the watchdog observer, and runs until interrupted.

    :requirement: URS-10.1 - System shall monitor URS output
                  directory and refresh the Traceability Matrix
                  on changes.
    """
    URS_DIR.mkdir(parents=True, exist_ok=True)

    handler = URSChangeHandler()
    observer = Observer()
    observer.schedule(handler, str(URS_DIR), recursive=False)

    logger.info("=" * 60)
    logger.info(
        "EVOLV Validation Factory - URS File Monitor Started"
    )
    logger.info("Monitoring: %s", URS_DIR)
    logger.info(
        "Debounce interval: %s seconds", DEBOUNCE_SECONDS
    )
    logger.info("=" * 60)
    logger.info(
        "Waiting for changes... (Press Ctrl+C to stop)"
    )

    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user.")
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()
