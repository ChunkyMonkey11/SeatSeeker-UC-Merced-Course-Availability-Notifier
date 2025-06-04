"""
main.py will remains as a standalone script that will be used to design functions for effective testing of the CourseScrapper class.
    1. First recreate the function that sorts through requestedClasses it will do this and return a list of courseReferenceNumbers that are open for enrollment.
    2. 

"""

from ClassAutomation import CourseScraper

# scraper is equal to a CourseScraper object.
scraper = CourseScraper(runtime=1, subject="CSE", courseNumber="015")
requested_object = scraper.run()
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

def find_open_sections_per_requested_course(user_info) -> dict:
    # Write a function that iterates over user_zero_info and finds open courses for the subject and courseNumber. If the requested class is in that list. Send email. 
    pass



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
