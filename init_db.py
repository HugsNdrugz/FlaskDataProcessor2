from app import create_app
from models import db, Chat, Messages
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

        # Create sample chat data with incoming messages
        now = datetime.utcnow()
        
        # Sample chat messages
        sample_chats = [
            Chat(sender='Alice', text='Hey there!', time=now - timedelta(hours=5)),
            Chat(sender='Alice', text='I\'m good, thanks! Want to grab lunch?', time=now - timedelta(hours=4, minutes=50)),
            Chat(sender='Bob', text='How are you?', time=now - timedelta(hours=3)),
            Chat(sender='Bob', text='Pretty good! Working on the project', time=now - timedelta(hours=2, minutes=50)),
            Chat(sender='Charlie', text='Meeting at 3?', time=now - timedelta(hours=1)),
            Chat(sender='Charlie', text='Great, see you then!', time=now - timedelta(minutes=50)),
            Chat(sender='Charlie', text='Yep, that\'s correct', time=now - timedelta(minutes=40))
        ]

        # Sample messenger data
        sample_messages = [
            Messages(sender='Alice', recipient='user', message='Hey there!', timestamp=now - timedelta(hours=5)),
            Messages(sender='Alice', recipient='user', message='I\'m good, thanks! Want to grab lunch?', timestamp=now - timedelta(hours=4, minutes=50)),
            Messages(sender='Bob', recipient='user', message='How are you?', timestamp=now - timedelta(hours=3)),
            Messages(sender='Bob', recipient='user', message='Pretty good! Working on the project', timestamp=now - timedelta(hours=2, minutes=50)),
            Messages(sender='Charlie', recipient='user', message='Meeting at 3?', timestamp=now - timedelta(hours=1)),
            Messages(sender='Charlie', recipient='user', message='Great, see you then!', timestamp=now - timedelta(minutes=50)),
            Messages(sender='Charlie', recipient='user', message='Yep, that\'s correct', timestamp=now - timedelta(minutes=40))
        ]

        # Add sample data to database
        db.session.add_all(sample_chats)
        db.session.add_all(sample_messages)
        
        try:
            db.session.commit()
            logger.info("Database initialized successfully!")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            db.session.rollback()

if __name__ == '__main__':
    init_db()
