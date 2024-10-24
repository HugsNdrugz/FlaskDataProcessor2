from flask import Blueprint, render_template, jsonify, request
from sqlalchemy import text
from models import db, Messages
from datetime import datetime

routes = Blueprint('routes', __name__)

@routes.route('/')
def index():
    # Fixed DISTINCT ON query with proper ORDER BY clause
    query = text("""
        SELECT DISTINCT ON (contact) 
            contact,
            time,
            text,
            location
        FROM (
            SELECT sender as contact, time, text, NULL as location
            FROM chat
            UNION ALL
            SELECT from_to as contact, time, text, location
            FROM sms
            UNION ALL
            SELECT sender as contact, timestamp as time, message as text, NULL as location
            FROM messages
            WHERE recipient = 'You'
        ) combined
        ORDER BY contact, time DESC
    """)
    
    try:
        result = db.session.execute(query)
        contacts = [
            {
                'sender': row.contact,
                'time': row.time.strftime('%Y-%m-%d %H:%M:%S'),
                'text': row.text,
                'location': row.location
            }
            for row in result
        ]
        return render_template('index.html', contacts=contacts, messages=[])
    except Exception as e:
        print(f"Database error: {str(e)}")
        return render_template('index.html', contacts=[], messages=[])

@routes.route('/messages/<contact>')
def get_messages(contact):
    query = text("""
        SELECT 
            sender,
            time,
            text,
            location
        FROM (
            SELECT 
                CASE 
                    WHEN sender = :contact THEN sender 
                    ELSE 'You'
                END as sender,
                time,
                text,
                NULL as location
            FROM chat 
            WHERE sender = :contact
            UNION ALL
            SELECT 
                CASE 
                    WHEN from_to = :contact THEN from_to
                    ELSE 'You'
                END as sender,
                time,
                text,
                location
            FROM sms
            WHERE from_to = :contact
            UNION ALL
            SELECT 
                CASE 
                    WHEN sender = :contact THEN sender
                    ELSE 'You'
                END as sender,
                timestamp as time,
                message as text,
                NULL as location
            FROM messages
            WHERE sender = :contact OR recipient = :contact
        ) combined
        ORDER BY time ASC
    """)
    
    try:
        result = db.session.execute(query, {'contact': contact})
        messages = [
            {
                'sender': row.sender,
                'time': row.time.strftime('%Y-%m-%d %H:%M:%S'),
                'text': row.text,
                'location': row.location
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
        
        # Insert into messages table
        new_message = Messages(
            sender='You',
            recipient=contact,
            message=message_text,
            timestamp=datetime.utcnow(),
            is_read=True
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to send message'}), 500
