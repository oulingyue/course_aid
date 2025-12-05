import re

def extract_courses_from_user_query(query:str):
    pattern = r'\b[A-Z]{2}\d{4}\b'
    return re.findall(pattern, query)


def extract_two_prof_names(text: str):

    pattern = r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:and|&)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        return [match.group(1), match.group(2)]

    return None


