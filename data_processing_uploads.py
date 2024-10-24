
import pandas as pd
import psycopg2
import os
from psycopg2 import sql
import chardet

def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def process_and_insert_data(file_path):
    encoding = detect_encoding(file_path)
    df = pd.read_csv(file_path, encoding=encoding, on_bad_lines='skip')
    table_name = detect_file_type(df)

    if table_name:
        df_cleaned = process_data(df)
        insert_data(table_name, df_cleaned)
    else:
        raise ValueError("File type not recognized.")

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

def detect_file_type(df):
    columns = set(df.columns.str.lower())
    if 'call type' in columns:
        return 'calls'
    elif 'name' in columns and 'phone number' in columns:
        return 'contacts'
    elif 'sms type' in columns:
        return 'sms'
    elif 'application name' in columns and 'package name' in columns:
        return 'applications'
    elif 'time' in columns and 'sender' in columns:
        return 'chats'
    return None

def process_data(df):
    if 'sms type' in df.columns:
        df.rename(columns={'SMS type': 'message_type'}, inplace=True)
    return df

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

def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS sms (
            sms_id SERIAL PRIMARY KEY,
            sender VARCHAR(50),
            receiver VARCHAR(50),
            message TEXT
        )
        '''
    )
    conn.commit()
    cur.close()
    conn.close()

def test_db_connection():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False
