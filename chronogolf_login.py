import os
import logging
import time
import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Callable, Any
from dataclasses import dataclass
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from enum import Enum, auto

class BookingMode(Enum):
    TEST = auto()
    SCHEDULED = auto()

class BookingError(Exception):
    """Custom exception for booking-related errors"""
    pass

@dataclass
class Selectors:
    """Store all CSS/XPATH selectors in one place"""
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
        (By.XPATH, "//button[contains(@class, 'btn-sm')]//span[text()='{}']/..")
    ]
    DATE_NAVIGATION = [
        (By.CSS_SELECTOR, "button.btn.btn-default.btn-sm[ng-click*='move(-1)']"),  # Previous
        (By.CSS_SELECTOR, "button.btn.btn-default.btn-sm[ng-click*='move(1)']")    # Next
    ]
    MONTH_LABEL = [
        (By.CSS_SELECTOR, "button.btn.btn-default.btn-sm.uib-title strong"),  # Shows current month/year
    ]
    CALENDAR = [
        (By.CSS_SELECTOR, "button.btn.btn-default.btn-sm"),
    ]
    MONTH_NAVIGATION = [
        (By.CSS_SELECTOR, "button.btn.btn-default.btn-sm[ng-click*='move(-1)']"),  # Previous
        (By.CSS_SELECTOR, "button.btn.btn-default.btn-sm[ng-click*='move(1)']"),   # Next
    ]
    MONTH_TITLE = [
        (By.CSS_SELECTOR, "button.btn.btn-default.btn-sm.uib-title strong"),
    ]
    PLAYER_BUTTONS = [
        (By.CSS_SELECTOR, "a.toggler-heading.fl-button[ng-model='step.nbPlayers']"),
        (By.XPATH, "//a[contains(@class, 'toggler-heading') and contains(text(), '{}')]")
    ]
    CONTINUE_BUTTON = [
        (By.CSS_SELECTOR, "button.fl-button-primary[ng-click*='continue']"),
        (By.XPATH, "//button[contains(@class, 'fl-button-primary') and contains(., 'Continue')]")
    ]
    TIME_SLOTS = [
        (By.CSS_SELECTOR, "div.widget-teetime-tag"),  # The time display element
        (By.CSS_SELECTOR, "a.widget-teetime-rate")    # The clickable price element
    ]
    FINAL_CONTINUE = [
        (By.CSS_SELECTOR, "button.fl-button.fl-button-primary[ng-click='confirmStep()']"),
        (By.CSS_SELECTOR, "button.fl-button-block.fl-button-primary"),
        (By.XPATH, "//button[contains(@class, 'fl-button-primary') and text()='Continue']")
    ]
    AGREE_CHECKBOX = [
        (By.CSS_SELECTOR, "input[ng-model='vm.acceptTermsAndConditions'][type='checkbox']"),
        # Keep your existing fallback selectors if desired
        (By.CSS_SELECTOR, "input.fl-checkbox-input[ng-required='true']"),
        (By.CSS_SELECTOR, "input[type='checkbox'][required]")
    ]
    CONFIRM_BOOKING = [
        (By.CSS_SELECTOR, "button.fl-button-primary[type='submit']"),
        (By.CSS_SELECTOR, "button.fl-button-primary.fl-button-block"),
        (By.XPATH, "//button[contains(@class, 'fl-button-primary') and contains(text(), 'Confirm')]")
    ]

@dataclass
class BookingConfig:
    """Store booking configuration"""
    RELEASE_TIME = datetime.time(7, 0)  # 7:00 AM
    ADVANCE_DAYS = 7 # Number of days in advance to book
    PRE_ATTEMPT_SECONDS = 10  # Start trying 10 seconds before
    MAX_RETRIES = 60  # Retry for up to 1 minute
    RETRY_DELAY = 1  # Wait 1 second between retries
    DEFAULT_WAIT_TIMEOUT = 10  # Default timeout for waits in seconds
    
    @property
    def target_date(self) -> datetime.date:
        """Calculate target booking date"""
        return datetime.datetime.now().date() + datetime.timedelta(days=self.ADVANCE_DAYS)
    
    @property
    def target_date_str(self) -> str:
        """Get target date in YYYY-MM-DD format"""
        return self.target_date.strftime('%Y-%m-%d')

