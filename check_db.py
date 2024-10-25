import logging
from models import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_db_status():
    """Check database connection and table status"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check database connection
                cur.execute('SELECT version()')
                version = cur.fetchone()
                logger.info(f"Database version: {version[0]}")
                
                # Check table existence and structure
                cur.execute("""
                    SELECT table_name, column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public'
                    ORDER BY table_name, ordinal_position
                """)
                tables = cur.fetchall()
                
                if not tables:
                    logger.error("No tables found in database")
                    return False
                    
                logger.info("Database tables and columns:")
                current_table = None
                for table in tables:
                    if current_table != table[0]:
                        current_table = table[0]
                        logger.info(f"\nTable: {current_table}")
                    logger.info(f"  - {table[1]} ({table[2]})")
                
                return True
                
    except Exception as e:
        logger.error(f"Database check failed: {str(e)}")
        return False

if __name__ == '__main__':
    check_db_status()
