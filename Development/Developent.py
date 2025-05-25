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
    # Constuctor
    def __init__(self, runtime=15):
        options = Options()
        # uncomment the next line to run headless
        # options.add_argument("--headless=new")  # Uncomment this line to run the browser in headless mode (no UI).

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        self.runtime = runtime
        # URL for the class search page
        self.url = (
            "https://reg-prod.ec.ucmerced.edu/StudentRegistrationSsb/ssb/term/termSelection?mode=search"
        )

    # select_terms(): method that selects fall 2025 term and continues to the class search page
    def select_term(self, term_value="202530"):
        """
        Selects the term (e.g. Fall 2025) from the Select2 dropdown.
        """
        self.driver.get(self.url)

        # Wait for the term dropdown to be clickable and open it
        term_container = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "s2id_txt_term"))
        )
        term_container.click()
        

        # Wait for and click the specific term option
        # Use the term_value argument to dynamically select the term
        term_option = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, term_value))
        )
        term_option.click() 

        continue_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "term-go"))
        )
        continue_btn.click()

    # prepare_for_xhr_injection(): method does the bare minimum to prepare the browser to be able to send an XHR request. 
    def prepare_for_xhr_injection(self):
            subject_box = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "s2id_txt_subject")))
            subject_box.click()


    # peform_class_search(): method should select subject for class result search
    def select_subject(self, subject="CSE"):
        """
        Fills out the subject and course number and submits the search.
        """
        subject_box = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "s2id_txt_subject")))
        subject_box.click()

    
       # Type the subject into the input field
        search_input = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "select2-input"))
        )
        search_input.clear()
        search_input.send_keys(subject)

        # Wait for the matching result and click it
        result = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//div[@id='{subject}']"))
        )
        result.click()
    

    # fill_out_course_number(): method that fills out the course number and performs search
    def fill_out_course_number(self, course_number="005"):
        # Fill out Course Number
        course_input = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "txt_courseNumber"))
        )
        course_input.clear()
        course_input.send_keys(course_number)

        # Click the Search button
        search_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "search-go"))
        )
        search_button.click()
    
    # Manually inject XHR from inside the broswer...
    def inject_XHR(self):
        import json
        # Make method call prepare_for_xhr_injection so driver is prepared to send fetch request
        self.prepare_for_xhr_injection()
        url = "https://reg-prod.ec.ucmerced.edu/StudentRegistrationSsb/ssb/searchResults/searchResults"

        unique_session = self.driver.execute_script(
            "return window.localStorage.getItem('uniqueSessionId');"
        )
        csrf_token = self.driver.execute_script(
            "return window.localStorage.getItem('x-synchronizer-token');"
        )

        # 3. Define the in-browser fetch as an async script
        fetch_js = """
        const [url, token, sessionId, cb] = arguments;
        const qs = '?txt_subject=MATH'
                + '&txt_courseNumber=024'
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

        # 4. Execute it and capture the result
        result = self.driver.execute_async_script(fetch_js, url, csrf_token, unique_session)

        # 5. Print it nicely
        print(json.dumps(result, indent=2))

    
    def shutdown_browser(self):
        """Clean up the browser."""
        self.driver.quit()

    def run(self):
        try:
            self.select_term()
            self.inject_XHR()
            time.sleep(self.runtime)
        finally:
            self.shutdown_browser()


if __name__ == "__main__":
    checker = CourseChecker(runtime=15)
    checker.run()
