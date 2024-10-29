import os
from flask import Flask
from models import init_db
from routes import bp

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default-secret-key')

# Register blueprints
app.register_blueprint(bp)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
