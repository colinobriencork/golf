"""Page Object classes - focused, tested implementations."""

import datetime
import logging
import time
from pathlib import Path
from typing import Any

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


class BasePage:
    """Base class for all pages."""

    def __init__(
        self, driver: WebDriver, element_manager: Any, selectors: Any, config: Any
    ) -> None:
        self.driver = driver
        self.element_manager = element_manager
        self.selectors = selectors
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)


class LoginPage(BasePage):
    """Handles login functionality."""

    def login(self, username: str, password: str, output_dirs: dict[str, Path]) -> bool:
        """Execute login process."""
        try:
            # Click login tab
            tab = self.element_manager.find_element_safe(
                self.selectors.MEMBERS_TAB, condition="clickable"
            )
            if not tab or not self.element_manager.click_element_safe(tab):
                return False

            # Fill form
            email = self.element_manager.find_element_safe(
                self.selectors.EMAIL_FIELD, condition="visible"
            )
            password_field = self.element_manager.find_element_safe(
                self.selectors.PASSWORD_FIELD, condition="visible"
            )

            if not email or not password_field:
                return False

            email.clear()
            email.send_keys(username)
            password_field.clear()
            password_field.send_keys(password)

            # Submit
            login_btn = self.element_manager.find_element_safe(
                self.selectors.LOGIN_BUTTON, condition="clickable"
            )
            if not login_btn or not self.element_manager.click_element_safe(login_btn):
                return False

            # Verify success
            success = self.element_manager.find_element_safe(
                self.selectors.LOGIN_SUCCESS, timeout=15, condition="visible"
            )
            return success is not None

        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            return False


class DateSelectionPage(BasePage):
    """Handles date selection."""

    def select_date(self, target_date_str: str, output_dirs: dict[str, Path]) -> bool:
        """Select date from calendar."""
        try:
            target_date = datetime.datetime.strptime(target_date_str, "%Y-%m-%d")
            self._navigate_to_month(target_date)
            return self._click_date(target_date)
        except Exception as e:
            self.logger.error(f"Date selection failed: {e}")
            return False

    def _navigate_to_month(self, target_date: datetime.datetime) -> None:
        """Navigate to target month."""
        while True:
            title = self.element_manager.find_element_safe(
                self.selectors.MONTH_TITLE, condition="visible"
            )
            if not title:
                raise Exception("Month title not found")

            current = self._parse_month_title(title.text)
            if current.year == target_date.year and current.month == target_date.month:
                break

            next_btn = self.element_manager.find_element_safe(
                [self.selectors.MONTH_NAVIGATION[1]], condition="clickable"
            )
            if not next_btn or not self.element_manager.click_element_safe(next_btn):
                raise Exception("Cannot navigate month")

    def _click_date(self, target_date: datetime.datetime) -> bool:
        """Click specific date."""
        day_str = f"{target_date.day: 02d}"
        spans = self.driver.find_elements(
            By.XPATH,
            f"//span[not(contains(@class, 'text-muted')) and text()='{day_str}']",
        )

        if not spans:
            return False

        date_btn = spans[0].find_element(By.XPATH, "..")
        if date_btn.get_attribute("disabled"):
            return False

        return bool(self.element_manager.click_element_safe(date_btn))

    def _parse_month_title(self, title_text: str) -> datetime.datetime:
        """Parse month title to datetime."""
        return datetime.datetime.strptime(title_text, "%B %Y")


class PlayerSelectionPage(BasePage):
    """Handles player selection."""

    def select_players(self, num_players: int, output_dirs: dict[str, Path]) -> bool:
        """Select number of players."""
        try:
            selectors = [
                (t, s.format(num_players))
                for t, s in self.selectors.PLAYER_BUTTONS
                if "{}" in s
            ]
            player_btn = self.element_manager.find_element_safe(
                selectors, condition="clickable"
            )

            if not player_btn or "disabled" in player_btn.get_attribute("class"):
                return False

            return bool(self.element_manager.click_element_safe(player_btn))
        except Exception as e:
            self.logger.error(f"Player selection failed: {e}")
            return False


