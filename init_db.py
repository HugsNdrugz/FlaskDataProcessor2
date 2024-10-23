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
            Chat(sender="Alice", text="Doing great! Want to meet up later?", time=datetime.utcnow() - timedelta(minutes=20)),
            Chat(sender="Bob", text="Sure, that sounds good!", time=datetime.utcnow() - timedelta(minutes=15))
        ]
        
        # Sample SMS messages
        sms = [
            SMS(from_to="Charlie", text="I'm at the coffee shop", time=datetime.utcnow() - timedelta(minutes=28),
                location="Downtown Coffee"),
            SMS(from_to="David", text="Running late, be there in 10", time=datetime.utcnow() - timedelta(minutes=22),
                location="Central Station")
        ]
        
        db.session.add_all(chats)
        db.session.add_all(sms)
        db.session.commit()

if __name__ == "__main__":
    init_db()
