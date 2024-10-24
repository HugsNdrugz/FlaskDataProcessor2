from nicegui import ui
import pandas as pd
import psycopg2
from psycopg2 import sql
import os
from datetime import datetime, timedelta
import chardet

# Accessing PostgreSQL environment variables from Replit secrets
PGDATABASE = os.environ.get('PGDATABASE')
PGHOST = os.environ.get('PGHOST')
PGPORT = os.environ.get('PGPORT')
PGUSER = os.environ.get('PGUSER')
PGPASSWORD = os.environ.get('PGPASSWORD')
DATABASE_URL = os.environ.get('DATABASE_URL')

# Calculate Easter for a given year (using the Anonymous Gregorian algorithm)
def get_easter(year):
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return datetime(year, month, day)

# Convert to UTC-safe format with year assumption and Easter handling
def convert_to_utc_safe(time_str, format_str="%b %d, %I:%M %p"):
    try:
        dt = datetime.strptime(time_str, format_str)
        if dt.year == 1900:  # Default year from strptime when year is not given
            dt = dt.replace(year=2024)
        easter_2024 = get_easter(2024)
        if dt.date() == easter_2024.date():
            dt -= timedelta(days=1)  # Shift back by one day if it’s Easter
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        # Default fallback in case of parsing errors
        return datetime(2024, 2, 28, 23, 59).strftime("%Y-%m-%d %H:%M:%S")

# Establish the database connection
def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=PGDATABASE,
            user=PGUSER,
            password=PGPASSWORD,
            host=PGHOST,
            port=PGPORT,
            sslmode='require'
        )
        return conn
    except Exception as e:
        ui.notify(f"Connection error: {str(e)}", color='red')

# Detect encoding of uploaded files
def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result.get('encoding', 'utf-8')

# Upload and display file contents
@ui.refreshable
def display_file_contents(file):
    encoding = detect_encoding(file.name)
    df = pd.read_csv(file, encoding=encoding)
    ui.table(df.values.tolist(), headers=df.columns.tolist())

# Insert data into the database
def insert_data(table_name, df):
    conn = get_db_connection()
    cur = conn.cursor()
    columns = df.columns.tolist()
    values = [tuple(x) for x in df.to_numpy()]

    query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
        sql.Identifier(table_name),
        sql.SQL(', ').join(map(sql.Identifier, columns)),
        sql.SQL(', ').join(sql.Placeholder() * len(columns))
    )

    try:
        cur.executemany(query, values)
        conn.commit()
        ui.notify(f"Inserted {len(values)} rows into {table_name}.")
    except Exception as e:
        conn.rollback()
        ui.notify(f"Error: {str(e)}", color='red')
    finally:
        cur.close()
        conn.close()

# Create necessary tables
def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()

    tables = [
        """CREATE TABLE IF NOT EXISTS contacts (
            contact_id SERIAL PRIMARY KEY,
            contact_name VARCHAR(255),
            phone_number VARCHAR(50),
            email VARCHAR(255)
        )""",
        """CREATE TABLE IF NOT EXISTS sms (
            sms_id SERIAL PRIMARY KEY,
            sender_id VARCHAR(50),
            receiver_id VARCHAR(50),
            message_type VARCHAR(50),
            message_time TIMESTAMP,
            message_text TEXT,
            location TEXT
        )"""
    ]

    try:
        for table in tables:
            cur.execute(table)
        conn.commit()
        ui.notify("Tables created successfully.")
    except Exception as e:
        ui.notify(f"Error: {str(e)}", color='red')
    finally:
        cur.close()
        conn.close()

# Test the database connection
def test_db_connection():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        ui.notify("Database connection successful.")
    except Exception as e:
        ui.notify(f"Connection error: {str(e)}", color='red')

# Main GUI layout
def main_gui():
    ui.label("Data Management Interface").classes('text-2xl')

    with ui.row():
        ui.upload(on_upload=lambda e: display_file_contents(e), multiple=False)

    with ui.row():
        ui.button("Create Tables", on_click=create_tables)
        ui.button("Test DB Connection", on_click=test_db_connection)

    ui.run(title="Data Manager", port=8080)

# Run th
if __name__ in {"__main__","__mp_main__"}:
    main_gui()