import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "main"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from ClassChecker import ClassChecker


def test_find_open_section_signatures_keeps_distinct_dataset_dates():
    checker = ClassChecker()
    checker.course_data = {
        "data": [
            {
                "courseReferenceNumber": "12345",
                "openSection": True,
                "seatsAvailable": 2,
                "meetingsFaculty": [
                    {"meetingTime": {"startDate": "08/26/2026"}},
                ],
            },
            {
                "courseReferenceNumber": "12345",
                "openSection": True,
                "seatsAvailable": 3,
                "meetingsFaculty": [
                    {"meetingTime": {"startDate": "09/02/2026"}},
                ],
            },
        ]
    }

    signatures = checker.find_open_section_signatures()

    assert signatures == {
        ("12345", "08/26/2026"),
        ("12345", "09/02/2026"),
    }


def test_extract_dataset_date_falls_back_to_term_when_meeting_start_date_missing():
    checker = ClassChecker()
    section = {
        "term": "202630",
        "meetingsFaculty": [{"meetingTime": {}}],
    }

    assert checker.extract_dataset_date(section) == "term:202630"
