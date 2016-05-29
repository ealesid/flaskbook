from flask import Flask, request, render_template, session, redirect, url_for, flash
from flask_mongoengine import MongoEngine
from flask_script import Manager, Server
from flask_bootstrap import Bootstrap
from flask_wtf import Form
from flask_mail import Mail, Message
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import os


class NameForm(Form):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')



app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret_key'
app.config['MONGODB_SETTINGS'] = {'DB': 'test'}
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['FLASKBOOK_ADMIN'] = os.environ.get('FLASKBOOK_ADMIN')
app.config['FLASKBOOK_MAIL_SUBJECT_PREFIX'] = '[Flaskbook]'
app.config['FLASKBOOK_MAIL_SENDER'] = 'Flaskbook Admin <ealesid@gmail.com>'

manager = Manager(app)
manager.add_command('runserver', Server(
    use_debugger=True,
    use_reloader=True,
    host='0.0.0.0'
))
bs = Bootstrap(app)
db = MongoEngine(app)
mail = Mail(app)

class Role(db.Document):
    # id = db.IntField(primary_key=True)
    name = db.StringField(max_length=True, unique=True)

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Document):
    # id = db.IntField(primary_key=True)
    username = db.StringField(max_length=64, unique=True)

    def __repr__(self):
        return '<User %r>' % self.username

### Before database implementation
# @app.route('/', methods=['GET', 'POST'])
# def index():
#     name = None
#     form = NameForm()
#     if form.validate_on_submit():
#         old_name = session.get('name')
#         if old_name is not None and old_name != form.name.data:
#             flash('Looks like you have changed your name!')
#         session['name'] = form.name.data
#         form.name.data = ''
#         return redirect(url_for('index'))
#     ua = request.headers.get('User-Agent')
#     # return '<h1>Hello!!!</h1><p>Your browser is %s</p>' % ua
#     return render_template('index.html', ua=ua, form=form, name=session.get('name'))

@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        user = User.objects(username__exact=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            user.save()
            session['known'] = False
            if app.config['FLASKBOOK_ADMIN']:
                send_email(app.config['FLASKBOOK_ADMIN'], 'New user', 'mail/new_user', user=user)
        else: session['known'] = True
        session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('index'))
    return render_template('index.html', form=form, name=session.get('name'), known=session.get('known'), emailto=[os.environ.get('FLASKBOOK_ADMIN')])


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


def send_email(to, subject, template, **kwargs):
    msg = Message(app.config['FLASKBOOK_MAIL_SUBJECT_PREFIX'] + subject,
                   sender=app.config['FLASKBOOK_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    mail.send(msg)

if __name__ == '__main__':
    # app.run(debug=True)
    manager.run()           # to run in command line as 'python3 ./run.py runserver'

