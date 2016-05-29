from . import db

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

