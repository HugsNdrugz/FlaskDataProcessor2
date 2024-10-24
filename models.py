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
                # Create chats table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS chats (
                        chat_id SERIAL PRIMARY KEY,
                        messenger VARCHAR(100),
                        time TIMESTAMP NOT NULL,
                        sender VARCHAR(100) NOT NULL,
                        text TEXT NOT NULL
                    )
                """)
                
                # Create indexes for better performance
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chats_sender_hash 
                    ON chats USING hash (sender)
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chats_time_brin 
                    ON chats USING brin (time)
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chats_sender_time_btree
                    ON chats USING btree (sender, time)
                """)
                
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise
