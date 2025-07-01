"""Tests for page object classes - written first to drive implementation."""

import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.config import BookingConfig, Selectors


class TestLoginPage:
    """Test LoginPage behavior."""

    @pytest.fixture
    def login_page_deps(
        self, mock_driver: Any, mock_env_vars: Any
    ) -> tuple[Any, Any, Any, Any]:
        """Create dependencies for LoginPage."""
        element_manager = MagicMock()
        selectors = Selectors()
        config = BookingConfig()
        return mock_driver, element_manager, selectors, config

    @pytest.mark.unit
    def test_login_page_can_be_created(
        self, login_page_deps: tuple[Any, Any, Any, Any]
    ) -> None:
        """Test that LoginPage can be instantiated."""
        from src.booking_pages import LoginPage

        driver, element_manager, selectors, config = login_page_deps
        page = LoginPage(driver, element_manager, selectors, config)

        assert page.driver == driver
        assert page.element_manager == element_manager

    @pytest.mark.unit
    def test_login_success(
        self,
        login_page_deps: tuple[Any, Any, Any, Any],
        temp_output_dirs: dict[str, Path],
    ) -> None:
        """Test successful login flow."""
        from src.booking_pages import LoginPage

        driver, element_manager, selectors, config = login_page_deps
        element_manager.find_element_safe.return_value = MagicMock()
        element_manager.click_element_safe.return_value = True

        page = LoginPage(driver, element_manager, selectors, config)
        result = page.login("test@example.com", "password", temp_output_dirs)

        assert result is True
        assert (
            element_manager.find_element_safe.call_count >= 3
        )  # Tab, email, password fields

    @pytest.mark.unit
    def test_login_failure(
        self,
        login_page_deps: tuple[Any, Any, Any, Any],
        temp_output_dirs: dict[str, Path],
    ) -> None:
        """Test login failure when elements not found."""
        from src.booking_pages import LoginPage

        driver, element_manager, selectors, config = login_page_deps
        element_manager.find_element_safe.return_value = None

        page = LoginPage(driver, element_manager, selectors, config)
        result = page.login("test@example.com", "password", temp_output_dirs)

        assert result is False


class TestDateSelectionPage:
    """Test DateSelectionPage behavior."""

    @pytest.fixture
    def date_page_deps(self, mock_driver: Any) -> tuple[Any, Any, Any, Any]:
        """Create dependencies for DateSelectionPage."""
        element_manager = MagicMock()
        selectors = Selectors()
        config = BookingConfig()
        return mock_driver, element_manager, selectors, config

    @pytest.mark.unit
    def test_date_page_can_be_created(
        self, date_page_deps: tuple[Any, Any, Any, Any]
    ) -> None:
        """Test that DateSelectionPage can be instantiated."""
        from src.booking_pages import DateSelectionPage

        driver, element_manager, selectors, config = date_page_deps
        page = DateSelectionPage(driver, element_manager, selectors, config)

        assert page.driver == driver
        assert page.element_manager == element_manager

    @pytest.mark.unit
    def test_select_date_success(
        self,
        date_page_deps: tuple[Any, Any, Any, Any],
        temp_output_dirs: dict[str, Path],
    ) -> None:
        """Test successful date selection."""
        from src.booking_pages import DateSelectionPage

        driver, element_manager, selectors, config = date_page_deps

        # Mock successful element finding
        mock_element = MagicMock()
        mock_element.text = "April 2024"
        element_manager.find_element_safe.return_value = mock_element
        element_manager.click_element_safe.return_value = True

        # Mock driver find_elements for date clicking
        mock_span = MagicMock()
        mock_button = MagicMock()
        mock_button.get_attribute.return_value = None  # Not disabled
        mock_span.find_element.return_value = mock_button
        driver.find_elements.return_value = [mock_span]

        page = DateSelectionPage(driver, element_manager, selectors, config)
        result = page.select_date("2024-04-15", temp_output_dirs)

        assert result is True

    @pytest.mark.unit
    def test_select_date_parses_month_correctly(
        self, date_page_deps: tuple[Any, Any, Any, Any]
    ) -> None:
        """Test that month title parsing works."""
        from src.booking_pages import DateSelectionPage

        driver, element_manager, selectors, config = date_page_deps
        page = DateSelectionPage(driver, element_manager, selectors, config)

        result = page._parse_month_title("April 2024")

        assert result.year == 2024
        assert result.month == 4


class TestPlayerSelectionPage:
    """Test PlayerSelectionPage behavior."""

    @pytest.fixture
    def player_page_deps(self, mock_driver: Any) -> tuple[Any, Any, Any, Any]:
        """Create dependencies for PlayerSelectionPage."""
        element_manager = MagicMock()
        selectors = Selectors()
        config = BookingConfig()
        return mock_driver, element_manager, selectors, config

    @pytest.mark.unit
    def test_player_page_can_be_created(
        self, player_page_deps: tuple[Any, Any, Any, Any]
    ) -> None:
        """Test that PlayerSelectionPage can be instantiated."""
        from src.booking_pages import PlayerSelectionPage

        driver, element_manager, selectors, config = player_page_deps
        page = PlayerSelectionPage(driver, element_manager, selectors, config)

        assert page.driver == driver

    @pytest.mark.unit
    def test_select_players_success(
        self,
        player_page_deps: tuple[Any, Any, Any, Any],
        temp_output_dirs: dict[str, Path],
    ) -> None:
        """Test successful player selection."""
        from src.booking_pages import PlayerSelectionPage

        driver, element_manager, selectors, config = player_page_deps

        mock_button = MagicMock()
        mock_button.get_attribute.return_value = ""  # Not disabled
        element_manager.find_element_safe.return_value = mock_button
        element_manager.click_element_safe.return_value = True

        page = PlayerSelectionPage(driver, element_manager, selectors, config)
        result = page.select_players(4, temp_output_dirs)

        assert result is True
        element_manager.click_element_safe.assert_called_once_with(mock_button)


