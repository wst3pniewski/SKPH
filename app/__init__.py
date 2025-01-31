import os
from flask import Flask, render_template, request, redirect
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.affected.routes import bp as affected_bp
from app.auth.routes import bp as auth_bp
from app.auth.user_service import init_login_manager
from app.communication.routes import bp as chat_bp
from app.communication.socketio_chat import socketio
from app.donors.routes import bp as donors_bp
from app.extensions import babel, db, get_locale, mail
from app.maps.routes import bp as maps_bp
from app.organization.routes import bp as organization_bp
from app.reports.routes import bp as reports_bp
from app.volunteers.routes import bp as volunteers_bp
from app.supply_chain.routes import bp as supply_chain_bp
from config import config


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    flask_app = Flask(__name__)
    flask_app.config.from_object(config[config_name])

    # Initialize Flask extensions here
    db.init_app(flask_app)
    babel.init_app(flask_app, locale_selector=get_locale)
    init_login_manager(flask_app)
    mail.init_app(flask_app)
    socketio.init_app(flask_app)

    with flask_app.app_context():
        # db.drop_all()
        db.create_all()

    # Register blueprints here
    flask_app.register_blueprint(auth_bp, url_prefix='/auth')

    flask_app.register_blueprint(reports_bp, url_prefix='/reports')

    flask_app.register_blueprint(volunteers_bp, url_prefix='/volunteers')

    flask_app.register_blueprint(chat_bp, url_prefix="/communication")

    flask_app.register_blueprint(affected_bp, url_prefix='/affected')

    flask_app.register_blueprint(donors_bp, url_prefix='/donors')

    flask_app.register_blueprint(organization_bp, url_prefix='/organizations')

    flask_app.register_blueprint(maps_bp, url_prefix='/maps')

    flask_app.register_blueprint(supply_chain_bp, url_prefix='/supply-chain')

    @flask_app.route('/set_language', methods=['POST'])
    def set_language():
        lang = request.form.get('lang')
        response = redirect(request.referrer)
        response.set_cookie('lang', lang)
        return response

    @flask_app.route('/')
    def home():
        return render_template('index.jinja')

    @flask_app.route('/db')
    def check_db():
        try:
            with db.engine.connect() as connection:
                result = connection.execute(
                    text('SELECT CURRENT_TIMESTAMP')).scalar()
                print(result)
                if result:
                    return f'Database connection is established. Current timestamp: {result}'
                else:
                    return 'Database connection failed.'
        except SQLAlchemyError as e:
            return f'Database connection failed: {str(e)}'

    return flask_app
