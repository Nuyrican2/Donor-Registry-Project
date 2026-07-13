"""Shared Flask extension instances (initialized in the app factory)."""
from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to view your dashboard."
