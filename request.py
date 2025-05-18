from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests

def init_guest_session():
    """Launches browser to simulate a guest visiting the class search page. Extracts cookies and session ID."""
    options = Options()
    # Uncomment this for background (headless) mode:
    # options.add_argument("--headless=new")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get("https://reg-prod.ec.ucmerced.edu/StudentRegistrationSsb/ssb/registration")

        # Try to click 'Register for Classes' button to initiate session
        register_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "registerLink"))
        )
        register_btn.click()

        # Extract cookies
        cookies = {c['name']: c['value'] for c in driver.get_cookies()}

        # Extract session ID from sessionStorage
        session_id = driver.execute_script("return window.sessionStorage.getItem('uniqueSessionId');")

        return cookies, session_id

    except Exception as e:
        print("[init_guest_session] Error during session setup:", e)
        return {}, None

    finally:
        driver.quit()

def fetch_course_data(cookies, session_id):
    """Uses cookies and session ID to call the course API."""
    session = requests.Session()
    for k, v in cookies.items():
        session.cookies.set(k, v)

    url = "https://reg-prod.ec.ucmerced.edu/StudentRegistrationSsb/ssb/searchResults/searchResults"

    params = {
        "txt_subject": "CSE",
        "txt_courseNumber": "005",
        "txt_term": "202530",
        "startDatepicker": "",
        "endDatepicker": "",
        "uniqueSessionId": session_id,
        "pageOffset": 0,
        "pageMaxSize": 10,
        "sortColumn": "subjectDescription",
        "sortDirection": "asc"
    }

    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest"
    }

    response = session.get(url, params=params, headers=headers)
    print("Status:", response.status_code)
    print(response.json())

if __name__ == "__main__":
    cookies, session_id = init_guest_session()
    if session_id:
        fetch_course_data(cookies, session_id)
    else:
        print("Session ID not found. API request aborted./n")
        print("init_guest_session : failed to find info ")
