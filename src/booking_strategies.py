"""Booking strategy classes - minimal TDD implementation."""

import datetime
import logging
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pytz

pacific_tz = pytz.timezone("US/Pacific")


class BookingStrategy(ABC):
    """Abstract base class for booking strategies."""

    def __init__(self, pages: Any, config: Any) -> None:
        self.pages = pages
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def execute_booking(self, output_dirs: dict[str, Path]) -> bool:
        """Execute the booking strategy."""
        pass


class TestModeStrategy(BookingStrategy):
    """Strategy for test mode - single booking flow."""

    def execute_booking(self, output_dirs: dict[str, Path]) -> bool:
        """Execute test mode booking."""
        self.logger.info("🎯 Starting test mode booking flow...")
        
        # Simple flow for test mode
        steps = [
            ("Date Selection", self.pages.date.select_date),
            ("Player Selection", self.pages.player.select_players),
            ("Continue to Time Slots", self.pages.confirmation.continue_to_next_screen),
            ("Time Slot Selection", self._select_time_slot),
            ("Continue Final", self.pages.confirmation.continue_final_step),
            ("Accept Agreement", self.pages.confirmation.accept_agreement),
            ("Confirm Booking", self.pages.confirmation.confirm_booking),
        ]

        for step_name, step_func in steps:
            self.logger.info(f"🔄 Executing step: {step_name}")
            if not self._execute_step(step_func, output_dirs):
                self.logger.error(f"❌ Step failed: {step_name}")
                return False
            self.logger.info(f"✅ Step completed: {step_name}")
            
        self.logger.info("✅ All booking steps completed successfully!")
        return True

    def _execute_step(self, step_func: Any, output_dirs: dict[str, Path]) -> bool:
        """Execute a single step with error handling."""
        try:
            if step_func == self.pages.date.select_date:
                return bool(step_func(self.config.target_date_str, output_dirs))
            elif step_func == self.pages.player.select_players:
                return bool(
                    step_func(int(os.getenv("NUMBER_OF_PLAYERS", "4")), output_dirs)
                )
            elif step_func == self._select_time_slot:
                return self._select_time_slot(output_dirs)
            else:
                return bool(step_func(output_dirs))
        except Exception as e:
            self.logger.error(f"Step failed: {e}")
            return False

    def _select_time_slot(self, output_dirs: dict[str, Path]) -> bool:
        """Select time slot."""
        time_range = os.getenv("PREFERRED_TIME_RANGE", "08:00-11:00")
        return bool(self.pages.timeslot.select_time_slot(time_range, output_dirs))


class ScheduledModeStrategy(BookingStrategy):
    """Strategy for scheduled mode - wait for release time."""

    def execute_booking(self, output_dirs: dict[str, Path]) -> bool:
        """Execute scheduled mode booking."""
        if not self._wait_for_release_time():
            return False
        if not self._setup_booking_state(output_dirs):
            return False
        return self._wait_and_complete_booking(output_dirs)

    def _wait_for_release_time(self) -> bool:
        """Wait for release time."""
        now = datetime.datetime.now(pacific_tz)
        # Create release datetime directly in Pacific timezone
        # Use a proper naive date to avoid timezone issues
        today_naive = now.replace(tzinfo=None).date()
        naive_release = datetime.datetime.combine(today_naive, self.config.RELEASE_TIME)
        release_datetime = pacific_tz.localize(naive_release)

        if now > release_datetime:
            return False

        start_time = release_datetime - datetime.timedelta(
            seconds=self.config.PRE_ATTEMPT_SECONDS
        )
        wait_seconds = (start_time - now).total_seconds()
        if wait_seconds > 0:
            time.sleep(wait_seconds)
        return True

    def _setup_booking_state(self, output_dirs: dict[str, Path]) -> bool:
        """Set up initial booking state."""
        return (
            bool(self.pages.date.select_date(self.config.target_date_str, output_dirs))
            and bool(
                self.pages.player.select_players(
                    int(os.getenv("NUMBER_OF_PLAYERS", "4")), output_dirs
                )
            )
            and bool(self.pages.confirmation.continue_to_next_screen(output_dirs))
        )

    def _wait_and_complete_booking(self, output_dirs: dict[str, Path]) -> bool:
        """Wait for time slots and complete booking."""
        slots = self._wait_for_time_slots(output_dirs)
        if not slots:
            return False

        time_range = os.getenv("PREFERRED_TIME_RANGE", "08:00-11:00")
        return self.pages.timeslot.select_time_slot(
            time_range, output_dirs
        ) and self._complete_final_steps(output_dirs)

    def _wait_for_time_slots(
        self, output_dirs: dict[str, Path], max_attempts: int = 60
    ) -> list[Any]:
        """Wait for time slots to appear."""
        for attempt in range(max_attempts):
            slots = self.pages.timeslot.element_manager.find_elements_safe(
                [("css", "div.widget-teetime")], timeout=2
            )
            if slots:
                return list(slots)  # Explicit conversion to list
            if attempt < max_attempts - 1:
                self.pages.timeslot.driver.refresh()
        return []

    def _complete_final_steps(self, output_dirs: dict[str, Path]) -> bool:
        """Complete final booking steps."""
        return bool(
            self.pages.confirmation.continue_final_step(output_dirs)
            and self.pages.confirmation.accept_agreement(output_dirs)
            and self.pages.confirmation.confirm_booking(output_dirs)
        )
