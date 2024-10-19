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
        print("Processing as SMS...")
        data['Time'] = data['Time'].apply(lambda x: convert_to_utc_safe(x) if pd.notna(x) else None)
        data['From/To'] = data['From/To'].str.strip()
        data['Text'] = data['Text'].str.strip()
        data.fillna("Unknown", inplace=True)

    elif 'call type' in columns:
        print("Processing as Calls...")
        data['Time'] = data['Time'].apply(lambda x: convert_to_utc_safe(x) if pd.notna(x) else None)
        data['Duration (Sec)'] = pd.to_numeric(data['Duration (Sec)'].str.replace(' Sec', ''), errors='coerce').fillna(0).astype(int)
        data['From/To'].fillna("Private", inplace=True)

    elif 'name' in columns:
        print("Processing as Contacts...")
        data['Phone Number'] = data['Phone Number'].str.replace(r'\D', '', regex=True)
        data['Email Id'].fillna("not_available@example.com", inplace=True)
        data['Last Contacted'] = data['Last Contacted'].apply(lambda x: convert_to_utc_safe(x) if pd.notna(x) else None)

    elif 'application name' in columns:
        print("Processing as Applications...")
        data = data.copy()  # Create a copy to avoid SettingWithCopyWarning
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
        if file_path.endswith('.csv'):
            try:
                encoding = detect_encoding(file_path)
                print(f"Processing {os.path.basename(file_path)} with detected encoding: {encoding}")
                df = pd.read_csv(file_path, encoding=encoding, on_bad_lines='skip')
            except UnicodeDecodeError:
                print(f"Retrying {os.path.basename(file_path)} with 'latin1' encoding.")
                df = pd.read_csv(file_path, encoding='latin1', on_bad_lines='skip')

        elif file_path.endswith(('.xlsx', '.xls')):
            print(f"Processing {os.path.basename(file_path)} as Excel.")
            df = pd.read_excel(file_path)

        else:
            print(f"Skipping unsupported file: {os.path.basename(file_path)}")
            return

        table_name = detect_file_type(df)
        if table_name:
            df_cleaned = process_data(df)
            insert_data(table_name, df_cleaned)
            print(f"Successfully processed and inserted data from {file_path} into {table_name} table")
        else:
            print(f"Could not determine table for {file_path}. Data not inserted.")

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        raise