from app import create_app
from models import db, Chat
from datetime import datetime, timedelta

def init_db():
    app = create_app()
    with app.app_context():
        # Drop existing tables and recreate them
        db.drop_all()
        db.create_all()

        # Create sample chat data with conversations
        now = datetime.utcnow()
        sample_chats = [
            # Alice conversation
            Chat(sender='Alice', text='Hey there!', time=now - timedelta(hours=5)),
            Chat(sender='You', text='Hi Alice! How are you?', time=now - timedelta(hours=4, minutes=55)),
            Chat(sender='Alice', text='I\'m good, thanks! Want to grab lunch?', time=now - timedelta(hours=4, minutes=50)),
            Chat(sender='You', text='Sure, that sounds great!', time=now - timedelta(hours=4, minutes=45)),
            
            # Bob conversation
            Chat(sender='Bob', text='How are you?', time=now - timedelta(hours=3)),
            Chat(sender='You', text='Doing well, thanks! How about you?', time=now - timedelta(hours=2, minutes=55)),
            Chat(sender='Bob', text='Pretty good! Working on the project', time=now - timedelta(hours=2, minutes=50)),
            Chat(sender='You', text='Nice! Let me know if you need help', time=now - timedelta(hours=2, minutes=45)),
            
            # Charlie conversation
            Chat(sender='Charlie', text='Meeting at 3?', time=now - timedelta(hours=1)),
            Chat(sender='You', text='Yes, I\'ll be there!', time=now - timedelta(minutes=55)),
            Chat(sender='Charlie', text='Great, see you then!', time=now - timedelta(minutes=50)),
            Chat(sender='You', text='Perfect, conference room A right?', time=now - timedelta(minutes=45)),
            Chat(sender='Charlie', text='Yep, that\'s correct', time=now - timedelta(minutes=40))
        ]

        # Add sample data to database
        db.session.add_all(sample_chats)
        
        try:
            db.session.commit()
            print("Database initialized successfully!")
        except Exception as e:
            print(f"Error initializing database: {e}")
            db.session.rollback()

if __name__ == '__main__':
    init_db()
