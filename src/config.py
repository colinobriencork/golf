"""Configuration and data classes."""

import datetime
from dataclasses import dataclass
from enum import Enum, auto

import pytz
from selenium.webdriver.common.by import By

pacific_tz = pytz.timezone("US/Pacific")


class BookingMode(Enum):
    TEST = auto()
    SCHEDULED = auto()


class BookingError(Exception):
    """Custom exception for booking-related errors."""

    pass


@dataclass
class Selectors:
    """Store all CSS/XPATH selectors in one place."""

    MEMBERS_TAB = [
        (By.CSS_SELECTOR, "li.widget-auth-tab--member"),
        (By.CSS_SELECTOR, "li.booking-widget-login"),
        (By.XPATH, "//li[contains(@class, 'widget-auth-tab--member')]"),
    ]
    EMAIL_FIELD = [
        (By.ID, "email"),
        (By.NAME, "email"),
        (By.CSS_SELECTOR, "input[type='email']"),
    ]
    PASSWORD_FIELD = [
        (By.ID, "password"),
        (By.NAME, "password"),
        (By.CSS_SELECTOR, "input[type='password']"),
    ]
    LOGIN_BUTTON = [
        (By.CSS_SELECTOR, "input.fl-button-primary[type='submit'][value='Log in']"),
        (By.CSS_SELECTOR, "input[type='submit']"),
    ]
    LOGIN_SUCCESS = [
        (By.CSS_SELECTOR, "a.widget-auth-tab--logout"),
        (By.CSS_SELECTOR, "a.widget-link.icon-exit"),
        (By.CSS_SELECTOR, "[qa-class='widget-auth-tab--logout']"),
    ]
    DATE_BUTTON = [
        (By.CSS_SELECTOR, "button.btn.btn-default.btn-sm[ng-click*='select']"),
        (By.XPATH, "//button[contains(@class, 'btn-sm')]//span[text()='{}']/.."),
    ]
    DATE_NAVIGATION = [
        (By.CSS_SELECTOR, "button.btn.btn-default.btn-sm[ng-click*='move(-1)']"),
        (By.CSS_SELECTOR, "button.btn.btn-default.btn-sm[ng-click*='move(1)']"),
    ]
    MONTH_LABEL = [
        (By.CSS_SELECTOR, "button.btn.btn-default.btn-sm.uib-title strong"),
    ]
    CALENDAR = [
        (By.CSS_SELECTOR, "button.btn.btn-default.btn-sm"),
    ]
    MONTH_NAVIGATION = [
        (By.CSS_SELECTOR, "button.btn.btn-default.btn-sm[ng-click*='move(-1)']"),
        (By.CSS_SELECTOR, "button.btn.btn-default.btn-sm[ng-click*='move(1)']"),
    ]
    MONTH_TITLE = [
        (By.CSS_SELECTOR, "button.btn.btn-default.btn-sm.uib-title strong"),
    ]
    PLAYER_BUTTONS = [
        (By.CSS_SELECTOR, "a.toggler-heading.fl-button[ng-model='step.nbPlayers']"),
        (By.CSS_SELECTOR, "a.toggler-heading[ng-model='step.nbPlayers']"),
        (By.CSS_SELECTOR, "a[ng-model='step.nbPlayers']"),
        (
            By.XPATH,
            "//a[contains(@class, 'toggler-heading') and contains(text(), '{}')]",
        ),
        (By.XPATH, "//a[contains(@class, 'fl-button') and contains(text(), '{}')]"),
        (By.XPATH, "//a[contains(@ng-model, 'nbPlayers') and contains(text(), '{}')]"),
    ]
    CONTINUE_BUTTON = [
        (By.CSS_SELECTOR, "button.fl-button-primary[ng-click*='continue']"),
        (
            By.XPATH,
            "//button[contains(@class, 'fl-button-primary') and "
            "contains(., 'Continue')]",
        ),
    ]
    TIME_SLOTS = [
        (By.CSS_SELECTOR, "div.widget-teetime-tag"),
        (By.CSS_SELECTOR, "a.widget-teetime-rate"),
    ]
    FINAL_CONTINUE = [
        (
            By.CSS_SELECTOR,
            "button.fl-button.fl-button-primary[ng-click='confirmStep()']",
        ),
        (By.CSS_SELECTOR, "button.fl-button-block.fl-button-primary"),
        (
            By.XPATH,
            "//button[contains(@class, 'fl-button-primary') and text()='Continue']",
        ),
    ]
    AGREE_CHECKBOX = [
        (
            By.CSS_SELECTOR,
            "input[ng-model='vm.acceptTermsAndConditions'][type='checkbox']",
        ),
        (By.CSS_SELECTOR, "input.fl-checkbox-input[ng-required='true']"),
        (By.CSS_SELECTOR, "input[type='checkbox'][required]"),
    ]
    CONFIRM_BOOKING = [
        (By.CSS_SELECTOR, "button.fl-button-primary[type='submit']"),
        (By.CSS_SELECTOR, "button.fl-button-primary.fl-button-block"),
        (
            By.XPATH,
            "//button[contains(@class, 'fl-button-primary') and "
            "contains(text(), 'Confirm')]",
        ),
    ]


@dataclass
class BookingConfig:
    """Store booking configuration with validation."""

    RELEASE_TIME: datetime.time = datetime.time(7, 0)
    ADVANCE_DAYS: int = 7
    PRE_ATTEMPT_SECONDS: int = 10
    MAX_RETRIES: int = 60
    RETRY_DELAY: int = 1
    DEFAULT_WAIT_TIMEOUT: int = 3

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.ADVANCE_DAYS < 0:
            raise ValueError("ADVANCE_DAYS must be non-negative")
        if self.PRE_ATTEMPT_SECONDS < 0:
            raise ValueError("PRE_ATTEMPT_SECONDS must be non-negative")
        if self.MAX_RETRIES < 1:
            raise ValueError("MAX_RETRIES must be at least 1")
        if self.DEFAULT_WAIT_TIMEOUT < 1:
            raise ValueError("DEFAULT_WAIT_TIMEOUT must be at least 1")

    @property
    def target_date(self) -> datetime.date:
        """Calculate target booking date."""
        return datetime.datetime.now(pacific_tz).date() + datetime.timedelta(
            days=self.ADVANCE_DAYS
        )

    @property
    def target_date_str(self) -> str:
        """Get target date in YYYY-MM-DD format."""
        return self.target_date.strftime("%Y-%m-%d")
