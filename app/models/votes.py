class Votes:
    @staticmethod
    def create_vote(cursor, review_id, username, vote_type):
        insert_query = '''
                       INSERT INTO votes (review_id, username, vote_type)
                       VALUES (%s, %s, %s) \
                       '''
        cursor.execute(insert_query, [review_id, username, vote_type])

    @staticmethod
    def count_votes(cursor, review_id):
        count_query = '''
                      SELECT (SELECT COUNT(*) FROM votes WHERE review_id = %s AND vote_type = 1)  as upvotes, \
                             (SELECT COUNT(*) FROM votes WHERE review_id = %s AND vote_type = -1) as downvotes \
                      '''
        cursor.execute(count_query, [review_id, review_id])
        return cursor.fetchone()

    @staticmethod
    def update_vote_id(cursor):
        cursor.execute('''
                       SELECT setval(pg_get_serial_sequence('votes', 'vote_id'),
                                     COALESCE((SELECT MAX(vote_id) FROM votes), 0) + 1,
                                     false)
                       ''')

    @staticmethod
    def check_vote(cursor, username, review_id):
        check_query = '''
                      SELECT vote_id, vote_type
                      FROM votes
                      WHERE review_id = %s
                        AND username = %s \
                      '''
        cursor.execute(check_query, [review_id, username])
        return cursor.fetchone()


    @staticmethod
    def edit_vote(cursor, existing_vote_id, vote_type):
        update_query = '''
                       UPDATE votes
                       SET vote_type = %s
                       WHERE vote_id = %s \
                       '''
        cursor.execute(update_query, [vote_type, existing_vote_id])


    @staticmethod
    def delete_vote(cursor, existing_vote_id):
        delete_query = '''
                       DELETE \
                       FROM votes
                       WHERE vote_id = %s \
                       '''
        cursor.execute(delete_query, [existing_vote_id])
