import os
import logging
from flask import Flask, render_template
from routes import routes
from models import test_db_connection
from flask_cors import CORS

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure Flask app"""
    try:
        app = Flask(__name__)
        app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev')
        
        # Configure CORS properly
        CORS(app, resources={
            r"/*": {
                "origins": "*",
                "methods": ["GET", "POST", "OPTIONS"],
                "allow_headers": ["Content-Type"]
            }
        })
        
        # Set Flask configuration
        app.config.update(
            SEND_FILE_MAX_AGE_DEFAULT=0,
            TEMPLATES_AUTO_RELOAD=True,
            JSON_SORT_KEYS=False,
            MAX_CONTENT_LENGTH=16 * 1024 * 1024,
            CORS_HEADERS='Content-Type'
        )

        # Register error handlers
        @app.errorhandler(404)
        def not_found_error(error):
            return render_template('404.html'), 404

        @app.errorhandler(500)
        def internal_error(error):
            logger.error(f"Internal server error: {error}")
            return render_template('500.html'), 500

        # Register routes blueprint
        app.register_blueprint(routes)
        
        # Test database connection
        if not test_db_connection():
            logger.error("Failed to connect to database")
            raise Exception("Database connection failed")
            
        logger.info("App created successfully")
        return app

    except Exception as e:
        logger.error(f"Error creating app: {str(e)}")
        raise

def run_app(app):
    """Run the Flask application with proper error handling"""
    try:
        port = int(os.environ.get('PORT', 5000))
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise

if __name__ == '__main__':
    try:
        logger.info("Starting Flask application...")
        app = create_app()
        run_app(app)
    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")
        raise
