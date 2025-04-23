.PHONY: setup install shell run clean

# Create virtual environment and install dependencies
install:
	pipenv install

# Install dev dependencies
dev:
	pipenv install --dev

# Activate the virtual environment shell
shell:
	pipenv shell

# Run the login script
run:
	pipenv run python chronogolf_login.py

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

# Complete setup in one command
init: install env
	@echo "Setup complete! Edit your .env file, then run 'make run' to test login."