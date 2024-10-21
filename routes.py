from flask import render_template, jsonify, request
from app import app, db
from models import User, Conversation, Message
from sqlalchemy import or_
from datetime import datetime

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
    conversations = Conversation.query.filter(
        or_(Conversation.user1_id == user_id, Conversation.user2_id == user_id)
    ).order_by(Conversation.last_message_time.desc()).all()
    
    result = []
    for conv in conversations:
        other_user = conv.user2 if conv.user1_id == user_id else conv.user1
        result.append({
            'id': conv.id,
            'other_user': other_user.username,
            'last_message_time': conv.last_message_time.isoformat()
        })
    
    return jsonify(result)

@app.route('/api/messages/<int:conversation_id>')
def get_messages(conversation_id):
    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.timestamp).all()
    result = [{
        'id': msg.id,
        'sender_id': msg.sender_id,
        'content': msg.content,
        'timestamp': msg.timestamp.isoformat()
    } for msg in messages]
    return jsonify(result)

@app.route('/api/send_message', methods=['POST'])
def send_message():
    data = request.json
    new_message = Message(
        conversation_id=data['conversation_id'],
        sender_id=data['sender_id'],
        content=data['content']
    )
    db.session.add(new_message)
    
    conversation = Conversation.query.get(data['conversation_id'])
    conversation.last_message_time = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'status': 'success', 'message_id': new_message.id})
