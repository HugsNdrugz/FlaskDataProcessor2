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

@routes.route('/')
@handle_errors
def index():
    """Get initial contacts with optimized query"""
    try:
        with get_db_connection(readonly=True) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Get initial set of contacts
                cur.execute("""
                    WITH RankedMessages AS (
                        SELECT DISTINCT ON (contact_name)
                            CASE 
                                WHEN sender = 'user' THEN recipient 
                                ELSE sender 
                            END as contact_name,
                            text,
                            time,
                            id,
                            ROW_NUMBER() OVER (ORDER BY time DESC) as rn
                        FROM chats
                        WHERE sender IS NOT NULL
                    )
                    SELECT *
                    FROM RankedMessages
                    WHERE rn <= 20
                    ORDER BY time DESC
                """)
                contacts = [{
                    'sender': row['contact_name'],
                    'text': row['text'],
                    'time': row['time'].strftime('%Y-%m-%d %H:%M:%S'),
                    'id': row['id']
                } for row in cur.fetchall()]
                return render_template('index.html', contacts=contacts)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return render_template('index.html', contacts=[])

@routes.route('/contacts')
@handle_errors
def get_contacts():
    """Get contacts with optimized pagination and cursor-based navigation"""
    cursor = request.args.get('cursor', type=int, default=0)
    limit = min(int(request.args.get('limit', 20)), 50)
    
    try:
        with get_db_connection(readonly=True) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Get next batch of contacts using cursor
                cur.execute("""
                    WITH RankedMessages AS (
                        SELECT DISTINCT ON (contact_name)
                            CASE 
                                WHEN sender = 'user' THEN recipient 
                                ELSE sender 
                            END as contact_name,
                            text,
                            time,
                            id,
                            ROW_NUMBER() OVER (ORDER BY time DESC) as rn
                        FROM chats
                        WHERE sender IS NOT NULL
                            AND id < %s
                    )
                    SELECT *
                    FROM RankedMessages
                    WHERE rn <= %s
                    ORDER BY time DESC
                """, (cursor if cursor > 0 else float('inf'), limit + 1))
                
                rows = cur.fetchall()
                has_more = len(rows) > limit
                contacts = rows[:limit]
                
                result = [{
                    'name': row['contact_name'],
                    'last_message': row['text'],
                    'last_message_time': row['time'].strftime('%Y-%m-%d %H:%M:%S'),
                    'cursor': row['id']
                } for row in contacts]
                
                return jsonify({
                    'contacts': result,
                    'has_more': has_more
                })
    except Exception as e:
        logger.error(f"Error in get_contacts route: {str(e)}")
        return jsonify({'contacts': [], 'has_more': False})

@routes.route('/messages/<contact>')
@handle_errors
def get_messages(contact):
    """Get messages with optimized caching and cursor-based pagination"""
    if not contact or not isinstance(contact, str):
        raise BadRequest('Invalid contact parameter')
    
    cursor = request.args.get('cursor', type=int, default=0)
    limit = min(int(request.args.get('limit', 20)), 50)
    
    cache_key = f'messages_{contact}_{cursor}_{limit}'
    cached_result = messages_cache.get(cache_key)
    if cached_result:
        return jsonify(cached_result)
    
    try:
        with get_db_connection(readonly=True) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Get messages with cursor-based pagination
                cur.execute("""
                    SELECT sender, text, time, id,
                           ROW_NUMBER() OVER (ORDER BY time DESC) as rn
                    FROM chats 
                    WHERE ((sender = %s AND recipient = 'user')
                        OR (sender = 'user' AND recipient = %s))
                        AND id < %s
                    ORDER BY time DESC
                    LIMIT %s
                """, (contact, contact, cursor if cursor > 0 else float('inf'), limit + 1))
                
                rows = cur.fetchall()
                has_more = len(rows) > limit
                messages = rows[:limit]
                
                result = {
                    'messages': [{
                        'sender': row['sender'],
                        'time': row['time'].strftime('%Y-%m-%d %H:%M:%S'),
                        'text': row['text'],
                        'cursor': row['id']
                    } for row in messages],
                    'has_more': has_more
                }
                
                messages_cache[cache_key] = result
                return jsonify(result)
    except Exception as e:
        logger.error(f"Error in get_messages route: {str(e)}")
        return jsonify({'messages': [], 'has_more': False})

@routes.route('/health')
def health_check():
    """Health check endpoint with connection monitoring"""
    try:
        with get_db_connection(readonly=True) as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
                cur.execute('SELECT count(*) FROM pg_stat_activity')
                connection_count = cur.fetchone()[0]
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow(),
            'active_connections': connection_count
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503
