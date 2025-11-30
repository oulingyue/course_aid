import json

import psycopg2
def validate_instructor(cursor, instructor_name):
    instructor_first = instructor_name.split(" ")[0]
    instructor_last = instructor_name.split(" ")[-1]

    check_query = '''
                  select first_name, last_name \
                  from instructors; \
                  '''
    cursor.execute(check_query)
    valid_instructors = cursor.fetchall()
    for valid_instructor in valid_instructors:
        if (instructor_first.lower() == valid_instructor[0].lower() and
            instructor_last.lower() == valid_instructor[1].lower()):
            return valid_instructor[0], valid_instructor[1]

    return None

def get_average_rating(cursor, instructor_name):
    instructor_first, instructor_last = validate_instructor(cursor, instructor_name)

    avg_query = '''
    select round(avg(rating),2) from review where instructor_first=%s and instructor_last=%s
    '''
    try:
        cursor.execute(avg_query, (instructor_first, instructor_last))

        avg_rating = cursor.fetchall()[0][0]
        if avg_rating:
            return avg_rating
        return None
    except psycopg2.ProgrammingError as e:
        raise Exception(f"{e}")


def get_courses_of_instructor(cursor, instructor_name):
    instructor_first, instructor_last = validate_instructor(cursor, instructor_name)

    courses_of_instructor_query = '''
    select course_number from course_section where instructor_first=%s and instructor_last=%s
    '''

    try:
        cursor.execute(courses_of_instructor_query, (instructor_first, instructor_last))
        rows = cursor.fetchall()
        courses_of_instructor = [row[0] for row in rows]
        return courses_of_instructor
    except psycopg2.ProgrammingError as e:
        raise Exception(f"{e}")

def get_departments_of_instructor(cursor, instructor_name):

    instructor_first, instructor_last = validate_instructor(cursor, instructor_name)

    departments_of_instructor_query = '''
    select department_name from instructor_to_department where instructor_first=%s and instructor_last=%s
    
    '''

    try:
        cursor.execute(departments_of_instructor_query, (instructor_first, instructor_last))
        rows= cursor.fetchall()
        departments_of_instructor = [row[0] for row in rows]
        return departments_of_instructor
    except psycopg2.ProgrammingError as e:
        raise Exception(f"{e}")

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
                             WHERE review_id = r.review_id AND vote_type = 1)                                   as upvotes, \
                            (SELECT COUNT(vote_id) \
                             FROM votes \
                             WHERE review_id = r.review_id \
                               AND vote_type = -1)                                                              as downvotes, \
                            (SELECT vote_type \
                             FROM votes \
                             WHERE review_id = r.review_id AND username = %s)                                    as user_vote
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
                             WHERE review_id = r.review_id AND vote_type = 1)                                   as upvotes, \
                            (SELECT COUNT(vote_id) \
                             FROM votes \
                             WHERE review_id = r.review_id \
                               AND vote_type = -1)                                                              as downvotes, \
                            NULL                                                                                as user_vote
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


def get_all_comments_for_instructor(cursor, instructor_first, instructor_last):
    all_reviews = '''
                  select comment \
                  from review \
                  where instructor_first = %s \
                    and instructor_last = %s \

                  '''

    try:
        cursor.execute(all_reviews, [instructor_first, instructor_last])
        comments = cursor.fetchall()
        if len(comments) == 0:
            return None

        else:
            return comments

    except psycopg2.Error as e:
        raise Exception(f"Error fetching reviews: {e}")



def get_summary(instructor_first, instructor_last):

    with open("summary_cache.json", "r") as file:
        summary_cache = json.load(file)

    for data in summary_cache["data"]:
        if data["first"] == instructor_first and data["last"] == instructor_last:
            return data["summary"]