class TimeSlotPage(BasePage):
    """Handles time slot selection."""

    def select_time_slot(self, time_range: str, output_dirs: dict[str, Path]) -> bool:
        """Select time slot within range."""
        try:
            start_time, end_time = self._parse_time_range(time_range)
            slots = self._find_available_slots(start_time, end_time)

            if not slots:
                return False

            # Select middle slot
            slots.sort(key=lambda x: x[0])
            middle_slot = slots[len(slots) // 2]
            return bool(self.element_manager.click_element_safe(middle_slot[1]))

        except Exception as e:
            self.logger.error(f"Time slot selection failed: {e}")
            return False

    def _parse_time_range(self, time_range: str) -> tuple[datetime.time, datetime.time]:
        """Parse time range string."""
        start_str, end_str = time_range.split("-")
        start_time = datetime.datetime.strptime(start_str.strip(), "%H:%M").time()
        end_time = datetime.datetime.strptime(end_str.strip(), "%H:%M").time()
        return start_time, end_time

    def _find_available_slots(
        self, start_time: datetime.time, end_time: datetime.time
    ) -> list[tuple[datetime.time, WebElement]]:
        """Find available slots in time range."""
        containers = self.element_manager.find_elements_safe(
            [("css", "div.widget-teetime")], timeout=15
        )
        available = []

        for container in containers:
            try:
                time_elem = container.find_element(
                    By.CSS_SELECTOR, "div.widget-teetime-tag"
                )
                price_elem = container.find_element(
                    By.CSS_SELECTOR, "a.widget-teetime-rate"
                )

                if "disabled" in price_elem.get_attribute("class"):
                    continue

                slot_time = self._parse_time_from_element(time_elem)
                if slot_time and start_time <= slot_time <= end_time:
                    available.append((slot_time, price_elem))
            except Exception:
                continue

        return available

    def _parse_time_from_element(
        self, time_element: WebElement
    ) -> datetime.time | None:
        """Parse time from element text."""
        try:
            text = time_element.text.strip()
            for fmt in ["%I:%M %p", "%H:%M"]:
                try:
                    return datetime.datetime.strptime(text, fmt).time()
                except ValueError:
                    continue
        except Exception:
            pass
        return None


class BookingConfirmationPage(BasePage):
    """Handles booking confirmation steps."""

    def continue_to_next_screen(self, output_dirs: dict[str, Path]) -> bool:
        """Click continue button."""
        btn = self.element_manager.find_element_safe(
            self.selectors.CONTINUE_BUTTON, condition="clickable"
        )
        return (
            btn
            and "disabled" not in btn.get_attribute("class")
            and self.element_manager.click_element_safe(btn)
        )

    def continue_final_step(self, output_dirs: dict[str, Path]) -> bool:
        """Click final continue button."""
        btn = self.element_manager.find_element_safe(
            self.selectors.FINAL_CONTINUE, condition="clickable"
        )
        return (
            btn
            and "disabled" not in btn.get_attribute("class")
            and self.element_manager.click_element_safe(btn)
        )

    def accept_agreement(self, output_dirs: dict[str, Path]) -> bool:
        """Accept terms and conditions."""
        time.sleep(2)  # Allow page load
        checkbox = self.element_manager.find_element_safe(
            self.selectors.AGREE_CHECKBOX, scroll_into_view=True
        )

        if not checkbox:
            return False

        if not checkbox.is_selected():
            return bool(self.element_manager.click_element_safe(checkbox))
        return True

    def confirm_booking(self, output_dirs: dict[str, Path]) -> bool:
        """Confirm final booking."""
        btn = self.element_manager.find_element_safe(
            self.selectors.CONFIRM_BOOKING, condition="clickable"
        )
        return (
            btn
            and "disabled" not in btn.get_attribute("class")
            and self.element_manager.click_element_safe(btn)
        )
