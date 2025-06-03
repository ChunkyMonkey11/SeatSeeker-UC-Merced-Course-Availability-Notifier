"""
refactored_model.py

Automates the process of checking course availability at UC Merced using Selenium WebDriver.
This module provides the CourseChecker class, which can select a term, subject, and course number,
and perform an XHR request to fetch course data directly from the registration system.

Classes:
    CourseChecker: Automates browser actions to check course availability.

Usage:
    checker = CourseChecker(runtime=15)
    checker.run()
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class CourseChecker:
    """
    Automates course availability checks on the UC Merced registration site.

    Args:
        runtime (int): Time in seconds to keep the browser open after running (default: 15).

    Attributes:
        driver (webdriver.Chrome): Selenium WebDriver instance.
        runtime (int): Duration to keep the browser open.
        url (str): URL of the class search page.
    """
#   In Use
    def __init__(self, runtime: int = 15):
        """
        Initializes the CourseChecker with a Chrome WebDriver.

        Args:
            runtime (int): Time in seconds to keep the browser open after running.
        """
        options = Options()
        # options.add_argument("--headless=new")  # Uncomment to run headless (no UI).
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        self.runtime = runtime
        self.url = (
            "https://reg-prod.ec.ucmerced.edu/StudentRegistrationSsb/ssb/term/termSelection?mode=search"
        )

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

#   Not In Use
    def select_subject(self, subject: str = "CSE") -> None:
        """
        Selects the subject for class search.

        Args:
            subject (str): The subject code to search for (default: "CSE").
        """
        subject_box = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "s2id_txt_subject"))
        )
        subject_box.click()
        search_input = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "select2-input"))
        )
        search_input.clear()
        search_input.send_keys(subject)
        result = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//div[@id='{subject}']"))
        )
        result.click()

#   Not In Use
    def fill_out_course_number(self, course_number: str = "005") -> None:
        """
        Fills out the course number and performs the search.

        Args:
            course_number (str): The course number to search for (default: "005").
        """
        course_input = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "txt_courseNumber"))
        )
        course_input.clear()
        course_input.send_keys(course_number)
        search_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "search-go"))
        )
        search_button.click()

#   Finished -Refinable
    def inject_XHR(self, subject, courseNuber) -> dict:
        """
        Injects and executes an XHR request in the browser to fetch course data directly.

        Prints the JSON response to stdout.
        """
        import json
        self.prepare_for_xhr_injection()
        url = "https://reg-prod.ec.ucmerced.edu/StudentRegistrationSsb/ssb/searchResults/searchResults"
        unique_session = self.driver.execute_script(
            "return window.localStorage.getItem('uniqueSessionId');"
        )
        csrf_token = self.driver.execute_script(
            "return window.localStorage.getItem('x-synchronizer-token');"
        )
        
        fetch_js = """
        const [url, token, sessionId, subject, courseNumber, cb] = arguments;
        const qs = `?txt_subject=${encodeURIComponent(subject)}`
                + `&txt_courseNumber=${encodeURIComponent(courseNumber)}`
                + '&txt_term=202530'
                + '&startDatepicker=&endDatepicker='
                + `&uniqueSessionId=${encodeURIComponent(sessionId)}`
                + '&pageOffset=0&pageMaxSize=10'
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

        subject_for_search = subject
        courseNuber_for_search = courseNuber
        result = self.driver.execute_async_script(fetch_js, url, csrf_token, unique_session, subject, courseNuber)
        return result

#   Finished -Refinable
    def print_sections_by_id(self,json_to_parse) -> str:
        import json
        if isinstance(json_to_parse, str):
            json_to_parse = json.loads(json_to_parse)
        
        # Optionally, only work with open sections
        """
        While we want to be eventually looking at open sections only it is important to first look for the sections indivudally finding commanilites by open sections.
         # sections = [section for section in json_to_parse["data"] if section.get("openSection")]
        # To get all sections, just: 
        """
        # To get all sections, just:
        sections = json_to_parse.get("data", [])

        for section in sections:
            section_id = section.get("id", "No ID")
            courseReferenceNumber = section.get("courseReferenceNumber")
            print(f"\n{'='*30}\nSection ID: {section_id}\n{'='*30}")
            print(f"\n{'='*30}\nCourse Reference Number: {courseReferenceNumber}\n{'='*30}") 
            print(json.dumps(section, indent=5))



#  <Develop a method that looks for open classes that are available to sign up>

    def find_open_classes(self, class_json):
      """
      Get data from the json.
      Find what determines if a class is available. If it is then return a json that contains course reference numbers with attached boolean value True or false that signfies if a class is avavilbe. 
      """







#   Finished -Refinable
    def shutdown_browser(self) -> None:
        """
        Closes the browser and cleans up resources.
        """
        self.driver.quit()

#   In Use
    def run(self) -> None:
        """
        Runs the course checker: selects term, injects XHR, and keeps the browser open for the specified runtime.
        """
        try:
            self.select_term()
            requested_object = self.inject_XHR(subject="MATH",courseNuber="024")
            self.print_sections_by_id(requested_object)


            self.find_open_classes(requested_object) #Not in use right now but will be used. 
            # Create a method to parse through json object look for request CRN return True if class is available to sign up or not. 

            time.sleep(self.runtime)
        finally:
            self.shutdown_browser()

if __name__ == "__main__":
    checker = CourseChecker(runtime=15)
    checker.run()
