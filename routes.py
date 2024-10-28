from flask import Blueprint, render_template, jsonify, request
import logging
from functools import wraps
from datetime import datetime
from werkzeug.exceptions import BadRequest
from cachetools import TTLCache
import psycopg2.extras
from models import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize cache with 5-minute TTL
messages_cache = TTLCache(maxsize=100, ttl=300)
contacts_cache = TTLCache(maxsize=100, ttl=300)

routes = Blueprint('routes', __name__)

def handle_errors(f):
    """Decorator for consistent error handling"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except BadRequest as e:
            logger.warning(f"Bad request: {str(e)}")
            return jsonify({'error': str(e)}), 400
        except psycopg2.Error as e:
            logger.error(f"Database error: {str(e)}")
            return jsonify({'error': 'Database error occurred'}), 500
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return jsonify({'error': 'An unexpected error occurred'}), 500
    return wrapper

def get_contacts():
    """Get all contacts with their latest messages"""
    cache_key = 'contacts_list'
    if cache_key in contacts_cache:
        return contacts_cache[cache_key]
        
    query = """
        WITH RankedMessages AS (
            SELECT 
                c.sender,
                c.recipient,
                c.time,
                c.text,
                ROW_NUMBER() OVER (PARTITION BY CASE 
                    WHEN c.sender = 'user' THEN c.recipient 
                    ELSE c.sender 
                END ORDER BY c.time DESC) as rn
            FROM chats c
            WHERE c.sender IS NOT NULL
        )
        SELECT sender, recipient, time, text
        FROM RankedMessages
        WHERE rn = 1
        ORDER BY time DESC
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(query)
                rows = cur.fetchall()
                contacts = []
                for row in rows:
                    contact_name = row['recipient'] if row['sender'] == 'user' else row['sender']
                    contacts.append({
                        'name': contact_name,
                        'lastMessage': row['text'],
                        'time': row['time'].strftime('%Y-%m-%d %H:%M:%S')
                    })
                contacts_cache[cache_key] = contacts
                return contacts
    except Exception as e:
        logger.error(f"Error fetching contacts: {str(e)}")
        return []

@routes.route('/')
@handle_errors
def index():
    """Display contacts list"""
    contacts = get_contacts()
    return render_template('index.html', contacts=contacts)

@routes.route('/messages/<contact>')
@handle_errors
def get_messages(contact):
    """Get all messages for a specific contact"""
    if not contact or not isinstance(contact, str):
        raise BadRequest('Invalid contact parameter')
    
    cache_key = f'messages_{contact}'
    if cache_key in messages_cache:
        return jsonify(messages_cache[cache_key])
    
    query = """
        SELECT sender, recipient, text, time
        FROM chats 
        WHERE (sender = %s AND recipient = 'user')
           OR (sender = 'user' AND recipient = %s)
        ORDER BY time ASC
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(query, (contact, contact))
                rows = cur.fetchall()
                messages = [
                    {
                        'sender': row['sender'],
                        'time': row['time'].strftime('%Y-%m-%d %H:%M:%S'),
                        'text': row['text']
                    }
                    for row in rows
                ]
                messages_cache[cache_key] = messages
                return jsonify(messages)
    except Exception as e:
        logger.error(f"Error in get_messages route: {str(e)}")
        return jsonify([])

@routes.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
                return jsonify({'status': 'healthy'})
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503
