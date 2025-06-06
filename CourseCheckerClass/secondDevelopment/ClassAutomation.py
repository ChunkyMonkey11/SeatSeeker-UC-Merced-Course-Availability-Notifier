import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json

class CourseScraper:
    """
    Automates course availability checks on the UC Merced registration site.

    Args:
        runtime (int): Time in seconds to keep the browser open after running (default: 15).

    Attributes:
        driver (webdriver.Chrome): Selenium WebDriver instance.
        runtime (int): Duration to keep the browser open.
        url (str): URL of the class search page.
    """

# Constructor
    def __init__(self, runtime: int = 5, courses_to_grab: list = []):
        """
        Initializes the CourseChecker with a Chrome WebDriver.

        Args:
            runtime (int): Time in seconds to keep the browser open after running.
        """
        options = Options()
        # options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument("--headless=new")  # Uncomment to run headless (no UI).
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        self.runtime = runtime
        self.url = (
            "https://reg-prod.ec.ucmerced.edu/StudentRegistrationSsb/ssb/term/termSelection?mode=search"
        )
        self.courses_to_grab = courses_to_grab


#   Finished -Refinable
    def select_term(self, term_value: str = "202530") -> None:
        """
        Selects the specified term from the dropdown and continues to the class search page.

        Args:
            term_value (str): The value attribute of the term to select (default: "202530" for Fall 2025).
        """
        self.driver.get(self.url)
        term_container = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "s2id_txt_term"))
        )
        term_container.click()
        term_option = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, term_value))
        )
        term_option.click()
        continue_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "term-go"))
        )
        continue_btn.click()

#   Finished -Refinable
    def prepare_for_xhr_injection(self) -> None:
        """
        Prepares the browser for XHR injection by focusing the subject box.
        """
        subject_box = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "s2id_txt_subject"))
        )
        subject_box.click()

   
#   Finished Refinable
    def fetch_course_data_pagination(self, subjects):
        self.driver.set_script_timeout(180)
        """
        Fetches all course data for the given subjects by paginating through all results.
        Does 5 subjects at a time, refreshing driver after each batch.
        Returns a list of all class section dicts.
        """
        url = "https://reg-prod.ec.ucmerced.edu/StudentRegistrationSsb/ssb/searchResults/searchResults"

        # JS for async API fetch, unchanged except now for a batch of subjects
        fetch_js = """
            const [url, token, sessionId, subjects, pageOffset, cb] = arguments;
            const qs = `?txt_subject=${encodeURIComponent(subjects.join(','))}`
                + '&txt_term=202530'
                + '&startDatepicker=&endDatepicker='
                + `&uniqueSessionId=${encodeURIComponent(sessionId)}`
                + `&pageOffset=${encodeURIComponent(pageOffset)}`
                + '&pageMaxSize=10'
                + '&sortColumn=subjectDescription&sortDirection=asc';
            fetch(url + qs, {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-Synchronizer-Token': token
                }
            })
            .then(resp => resp.json())
            .then(data => cb(data))
            .catch(err => cb({ error: err.message }));
        """

        all_results = []
        # Break the subjects list into batches of 5
        batch_size = 5
        for i in range(0, len(subjects), batch_size):
            batch_subjects = subjects[i:i + batch_size]
            page_offset = 0
            page_max_size = 10

            # Get session/token *inside* the batch, in case it changes after refresh
            unique_session = self.driver.execute_script(
                "return window.localStorage.getItem('uniqueSessionId');"
            )
            csrf_token = self.driver.execute_script(
                "return window.localStorage.getItem('x-synchronizer-token');"
            )

            while True:
                # Pass batch_subjects as a list
                result = self.driver.execute_async_script(fetch_js, url, csrf_token, unique_session, batch_subjects, page_offset)
                data = result.get("data", [])
                if not data:
                    break
                all_results.extend(data)
                if len(data) < page_max_size:
                    break  # last page reached
                page_offset += page_max_size
            # Refresh driver after every batch of 5
            self.refreshDriver()

        return all_results


#   Finished
    def refreshDriver(self):
        """
        refreshDriver will perform a refresh on the website equivlent to pressing the restart button.
        Need to make sure that the search bar is still there. 
        """
        self.driver.refresh()



#   Finished 
    def shutdown_browser(self) -> None:
        """
        Closes the browser and cleans up resources.
        """
        self.driver.quit()

#   In Use
    def start_browser(self) -> None:
        """
        Runs the course checker: selects term, injects XHR, and keeps the browser open for the specified runtime.
        """
        self.select_term()
        self.prepare_for_xhr_injection()
        time.sleep(self.runtime)



