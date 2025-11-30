import os
import psycopg2
import functools
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, g, flash
from flask_cors import CORS
from datetime import datetime
from db_connection import connect, close
from auth import auth

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

app.register_blueprint(auth)

CORS(app)

#---- review class ----#
class Review():
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


#---- sql commands ----# 
def login_required(f):
    """Decorator to require login for a route"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def execute_qry(sql_cmd, params):
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute(sql_cmd, params)
        if sql_cmd.strip().upper().startswith(("INSERT")):
            conn.commit()
            print("Insertion committed to the database.")
            return cur.lastrowid if cur.lastrowid else None
        elif sql_cmd.strip().upper().startswith(("UPDATE", "DELETE")):
            conn.commit()
            print("Changes committed to the database.")
            return cur.rowcount if cur.rowcount else None
        else:
                result = cur.fetchall()
                return result
    except psycopg2.Error as e:
        conn.rollback()
        print(f"failed to query: {e}")
        return None
    finally: 
        cur.close()
        conn.close()

def get_course_sections(instructor_first,instructor_last):
    cmd = f'SELECT course_number FROM course_section where (instructor_first = %s) and (instructor_last= %s);'
    results = execute_qry(cmd, (instructor_first, instructor_last))
    return [r[0] for r in results]  if results else None

def save_review(review:Review):
    """Save a review to the database"""
    sql_cmd = f'INSERT INTO review (comment, rating, post_time, last_updated, course_number, instructor_first, instructor_last, username) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
    execute_qry(sql_cmd, (review.comment, review.rating, review.post_time, review.last_updated, review.course_num, review.instructor_first, review.instructor_last, review.username))
    print('insert success.')

def get_reviews():
    sql_cmd = f'select * from review;'
    results = execute_qry(sql_cmd, ())
    return results if results else None
    
# ----- endpoints ------- # 


@app.route('/')
def index():
    """Display list of professors"""
    return render_template('base.html')

@app.route('/review/<instructor_first>/<instructor_last>', methods=['GET', 'POST'])
@login_required
def review_form(instructor_first,instructor_last):
    """Display review form for a specific professor"""
    user_id = session.get("user_id")
    courses = get_course_sections(instructor_first, instructor_last)
    if not courses:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        course_number = request.form.get('course_number') or request.json.get('course_number')
        rating = request.form.get('rating') or request.json.get('rating')
        comment = request.form.get('comment') or request.json.get('comment')
        if not course_number or not rating or not comment:
            return jsonify({"error": "Invalid data"}), 400
        
        # Save review
        new_review = Review(
                        comment=comment, 
                        instructor_first=instructor_first,
                        instructor_last=instructor_last, 
                        course_num=course_number,
                        rating = rating,
                        username = user_id)
        review = save_review(new_review)
        
        # Return JSON if requested, otherwise redirect
        if request.is_json:
            return jsonify(new_review.to_dict()), 201
        
        flash(f'Review for {instructor_first} {instructor_last} submitted successfully!', 'success')
        return redirect(url_for('index'))
    
    # GET request - display form
    return render_template('reviews/review_form.html', courses=courses, instructor_first=instructor_first, instructor_last=instructor_last)


@app.route('/reviews')
def view_reviews():
    """Display all submitted reviews (optional - for testing)"""
    reviews = get_reviews()
    return render_template('reviews/reviews_list.html', reviews=reviews)

if __name__ == '__main__':
    app.run(debug=True)