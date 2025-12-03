import psycopg2
from sentence_transformers import SentenceTransformer
from torch.distributed._shard.sharding_spec.chunk_sharding_spec_ops import embedding


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


