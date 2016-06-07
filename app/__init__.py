from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_mongoengine import MongoEngine
from config import config
from flask_login import LoginManager, login_required
from flask_debugtoolbar import DebugToolbarExtension


bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = MongoEngine()
login_mananger = LoginManager()
login_mananger.session_protection = 'strong'
login_mananger.login_view = 'auth.login'
toolbar = DebugToolbarExtension()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_mananger.init_app(app)
    # toolbar.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    @app.route('/secret')
    @login_required
    def secret():
        return 'Only authenticated users are allowed!!!'

    return app
