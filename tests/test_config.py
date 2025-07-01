"""Tests for configuration and data classes."""

import datetime
from unittest.mock import patch

import pytest
import pytz
from selenium.webdriver.common.by import By

from src.config import BookingConfig, BookingError, BookingMode, Selectors


class TestBookingMode:
    """Test the BookingMode enum."""

    @pytest.mark.unit
    def test_booking_modes_exist(self) -> None:
        """Test that required booking modes are defined."""
        assert BookingMode.TEST
        assert BookingMode.SCHEDULED

    @pytest.mark.unit
    def test_booking_mode_values(self) -> None:
        """Test that booking modes have unique values."""
        test_mode = BookingMode.TEST
        scheduled_mode = BookingMode.SCHEDULED
        assert test_mode != scheduled_mode
        assert test_mode.value != scheduled_mode.value


class TestBookingError:
    """Test the custom BookingError exception."""

    @pytest.mark.unit
    def test_booking_error_is_exception(self) -> None:
        """Test that BookingError is an Exception subclass."""
        assert issubclass(BookingError, Exception)

    @pytest.mark.unit
    def test_booking_error_message(self) -> None:
        """Test that BookingError can be raised with a message."""
        with pytest.raises(BookingError) as exc_info:
            raise BookingError("Test error message")
        assert str(exc_info.value) == "Test error message"


class TestSelectors:
    """Test the Selectors dataclass."""

    @pytest.mark.unit
    def test_selectors_initialization(self) -> None:
        """Test that Selectors can be initialized."""
        selectors = Selectors()
        assert selectors is not None

    @pytest.mark.unit
    def test_selector_structure(self) -> None:
        """Test that selectors are lists of tuples with By and string."""
        selectors = Selectors()

        # Check a few key selectors
        assert isinstance(selectors.MEMBERS_TAB, list)
        assert len(selectors.MEMBERS_TAB) > 0
        assert all(isinstance(s, tuple) and len(s) == 2 for s in selectors.MEMBERS_TAB)
        assert all(isinstance(s[0], type(By.ID)) for s in selectors.MEMBERS_TAB)
        assert all(isinstance(s[1], str) for s in selectors.MEMBERS_TAB)

    @pytest.mark.unit
    def test_all_required_selectors_exist(self) -> None:
        """Test that all required selectors are defined."""
        selectors = Selectors()
        required_selectors = [
            "MEMBERS_TAB",
            "EMAIL_FIELD",
            "PASSWORD_FIELD",
            "LOGIN_BUTTON",
            "LOGIN_SUCCESS",
            "DATE_BUTTON",
            "PLAYER_BUTTONS",
            "CONTINUE_BUTTON",
            "TIME_SLOTS",
            "FINAL_CONTINUE",
            "AGREE_CHECKBOX",
            "CONFIRM_BOOKING",
        ]

        for selector_name in required_selectors:
            assert hasattr(selectors, selector_name), (
                f"Missing selector: {selector_name}"
            )
            selector_value = getattr(selectors, selector_name)
            assert isinstance(selector_value, list), f"{selector_name} should be a list"
            assert len(selector_value) > 0, f"{selector_name} should not be empty"


class TestBookingConfig:
    """Test the BookingConfig dataclass."""

    @pytest.mark.unit
    def test_booking_config_initialization(self) -> None:
        """Test that BookingConfig can be initialized with defaults."""
        config = BookingConfig()
        assert datetime.time(7, 0) == config.RELEASE_TIME
        assert config.advance_days >= 1  # Should read from env or use default
        assert config.PRE_ATTEMPT_SECONDS == 10
        assert config.MAX_RETRIES == 60
        assert config.RETRY_DELAY == 1
        assert config.DEFAULT_WAIT_TIMEOUT == 3

    @pytest.mark.unit
    def test_target_date_calculation(self) -> None:
        """Test that target_date calculates correctly."""
        config = BookingConfig()
        pacific_tz = pytz.timezone("US/Pacific")

        # Mock the current time and advance days
        mock_now = datetime.datetime(2024, 4, 15, 10, 0, 0, tzinfo=pacific_tz)
        with (
            patch("src.config.datetime") as mock_datetime,
            patch("os.getenv") as mock_getenv,
        ):
            # Keep original datetime for timedelta
            mock_datetime.datetime.now.return_value = mock_now
            mock_datetime.timedelta = datetime.timedelta
            mock_getenv.return_value = "7"  # Mock ADVANCE_DAYS=7

            expected_date = datetime.date(2024, 4, 22)  # 7 days later
            assert config.target_date == expected_date

    @pytest.mark.unit
    def test_target_date_str_format(self) -> None:
        """Test that target_date_str returns correct format."""
        config = BookingConfig()
        pacific_tz = pytz.timezone("US/Pacific")

        # Mock the current time
        mock_now = datetime.datetime(2024, 4, 15, 10, 0, 0, tzinfo=pacific_tz)
        with (
            patch("src.config.datetime") as mock_datetime,
            patch("os.getenv") as mock_getenv,
        ):
            mock_datetime.datetime.now.return_value = mock_now
            mock_datetime.timedelta = datetime.timedelta
            mock_getenv.return_value = "7"  # Mock ADVANCE_DAYS=7

            assert config.target_date_str == "2024-04-22"

    @pytest.mark.unit
    def test_config_immutability(self) -> None:
        """Test that config values are constants (convention-based)."""
        config = BookingConfig()

        # These should be treated as constants (UPPER_CASE naming)
        assert hasattr(config, "RELEASE_TIME")
        assert hasattr(config, "advance_days")  # Now a property, not attribute
        assert hasattr(config, "PRE_ATTEMPT_SECONDS")
