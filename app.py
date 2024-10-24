import os
from flask import Flask
from routes import routes
from models import db, test_db_connection, init_db_settings
import logging

logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # Configure database
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

    # Initialize database
    with app.app_context():
        try:
            db.create_all()
            init_db_settings(app)
            logger.info("Database initialized successfully!")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
        
    return app

if __name__ == '__main__':
    try:
        app = create_app()
        if test_db_connection(app):
            app.run(host='0.0.0.0', port=5000)
        else:
            logger.error("Failed to connect to database. Exiting.")
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
