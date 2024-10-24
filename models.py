import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text, Index, create_engine
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize connection pool with optimal settings for Replit
pool = SimpleConnectionPool(
    minconn=1,
    maxconn=10,  # Replit has limited resources, keep pool size moderate
    dbname=os.getenv('PGDATABASE'),
    user=os.getenv('PGUSER'),
    password=os.getenv('PGPASSWORD'),
    host=os.getenv('PGHOST'),
    port=os.getenv('PGPORT'),
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

class Base(DeclarativeBase):
    pass

# Configure SQLAlchemy with optimized engine options
db = SQLAlchemy(
    model_class=Base,
    engine_options={
        'pool_size': 5,
        'max_overflow': 10,
        'pool_timeout': 30,
        'pool_pre_ping': True,
        'pool_recycle': 1800
    }
)

def test_db_connection(app):
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

class Chat(db.Model):
    """Chat model with optimized indexes for PostgreSQL 15"""
    __tablename__ = 'chat'
    
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(100), nullable=False, index=True)
    text = db.Column(db.Text, nullable=False)
    time = db.Column(db.DateTime, nullable=False, index=True)
    
    # Optimized compound index for common queries
    __table_args__ = (
        Index('idx_sender_time_btree', 'sender', 'time', postgresql_using='btree'),
    )

    def __init__(self, sender, text, time=None):
        self.sender = sender
        self.text = text
        self.time = time or datetime.utcnow()

    def __repr__(self):
        return f'<Chat {self.sender}: {self.text[:50]}>'

def init_db_settings(app):
    """Initialize database settings with production configuration"""
    with app.app_context():
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # PostgreSQL 15 optimized settings
                    cur.execute("SET work_mem = '16MB'")
                    cur.execute("SET maintenance_work_mem = '64MB'")
                    cur.execute("SET random_page_cost = 1.1")
                    cur.execute("SET effective_io_concurrency = 200")
                    cur.execute("SET vacuum_cost_delay = 20")
                    cur.execute("SET vacuum_cost_limit = 2000")
                    
                    # Create optimized indexes
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_chat_sender_hash 
                        ON chat USING hash (sender)
                    """)
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_chat_time_brin 
                        ON chat USING brin (time)
                    """)
                logger.info("Database settings initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database settings: {str(e)}")
            raise
