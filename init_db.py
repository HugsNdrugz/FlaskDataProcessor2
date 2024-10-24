from app import create_app
from models import db, Messages
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    app = create_app()
    with app.app_context():
        # Drop existing tables and recreate them
        db.drop_all()
        db.create_all()

        # Create sample messenger data with conversations
        now = datetime.utcnow()
        
        sample_messages = [
            Messages(sender='Alice', recipient='user', message='Hey there!', timestamp=now - timedelta(hours=5)),
            Messages(sender='user', recipient='Alice', message='Hi Alice! How are you?', timestamp=now - timedelta(hours=4, minutes=55)),
            Messages(sender='Alice', recipient='user', message='I\'m good, thanks! Want to grab lunch?', timestamp=now - timedelta(hours=4, minutes=50)),
            Messages(sender='Bob', recipient='user', message='How are you?', timestamp=now - timedelta(hours=3)),
            Messages(sender='user', recipient='Bob', message='Doing well! Working on the project', timestamp=now - timedelta(hours=2, minutes=55)),
            Messages(sender='Bob', recipient='user', message='Pretty good! Making progress?', timestamp=now - timedelta(hours=2, minutes=50)),
            Messages(sender='Charlie', recipient='user', message='Meeting at 3?', timestamp=now - timedelta(hours=1)),
            Messages(sender='user', recipient='Charlie', message='Yes, that works for me', timestamp=now - timedelta(minutes=55)),
            Messages(sender='Charlie', recipient='user', message='Great, see you then!', timestamp=now - timedelta(minutes=50)),
            Messages(sender='Charlie', recipient='user', message='Yep, that\'s correct', timestamp=now - timedelta(minutes=40))
        ]

        # Add sample data to database
        db.session.add_all(sample_messages)
        
        try:
            db.session.commit()
            logger.info("Database initialized successfully!")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            db.session.rollback()

if __name__ == '__main__':
    init_db()
