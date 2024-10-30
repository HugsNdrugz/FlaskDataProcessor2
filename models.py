from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Contact(db.Model):
    __tablename__ = 'contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    avatar = db.Column(db.String(255))
    online = db.Column(db.Boolean, default=False)
    last_message = db.Column(db.Text)
    messages = db.relationship('Message', backref='contact', lazy=True)

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    sender = db.Column(db.String(50), nullable=False)
    outgoing = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'), nullable=False)
