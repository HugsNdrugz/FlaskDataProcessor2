import os
import logging
from datetime import datetime
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Parse DATABASE_URL for connection parameters
db_url = urlparse(os.getenv('DATABASE_URL'))

# Initialize connection pool with optimal settings for Replit
pool = SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    database=db_url.path[1:],
    user=db_url.username,
    password=db_url.password,
    host=db_url.hostname,
    port=db_url.port,
    sslmode='require'
)

@contextmanager
def get_db_connection():
    """Get a connection from the pool with proper error handling and cleanup"""
    conn = None
    try:
        conn = pool.getconn()
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database connection error: {str(e)}")
        raise
    finally:
        if conn:
            try:
                pool.putconn(conn)
            except Exception as e:
                logger.error(f"Error returning connection to pool: {str(e)}")

def test_db_connection():
    """Test database connection"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
                # Check if tables exist
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'chats'
                    )
                """)
                chats_exists = cur.fetchone()[0]
                logger.info(f"Chats table exists: {chats_exists}")
            logger.info("Database connection test successful!")
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False

def init_db():
    """Initialize database schema"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Drop existing tables if they exist
                cur.execute("""
                    DROP TABLE IF EXISTS chats CASCADE;
                """)
                
                # Create chats table with correct schema
                cur.execute("""
                    CREATE TABLE chats (
                        id SERIAL PRIMARY KEY,
                        sender VARCHAR(255) NOT NULL,
                        recipient VARCHAR(255) NOT NULL,
                        text TEXT NOT NULL,
                        time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        type VARCHAR(50) DEFAULT 'message',
                        status VARCHAR(20) DEFAULT 'sent',
                        messenger VARCHAR(100) DEFAULT 'default',
                        CONSTRAINT valid_participants CHECK (
                            sender != recipient AND 
                            (sender = 'user' OR recipient = 'user')
                        )
                    )
                """)
                
                # Create indexes for better performance
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chats_sender_recipient 
                    ON chats(sender, recipient)
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chats_time 
                    ON chats(time DESC)
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chats_type 
                    ON chats(type)
                """)
                
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise
