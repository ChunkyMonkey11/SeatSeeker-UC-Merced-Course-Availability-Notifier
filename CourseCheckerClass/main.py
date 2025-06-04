from ClassAutomation import CourseScraper


scraper = CourseScraper(runtime=1, subject="MATH", courseNumber="024")
requested_object = scraper.run()
print(requested_object)

