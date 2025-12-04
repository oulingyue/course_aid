import psycopg2
from datetime import datetime
from app.utils.helper import execute_qry
from sentence_transformers import SentenceTransformer
from torch.distributed._shard.sharding_spec.chunk_sharding_spec_ops import embedding

#---- review class ----#
class Review:
    def __init__(self, comment: str, instructor_first: str, instructor_last: str, course_num:str, username= str, rating = int, id= None):
        self.comment = comment
        self.instructor_first = instructor_first
        self.instructor_last = instructor_last
        self.course_num = course_num
        self.username = username
        self.rating = rating
        self.post_time = datetime.now().isoformat()
        self.last_updated = datetime.now().isoformat()
        self.id = id
        self.gemma_model = SentenceTransformer("google/embeddinggemma-300m")
        self.embedding = self.gemma_model.encode_document(comment)
    
    def to_dict(self):
        """
        Convert the task to a dictionary representation for json formatting.
        """
        return {
            'review_id': self.id,
            'instructor_first': self.instructor_first,
            'instructor_last': self.instructor_last,
            'course_num': self.course_num,
            'username': self.username,
            'rating': self.rating,
            'comment': self.comment,
            'post_time': self.post_time,
            'last_updated': self.last_updated
        }

def save_review(review:Review):
    """Save a review to the database"""
    sql_cmd = f'INSERT INTO review (comment, rating, post_time, last_updated, course_number, instructor_first, instructor_last, username) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
    execute_qry(sql_cmd, (review.comment, review.rating, review.post_time, review.last_updated, review.course_num, review.instructor_first, review.instructor_last, review.username))
    print('insert success.')

def save_review_embedding(review_id : int, embedding):
    q = "INSERT INTO review_embeddings (review_id, embedding) VALUES (%s, %s)"
    execute_qry(q, (review_id, embedding.tolist()))
    print('embedding insertion success.')

def get_course_sections(instructor_first,instructor_last):
    cmd = f'SELECT course_number FROM course_section where (instructor_first = %s) and (instructor_last= %s);'
    results = execute_qry(cmd, (instructor_first, instructor_last))
    return [r[0] for r in results]  if results else None

def get_reviews():
    sql_cmd = f'select * from review;'
    results = execute_qry(sql_cmd, ())
    return results if results else None
    

class Reviews:

    def __init__(self):

       self.gemma_model = SentenceTransformer("google/embeddinggemma-300m")


    def insert_document_with_embedding(self, cursor, comment, rating, course_number, instructor_first, instructor_last,
                                       username):

        cursor.execute("""
                       INSERT INTO review (comment, rating, course_number, instructor_first, instructor_last, username)
                       VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                       """, (comment, rating, course_number, instructor_first, instructor_last, username))

        review_id = cursor.fetchone()[0]

        embedding = self.gemma_model.encode_document(comment)

        cursor.execute("""
                       INSERT INTO review_embeddings (review_id, embedding)
                       VALUES (%s, %s)
                       """, (review_id, embedding.tolist()))

        cursor.commit()



    @staticmethod
    def get_reviews_for_instructor(cursor, instructor_first, instructor_last, user_id):


        user_vote_check_query = '''
                                SELECT DISTINCT r.review_id
                                FROM review r
                                         INNER JOIN votes v ON r.review_id = v.review_id
                                WHERE r.instructor_first = %s
                                  AND r.instructor_last = %s
                                  AND v.username = %s \
                                '''

        try:
            cursor.execute(user_vote_check_query, [instructor_first, instructor_last, user_id])
            user_has_votes = cursor.fetchone() is not None
        except psycopg2.Error as e:
            raise Exception(f"Error checking user votes: {e}")

        if user_has_votes:

            main_query = '''
                         SELECT r.review_id, \
                                r.comment, \
                                r.rating, \
                                r.post_time, \
                                r.last_updated, \
                                r.course_number, \
                                (SELECT COUNT(vote_id) \
                                 FROM votes \
                                 WHERE review_id = r.review_id \
                                   AND vote_type = 1)  as upvotes, \
                                (SELECT COUNT(vote_id) \
                                 FROM votes \
                                 WHERE review_id = r.review_id \
                                   AND vote_type = -1) as downvotes, \
                                (SELECT vote_type \
                                 FROM votes \
                                 WHERE review_id = r.review_id \
                                   AND username = %s)  as user_vote
                         FROM review r
                         WHERE r.instructor_first = %s
                           AND r.instructor_last = %s
                         ORDER BY r.post_time DESC \
                         '''
            params = [user_id, instructor_first, instructor_last]
        else:

            main_query = '''
                         SELECT r.review_id, \
                                r.comment, \
                                r.rating, \
                                r.post_time, \
                                r.last_updated, \
                                r.course_number, \
                                (SELECT COUNT(vote_id) \
                                 FROM votes \
                                 WHERE review_id = r.review_id \
                                   AND vote_type = 1)  as upvotes, \
                                (SELECT COUNT(vote_id) \
                                 FROM votes \
                                 WHERE review_id = r.review_id \
                                   AND vote_type = -1) as downvotes, \
                                NULL                   as user_vote
                         FROM review r
                         WHERE r.instructor_first = %s
                           AND r.instructor_last = %s
                         ORDER BY r.post_time DESC \
                         '''
            params = [instructor_first, instructor_last]

        try:
            cursor.execute(main_query, params)
        except psycopg2.Error as e:
            raise Exception(f"Error fetching reviews: {e}")

        rows = cursor.fetchall()

        result = []
        for row in rows:

            user_vote = None
            if row[8] == 1:
                user_vote = 'upvote'
            elif row[8] == -1:
                user_vote = 'downvote'

            result.append({
                'review_id': row[0],
                'comment': row[1],
                'rating': row[2],
                'post_time': row[3],
                'last_updated': row[4],
                'course_number': row[5],
                'upvotes': row[6] if row[6] else 0,
                'downvotes': row[7] if row[7] else 0,
                'user_vote': user_vote
            })

        return result

    @staticmethod
    def get_user_past_reviews(cursor, username):
        query = '''
                select r.review_id, \
                       r.comment, \
                       r.rating, \
                       r.post_time, \
                       r.last_updated, \
                       r.course_number, \
                       r.instructor_first, \
                       r.instructor_last
                from review r \
                where r.username = %s \
                '''

        cursor.execute(query, (username,))
        return cursor.fetchall()

    @staticmethod
    def check_review_exists(cursor, username, review_id):
        check_query = '''
                      select review \
                      from review \
                      where review_id = %s \
                        and username = %s \
                      '''
        cursor.execute(check_query, [review_id, username])

        if cursor.fetchone() is None:
            return None
        else:
            return cursor.fetchone()

    @staticmethod
    def edit_review(cursor, new_comment, new_rating, username, review_id):
        update_query = '''
                       update review \
                       set comment      = %s, \
                           rating       = %s, \
                           last_updated = CURRENT_TIMESTAMP
                       where review_id = %s \
                         and username = %s \
                       '''

        cursor.execute(update_query, (new_comment, new_rating, review_id, username))

    @staticmethod
    def delete_review(cursor, username, review_id):
        delete_query = '''
                       delete \
                       from review \
                       where review_id = %s \
                         and username = %s'''

        cursor.execute(delete_query, [review_id, username])


