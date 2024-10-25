import pandas as pd
import logging
from models import get_db_connection
from datetime import datetime
import psycopg2.extras
import psycopg2.extensions
import re
import chardet
import os
import time
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

@contextmanager
def table_lock(conn, table_name):
    """Acquire a lock on a table with improved deadlock handling"""
    max_retries = 3
    retry_delay = 1
    for attempt in range(max_retries):
        try:
            with conn.cursor() as cur:
                # Use less restrictive lock mode
                cur.execute(f"LOCK TABLE {table_name} IN SHARE ROW EXCLUSIVE MODE")
                yield
                break
        except psycopg2.errors.LockNotAvailable:
            if attempt < max_retries - 1:
                logger.warning(f"Lock unavailable for {table_name}, retry {attempt + 1}/{max_retries}")
                time.sleep(retry_delay)
            else:
                raise

def detect_encoding(filename):
    """Detect file encoding using chardet"""
    try:
        if not os.path.exists(filename):
            logger.error(f"File not found: {filename}")
            return None
            
        with open(filename, 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            confidence = result.get('confidence', 0)
            encoding = result.get('encoding', 'utf-8')
            
            logger.info(f"Detected encoding for {filename}: {encoding} (confidence: {confidence:.2%})")
            return encoding if confidence > 0.7 else 'utf-8'
    except Exception as e:
        logger.error(f"Error detecting encoding for {filename}: {str(e)}")
        return 'utf-8'

def read_csv_safe(filename):
    """Read CSV with encoding detection"""
    try:
        if not os.path.exists(filename):
            raise FileNotFoundError(f"File not found: {filename}")
            
        encoding = detect_encoding(filename)
        if not encoding:
            raise ValueError(f"Could not detect encoding for {filename}")
            
        logger.info(f"Reading {filename} with {encoding} encoding")
        
        try:
            df = pd.read_csv(filename, encoding=encoding)
            return df
        except Exception as first_error:
            logger.warning(f"Failed with detected encoding: {str(first_error)}")
            
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            for enc in encodings:
                try:
                    df = pd.read_csv(filename, encoding=enc)
                    logger.info(f"Successfully read with {enc} encoding")
                    return df
                except Exception:
                    continue
                    
            raise ValueError(f"Could not read file with any encoding")
            
    except Exception as e:
        logger.error(f"Error reading file {filename}: {str(e)}")
        raise

def clean_text(text):
    """Clean and validate text data"""
    if pd.isna(text):
        return None
    if not isinstance(text, str):
        text = str(text)
    text = text.strip()
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    text = text.replace('&amp;', '&').replace('&nbsp;', ' ')
    return text

def parse_timestamp(time_str):
    """Parse timestamp with better handling"""
    if pd.isna(time_str):
        return None
    
    try:
        if isinstance(time_str, str):
            time_str = time_str.strip()
            
            if 'Feb 29' in time_str:
                time_str = time_str.replace('Feb 29', 'Feb 28')
            
            formats = [
                '%b %d, %I:%M %p',
                '%Y-%m-%d %H:%M:%S',
                '%m/%d/%Y %I:%M %p',
                '%b %d, %Y %I:%M %p',
                '%Y-%m-%d %H:%M:%S.%f',
                '%m/%d/%y %I:%M %p'
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(time_str, fmt)
                    if dt.year == 1900:
                        dt = dt.replace(year=2024)
                    return dt
                except ValueError:
                    continue
        
        if isinstance(time_str, (pd.Timestamp, datetime)):
            dt = pd.Timestamp(time_str).to_pydatetime()
            if dt.year == 1900:
                dt = dt.replace(year=2024)
            return dt
            
        dt = pd.to_datetime(time_str, errors='coerce')
        if pd.notnull(dt):
            if dt.year == 1900:
                dt = dt.replace(year=2024)
            return dt.to_pydatetime()
        
        return None
        
    except Exception as e:
        logger.warning(f"Error parsing timestamp {time_str}: {str(e)}")
        return None

def import_table_data(conn, df, table_name, transform_func, batch_size=50):
    """Import data with better transaction handling"""
    total_imported = 0
    total_failed = 0
    total_duplicates = 0
    
    try:
        # Start a new transaction
        conn.set_session(isolation_level=psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED)
        
        with conn.cursor() as cur:
            # Get existing count
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            existing_count = cur.fetchone()[0]
            logger.info(f"Found {existing_count} existing records in {table_name}")
            
            # Process in batches
            for i in range(0, len(df), batch_size):
                try:
                    batch = df.iloc[i:i + batch_size]
                    values = []
                    
                    for _, row in batch.iterrows():
                        try:
                            value = transform_func(row)
                            if value and all(v is not None for v in value.values()):
                                values.append(value)
                            else:
                                total_failed += 1
                        except Exception as e:
                            logger.error(f"Transform error: {str(e)}")
                            total_failed += 1
                            continue
                    
                    if values:
                        columns = ','.join(values[0].keys())
                        placeholders = ','.join(['%s'] * len(values[0]))
                        
                        insert_query = f"""
                            INSERT INTO {table_name} ({columns})
                            VALUES ({placeholders})
                            ON CONFLICT DO NOTHING
                        """
                        
                        cur.executemany(insert_query, [tuple(v.values()) for v in values])
                        conn.commit()  # Commit each batch
                        
                        # Count actual inserts
                        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                        new_count = cur.fetchone()[0]
                        inserted = new_count - (total_imported + existing_count)
                        duplicates = len(values) - inserted
                        
                        total_imported += inserted
                        total_duplicates += duplicates
                        
                        logger.info(f"Batch progress: +{inserted}/{len(values)} records "
                                  f"(Duplicates: {duplicates}, Total: {total_imported})")
                                  
                except Exception as e:
                    logger.error(f"Batch error: {str(e)}")
                    conn.rollback()
                    total_failed += len(batch)
                    continue
            
            logger.info(f"\nImport results for {table_name}:")
            logger.info(f"Total processed: {len(df)}")
            logger.info(f"Successfully imported: {total_imported}")
            logger.info(f"Duplicates skipped: {total_duplicates}")
            logger.info(f"Failed records: {total_failed}")
            
            return total_imported > 0
            
    except Exception as e:
        logger.error(f"Import error for {table_name}: {str(e)}")
        conn.rollback()
        return False

def import_all_data():
    """Import all data with improved transaction handling"""
    try:
        logger.info("Starting data import process...")
        
        with get_db_connection() as conn:
            # Use READ COMMITTED isolation
            conn.set_session(isolation_level=psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED)
            
            # Import applications
            logger.info("\nImporting applications...")
            df = read_csv_safe('appex.csv')
            def transform_app(row):
                return {
                    'application_name': clean_text(row.get('Application Name')),
                    'package_name': clean_text(row.get('Package Name')),
                    'installed_date': parse_timestamp(row.get('Installed Date'))
                }
            success = import_table_data(conn, df, 'applications', transform_app)
            if not success:
                raise Exception("Applications import failed")
            
            # Import calls
            logger.info("\nImporting calls...")
            df = read_csv_safe('callex.csv')
            def transform_call(row):
                return {
                    'call_type': clean_text(row.get('Call type')),
                    'call_time': parse_timestamp(row.get('Time')),
                    'from_to': clean_text(row.get('From/To')),
                    'duration': int(''.join(filter(str.isdigit, str(row.get('Duration (Sec)', '0')))) or 0),
                    'location': clean_text(row.get('Location', ''))
                }
            success = import_table_data(conn, df, 'calls', transform_call)
            if not success:
                raise Exception("Calls import failed")
            
            # Import chats
            logger.info("\nImporting chats...")
            df = read_csv_safe('chatex.csv')
            def transform_chat(row):
                return {
                    'messenger': clean_text(row.get('Messenger')),
                    'time': parse_timestamp(row.get('Time')),
                    'sender': clean_text(row.get('Sender')),
                    'recipient': 'user',
                    'text': clean_text(row.get('Text')) or ''
                }
            success = import_table_data(conn, df, 'chats', transform_chat)
            if not success:
                raise Exception("Chats import failed")
            
            # Import contacts
            logger.info("\nImporting contacts...")
            df = read_csv_safe('Contactsex.csv')
            def transform_contact(row):
                return {
                    'name': clean_text(row.get('Name')),
                    'last_message_time': parse_timestamp(row.get('Last Contacted'))
                }
            success = import_table_data(conn, df, 'contacts', transform_contact)
            if not success:
                raise Exception("Contacts import failed")
            
            # Import keylogs
            logger.info("\nImporting keylogs...")
            df = read_csv_safe('keyex.csv')
            def transform_keylog(row):
                return {
                    'application': clean_text(row.get('Application')),
                    'time': parse_timestamp(row.get('Time')),
                    'text': clean_text(row.get('Text')) or ''
                }
            success = import_table_data(conn, df, 'keylogs', transform_keylog)
            if not success:
                raise Exception("Keylogs import failed")
            
            # Import SMS
            logger.info("\nImporting SMS...")
            df = read_csv_safe('smsex.csv')
            def transform_sms(row):
                return {
                    'from_to': clean_text(row.get('From/To')),
                    'text': clean_text(row.get('Text')) or '',
                    'time': parse_timestamp(row.get('Time')),
                    'location': clean_text(row.get('Location', ''))
                }
            success = import_table_data(conn, df, 'sms', transform_sms)
            if not success:
                raise Exception("SMS import failed")
            
            logger.info("All data imported successfully")
            return True
            
    except Exception as e:
        logger.error(f"Import process failed: {str(e)}")
        return False

if __name__ == '__main__':
    success = import_all_data()
    if success:
        logger.info("Data import completed successfully")
    else:
        logger.error("Data import failed")
