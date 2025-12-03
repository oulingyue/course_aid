import os

from flask import Flask
from flask_cors import CORS
from course_aid.app.middleware.auth import auth
from course_aid.app.controllers import vote_controller, review_controller, assistant_controller
from course_aid.app.utils.helper import login_required
from course_aid.app.config import db_connection
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

app.register_blueprint(auth)

CORS(app)

conn = db_connection.connect()

@app.route("/instructor/<instructor_name>/review", methods=["GET"])
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