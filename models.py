import os
import logging
from datetime import datetime
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from contextlib import contextmanager
from urllib.parse import urlparse
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Parse DATABASE_URL for connection parameters
db_url = urlparse(os.getenv('DATABASE_URL'))

# Initialize connection pool with optimized settings
pool = ThreadedConnectionPool(
    minconn=1,
    maxconn=10,
    database=db_url.path[1:],
    user=db_url.username,
    password=db_url.password,
    host=db_url.hostname,
    port=db_url.port,
    sslmode='require',
    connect_timeout=3,
    keepalives=1,
    keepalives_idle=30,
    keepalives_interval=10,
    keepalives_count=5
)

@contextmanager
def get_db_connection(readonly=True, max_retries=3, retry_delay=1):
    """Get a connection from the pool with improved retry logic"""
    conn = None
    
    for attempt in range(max_retries):
        try:
            conn = pool.getconn()
            
            # Set session parameters
            conn.set_session(
                isolation_level=psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED,
                readonly=readonly,
                autocommit=False if readonly else True
            )
            
            # Test connection
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
                if not readonly:
                    conn.commit()
            
            yield conn
            
            if not readonly:
                try:
                    conn.commit()
                except:
                    conn.rollback()
                    raise
            break
            
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            logger.warning(f"Database connection attempt {attempt + 1} failed: {str(e)}")
            if conn:
                try:
                    pool.putconn(conn, close=True)
                except Exception:
                    pass
                conn = None
                
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise
                
        finally:
            if conn:
                try:
                    pool.putconn(conn)
                except Exception as e:
                    logger.error(f"Error returning connection to pool: {str(e)}")

def test_db_connection():
    """Test database connection with improved error handling"""
    try:
        with get_db_connection(readonly=True) as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
                logger.info("Database connection test successful!")
                return True
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False
