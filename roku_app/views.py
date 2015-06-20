from roku_app import roku_app

@roku_app.route('/')
@roku_app.route('/index')
def index():
    return "Hello, World!"
