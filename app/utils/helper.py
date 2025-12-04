import json
import os
from functools import wraps
from flask import jsonify, session
from app.config import db_connection


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Login required'}), 401
        return f(*args, **kwargs)

    return decorated_function

def execute_qry(sql_cmd, params):
    """
    This method is a helper function that helps execute a sql command with indicated parameters. 
    Can be used for insert, read, update, and delete queries 
    """
    conn = db_connection.connect()
    cur = conn.cursor()
    try:
        cur.execute(sql_cmd, params)
        if sql_cmd.strip().upper().startswith(("INSERT")):
            if "RETURNING" in sql_cmd.upper():
                result = cur.fetchone()
                conn.commit()
                print("Insertion committed to the database.")
                return result[0] if result else None
            else:
                conn.commit()
                print("Insertion committed to the database.")
                return None
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

def validate_instructor(cursor, instructor_name):
    instructor_first = instructor_name.split(" ")[0]
    instructor_last = instructor_name.split(" ")[-1]

    check_query = '''
                  select first_name, last_name \
                  from instructors; \
                  '''
    cursor.execute(check_query)
    valid_instructors = cursor.fetchall()
    for valid_instructor in valid_instructors:
        if (instructor_first.lower() == valid_instructor[0].lower() and
            instructor_last.lower() == valid_instructor[1].lower()):
            return valid_instructor[0], valid_instructor[1]

    return None

def check_for_summary(cursor, instructor_name):

    instructor_first, instructor_last = validate_instructor(cursor, instructor_name)

    cursor.execute('''
        select check_for_summary( %s, %s, CURRENT_TIMESTAMP)
    ''', [instructor_first, instructor_last])

    return cursor.fetchone()[0]


def get_consensus_summary(instructor_first, instructor_last):
    BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
    CACHE_FILE = os.path.join(BASE_DIR, 'summary_cache.json')

    with open(CACHE_FILE, "r") as file:
        summary_cache = json.load(file)

    for data in summary_cache["data"]:
        if data["first"] == instructor_first and data["last"] == instructor_last:
            return data["summary"]



def update_summary_cache(cursor):
    from course_aid.app.models.assistant import AssistantRoles
    deepseek = AssistantRoles()
    with open("utils/summary_cache.json", "rw") as file:
        summary_cache = json.load(file)

    for data in summary_cache["data"]:
        instructor_first = data["first"]
        instructor_last = data["last"]

        if (check_for_summary(cursor, f"{instructor_first} {instructor_last}")):
            summary = deepseek.generate_consensus_summary(instructor_first, instructor_last)
            if data["first"] == instructor_first and data["last"] == instructor_last:
                data["summary"] = summary

            print("Updated summary cache for instructor", instructor_first, instructor_last)

        else:
            print("Condition to update summary cache not satisfied for instructor", instructor_first, instructor_last)




if __name__ == '__main__':

    # conn = db_connection.connect()
    #
    # try:
    #
    #     update_summary_cache(cursor)
    #
    # except Exception as e:
    #     print(e)
    # finally:
    #
    #     conn.close()

    '''
    CREATE OR REPLACE FUNCTION check_for_summary(
    in first_name varchar(50), 
    in last_name varchar(50), 
    in check_timestamp timestamptz
)
RETURNS boolean AS $$
DECLARE
    max_timestamp timestamptz;
    comment_count integer;
BEGIN
    
    SELECT MAX(last_updated) INTO max_timestamp
    FROM review 
    WHERE instructor_first = first_name
      AND instructor_last = last_name;
    
    
    IF max_timestamp < current_timestamp THEN
        
        SELECT COUNT(comment) INTO comment_count
        FROM review 
        WHERE instructor_first = first_name
          AND instructor_last = last_name;
        
        IF comment_count >= 20 THEN
            RETURN TRUE;
        ELSE
            RETURN FALSE;
        END IF;
    ELSE
        RETURN FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql;
    '''



