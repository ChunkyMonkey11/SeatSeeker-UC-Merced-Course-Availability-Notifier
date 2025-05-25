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
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://reg-prod.ec.ucmerced.edu/StudentRegistrationSsb/ssb/registration")

    # Now navigate to the session-creating page
    driver.get("https://reg-prod.ec.ucmerced.edu/StudentRegistrationSsb/ssb/classSearch/classSearch")

    # Wait for sessionStorage to be ready
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script("return sessionStorage.getItem('xe.unique.session.storage.id') !== null")
    )

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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://reg-prod.ec.ucmerced.edu/StudentRegistrationSsb/ssb/classSearch/classSearch",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Sec-CH-UA": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
    "Priority": "u=1, i"
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
        "txt_courseNumber": "005",
        "txt_term": "202530",
        "startDatepicker": "",
        "endDatepicker": "",
        "uniqueSessionId": data["uniqueSessionId"],
        "pageOffset": "0",
        "pageMaxSize": "10",
        "sortColumn": "subjectDescription",
        "sortDirection": "asc"
    }

    # Clean headers to avoid Cookie conflict
    headers = {k: v for k, v in data["headers"].items() if k.lower() != "cookie"}

    response = requests.get(url, headers=headers, cookies=data["cookies"], params=params)

    print("Final URL:", response.url)
    print("Status Code:", response.status_code)
    print("Response Preview:", response.text[:300])

    response.raise_for_status()
    return response.json()


MAX_ATTEMPTS = 5
DATA_FOUND_FLAG = False
attempt = 0

while attempt < MAX_ATTEMPTS and not DATA_FOUND_FLAG:
    driver = open_intial_tab()
    data = collect_header_information(driver)
    print(f"{attempt+1} Try Has uniqueSessionId->{data['uniqueSessionId']}, as well as headers->{data['headers']}")
    
    try:
        result = get_json_data(data)
        if result.get("data"):  # ✅ Ensures 'data' key exists and is not empty
            DATA_FOUND_FLAG = True
            print("✅ Data Found:")
            print(result["data"])
            driver.quit() 
        else:
            print("⚠️ No data found, retrying...")
            driver.quit()
            attempt += 1
            time.sleep(1)
    except Exception as e:
        print(f"🔥 Exception occurred: {e}")
        driver.quit()
        attempt += 1
        time.sleep(1)


