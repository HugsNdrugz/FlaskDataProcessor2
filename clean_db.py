import logging
from models import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_database():
    """Clean up database by dropping duplicate/conflicting tables"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Drop all existing tables
                tables_to_drop = [
                    'chat', 'message', 'messages', 'conversation',
                    'user', 'installed_apps'
                ]
                
                for table in tables_to_drop:
                    cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                    logger.info(f"Dropped table: {table}")
                
                logger.info("Database cleanup completed successfully")
                return True
    except Exception as e:
        logger.error(f"Database cleanup failed: {str(e)}")
        return False

if __name__ == '__main__':
    clean_database()
