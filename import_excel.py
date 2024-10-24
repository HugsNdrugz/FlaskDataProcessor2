import pandas as pd
from models import get_db_connection
import logging
from datetime import datetime
import psycopg2.extras

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clean_text(text):
    """Clean and validate text data"""
    if pd.isna(text) or text == '':
        return None
    return str(text).strip()

def parse_timestamp(time_str):
    """Parse timestamp from Excel format with better error handling"""
    try:
        if pd.isna(time_str):
            return None
            
        # Handle February 29th cases
        if isinstance(time_str, str) and 'Feb 29' in time_str:
            # Replace Feb 29 with Feb 28
            time_str = time_str.replace('Feb 29', 'Feb 28')
            
        # Handle AM/PM format
        if isinstance(time_str, str):
            return datetime.strptime(time_str, '%b %d, %I:%M %p')
        return pd.to_datetime(time_str)
    except Exception as e:
        logger.warning(f"Error parsing timestamp {time_str}, using Feb 28: {str(e)}")
        try:
            # Second attempt with Feb 28
            if isinstance(time_str, str) and 'Feb 29' in time_str:
                modified_str = time_str.replace('Feb 29', 'Feb 28')
                return datetime.strptime(modified_str, '%b %d, %I:%M %p')
        except Exception as e2:
            logger.error(f"Failed second parsing attempt: {str(e2)}")
        return None

def is_duplicate(cur, sender, time):
    """Check if a message already exists"""
    cur.execute('''
        SELECT EXISTS(
            SELECT 1 FROM chats 
            WHERE sender = %s AND time = %s
        )
    ''', (sender, time))
    return cur.fetchone()[0]

def setup_database():
    """Set up database constraints and indexes"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Create unique index for preventing duplicates
                cur.execute("""
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_chats_sender_time 
                    ON chats(sender, time) 
                    WHERE sender IS NOT NULL AND time IS NOT NULL
                """)
                logger.info("Database constraints and indexes created successfully")
    except Exception as e:
        logger.error(f"Error setting up database: {str(e)}")
        raise

def import_excel_data(filename='Tracking Smartphone - Free Remote Monitoring Tool For Android (11).xlsx'):
    """Import chat data from Excel file into the database"""
    try:
        # Set up database constraints first
        setup_database()
        
        # Read the Excel file
        logger.info(f"Reading Excel file: {filename}")
        df = pd.read_excel(filename, skiprows=1)  # Skip the header row
        logger.info(f"Read {len(df)} rows from Excel file")
        
        # Rename columns to match expected format
        df.columns = ['messenger', 'time', 'sender', 'text'] + ['unused' + str(i) for i in range(len(df.columns)-4)]
        
        # Clean and validate data
        df['text'] = df['text'].apply(clean_text)
        df['sender'] = df['sender'].apply(clean_text)
        df['time'] = df['time'].apply(parse_timestamp)
        df['messenger'] = df['messenger'].apply(clean_text)
        
        # Remove rows with missing essential data
        df = df.dropna(subset=['sender', 'text', 'time'])
        logger.info(f"After cleaning, {len(df)} valid rows remaining")
        
        # Use batch processing for better performance
        batch_size = 1000
        total_imported = 0
        duplicates_found = 0
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                for i in range(0, len(df), batch_size):
                    batch = df.iloc[i:i+batch_size]
                    
                    # Convert batch to list of tuples
                    values = []
                    for _, row in batch.iterrows():
                        if not is_duplicate(cur, row['sender'], row['time']):
                            values.append((
                                row['messenger'],
                                row['time'],
                                row['sender'],
                                'user',  # Set recipient as 'user' for all messages
                                row['text']
                            ))
                        else:
                            duplicates_found += 1
                    
                    if values:
                        # Insert batch using UPSERT with the unique constraint
                        cur.executemany("""
                            INSERT INTO chats (messenger, time, sender, recipient, text)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (sender, time) 
                            WHERE sender IS NOT NULL AND time IS NOT NULL
                            DO NOTHING
                        """, values)
                        
                        total_imported += len(values)
                        logger.info(f"Imported {total_imported}/{len(df)} records")
                
                # Verify import
                cur.execute("SELECT COUNT(*) FROM chats")
                count = cur.fetchone()[0]
                logger.info(f"Total records in database after import: {count}")
                logger.info(f"Duplicates found and skipped: {duplicates_found}")
                
        return total_imported
        
    except pd.errors.EmptyDataError:
        logger.error("Excel file is empty")
        raise
    except pd.errors.ParserError as e:
        logger.error(f"Error parsing Excel file: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error importing Excel data: {str(e)}")
        raise

if __name__ == '__main__':
    try:
        total_imported = import_excel_data()
        logger.info(f"Successfully imported {total_imported} records")
    except Exception as e:
        logger.error(f"Import failed: {str(e)}")
