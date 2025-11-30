from db_connection import connect
from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)



rev = Blueprint('review', __name__, url_prefix='/review')

@rev.route('/<instructor_name>', methods=('GET', 'POST'))
def post_review():
    if request.method == 'POST':
        content = request.form['review']
        rating = request.form['rating']
        course_number = request.form ['course_number']
        

    elif request.method == 'GET':


