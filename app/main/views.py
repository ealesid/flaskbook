import os
from flask import render_template
from . import main

@main.route('/')
def index():
    return render_template('index.html', emailto=[os.environ.get('FLASKBOOK_ADMIN')])
