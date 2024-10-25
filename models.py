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
                # Drop existing tables
                cur.execute("""
                    DROP TABLE IF EXISTS applications, calls, chats, contacts, keylogs, sms CASCADE;
                """)
                
                # Create applications table
                cur.execute("""
                    CREATE TABLE applications (
                        application_id SERIAL PRIMARY KEY,
                        application_name VARCHAR(255) NOT NULL,
                        package_name VARCHAR(255) UNIQUE NOT NULL,
                        installed_date TIMESTAMP
                    )
                """)
                
                # Create calls table
                cur.execute("""
                    CREATE TABLE calls (
                        id SERIAL PRIMARY KEY,
                        call_type VARCHAR(50),
                        call_time TIMESTAMP,
                        from_to VARCHAR(255),
                        duration VARCHAR(50),
                        location TEXT
                    )
                """)
                
                # Create chats table
                cur.execute("""
                    CREATE TABLE chats (
                        id SERIAL PRIMARY KEY,
                        messenger VARCHAR(100),
                        time TIMESTAMP,
                        sender VARCHAR(255),
                        recipient VARCHAR(255),
                        text TEXT
                    )
                """)
                
                # Create contacts table
                cur.execute("""
                    CREATE TABLE contacts (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) UNIQUE NOT NULL,
                        last_message_time TIMESTAMP
                    )
                """)
                
                # Create keylogs table
                cur.execute("""
                    CREATE TABLE keylogs (
                        id SERIAL PRIMARY KEY,
                        application VARCHAR(255),
                        time TIMESTAMP,
                        text TEXT
                    )
                """)
                
                # Create SMS table
                cur.execute("""
                    CREATE TABLE sms (
                        id SERIAL PRIMARY KEY,
                        from_to VARCHAR(255),
                        text TEXT,
                        time TIMESTAMP,
                        location TEXT
                    )
                """)
                
                # Create indexes for better performance
                cur.execute("CREATE INDEX idx_apps_installed_date ON applications(installed_date)")
                cur.execute("CREATE INDEX idx_calls_time ON calls(call_time)")
                cur.execute("CREATE INDEX idx_chats_time ON chats(time)")
                cur.execute("CREATE INDEX idx_contacts_name ON contacts(name)")
                cur.execute("CREATE INDEX idx_keylogs_time ON keylogs(time)")
                cur.execute("CREATE INDEX idx_sms_time ON sms(time)")
                
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise
