from flask import Flask, request, render_template
from flask_script import Manager
from flask_bootstrap import Bootstrap

app = Flask(__name__)
manager = Manager(app)
bs = Bootstrap(app)


@app.route('/')
def index():
    ua = request.headers.get('User-Agent')
    # return '<h1>Hello!!!</h1><p>Your browser is %s</p>' % ua
    return render_template('index.html', ua=ua)



@app.route('/user/<name>')
def user(name):
    # return '<h1>Hello, %s!</h1>' % name
    return render_template('user.html', name=name)



@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template(('500.html')), 500


if __name__ == '__main__':
    # app.run(debug=True)
    manager.run()           # to run in command line as 'python3 ./run.py runserver'

