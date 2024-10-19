import pandas as pd
import chardet
from datetime import datetime
import os
import psycopg2
from psycopg2 import sql

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result.get('encoding', 'utf-8')

def convert_to_utc_safe(time_str, format_str="%b %d, %I:%M %p"):
    try:
        dt = datetime.strptime(time_str, format_str)
        dt = dt.replace(year=datetime.now().year)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return datetime(datetime.now().year, 2, 28, 23, 59).strftime("%Y-%m-%d %H:%M:%S")

def detect_file_type(df):
    columns = set(df.columns.str.lower())
    if 'call type' in columns:
        return 'calls'
    elif 'name' in columns and 'phone number' in columns:
        return 'contacts'
    elif 'sms type' in columns:
        return 'sms'
    elif 'application name' in columns and 'package name' in columns and 'installed date' in columns:
        return 'applications'
    elif 'application' in columns and 'text' in columns:
        return 'keylogs'
    elif 'time' in columns and 'sender' in columns and 'text' in columns:
        return 'chats'
    return None

def process_data(data):
    columns = set(data.columns.str.lower())

    if 'sms type' in columns:
        print('Processing as SMS...')
        data = data.copy()
        data.rename(columns={
            'SMS type': 'message_type',
            'Time': 'message_time',
            'From/To': 'sender_receiver',
            'Text': 'message_text',
            'Location': 'location'
        }, inplace=True)
        data['message_time'] = data['message_time'].apply(lambda x: convert_to_utc_safe(x) if pd.notna(x) else None)
        data['sender_id'] = data['sender_receiver'].str.split(',').str[0]
        data['receiver_id'] = data['sender_receiver'].str.split(',').str[-1]
        data.drop('sender_receiver', axis=1, inplace=True)
        data.fillna('Unknown', inplace=True)
        return data[['sender_id', 'receiver_id', 'message_type', 'message_time', 'message_text', 'location']]

    elif 'call type' in columns:
        print("Processing as Calls...")
        data = data.copy()
        data.rename(columns={
            'Call type': 'call_type',
            'Time': 'call_time',
            'From/To': 'contact_id',
            'Duration (Sec)': 'duration',
            'Location': 'location'
        }, inplace=True)
        data['call_time'] = data['call_time'].apply(lambda x: convert_to_utc_safe(x) if pd.notna(x) else None)
        data['duration'] = pd.to_numeric(data['duration'].str.replace(' Sec', '').str.replace('Min &amp; ', '').str.replace(' Min', ''), errors='coerce').fillna(0).astype(int)
        data['contact_id'] = data['contact_id'].fillna("Private")
        data = data[['call_type', 'call_time', 'contact_id', 'duration', 'location']]

    elif 'name' in columns:
        print("Processing as Contacts...")
        data['Phone Number'] = data['Phone Number'].str.replace(r'\D', '', regex=True)
        data['Email Id'].fillna("not_available@example.com", inplace=True)
        data['Last Contacted'] = data['Last Contacted'].apply(lambda x: convert_to_utc_safe(x) if pd.notna(x) else None)

    elif 'application name' in columns:
        print("Processing as Applications...")
        data = data.copy()
        data['Installed Date'] = data['Installed Date'].apply(lambda x: convert_to_utc_safe(x) if pd.notna(x) else None)
        data.rename(columns={
            'Application Name': 'application_name',
            'Package Name': 'package_name',
            'Installed Date': 'installed_date'
        }, inplace=True)
        data = data[['application_name', 'package_name', 'installed_date']]
        data.drop_duplicates(subset=['package_name'], inplace=True)

    elif 'application' in columns and 'text' in columns:
        print("Processing as Keylogs...")
        data['Time'] = data['Time'].apply(lambda x: convert_to_utc_safe(x) if pd.notna(x) else None)
        data = data[data['Text'].str.len() >= 3]

    elif 'time' in columns and 'sender' in columns and 'text' in columns:
        print("Processing as Chats...")
        data['time'] = data['Time'].apply(lambda x: convert_to_utc_safe(x) if pd.notna(x) else None)
        data['sender'] = data['Sender'].apply(lambda x: "GroupName" if "Group Chat" in x else x)
        data['text'] = data['Text']
        data = data[['time', 'sender', 'text']]

    return data

def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

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

    try:
        cur.executemany(insert_query, values)
        conn.commit()
        print(f"Successfully inserted {len(values)} rows into {table_name} table")
    except Exception as e:
        conn.rollback()
        print(f"Error inserting data into {table_name} table: {str(e)}")
    finally:
        cur.close()
        conn.close()

def process_and_insert_data(file_path):
    try:
        if file_path.endswith('.csv'):
            encoding = detect_encoding(file_path)
            print(f"Processing {os.path.basename(file_path)} with detected encoding: {encoding}")
            df = pd.read_csv(file_path, encoding=encoding, on_bad_lines='skip')
        elif file_path.endswith(('.xlsx', '.xls')):
            print(f"Processing {os.path.basename(file_path)} as Excel.")
            df = pd.read_excel(file_path)
            print("Columns:", df.columns.tolist())
            print("\nFirst few rows:")
            print(df.head().to_string())
            
            if not set(df.columns).issubset({'SMS type', 'Time', 'From/To', 'Text', 'Location', 
                                             'Call type', 'Duration (Sec)',
                                             'Name', 'Phone Number', 'Email Id', 'Last Contacted',
                                             'Application Name', 'Package Name', 'Installed Date',
                                             'Application', 'Messenger', 'Sender'}):
                print("First row doesn't contain expected column names. Treating it as data.")
                new_header = df.iloc[0]
                df = df[1:]
                df.columns = new_header
                df.reset_index(drop=True, inplace=True)
                print("Updated first few rows:")
                print(df.head().to_string())
        else:
            print(f"Skipping unsupported file: {os.path.basename(file_path)}")
            return

        table_name = detect_file_type(df)
        if table_name:
            df_cleaned = process_data(df)
            print(f"Processed data structure for {os.path.basename(file_path)}:")
            print(df_cleaned.head().to_string())
            insert_data(table_name, df_cleaned)
            print(f"Successfully processed and inserted data from {file_path} into {table_name} table")
        else:
            print(f"Could not determine table for {file_path}. Attempting to infer based on column names.")
            inferred_table = infer_table_from_columns(df.columns)
            if inferred_table:
                df_cleaned = process_data(df)
                print(f"Processed data structure for {os.path.basename(file_path)}:")
                print(df_cleaned.head().to_string())
                insert_data(inferred_table, df_cleaned)
                print(f"Inferred table type: {inferred_table}. Data inserted successfully.")
            else:
                print(f"Could not infer table type. Data not inserted.")

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        raise

def infer_table_from_columns(columns):
    columns = set(str(col).lower() for col in columns)
    if {'sms type', 'time', 'from/to', 'text'}.issubset(columns):
        return 'sms'
    elif {'call type', 'time', 'from/to', 'duration'}.issubset(columns):
        return 'calls'
    elif {'name', 'phone number'}.issubset(columns):
        return 'contacts'
    elif {'application name', 'package name', 'installed date'}.issubset(columns):
        return 'applications'
    elif {'application', 'time', 'text'}.issubset(columns):
        return 'keylogs'
    elif {'time', 'sender', 'text'}.issubset(columns):
        return 'chats'
    return None

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

def test_db_connection():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f'Database connection error: {str(e)}')
        return False
