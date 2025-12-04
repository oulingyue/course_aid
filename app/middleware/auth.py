import psycopg2
from app.config.db_connection import connect
from flask import (Blueprint, flash, redirect, render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

auth = Blueprint('auth', __name__, url_prefix='/auth')

@auth.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        school_year = request.form.get('school_year') or None 
        db = connect()
        cursor = db.cursor()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                hashed_pw = generate_password_hash(password)
                print(f"Username: {username}")
                print(f"Hashed password: {hashed_pw}")
                cursor.execute(
                    "INSERT INTO users (username, password, school_year) VALUES (%s, %s, %s)",
                    (username, hashed_pw, school_year),
                )
                db.commit()
            except psycopg2.IntegrityError:
                db.rollback()
                error = f"User {username} is already registered."
            except Exception as e:
                db.rollback()
                error = f"Error: {str(e)}"
            else: 
                cursor.close()
                return redirect(url_for("auth.login"))

        flash(error)
        cursor.close()

    return render_template('auth/register.html')

@auth.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = connect()
        cursor = db.cursor()
        error = None

        cursor.execute(
            'SELECT * FROM users WHERE username = %s', (username,)
        )
        user = cursor.fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user[1], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user[0]
            print(user[0])
            cursor.close()
            return redirect(url_for('index'))

        flash(error)
        cursor.close()

    return render_template('auth/login.html')

@auth.route("/logout")
def logout():
    """Clear the current session, including the stored user id."""
    session.clear()
    return redirect(url_for("index"))