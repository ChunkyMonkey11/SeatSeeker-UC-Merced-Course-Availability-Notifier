from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import requests
import time

def init_guest_session():
    """Launch Chrome, hit the search page, and grab cookies + tokens."""
    options = Options()
    # options.add_argument("--headless=new") #Use for headless testing.

    # Chrome Driver Instance
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    # 1️⃣ Go to the page that issues your tokens+cookies
    driver.get("https://reg-prod.ec.ucmerced.edu/StudentRegistrationSsb/ssb/term/termSelection?mode=search")
    time.sleep(5)  # let JS fire and storage/meta tags populate

    # 2️⃣ Grab all cookies
    cookies = {c['name']: c['value'] for c in driver.get_cookies()}

    # 3️⃣ Grab your session ID from sessionStorage
    session_id = driver.execute_script(
        "return window.sessionStorage.getItem"
        "('xe.unique.session.storage.id');"
    )

    # 4️⃣ Grab the CSRF token (meta tag or hidden input)
    sync_token = driver.execute_script(
        "let m = document.querySelector"
        "('meta[name=\"synchronizerToken\"]');"
        "return m ? m.content : null;"
    )

    return driver, cookies, session_id, sync_token


def fetch_course_data(cookies, session_id, sync_token, max_retries=5):
    """Replay the AJAX call using requests, retrying if 'data' is null/empty."""
    session = requests.Session()
    # seed the session with your Selenium cookies
    for name, val in cookies.items():
        session.cookies.set(name, val)

    url = "https://reg-prod.ec.ucmerced.edu/StudentRegistrationSsb/ssb/searchResults/searchResults"
    params = {
        "txt_subject":      "CSE",
        "txt_courseNumber": "005",
        "txt_term":         "202530",
        "startDatepicker":  "",
        "endDatepicker":    "",
        "uniqueSessionId":  session_id,
        "pageOffset":       0,
        "pageMaxSize":      10,
        "sortColumn":       "subjectDescription",
        "sortDirection":    "asc",
    }
    headers = {
        "Accept":               "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With":     "XMLHttpRequest",
        "X-Synchronizer-Token": sync_token,
        "Referer":              "https://reg-prod.ec.ucmerced.edu/StudentRegistrationSsb/ssb/classSearch/classSearch",
        "User-Agent":           "Mozilla/5.0",
    }

    for attempt in range(1, max_retries + 1):
        resp = session.get(url, params=params, headers=headers)
        print(resp)
        resp.raise_for_status()
        payload = resp.json()
        print(payload)
        # Check if we got real data (not null or empty)
        if payload.get("data"):
            return payload

        # otherwise wait a bit and retry
        print(f"Attempt {attempt} returned no data; retrying…")
        time.sleep(1)

    # If we fall out of the loop, all attempts failed
    raise RuntimeError(f"No valid data after {max_retries} retries")

if __name__ == "__main__":
    driver, cookies, session_id, sync_token = init_guest_session()

    if not session_id or not sync_token:
        print("❌ Missing session ID or sync token; aborting.")
    else:
        data = fetch_course_data(cookies, session_id, sync_token)
        print("✅ Course data:", data)

    driver.quit()
