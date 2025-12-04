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
search = Blueprint('search', __name__, url_prefix='/search')

def get_departments():
    """
    returning all present departments in the database
    """
    q = "SELECT department_name FROM departments"
    results = execute_qry(q,)
    return [row["department_name"] for row in results]

@app.route("/search-page")
def search_page():
    """Render the search page."""
    try:
        departments = get_departments()
    except Exception as e:
        print(f"Database error: {e}")
        departments = []
    return render_template("search.html", departments=departments)

@app.route('/search')
def search():
    query = request.args.get("q", "").strip()
    mode = request.args.get("mode", "course")
    dept_filter = request.args.get("department", "all")
    sort_order = request.args.get("sort", "desc")

    if not query:
        return jsonify([])
    
    dept_param = None if dept_filter == "all" else dept_filter
    sort_asc = sort_order == "asc"

    if mode == "course":
        q = "SELECT * FROM search_prof_by_course(%s, %s, %s)"
    
    else: 
        q = "SELECT * FROM search_prof_by_name(%s, %s, %s)"
    
    results = execute_qry(q, (query, dept_param, sort_asc))

    formatted = []
    for prof in results:
        prof_data = {
            "first_name": prof["instructor_first"],
            "last_name": prof["instructor_last"],
            "rating": float(prof["avg_rating"]) if prof["avg_rating"] else 0,
            "department": prof.get("department", "Unknown")
        }
        
        formatted.append(prof_data)
            
    return jsonify(formatted)