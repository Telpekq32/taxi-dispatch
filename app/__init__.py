from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Бұл бетке кіру үшін жүйеге кіріңіз."
login_manager.login_message_category = "warning"


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    from app.blueprints.auth import auth_bp
    from app.blueprints.main import main_bp
    from app.blueprints.rides import rides_bp
    from app.blueprints.drivers import drivers_bp
    from app.blueprints.customers import customers_bp
    from app.blueprints.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(rides_bp)
    app.register_blueprint(drivers_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # Error handlers
    from app.errors import register_error_handlers
    register_error_handlers(app)

    # Ensure upload folder exists
    import os
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    return app
