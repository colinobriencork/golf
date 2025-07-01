.PHONY: setup install shell run clean test lint format check all-checks

# Create virtual environment and install dependencies
install:
	pipenv install

# Install dev dependencies
dev:
	pipenv install --dev

# Activate the virtual environment shell
shell:
	pipenv shell

# Run the booking script
run:
	pipenv run python -m src.main

# Clean up cached files
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.log" -delete

clean_logs:
	rm -rf ./chronogolf_output/*

# Create .env file template if it doesn't exist
env:
	@if [ ! -f .env ]; then \
		echo "# .env file for Chronogolf Login" > .env; \
		echo "GOLF_USERNAME=\"your_email@example.com\"" >> .env; \
		echo "GOLF_PASSWORD=\"your_password\"" >> .env; \
		echo "BOOKING_URL=\"https://widget.chronogolf.com/yourgolfclub\"" >> .env; \
		echo ".env template created. Please edit with your credentials."; \
	else \
		echo ".env file already exists."; \
	fi

# Run tests
test:
	pipenv run pytest

# Run tests with coverage
test-cov:
	pipenv run pytest --cov=. --cov-report=html --cov-report=term

# Run linter
lint:
	pipenv run ruff check src/ tests/

# Format code
format:
	pipenv run ruff format src/ tests/

# Type check
typecheck:
	pipenv run mypy

# Check code quality (lint + format check + type check)
check: 
	pipenv run ruff check src/ tests/
	pipenv run ruff format --check src/ tests/
	pipenv run mypy

# Run all quality checks (tests + linting + formatting + type checking)
all-checks:
	@echo "🧪 Running all tests (including timezone tests)..."
	pipenv run pytest
	@echo "✅ Tests completed"
	@echo ""
	@echo "🔍 Checking code formatting..."
	pipenv run ruff format --check src/ tests/
	@echo "✅ Code formatting verified"
	@echo ""
	@echo "📋 Running linter..."
	pipenv run ruff check src/ tests/
	@echo "✅ Linting completed"
	@echo ""
	@echo "🔬 Type checking..."
	pipenv run mypy
	@echo "✅ Type checking completed"
	@echo ""
	@echo "🎉 All checks passed!"

# Complete setup in one command
init: install env
	@echo "Setup complete! Edit your .env file, then run 'make run' to test login."