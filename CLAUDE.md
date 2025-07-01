# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup and Installation
```bash
make init        # Complete setup (install dependencies + create .env template)
make install     # Install production dependencies using pipenv
make dev         # Install dev dependencies
make shell       # Activate pipenv virtual environment
```

### Running the Application
```bash
make run         # Run the main chronogolf_login.py script
```

### Code Quality (Modern Toolchain)
```bash
make format             # Format code with Ruff (replaces Black)
make lint               # Run Ruff linter on src/ and tests/ (replaces flake8)
make typecheck          # Run mypy type checking on src/ and tests/
make check              # Run lint + format + type checks
make all-checks         # Full CI pipeline: tests + lint + format + types
```

**Why Ruff?** Ruff is 10-100x faster than Black+flake8+isort combined, has fewer configuration conflicts, and includes modern Python linting rules. We use it for both formatting and linting, applying to both `src/` and `tests/` directories.

**Type Checking**: mypy runs on both source code AND tests because tests are code too! Type safety helps catch bugs in test logic and ensures proper mock usage.

### Cleanup
```bash
make clean       # Remove cache files, pyc files, and logs
make clean_logs  # Remove all output directories
```

## Architecture Overview

This is a Selenium-based web automation project for booking golf tee times on ChronoGolf platforms. The codebase follows a structured approach with clear separation of concerns:

### Core Components

1. **`src/main.py`** - Main entry point with clean, focused responsibilities:
   - Output directory setup and logging configuration
   - Mode determination (TEST vs SCHEDULED)
   - Orchestrator initialization and execution

2. **`src/booking_orchestrator.py`** - Central coordination:
   - Manages WebDriver lifecycle and browser setup
   - Coordinates page objects and booking strategies
   - Environment validation and error handling

3. **`src/booking_strategies.py`** - Strategy pattern implementation:
   - `TestModeStrategy`: Simple single booking flow
   - `ScheduledModeStrategy`: Waits for release time, handles retries
   - Abstract base for extensibility

4. **`src/booking_pages.py`** - Page Object pattern:
   - `LoginPage`, `DateSelectionPage`, `PlayerSelectionPage`, `TimeSlotPage`, `BookingConfirmationPage`
   - Clean separation of concerns, each page handles its own interactions

5. **`src/config.py`** - Configuration and data structures:
   - `BookingConfig` dataclass: Timing and retry parameters
   - `Selectors` dataclass: Centralized CSS/XPath selectors
   - `BookingMode` enum and `BookingError` exception

6. **`src/element_manager.py`** - Robust web element handling:
   - Multiple fallback selectors, retry logic, stale element recovery
   - Enhanced reliability for dynamic web content

7. **GitHub Actions Workflow** (`.github/workflows/get_teetime.yml`):
   - Scheduled automation (6:50 AM Pacific on weekends)
   - Manual trigger support for testing
   - Environment variables and secrets management
   - Artifact collection for logs and screenshots

### Key Design Patterns

- **Page Object Pattern**: Selectors are centralized in the `Selectors` dataclass
- **Retry Logic**: Built-in retry mechanisms for handling stale elements and timing issues
- **Comprehensive Logging**: All actions are logged with screenshots at key steps
- **Environment Configuration**: Uses `.env` file for credentials and settings

### Environment Variables
Required in `.env` file:
- `GOLF_USERNAME`: Login email
- `GOLF_PASSWORD`: Login password  
- `BOOKING_URL`: ChronoGolf widget URL
- `PREFERRED_TIME_RANGE`: Time preference (e.g., "08:00-11:00")
- `NUMBER_OF_PLAYERS`: Number of players to book
- `TEST_MODE`: Enable/disable test mode

### Output Structure
```
chronogolf_output/
└── run_YYYYMMDD_HHMMSS/
    ├── logs/
    │   └── booking.log
    └── screenshots/
        └── [step_screenshots].png
```

## Development Process

### 1. Interactive Planning
- **Always plan extensively** with the user before writing any code
- Discuss the approach, architecture, and implementation details
- Confirm the plan with the user before proceeding to implementation
- Break down complex features into smaller, manageable tasks

### 2. Test-Driven Development (TDD)
- **Write tests first** before implementing functionality
- Start with simple test cases that clearly illustrate the expected behavior
- Expand tests incrementally as features are developed
- Unit tests should focus on **behavior**, not implementation details
- Test important edge cases but avoid chasing arbitrary coverage metrics
- Avoid excessive mocking of internal helper functions

### 3. Code Style and Standards
- Write **simple, readable code** over clever abstractions
- Follow **PEP 8** standards for Python 3.10+
- Use type hints where they improve clarity
- Prefer explicit over implicit
- Keep functions small and focused on a single responsibility
- Use descriptive variable and function names

### Example TDD Workflow

**Proven in practice - we used this to refactor from 1000 lines to modular architecture:**

```python
# 1. Write a failing test that describes the behavior
def test_login_page_can_be_created():
    page = LoginPage(driver, element_manager, selectors, config)
    assert page.driver == driver

# 2. Write minimal code to make the test pass
class LoginPage:
    def __init__(self, driver, element_manager, selectors, config):
        self.driver = driver
        # ... minimal implementation

# 3. Test passes - move to next test
def test_login_success():
    result = page.login("user", "pass", output_dirs)
    assert result is True

# 4. Add just enough code to pass this test
# 5. Refactor while keeping tests green
# 6. Repeat cycle
```

**Result: 24 lines of tested code vs 938 lines of monolithic code**

## Important Implementation Notes

- The system uses Pacific timezone (`US/Pacific`) for all time calculations
- Booking attempts start 10 seconds before the configured release time
- Maximum retry period is 60 seconds with 1-second intervals
- WebDriverManager automatically handles Chrome driver installation
- The code includes extensive wait strategies for handling dynamic web content