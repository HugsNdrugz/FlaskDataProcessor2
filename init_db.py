from datetime import datetime, timedelta
from app import app, db
from models import Chat, SMS

def init_db():
    with app.app_context():
        # Drop all tables in correct order
        db.session.commit()  # Commit any pending changes
        db.drop_all()  # This will handle dependencies correctly
        db.create_all()
        
        # Sample chat messages
        chats = [
            Chat(sender="Alice", text="Hey, how are you?", time=datetime.utcnow() - timedelta(minutes=30)),
            Chat(sender="Bob", text="I'm good, thanks! How about you?", time=datetime.utcnow() - timedelta(minutes=25)),
            Chat(sender="Alice", text="Doing great! Want to meet up later?", time=datetime.utcnow() - timedelta(minutes=20)),
            Chat(sender="Bob", text="Sure, that sounds good!", time=datetime.utcnow() - timedelta(minutes=15))
        ]
        
        db.session.add_all(chats)
        db.session.commit()

if __name__ == "__main__":
    init_db()
