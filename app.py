from flask import Flask, render_template, jsonify
import os
from models import db

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ['FLASK_SECRET_KEY']

# Initialize database
db.init_app(app)

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/api/contacts')
def get_contacts():
    # Mock data for now
    contacts = [
        {
            'id': 1,
            'name': 'John Doe',
            'avatar': None,
            'online': True,
            'lastMessage': 'Hey, how are you?'
        },
        {
            'id': 2,
            'name': 'Jane Smith',
            'avatar': None,
            'online': False,
            'lastMessage': 'See you tomorrow!'
        }
    ]
    return jsonify(contacts)

@app.route('/api/messages/<int:contact_id>')
def get_messages(contact_id):
    # Mock data for now
    messages = [
        {
            'id': 1,
            'content': 'Hey, how are you?',
            'sender': 'them',
            'outgoing': False,
            'timestamp': '2024-10-30T10:00:00'
        },
        {
            'id': 2,
            'content': 'I\'m good, thanks! How about you?',
            'sender': 'me',
            'outgoing': True,
            'timestamp': '2024-10-30T10:01:00'
        }
    ]
    return jsonify(messages)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
