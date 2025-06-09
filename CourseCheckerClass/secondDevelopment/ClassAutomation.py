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
        runtime (int): Time in seconds to keep the browser open after running (default: 5).

    Attributes:
        driver (webdriver.Chrome): Selenium WebDriver instance.
        runtime (int): Duration to keep the browser open.
        url (str): URL of the class search page.
    """

    def __init__(self, runtime: int = 5):
        """
        Initializes the CourseScraper with a Chrome WebDriver.

        Args:
            runtime (int): Time in seconds to keep the browser open after running.
        """
        options = Options()
        options.add_argument("--headless=new")
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        self.runtime = runtime
        self.url = (
            "https://reg-prod.ec.ucmerced.edu/StudentRegistrationSsb/ssb/term/termSelection?mode=search"
        )
        self.courses_to_grab = [
            "ANTH", "BCME", "BIOE", "BIO", "CHEM", "CCST", "CHN", "CEE", "COGS", "COMM", "CRS", "CSE", "CRES",
            "DSA", "DSC", "ECON", "EDUC", "EECS", "EE", "ENGR", "ENG", "EH", "ES", "ESS", "FRE", "GEOG", "GASP",
            "GSTU", "HS", "HIST", "IH", "JPN", "MGMT", "MBSE", "MSE", "MATH", "ME", "MIST", "NSED", "NEUR",
            "PHIL", "PHYS", "POLI", "PSY", "PH", "QSB", "ROTC", "SOC", "SPAN", "SPRK", "USTU", "WRI"
        ]

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
   
    def prepare_for_xhr_injection(self) -> None:
        """
        Prepares the browser for XHR injection by focusing the subject box.
        """
        subject_box = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "s2id_txt_subject"))
        )
        subject_box.click()

    def fetch_course_data_pagination(self):
        """
        Fetches all course data for the given subjects by paginating through all results.
        Does 5 subjects at a time, refreshing driver after each batch.
        Returns a list of all class section dicts.
        """
        self.driver.set_script_timeout(180)
        url = "https://reg-prod.ec.ucmerced.edu/StudentRegistrationSsb/ssb/searchResults/searchResults"
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
        subjects = self.courses_to_grab
        batch_size = 5
        for i in range(0, len(subjects), batch_size):
            batch_subjects = subjects[i:i + batch_size]
            page_offset = 0
            page_max_size = 10

            unique_session = self.driver.execute_script(
                "return window.localStorage.getItem('uniqueSessionId');"
            )
            csrf_token = self.driver.execute_script(
                "return window.localStorage.getItem('x-synchronizer-token');"
            )

            while True:
                result = self.driver.execute_async_script(
                    fetch_js, url, csrf_token, unique_session, batch_subjects, page_offset
                )
                data = result.get("data", [])
                if not data:
                    break
                all_results.extend(data)
                if len(data) < page_max_size:
                    break
                page_offset += page_max_size
            self.refreshDriver()

        return all_results

    def find_open_sections_by_subject(self, courses: list) -> dict:
        """
        Accepts a list of course section dictionaries.
        Returns a dictionary {subject: [open courseReferenceNumbers]}
        """
        open_sections_by_subject = {}
        for section in courses:
            if not isinstance(section, dict):
                continue
            subject = section.get("subject")
            course_ref = section.get("courseReferenceNumber")
            open_section = section.get("openSection")
            seats = section.get("seatsAvailable", 0)
            if subject and open_section and seats > 0:
                open_sections_by_subject.setdefault(subject, []).append(course_ref)
        return open_sections_by_subject

    def save_classes(self, classes_to_save):
        """
        Saves the open classes to a file.
        """
        with open("open_classes", "w") as f:
            f.write(str(classes_to_save))

    def save_to_db(self, classes_to_save):
        import sqlite3

    def store_open_crn_to_set():
        # write a function that puts all the data in a set
        pass









    def refreshDriver(self):
        """
        Refreshes the browser.
        """
        self.driver.refresh()

    def shutdown_browser(self) -> None:
        """
        Closes the browser and cleans up resources.
        """
        self.driver.quit()

    def start_browser(self) -> None:
        """
        Runs the course checker: selects term, injects XHR, and keeps the browser open for the specified runtime.
        """
        self.select_term()
        self.prepare_for_xhr_injection()
        time.sleep(self.runtime)

    def run(self) -> dict:
        """
        Main method to call in any file. Updates the file : open_classes.txt and maintains function order.
        """
        self.start_browser()
        all_class_info = self.fetch_course_data_pagination()
        open_classes = self.find_open_sections_by_subject(all_class_info)
        self.save_classes(open_classes)
        # self.save_to_db(open_classes)  # Uncomment or implement as needed
        return open_classes
