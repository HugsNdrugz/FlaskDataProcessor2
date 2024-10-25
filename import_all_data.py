import pandas as pd
import logging
from models import get_db_connection
from datetime import datetime
import psycopg2.extras
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clean_text(text):
    """Clean and validate text data"""
    if pd.isna(text):
        return None
    return str(text).strip()

def parse_timestamp(time_str):
    """Parse timestamp with better handling"""
    if pd.isna(time_str):
        return None
        
    try:
        if isinstance(time_str, str):
            # Handle Feb 29 cases first
            if 'Feb 29' in time_str:
                time_str = time_str.replace('Feb 29', 'Feb 28')
            
            # Try parsing with common formats
            formats = [
                '%b %d, %I:%M %p',
                '%Y-%m-%d %H:%M:%S',
                '%m/%d/%Y %I:%M %p'
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(time_str, fmt)
                    # If year is 1900, set it to 2024
                    if dt.year == 1900:
                        dt = dt.replace(year=2024)
                    return dt
                except ValueError:
                    continue
                    
        # Try pandas timestamp parsing as fallback
        dt = pd.to_datetime(time_str)
        if dt.year == 1900:
            dt = dt.replace(year=2024)
        return dt
        
    except Exception as e:
        logger.warning(f"Error parsing timestamp {time_str}: {str(e)}")
        return None

def validate_data(df, required_columns):
    """Validate dataframe structure and content"""
    # Check required columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        
    # Remove rows with all NaN values
    df = df.dropna(how='all')
    
    # Remove rows where required columns are NaN
    df = df.dropna(subset=required_columns)
    
    return df

def import_applications():
    """Import applications data"""
    try:
        df = pd.read_csv('appex.csv')
        logger.info(f"Reading applications data: {len(df)} rows")
        
        df = validate_data(df, ['Application Name', 'Package Name', 'Installed Date'])
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                for _, row in df.iterrows():
                    try:
                        cur.execute("""
                            INSERT INTO applications (application_name, package_name, installed_date)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (package_name) DO UPDATE SET
                                application_name = EXCLUDED.application_name,
                                installed_date = EXCLUDED.installed_date
                        """, (
                            clean_text(row['Application Name']),
                            clean_text(row['Package Name']),
                            parse_timestamp(row['Installed Date'])
                        ))
                    except Exception as e:
                        logger.error(f"Error importing application row: {str(e)}")
                        continue
        logger.info("Applications data imported successfully")
        return True
    except Exception as e:
        logger.error(f"Error importing applications data: {str(e)}")
        return False

def import_calls():
    """Import call logs"""
    try:
        df = pd.read_csv('callex.csv')
        logger.info(f"Reading call logs: {len(df)} rows")
        
        df = validate_data(df, ['Call type', 'Time', 'From/To'])
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                for _, row in df.iterrows():
                    try:
                        cur.execute("""
                            INSERT INTO calls (call_type, call_time, from_to, duration, location)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (
                            clean_text(row['Call type']),
                            parse_timestamp(row['Time']),
                            clean_text(row['From/To']),
                            clean_text(row['Duration (Sec)']),
                            clean_text(row.get('Location'))
                        ))
                    except Exception as e:
                        logger.error(f"Error importing call row: {str(e)}")
                        continue
        logger.info("Call logs imported successfully")
        return True
    except Exception as e:
        logger.error(f"Error importing call logs: {str(e)}")
        return False

def import_chats():
    """Import chat messages"""
    try:
        df = pd.read_csv('chatex.csv')
        logger.info(f"Reading chat messages: {len(df)} rows")
        
        df = validate_data(df, ['Messenger', 'Time', 'Sender', 'Text'])
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                for _, row in df.iterrows():
                    try:
                        cur.execute("""
                            INSERT INTO chats (messenger, time, sender, recipient, text)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (
                            clean_text(row['Messenger']),
                            parse_timestamp(row['Time']),
                            clean_text(row['Sender']),
                            'user',  # Set recipient as 'user'
                            clean_text(row['Text'])
                        ))
                    except Exception as e:
                        logger.error(f"Error importing chat row: {str(e)}")
                        continue
        logger.info("Chat messages imported successfully")
        return True
    except Exception as e:
        logger.error(f"Error importing chat messages: {str(e)}")
        return False

def import_contacts():
    """Import contacts"""
    try:
        df = pd.read_csv('Contactsex.csv')
        logger.info(f"Reading contacts: {len(df)} rows")
        
        df = validate_data(df, ['Name'])
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                for _, row in df.iterrows():
                    try:
                        cur.execute("""
                            INSERT INTO contacts (name, last_message_time)
                            VALUES (%s, %s)
                            ON CONFLICT (name) DO UPDATE SET
                                last_message_time = EXCLUDED.last_message_time
                        """, (
                            clean_text(row['Name']),
                            parse_timestamp(row['Last Contacted'])
                        ))
                    except Exception as e:
                        logger.error(f"Error importing contact row: {str(e)}")
                        continue
        logger.info("Contacts imported successfully")
        return True
    except Exception as e:
        logger.error(f"Error importing contacts: {str(e)}")
        return False

def import_keylogs():
    """Import keylog data"""
    try:
        df = pd.read_csv('keyex.csv')
        logger.info(f"Reading keylogs: {len(df)} rows")
        
        df = validate_data(df, ['Application', 'Time', 'Text'])
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                for _, row in df.iterrows():
                    try:
                        cur.execute("""
                            INSERT INTO keylogs (application, time, text)
                            VALUES (%s, %s, %s)
                        """, (
                            clean_text(row['Application']),
                            parse_timestamp(row['Time']),
                            clean_text(row['Text'])
                        ))
                    except Exception as e:
                        logger.error(f"Error importing keylog row: {str(e)}")
                        continue
        logger.info("Keylogs imported successfully")
        return True
    except Exception as e:
        logger.error(f"Error importing keylogs: {str(e)}")
        return False

def import_sms():
    """Import SMS messages"""
    try:
        df = pd.read_csv('smsex.csv')
        logger.info(f"Reading SMS messages: {len(df)} rows")
        
        df = validate_data(df, ['From/To', 'Text', 'Time'])
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                for _, row in df.iterrows():
                    try:
                        cur.execute("""
                            INSERT INTO sms (from_to, text, time, location)
                            VALUES (%s, %s, %s, %s)
                        """, (
                            clean_text(row['From/To']),
                            clean_text(row['Text']),
                            parse_timestamp(row['Time']),
                            clean_text(row.get('Location'))
                        ))
                    except Exception as e:
                        logger.error(f"Error importing SMS row: {str(e)}")
                        continue
        logger.info("SMS messages imported successfully")
        return True
    except Exception as e:
        logger.error(f"Error importing SMS messages: {str(e)}")
        return False

if __name__ == '__main__':
    try:
        # Import all data
        results = {
            'applications': import_applications(),
            'calls': import_calls(),
            'chats': import_chats(),
            'contacts': import_contacts(),
            'keylogs': import_keylogs(),
            'sms': import_sms()
        }
        
        # Log summary
        logger.info("\nImport Summary:")
        for table, success in results.items():
            logger.info(f"{table}: {'Success' if success else 'Failed'}")
        
        # Verify row counts
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                for table in results.keys():
                    cur.execute(f'SELECT COUNT(*) FROM {table}')
                    count = cur.fetchone()[0]
                    logger.info(f"{table} count: {count} rows")
                    
    except Exception as e:
        logger.error(f"Import process failed: {str(e)}")
