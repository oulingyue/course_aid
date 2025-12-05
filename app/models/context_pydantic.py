from pydantic import BaseModel, Field
from typing import Optional, List


class CourseContext(BaseModel):
    course_code: str
    course_desc: str

    def format(self):
        return f"course code: {self.course_code} - course description: {self.course_desc}"



class ReviewContext(BaseModel):
    professor_fname: str
    professor_lname: str
    course_code: str
    comment: str

    def format(self) -> str:
        return f"{self.professor_fname} {self.professor_lname} - {self.course_code}: {self.comment}"



class ProfessorComparisonContext(BaseModel):

    professor1_fname: str
    professor1_lname: str
    professor1_reviews: List[ReviewContext] = Field(max_items=20)
    professor2_fname: str
    professor2_lname: str
    professor2_reviews: List[ReviewContext] = Field(max_items=20)

    def format_for_llm(self) -> str:

        context = f"PROFESSOR 1: {self.professor1_fname} {self.professor1_lname}\n"
        context += "Reviews:\n"
        for review in self.professor1_reviews:
            context += f"  - {review.format()}\n"

        context += f"\nPROFESSOR 2: {self.professor2_fname} {self.professor2_lname}\n"
        context += "Reviews:\n"
        for review in self.professor2_reviews:
            context += f"  - {review.format()}\n"

        return context


class CourseRecommendationContext(BaseModel):

    user_preferences: str
    matching_courses: List[CourseContext]

    def format_for_llm(self) -> str:
        context = f"User is looking to study: {self.user_preferences}\n\n"
        context += "Relevant Courses:\n"
        for course in self.matching_courses:
            context += f"\n{course.format()}:\n"

        return context


class MiscellaneousInfoContext(BaseModel):
    question: str
    relevant_courses: List[CourseContext]
    relevant_reviews: List[ReviewContext]

    def format_for_llm(self) -> str:
        context = (f"User question: {self.question}\n:")
        context += "Relevant Courses:\n"
        for course in self.relevant_courses:
            context += f"\n{course.format()}:\n"
        context += "Reviews:\n"
        for review in self.relevant_reviews:
            context += f"{review.format()}\n"

        return context






