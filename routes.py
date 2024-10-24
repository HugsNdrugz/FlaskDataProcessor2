from flask import Blueprint, render_template, jsonify
from sqlalchemy import text
from models import db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        WHERE sender IS NOT NULL
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
        logger.error(f"Database error in index route: {str(e)}")
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
        logger.error(f"Database error in get_messages route: {str(e)}")
        return jsonify([])
