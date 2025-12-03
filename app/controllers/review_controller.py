import os
import psycopg2
from dotenv.main import rewrite
from flask import Flask, request, jsonify, render_template, session
from course_aid.app.utils import helper
from course_aid.app.models.intructors import Instructor
from course_aid.app.models.reviews import Reviews

def get_user_reviews(conn):
        cursor = conn.cursor()

        message = ""
        username = session.get("user_id")

        try:
            result = []

            rows = Reviews.get_user_past_reviews(cursor, username)

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

        return render_template("view/templates/pastreviews.html", reviews=result,
                               message = message, message_type="info")


def get_reviews_for_instructor(conn, instructor_name):

    '''
        Endpoint for getting reviews for a given instructor
        :param instructor_name:
        :return: a list of reviews with user's vote status
        '''
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
        return render_template("view/templates/reviews.html", reviews=[], message=message)

    try:
        consensus_summary = helper.get_consensus_summary(instructor_first, instructor_last)
        departments = Instructor.get_departments_of_instructor(cursor, instructor_name)
        courses = Instructor.get_courses_of_instructor(cursor, instructor_name)
        avg_rating = Instructor.get_average_rating(cursor, instructor_name)

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
        result = Reviews.get_reviews_for_instructor(cursor, instructor_first, instructor_last, username)

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

    return render_template("view/templates/reviews.html",
                           reviews=result,
                           message=message,
                           instructor_name=f"{instructor_first} {instructor_last}",
                           instructor_info=instructor_info, )



def edit_review(review_id, conn):
    '''
      Endpoint for editing a past review for a given review_id
      :param username: usernamne of user
      :return: a list of reviews
    '''

    cursor = conn.cursor()
    message = ""

    try:


        if Reviews.check_review_exists(conn, session.get("user_id"), review_id) is None:
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

        Reviews.edit_review(cursor,new_comment, new_rating, session.get("user_id"), review_id)
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

def delete_review(review_id, conn):
    '''
         Endpoint for editing a past review for a given review_id
         :param username: usernamne of user
         :return: a list of reviews
    '''

    cursor = conn.cursor()
    message = ""

    try:

        if Reviews.check_review_exists(cursor, session.get("user_id"), review_id) is None:
            cursor.close()
            conn.close()
            message += "No review found for this username"
            return jsonify({
                'success': False,
                'message': message
            })

        Reviews.delete_review(cursor, session.get("user_id"), review_id)
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



