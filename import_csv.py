import pandas as pd
from app import create_app
from models import db, Chat, SMS, Calls, Contacts, InstalledApps, Keylogs
from datetime import datetime
import os
import logging
import time
from sqlalchemy.exc import OperationalError, IntegrityError
from sqlalchemy import text
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BATCH_SIZE = 50  # Reduced batch size to minimize deadlock risk
MAX_RETRIES = 5  # Increased retries
RETRY_DELAY = 2  # seconds

def create_indexes():
    """Create indexes to improve import performance"""
    try:
        with db.engine.connect() as conn:
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_chat_sender ON chat(sender)",
                "CREATE INDEX IF NOT EXISTS idx_chat_time ON chat(time)",
                "CREATE INDEX IF NOT EXISTS idx_sms_from_to ON sms(from_to)",
                "CREATE INDEX IF NOT EXISTS idx_sms_time ON sms(time)",
                "CREATE INDEX IF NOT EXISTS idx_calls_from_to ON calls(from_to)",
                "CREATE INDEX IF NOT EXISTS idx_calls_time ON calls(time)",
                "CREATE INDEX IF NOT EXISTS idx_keylogs_time ON keylogs(time)",
                "CREATE INDEX IF NOT EXISTS idx_installed_apps_name ON installed_apps(application_name)"
            ]
            
            for index_sql in indexes:
                conn.execute(text(index_sql))
                conn.commit()
            
            logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating indexes: {str(e)}")
        raise

@contextmanager
def transaction_scope():
    """Provide a transactional scope with proper isolation level"""
    connection = db.engine.connect()
    transaction = connection.begin()
    try:
        connection.execute(text("SET TRANSACTION ISOLATION LEVEL READ COMMITTED"))
        yield connection
        transaction.commit()
    except Exception as e:
        transaction.rollback()
        logger.error(f"Transaction error: {str(e)}")
        raise
    finally:
        connection.close()

def import_in_batches(df, model_class, transform_func, table_name):
    """Import data in batches with improved retry logic"""
    total_records = len(df)
    processed = 0
    
    for start_idx in range(0, total_records, BATCH_SIZE):
        end_idx = min(start_idx + BATCH_SIZE, total_records)
        batch_df = df[start_idx:end_idx]
        
        retries = 0
        while retries < MAX_RETRIES:
            try:
                with transaction_scope() as conn:
                    objects = []
                    for _, row in batch_df.iterrows():
                        obj = model_class()
                        for key, value in transform_func(row).items():
                            setattr(obj, key, value)
                        objects.append(obj)
                    
                    db.session.bulk_save_objects(objects)
                    db.session.flush()
                    
                processed += len(batch_df)
                logger.info(f"Imported {processed}/{total_records} records into {table_name}")
                break
                
            except OperationalError as e:
                if "deadlock detected" in str(e).lower():
                    retries += 1
                    logger.warning(f"Deadlock detected, retry {retries}/{MAX_RETRIES} for {table_name}")
                    time.sleep(RETRY_DELAY * retries)  # Exponential backoff
                    db.session.rollback()
                else:
                    logger.error(f"Operational error: {str(e)}")
                    raise
            except Exception as e:
                logger.error(f"Error importing batch: {str(e)}")
                db.session.rollback()
                raise

def import_csv_data():
    app = create_app()
    with app.app_context():
        try:
            create_indexes()
            
            import_configs = [
                ('data/contacts.csv', Contacts, 
                 lambda row: {'name': row['name']}),
                
                ('data/installed_apps.csv', InstalledApps,
                 lambda row: {
                     'application_name': row['application_name'],
                     'package_name': row['package_name'],
                     'install_date': datetime.strptime(row['install_date'], '%Y-%m-%d %H:%M:%S')
                 }),
                
                ('data/chats.csv', Chat,
                 lambda row: {
                     'sender': row['sender'],
                     'text': row['text'],
                     'time': datetime.strptime(row['time'], '%Y-%m-%d %H:%M:%S')
                 }),
                
                ('data/sms.csv', SMS,
                 lambda row: {
                     'from_to': row['from_to'],
                     'text': row['text'],
                     'time': datetime.strptime(row['time'], '%Y-%m-%d %H:%M:%S'),
                     'location': row.get('location')
                 }),
                
                ('data/calls.csv', Calls,
                 lambda row: {
                     'call_type': row['call_type'],
                     'time': datetime.strptime(row['time'], '%Y-%m-%d %H:%M:%S'),
                     'from_to': row['from_to'],
                     'duration': row['duration'],
                     'location': row.get('location')
                 }),
                
                ('data/keylogs.csv', Keylogs,
                 lambda row: {
                     'application': row['application'],
                     'time': datetime.strptime(row['time'], '%Y-%m-%d %H:%M:%S'),
                     'text': row['text']
                 })
            ]
            
            for csv_file, model, transform in import_configs:
                if os.path.exists(csv_file):
                    logger.info(f"Starting import of {csv_file}")
                    df = pd.read_csv(csv_file)
                    import_in_batches(df, model, transform, model.__tablename__)
                else:
                    logger.warning(f"CSV file not found: {csv_file}")
            
            logger.info("CSV import completed successfully")
            
        except Exception as e:
            logger.error(f"Error during import process: {str(e)}")
            raise

if __name__ == '__main__':
    try:
        import_csv_data()
    except Exception as e:
        logger.error(f"Import failed: {str(e)}")
        exit(1)
