from datetime import datetime
from mongoengine import NotUniqueError, queryset_manager, Q
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request
from flask_login import UserMixin, AnonymousUserMixin
from markdown import markdown
import bleach
from . import db, login_manager
import hashlib


class Permission:
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80


class Role(db.Document):
    name = db.StringField(max_length=64, unique=True)
    default = db.BooleanField(default=False, index=True)
    permissions = db.IntField()

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.FOLLOW |
                     Permission.COMMENT |
                     Permission.WRITE_ARTICLES, True),
            'Moderator': (Permission.FOLLOW |
                          Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.objects(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            role.save()

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Document, UserMixin):
    username = db.StringField(max_length=64, unique=True)
    password_hash = db.StringField(max_length=128)
    email = db.StringField(max_length=64, unique=True, index=True)
    confirmed = db.BooleanField(default=False)
    role = db.ReferenceField(Role)
    name = db.StringField(max_length=64)
    location = db.StringField(max_length=64)
    about_me = db.StringField()
    member_since = db.DateTimeField(default=datetime.utcnow)
    last_seen = db.DateTimeField(default=datetime.utcnow)
    avatar_hash = db.StringField(max_length=32)

    @staticmethod
    def generate_fake(count=100):
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password_hash=generate_password_hash(forgery_py.lorem_ipsum.word()),
                     confirmed=True,
                     name=forgery_py.name.full_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True))
            try:
                u.save()
            except NotUniqueError:
                pass

    @staticmethod
    def add_self_follows():
        for user in User.objects():
            if not user.is_following(user):
                user.follow(user)
                user.save()

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKBOOK_ADMIN']:
                self.role = Role.objects(permissions=0xff).first()
            if self.role is None:
                self.role = Role.objects(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        # self.follow(self)

    @property
    def password(self):
        raise AttributeError('Password is not readable attribute')

    @property
    def followed_posts(self):
        user = User.objects(username=self.username).first()
        pipeline = [{"$lookup": {"from": "post",
                                 "localField": "followed",
                                 "foreignField": "author_id",
                                 "as": "followed_posts"}},
                    {"$unwind": "$followed_posts"},
                    {"$project": {"_id": "$followed_posts._id",
                                  "follower": 1,
                                  "body": "$followed_posts.body",
                                  "timestamp": "$followed_posts.timestamp",
                                  "author_id": "$followed_posts.author_id"}},
                    {"$out": "followed_posts"}]
        Follow.objects(follower=user).aggregate(*pipeline)

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def get_id(self):
        return User.objects(username=self.username).first()['username']

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
        self.save()
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.username})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.username:
            return False
        self.password_hash = generate_password_hash(new_password)
        self.save()
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.username, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.username:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if User.objects(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        self.save()
        return True

    def can(self, permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen = datetime.utcnow()
        self.save()

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def follow(self, user):
        if not Follow.is_following(self, user):
            Follow(follower=self, followed=user, timestamp=datetime.utcnow()).save()

    def unfollow(self, user):
        Follow.objects().filter(Q(follower=self) & Q(followed=user)).first().delete()

    def is_following(self, user):
        return Follow.is_following(self, user).first() is not None

    def is_followed(self, user):
        return Follow.is_followed(self, user) is not None

    def count_followers(self):
        return Follow.objects().filter(followed=self).count()

    def count_followed(self):
        return Follow.objects().filter(follower=self).count()


class Follow(db.Document):
    follower = db.ReferenceField(User)
    followed = db.ReferenceField(User)
    timestamp = db.DateTimeField()

    @queryset_manager
    def is_following(doc_cls, queryset, follower, followed):
        return queryset(Q(follower=follower) & Q(followed=followed))

    @queryset_manager
    def is_followed(doc_cls, queryset, follower, followed):
        return queryset(Q(followed=followed) & Q(follower=follower))


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(username):
    return User.objects(username=username).first()


class Post(db.Document):
    body = db.StringField()
    body_html = db.StringField()
    timestamp = db.DateTimeField(index=True, default=datetime.utcnow)
    author_id = db.ReferenceField(User)

    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.objects().count()
        for i in range(count):
            u = User.objects().skip(randint(0, user_count - 1)).first()
            p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1, 5)),
                     timestamp=forgery_py.date.date(True),
                     author_id=u)
            p.save()

    @staticmethod
    def on_change_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul', 'p',
                        'h1', 'h2', 'h3']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))


class FollowedPosts(db.Document):
    follower = db.ReferenceField(User)
    post = db.ReferenceField(Post)
    timestamp = db.DateTimeField()
    author_id = db.ReferenceField(User)
    body = db.StringField()

# AttributeError: 'MongoEngine' object has no attribute 'event'
# db.event.listen(Post.body, 'set', Post.on_change_body)
