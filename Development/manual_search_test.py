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

    def perform_class_search(self, subject="CSE", course_number="005"):
        """
        Fills out the subject and course number and submits the search.
        """
        subject_box = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "s2id_txt_subject")))
        subject_box.click()

       
        # wait until the mask is gone
        self.driver.execute_script("""
            const mask = document.getElementById('select2-drop-mask');
            if (mask && mask.parentNode) {
                mask.parentNode.removeChild(mask);
            }
            """)
   
        search_input = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "s2id_txt_subject"))
        )
        search_input.click()

        subject_found = False
        attempts = 0
        max_attempts = 15

        while not subject_found and attempts < max_attempts:

            # Rewrite this bullshit 
            # try:
            #     print("Try works")
            #     select_subject = WebDriverWait(self.driver, 10).until(
            #         EC.element_to_be_clickable((By.ID,"CSE"))
            #     ) 
            #     select_subject.click()
            #     subject_found = True  # Correct assignment
            # except TimeoutError:
            #     print("Timeout Error")
            # # Use search_input for arrow down
            #     search_input.send_keys(Keys.ARROW_DOWN)
            #     search_input.send_keys(Keys.ENTER)  
            #     attempts += 1  # Increment attempts
                



            # Course Number
            course_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "txt_courseNumber"))
            )
            course_input.clear()
            course_input.send_keys(course_number)

            # Click the Search button
            search_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "searchButton"))
            )
            search_button.click()

            # Wait for the results container
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,".searchResultsContainer"))
            )

    def shutdown(self):
        """Clean up the browser."""
        self.driver.quit()

    def run(self):
        try:
            self.select_term()
            self.perform_class_search()
            time.sleep(self.runtime)
        finally:
            self.shutdown()


if __name__ == "__main__":
    checker = CourseChecker(runtime=15)
    checker.run()
