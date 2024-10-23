from flask import render_template
from app import app, db
from models import Chat, SMS
from sqlalchemy import desc

@app.route('/')
def index():
    messages = Chat.query.order_by(desc(Chat.time)).all()
    # For demo purposes, set current_user as 'Alice'
    current_user = 'Alice'
    return render_template('index.html', messages=messages, current_user=current_user)

@app.route('/chats')
def chats():
    messages = Chat.query.order_by(desc(Chat.time)).all()
    return render_template('chats.html', messages=messages)

@app.route('/sms')
def sms():
    messages = SMS.query.order_by(desc(SMS.time)).all()
    return render_template('sms.html', messages=messages)
