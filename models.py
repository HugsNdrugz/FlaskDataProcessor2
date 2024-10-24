import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text, Index, create_engine
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime
import psycopg2
from psycopg2.pool import SimpleConnectionPool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize connection pool
pool = SimpleConnectionPool(
    minconn=1,
    maxconn=20,
    dbname=os.getenv('PGDATABASE'),
    user=os.getenv('PGUSER'),
    password=os.getenv('PGPASSWORD'),
    host=os.getenv('PGHOST'),
    port=os.getenv('PGPORT'),
    sslmode='require'
)

def get_db_connection():
    """Get a connection from the pool with error handling"""
    try:
        conn = pool.getconn()
        logger.info("Successfully acquired database connection from pool")
        return conn
    except Exception as e:
        logger.error(f"Error getting database connection: {str(e)}")
        raise

class Base(DeclarativeBase):
    pass

# Configure SQLAlchemy with engine options for production
db = SQLAlchemy(
    model_class=Base,
    engine_options={
        'pool_size': 10,
        'max_overflow': 20,
        'pool_timeout': 30,
        'pool_pre_ping': True
    }
)

def test_db_connection(app):
    """Test database connection with improved error handling and logging"""
    try:
        with app.app_context():
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
            pool.putconn(conn)
            logger.info("Database connection test successful!")
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False

class Messages(db.Model):
    """Messages model with optimized indexes"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(100), nullable=False, index=True)
    recipient = db.Column(db.String(100), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    is_read = db.Column(db.Boolean, default=False)
    
    __table_args__ = (
        Index('idx_sender_recipient', 'sender', 'recipient'),
        Index('idx_timestamp', 'timestamp'),
    )

    def __init__(self, sender, recipient, message, timestamp=None, is_read=False):
        self.sender = sender
        self.recipient = recipient
        self.message = message
        self.timestamp = timestamp or datetime.utcnow()
        self.is_read = is_read

    def __repr__(self):
        return f'<Message {self.sender} to {self.recipient}: {self.message[:50]}>'

def init_db_settings(app):
    """Initialize database settings with production configuration"""
    with app.app_context():
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                # Set only session-level parameters
                cur.execute("SET work_mem = '16MB'")
                cur.execute("SET maintenance_work_mem = '128MB'")
                cur.execute("SET random_page_cost = 1.1")
            conn.commit()
            pool.putconn(conn)
            logger.info("Database settings initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database settings: {str(e)}")
            if 'conn' in locals():
                pool.putconn(conn)
            raise
