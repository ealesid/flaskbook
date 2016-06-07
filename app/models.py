from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask_login import UserMixin
from . import db, login_mananger


class Role(db.Document):
    name = db.StringField(max_length=True, unique=True)

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Document, UserMixin):
    username = db.StringField(max_length=64, unique=True)
    password_hash = db.StringField(max_length=128)
    email = db.StringField(max_length=64, unique=True, index=True)
    confirmed = db.BooleanField(default=False)

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

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.username})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.username:
            return False
        self.confirmed = True
        # db.session.add(self)
        self.save()
        return True

    def get_id(self):
        return User.objects(username__exact=self.username).first()['username']

    def __repr__(self):
        return '<User %r>' % self.username


@login_mananger.user_loader
def load_user(username):
    return User.objects(username__exact=username).first()
