import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests

""" TO CODE """
#1 Start browser.
def open_intial_tab():
    options = Options()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)
    starting_url = "https://reg-prod.ec.ucmerced.edu/StudentRegistrationSsb/ssb/registration"
    driver.get(starting_url)
    return driver

#2 Collect Cookies Information and Unique Session ID
def collect_header_information(driver):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # 🍪 Extract Cookies
    cookies = driver.get_cookies()
    cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
    cookie_header = "; ".join(f"{k}={v}" for k, v in cookie_dict.items())

    # 🧠 Access Local Storage via JS
    local_storage = driver.execute_script(
        "let items = {}; "
        "for (let i = 0; i < localStorage.length; i++) { "
        "   let key = localStorage.key(i); "
        "   items[key] = localStorage.getItem(key); "
        "} "
        "return items;"
    )

    # 🧬 Try extracting session-related fields
    synchronizer_token = local_storage.get("x-synchronizer-token") or local_storage.get("synchronizerToken")
    unique_session_id = driver.execute_script("return sessionStorage.getItem('xe.unique.session.storage.id')")

    # 🧬 Construct headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://reg-prod.ec.ucmerced.edu/StudentRegistrationSsb/ssb/classSearch/classSearch",
        "X-Requested-With": "XMLHttpRequest",
        "Cookie": cookie_header
    }

    if synchronizer_token:
        headers["x-synchronizer-token"] = synchronizer_token

    return {
        "headers": headers,
        "cookies": cookie_dict,
        "local_storage": local_storage,
        "uniqueSessionId": unique_session_id
    }

# Get JSON Response
def get_json_data(data):
    url = "https://reg-prod.ec.ucmerced.edu/StudentRegistrationSsb/ssb/searchResults/searchResults"

    params = {
        "txt_subject": "CSE",
        "txt_courseNumber": 005,
        "txt_term": 202530,
        "startDatepicker": "",
        "endDatepicker": "",
        "uniqueSessionId": data["uniqueSessionId"],
        "pageOffset": str(0),
        "pageMaxSize": str(10),
        "sortColumn": "subjectDescription",
        "sortDirection": "asc"
    }

    # Launch the GET request
    response = requests.get(url, headers=data["headers"], cookies=data["cookies"], params=params)

    # Raise exception if error
    response.raise_for_status()

    # Return parsed JSON
    return response.json()





driver = open_intial_tab()
data = collect_header_information(driver)
result = get_json_data(data)
print(data["uniqueSessionId"])
print(data["headers"])
print(result)