

"""
                            The ClassChecker module when ran goes and fetches all crns that are available to register for and stores them in a set.
                            The set returned can be used evaluate if a user requested class is available.
"""






import requests
import urllib.parse

class ClassChecker:
    def __init__(self):
        self.url1 = 'https://reg-prod.ec.ucmerced.edu/StudentRegistrationSsb/ssb/term/search?mode=search&term=202530'
        self.courses_to_grab = ["ANTH","WRI"]
        encoded_subjects = urllib.parse.quote(",".join(self.courses_to_grab))
        self.url2 = f"https://reg-prod.ec.ucmerced.edu/StudentRegistrationSsb/ssb/searchResults/searchResults?txt_subject={encoded_subjects}&txt_term=202530&pageOffset=0&pageMaxSize=50" 

        
        # Start a session to persist cookies
        self.session = requests.Session()

        # Step 1: Post request to set required cookies
        response1 = self.session.post(self.url1)
        
        # Step 2: Request to get CSE classes
        response2 = self.session.get(self.url2)

        # Step 3: Save all course data as a json object
        self.course_data = response2.json()
   
    def find_open_sections(self):
        open_crns = set()

        if not isinstance(self.course_data, dict) or "data" not in self.course_data:
            print("No valid data to process.")
            return open_crns
        
        for section in self.course_data["data"]:
            if not isinstance(section, dict):
                continue
            crn = section.get("courseReferenceNumber")
            open_section = section.get("openSection")
            seats = section.get("seatsAvailable", 0)

            if crn and open_section and seats > 0:
                open_crns.add(crn)

        return open_crns 

    def write_data_to_file(self):
        with open("course.json", "w+") as f:
            all_course_data = str(self.course_data)
            f.write(all_course_data)
        f.close()

        with open("available_CRNS.txt", "w") as CRNFILE:
            open_sections = str(self.find_open_sections())
            CRNFILE.write(open_sections)
        CRNFILE.close()

    def run(self):
        self.session = requests.Session()
        response1 = self.session.post(self.url1)
        response2 = self.session.get(self.url2)
        open_sections = response2.json()
        open_sections = self.find_open_sections()
        # self.write_data_to_file()
        return open_sections


