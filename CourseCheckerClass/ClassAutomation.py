from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class CourseChecker:
    """
    Automates course availability checking via UC Merced's registration portal.

    Attributes:
        driver: Selenium WebDriver instance.
        crns: List of CRNs to monitor.
        runtime: Interval between course checks (in seconds).
        registration_home_url: Entry point URL for course registration.
    """
    
    def __init__(self, crns=None, runtime=None, registration_home_url=None):
        self.driver = self._init_browser()
        self.crns = crns
        self.runtime = runtime or 1800
        self.registration_home_url = registration_home_url or "https://reg-prod.ec.ucmerced.edu/StudentRegistrationSsb/ssb/registration"

    def _init_browser(self):
        """Initializes a Chrome WebDriver instance."""
        options = Options()
        # IMPORTANT: Uncomment for headless operation in production
        # options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def start_login_flow(self):
        """
        Starts the login flow by navigating to the registration entry page
        and clicking the 'Register for Classes' link.
        """
        self.driver.get(self.registration_home_url)
        try:
            register_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, "registerLink"))
            )
            register_btn.click()
        except Exception as e:
            print("[start_login_flow] Unable to initiate login:", e)
            self.shutdown()

    def perform_login(self, username, password):
        """Handles filling out and submitting the login form."""
        # Placeholder: actual login form logic should go here
        try:
            username_field = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, "Rd6" ))
            )
            print(username_field.is_selected)
        except Exception as e:
            print("[perform_logic] Unable to login with credentials:", e)

    def shutdown(self):
        """Cleans up driver and exits script."""
        self.driver.quit()
        exit()

    def run(self):
        """Main execution loop."""
        self.start_login_flow()
        # self.perform_login(username="revantp", password="1234")
        time.sleep(self.runtime)
        self.shutdown()

if __name__ == "__main__":
    MercedChecker = CourseChecker(runtime=15)
    MercedChecker.run()
