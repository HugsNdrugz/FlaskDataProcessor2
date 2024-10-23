from flask import render_template, jsonify, request
from app import app, db
from models import Chat, SMS
from sqlalchemy import desc, union_all, func

@app.route('/')
def index():
    # Get all unique contacts with their latest messages
    chat_messages = db.session.query(
        Chat.sender.label('contact'),
        Chat.time.label('time'),
        Chat.text.label('text'),
        db.null().label('location')
    )
    
    sms_messages = db.session.query(
        SMS.from_to.label('contact'),
        SMS.time.label('time'),
        SMS.text.label('text'),
        SMS.location.label('location')
    )
    
    # Combine all messages and get latest for each contact
    all_messages = chat_messages.union_all(sms_messages).subquery()
    
    latest_messages = db.session.query(
        all_messages.c.contact,
        all_messages.c.time,
        all_messages.c.text,
        all_messages.c.location
    ).order_by(
        desc(all_messages.c.time)
    ).distinct(all_messages.c.contact).all()
    
    selected_contact = request.args.get('contact')
    messages = []
    
    if selected_contact:
        filtered_chat = chat_messages.filter(Chat.sender == selected_contact)
        filtered_sms = sms_messages.filter(SMS.from_to == selected_contact)
        messages = filtered_chat.union_all(filtered_sms).order_by(desc('time')).all()
    
    return render_template('index.html', 
                         contacts=latest_messages,
                         messages=messages,
                         selected_contact=selected_contact)

@app.route('/messages/<contact>')
def get_contact_messages(contact):
    chat_messages = db.session.query(
        Chat.sender.label('sender'),
        Chat.time.label('time'),
        Chat.text.label('text'),
        db.null().label('location')
    ).filter(Chat.sender == contact)
    
    sms_messages = db.session.query(
        SMS.from_to.label('sender'),
        SMS.time.label('time'),
        SMS.text.label('text'),
        SMS.location.label('location')
    ).filter(SMS.from_to == contact)
    
    messages = chat_messages.union_all(sms_messages).order_by(desc('time')).all()
    return jsonify([{
        'sender': msg.sender,
        'text': msg.text,
        'time': msg.time.strftime('%H:%M'),
        'location': msg.location
    } for msg in messages])
