from flask import Blueprint, render_template, jsonify, request, current_app
from sqlalchemy import text
from models import db, Messages, get_db_connection
import logging
from functools import wraps
from datetime import datetime
import time
from werkzeug.exceptions import BadRequest
from cachetools import TTLCache
from sqlalchemy.exc import SQLAlchemyError
import psycopg2.extras

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize cache with 5-minute TTL
messages_cache = TTLCache(maxsize=100, ttl=300)

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
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return jsonify({'error': 'Database error occurred'}), 500
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return jsonify({'error': 'An unexpected error occurred'}), 500
    return wrapper

@routes.route('/')
@handle_errors
def index():
    """Get all contacts with their latest messages"""
    query = """
        SELECT DISTINCT ON (m.sender) 
            m.sender,
            m.timestamp as time,
            m.message as text,
            COUNT(CASE WHEN m.is_read = false AND m.recipient = 'user' THEN 1 END) as unread_count
        FROM messages m
        WHERE m.sender IS NOT NULL
        GROUP BY m.sender, m.timestamp, m.message
        ORDER BY m.sender, m.timestamp DESC
    """
    
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(query)
            rows = cur.fetchall()
            contacts = [
                {
                    'sender': row['sender'],
                    'time': row['time'].strftime('%Y-%m-%d %H:%M:%S'),
                    'text': row['text'],
                    'unread': row['unread_count']
                }
                for row in rows
            ]
            return render_template('index.html', contacts=contacts)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return render_template('index.html', contacts=[])
    finally:
        if 'conn' in locals():
            try:
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"Error closing connection: {str(e)}")

@routes.route('/messages/<contact>')
@handle_errors
def get_messages(contact):
    """Get all messages for a specific contact"""
    if not contact or not isinstance(contact, str) or len(contact) > 100:
        raise BadRequest('Invalid contact parameter')
    
    cache_key = f'messages_{contact}'
    if cache_key in messages_cache:
        return jsonify(messages_cache[cache_key])
    
    query = """
        SELECT 
            sender,
            recipient,
            message as text,
            timestamp as time,
            is_read
        FROM messages 
        WHERE (sender = %s AND recipient = 'user')
           OR (sender = 'user' AND recipient = %s)
        ORDER BY timestamp ASC
    """
    
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(query, (contact, contact))
            rows = cur.fetchall()
            messages = [
                {
                    'sender': row['sender'],
                    'recipient': row['recipient'],
                    'time': row['time'].strftime('%Y-%m-%d %H:%M:%S'),
                    'text': row['text'],
                    'is_read': row['is_read']
                }
                for row in rows
            ]
            
            # Mark messages as read
            update_query = """
                UPDATE messages 
                SET is_read = true 
                WHERE sender = %s 
                AND recipient = 'user' 
                AND is_read = false
            """
            cur.execute(update_query, (contact,))
            conn.commit()
            
            messages_cache[cache_key] = messages
            return jsonify(messages)
    except Exception as e:
        logger.error(f"Error in get_messages route: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return jsonify([])
    finally:
        if 'conn' in locals():
            try:
                conn.close()
            except Exception as e:
                logger.error(f"Error closing connection: {str(e)}")

@routes.route('/health')
def health_check():
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT 1')
        conn.close()
        return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow()})
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503
