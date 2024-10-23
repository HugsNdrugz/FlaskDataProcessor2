from flask import render_template, jsonify
from app import app, db
from models import Chat
from sqlalchemy import desc

@app.route('/')
def index():
    # Get all messages ordered by time
    messages = Chat.query.order_by(Chat.time).all()
    return render_template('index.html', messages=messages)

@app.route('/chats/<sender>')
def get_chat(sender):
    messages = Chat.query.filter_by(sender=sender).order_by(Chat.time).all()
    return jsonify([{
        'sender': msg.sender,
        'text': msg.text,
        'time': msg.time.strftime('%B %d, %H:%M')
    } for msg in messages])
