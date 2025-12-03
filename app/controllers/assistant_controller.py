import os
from flask import request, jsonify, render_template, session


def assistant():
    return render_template("views/templates/assistant.html")

