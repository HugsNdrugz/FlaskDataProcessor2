from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

def test_db_connection(app):
    """Test database connection and log the result"""
    try:
        with app.app_context():
            # Try to execute a simple query using text()
            db.session.execute(text('SELECT 1'))
            logger.info("Database connection successful!")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False

class Chat(db.Model):
    __tablename__ = 'chat'
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Chat {self.sender}: {self.text}>'

class SMS(db.Model):
    __tablename__ = 'sms'
    id = db.Column(db.Integer, primary_key=True)
    from_to = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))

    def __repr__(self):
        return f'<SMS {self.from_to}: {self.text}>'

class Calls(db.Model):
    __tablename__ = 'calls'
    id = db.Column(db.Integer, primary_key=True)
    call_type = db.Column(db.String(50), nullable=False)
    time = db.Column(db.DateTime, nullable=False)
    from_to = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer)
    location = db.Column(db.String(200))

    def __repr__(self):
        return f'<Call {self.from_to}: {self.duration}s>'

class Contacts(db.Model):
    __tablename__ = 'contacts'
    contact_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Contact {self.name}>'

class InstalledApps(db.Model):
    __tablename__ = 'installed_apps'
    app_id = db.Column(db.Integer, primary_key=True)
    application_name = db.Column(db.String(200), nullable=False)
    package_name = db.Column(db.String(200), nullable=False)
    install_date = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<App {self.application_name}>'

class Keylogs(db.Model):
    __tablename__ = 'keylogs'
    keylog_id = db.Column(db.Integer, primary_key=True)
    application = db.Column(db.String(200), nullable=False)
    time = db.Column(db.DateTime, nullable=False)
    text = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<Keylog {self.application}: {self.text[:20]}...>'

class Messages(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(100), nullable=False)
    recipient = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Message {self.sender} to {self.recipient}: {self.message[:20]}...>'
