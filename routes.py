from flask import Blueprint, render_template, jsonify, current_app
import logging
from models import test_db_connection
import psycopg2
from datetime import datetime
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bp = Blueprint('routes', __name__)

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=os.environ['PGDATABASE'],
            user=os.environ['PGUSER'],
            password=os.environ['PGPASSWORD'],
            host=os.environ['PGHOST'],
            port=os.environ['PGPORT']
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return None

@bp.route('/')
def index():
    try:
        # Test database connection
        if not test_db_connection():
            raise Exception("Database connection failed")

        # Get database connection
        conn = get_db_connection()
        if not conn:
            raise Exception("Could not establish database connection")

        with conn.cursor() as cur:
            # Get contacts with their latest message
            cur.execute("""
                WITH LatestMessages AS (
                    SELECT 
                        CASE 
                            WHEN sender = 'user' THEN recipient
                            ELSE sender 
                        END as contact_name,
                        text,
                        time,
                        ROW_NUMBER() OVER (
                            PARTITION BY 
                                CASE 
                                    WHEN sender = 'user' THEN recipient
                                    ELSE sender 
                                END
                            ORDER BY time DESC
                        ) as rn
                    FROM chats
                )
                SELECT 
                    c.name as name,
                    COALESCE(lm.text, '') as last_message,
                    COALESCE(lm.time, NOW()) as last_message_time,
                    COUNT(CASE WHEN ch.read = false AND ch.recipient = 'user' THEN 1 END) as unread_count,
                    CASE 
                        WHEN c.last_active > NOW() - INTERVAL '5 minutes' THEN true
                        ELSE false
                    END as is_online
                FROM contacts c
                LEFT JOIN LatestMessages lm ON lm.contact_name = c.name AND lm.rn = 1
                LEFT JOIN chats ch ON (ch.sender = c.name OR ch.recipient = c.name)
                GROUP BY c.name, c.last_active, lm.text, lm.time
                ORDER BY lm.time DESC NULLS LAST;
            """)
            
            contacts = []
            for row in cur.fetchall():
                contacts.append({
                    'name': row[0],
                    'last_message': row[1],
                    'last_message_time': row[2].strftime('%Y-%m-%d %H:%M:%S') if row[2] else None,
                    'unread_count': row[3] or 0,
                    'is_online': row[4]
                })

        conn.close()
        return render_template('index.html', contacts=contacts)

    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        # Return template with empty contacts list in case of error
        return render_template('index.html', contacts=[])

@bp.route('/messages/<contact>')
def get_messages(contact):
    try:
        conn = get_db_connection()
        if not conn:
            raise Exception("Could not establish database connection")

        with conn.cursor() as cur:
            cur.execute("""
                SELECT sender, recipient, text, time
                FROM chats
                WHERE (sender = %s AND recipient = 'user')
                   OR (sender = 'user' AND recipient = %s)
                ORDER BY time DESC
                LIMIT 50;
            """, (contact, contact))
            
            messages = []
            for row in cur.fetchall():
                messages.append({
                    'sender': row[0],
                    'recipient': row[1],
                    'text': row[2],
                    'time': row[3].strftime('%Y-%m-%d %H:%M:%S')
                })

        conn.close()
        return jsonify(messages)

    except Exception as e:
        logger.error(f"Error fetching messages: {str(e)}")
        return jsonify({'error': 'Failed to fetch messages'}), 500
