from datetime import datetime
from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(64), nullable=False)
    time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    text = db.Column(db.Text, nullable=False)

class SMS(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_to = db.Column(db.String(64), nullable=False)
    time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    text = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(256))
