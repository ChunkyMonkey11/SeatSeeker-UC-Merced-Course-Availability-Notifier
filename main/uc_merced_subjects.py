


"""
UC Merced Subject Codes
This file contains the actual subject codes for courses offered at UC Merced,
extracted from the registration system URL.
Organized by school/department for easy reference and filtering.
"""

# School of Engineering
ENGINEERING_SUBJECTS = [
    "BIOE",  # Bioengineering
    "CSE",   # Computer Science and Engineering
    "CEE",   # Civil and Environmental Engineering
    "EE",    # Electrical Engineering
    "EECS",  # Electrical Engineering and Computer Science
    "ME",    # Mechanical Engineering
    "MSE",   # Materials Science and Engineering
    "ENGR",  # Engineering (general)
    "ENG",   # Engineering (alternative)
]

# School of Natural Sciences
NATURAL_SCIENCES_SUBJECTS = [
    "BIO",   # Biological Sciences
    "CHEM",  # Chemistry and Chemical Biology
    "CHE",   # Chemistry (alternative)
    "MATH",  # Applied Mathematics
    "PHYS",  # Physics
    "PSY",   # Psychological Sciences
    "NEUR",  # Neuroscience
    "QSB",   # Quantitative and Systems Biology
    "MBSE",  # Molecular and Cell Biology
]

# School of Social Sciences, Humanities and Arts
SOCIAL_SCIENCES_SUBJECTS = [
    "ANTH",  # Anthropology
    "CRES",  # Critical Race and Ethnic Studies
    "ECON",  # Economics
    "HIST",  # History
    "POLI",  # Political Science
    "SOC",   # Sociology
    "WRI",   # Writing
    "COMM",  # Communication
    "PHIL",  # Philosophy
    "SPAN",  # Spanish
    "FRE",   # French
    "JPN",   # Japanese
    "GEOG",  # Geography
]

# Interdisciplinary Programs
INTERDISCIPLINARY_SUBJECTS = [
    "COGS",  # Cognitive and Information Sciences
    "GASP",  # Global Arts Studies Program
    "MIST",  # Management of Innovation, Sustainability and Technology
    "ESS",   # Environmental Systems Science
    "ES",    # Environmental Systems
    "EH",    # Environmental Health
    "IH",    # Interdisciplinary Honors
    "HON",   # Honors
    "USTU",  # University Studies
    "GSTU",  # Global Studies
    "HS",    # Health Sciences
    "PH",    # Public Health
    "DSA",   # Data Science and Analytics
    "DSC",   # Data Science
    "CCST",  # Critical and Creative Studies
    "CRS",   # Critical Race Studies
    "NSED",  # Natural Sciences Education
    "EDUC",  # Education
    "ROTC",  # Reserve Officers' Training Corps
    "SPRK",  # Spark (special programs)
]

# Additional/Alternative Subject Codes
ADDITIONAL_SUBJECTS = [
    "BCME",  # Bioengineering and Chemical Engineering
    "MGMT",  # Management
]

# All subjects combined (from the actual URL)
ALL_SUBJECTS = [
    "ANTH", "BCME", "BIOE", "BIO", "CHE", "CHEM", "CCST", "CEE", "COGS", "COMM", 
    "CRS", "CSE", "CRES", "DSA", "DSC", "ECON", "EDUC", "EECS", "EE", "ENGR", 
    "ENG", "EH", "ES", "ESS", "FRE", "GEOG", "GASP", "GSTU", "HS", "HIST", 
    "IH", "JPN", "MGMT", "MBSE", "MSE", "MATH", "ME", "MIST", "NSED", "NEUR", 
    "PHIL", "PHYS", "POLI", "PSY", "PH", "QSB", "ROTC", "SOC", "SPAN", "SPRK", 
    "USTU", "HON", "WRI"
]

