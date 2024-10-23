from app import app, db
from models import User, Conversation, Message
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

def init_db():
    # Clear existing data
    Message.query.delete()
    Conversation.query.delete()
    User.query.delete()
    
    # Create sample users
    users = [
        User(username='alice', email='alice@example.com', password_hash=generate_password_hash('password123')),
        User(username='bob', email='bob@example.com', password_hash=generate_password_hash('password123')),
        User(username='charlie', email='charlie@example.com', password_hash=generate_password_hash('password123'))
    ]
    
    for user in users:
        db.session.add(user)
    db.session.commit()
    
    # Create conversations
    conversations = [
        Conversation(user1_id=1, user2_id=2),  # Alice and Bob
        Conversation(user1_id=1, user2_id=3),  # Alice and Charlie
        Conversation(user2_id=2, user1_id=3)   # Bob and Charlie
    ]
    
    for conv in conversations:
        db.session.add(conv)
    db.session.commit()
    
    # Create sample messages
    base_time = datetime.utcnow() - timedelta(days=1)
    messages = [
        # Conversation between Alice and Bob
        Message(conversation_id=1, sender_id=1, content="Hey Bob, how are you?", timestamp=base_time),
        Message(conversation_id=1, sender_id=2, content="Hi Alice! I'm good, thanks!", timestamp=base_time + timedelta(minutes=5)),
        Message(conversation_id=1, sender_id=1, content="Great to hear that!", timestamp=base_time + timedelta(minutes=10)),
        
        # Conversation between Alice and Charlie
        Message(conversation_id=2, sender_id=1, content="Hello Charlie!", timestamp=base_time + timedelta(hours=1)),
        Message(conversation_id=2, sender_id=3, content="Hi Alice, nice to hear from you!", timestamp=base_time + timedelta(hours=1, minutes=5)),
        
        # Conversation between Bob and Charlie
        Message(conversation_id=3, sender_id=2, content="Charlie, are you there?", timestamp=base_time + timedelta(hours=2)),
        Message(conversation_id=3, sender_id=3, content="Yes Bob, what's up?", timestamp=base_time + timedelta(hours=2, minutes=3))
    ]
    
    for msg in messages:
        db.session.add(msg)
        # Update conversation last_message_time
        conv = Conversation.query.get(msg.conversation_id)
        conv.last_message_time = msg.timestamp
    
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        init_db()
        print("Database initialized with sample data!")
