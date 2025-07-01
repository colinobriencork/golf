#!/usr/bin/env python3
"""Golf booking application - clean, modular main entry point."""

import datetime
import logging
import os
from pathlib import Path

import pytz
from dotenv import load_dotenv

from src.booking_orchestrator import BookingOrchestrator
from src.config import BookingMode

# Load environment variables
load_dotenv()

pacific_tz = pytz.timezone("US/Pacific")


def setup_output_dirs() -> dict[str, Path]:
    """Create organized output directories."""
    timestamp = datetime.datetime.now(pacific_tz).strftime("%Y%m%d_%H%M%S")
    base_dir = Path("chronogolf_output")
    run_dir = base_dir / f"run_{timestamp}"

    dirs = {
        "run_dir": run_dir,
        "screenshots_dir": run_dir / "screenshots",
        "logs_dir": run_dir / "logs",
    }

    for directory in dirs.values():
        directory.mkdir(exist_ok=True, parents=True)

    return dirs


def setup_logging(output_dirs: dict[str, Path]) -> None:
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(output_dirs["logs_dir"] / "booking.log"),
            logging.StreamHandler(),
        ],
    )

    # Reduce noise from selenium
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def main() -> bool:
    """Main execution function."""
    output_dirs = setup_output_dirs()
    setup_logging(output_dirs)

    # Determine mode
    mode = BookingMode.TEST if os.getenv("TEST_MODE") else BookingMode.SCHEDULED

    # Create orchestrator
    orchestrator = BookingOrchestrator(
        mode=mode, headless=True, output_dirs=output_dirs
    )

    try:
        logging.info(f"Starting {mode.name} mode booking")
        success = orchestrator.book_tee_time()

        if success:
            logging.info("✅ Booking completed successfully!")
            logging.info(f"Output saved to: {output_dirs['run_dir']}")
        else:
            logging.error("❌ Booking failed")

        return success

    except Exception as e:
        logging.error(f"Fatal error: {e}")
        return False
    finally:
        orchestrator.close()


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
