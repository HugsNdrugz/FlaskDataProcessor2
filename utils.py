import pandas as pd
import chardet
from datetime import datetime
import os
import psycopg2
from psycopg2 import sql
import openpyxl

def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def test_db_connection():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        return "Success"
    except Exception as e:
        return f"Failed: {str(e)}"

def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    
    tables = [
        """
        CREATE TABLE IF NOT EXISTS calls (
            call_id SERIAL PRIMARY KEY,
            contact_id VARCHAR(50),
            call_type VARCHAR(50),
            call_time TIMESTAMP,
            duration INTEGER,
            location TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS contacts (
            contact_id SERIAL PRIMARY KEY,
            contact_name VARCHAR(255),
            phone_number VARCHAR(50),
            email VARCHAR(255)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS sms (
            sms_id SERIAL PRIMARY KEY,
            sender_id VARCHAR(50),
            receiver_id VARCHAR(50),
            message_type VARCHAR(50),
            message_time TIMESTAMP,
            message_text TEXT,
            location TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS applications (
            application_id SERIAL PRIMARY KEY,
            application_name VARCHAR(255),
            package_name VARCHAR(255),
            installed_date TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS keylogs (
            keylog_id SERIAL PRIMARY KEY,
            application_id VARCHAR(50),
            log_time TIMESTAMP,
            keylog_text TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS chats (
            chat_id SERIAL PRIMARY KEY,
            messenger VARCHAR(50),
            time TIMESTAMP,
            sender VARCHAR(50),
            text TEXT
        )
        """
    ]
    
    for table in tables:
        cur.execute(table)
    
    conn.commit()
    cur.close()
    conn.close()

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

def convert_to_utc_safe(time_str, format_str="%b %d, %I:%M %p"):
    try:
        dt = datetime.strptime(time_str, format_str)
        dt = dt.replace(year=datetime.now().year)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

def process_data(df):
    columns = set(df.columns.str.lower())
    
    if 'call type' in columns:
        df['Time'] = df['Time'].apply(lambda x: convert_to_utc_safe(x) if pd.notna(x) else None)
        df['Duration (Sec)'] = pd.to_numeric(df['Duration (Sec)'].str.replace(' Sec', ''), errors='coerce').fillna(0).astype(int)
        return 'calls', df
    elif 'name' in columns and 'phone number' in columns:
        df['Phone Number'] = df['Phone Number'].str.replace(r'\D', '', regex=True)
        df['Email Id'].fillna("not_available@example.com", inplace=True)
        return 'contacts', df
    elif 'sms type' in columns:
        df['Time'] = df['Time'].apply(lambda x: convert_to_utc_safe(x) if pd.notna(x) else None)
        return 'sms', df
    elif 'application name' in columns:
        df['Installed Date'] = df['Installed Date'].apply(lambda x: convert_to_utc_safe(x) if pd.notna(x) else None)
        return 'applications', df
    elif 'application' in columns and 'text' in columns:
        df['Time'] = df['Time'].apply(lambda x: convert_to_utc_safe(x) if pd.notna(x) else None)
        return 'keylogs', df
    elif 'messenger' in columns:
        df['Time'] = df['Time'].apply(lambda x: convert_to_utc_safe(x) if pd.notna(x) else None)
        return 'chats', df
    else:
        raise ValueError("Unknown file type")

def insert_data(table_name, df):
    conn = get_db_connection()
    cur = conn.cursor()
    
    columns = df.columns.tolist()
    values = [tuple(x) for x in df.to_numpy()]
    
    insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
        sql.Identifier(table_name),
        sql.SQL(', ').join(map(sql.Identifier, columns)),
        sql.SQL(', ').join(sql.Placeholder() * len(columns))
    )
    
    cur.executemany(insert_query, values)
    conn.commit()
    cur.close()
    conn.close()

def process_and_insert_data(file_path):
    try:
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == '.csv':
            encoding = detect_encoding(file_path)
            df = pd.read_csv(file_path, encoding=encoding)
        elif file_extension in ('.xlsx', '.xls'):
            df = pd.read_excel(file_path, engine='openpyxl')
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        table_name, processed_df = process_data(df)
        insert_data(table_name, processed_df)
        print(f"Successfully processed and inserted data from {file_path}")
    except Exception as e:
        raise Exception(f"Error processing file {file_path}: {str(e)}")