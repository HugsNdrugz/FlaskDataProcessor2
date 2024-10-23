from flask import render_template, jsonify
from app import app, db
from models import Chat, SMS
from sqlalchemy import desc, union_all

@app.route('/')
def index():
    # Create a union of Chat and SMS messages
    chat_messages = db.session.query(
        Chat.sender.label('sender'),
        Chat.time.label('time'),
        Chat.text.label('text'),
        db.null().label('location')
    )
    
    sms_messages = db.session.query(
        SMS.from_to.label('sender'),
        SMS.time.label('time'),
        SMS.text.label('text'),
        SMS.location.label('location')
    )
    
    # Combine and order all messages
    all_messages = chat_messages.union_all(sms_messages).order_by(desc('time')).all()
    return render_template('index.html', messages=all_messages)

@app.route('/api/messages')
def get_messages():
    chat_messages = db.session.query(
        Chat.sender.label('sender'),
        Chat.time.label('time'),
        Chat.text.label('text'),
        db.null().label('location')
    )
    
    sms_messages = db.session.query(
        SMS.from_to.label('sender'),
        SMS.time.label('time'),
        SMS.text.label('text'),
        SMS.location.label('location')
    )
    
    all_messages = chat_messages.union_all(sms_messages).order_by(desc('time')).all()
    return jsonify([{
        'sender': msg.sender,
        'text': msg.text,
        'time': msg.time.strftime('%B %d, %H:%M'),
        'location': msg.location
    } for msg in all_messages])
