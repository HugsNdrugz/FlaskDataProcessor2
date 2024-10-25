import logging
from models import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_import():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check row counts for each table
                tables = ['applications', 'calls', 'chats', 'contacts', 'keylogs', 'sms']
                results = {}
                for table in tables:
                    cur.execute(f'SELECT COUNT(*) FROM {table}')
                    count = cur.fetchone()[0]
                    results[table] = count
                    logger.info(f'{table}: {count} rows')
                return all(count > 0 for count in results.values())
    except Exception as e:
        logger.error(f'Error checking tables: {str(e)}')
        return False

if __name__ == '__main__':
    success = check_import()
    logger.info(f'Import verification {"successful" if success else "failed"}')
