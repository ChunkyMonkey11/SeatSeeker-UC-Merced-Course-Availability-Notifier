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
    def __init__(self, runtime=15):
        options = Options()
        # uncomment the next line to run headless
        # options.add_argument("--headless=new")

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
        # "202530" is the ID that corresponds to Fall 2025 
        term_option = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "202530"))
        )
        term_option.click() 

        continue_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "term-go"))
        )
        continue_btn.click()

    # peform_class_search(): method should select subject for class result search
    def select_subject(self, subject="CSE"):
        """
        Fills out the subject and course number and submits the search.
        """
        subject_box = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "s2id_txt_subject")))
        subject_box.click()

        
        # wait until the mask is gone
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
    def inject():
        raise KeyError




















    def shutdown(self):
        """Clean up the browser."""
        self.driver.quit()

    def run(self):
        try:
            self.select_term()
            self.select_subject()
            self.inject()
            # self.fill_out_course_number()
            time.sleep(self.runtime)
        finally:
            self.shutdown()


if __name__ == "__main__":
    checker = CourseChecker(runtime=15)
    checker.run()
