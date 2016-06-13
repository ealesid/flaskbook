import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret_key'
    FLASKBOOK_MAIL_SUBJECT_PREFIX = '[Flaskbook]'
    FLASKBOOK_MAIL_SENDER = 'Flaskbook Admin <ealesid@gmail.com>'
    # FLASKBOOK_ADMIN = os.environ.get('FLASKBOOK_ADMIN')
    DEBUG_TB_INTERCEPT_REDIRECTS = False


    @staticmethod
    def init_app(app):
        pass

class DevConfig(Config):
    DEBUG = True
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    # MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    # MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    FLASKBOOK_ADMIN = 'ealesid@gmail.com'
    MAIL_USERNAME = 'ealesid'
    MAIL_PASSWORD = 'sdrvAlks2201$'


config = {
    'development': DevConfig,
    'default': DevConfig
}
