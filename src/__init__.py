"""
This module defines the creation of the Flask application, configures the
necessary settings, initializes the database, and registers the application's
blueprints for routing.

It provides a function `create_app()` to set up the app and is used for
creating a Flask instance with proper configurations, extensions, and routes.

Main responsibilities:
- Initialize and configure the Flask application.
- Set up database connection using SQLAlchemy.
- Register blueprints for application routing.
- Define application-specific settings like upload folder and allowed file extensions.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
import os

db = SQLAlchemy()

def create_app():
    """
    Create and configure the Flask application.

    This function sets up the Flask application with the configurations from the 
    `Config` class, initializes the database, and registers the main blueprint.

    Returns:
        app (Flask): The configured Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
    db.init_app(app)
    from .routes import main
    app.register_blueprint(main)
    return app
