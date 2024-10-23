from app import create_app
from models import db, Chat, SMS
from datetime import datetime, timedelta

def init_db():
    app = create_app()
    with app.app_context():
        # Drop existing tables and recreate them
        db.drop_all()
        db.create_all()

        # Create sample data
        sample_chats = [
            Chat(sender='Alice', text='Hey there!', time=datetime.utcnow() - timedelta(days=1)),
            Chat(sender='Bob', text='How are you?', time=datetime.utcnow() - timedelta(hours=12)),
            Chat(sender='Charlie', text='Meeting at 3?', time=datetime.utcnow() - timedelta(hours=2))
        ]

        sample_sms = [
            SMS(from_to='Alice', text='At the coffee shop', time=datetime.utcnow() - timedelta(hours=1), 
                location='Coffee Shop, Downtown'),
            SMS(from_to='Bob', text='On my way', time=datetime.utcnow() - timedelta(minutes=30), 
                location='Central Station'),
            SMS(from_to='Charlie', text='Yes, see you there!', time=datetime.utcnow(), 
                location='Office Building')
        ]

        # Add sample data to database
        db.session.add_all(sample_chats)
        db.session.add_all(sample_sms)
        
        try:
            db.session.commit()
            print("Database initialized successfully!")
        except Exception as e:
            print(f"Error initializing database: {e}")
            db.session.rollback()

if __name__ == '__main__':
    init_db()
