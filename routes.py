from flask import render_template
from app import app, db
from models import Chat, SMS
from sqlalchemy import desc

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chats')
def chats():
    messages = Chat.query.order_by(desc(Chat.time)).all()
    return render_template('chats.html', messages=messages)

@app.route('/sms')
def sms():
    messages = SMS.query.order_by(desc(SMS.time)).all()
    return render_template('sms.html', messages=messages)
