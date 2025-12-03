from course_aid.app import app, conn
from course_aid.app.controllers import vote_controller, review_controller, assistant_controller, index_controller
from course_aid.app.utils.helper import login_required


@app.route('/')
def index():
    return index_controller.index()
@app.route("/instructor/<instructor_name>/reviews", methods=["GET"])
@login_required
def instructor_review(instructor_name):
    return review_controller.get_reviews_for_instructor(conn, instructor_name)

@app.route("/reviews/<int:review_id>/vote", methods=["POST"])
@login_required
def handle_votes(review_id):
    return vote_controller.handle_votes(conn, review_id)


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


@app.route("/assistant", methods=["GET","POST"])
@login_required
def assistant():
    return assistant_controller.get_assistant()