def get_subjects_by_school(school_name):
    """
    Get subjects for a specific school
    
    Args:
        school_name (str): Name of the school (case-insensitive)
        
    Returns:
        list: List of subject codes for the specified school
        
    Example:
        >>> get_subjects_by_school("engineering")
        ['BIOE', 'CSE', 'CEE', 'EE', 'EECS', 'ME', 'MSE', 'ENGR', 'ENG']
    """
    school_map = {
        "engineering": ENGINEERING_SUBJECTS,
        "natural_sciences": NATURAL_SCIENCES_SUBJECTS,
        "social_sciences": SOCIAL_SCIENCES_SUBJECTS,
        "interdisciplinary": INTERDISCIPLINARY_SUBJECTS,
        "all": ALL_SUBJECTS
    }
    return school_map.get(school_name.lower(), ALL_SUBJECTS)

def get_all_subjects():
    """
    Get all available subject codes from the actual UC Merced system
    
    Returns:
        list: Complete list of all subject codes (53 total)
        
    Example:
        >>> get_all_subjects()
        ['ANTH', 'BCME', 'BIOE', 'BIO', 'CHE', 'CHEM', ...]
    """
    return ALL_SUBJECTS.copy()

def get_schools():
    """
    Get list of available schools
    
    Returns:
        list: List of school names
        
    Example:
        >>> get_schools()
        ['engineering', 'natural_sciences', 'social_sciences', 'interdisciplinary']
    """
    return ["engineering", "natural_sciences", "social_sciences", "interdisciplinary"]

def search_subjects(keyword):
    """
    Search for subjects by keyword
    
    Args:
        keyword (str): Keyword to search for in subject codes or descriptions
        
    Returns:
        list: Matching subject codes
        
    Example:
        >>> search_subjects("computer")
        ['CSE', 'EECS']
    """
    keyword = keyword.upper()
    matches = []
    
    # Subject code to description mapping
    subject_descriptions = {
        "ANTH": "Anthropology",
        "BCME": "Bioengineering and Chemical Engineering",
        "BIOE": "Bioengineering",
        "BIO": "Biological Sciences",
        "CHE": "Chemistry",
        "CHEM": "Chemistry and Chemical Biology",
        "CCST": "Critical and Creative Studies",
        "CEE": "Civil and Environmental Engineering",
        "COGS": "Cognitive and Information Sciences",
        "COMM": "Communication",
        "CRS": "Critical Race Studies",
        "CSE": "Computer Science and Engineering",
        "CRES": "Critical Race and Ethnic Studies",
        "DSA": "Data Science and Analytics",
        "DSC": "Data Science",
        "ECON": "Economics",
        "EDUC": "Education",
        "EECS": "Electrical Engineering and Computer Science",
        "EE": "Electrical Engineering",
        "ENGR": "Engineering",
        "ENG": "Engineering",
        "EH": "Environmental Health",
        "ES": "Environmental Systems",
        "ESS": "Environmental Systems Science",
        "FRE": "French",
        "GEOG": "Geography",
        "GASP": "Global Arts Studies Program",
        "GSTU": "Global Studies",
        "HS": "Health Sciences",
        "HIST": "History",
        "IH": "Interdisciplinary Honors",
        "JPN": "Japanese",
        "MGMT": "Management",
        "MBSE": "Molecular and Cell Biology",
        "MSE": "Materials Science and Engineering",
        "MATH": "Applied Mathematics",
        "ME": "Mechanical Engineering",
        "MIST": "Management of Innovation, Sustainability and Technology",
        "NSED": "Natural Sciences Education",
        "NEUR": "Neuroscience",
        "PHIL": "Philosophy",
        "PHYS": "Physics",
        "POLI": "Political Science",
        "PSY": "Psychological Sciences",
        "PH": "Public Health",
        "QSB": "Quantitative and Systems Biology",
        "ROTC": "Reserve Officers' Training Corps",
        "SOC": "Sociology",
        "SPAN": "Spanish",
        "SPRK": "Spark",
        "USTU": "University Studies",
        "HON": "Honors",
        "WRI": "Writing"
    }
    
    for subject in ALL_SUBJECTS:
        if (keyword in subject or 
            keyword in subject_descriptions.get(subject, "").upper()):
            matches.append(subject)
    
    return matches

def get_subject_count():
    """
    Get the total number of subject codes
    
    Returns:
        int: Total number of subject codes
        
    Example:
        >>> get_subject_count()
        53
    """
    return len(ALL_SUBJECTS)

# For backward compatibility - export the main list as 'subjects'
subjects = ALL_SUBJECTS
