"""Application factory."""
from flask import Flask

from config import Config
from .extensions import db, login_manager, mail


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    from .auth.routes import auth_bp
    from .dashboard.routes import dashboard_bp
    from .admin.routes import admin_bp
    from .emails.routes import emails_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(emails_bp)

    with app.app_context():
        db.create_all()

    return app
