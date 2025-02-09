"""
This module defines the `User` and `Health` models used in the application.

The `User` model represents the users of the application, storing their personal
information such as username, email, password, and other profile details. It also
maintains a relationship to the `Health` model to store associated health data.

The `Health` model represents health-related data for each user, including the
date of data recording, steps taken, heart rate, calories burned, stress level,
and sleep hours.

Models:
    - `User`: Stores user details and maintains a relationship with the health data.
    - `Health`: Stores health data for each user, including steps, heart rate, calories,
      stress, and sleep information.

These models interact with the database using SQLAlchemy, with the `Health` model
linked to the `User` model through a foreign key relationship.
"""
from src import db
from datetime import datetime, timezone
from sqlalchemy.orm import relationship

class Health(db.Model):
    """
    Represents a user's health data, including steps, heart rate, calories,
    stress level, and sleep hours for a given date.

    Attributes:
        id (int): The primary key for the health data record.
        userid (int): Foreign key linking to the User table.
        date (datetime): The date when the health data was recorded.
        steps (int): The number of steps recorded on the given day.
        heartrate (int): The average heart rate recorded on the given day.
        calories (int): The number of calories burned on the given day.
        stress (int): The stress level recorded on the given day.
        sleephours (float): The number of hours slept on the given day.
    """
    __tablename__ = "health_data"

    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    steps = db.Column(db.Integer, default=0)
    heartrate = db.Column(db.Integer, default=0)
    calories = db.Column(db.Integer, default=0)
    stress = db.Column(db.Integer, default=0)
    sleephours = db.Column(db.Float, default=0.0)

    def __repr__(self):
        """
        Returns a string representation of the Health record.

        Returns:
            str: A string representation of the health data, including the
                 date, steps, heart rate, and calories.
        """
        return f"<Health {self.date} - Steps: {self.steps}, HR: {self.heartrate}, Calories: {self.calories}>"

class User(db.Model):
    """
    Represents a user of the application.

    Attributes:
        id (int): The primary key for the user.
        username (str): The user's unique username.
        email (str): The user's unique email address.
        firstname (str): The user's first name.
        surname (str): The user's last name.
        password (str): The hashed password for the user.
        profilepic (str): The URL to the user's profile picture.
        height (float): The user's height in meters or centimeters.
        weight (float): The user's weight in kilograms.
        age (int): The user's age.
        gender (str): The user's gender.
        healthinfo (relationship): The relationship to the Health table, containing the user's health data.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    firstname = db.Column(db.String(80), nullable=False)
    surname = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    profilepic = db.Column(db.String(200), nullable=True)
    healthinfo = relationship(Health)

    height = db.Column(db.Float, nullable=True)
    weight = db.Column(db.Float, nullable=True)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(10), nullable=True)

    def __repr__(self):
        """
        Returns a string representation of the User.

        Returns:
            str: A string representation of the user's username.
        """
        return f'<User {self.username}>'
