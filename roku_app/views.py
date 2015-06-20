from roku_app import roku_app
from flask import render_template

@roku_app.route('/')
@roku_app.route('/index')
def index():
    return render_template('videos.html')
