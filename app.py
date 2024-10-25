import os
import logging
from flask import Flask, render_template
from flask_socketio import SocketIO
from routes import routes
from models import test_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure Flask app"""
    app = Flask(__name__)
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev')
    
    # Initialize SocketIO with simplified settings
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='threading',
        logger=True,
        engineio_logger=True
    )
    
    # Enable CORS
    @app.after_request
    def after_request(response):
        response.headers.update({
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET, POST',
            'Cache-Control': 'no-cache'
        })
        return response

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500
    
    # Register routes blueprint
    app.register_blueprint(routes)
    
    # Test database connection
    try:
        if not test_db_connection():
            logger.error("Failed to connect to database")
            raise Exception("Database connection failed")
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise

    return app, socketio

if __name__ == '__main__':
    try:
        logger.info("Starting Flask application...")
        app, socketio = create_app()
        
        port = int(os.environ.get('PORT', 5000))
        socketio.run(
            app,
            host='0.0.0.0',
            port=port,
            debug=False,  # Disable debug mode
            log_output=True
        )
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise
