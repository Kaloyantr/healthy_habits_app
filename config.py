import os

class Config:
    """Основна конфигурация за приложението"""
    SECRET_KEY = os.environ.get("SECRET_KEY", "default-secret-key")
    SQLALCHEMY_DATABASE_URI = "sqlite:///src/database/db.sqlite3"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
