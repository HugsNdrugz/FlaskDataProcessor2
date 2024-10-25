import logging
from models import get_db_connection
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_import(max_retries=3, retry_delay=5):
    """Check import status with retries and detailed reporting"""
    # Map of table names to their primary key columns
    pk_columns = {
        'applications': 'application_id',
        'calls': 'id',
        'chats': 'id',
        'contacts': 'id',
        'keylogs': 'id',
        'sms': 'id'
    }
    
    for attempt in range(max_retries):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check row counts and constraints for each table
                    tables = ['applications', 'calls', 'chats', 'contacts', 'keylogs', 'sms']
                    results = {}
                    
                    for table in tables:
                        # Check total count
                        cur.execute(f'SELECT COUNT(*) FROM {table}')
                        count = cur.fetchone()[0]
                        
                        # Get primary key column for this table
                        pk_col = pk_columns[table]
                        
                        # Check for NULL values in critical columns
                        cur.execute(f"""
                            SELECT COUNT(*) 
                            FROM {table} 
                            WHERE {pk_col} IS NULL
                        """)
                        null_count = cur.fetchone()[0]
                        
                        results[table] = {
                            'total_rows': count,
                            'null_ids': null_count
                        }
                        
                        logger.info(f"{table}: {count} rows (Invalid records: {null_count})")
                    
                    # Verify data integrity
                    success = all(r['total_rows'] > 0 and r['null_ids'] == 0 
                                for r in results.values())
                    
                    if success:
                        logger.info("Import verification successful!")
                        return True
                    elif attempt < max_retries - 1:
                        logger.warning(f"Verification incomplete, retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        logger.error("Import verification failed after retries")
                        return False
                        
        except Exception as e:
            logger.error(f'Error checking tables: {str(e)}')
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                return False

if __name__ == '__main__':
    success = check_import()
    logger.info(f'Import verification {"successful" if success else "failed"}')
