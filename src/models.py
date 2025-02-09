from src import db
from datetime import datetime, timezone
from sqlalchemy.orm import relationship

class Health(db.Model):
    __tablename__ = "health_data"

    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, unique = False)
    steps = db.Column(db.Integer, default=0)
    heartrate = db.Column(db.Integer, default=0.0)
    calories = db.Column(db.Integer, default=0.0)
    stress = db.Column(db.Integer, default=0.0)
    sleephours = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return f"<Health {self.date} - Steps: {self.steps}, HR: {self.heartrate}, Calories: {self.calories}>"

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    firstname = db.Column(db.String(80), nullable=False)
    surname = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    profilepic = db.Column(db.String(200), nullable=True)
    healthinfo = relationship(Health)
    
    height = db.Column(db.Float, nullable=True)      # Височина (например в сантиметри или метри)
    weight = db.Column(db.Float, nullable=True)      # Тегло (например в килограми)
    age = db.Column(db.Integer, nullable=True)         # Години
    gender = db.Column(db.String(10), nullable=True)

    def __repr__(self):
        return f'<User {self.username}>'