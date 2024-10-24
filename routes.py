from flask import Blueprint, render_template, jsonify
from sqlalchemy import text
from models import db
from datetime import datetime

routes = Blueprint('routes', __name__)

@routes.route('/')
def index():
    # Query to get latest message for each contact from chats table
    query = text("""
        SELECT DISTINCT ON (sender) 
            sender as contact,
            time,
            text
        FROM chat
        WHERE sender != 'You'
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
            c.sender,
            c.time,
            c.text,
            CASE 
                WHEN c.sender = :contact THEN false
                ELSE true
            END as is_outgoing
        FROM chat c
        WHERE c.sender = :contact OR c.sender = 'You'
        ORDER BY c.time ASC
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