def setup_output_dirs() -> Dict[str, Path]:
    """Create and return organized directories for logs and screenshots."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_dir = Path("chronogolf_output")
    run_dir = base_dir / f"run_{timestamp}"
    
    dirs = {
        "run_dir": run_dir,
        "screenshots_dir": run_dir / "screenshots",
        "logs_dir": run_dir / "logs"
    }
    
    for directory in dirs.values():
        directory.mkdir(exist_ok=True, parents=True)
    
    return dirs

class ChronogolfLogin:
    def __init__(self, mode: BookingMode, headless: bool = False, output_dirs: Optional[Dict[str, Path]] = None):
        load_dotenv()
        self._validate_env_vars()
        
        self.mode = mode
        self.headless = headless
        self.output_dirs = output_dirs or {}
        self.driver = None
        self.selectors = Selectors()
        self.config = BookingConfig()

    def wait_for_element(self, selectors: List[Tuple[str, str]], timeout=None, condition="presence") -> WebElement:
        """Wait for an element to meet the specified condition."""
        if timeout is None:
            timeout = self.config.DEFAULT_WAIT_TIMEOUT
            
        end_time = time.time() + timeout
        last_exception = None
        
        while time.time() < end_time:
            for selector_type, selector in selectors:
                try:
                    if condition == "presence":
                        return WebDriverWait(self.driver, 1).until(
                            EC.presence_of_element_located((selector_type, selector))
                        )
                    elif condition == "clickable":
                        return WebDriverWait(self.driver, 1).until(
                            EC.element_to_be_clickable((selector_type, selector))
                        )
                    elif condition == "visible":
                        return WebDriverWait(self.driver, 1).until(
                            EC.visibility_of_element_located((selector_type, selector))
                        )
                except (NoSuchElementException, TimeoutException) as e:
                    last_exception = e
                    continue
                
        if last_exception:
            raise BookingError(f"Element not found with any selector after {timeout} seconds: {last_exception}")
        raise BookingError(f"Element not found with any selector after {timeout} seconds")

    def wait_for_page_load(self, timeout=None):
        """Wait for page to fully load."""
        if timeout is None:
            timeout = self.config.DEFAULT_WAIT_TIMEOUT
            
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            return True
        except Exception as e:
            logging.error(f"Page did not load completely: {str(e)}")
            return False
            
    def wait_for_ajax(self, timeout=None):
        """Wait for jQuery AJAX requests to complete."""
        if timeout is None:
            timeout = self.config.DEFAULT_WAIT_TIMEOUT
            
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return jQuery.active == 0")
            )
            return True
        except Exception as e:
            logging.error(f"AJAX requests did not complete: {str(e)}")
            return False
    
    def retry_on_stale_element(self, action: Callable[[], Any], max_attempts=3) -> Any:
        """Retry an action if a stale element reference exception occurs."""
        attempts = 0
        while attempts < max_attempts:
            try:
                return action()
            except StaleElementReferenceException:
                attempts += 1
                logging.warning(f"Stale element encountered, retrying ({attempts}/{max_attempts})")
                if attempts == max_attempts:
                    raise
            except Exception as e:
                logging.error(f"Error during action: {str(e)}")
                raise
    
    def _validate_env_vars(self):
        """Validate required environment variables exist."""
        self.username = os.getenv("GOLF_USERNAME")
        self.password = os.getenv("GOLF_PASSWORD")
        self.site_url = os.getenv("BOOKING_URL")
        
        if not all([self.username, self.password, self.site_url]):
            raise ValueError("Missing required environment variables in .env file")

    def _find_element(self, selectors: List[Tuple[str, str]]) -> WebElement:
        """Internal method - raises exception if element not found"""
        for selector_type, selector in selectors:
            try:
                return self.driver.find_element(selector_type, selector)
            except NoSuchElementException:
                continue
        raise BookingError("Element not found with any selector")

    def setup_driver(self):
        """Initialize Chrome WebDriver with appropriate options."""
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.maximize_window()
        logging.info("Web driver initialized")

    def save_screenshot(self, filename: str):
        """Save screenshot if driver and screenshots directory exist."""
        if self.driver and "screenshots_dir" in self.output_dirs:
            filepath = self.output_dirs["screenshots_dir"] / filename
            self.driver.save_screenshot(str(filepath))
            logging.info(f"Screenshot saved: {filepath}")

    def _click_login_tab(self) -> None:
        """Click the member login tab to show login form."""
        try:
            member_tab = self.wait_for_element(
                self.selectors.MEMBERS_TAB, 
                condition="clickable"
            )
            member_tab.click()
            logging.info("Clicked member login tab")
            self.save_screenshot("02_login_tab_clicked.png")
        except BookingError as e:
            logging.error(f"Failed to click login tab: {str(e)}")
            raise

    def _handle_login_form(self) -> None:
        """Fill and submit login form."""
        try:
            # Wait for form elements to be interactable
            email_field = self.wait_for_element(
                self.selectors.EMAIL_FIELD, 
                condition="visible"
            )
            password_field = self.wait_for_element(
                self.selectors.PASSWORD_FIELD, 
                condition="visible"
            )
            
            email_field.clear()
            email_field.send_keys(self.username)
            
            password_field.clear()
            password_field.send_keys(self.password)
            
            login_button = self.wait_for_element(
                self.selectors.LOGIN_BUTTON, 
                condition="clickable"
            )
            login_button.click()
            self.save_screenshot("03_login_submitted.png")
            
        except BookingError as e:
            logging.error(f"Login form handling failed: {str(e)}")
            raise

    def login(self) -> bool:
        """Public method to handle complete login process."""
        try:
            # First click the login tab
            self._click_login_tab()
            
            # Then handle the login form
            self._handle_login_form()
            
            # Verify login success
            if not self._verify_login_success():
                return False
                
            logging.info("Login successful!")
            return True
            
        except BookingError as e:
            logging.error(f"Login failed: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error during login: {str(e)}")
            return False

    def _verify_login_success(self) -> bool:
        """Verify if login was successful."""
        try:
            success_element = self.wait_for_element(
                self.selectors.LOGIN_SUCCESS, 
                timeout=15,  # Give extra time for login to process
                condition="visible"
            )
            logging.info(f"Login successful! here is the verifying element: {success_element.text}")
            self.save_screenshot("04_login_successful.png")
            return True
        except Exception:
            logging.error("Login verification failed")
            self.save_screenshot("04_login_failed.png")
            return False

    def _parse_month_title(self, title_text: str) -> datetime.datetime:
        """Parse the month title (e.g., 'April 2025') into a datetime object."""
        try:
            return datetime.datetime.strptime(title_text, '%B %Y')
        except ValueError as e:
            logging.error(f"Could not parse month title: {title_text}")
            raise e

    def _navigate_to_target_month(self, target_date: datetime.datetime) -> None:
        """Internal method to navigate to target month."""
        try:
            month_title = self.wait_for_element(
                self.selectors.MONTH_TITLE,
                condition="visible"
            )
            current_month = self._parse_month_title(month_title.text)
            
            # Only navigate forward until we reach target month
            while current_month.year != target_date.year or current_month.month != target_date.month:
                next_button = self.wait_for_element(
                    [self.selectors.MONTH_NAVIGATION[1]],
                    condition="clickable"
                )
                
                if 'disabled' in next_button.get_attribute('class'):
                    raise BookingError("Cannot navigate to future month")
                
                next_button.click()
                
                # Wait for calendar to update
                self.wait_for_ajax()
                
                # Get updated month title
                month_title = self.wait_for_element(
                    self.selectors.MONTH_TITLE,
                    condition="visible"
                )
                current_month = self._parse_month_title(month_title.text)
        except BookingError as e:
            logging.error(f"Failed to navigate to target month: {str(e)}")
            raise

    def _select_date(self, target_date_str: str) -> bool:
        """Select a date from the datepicker."""
        try:
            target_date = datetime.datetime.strptime(target_date_str, '%Y-%m-%d')
            self._navigate_to_target_month(target_date)
            
            # Format day with leading zero if needed
            day_str = f"{target_date.day:02d}"  # Ensures "5" becomes "05"
            
            # Look for non-muted spans with the target day
            xpath = f"//span[not(contains(@class, 'text-muted')) and text()='{day_str}']"
            spans = self.driver.find_elements(By.XPATH, xpath)
            
            if not spans:
                logging.error(f"Could not find date {target_date_str} in current month")
                return False
                
            # Get the parent button and check if it's disabled
            date_button = spans[0].find_element(By.XPATH, "..")
            if date_button.get_attribute("disabled") == "true":
                logging.error(f"Date {target_date_str} is disabled/unavailable")
                return False
                
            # Click the button
            date_button.click()
            
            logging.info(f"Selected date: {target_date_str}")
            self.save_screenshot("date_selected.png")
            
            # Wait for selection to process
            self.wait_for_ajax()
            return True
            
        except Exception as e:
            logging.error(f"Error selecting date: {str(e)}")
            return False
    
    def _select_players(self, num_players: int) -> bool:
        """Internal method to select number of players."""
        try:
            # Try finding the specific player button using the number
            player_xpath = f"//a[contains(@class, 'toggler-heading') and contains(text(), '{num_players}')]"
            
            # Wait for player selection to be available
            player_button = WebDriverWait(self.driver, self.config.DEFAULT_WAIT_TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, player_xpath))
            )
            
            if 'disabled' in player_button.get_attribute('class'):
                logging.error(f"Cannot select {num_players} players - option is disabled")
                return False
                
            def click_player():
                player_button.click()
                
            self.retry_on_stale_element(click_player)
            
            logging.info(f"Selected {num_players} players")
            self.save_screenshot("06_players_selected.png")
            
            # Wait for player selection to process
            self.wait_for_ajax()
            
            return True
            
        except NoSuchElementException:
            logging.error(f"Could not find button for {num_players} players")
            return False
        except Exception as e:
            logging.error(f"Error selecting number of players: {str(e)}")
            return False
        
    def _parse_time_range(self, time_range: str) -> tuple[datetime.time, datetime.time]:
        """Parse time range string (e.g. '07:00-11:00') into start and end times."""
        try:
            start_str, end_str = time_range.split('-')
            start_time = datetime.datetime.strptime(start_str.strip(), '%H:%M').time()
            end_time = datetime.datetime.strptime(end_str.strip(), '%H:%M').time()
            return start_time, end_time
        except ValueError as e:
            logging.error(f"Invalid time range format: {time_range}")
            raise e
        
    def _parse_time_from_element(self, time_element: WebElement) -> Optional[datetime.time]:
        """Extract time from the time display element."""
        try:
            time_text = time_element.text.strip()
            return datetime.datetime.strptime(time_text, '%I:%M %p').time()
        except ValueError as e:
            logging.error(f"Could not parse time from text: {time_text}")
            return None

    def _select_time_slot(self) -> bool:
        """Internal method to select time slot."""
        try:
            time_range = os.getenv("PREFERRED_TIME_RANGE")
            if not time_range:
                logging.error("No preferred time range specified in environment variables")
                return False
        
            start_time, end_time = self._parse_time_range(time_range)
            logging.info(f"Looking for time slots between {start_time} and {end_time}")
            
            # Wait for containers to be present
            self.wait_for_element(
                [(By.CSS_SELECTOR, "div.widget-teetime")], 
                timeout=15, 
                condition="presence"
            )
            
            # Get all container elements
            available_slots = []
            containers = self.driver.find_elements(By.CSS_SELECTOR, "div.widget-teetime")
            
            for container in containers:
                try:
                    # Find the time element within the container
                    time_element = container.find_element(By.CSS_SELECTOR, "div.widget-teetime-tag")
                    # Find the price/rate element within the container
                    price_element = container.find_element(By.CSS_SELECTOR, "a.widget-teetime-rate")
                    
                    # Check if the slot is disabled
                    if price_element and 'disabled' in price_element.get_attribute('class'):
                        continue
                    
                    # Parse the time
                    slot_time = self._parse_time_from_element(time_element)
                    if not slot_time:
                        continue
                    
                    # Check if slot is within preferred range
                    if start_time <= slot_time <= end_time:
                        price_text = price_element.text.strip() if price_element else "N/A"
                        logging.info(f"Found available slot: {slot_time} - {price_text}")
                        available_slots.append((slot_time, price_element))
                        
                except NoSuchElementException:
                    continue
            
            if not available_slots:
                logging.error("No available time slots found within preferred range")
                self.save_screenshot("09_no_times_available.png")
                return False
            
            # Sort slots by time and select middle-most
            available_slots.sort(key=lambda x: x[0])
            middle_index = len(available_slots) // 2
            selected_time, selected_price_element = available_slots[middle_index]
            
            logging.info(f"Selected middle slot: {selected_time}")
            self.save_screenshot("07_before_time_selection.png")
            
            def click_time():
                selected_price_element.click()
                
            self.retry_on_stale_element(click_time)
            
            logging.info(f"Clicked time slot for {selected_time.strftime('%I:%M %p')}")
            self.save_screenshot("08_after_time_selection.png")
            
            # Wait for time selection to process
            self.wait_for_ajax()
            
            return True
        
        except Exception as e:
            logging.error(f"Error selecting time slot: {str(e)}")
            self.save_screenshot("error_time_selection.png")
            return False

    def _continue_to_next_screen(self) -> bool:
        """Internal method to handle continue button."""
        try:
            continue_button = self.wait_for_element(
                self.selectors.CONTINUE_BUTTON,
                condition="clickable"
            )
            
            if 'disabled' in continue_button.get_attribute('class'):
                logging.error("Continue button is disabled")
                return False
            
            def click_continue():
                continue_button.click()
                
            self.retry_on_stale_element(click_continue)
            
            logging.info("Clicked continue button")
            self.save_screenshot("09_continued_to_next.png")
            
            # Wait for next screen to load
            self.wait_for_page_load()
            self.wait_for_ajax()
            
            return True
            
        except Exception as e:
            logging.error(f"Error clicking continue button: {str(e)}")
            return False

    def _continue_final_step(self) -> bool:
        """Click the final continue button after time selection."""
        try:
            continue_button = self.wait_for_element(
                self.selectors.FINAL_CONTINUE,
                condition="clickable"
            )
            
            if 'disabled' in continue_button.get_attribute('class'):
                logging.error("Final continue button is disabled")
                return False
            
            def click_final_continue():
                continue_button.click()
                
            self.retry_on_stale_element(click_final_continue)
            
            logging.info("Clicked final continue button")
            self.save_screenshot("10_final_continue.png")
            
            # Wait for next screen to load
            self.wait_for_page_load()
            self.wait_for_ajax()
            
            return True
            
        except Exception as e:
            logging.error(f"Error clicking final continue button: {str(e)}")
            self.save_screenshot("error_final_continue.png")
            return False

    def _accept_agreement(self) -> bool:
        """Internal method to handle agreement checkbox."""
        try:
            time.sleep(5)  # Keep this simple to allow for any loading
            
            checkbox = self._find_element(self.selectors.AGREE_CHECKBOX)
            if not checkbox:
                logging.error("Agreement checkbox not found")
                return False
            
            if not checkbox.is_selected():
                # Add a scroll before clicking
                self.driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                # Keep your existing click
                checkbox.click()
                logging.info("Clicked agreement checkbox")
                self.save_screenshot("11_agreement_checked.png")
            
            return True
            
        except Exception as e:
            logging.error(f"Error accepting agreement: {str(e)}")
            self.save_screenshot("error_agreement.png")
            return False

    def _confirm_booking(self) -> bool:
        """Internal method to handle final confirmation."""
        try:
            confirm_button = self.wait_for_element(
                self.selectors.CONFIRM_BOOKING,
                condition="clickable"
            )
            
            if 'disabled' in confirm_button.get_attribute('class'):
                logging.error("Confirm button is disabled")
                return False
            
            def click_confirm():
                confirm_button.click()
                
            self.retry_on_stale_element(click_confirm)
            
            logging.info("Clicked confirm reservation button")
            
            # Wait for confirmation to process
            WebDriverWait(self.driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            self.save_screenshot("12_booking_confirmed.png")
            return True
            
        except Exception as e:
            logging.error(f"Error confirming reservation: {str(e)}")
            self.save_screenshot("error_confirmation.png")
            return False

    def wait_for_release_time(self) -> bool:
        now = datetime.datetime.now()
        release_datetime = datetime.datetime.combine(now.date(), self.config.RELEASE_TIME)
        
        if now.time() > self.config.RELEASE_TIME:
            logging.error(f"Current time ({now.time()}) is past release time ({self.config.RELEASE_TIME})")
            logging.error(f"Cannot book for target date {self.config.target_date_str}")
            logging.error("Please run the script before the release time")
            return False
        
        start_time = release_datetime - datetime.timedelta(seconds=self.config.PRE_ATTEMPT_SECONDS)
        wait_seconds = (start_time - now).total_seconds()
        if wait_seconds > 0:
            logging.info(f"Waiting until {start_time} before attempting booking for {self.config.target_date_str}")
            time.sleep(wait_seconds)
        return True

    def perform_booking_flow(self) -> bool:
        """Execute the complete booking flow as a single attempt."""
        try:
            # Define all steps in the booking process
            steps = [
                (self._select_date, [self.config.target_date_str], "Selecting date"),
                (self._select_players, [int(os.getenv("NUMBER_OF_PLAYERS", "4"))], "Selecting players"),
                (self._continue_to_next_screen, [], "Continuing to time selection"),
                (self._select_time_slot, [], "Selecting time slot"),
                (self._continue_final_step, [], "Continuing to final step"),
                (self._accept_agreement, [], "Accepting agreement"),
                (self._confirm_booking, [], "Confirming booking")
            ]
    
            # Execute each step in sequence
            for step_func, args, desc in steps:
                logging.info(f"Attempting: {desc}")
                if not step_func(*args):
                    logging.error(f"Failed at: {desc}")
                    return False
    
            logging.info("Booking flow completed successfully!")
            return True
    
        except Exception as e:
            logging.error(f"Error in booking flow: {str(e)}")
            return False

    def retry_booking_flow(self) -> bool:
        """Retry the booking flow until successful or max retries reached."""
        retries = 0
        logging.info(f"Beginning retry attempts for date: {self.config.target_date_str}")
        
        while retries < self.config.MAX_RETRIES:
            try:
                if self.perform_booking_flow():
                    logging.info("Booking successful!")
                    return True
                
                retries += 1
                if retries < self.config.MAX_RETRIES:
                    logging.info(f"Retry {retries}/{self.config.MAX_RETRIES}...")
                    time.sleep(self.config.RETRY_DELAY)
                    
            except Exception as e:
                logging.error(f"Error during retry attempt {retries}: {str(e)}")
                retries += 1
        
        logging.error(f"Failed to complete booking after {self.config.MAX_RETRIES} attempts")
        return False

    def complete_booking(self) -> bool:
        """Complete the final steps of booking."""
        if not self._continue_final_step():
            return False
        if not self._accept_agreement():
            return False
        if not self._confirm_booking():
            return False
        return True

    def book_tee_time(self) -> bool:
        """Book a tee time based on mode."""
        try:
            # Initial setup and login for both modes
            if not self.initialize():
                return False
                
            if not self.login():
                return False
            
            if self.mode == BookingMode.SCHEDULED:
                # Scheduled mode: Wait and retry
                if not self.wait_for_release_time():
                    return False
                return self.retry_booking_flow()
            else:
                # Test mode: Single attempt
                return self.perform_booking_flow()
            
        except Exception as e:
            logging.error(f"Error booking tee time: {str(e)}")
            return False

    def navigate_to_site(self) -> bool:
        """Navigate to the booking site."""
        try:
            if not self.driver:
                raise BookingError("WebDriver not initialized")
            
            self.driver.get(self.site_url)
            logging.info(f"Navigated to {self.site_url}")
            
            # Wait for page to fully load
            self.wait_for_page_load()
            
            self.save_screenshot("01_initial_page.png")
            return True
            
        except Exception as e:
            logging.error(f"Error navigating to site: {str(e)}")
            return False

    def initialize(self) -> bool:
        """Initialize the driver and navigate to site."""
        try:
            self.setup_driver()
            return self.navigate_to_site()
        except Exception as e:
            logging.error(f"Error during initialization: {str(e)}")
            return False

    def close(self):
        """Close the browser and clean up."""
        if self.driver:
            self.driver.quit()
            logging.info("Browser closed")
            self.driver = None

    def __del__(self):
        self.close()

def main() -> bool:
    """Main execution function."""
    # Setup output directories and logging
    output_dirs = setup_output_dirs()
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(output_dirs["logs_dir"] / "chronogolf_login.log"),
            logging.StreamHandler()
        ]
    )

    # Initialize booking handler with appropriate mode
    mode = BookingMode.TEST if os.getenv("TEST_MODE") else BookingMode.SCHEDULED
    booking = ChronogolfLogin(mode=mode, headless=True, output_dirs=output_dirs)
    
    try:
        logging.info(f"Starting {mode.name} mode booking")
        success = booking.book_tee_time()
        
        if success:
            logging.info("✅ Booking completed successfully!")
            logging.info(f"Output saved to: {output_dirs['run_dir']}")
        return success
        
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        return False
    finally:
        booking.close()

if __name__ == "__main__":
    main()
