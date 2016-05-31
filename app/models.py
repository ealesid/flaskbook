from . import db
from werkzeug.security import generate_password_hash, check_password_hash

class Role(db.Document):
    # id = db.IntField(primary_key=True)
    name = db.StringField(max_length=True, unique=True)

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Document):
    # id = db.IntField(primary_key=True)
    username = db.StringField(max_length=64, unique=True)
    password_hash = db.StringField(max_length=128)

    @property
    def password(self):
        raise AttributeError('Password is not readable attribute')

    @password.setter
    def password(self, password):
        self.pasword_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.pasword_hash, password)

    def __repr__(self):
        return '<User %r>' % self.username

