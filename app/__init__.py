import os
from flask import Flask
from flask_cors import CORS
from course_aid.app.middleware.auth import auth
from course_aid.app.config import db_connection
from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__,
            template_folder='view/templates',
            static_folder='view/static')

app.secret_key = os.getenv("SECRET_KEY")
app.register_blueprint(auth)
CORS(app)

conn = db_connection.connect()


from course_aid.app import routes