from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def setup_driver():
    """Initializes and returns a Chrome WebDriver instance."""
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    return driver

def login_to_portal(driver):
    """Logs into the course portal if needed."""
    pass  # TODO: Add login logic

def navigate_to_search_page(driver):
    driver.get("https://reg-prod.ec.ucmerced.edu/StudentRegistrationSsb/ssb/registration")
    
    # OPTIONAL: click "Register for Classes" if needed
    try:
        register_link = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "registerLink"))
        )
        register_link.click()
        
    except:
        pass  # If not needed, skip

def search_for_courses(driver):
    """Searches for course by CRNS"""

    pass # TODO: Search Course by CRNS
def check_availability(driver):
    """Checks if the course is open and logs/sends notification."""
    pass  # TODO: Check status and trigger notification

def send_notification(course_name):
    """Sends email/text if the course is available."""
    pass  # TODO: Send email/text notification

def main_loop():
    """Main checking loop."""
    driver = setup_driver()

    try:
        login_to_portal(driver)
        while True:
            navigate_to_search_page(driver)
            search_for_courses(driver)
            check_availability(driver)
            
            # Wait before checking again
            time.sleep(1800)  # 30 minutes
    finally:
        driver.quit()

if __name__ == "__main__":
    main_loop()
