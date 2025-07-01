"""Slim orchestrator for golf booking system."""

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver

from src.booking_pages import (
    BookingConfirmationPage,
    DateSelectionPage,
    LoginPage,
    PlayerSelectionPage,
    TimeSlotPage,
)
from src.booking_strategies import ScheduledModeStrategy, TestModeStrategy
from src.config import BookingConfig, BookingMode, Selectors
from src.element_manager import ElementManager


class BookingOrchestrator:
    """Coordinates the booking process using modular components."""

    def __init__(
        self,
        mode: BookingMode,
        headless: bool = False,
        output_dirs: dict[str, Path] | None = None,
    ):
        self.mode = mode
        self.headless = headless
        self.output_dirs = output_dirs or {}
        self.driver: WebDriver | None = None
        self.element_manager: ElementManager | None = None
        self.pages: Any | None = None
        self.strategy: TestModeStrategy | ScheduledModeStrategy | None = None
        self.config = BookingConfig()
        self.selectors = Selectors()
        self.logger = logging.getLogger(__name__)

        # Validate environment
        self.username = os.getenv("GOLF_USERNAME")
        self.password = os.getenv("GOLF_PASSWORD")
        self.site_url = os.getenv("BOOKING_URL")

        if not all([self.username, self.password, self.site_url]):
            missing = [
                v
                for v in ["GOLF_USERNAME", "GOLF_PASSWORD", "BOOKING_URL"]
                if not os.getenv(v)
            ]
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")

    def initialize(self) -> bool:
        """Initialize browser and components."""
        try:
            self._setup_driver()
            self._setup_components()
            return self._navigate_to_site()
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            return False

    def _setup_driver(self) -> None:
        """Initialize Chrome WebDriver."""
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        if self.headless:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

        if not self.headless and self.driver:
            self.driver.maximize_window()

    def _setup_components(self) -> None:
        """Initialize page objects and strategy."""
        if self.driver:
            self.element_manager = ElementManager(
                self.driver, self.config.DEFAULT_WAIT_TIMEOUT
            )

        # Create page objects
        if self.driver and self.element_manager:
            args = (self.driver, self.element_manager, self.selectors, self.config)
            self.pages = type(
                "Pages",
                (),
                {
                    "login": LoginPage(*args),
                    "date": DateSelectionPage(*args),
                    "player": PlayerSelectionPage(*args),
                    "timeslot": TimeSlotPage(*args),
                    "confirmation": BookingConfirmationPage(*args),
                },
            )()

        # Create strategy
        if self.mode == BookingMode.TEST:
            self.strategy = TestModeStrategy(self.pages, self.config)
        else:
            self.strategy = ScheduledModeStrategy(self.pages, self.config)

    def _navigate_to_site(self) -> bool:
        """Navigate to booking site."""
        try:
            if self.driver and self.element_manager and self.site_url:
                self.driver.get(self.site_url)
                self.element_manager.wait_for_page_ready()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Navigation failed: {e}")
            return False

    def login(self) -> bool:
        """Execute login."""
        self.logger.info("🔑 Starting login process...")
        if self.pages:
            success = bool(
                self.pages.login.login(self.username, self.password, self.output_dirs)
            )
            if success:
                self.logger.info("✅ Login successful")
            else:
                self.logger.error("❌ Login failed")
            return success
        self.logger.error("❌ Login failed - pages not initialized")
        return False

    def execute_booking(self) -> bool:
        """Execute booking strategy."""
        self.logger.info("📅 Starting booking execution...")
        if self.strategy:
            success = bool(self.strategy.execute_booking(self.output_dirs))
            if success:
                self.logger.info("✅ Booking execution successful")
            else:
                self.logger.error("❌ Booking execution failed")
            return success
        self.logger.error("❌ Booking failed - strategy not initialized")
        return False

    def book_tee_time(self) -> bool:
        """Main booking method."""
        try:
            if not self.initialize():
                return False
            if not self.login():
                return False
            return self.execute_booking()
        except Exception as e:
            self.logger.error(f"Booking failed: {e}")
            return False

    def close(self) -> None:
        """Clean up."""
        if self.driver:
            self.driver.quit()
            self.driver = None
