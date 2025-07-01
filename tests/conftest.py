"""Shared pytest fixtures and configuration."""

import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from selenium.webdriver.remote.webelement import WebElement


@pytest.fixture
def mock_env_vars(monkeypatch: Any) -> dict[str, str]:
    """Set up test environment variables."""
    test_env = {
        "GOLF_USERNAME": "test@example.com",
        "GOLF_PASSWORD": "testpassword123",
        "BOOKING_URL": "https://test.chronogolf.com",
        "PREFERRED_TIME_RANGE": "08:00-11:00",
        "NUMBER_OF_PLAYERS": "4",
        "TEST_MODE": "true",
    }
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)
    return test_env


@pytest.fixture
def temp_output_dirs() -> Generator[dict[str, Path], None, None]:
    """Create temporary directories for test outputs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)
        dirs = {
            "run_dir": base_path / "test_run",
            "screenshots_dir": base_path / "test_run" / "screenshots",
            "logs_dir": base_path / "test_run" / "logs",
        }
        for directory in dirs.values():
            directory.mkdir(exist_ok=True, parents=True)
        yield dirs


@pytest.fixture
def mock_driver() -> Any:
    """Create a mock Selenium WebDriver."""
    driver = MagicMock()
    driver.find_element = MagicMock()
    driver.find_elements = MagicMock(return_value=[])
    driver.execute_script = MagicMock(return_value="complete")
    driver.save_screenshot = MagicMock(return_value=True)
    driver.quit = MagicMock()
    driver.get = MagicMock()
    driver.refresh = MagicMock()
    driver.maximize_window = MagicMock()
    return driver


@pytest.fixture
def mock_web_element() -> Any:
    """Create a mock WebElement."""
    element = MagicMock(spec=WebElement)
    element.click = MagicMock()
    element.send_keys = MagicMock()
    element.clear = MagicMock()
    element.text = "Test Text"
    element.get_attribute = MagicMock(return_value="")
    element.is_selected = MagicMock(return_value=False)
    element.find_element = MagicMock()
    element.find_elements = MagicMock(return_value=[])
    return element


@pytest.fixture
def mock_webdriver_wait(mocker: Any) -> Any:
    """Mock WebDriverWait to return immediately."""
    wait_mock = mocker.patch("selenium.webdriver.support.ui.WebDriverWait")
    wait_instance = MagicMock()
    wait_mock.return_value = wait_instance
    return wait_instance


@pytest.fixture(autouse=True)
def prevent_real_webdriver_creation(mocker: Any) -> None:
    """Prevent creation of real WebDriver instances in tests."""
    mocker.patch("selenium.webdriver.Chrome", return_value=MagicMock())
    mocker.patch("webdriver_manager.chrome.ChromeDriverManager")
    mocker.patch("selenium.webdriver.chrome.service.Service")
