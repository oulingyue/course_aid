from app import app, conn
from app.controllers import vote_controller, review_controller, assistant_controller, index_controller
from app.utils.helper import login_required, execute_qry
from flask import (g, session)


#---- Review forms ----# 
@app.route('/')
def index():
    return index_controller.index()

#--- Check if user is logged in ----#
@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        q = f'SELECT * FROM users WHERE username = %s'
        result = execute_qry(q, (user_id,))
        g.user = result[0] if result else None


#---- endpoints for instructor view ----#
@app.route("/instructor/<instructor_name>/reviews", methods=["GET"])
@login_required
def instructor_review(instructor_name):
    return review_controller.get_reviews_for_instructor(conn, instructor_name)

@app.route("/reviews/<int:review_id>/vote", methods=["POST"])
@login_required
def handle_votes(review_id):
    return vote_controller.handle_votes(conn, review_id)


#---- Endpoints for user reviews -----# 
@app.route("/user_reviews")
@login_required
def get_user_reviews():
    return review_controller.get_user_reviews(conn)

@app.route("/user_reviews/<int:review_id>/edit", methods=["PATCH", "PUT"])
@login_required
def edit_reviews(review_id):
    return review_controller.edit_review(review_id, conn)

@app.route("/user_reviews/<int:review_id>/delete", methods=["DELETE"])
@login_required
def delete_reviews(review_id):
    return review_controller.delete_review(review_id, conn)


#---- assistant API endpoints----#
@app.route("/assistant", methods=["GET","POST"])
@login_required
def assistant():
    return assistant_controller.get_assistant()


#---- API endpoints for posting reviews ----# 
@app.route('/review/<instructor_first>/<instructor_last>', methods=['GET', 'POST'])
@login_required
def review_form(instructor_first,instructor_last):
    """ review form for a specific professor"""
    return review_controller.review_form(instructor_first,instructor_last)

@app.route('/reviews')
@login_required
def view_reviews():
    return review_controller.view_reviews()

#---- search reviews ----# 
@app.route("/search-page")
@login_required
def search_page():
    """Render the search page."""
    return index_controller.search_page()

@app.route('/search')
@login_required
def search():
    """
    Endpoint for searching all professors
    """
    return index_controller.search()

