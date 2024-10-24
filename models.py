from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text, Index
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Configure SQLAlchemy
db = SQLAlchemy(model_class=Base)

def test_db_connection(app):
    """Test database connection with improved error handling and logging"""
    try:
        with app.app_context():
            db.session.execute(text('SELECT 1'))
            logger.info("Database connection successful!")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False

class Messages(db.Model):
    """Messages model with optimized indexes"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender = db.Column(db.String(100), nullable=False, index=True)
    recipient = db.Column(db.String(100), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
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

class Chat(db.Model):
    """Chat model with optimized indexes"""
    __tablename__ = 'chat'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender = db.Column(db.String(100), nullable=False, index=True)
    text = db.Column(db.Text, nullable=False)
    time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_sender_time', 'sender', 'time'),
    )

    def __init__(self, sender, text, time=None):
        self.sender = sender
        self.text = text
        self.time = time or datetime.utcnow()

    def __repr__(self):
        return f'<Chat {self.sender}: {self.text[:50]}>'

def init_db_settings(app):
    """Initialize database settings"""
    with app.app_context():
        try:
            # Set session parameters for optimization
            db.session.execute(text("SET work_mem = '16MB'"))
            db.session.execute(text("SET maintenance_work_mem = '128MB'"))
            db.session.execute(text("SET random_page_cost = 1.1"))
            db.session.execute(text("SET effective_cache_size = '1GB'"))
            db.session.commit()
            logger.info("Database settings initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database settings: {str(e)}")
            db.session.rollback()
