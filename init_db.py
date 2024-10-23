from datetime import datetime, timedelta
from app import app, db
from models import Chat, SMS

def init_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        # Sample chat messages
        chats = [
            Chat(sender="Alice", text="Hey, how are you?", time=datetime.utcnow() - timedelta(minutes=30)),
            Chat(sender="Bob", text="I'm good, thanks! How about you?", time=datetime.utcnow() - timedelta(minutes=25)),
            Chat(sender="Alice", text="Doing great! Want to meet up later?", time=datetime.utcnow() - timedelta(minutes=20))
        ]
        
        # Sample SMS messages
        sms = [
            SMS(from_to="John", text="Will be there in 10 mins", time=datetime.utcnow() - timedelta(hours=2), location="Downtown"),
            SMS(from_to="Mary", text="Got the tickets!", time=datetime.utcnow() - timedelta(hours=1), location="Theater"),
            SMS(from_to="David", text="Meeting postponed to 3 PM", time=datetime.utcnow() - timedelta(minutes=45), location="Office")
        ]
        
        db.session.add_all(chats)
        db.session.add_all(sms)
        db.session.commit()

if __name__ == "__main__":
    init_db()
