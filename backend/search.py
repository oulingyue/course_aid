'''
Endpoints for search functions 
'''
from app import execute_qry
from flask import Flask, render_template, request, jsonify
from db_connection import connect, close


''' 
What needs to be written: 
course search 
prof search 
/
'''

def search_by_professor()


search = Blueprint('search', __name__, url_prefix='/search')


@app.route('/')
def search_course(content:str):
    q = request.args.get("q", "").lower().strip()
    mode = request.args.get("mode", "course")
    dept_filter = request.args.get("departments ")
    sort_order = request.args.get("sort", desc)

    if not q:
        return jsonify([])

    results = []

    if mode == "course":
        for prof in professors: 
            