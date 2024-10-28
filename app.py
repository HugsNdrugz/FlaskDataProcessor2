from flask import Flask
from flask_cors import CORS
from routes import routes
from models import init_db, test_db_connection
import logging
import os

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure Flask application"""
    try:
        app = Flask(__name__)
        
        # Enable CORS with additional configuration
        CORS(app, resources={r"/*": {"origins": "*", "allow_headers": "*", "expose_headers": "*"}})
        app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev')
        
        # Test database connection before registering blueprints
        if not test_db_connection():
            logger.error("Failed to connect to database")
            raise Exception("Database connection failed")
            
        # Register blueprints
        app.register_blueprint(routes)
        
        @app.before_request
        def before_request():
            """Ensure database connection is available"""
            if not test_db_connection():
                logger.error("Database connection lost")
                return {'error': 'Database connection error'}, 503
        
        @app.errorhandler(404)
        def not_found_error(error):
            logger.warning(f"404 error: {str(error)}")
            return {'error': 'Not found'}, 404

        @app.errorhandler(500)
        def internal_error(error):
            logger.error(f"500 error: {str(error)}")
            return {'error': 'Internal server error'}, 500
        
        @app.after_request
        def after_request(response):
            """Add CORS headers"""
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
            return response
            
        return app
        
    except Exception as e:
        logger.error(f"Error creating application: {str(e)}")
        raise

def main():
    try:
        logger.info("Starting Flask application...")
        app = create_app()
        logger.info("Application created successfully")
        
        # Ensure proper host binding and port configuration
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise

if __name__ == '__main__':
    main()
