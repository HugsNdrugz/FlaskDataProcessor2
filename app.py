from flask import Flask
from routes import routes
from models import init_db, test_db_connection
import logging
import os

logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev')
    
    # Register blueprints
    app.register_blueprint(routes)
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully!")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise
        
    return app

if __name__ == '__main__':
    try:
        app = create_app()
        if test_db_connection():
            app.run(host='0.0.0.0', port=5000)
        else:
            logger.error("Failed to connect to database. Exiting.")
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
