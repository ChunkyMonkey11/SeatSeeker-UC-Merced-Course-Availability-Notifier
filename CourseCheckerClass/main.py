"""
main.py will remains as a standalone script that will be used to design functions for effective testing of the CourseScrapper class.
    1. First recreate the function that sorts through requestedClasses it will do this and return a list of courseReferenceNumbers that are open for enrollment.
    2. 

"""

from ClassAutomation import CourseScraper


def find_open_sections(all_classes_json) -> list:
    """
    Takes a list where each item is a dict (JSON response from the API for a subject/course),
    and returns a list of all open sections' courseReferenceNumbers.
    """
    open_sections = []
    import json

    for classes_to_parse in all_classes_json:
        try:
            # If item is a JSON string, decode it first
            if isinstance(classes_to_parse, str):
                classes_to_parse = json.loads(classes_to_parse)
            sections = classes_to_parse.get("data", [])
            for section in sections:
                openSection = section.get("openSection")
                seatsAvailable = section.get("seatsAvailable")
                courseReferenceNumber = section.get("courseReferenceNumber")
                if openSection and (seatsAvailable > 0):
                    open_sections.append(courseReferenceNumber)
        except (json.JSONDecodeError, AttributeError, TypeError) as e:
            print(f"Error parsing sections: {e}")
    return open_sections


def find_open_sections_by_subject(list_of_classes_lists) -> dict:
    """
    Accepts a list of lists, where each sublist contains dicts for each course section (from one subject).
    Returns a dict: {subject: [open courseReferenceNumbers, ...]}
    """
    open_sections_by_subject = {}
    for classes_for_course in list_of_classes_lists:
        for section in classes_for_course:
            subject = section.get("subject")
            openSection = section.get("openSection")
            seatsAvailable = section.get("seatsAvailable")
            courseReferenceNumber = section.get("courseReferenceNumber")
            
            # Safe check: seatsAvailable is not None and is > 0
            if openSection and seatsAvailable is not None and seatsAvailable > 0:
                if subject not in open_sections_by_subject:
                    open_sections_by_subject[subject] = []
                open_sections_by_subject[subject].append(courseReferenceNumber)
    return open_sections_by_subject





def collect_classes_info(user_info) -> dict:
    """
    find_open_sections_per_requested_course : Iterates over user information to find open courses for the specified subject and course number.

    Parameters:
    # Iterate over the object
                          {
                              "email": "user@example.com",
                              "classes": [
                                  {
                                      "subject": "SUBJECT",
                                      "courseNumber": "COURSE_NUMBER",
                                      "courseReferenceNumber": "REFERENCE_NUMBER"
                                  }
                              ]
                          }

    Returns:
        dict: A dictionary containing the user's email and a list of open course reference numbers for the requested classes.
              Example format:
              {
                  "email": "user@example.com",
                  "openCourses": ["REFERENCE_NUMBER_1", "REFERENCE_NUMBER_2"]
              }

    Behavior:
        - Extracts the user's email and requested classes from the input dictionary.
        - Finds open courses for the specified subject and course number.
        - Returns a dictionary with the user's email and a list of open course reference numbers.
    """
    # Collect needed user info
    user_info = user_info
    user_email = user_info.get("email")
    classes = user_info.get("classes", [])
    scraper = CourseScraper(runtime=30)
    scraper.start_browser()


    if not user_email or not isinstance(classes, list):
        print("Error: Missing or invalid 'email' or 'classes' in user_info.")
        return {}
    

    class_info = [] 
    for course in classes:
        subject = course.get("subject")
        courseNumber = course.get("courseNumber")
        try:
            class_info_being_found = scraper.fetch_course_data_pagination(subject=subject, courseNumber=courseNumber)
            class_info.append(class_info_being_found)
            # Refresh Needs to be called in order for a new request to be made. 
            scraper.refreshDriver()
        except Exception as e:
            class_info.append(f"The class with Subject: {subject} and courseNumber: {courseNumber} ran into Exception {e}")
    
    return class_info

# This is a test function that tests the pagination function
def scrape_one_class():
    subject = "MATH"
    courseNumber = "024"
    scraper = CourseScraper(runtime=25)
    scraper.start_browser()
    scraped_course_info = scraper.fetch_course_data_pagination(subject=subject, courseNumber=courseNumber)
    scraper.shutdown_browser
    return scraped_course_info

user_zero_info = {
    "email": "revant.h.patel@gmail.com",
    "classes": [
        {
            "subject": "MATH",
            "courseNumber": "024",
            "courseReferenceNumber": "30085"
        },
        {
            "subject": "CSE",
            "courseNumber": "015",
            "courseReferenceNumber": "30515"
        }
    ]
}

class_info = collect_classes_info(user_zero_info)

availableClassesBySubject = find_open_sections_by_subject(class_info)
print(availableClassesBySubject)
