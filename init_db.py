from models import init_db, test_db_connection
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    try:
        init_db()
        if test_db_connection():
            logger.info("Database initialized successfully!")
        else:
            logger.error("Database connection test failed")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
