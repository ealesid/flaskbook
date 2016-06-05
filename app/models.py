from . import db, login_mananger
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


@login_mananger.user_loader
def load_user(username):
    return User.objects(username__exact=username).first()

class Role(db.Document):
    name = db.StringField(max_length=True, unique=True)

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Document, UserMixin):
    username = db.StringField(max_length=64, unique=True)
    password_hash = db.StringField(max_length=128)
    email = db.StringField(max_length=64, unique=True, index=True)

    @property
    def password(self):
        raise AttributeError('Password is not readable attribute')

    @password.setter
    def password(self, password):
        self.pasword_hash = generate_password_hash(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return User.objects(username__exact=self.username).first()['username']

    def __repr__(self):
        return '<User %r>' % self.username
