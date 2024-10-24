from flask import Flask
from routes import routes
from models import init_db, test_db_connection
import logging
import os

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev')
    
    # Register blueprints
    app.register_blueprint(routes)
    
    # Test database connection before proceeding
    if not test_db_connection():
        logger.error("Failed to connect to database")
        raise Exception("Database connection failed")
        
    return app

if __name__ == '__main__':
    try:
        logger.info("Starting Flask application...")
        app = create_app()
        logger.info("Application created successfully")
        app.run(host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise
