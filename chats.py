from nicegui import ui
import psycopg2
import os

# Fetch secrets from Replit's environment
db = psycopg2.connect(
    dbname=os.getenv('PGDATABASE'),
    user=os.getenv('PGUSER'),
    password=os.getenv('PGPASSWORD'),
    host=os.getenv('PGHOST'),
    port=os.getenv('PGPORT')
)

def fetch_contacts():
    cursor = db.cursor()
    cursor.execute('SELECT DISTINCT sender FROM Messenger')
    return [row[0] for row in cursor.fetchall()]

def fetch_chat_history(contact):
    cursor = db.cursor()
    cursor.execute(
        'SELECT time, sender, text FROM Messenger WHERE sender = %s ORDER BY time DESC',
        (contact,)
    )
    return cursor.fetchall()

contacts = fetch_contacts()

with ui.tab_bar() as tab_bar:
    for contact in contacts:
        with ui.tab(contact):
            messages = fetch_chat_history(contact)
            with ui.column().classes('chat-container'):
                for msg in messages:
                    time, sender, text = msg
                    ui.card().classes('chat-bubble').style(
                        'margin: 5px; padding: 10px; border-radius: 15px; max-width: 70%;'
                    ).content(
                        f'[{time}] **{sender}**: {text}'
                    )

ui.run()