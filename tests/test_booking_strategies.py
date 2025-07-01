"""Tests for booking strategy classes - written first to drive implementation."""

import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import pytz

from src.config import BookingConfig


class TestTestModeStrategy:
    """Test TestModeStrategy behavior."""

    @pytest.fixture
    def mock_pages(self) -> Any:
        """Create mock page objects."""
        pages = MagicMock()
        pages.date.select_date.return_value = True
        pages.player.select_players.return_value = True
        pages.confirmation.continue_to_next_screen.return_value = True
        pages.confirmation.continue_final_step.return_value = True
        pages.confirmation.accept_agreement.return_value = True
        pages.confirmation.confirm_booking.return_value = True
        pages.timeslot.select_time_slot.return_value = True
        return pages

    @pytest.fixture
    def test_strategy(self, mock_pages: Any, mock_env_vars: Any) -> Any:
        """Create TestModeStrategy instance."""
        from src.booking_strategies import TestModeStrategy

        config = BookingConfig()
        return TestModeStrategy(mock_pages, config)

    @pytest.mark.unit
    def test_test_strategy_can_be_created(self, mock_pages: Any) -> None:
        """Test that TestModeStrategy can be instantiated."""
        from src.booking_strategies import TestModeStrategy

        config = BookingConfig()
        strategy = TestModeStrategy(mock_pages, config)

        assert strategy.pages == mock_pages
        assert strategy.config == config

    @pytest.mark.unit
    def test_execute_booking_success(
        self, test_strategy: Any, temp_output_dirs: dict[str, Path]
    ) -> None:
        """Test successful booking execution in test mode."""
        result = test_strategy.execute_booking(temp_output_dirs)

        assert result is True

        # Verify all steps were called
        test_strategy.pages.date.select_date.assert_called_once()
        test_strategy.pages.player.select_players.assert_called_once()
        test_strategy.pages.confirmation.continue_to_next_screen.assert_called_once()
        test_strategy.pages.timeslot.select_time_slot.assert_called_once()
        test_strategy.pages.confirmation.continue_final_step.assert_called_once()
        test_strategy.pages.confirmation.accept_agreement.assert_called_once()
        test_strategy.pages.confirmation.confirm_booking.assert_called_once()

    @pytest.mark.unit
    def test_execute_booking_failure_at_step(
        self, test_strategy: Any, temp_output_dirs: dict[str, Path]
    ) -> None:
        """Test booking failure when a step fails."""
        # Make player selection fail
        test_strategy.pages.player.select_players.return_value = False

        result = test_strategy.execute_booking(temp_output_dirs)

        assert result is False

        # Should stop at failed step
        test_strategy.pages.date.select_date.assert_called_once()
        test_strategy.pages.player.select_players.assert_called()
        # Should not proceed to time slot selection
        test_strategy.pages.timeslot.select_time_slot.assert_not_called()


