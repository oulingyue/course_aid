import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from auth import auth

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

app.register_blueprint(auth)

CORS(app)

@app.route('/')
def index():
    return render_template('base.html')
    

if __name__ == '__main__':
    app.run(debug=True)