class TestTimeSlotPage:
    """Test TimeSlotPage behavior."""

    @pytest.fixture
    def timeslot_page_deps(self, mock_driver: Any) -> tuple[Any, Any, Any, Any]:
        """Create dependencies for TimeSlotPage."""
        element_manager = MagicMock()
        selectors = Selectors()
        config = BookingConfig()
        return mock_driver, element_manager, selectors, config

    @pytest.mark.unit
    def test_timeslot_page_can_be_created(
        self, timeslot_page_deps: tuple[Any, Any, Any, Any]
    ) -> None:
        """Test that TimeSlotPage can be instantiated."""
        from src.booking_pages import TimeSlotPage

        driver, element_manager, selectors, config = timeslot_page_deps
        page = TimeSlotPage(driver, element_manager, selectors, config)

        assert page.driver == driver

    @pytest.mark.unit
    def test_parse_time_range_valid(
        self, timeslot_page_deps: tuple[Any, Any, Any, Any]
    ) -> None:
        """Test parsing valid time range."""
        from src.booking_pages import TimeSlotPage

        driver, element_manager, selectors, config = timeslot_page_deps
        page = TimeSlotPage(driver, element_manager, selectors, config)

        start_time, end_time = page._parse_time_range("08:00-11:00")

        assert start_time == datetime.time(8, 0)
        assert end_time == datetime.time(11, 0)

    @pytest.mark.unit
    def test_select_time_slot_success(
        self,
        timeslot_page_deps: tuple[Any, Any, Any, Any],
        temp_output_dirs: dict[str, Path],
    ) -> None:
        """Test successful time slot selection."""
        from src.booking_pages import TimeSlotPage

        driver, element_manager, selectors, config = timeslot_page_deps

        # Mock finding time slot containers
        mock_container = MagicMock()
        mock_time_element = MagicMock()
        mock_time_element.text = "9:30 AM"
        mock_price_element = MagicMock()
        mock_price_element.get_attribute.return_value = ""  # Not disabled

        mock_container.find_element.side_effect = [
            mock_time_element,
            mock_price_element,
        ]
        element_manager.find_elements_safe.return_value = [mock_container]
        element_manager.click_element_safe.return_value = True

        page = TimeSlotPage(driver, element_manager, selectors, config)
        result = page.select_time_slot("08:00-11:00", temp_output_dirs)

        assert result is True


class TestBookingConfirmationPage:
    """Test BookingConfirmationPage behavior."""

    @pytest.fixture
    def confirmation_page_deps(self, mock_driver: Any) -> tuple[Any, Any, Any, Any]:
        """Create dependencies for BookingConfirmationPage."""
        element_manager = MagicMock()
        selectors = Selectors()
        config = BookingConfig()
        return mock_driver, element_manager, selectors, config

    @pytest.mark.unit
    def test_confirmation_page_can_be_created(
        self, confirmation_page_deps: tuple[Any, Any, Any, Any]
    ) -> None:
        """Test that BookingConfirmationPage can be instantiated."""
        from src.booking_pages import BookingConfirmationPage

        driver, element_manager, selectors, config = confirmation_page_deps
        page = BookingConfirmationPage(driver, element_manager, selectors, config)

        assert page.driver == driver

    @pytest.mark.unit
    def test_continue_to_next_screen_success(
        self,
        confirmation_page_deps: tuple[Any, Any, Any, Any],
        temp_output_dirs: dict[str, Path],
    ) -> None:
        """Test successful continue to next screen."""
        from src.booking_pages import BookingConfirmationPage

        driver, element_manager, selectors, config = confirmation_page_deps

        mock_button = MagicMock()
        mock_button.get_attribute.return_value = ""  # Not disabled
        element_manager.find_element_safe.return_value = mock_button
        element_manager.click_element_safe.return_value = True

        page = BookingConfirmationPage(driver, element_manager, selectors, config)
        result = page.continue_to_next_screen(temp_output_dirs)

        assert result is True

    @pytest.mark.unit
    def test_accept_agreement_success(
        self,
        confirmation_page_deps: tuple[Any, Any, Any, Any],
        temp_output_dirs: dict[str, Path],
    ) -> None:
        """Test successful agreement acceptance."""
        from src.booking_pages import BookingConfirmationPage

        driver, element_manager, selectors, config = confirmation_page_deps

        mock_checkbox = MagicMock()
        mock_checkbox.is_selected.return_value = False
        element_manager.find_element_safe.return_value = mock_checkbox
        element_manager.click_element_safe.return_value = True

        page = BookingConfirmationPage(driver, element_manager, selectors, config)
        result = page.accept_agreement(temp_output_dirs)

        assert result is True
        element_manager.click_element_safe.assert_called_once_with(mock_checkbox)

    @pytest.mark.unit
    def test_confirm_booking_success(
        self,
        confirmation_page_deps: tuple[Any, Any, Any, Any],
        temp_output_dirs: dict[str, Path],
    ) -> None:
        """Test successful booking confirmation."""
        from src.booking_pages import BookingConfirmationPage

        driver, element_manager, selectors, config = confirmation_page_deps

        mock_button = MagicMock()
        mock_button.get_attribute.return_value = ""  # Not disabled
        element_manager.find_element_safe.return_value = mock_button
        element_manager.click_element_safe.return_value = True

        page = BookingConfirmationPage(driver, element_manager, selectors, config)
        result = page.confirm_booking(temp_output_dirs)

        assert result is True
