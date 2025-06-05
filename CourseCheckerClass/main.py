"""
main.py will remains as a standalone script that will be used to design functions for effective testing of the CourseScrapper class.
    1. First recreate the function that sorts through requestedClasses it will do this and return a list of courseReferenceNumbers that are open for enrollment.
    2. 

"""

from ClassAutomation import CourseScraper


# Find Open_Sections Function
def find_open_sections(classes_to_parse) -> list:
    import json
    """
        find_open_sections : returns a list of open classes to sign up for based on subject, and course Number. 
    """
   
    open_sections = []
    try:
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
    scraper = CourseScraper(runtime=15)
    scraper.start_browser()


    if not user_email or not isinstance(classes, list):
        print("Error: Missing or invalid 'email' or 'classes' in user_info.")
        return {}
    

    class_info = [] 
    for course in classes:
        subject = course.get("subject")
        courseNumber = course.get("courseNumber")
        try:
            class_info_being_found = scraper.scrape_course(subject=subject,courseNumber=courseNumber)
            class_info.append(class_info_being_found)
            # Implement a refresh Driver method in the ClassAutomation file.
            scraper.refreshDriver()
        except Exception as e:
            class_info.append(f"The class with Subject: {subject} and courseNumber: {courseNumber} ran into Exception {e}")
    
    scraper.shutdown_browser
    return class_info


    # For each class we want to search for and find all open classes based on subject and course number.

    


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
 
for classToPrint in class_info:
    print(f"{"="*30}")
    print(classToPrint)
    print(f"{"="*30}")
    
