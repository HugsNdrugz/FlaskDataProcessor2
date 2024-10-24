from flask import Blueprint, render_template, jsonify, request
from sqlalchemy import text
from models import db, Messages, Chat
from datetime import datetime

routes = Blueprint('routes', __name__)

@routes.route('/')
def index():
    query = text("""
        SELECT DISTINCT ON (sender) 
            sender as contact,
            time,
            text
        FROM chat
        ORDER BY sender, time DESC
    """)
    
    try:
        result = db.session.execute(query)
        contacts = [
            {
                'sender': row.contact,
                'time': row.time.strftime('%Y-%m-%d %H:%M:%S'),
                'text': row.text
            }
            for row in result
        ]
        return render_template('index.html', contacts=contacts)
    except Exception as e:
        print(f"Database error: {str(e)}")
        return render_template('index.html', contacts=[])

@routes.route('/messages/<contact>')
def get_messages(contact):
    query = text("""
        SELECT 
            sender,
            time,
            text,
            CASE 
                WHEN sender = :contact THEN false
                ELSE true
            END as is_outgoing
        FROM chat 
        WHERE sender = :contact OR sender = 'You'
        ORDER BY time ASC
    """)
    
    try:
        result = db.session.execute(query, {'contact': contact})
        messages = [
            {
                'sender': row.sender,
                'time': row.time.strftime('%Y-%m-%d %H:%M:%S'),
                'text': row.text,
                'is_outgoing': row.is_outgoing
            }
            for row in result
        ]
        return jsonify(messages)
    except Exception as e:
        print(f"Database error: {str(e)}")
        return jsonify([])

@routes.route('/messages/send', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        contact = data.get('contact')
        message_text = data.get('message')
        
        if not contact or not message_text:
            return jsonify({'error': 'Missing contact or message'}), 400
        
        # Insert into chat table
        new_message = Chat(
            sender='You',
            text=message_text,
            time=datetime.utcnow()
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to send message'}), 500
