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
    maxconn=10,  # Replit has limited resources, keep pool size moderate
    database=db_url.path[1:],
    user=db_url.username,
    password=db_url.password,
    host=db_url.hostname,
    port=db_url.port,
    sslmode='require',
    # PostgreSQL 15 optimized settings
    options='-c work_mem=16MB -c maintenance_work_mem=64MB -c effective_cache_size=128MB'
)

@contextmanager
def get_db_connection():
    """Get a connection from the pool with proper error handling and cleanup"""
    conn = None
    try:
        conn = pool.getconn()
        # Set session-specific parameters
        with conn.cursor() as cur:
            cur.execute("SET SESSION synchronous_commit = off")
            cur.execute("SET SESSION statement_timeout = '30s'")
        logger.info("Successfully acquired database connection from pool")
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
    """Test database connection with improved error handling and logging"""
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
    """Initialize database schema and settings"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Create chat table with optimized schema
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS chat (
                        id SERIAL PRIMARY KEY,
                        sender VARCHAR(100) NOT NULL,
                        text TEXT NOT NULL,
                        time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create optimized indexes
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chat_sender_hash 
                    ON chat USING hash (sender)
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chat_time_brin 
                    ON chat USING brin (time)
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_sender_time_btree
                    ON chat USING btree (sender, time)
                """)
                
                # Set PostgreSQL 15 optimized settings
                cur.execute("SET work_mem = '16MB'")
                cur.execute("SET maintenance_work_mem = '64MB'")
                cur.execute("SET random_page_cost = 1.1")
                cur.execute("SET effective_io_concurrency = 200")
                cur.execute("SET vacuum_cost_delay = 20")
                cur.execute("SET vacuum_cost_limit = 2000")
                
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise
