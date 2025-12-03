import os

from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from course_aid.app.middleware.auth import auth
import psycopg2
from functools import wraps
import helper
from course_aid.app.config import db_connection
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

app.register_blueprint(auth)

CORS(app)



def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Login required'}), 401
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
def index():
    return render_template('base.html')


@app.get("instructor/<instructor_name>/reviews")
@login_required
def get_reviews(instructor_name):
    '''
    Endpoint for getting reviews for a given instructor
    :param instructor_name:
    :return: a list of reviews with user's vote status
    '''
    conn = db_connection.connect()
    cursor = conn.cursor()

    message = ""
    instructor_first = ""
    instructor_last = ""

    if (helper.validate_instructor(cursor, instructor_name)):
        instructor_first, instructor_last = helper.validate_instructor(cursor, instructor_name)

    else:
        message += "Instructor does not exist"
        cursor.close()
        conn.close()
        return render_template("reviews.html", reviews=[], message=message)

    try:
        consensus_summary = helper.get_summary(instructor_first, instructor_last)
        departments = helper.get_departments_of_instructor(cursor, instructor_name)
        courses = helper.get_courses_of_instructor(cursor, instructor_name)
        avg_rating = helper.get_average_rating(cursor, instructor_name)

        if not departments:
            departments = []
        if not courses:
            courses = []
        if not avg_rating:
            avg_rating = 'NA'

        username = session.get("user_id")

        instructor_info = {
            'first_name': instructor_first,
            'last_name': instructor_last,
            'courses': courses,
            'departments': departments,
            'avg_rating': avg_rating,
            'consensus_summary': consensus_summary
        }
        result = helper.get_reviews_for_instructor(cursor, instructor_first, instructor_last, username)

        if not result:
            message += "No reviews found for this instructor"

    except Exception as e:
        message = f"Error getting reviews for {instructor_name}: {e}"
        result = []
        instructor_info = {
            'first_name': instructor_first,
            'last_name': instructor_last,
            'courses': [],
            'departments': [],
            'avg_rating': 'N/A',
            'consensus_summary': "N/A"
        }

    finally:
        cursor.close()
        conn.close()

    return render_template("reviews.html",
                           reviews=result,
                           message=message,
                           instructor_name=f"{instructor_first} {instructor_last}",
                           instructor_info=instructor_info,)


@app.route("/reviews/<int:review_id>/vote", methods=["POST"])
@login_required
def handle_votes(review_id):
    '''
    Endpoint for creating/updating/deleting a vote on a review
    :param review_id: review id
    :return: JSON response with success status and updated counts
    '''
    conn = db_connection.connect()
    cursor = conn.cursor()

    try:
        data = request.get_json()
        vote_type_str = data.get('vote_type')


        vote_type = 1 if vote_type_str == 'upvote' else -1

        username = session.get("user_id")


        check_query = '''
            SELECT vote_id, vote_type 
            FROM votes
            WHERE review_id = %s 
              AND username = %s
        '''
        cursor.execute(check_query, [review_id, username])
        existing_vote = cursor.fetchone()

        action = ""

        if existing_vote:
            existing_vote_id = existing_vote[0]
            existing_vote_type = existing_vote[1]


            if existing_vote_type == vote_type:
                delete_query = '''
                    DELETE FROM votes 
                    WHERE vote_id = %s
                '''
                cursor.execute(delete_query, [existing_vote_id])
                action += 'removed'
            else:

                update_query = '''
                    UPDATE votes 
                    SET vote_type = %s
                    WHERE vote_id = %s
                '''
                cursor.execute(update_query, [vote_type, existing_vote_id])
                action += 'changed'
        else:

            cursor.execute('''
                           SELECT setval(pg_get_serial_sequence('votes', 'vote_id'),
                                         COALESCE((SELECT MAX(vote_id) FROM votes), 0) + 1,
                                         false)
                           ''')

            insert_query = '''
                INSERT INTO votes (review_id, username, vote_type)
                VALUES (%s, %s, %s)
            '''
            cursor.execute(insert_query, [review_id, username, vote_type])
            action += 'added'

        conn.commit()

        count_query = '''
            SELECT 
                (SELECT COUNT(*) FROM votes WHERE review_id = %s AND vote_type = 1) as upvotes,
                (SELECT COUNT(*) FROM votes WHERE review_id = %s AND vote_type = -1) as downvotes
        '''
        cursor.execute(count_query, [review_id, review_id])
        counts = cursor.fetchone()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'action': action,
            'upvotes': counts[0] if counts[0] else 0,
            'downvotes': counts[1] if counts[1] else 0,
            'message': f'Vote {action} successfully'
        })

    except psycopg2.Error as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({
            'success': False,
            'message': f'Database error: {str(e)}'
        }), 500

    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route("/user_reviews")
@login_required
def get_user_reviews():

    '''
    Endpoint for getting past reviews for a given username
    :param username: usernamne of user
    :return: a list of reviews
    '''

    conn = db_connection.connect()
    cursor = conn.cursor()

    message = ""
    username = session.get("user_id")

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

    try:


        result = []

        cursor.execute(query,(username,))

        rows = cursor.fetchall()

        for row in rows:
            result.append({
                'review_id': row[0],
                'comment': row[1],
                'rating': row[2],
                'post_time': row[3],
                'last_updated': row[4],
                'course_number': row[5],
                'instructor_first': row[6],
                'instructor_last': row[7],
            })

    except psycopg2.Error as e:
        message = f"Error getting reviews for {username}: {e}"

    finally:

        cursor.close()

    return render_template("pastreviews.html", reviews=result,
                           message = message, message_type="info")

@app.route("/user_reviews/<int:review_id>/edit", methods=["PATCH", "PUT"])
@login_required
def edit_reviews(review_id):
    '''
      Endpoint for editing a past review for a given review_id
      :param username: usernamne of user
      :return: a list of reviews
    '''

    conn = db_connection.connect()
    cursor = conn.cursor()
    message = ""

    try:

        check_query = '''
        select review from review where review_id = %s and username = %s
        '''
        cursor.execute(check_query, [review_id, session.get("user_id")])

        if cursor.fetchone() is None:
            cursor.close()
            conn.close()
            message += "No review found for this username"
            return jsonify({
                'success': False,
                'message': message
            })


        data = request.get_json()
        new_comment = data.get('comment')
        new_rating = data.get('rating')

        update_query = '''
        update review set comment = %s,
            rating = %s,
            last_updated = CURRENT_TIMESTAMP
            where review_id = %s and username = %s
        '''

        cursor.execute(update_query, (new_comment, new_rating, review_id, session.get("user_id")))
        conn.commit()

        cursor.close()
        conn.close()

        message = f"Review {review_id} successfully updated"

        return jsonify({
            'success': True,
            'message': message
        })


    except psycopg2.Error as e:
        message += f"Error getting reviews for {review_id}: {e}"
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({
            'success': False,
            'message': message
        })

    except Exception as e:
        message = f"Error getting reviews for {review_id}: {e}"
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({
            'success':False,
            'message': message
        })





@app.route("/user_reviews/<int:review_id>/delete", methods=["DELETE"])
@login_required
def delete_reviews(review_id):
    '''
         Endpoint for editing a past review for a given review_id
         :param username: usernamne of user
         :return: a list of reviews
    '''


    conn = db_connection.connect()
    cursor = conn.cursor()
    message = ""

    try:
        check_query = '''
        select comment from review where review_id = %s and username = %s
        '''
        cursor.execute(check_query, [review_id, session.get("user_id")])

        if cursor.fetchone() is None:
            cursor.close()
            conn.close()
            message += "No review found for this username"
            return jsonify({
                'success': False,
                'message': message
            })

        delete_query = '''
        delete from review where review_id = %s and username = %s'''

        cursor.execute(delete_query, [review_id, session.get("user_id")])
        conn.commit()

        cursor.close()
        conn.close()

        message = f"Review {review_id} successfully deleted"
        return jsonify({
            'success': True,
            'message': message
        })

    except psycopg2.Error as e:
        message = f"Database error: {review_id}: {e}"
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({
            'success': False,
            'message': message
        }), 500

    except Exception as e:
        message = f"Error getting reviews for {review_id}: {e}"
        conn.rollback()
        cursor.close()
        conn.close()

        return jsonify({
            'success': False,
            'message': message
        }), 500



@app.route("/assistant", methods=["GET","POST"])
@login_required
def assistant():
    return render_template("assistant.html")


if __name__ == '__main__':
    app.run(debug=True)







