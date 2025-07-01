"""Enhanced element management for more reliable web automation."""

import logging
import time
from collections.abc import Callable
from typing import Any

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait


class ElementManager:
    """Manages element finding and interaction with enhanced reliability."""

    def __init__(self, driver: WebDriver, default_timeout: int = 10):
        self.driver = driver
        self.default_timeout = default_timeout
        self.logger = logging.getLogger(__name__)

    def find_element_safe(
        self,
        selectors: list[tuple[By, str]],
        timeout: int | None = None,
        condition: str = "presence",
        retry_stale: bool = True,
        scroll_into_view: bool = False,
    ) -> WebElement | None:
        """
        Find element with multiple fallback selectors and enhanced error handling.

        Args:
            selectors: List of (By, selector) tuples to try
            timeout: Maximum wait time (uses default if None)
            condition: Wait condition - "presence", "clickable", "visible"
            retry_stale: Whether to retry on stale element
            scroll_into_view: Whether to scroll element into view

        Returns:
            WebElement if found, None otherwise
        """
        timeout = timeout or self.default_timeout
        last_exception: Exception | None = None

        for selector_type, selector_value in selectors:
            try:
                element = self._wait_for_element(
                    selector_type, selector_value, timeout, condition
                )

                if element and scroll_into_view:
                    self._scroll_to_element(element)

                # Verify element is still valid
                if retry_stale:
                    element = self._verify_element_valid(
                        element, selector_type, selector_value, condition
                    )

                return element

            except (NoSuchElementException, TimeoutException) as e:
                self.logger.debug(
                    f"Element not found with {selector_type}='{selector_value}': {e}"
                )
                last_exception = e
                continue
            except Exception as e:
                self.logger.warning(f"Unexpected error finding element: {e}")
                last_exception = e
                continue

        self.logger.error(
            f"Element not found with any selector. Last error: {last_exception}"
        )
        return None

    def _wait_for_element(
        self, by: By, value: str, timeout: int, condition: str
    ) -> WebElement:
        """Wait for element with specified condition."""
        wait = WebDriverWait(self.driver, timeout)

        if condition == "presence":
            return wait.until(
                expected_conditions.presence_of_element_located((by, value))  # type: ignore[arg-type]
            )
        elif condition == "clickable":
            return wait.until(expected_conditions.element_to_be_clickable((by, value)))  # type: ignore[arg-type]
        elif condition == "visible":
            return wait.until(
                expected_conditions.visibility_of_element_located((by, value))  # type: ignore[arg-type]
            )
        else:
            raise ValueError(f"Unknown condition: {condition}")

    def _verify_element_valid(
        self, element: WebElement, by: By, value: str, condition: str
    ) -> WebElement:
        """Verify element is still valid, re-find if stale."""
        try:
            # Try to access element property to check if stale
            _ = element.is_enabled()
            return element
        except StaleElementReferenceException:
            self.logger.debug("Element was stale, re-finding...")
            return self._wait_for_element(by, value, 2, condition)

    def _scroll_to_element(self, element: WebElement) -> None:
        """Scroll element into view."""
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});",
                element,
            )
            time.sleep(0.5)  # Brief pause for scroll to complete
        except Exception as e:
            self.logger.debug(f"Could not scroll to element: {e}")

    def click_element_safe(
        self,
        element: WebElement,
        retry_attempts: int = 3,
        wait_after_click: float = 0.5,
    ) -> bool:
        """
        Click element with retry logic for common failures.

        Args:
            element: Element to click
            retry_attempts: Number of retry attempts
            wait_after_click: Time to wait after successful click

        Returns:
            True if click succeeded, False otherwise
        """
        for attempt in range(retry_attempts):
            try:
                # First try normal click
                element.click()
                time.sleep(wait_after_click)
                return True

            except ElementClickInterceptedException:
                self.logger.debug(
                    f"Click intercepted (attempt {attempt + 1}), "
                    "trying JavaScript click"
                )
                try:
                    self.driver.execute_script("arguments[0].click();", element)
                    time.sleep(wait_after_click)
                    return True
                except Exception as js_error:
                    self.logger.debug(f"JavaScript click failed: {js_error}")

            except ElementNotInteractableException:
                self.logger.debug(
                    f"Element not interactable (attempt {attempt + 1}), waiting..."
                )
                time.sleep(1)

            except StaleElementReferenceException:
                self.logger.error("Element became stale during click")
                return False

            except Exception as e:
                self.logger.warning(f"Unexpected error clicking element: {e}")

            if attempt < retry_attempts - 1:
                time.sleep(0.5)

        return False

    def wait_for_page_ready(self, timeout: int | None = None) -> bool:
        """
        Wait for page to be fully loaded and ready.

        Args:
            timeout: Maximum wait time

        Returns:
            True if page is ready, False otherwise
        """
        timeout = timeout or self.default_timeout

        try:
            # Wait for document ready state
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            # Wait for jQuery if present
            has_jquery = self.driver.execute_script(
                "return typeof jQuery !== 'undefined'"
            )

            if has_jquery:
                WebDriverWait(self.driver, timeout).until(
                    lambda d: d.execute_script("return jQuery.active == 0")
                )

            # Brief pause to ensure any final rendering
            time.sleep(0.5)
            return True

        except TimeoutException:
            self.logger.warning("Page did not become ready within timeout")
            return False
        except Exception as e:
            self.logger.error(f"Error waiting for page ready: {e}")
            return False

    def find_elements_safe(
        self, selectors: list[tuple[By, str]], timeout: int | None = None
    ) -> list[WebElement]:
        """
        Find multiple elements with fallback selectors.

        Args:
            selectors: List of (By, selector) tuples to try
            timeout: Maximum wait time

        Returns:
            List of found elements (may be empty)
        """
        timeout = timeout or self.default_timeout
        elements = []

        for selector_type, selector_value in selectors:
            try:
                wait = WebDriverWait(self.driver, timeout)
                elements = wait.until(
                    expected_conditions.presence_of_all_elements_located(
                        (selector_type, selector_value)  # type: ignore[arg-type]
                    )
                )
                if elements:
                    return elements
            except TimeoutException:
                continue
            except Exception as e:
                self.logger.debug(f"Error finding elements: {e}")
                continue

        return elements

    def retry_action(
        self,
        action: Callable[[], Any],
        max_attempts: int = 3,
        delay_between: float = 1.0,
        exceptions_to_retry: tuple[type[BaseException], ...] = (Exception,),
    ) -> tuple[bool, Any]:
        """
        Retry an action with configurable parameters.

        Args:
            action: Function to execute
            max_attempts: Maximum retry attempts
            delay_between: Delay between attempts
            exceptions_to_retry: Tuple of exception types to retry on

        Returns:
            Tuple of (success, result/exception)
        """
        last_exception = None

        for attempt in range(max_attempts):
            try:
                result = action()
                return True, result
            except exceptions_to_retry as e:
                last_exception = e
                self.logger.debug(
                    f"Action failed (attempt {attempt + 1}/{max_attempts}): {e}"
                )
                if attempt < max_attempts - 1:
                    time.sleep(delay_between)
            except Exception as e:
                # Don't retry on unexpected exceptions
                self.logger.error(f"Unexpected error in retry_action: {e}")
                return False, e

        return False, last_exception
