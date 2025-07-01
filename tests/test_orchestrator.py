"""Tests for booking orchestrator - written first to drive implementation."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.config import BookingMode


class TestBookingOrchestrator:
    """Test BookingOrchestrator behavior."""

    @pytest.mark.unit
    def test_orchestrator_can_be_created(
        self, mock_env_vars: Any, temp_output_dirs: dict[str, Path]
    ) -> None:
        """Test that BookingOrchestrator can be instantiated."""
        from src.booking_orchestrator import BookingOrchestrator

        orchestrator = BookingOrchestrator(
            mode=BookingMode.TEST, headless=True, output_dirs=temp_output_dirs
        )

        assert orchestrator.mode == BookingMode.TEST
        assert orchestrator.headless is True
        assert orchestrator.output_dirs == temp_output_dirs

    @pytest.mark.unit
    def test_orchestrator_validates_environment(
        self, monkeypatch: Any, temp_output_dirs: dict[str, Path]
    ) -> None:
        """Test that orchestrator validates required environment variables."""
        from src.booking_orchestrator import BookingOrchestrator

        # Clear environment variables
        monkeypatch.delenv("GOLF_USERNAME", raising=False)
        monkeypatch.delenv("GOLF_PASSWORD", raising=False)
        monkeypatch.delenv("BOOKING_URL", raising=False)

        with pytest.raises(ValueError) as exc_info:
            BookingOrchestrator(mode=BookingMode.TEST, output_dirs=temp_output_dirs)

        assert "Missing environment variables" in str(exc_info.value)
        assert "GOLF_USERNAME" in str(exc_info.value)
        assert "GOLF_PASSWORD" in str(exc_info.value)
        assert "BOOKING_URL" in str(exc_info.value)

    @pytest.mark.unit
    def test_initialize_success(
        self, mock_env_vars: Any, temp_output_dirs: dict[str, Path]
    ) -> None:
        """Test successful initialization."""
        from src.booking_orchestrator import BookingOrchestrator

        orchestrator = BookingOrchestrator(
            mode=BookingMode.TEST, headless=True, output_dirs=temp_output_dirs
        )

        with (
            patch.object(orchestrator, "_setup_driver") as mock_setup_driver,
            patch.object(orchestrator, "_setup_components") as mock_setup_components,
            patch.object(
                orchestrator, "_navigate_to_site", return_value=True
            ) as mock_navigate,
        ):
            result = orchestrator.initialize()

            assert result is True
            mock_setup_driver.assert_called_once()
            mock_setup_components.assert_called_once()
            mock_navigate.assert_called_once()

    @pytest.mark.unit
    def test_initialize_failure(
        self, mock_env_vars: Any, temp_output_dirs: dict[str, Path]
    ) -> None:
        """Test initialization failure."""
        from src.booking_orchestrator import BookingOrchestrator

        orchestrator = BookingOrchestrator(
            mode=BookingMode.TEST, headless=True, output_dirs=temp_output_dirs
        )

        with patch.object(
            orchestrator, "_setup_driver", side_effect=Exception("Driver error")
        ):
            result = orchestrator.initialize()

            assert result is False

    @pytest.mark.unit
    def test_setup_components_creates_pages_and_strategy(
        self, mock_env_vars: Any, temp_output_dirs: dict[str, Path]
    ) -> None:
        """Test that setup_components creates page objects and strategy."""
        from src.booking_orchestrator import BookingOrchestrator

        orchestrator = BookingOrchestrator(
            mode=BookingMode.TEST, headless=True, output_dirs=temp_output_dirs
        )
        orchestrator.driver = MagicMock()

        with (
            patch("src.booking_orchestrator.ElementManager"),
            patch("src.booking_orchestrator.LoginPage"),
            patch("src.booking_orchestrator.DateSelectionPage"),
            patch("src.booking_orchestrator.PlayerSelectionPage"),
            patch("src.booking_orchestrator.TimeSlotPage"),
            patch("src.booking_orchestrator.BookingConfirmationPage"),
            patch("src.booking_orchestrator.TestModeStrategy") as mock_strategy,
        ):
            orchestrator._setup_components()

            assert orchestrator.element_manager is not None
            assert orchestrator.pages is not None
            assert orchestrator.strategy is not None
            mock_strategy.assert_called_once()

    @pytest.mark.unit
    def test_setup_components_creates_scheduled_strategy(
        self, mock_env_vars: Any, temp_output_dirs: dict[str, Path]
    ) -> None:
        """Test that SCHEDULED mode creates ScheduledModeStrategy."""
        from src.booking_orchestrator import BookingOrchestrator

        orchestrator = BookingOrchestrator(
            mode=BookingMode.SCHEDULED, headless=True, output_dirs=temp_output_dirs
        )
        orchestrator.driver = MagicMock()

        with (
            patch("src.booking_orchestrator.ElementManager"),
            patch("src.booking_orchestrator.LoginPage"),
            patch("src.booking_orchestrator.DateSelectionPage"),
            patch("src.booking_orchestrator.PlayerSelectionPage"),
            patch("src.booking_orchestrator.TimeSlotPage"),
            patch("src.booking_orchestrator.BookingConfirmationPage"),
            patch("src.booking_orchestrator.ScheduledModeStrategy") as mock_strategy,
        ):
            orchestrator._setup_components()

            mock_strategy.assert_called_once()

    @pytest.mark.unit
    def test_login_delegates_to_login_page(
        self, mock_env_vars: Any, temp_output_dirs: dict[str, Path]
    ) -> None:
        """Test that login delegates to LoginPage."""
        from src.booking_orchestrator import BookingOrchestrator

        orchestrator = BookingOrchestrator(
            mode=BookingMode.TEST, headless=True, output_dirs=temp_output_dirs
        )

        # Mock pages
        mock_login_page = MagicMock()
        mock_login_page.login.return_value = True
        orchestrator.pages = MagicMock()
        orchestrator.pages.login = mock_login_page

        result = orchestrator.login()

        assert result is True
        mock_login_page.login.assert_called_once_with(
            orchestrator.username, orchestrator.password, temp_output_dirs
        )

    @pytest.mark.unit
    def test_execute_booking_delegates_to_strategy(
        self, mock_env_vars: Any, temp_output_dirs: dict[str, Path]
    ) -> None:
        """Test that execute_booking delegates to strategy."""
        from src.booking_orchestrator import BookingOrchestrator

        orchestrator = BookingOrchestrator(
            mode=BookingMode.TEST, headless=True, output_dirs=temp_output_dirs
        )

        # Mock strategy
        mock_strategy = MagicMock()
        mock_strategy.execute_booking.return_value = True
        orchestrator.strategy = mock_strategy

        result = orchestrator.execute_booking()

        assert result is True
        mock_strategy.execute_booking.assert_called_once_with(temp_output_dirs)

    @pytest.mark.unit
    def test_book_tee_time_full_flow_success(
        self, mock_env_vars: Any, temp_output_dirs: dict[str, Path]
    ) -> None:
        """Test successful complete booking flow."""
        from src.booking_orchestrator import BookingOrchestrator

        orchestrator = BookingOrchestrator(
            mode=BookingMode.TEST, headless=True, output_dirs=temp_output_dirs
        )

        with (
            patch.object(orchestrator, "initialize", return_value=True),
            patch.object(orchestrator, "login", return_value=True),
            patch.object(orchestrator, "execute_booking", return_value=True),
        ):
            result = orchestrator.book_tee_time()

            assert result is True

    @pytest.mark.unit
    def test_book_tee_time_initialization_failure(
        self, mock_env_vars: Any, temp_output_dirs: dict[str, Path]
    ) -> None:
        """Test booking fails when initialization fails."""
        from src.booking_orchestrator import BookingOrchestrator

        orchestrator = BookingOrchestrator(
            mode=BookingMode.TEST, headless=True, output_dirs=temp_output_dirs
        )

        with patch.object(orchestrator, "initialize", return_value=False):
            result = orchestrator.book_tee_time()

            assert result is False

    @pytest.mark.unit
    def test_book_tee_time_login_failure(
        self, mock_env_vars: Any, temp_output_dirs: dict[str, Path]
    ) -> None:
        """Test booking fails when login fails."""
        from src.booking_orchestrator import BookingOrchestrator

        orchestrator = BookingOrchestrator(
            mode=BookingMode.TEST, headless=True, output_dirs=temp_output_dirs
        )

        with (
            patch.object(orchestrator, "initialize", return_value=True),
            patch.object(orchestrator, "login", return_value=False),
        ):
            result = orchestrator.book_tee_time()

            assert result is False

    @pytest.mark.unit
    def test_close_cleans_up_driver(
        self, mock_env_vars: Any, temp_output_dirs: dict[str, Path]
    ) -> None:
        """Test that close method cleans up the driver."""
        from src.booking_orchestrator import BookingOrchestrator

        orchestrator = BookingOrchestrator(
            mode=BookingMode.TEST, headless=True, output_dirs=temp_output_dirs
        )

        mock_driver = MagicMock()
        orchestrator.driver = mock_driver

        orchestrator.close()

        mock_driver.quit.assert_called_once()
        assert orchestrator.driver is None

    @pytest.mark.unit
    def test_pages_structure(
        self, mock_env_vars: Any, temp_output_dirs: dict[str, Path]
    ) -> None:
        """Test that pages object has the expected structure."""
        from src.booking_orchestrator import BookingOrchestrator

        orchestrator = BookingOrchestrator(
            mode=BookingMode.TEST, headless=True, output_dirs=temp_output_dirs
        )
        orchestrator.driver = MagicMock()

        with (
            patch("src.booking_orchestrator.ElementManager"),
            patch("src.booking_orchestrator.LoginPage"),
            patch("src.booking_orchestrator.DateSelectionPage"),
            patch("src.booking_orchestrator.PlayerSelectionPage"),
            patch("src.booking_orchestrator.TimeSlotPage"),
            patch("src.booking_orchestrator.BookingConfirmationPage"),
        ):
            orchestrator._setup_components()

            assert hasattr(orchestrator.pages, "login")
            assert hasattr(orchestrator.pages, "date")
            assert hasattr(orchestrator.pages, "player")
            assert hasattr(orchestrator.pages, "timeslot")
            assert hasattr(orchestrator.pages, "confirmation")
