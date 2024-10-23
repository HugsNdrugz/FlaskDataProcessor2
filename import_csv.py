import pandas as pd
from app import create_app
from models import db, Chat, SMS, Calls, Contacts, InstalledApps, Keylogs
from datetime import datetime
import os
import logging
import time
from sqlalchemy.exc import OperationalError, IntegrityError
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BATCH_SIZE = 100
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

@contextmanager
def transaction_scope():
    """Provide a transactional scope around a series of operations."""
    try:
        yield
        db.session.commit()
    except Exception as e:
        logger.error(f"Error in transaction: {str(e)}")
        db.session.rollback()
        raise

def import_in_batches(df, model_class, transform_func, table_name):
    """Import data in batches with retry logic"""
    total_records = len(df)
    processed = 0
    
    for start_idx in range(0, total_records, BATCH_SIZE):
        end_idx = min(start_idx + BATCH_SIZE, total_records)
        batch_df = df[start_idx:end_idx]
        
        retries = 0
        while retries < MAX_RETRIES:
            try:
                with transaction_scope():
                    for _, row in batch_df.iterrows():
                        db.session.add(transform_func(row))
                    processed += len(batch_df)
                    logger.info(f"Imported {processed}/{total_records} records into {table_name}")
                break
            except OperationalError as e:
                if "deadlock detected" in str(e):
                    retries += 1
                    if retries < MAX_RETRIES:
                        logger.warning(f"Deadlock detected, retry {retries}/{MAX_RETRIES} for {table_name}")
                        time.sleep(RETRY_DELAY)
                    else:
                        logger.error(f"Max retries reached for {table_name} batch")
                        raise
                else:
                    raise

def import_csv_data():
    app = create_app()
    with app.app_context():
        try:
            # Import order: smaller tables first
            # 1. Contacts
            if os.path.exists('data/contacts.csv'):
                logger.info("Starting import of contacts")
                contacts_df = pd.read_csv('data/contacts.csv')
                import_in_batches(
                    contacts_df,
                    Contacts,
                    lambda row: Contacts(name=row['name']),
                    'contacts'
                )

            # 2. Installed Apps
            if os.path.exists('data/installed_apps.csv'):
                logger.info("Starting import of installed apps")
                apps_df = pd.read_csv('data/installed_apps.csv')
                import_in_batches(
                    apps_df,
                    InstalledApps,
                    lambda row: InstalledApps(
                        application_name=row['application_name'],
                        package_name=row['package_name'],
                        install_date=datetime.strptime(row['install_date'], '%Y-%m-%d %H:%M:%S')
                    ),
                    'installed_apps'
                )

            # 3. Chat messages
            if os.path.exists('data/chats.csv'):
                logger.info("Starting import of chat messages")
                chats_df = pd.read_csv('data/chats.csv')
                import_in_batches(
                    chats_df,
                    Chat,
                    lambda row: Chat(
                        sender=row['sender'],
                        text=row['text'],
                        time=datetime.strptime(row['time'], '%Y-%m-%d %H:%M:%S')
                    ),
                    'chat'
                )

            # 4. SMS messages
            if os.path.exists('data/sms.csv'):
                logger.info("Starting import of SMS messages")
                sms_df = pd.read_csv('data/sms.csv')
                import_in_batches(
                    sms_df,
                    SMS,
                    lambda row: SMS(
                        from_to=row['from_to'],
                        text=row['text'],
                        time=datetime.strptime(row['time'], '%Y-%m-%d %H:%M:%S'),
                        location=row.get('location')
                    ),
                    'sms'
                )

            # 5. Calls
            if os.path.exists('data/calls.csv'):
                logger.info("Starting import of calls")
                calls_df = pd.read_csv('data/calls.csv')
                import_in_batches(
                    calls_df,
                    Calls,
                    lambda row: Calls(
                        call_type=row['call_type'],
                        time=datetime.strptime(row['time'], '%Y-%m-%d %H:%M:%S'),
                        from_to=row['from_to'],
                        duration=row['duration'],
                        location=row.get('location')
                    ),
                    'calls'
                )

            # 6. Keylogs (last due to size and complexity)
            if os.path.exists('data/keylogs.csv'):
                logger.info("Starting import of keylogs")
                keylogs_df = pd.read_csv('data/keylogs.csv')
                import_in_batches(
                    keylogs_df,
                    Keylogs,
                    lambda row: Keylogs(
                        application=row['application'],
                        time=datetime.strptime(row['time'], '%Y-%m-%d %H:%M:%S'),
                        text=row['text']
                    ),
                    'keylogs'
                )

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
