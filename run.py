from flask import Flask, request
from flask_script import Manager

app = Flask(__name__)
manager = Manager(app)


@app.route('/')
def index():
    ua = request.headers.get('User-Agent')
    return '<h1>Hello!!!</h1><p>Your browser is %s</p>' % ua



@app.route('/user/<name>')
def user(name):
    return '<h1>Hello, %s!</h1>' % name


if __name__ == '__main__':
    # app.run(debug=True)
    manager.run()           # to run in command line as 'python3 ./run.py runserver'

