from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class Chat(db.Model):
    __tablename__ = 'chat'
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    time = db.Column(db.DateTime, nullable=False)

class SMS(db.Model):
    __tablename__ = 'sms'
    id = db.Column(db.Integer, primary_key=True)
    from_to = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
