import re

def extract_courses_from_user_query(query:str):
    pattern = r'\b[A-Z]{2}\d{4}\b'
    return re.findall(pattern, query)

