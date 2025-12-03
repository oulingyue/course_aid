import json
import os

from course_aid.app.config import db_connection

from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from pgvector.psycopg2 import register_vector


class populateDB:
    def __init__(self):
        with open("../data_json/rtu_main_entities.json", "r") as file:
            self.data = json.load(file)

        with open("../data_json/rtu_relationships.json", "r") as file:
            self.relationships = json.load(file)


        self.reviews = "../data_json/reviews/"
        self.votes = "../data_json/votes/"
        self.gemma_model = SentenceTransformer("google/embeddinggemma-300m")


    def populateCoursesTable(self, cursor):

        try:
            for record in tqdm(self.data["courses"], desc="Inserting courses"):
                course_number = record["course_number"]
                course_description = record["course_description"]

                cursor.execute(
                    '''INSERT INTO public.courses (course_number, course_description)
                       VALUES (%s, %s)''',

                    (course_number, course_description)
                )

            print("Successfully populated course table")

        except Exception as e:
            print("Failed to populate course table")
            print(e)


    def populateDepartmentsTable(self, cursor):

        try:
            for record in tqdm(self.data["departments"], desc="Inserting department names"):
                dept_name = record["department_name"]


                cursor.execute(
                    '''INSERT INTO public.departments (department_name)
                       VALUES (%s)''',

                    (dept_name,)
                )

            print("Successfully populated departments table")

        except Exception as e:
            print("Failed to populate departments table")
            print(e)

    def populateInstructorsTable(self, cursor):

        try:
            for record in tqdm(self.data["instructors"], desc="Inserting department names"):
                f_name = record["first_name"]
                l_name = record["last_name"]


                cursor.execute(
                    '''INSERT INTO public.instructors (first_name, last_name)
                       VALUES (%s, %s)''',

                    (f_name, l_name)
                )

            print("Successfully populated instructors table")

        except Exception as e:
            print("Failed to populate instructors table")
            print(e)

    def populateUsersTable(self, cursor):

        try:
            for record in tqdm(self.data["users"], desc="Inserting users"):
                username = record["username"]
                password = record["password"]
                school_year = record["school_year"]

                cursor.execute(
                    '''INSERT INTO public.users (username, password, school_year)
                       VALUES (%s, %s, %s)''',

                    (username, password, school_year)
                )

            print("Successfully populated users table")

        except Exception as e:
            print("Failed to populate users table")
            print(e)

    def populateReviewsTable(self, cursor):

        try:

            files = os.listdir(self.reviews)

            for file in tqdm(files, desc="Processing files"):
                with open(os.path.join(self.reviews, file), "r") as f:
                    review_data = json.load(f)

                batch_key = list(review_data.keys())[0]

                for record in review_data[batch_key]:

                    instructor_first = record["instructor_name"].split(" ")[0]
                    instructor_last = record["instructor_name"].split(" ")[1]


                    cursor.execute(
                        '''INSERT INTO public.review(comment, instructor_first, instructor_last, username, 
                                                           rating, post_time, last_updated, course_number)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',

                        (record["comment"], instructor_first, instructor_last,
                         record["username"], record["rating"], record["post_time"],
                         record["last_updated_time"], record["course_number"])
                    )

            print("Successfully populated review table")

        except Exception as e:

            print("Failed to populate review table")
            print(e)

    def populateCourseEmbeddingsTable(self, cursor):


        try:
            register_vector(cursor.connection)

            cursor.execute("SELECT course_number, course_description from courses")
            documents = cursor.fetchall()
            for record in tqdm(documents, desc="Populating course embeddings"):
                course_number = record[0]
                embeddings = self.gemma_model.encode_document(record[1])


                cursor.execute("INSERT INTO course_embeddings (course_id, embedding) VALUES (%s, %s)",
                               (course_number, embeddings)
                               )

        except Exception as e:
            print("Failed to populate course embeddings table: "+e)

    def populateReviewEmbeddingsTable(self, cursor):


        try:
            register_vector(cursor.connection)

            cursor.execute("SELECT review_id, comment from review")
            documents = cursor.fetchall()
            for record in tqdm(documents, desc="Populating review embeddings"):
                review_id = record[0]

                cursor.execute("INSERT INTO review_embeddings (review_id, embedding) VALUES (%s, %s)",
                               (review_id, self.gemma_model.encode_document(record[1])
                               ))

        except Exception as e:
            print("Failed to populate review embeddings table: "+str(e))

    def populateVotesTable(self, cursor):

        try:

            files = [f for f in os.listdir(self.votes) if f.endswith(".json")]

            for file in tqdm(files, desc="Processing files"):
                with open(os.path.join(self.votes, file), "r") as f:
                    votes_data = json.load(f)

                batch_key = list(votes_data.keys())[0]

                for record in votes_data[batch_key]:


                    cursor.execute(
                        '''INSERT INTO public.votes(vote_id, review_id, username, vote_type)
                           VALUES (%s, %s, %s, %s)''',

                        (record["vote_id"],record["review_id"],record["username"],record["vote_type"])
                    )

            print("Successfully populated votes table")

        except Exception as e:

            print("Failed to populate votes table")
            print(e)


    def populateCourseSectionTable(self, cursor):


        try:
            for record in tqdm(self.relationships["course_sections"], desc="Inserting course sections "):


                cursor.execute(
                    '''INSERT INTO public.course_section (course_number, instructor_last, instructor_first)
                       VALUES (%s, %s, %s)''',

                    (record["course_number"], record["instructor_last"],record["instructor_first"])
                )

            print("Successfully populated course_section table")

        except Exception as e:
            print("Failed to populate course_section table")
            print(e)


    def populateCourseToDepartmentTable(self, cursor):


        try:
            for record in tqdm(self.relationships["course_to_department"], desc="Inserting course to department names "):


                cursor.execute(
                    '''INSERT INTO public.course_to_department (course_number, department_name)
                       VALUES (%s, %s)''',

                    (record["course_number"], record["department_name"])
                )

            print("Successfully populated course_to_department table")

        except Exception as e:
            print("Failed to populate course_to_department table")
            print(e)

    def populateInstructorToDepartmentTable(self, cursor):


        try:
            for record in tqdm(self.relationships["instructor_to_department"], desc="Inserting instructor to department records "):


                cursor.execute(
                    '''INSERT INTO public.instructor_to_department (instructor_first, instructor_last, department_name)
                       VALUES (%s, %s, %s)''',

                    (record["instructor_first"], record["instructor_last"], record["department_name"])
                )

            print("Successfully populated instructor_to_department table")

        except Exception as e:
            print("Failed to populate instructor_to_department table")
            print(e)


    def populateUserToCourseTable(self, cursor):


        try:
            for record in tqdm(self.relationships["user_to_course"], desc="Inserting user to course records "):


                cursor.execute(
                    '''INSERT INTO public.user_to_course (username, course_number)
                       VALUES (%s, %s)''',

                    (record["username"], record["course_number"])
                )

            print("Successfully populated instructor_to_department table")

        except Exception as e:
            print("Failed to populate instructor_to_department table")
            print(e)




if __name__ == "__main__":
    cursor, connection = db_connection.connect()

    # change the name of the table you want to populate
    populateDB().populateVotesTable(cursor)
    connection.commit()

    cursor.close()
    connection.close()
    print("connection closed!")





