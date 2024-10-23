from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
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
            # Try to execute a simple query
            db.session.execute('SELECT 1')
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
