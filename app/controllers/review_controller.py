
import psycopg2
from flask import request, jsonify, render_template, session, flash, redirect, url_for
from app.models.intructors import Instructor
import app.models.reviews as r
from app.models.reviews import Reviews
from app.utils.helper import validate_instructor, get_consensus_summary

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

        return render_template("pastreviews.html", reviews=result,
                               message = message, message_type="info")

def get_reviews_for_instructor(conn, instructor_name):

    '''
        Endpoint for getting reviews for a given instructor
        :param instructor_name:
        :return: a list of reviews with user's vote status
        '''
    cursor = conn.cursor()

    message = ""

    validate_instructor_results = validate_instructor(cursor, instructor_name)

    if (validate_instructor_results):
        instructor_first, instructor_last = validate_instructor_results

    else:
        message += "Instructor does not exist"
        cursor.close()

        return render_template("professor_reviews.html", reviews=[], message=message)

    try:
        print("getting summary...")
        consensus_summary = get_consensus_summary(instructor_first, instructor_last)
        print("got summary")

        print("getting departments")
        departments = Instructor.get_departments_of_instructor(cursor, instructor_name)
        print("got departments")

        print("getting courses")
        courses = Instructor.get_courses_of_instructor(cursor, instructor_name)
        print("got courses")

        print("getting avg rating")
        avg_rating = Instructor.get_average_rating(cursor, instructor_name)
        print("got avg rating")

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
        print("getting reviews")
        result = Reviews.get_reviews_for_instructor(cursor, instructor_first, instructor_last, username)
        print("got reviews")

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

    return render_template("professor_reviews.html",
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


        if Reviews.check_review_exists(cursor, session.get("user_id"), review_id) is None:
            cursor.close()

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


        message = f"Review {review_id} successfully updated"

        return jsonify({
            'success': True,
            'message': message
        })


    except psycopg2.Error as e:
        message += f"Error getting reviews for {review_id}: {e}"
        conn.rollback()
        cursor.close()

        return jsonify({
            'success': False,
            'message': message
        })

    except Exception as e:
        message = f"Error getting reviews for {review_id}: {e}"
        conn.rollback()
        cursor.close()

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

            message += "No review found for this username"
            return jsonify({
                'success': False,
                'message': message
            })

        Reviews.delete_review(cursor, session.get("user_id"), review_id)
        conn.commit()

        cursor.close()


        message = f"Review {review_id} successfully deleted"
        return jsonify({
            'success': True,
            'message': message
        })

    except psycopg2.Error as e:
        message = f"Database error: {review_id}: {e}"
        conn.rollback()
        cursor.close()

        return jsonify({
            'success': False,
            'message': message
        }), 500

    except Exception as e:
        message = f"Error getting reviews for {review_id}: {e}"
        conn.rollback()
        cursor.close()


        return jsonify({
            'success': False,
            'message': message
        }), 500

def review_form(instructor_first,instructor_last):
    """Display review form for a specific professor"""
    user_id = session.get("user_id")
    courses = r.get_course_sections(instructor_first, instructor_last)
    if not courses:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        json_data = request.get_json(silent=True) or {}

        course_number = request.form.get('course_number') or json_data.get('course_number')
        rating = request.form.get('rating') or json_data.get('rating')
        comment = request.form.get('comment') or json_data.get('comment')
        if not course_number or not rating or not comment:
            flash("Please add a comment before submitting your review.", "error")
            return redirect(url_for("review_form", instructor_first=instructor_first, instructor_last=instructor_last))
        
        
        # Save review
        new_review = r.Review(
                        comment=comment, 
                        instructor_first=instructor_first,
                        instructor_last=instructor_last, 
                        course_num=course_number,
                        rating = rating,
                        username = user_id)
        review = r.save_review(new_review)
        r.save_review_embedding(review.id,review.embedding)
        print(review)
        
        # Return JSON if requested, otherwise redirect
        if request.is_json:
            return jsonify(new_review.to_dict()), 201
        
        flash(f'Review for {instructor_first} {instructor_last} submitted successfully!', 'success')
        return redirect(url_for('index'))
    
    # GET request - display form
    return render_template('reviews/review_form.html', courses=courses, instructor_first=instructor_first, instructor_last=instructor_last)

def view_reviews():
    """Display all submitted reviews (optional - for testing)"""
    reviews = r.get_reviews()
    return render_template('reviews/reviews_list.html', reviews=reviews)

