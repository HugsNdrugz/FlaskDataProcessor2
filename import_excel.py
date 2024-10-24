import pandas as pd
from models import get_db_connection
import logging
from datetime import datetime
import psycopg2.extras
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_excel_structure(df):
    """Validate Excel file structure and content"""
    try:
        # Extract metadata from first row
        metadata = df.iloc[0, 0]  # First cell of first row
        if not isinstance(metadata, str) or 'Tracking Smartphone' not in metadata:
            logger.warning("First row doesn't contain expected app metadata")
            
        # Get actual headers from second row
        headers = df.iloc[1].tolist()
        logger.info(f"Found headers: {headers}")
        
        # Required columns (case-insensitive check)
        required_columns = ['messenger', 'time', 'sender', 'text']
        found_columns = [str(h).strip().lower() for h in headers if pd.notna(h)]
        
        # Check for missing columns
        missing_columns = []
        for required in required_columns:
            if required not in found_columns:
                missing_columns.append(required.capitalize())
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Validate data rows (starting from third row)
        data_rows = df.iloc[2:]
        if len(data_rows) == 0:
            raise ValueError("No data rows found after headers")
            
        logger.info(f"Excel structure validated. Found {len(data_rows)} data rows")
        return True
        
    except Exception as e:
        logger.error(f"Excel structure validation failed: {str(e)}")
        raise

def clean_text(text):
    """Clean and validate text data"""
    if pd.isna(text):
        return None
    return str(text).strip()

def parse_timestamp(time_str):
    """Parse timestamp with better handling of February dates"""
    if pd.isna(time_str):
        return None
        
    try:
        if isinstance(time_str, str):
            # Handle Feb 29 cases
            if 'Feb 29' in time_str:
                # Extract time portion
                time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM))', time_str)
                if time_match:
                    time_part = time_match.group(1)
                    # Replace with Feb 28
                    modified_str = time_str.replace('Feb 29', 'Feb 28')
                    try:
                        return datetime.strptime(modified_str, '%b %d, %I:%M %p')
                    except ValueError:
                        logger.warning(f"Failed to parse modified date: {modified_str}")
            
            # Try common formats
            formats = [
                '%b %d, %I:%M %p',
                '%Y-%m-%d %H:%M:%S',
                '%m/%d/%Y %I:%M %p'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(time_str, fmt)
                except ValueError:
                    continue
                    
        return pd.to_datetime(time_str)
        
    except Exception as e:
        logger.warning(f"Error parsing timestamp {time_str}: {str(e)}")
        return None

def process_excel_data(df):
    """Process Excel data with proper header handling"""
    try:
        # Get headers from second row
        headers = df.iloc[1].tolist()
        
        # Create a new dataframe with data from third row onwards
        data_df = pd.DataFrame(df.iloc[2:].values, columns=headers)
        
        # Clean and validate data
        data_df['Text'] = data_df['Text'].apply(clean_text)
        data_df['Sender'] = data_df['Sender'].apply(clean_text)
        data_df['Time'] = data_df['Time'].apply(parse_timestamp)
        data_df['Messenger'] = data_df['Messenger'].apply(clean_text)
        
        # Remove rows with missing essential data
        data_df = data_df.dropna(subset=['Sender', 'Text', 'Time'])
        
        logger.info(f"Processed {len(data_df)} valid data rows")
        return data_df
        
    except Exception as e:
        logger.error(f"Error processing Excel data: {str(e)}")
        raise

def import_excel_data(filename='Tracking Smartphone - Free Remote Monitoring Tool For Android (11).xlsx'):
    """Import Excel data with proper metadata handling"""
    try:
        logger.info(f"Reading Excel file: {filename}")
        # Read Excel file without using any row as header
        df = pd.read_excel(filename, header=None)
        
        # Validate structure first
        validate_excel_structure(df)
        
        # Extract metadata
        metadata = {
            'app_name': str(df.iloc[0, 0]),  # First cell of first row
            'total_rows': len(df) - 2,  # Exclude metadata and header rows
            'import_time': datetime.now()
        }
        
        # Process the data
        processed_df = process_excel_data(df)
        
        total_imported = 0
        duplicates_found = 0
        batch_size = 1000
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Process in batches
                for i in range(0, len(processed_df), batch_size):
                    batch = processed_df.iloc[i:i + batch_size]
                    values = []
                    
                    for _, row in batch.iterrows():
                        # Skip invalid rows
                        if pd.isna(row['Time']) or pd.isna(row['Sender']):
                            continue
                            
                        # Check for duplicates
                        cur.execute(
                            "SELECT EXISTS(SELECT 1 FROM chats WHERE sender = %s AND time = %s)",
                            (row['Sender'], row['Time'])
                        )
                        
                        if not cur.fetchone()[0]:  # Not a duplicate
                            values.append((
                                row['Messenger'],
                                row['Time'],
                                row['Sender'],
                                'user',  # Set recipient as 'user'
                                row['Text']
                            ))
                        else:
                            duplicates_found += 1
                    
                    if values:
                        cur.executemany("""
                            INSERT INTO chats (messenger, time, sender, recipient, text)
                            VALUES (%s, %s, %s, %s, %s)
                        """, values)
                        
                        total_imported += len(values)
                        logger.info(f"Imported {total_imported} records")
                
                # Log import summary
                summary = f"""
                Import Summary:
                - Total rows in file: {len(processed_df)}
                - Successfully imported: {total_imported}
                - Duplicates found: {duplicates_found}
                - App name: {metadata['app_name']}
                - Import time: {metadata['import_time']}
                """
                logger.info(summary)
                
        return total_imported, metadata
        
    except Exception as e:
        logger.error(f"Error importing Excel data: {str(e)}")
        raise

if __name__ == '__main__':
    try:
        total_imported, metadata = import_excel_data()
        logger.info(f"Successfully imported {total_imported} records")
    except Exception as e:
        logger.error(f"Import failed: {str(e)}")
