import os
import urllib.parse

import requests

from uc_merced_subjects import subjects as all_subjects


class ClassChecker:
    """Fetch course registration data and extract open CRNs."""

    def __init__(self):
        self.term = os.getenv("TERM_CODE", "202630")
        configured_subjects = os.getenv("SUBJECT_CODES", "")
        if configured_subjects.strip():
            self.courses_to_grab = [s.strip().upper() for s in configured_subjects.split(",") if s.strip()]
        else:
            self.courses_to_grab = all_subjects

        encoded_subjects = urllib.parse.quote(",".join(self.courses_to_grab))
        self.url1 = (
            "https://reg-prod.ec.ucmerced.edu/StudentRegistrationSsb/ssb/term/search"
            f"?mode=search&term={self.term}"
        )
        self.url2 = (
            "https://reg-prod.ec.ucmerced.edu/StudentRegistrationSsb/ssb/searchResults/searchResults"
            f"?txt_subject={encoded_subjects}&txt_term={self.term}&pageOffset=0&pageMaxSize=2000"
        )
        self.timeout_seconds = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))
        self.session = requests.Session()
        self.course_data = {"data": []}
        self.open_section_signatures = set()

    @staticmethod
    def extract_dataset_date(section):
        meetings = section.get("meetingsFaculty", []) if isinstance(section, dict) else []
        dates = []

        for meeting in meetings:
            if not isinstance(meeting, dict):
                continue
            meeting_time = meeting.get("meetingTime")
            if not isinstance(meeting_time, dict):
                continue
            start_date = str(meeting_time.get("startDate", "")).strip()
            if start_date:
                dates.append(start_date)

        if dates:
            return min(dates)

        fallback_term = str(section.get("term", "")).strip() if isinstance(section, dict) else ""
        if fallback_term:
            return f"term:{fallback_term}"

        return "unknown"

    def fetch(self):
        """Fetch course data from UC Merced registration APIs."""
        self.session.post(self.url1, timeout=self.timeout_seconds)
        response = self.session.get(self.url2, timeout=self.timeout_seconds)
        response.raise_for_status()
        self.course_data = response.json()
        return self.course_data

    def find_open_sections(self):
        open_crns = set()

        if not isinstance(self.course_data, dict) or "data" not in self.course_data:
            return open_crns

        for section in self.course_data["data"]:
            if not isinstance(section, dict):
                continue

            crn = section.get("courseReferenceNumber")
            is_open = section.get("openSection")
            seats = section.get("seatsAvailable", 0)

            if crn and is_open and seats > 0:
                open_crns.add(str(crn))

        return open_crns

    def find_open_section_signatures(self):
        signatures = set()

        if not isinstance(self.course_data, dict) or "data" not in self.course_data:
            return signatures

        for section in self.course_data["data"]:
            if not isinstance(section, dict):
                continue

            crn = section.get("courseReferenceNumber")
            is_open = section.get("openSection")
            seats = section.get("seatsAvailable", 0)

            if crn and is_open and seats > 0:
                dataset_date = self.extract_dataset_date(section)
                signatures.add((str(crn), dataset_date))

        return signatures

    def run(self):
        self.fetch()
        self.open_section_signatures = self.find_open_section_signatures()
        return self.find_open_sections()
