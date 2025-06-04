UC Merced Course Availability Checker
This project automates the process of checking class availability on the UC Merced registration system.

Project Structure
ClassAutomation.py
Contains the CourseScraper class, which handles browser automation and data retrieval. This class uses Selenium to fetch course and section data directly from the UC Merced registration portal.

main.py
Demonstrates how to use the CourseScraper class. It calls the scraper to fetch live class data, then processes the results to search for open sections and compare them against a target course reference number (CRN) or list of desired classes.

How It Works
main.py imports the CourseScraper class from ClassAutomation.py.

The scraper navigates to the UC Merced course registration page and retrieves real-time course data.

After fetching data, main.py parses the response to:

Identify which sections are currently open for registration.

Cross-compare open sections against user-specified CRNs or courses of interest.

