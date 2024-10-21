from flask import render_template, jsonify, request
from app import app, db
from models import User, Conversation, Message
from sqlalchemy import or_
from datetime import datetime, timedelta

# Sample data
sample_users = [
    {'id': 1, 'username': 'alice', 'email': 'alice@example.com'},
    {'id': 2, 'username': 'bob', 'email': 'bob@example.com'},
    {'id': 3, 'username': 'charlie', 'email': 'charlie@example.com'},
]

sample_conversations = [
    {'id': 1, 'user1_id': 1, 'user2_id': 2, 'last_message_time': datetime.utcnow() - timedelta(minutes=5)},
    {'id': 2, 'user1_id': 1, 'user2_id': 3, 'last_message_time': datetime.utcnow() - timedelta(hours=1)},
]

sample_messages = [
    {'id': 1, 'conversation_id': 1, 'sender_id': 1, 'content': 'Hey Bob!', 'timestamp': datetime.utcnow() - timedelta(minutes=10)},
    {'id': 2, 'conversation_id': 1, 'sender_id': 2, 'content': 'Hi Alice!', 'timestamp': datetime.utcnow() - timedelta(minutes=5)},
    {'id': 3, 'conversation_id': 2, 'sender_id': 1, 'content': 'Hello Charlie!', 'timestamp': datetime.utcnow() - timedelta(hours=1)},
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat')
def chat_view():
    return render_template('chat_view.html')

@app.route('/api/conversations')
def get_conversations():
    # Assuming user_id 1 for demonstration purposes
    user_id = 1
    conversations = []
    for conv in sample_conversations:
        if conv['user1_id'] == user_id or conv['user2_id'] == user_id:
            other_user_id = conv['user2_id'] if conv['user1_id'] == user_id else conv['user1_id']
            other_user = next(user for user in sample_users if user['id'] == other_user_id)
            conversations.append({
                'id': conv['id'],
                'other_user': other_user['username'],
                'last_message_time': conv['last_message_time'].isoformat()
            })
    return jsonify(conversations)

@app.route('/api/messages/<int:conversation_id>')
def get_messages(conversation_id):
    messages = [msg for msg in sample_messages if msg['conversation_id'] == conversation_id]
    result = [{
        'id': msg['id'],
        'sender_id': msg['sender_id'],
        'content': msg['content'],
        'timestamp': msg['timestamp'].isoformat()
    } for msg in messages]
    return jsonify(result)

@app.route('/api/send_message', methods=['POST'])
def send_message():
    data = request.json
    new_message = {
        'id': len(sample_messages) + 1,
        'conversation_id': data['conversation_id'],
        'sender_id': data['sender_id'],
        'content': data['content'],
        'timestamp': datetime.utcnow()
    }
    sample_messages.append(new_message)
    return jsonify({'status': 'success', 'message_id': new_message['id']})
