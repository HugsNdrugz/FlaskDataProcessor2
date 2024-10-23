import os
from flask import Flask
from routes import routes
from models import db

def create_app():
    app = Flask(__name__)
    
    # Configure database using environment variables
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev')
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(routes)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
        
    return app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
