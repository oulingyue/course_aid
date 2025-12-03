import os
from flask import request, jsonify, render_template, session


def get_assistant():
    return render_template("view/templates/assistant.html")

