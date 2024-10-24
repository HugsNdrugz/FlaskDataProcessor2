from flask import Blueprint, render_template, jsonify
from sqlalchemy import text
from models import db
from datetime import datetime

routes = Blueprint('routes', __name__)

@routes.route('/')
def index():
    # Get latest message for each sender
    query = text('''
        SELECT DISTINCT ON (sender) 
            sender,
            time,
            text
        FROM chat
        ORDER BY sender, time DESC
    ''')
    
    try:
        result = db.session.execute(query)
        contacts = [
            {
                'sender': row.sender,
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
    query = text('''
        SELECT 
            sender,
            time,
            text
        FROM chat 
        WHERE sender = :contact
        ORDER BY time ASC
    ''')
    
    try:
        result = db.session.execute(query, {'contact': contact})
        messages = [
            {
                'sender': row.sender,
                'time': row.time.strftime('%Y-%m-%d %H:%M:%S'),
                'text': row.text
            }
            for row in result
        ]
        return jsonify(messages)
    except Exception as e:
        print(f"Database error: {str(e)}")
        return jsonify([])
