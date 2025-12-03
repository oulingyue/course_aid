'''
Endpoints for search functions 
'''
from db_connection import connect, close

''' 
What needs to be written: 
course search 
prof search 
/
'''

@app.route('/search_course/{}')
def search(content:str):
    db = connect()
    cursor = db.cursor()

@app.route('/search_professor/{instuctor_first}')