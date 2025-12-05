import psycopg2
import os
from tqdm import tqdm
from google import genai
from google.genai import types
from app.models.intructors import Instructor
from app.config.db_connection import connect
from app.utils.helper import validate_instructor
from app.utils.query_parser import extract_courses_from_user_query, extract_two_prof_names
from sentence_transformers import SentenceTransformer
from app.models.context_pydantic import CourseContext, CourseRecommendationContext, ProfessorComparisonContext, ReviewContext, MiscellaneousInfoContext
from dotenv import load_dotenv


class AssistantRoles:

    def __init__(self):
        load_dotenv()
        self.conn = connect()
        self.model='gemini-2.5-flash'
        self.system_prompt="""
        You are a helpful assistant for a website that allows students to review and rate their professors.
        You will act as an academic advisor who answer questions about professors and courses mainly based on 
        students' review of the professor and course description
                            
                             FORMATTING RULES: 
            - Write in plain text only, no markdown formatting 
            - Do NOT use asterisks (*), bold (**), italics, or any special formatting characters 
            - Do NOT use headers (###) or bullet points with asterisks 
            - Write naturally in complete sentences and paragraphs 
            - Use line breaks for clarity, but no special symbols
                            
                               IMPORTANT INSTRUCTIONS:
            - If no courses are found acknowledge this clearly and only analyze the courses that are found
            - Do NOT make up information or analyze non-existent courses or reviews
            - If a professor has "No reviews available", acknowledge this clearly and only analyze the professor who HAS reviews
            - If professors lack reviews, state this clearly
            - Focus only on actual student feedback provided                                         
                            """
        self.embedding_model = SentenceTransformer("google/embeddinggemma-300m")
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def get_database_results_for_relevant_reviews(self, cursor, user_query:str):
        query_embedding = self.embedding_model.encode_query(user_query)
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                           SELECT r.instructor_first, r.instructor_last, r.course_number, r.comment
                           FROM review_embeddings e
                                    JOIN review r ON e.review_id = r.review_id
                           ORDER BY e.embedding <=> %s::vector
                            LIMIT 10
                           """, ((query_embedding.tolist(),)))

            return cursor.fetchall()
        except psycopg2.ProgrammingError as e:
            print(f"Error: {e}")
            return None


    def get_database_results_for_curriculum(self, cursor, user_query:str):

        query_embedding = self.embedding_model.encode_query(user_query)


        query = '''
                select c.course_number, c.course_description
                    from course_embeddings as ce
                    join courses as c on ce.course_id = c.course_number
                    order by ce.embedding <=> %s::vector
                    LIMIT 10
                '''
        try:
            cursor.execute(query, (query_embedding.tolist(),))
            courses = cursor.fetchall()
            return courses
        except psycopg2.ProgrammingError as e:
            print(f"Error: {e}")
            return None

    def get_database_results_for_profcomparison(self, cursor, prof1_fname:str, prof2_fname:str, prof1_lname:str, prof2_lname:str):


        try:
            cursor.execute("""
                           SELECT r.instructor_first,
                                  r.instructor_last,
                                  r.course_number,
                                  r.comment
                           FROM review r
                           WHERE r.instructor_first = %s
                             AND r.instructor_last = %s
                           ORDER BY r.last_updated DESC limit 20
                           """, (prof1_fname, prof1_lname))

            prof1_review_rows = cursor.fetchall()

            cursor.execute("""
                           SELECT r.instructor_first,
                                  r.instructor_last,
                                  r.course_number,
                                  r.comment
                           FROM review r
                           WHERE r.instructor_first = %s
                             AND r.instructor_last = %s
                           ORDER BY r.last_updated DESC limit 20
                           """, (prof2_fname, prof2_lname))

            prof2_review_rows = cursor.fetchall()

            return prof1_review_rows, prof2_review_rows
        except psycopg2.ProgrammingError as e:
            cursor.close()
            print(f"error: {e}")
            return None, None


    async def chat(self, messages: list[str]):


        response = self.client.models.generate_content(
            model=self.model,
            contents=messages,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0) ,
                temperature=0.1,
                system_instruction=self.system_prompt

            )
        )

        return response.text

    def create_summary_prompt(self, contents: list[str]):
        messages = []

        messages.append("""Generate only a one or two line summary of the following reviews on a professor.
                                                   The intent behind this summary is for the viewer (student) to understand how 
                                                    professionally good/bad this professor is. Do not add any delimiters""")
        for content in contents[0]:
            messages.append(content)

        return messages

    async def generate_consensus_summary(self, instructor_first: str, instructor_last: str):

        comments = Instructor.get_all_comments_for_instructor(self.conn.cursor(), instructor_first, instructor_last)

        if not comments:
            return "No reviews yet"

        else:
            messages = self.create_summary_prompt(comments)

            result = await self.chat(messages)
            return result

    async def process_all_instructors(self,rows):
        results = []
        for row in tqdm(rows, total=len(rows)):
            result = await self.generate_consensus_summary(row[0], row[1])
            results.append({"first": row[0], "last": row[1], "summary": result})
        return results

    async def recommend_curriculum(self, cursor, user_query: str):

        database_results = self.get_database_results_for_curriculum(cursor, user_query)
        formatted_context = ""
        if not database_results:
            formatted_context += "No courses found related your field"
        else:
            course_contexts = [
                CourseContext(
                course_code=row[0],
                course_desc=row[1]
                )
                for row in database_results]


            context = CourseRecommendationContext(
                user_preferences=user_query,
                matching_courses=course_contexts,
            )

            formatted_context += context.format_for_llm()

        messages = [f"""
            Based on the user's preferred field or fields of study, explain how these the relevant courses
                are advisable for the student to take:
            {formatted_context}
            Base recommendations on course descriptions.
            For each course, explain why it matches their preferences and also future career outcomes
        
            
            """]


        return await self.chat(messages)

    async def QnA(self, cursor, user_query: str):

        relevant_reviews_rows = self.get_database_results_for_relevant_reviews(cursor, user_query)

        relevant_courses_rows = self.get_database_results_for_curriculum(cursor, user_query)

        if not relevant_reviews_rows:
            message = "no reviews yet"
            review_context = [ReviewContext(
                professor_fname=message,
                professor_lname=message,
                course_code=message,
                comment=message,
            )]
        else:
            review_context = [ReviewContext(
                professor_fname=row[0],
                professor_lname=row[1],
                course_code=row[2],
                comment=row[3]
            ) for row in relevant_reviews_rows]


        if not relevant_courses_rows:
            course_context = [CourseContext(
                course_code="no courses found",
                course_desc="no courses found"
            )]

        else:
            course_context = [CourseContext(
                course_code=row[0],
                course_desc=row[1]
            ) for row in relevant_courses_rows]


        context = MiscellaneousInfoContext(
            question=user_query,
            relevant_reviews=review_context,
            relevant_courses=course_context
        )

        formatted_context = context.format_for_llm()

        messages = [
         f"""
            
            You are answering specific questions about professors and courses based on student reviews of professors and courses.
            {formatted_context}
            
             IMPORTANT INSTRUCTIONS:
            - If a reviews or courses are not available, acknowledge this clearly and only analyze the professor who HAS reviews
            - Do NOT make up information or analyze non-existent reviews and course descriptions
            
                
            FORMATTING RULES: 
            - Write in plain text only, no markdown formatting 
            - Do NOT use asterisks (*), bold (**), italics, or any special formatting characters 
            - Do NOT use headers (###) or bullet points with asterisks 
            - Write naturally in complete sentences and paragraphs 
            - Use line breaks for clarity, but no special symbols
            
            Provide relevant answers and and stick to the context provided.

            """
        ]

        return await self.chat(messages)


    async def compare_two_professors(self, cursor, user_query: str):

        prof_names = extract_two_prof_names(user_query)

        prof1_fname, prof1_lname = validate_instructor(cursor, prof_names[0])
        prof2_fname, prof2_lname = validate_instructor(cursor, prof_names[1])


        print(prof1_fname, prof1_lname)

        print(prof2_fname, prof2_lname)

        prof1_review_rows, prof2_review_rows = self.get_database_results_for_profcomparison(cursor, prof1_fname, prof1_lname, prof2_fname, prof2_lname)
        if not prof1_review_rows:
            prof1_reviews = [
                ReviewContext(
                    professor_fname=prof1_fname,
                    professor_lname=prof1_lname,
                    course_code="N/A",
                    comment=f"No reviews for this professor or invalid professor {prof1_fname} {prof1_lname}"
                )
            ]
        else:
            prof1_reviews = [
                ReviewContext(
                    professor_fname=row[0],
                    professor_lname=row[1],
                    course_code=row[2],
                    comment=row[3]
                )
                for row in prof1_review_rows
            ]

        if not prof2_review_rows:

            prof2_reviews = [
                ReviewContext(
                    professor_fname=prof2_fname,
                    professor_lname=prof2_lname,
                    course_code="N/A",
                    comment=f"No reviews for this professor or invalid professor {prof2_fname} {prof2_lname}"
                )
            ]
        else:
            prof2_reviews = [
                ReviewContext(
                    professor_fname=row[0],
                    professor_lname=row[1],
                    course_code=row[2],
                    comment=row[3]
                )
                for row in prof2_review_rows
            ]
        context = ProfessorComparisonContext(
            professor1_fname=prof1_fname,
            professor2_fname=prof2_fname,
            professor1_lname=prof1_lname,
            professor2_lname=prof2_lname,
            professor1_reviews=prof1_reviews,
            professor2_reviews=prof2_reviews
        )

        formatted_context = context.format_for_llm()

        messages = [
        f"""
            Compare the following two professors based on student reviews:

            {formatted_context}    
            
            Analyze their:
            1. Teaching effectiveness
            2. Grading fairness
            3. Course difficulty
            4. Student support
            
            Which professor would you recommend for beginners vs advanced students?
            
            
            """
        ]

        return await self.chat(messages)



# example usage
if __name__ == '__main__':
    deepseek = AssistantRoles()
    # query = '''
    #         select first_name, last_name \
    #         from instructors \
    #         '''
    #
    # cursor = deepseek.conn.cursor()
    # cursor.execute(query)
    # rows = cursor.fetchall()
    #
    # with open('summary_cache.json', 'r') as outfile:
    #     data = json.load(outfile)
    #
    #
    # new_summaries = asyncio.run(deepseek.process_all_instructors(rows))
    # data["data"].extend(new_summaries)
    #
    # with open('summary_cache.json', 'w') as outfile:
    #     json.dump(data, outfile, indent=2)


