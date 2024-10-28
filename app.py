import os
import logging
from flask import Flask, render_template, request
from flask_cors import CORS
from flask_socketio import SocketIO
from routes import routes
from models import test_db_connection, get_db_connection

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
    
    # Configure CORS
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
    
    @app.after_request
    def after_request(response):
        """Add CORS headers"""
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        return response

    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500
        
    # SocketIO event handlers
    @socketio.on('connect')
    def handle_connect():
        logger.info('Client connected')

    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info('Client disconnected')

    @socketio.on('join')
    def handle_join(data):
        room = data.get('contact')
        if room:
            socketio.join_room(room)
            logger.info(f'Client joined room: {room}')

    @socketio.on('leave')
    def handle_leave(data):
        room = data.get('contact')
        if room:
            socketio.leave_room(room)
            logger.info(f'Client left room: {room}')

    return app, socketio

def init_app():
    """Initialize the full application"""
    app, socketio = create_app()
    
    # Register routes blueprint
    app.register_blueprint(routes)
    
    # Test database connection
    with app.app_context():
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
        app, socketio = init_app()
        
        port = int(os.environ.get('PORT', 5000))
        socketio.run(
            app,
            host='0.0.0.0',
            port=port,
            debug=False
        )
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise
