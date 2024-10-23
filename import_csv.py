import pandas as pd
from app import create_app
from models import db, Chat, SMS, Calls, Contacts, InstalledApps, Keylogs
from datetime import datetime
import os

def import_csv_data():
    app = create_app()
    with app.app_context():
        # Import Chats
        if os.path.exists('data/chats.csv'):
            chats_df = pd.read_csv('data/chats.csv')
            for _, row in chats_df.iterrows():
                chat = Chat(
                    sender=row['sender'],
                    text=row['text'],
                    time=datetime.strptime(row['time'], '%Y-%m-%d %H:%M:%S')
                )
                db.session.add(chat)

        # Import SMS
        if os.path.exists('data/sms.csv'):
            sms_df = pd.read_csv('data/sms.csv')
            for _, row in sms_df.iterrows():
                sms = SMS(
                    from_to=row['from_to'],
                    text=row['text'],
                    time=datetime.strptime(row['time'], '%Y-%m-%d %H:%M:%S'),
                    location=row.get('location')
                )
                db.session.add(sms)

        # Import Calls
        if os.path.exists('data/calls.csv'):
            calls_df = pd.read_csv('data/calls.csv')
            for _, row in calls_df.iterrows():
                call = Calls(
                    call_type=row['call_type'],
                    time=datetime.strptime(row['time'], '%Y-%m-%d %H:%M:%S'),
                    from_to=row['from_to'],
                    duration=row['duration'],
                    location=row.get('location')
                )
                db.session.add(call)

        # Import Contacts
        if os.path.exists('data/contacts.csv'):
            contacts_df = pd.read_csv('data/contacts.csv')
            for _, row in contacts_df.iterrows():
                contact = Contacts(
                    name=row['name']
                )
                db.session.add(contact)

        # Import Installed Apps
        if os.path.exists('data/installed_apps.csv'):
            apps_df = pd.read_csv('data/installed_apps.csv')
            for _, row in apps_df.iterrows():
                app = InstalledApps(
                    application_name=row['application_name'],
                    package_name=row['package_name'],
                    install_date=datetime.strptime(row['install_date'], '%Y-%m-%d %H:%M:%S')
                )
                db.session.add(app)

        # Import Keylogs
        if os.path.exists('data/keylogs.csv'):
            keylogs_df = pd.read_csv('data/keylogs.csv')
            for _, row in keylogs_df.iterrows():
                keylog = Keylogs(
                    application=row['application'],
                    time=datetime.strptime(row['time'], '%Y-%m-%d %H:%M:%S'),
                    text=row['text']
                )
                db.session.add(keylog)

        try:
            db.session.commit()
            print("Successfully imported data from CSV files")
        except Exception as e:
            db.session.rollback()
            print(f"Error importing data: {str(e)}")

if __name__ == '__main__':
    import_csv_data()