class TestScheduledModeStrategy:
    """Test ScheduledModeStrategy behavior."""

    @pytest.fixture
    def mock_pages(self) -> Any:
        """Create mock page objects."""
        pages = MagicMock()
        pages.date.select_date.return_value = True
        pages.player.select_players.return_value = True
        pages.confirmation.continue_to_next_screen.return_value = True
        pages.confirmation.continue_final_step.return_value = True
        pages.confirmation.accept_agreement.return_value = True
        pages.confirmation.confirm_booking.return_value = True
        pages.timeslot.select_time_slot.return_value = True
        pages.timeslot.element_manager.find_elements_safe.return_value = [MagicMock()]
        pages.timeslot.driver.refresh = MagicMock()
        pages.timeslot.save_screenshot = MagicMock()
        return pages

    @pytest.fixture
    def scheduled_strategy(self, mock_pages: Any, mock_env_vars: Any) -> Any:
        """Create ScheduledModeStrategy instance."""
        from src.booking_strategies import ScheduledModeStrategy

        config = BookingConfig()
        return ScheduledModeStrategy(mock_pages, config)

    @pytest.mark.unit
    def test_scheduled_strategy_can_be_created(self, mock_pages: Any) -> None:
        """Test that ScheduledModeStrategy can be instantiated."""
        from src.booking_strategies import ScheduledModeStrategy

        config = BookingConfig()
        strategy = ScheduledModeStrategy(mock_pages, config)

        assert strategy.pages == mock_pages
        assert strategy.config == config

    @pytest.mark.unit
    def test_wait_for_release_time_future(self, scheduled_strategy: Any) -> None:
        """Test waiting for future release time."""
        pacific_tz = pytz.timezone("US/Pacific")

        # Mock current time to be before release time (use localize for proper timezone)
        # Make it a bit earlier to ensure there's a wait period
        mock_now = pacific_tz.localize(datetime.datetime(2024, 4, 15, 6, 59, 45))

        with (
            patch("src.booking_strategies.datetime") as mock_datetime_module,
            patch("time.sleep") as mock_sleep,
        ):
            # Mock only the datetime class, not the whole module
            mock_datetime_module.datetime.now.return_value = mock_now
            # Keep original functions
            mock_datetime_module.datetime.combine = datetime.datetime.combine
            mock_datetime_module.timedelta = datetime.timedelta

            result = scheduled_strategy._wait_for_release_time()

            assert result is True
            mock_sleep.assert_called_once()

    @pytest.mark.unit
    def test_wait_for_release_time_past(self, scheduled_strategy: Any) -> None:
        """Test when release time has already passed."""
        pacific_tz = pytz.timezone("US/Pacific")

        # Mock current time to be after release time (use localize for proper timezone)
        mock_now = pacific_tz.localize(datetime.datetime(2024, 4, 15, 8, 0, 0))

        with patch("src.booking_strategies.datetime") as mock_datetime_module:
            mock_datetime_module.datetime.now.return_value = mock_now
            # Keep original functions
            mock_datetime_module.datetime.combine = datetime.datetime.combine
            mock_datetime_module.timedelta = datetime.timedelta

            result = scheduled_strategy._wait_for_release_time()

            assert result is False

    @pytest.mark.unit
    def test_setup_booking_state_success(
        self, scheduled_strategy: Any, temp_output_dirs: dict[str, Path]
    ) -> None:
        """Test successful booking state setup."""
        result = scheduled_strategy._setup_booking_state(temp_output_dirs)

        assert result is True
        scheduled_strategy.pages.date.select_date.assert_called_once()
        scheduled_strategy.pages.player.select_players.assert_called_once()
        scheduled_strategy.pages.confirmation.continue_to_next_screen.assert_called_once()

    @pytest.mark.unit
    def test_wait_for_time_slots_found_immediately(
        self, scheduled_strategy: Any, temp_output_dirs: dict[str, Path]
    ) -> None:
        """Test when time slots are found on first attempt."""
        mock_slots = [MagicMock(), MagicMock()]
        scheduled_strategy.pages.timeslot.element_manager.find_elements_safe.return_value = mock_slots

        result = scheduled_strategy._wait_for_time_slots(
            temp_output_dirs, max_attempts=3
        )

        assert result == mock_slots
        assert len(result) == 2

    @pytest.mark.unit
    def test_wait_for_time_slots_not_found(
        self, scheduled_strategy: Any, temp_output_dirs: dict[str, Path]
    ) -> None:
        """Test when no time slots are found."""
        scheduled_strategy.pages.timeslot.element_manager.find_elements_safe.return_value = []

        result = scheduled_strategy._wait_for_time_slots(
            temp_output_dirs, max_attempts=2
        )

        assert result == []
        # Should have refreshed once (attempt 1)
        scheduled_strategy.pages.timeslot.driver.refresh.assert_called_once()

    @pytest.mark.unit
    def test_complete_final_steps_success(
        self, scheduled_strategy: Any, temp_output_dirs: dict[str, Path]
    ) -> None:
        """Test successful completion of final steps."""
        result = scheduled_strategy._complete_final_steps(temp_output_dirs)

        assert result is True
        scheduled_strategy.pages.confirmation.continue_final_step.assert_called_once()
        scheduled_strategy.pages.confirmation.accept_agreement.assert_called_once()
        scheduled_strategy.pages.confirmation.confirm_booking.assert_called_once()

    @pytest.mark.unit
    def test_execute_booking_success(
        self, scheduled_strategy: Any, temp_output_dirs: dict[str, Path]
    ) -> None:
        """Test full scheduled booking execution."""
        # Mock successful wait for release time
        with (
            patch.object(
                scheduled_strategy, "_wait_for_release_time", return_value=True
            ),
            patch.object(scheduled_strategy, "_setup_booking_state", return_value=True),
            patch.object(
                scheduled_strategy, "_wait_and_complete_booking", return_value=True
            ),
        ):
            result = scheduled_strategy.execute_booking(temp_output_dirs)

            assert result is True
