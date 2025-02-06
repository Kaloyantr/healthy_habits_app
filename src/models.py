from src import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    firstname = db.Column(db.String(80), nullable=False)
    surname = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    profilepic = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f'<User {self.username}>'