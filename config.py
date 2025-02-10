import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = 'secret'
    # os.environ.get('SECRET_KEY')
    UPLOAD_FOLDER = 'app/static/uploads'

    BABEL_TRANSLATION_DIRECTORIES = '../translations'

    # postgresql+psycopg2://DATABASE_USER:PASSWORD@DATABASE_HOST_NAME:DATABASE_PORT/DATABASE_NAME
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI')

    # mail
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = os.getenv('MAIL_PORT')
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL') == 'True'
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')

    # hcaptcha
    HCAPTCHA_ENABLED = os.getenv('HCAPTCHA_ENABLED')
    HCAPTCHA_SITE_KEY = os.getenv('HCAPTCHA_SITE_KEY')
    HCAPTCHA_SECRET_KEY = os.getenv('HCAPTCHA_SECRET_KEY')


class DeploymentConfig(Config):
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOSTNAME = os.getenv('DB_HOSTNAME')
    DB_PORT = os.getenv('DB_PORT')
    DB_NAME = os.getenv('DB_NAME')

    SQLALCHEMY_DATABASE_URI = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOSTNAME}:{DB_PORT}/{DB_NAME}'


config = {
    'development': Config,
    'production': DeploymentConfig,
}
