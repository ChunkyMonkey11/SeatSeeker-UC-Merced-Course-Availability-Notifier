"""
main.py will remains as a standalone script that will be used to design functions for effective testing of the CourseScrapper class.
    1. First recreate the function that sorts through requestedClasses it will do this and return a list of courseReferenceNumbers that are open for enrollment.
    2. 

"""

from ClassAutomation import CourseScraper

#collect class information based on user data. 
def collect_classes_info(user_info) -> list:
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
    scraper = CourseScraper(runtime=3)
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



# Tries to collect class data on every possible class at UC MERCED
def collect_all_classes_info(subjects) -> list:

    scraper = CourseScraper(runtime=10)
    scraper.start_browser()

    classes = subjects
    class_info = [] 
    requested_info = scraper.fetch_course_data_pagination(subjects=classes)
    
    for class_to_add in requested_info:
        class_info.append(class_to_add)
    scraper.shutdown_browser()
    return requested_info




# TO DEVELOP: NEEDS TO BE ABLE TO PARSE EVERY COURSE RETRIVED.
def find_open_sections_by_subject(courses: list) -> dict:
    """
    Accepts a list of course section dictionaries.
    Returns a dictionary {subject: [open courseReferenceNumbers]}
    """
    open_sections_by_subject = {}

    for section in courses:
        # Defensive: skip if section is not a dict
        if not isinstance(section, dict):
            continue

        subject = section.get("subject")
        course_ref = section.get("courseReferenceNumber")
        open_section = section.get("openSection")
        seats = section.get("seatsAvailable", 0)

        if subject and open_section and seats > 0:
            if subject not in open_sections_by_subject:
                open_sections_by_subject[subject] = []
            open_sections_by_subject[subject].append(course_ref)

    return open_sections_by_subject

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


subjects = ["ANTH","BCME","BIOE","BIO","CHEM","CCST","CHN","CEE","COGS","COMM","CRS","CSE","CRES","DSA","DSC","ECON","EDUC","EECS","EE","ENGR","ENG","EH","ES","ESS","FRE","GEOG","GASP","GSTU","HS","HIST","IH","JPN","MGMT","MBSE","MSE","MATH","ME","MIST","NSED","NEUR","PHIL","PHYS","POLI","PSY","PH","QSB","ROTC","SOC","SPAN","SPRK","USTU","WRI"]
all_class_info = collect_all_classes_info(subjects)

def write_class_info_to_file(class_data):
    class_data = all_class_info
    converted_data = str(class_data)
    with open("demofile.txt", "w") as f:
        f.write(converted_data)
    return(print("WE HAVE WRITTEN ALL DATA TO : demofile.txt"))

open_classes = find_open_sections_by_subject(all_class_info)
for subject,crns in open_classes.items():
    print(f"{subject}: {crns}")



