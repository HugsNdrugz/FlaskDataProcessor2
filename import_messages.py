import pandas as pd
from app import create_app
from models import db, Messages
from datetime import datetime

def import_messages_data():
    app = create_app()
    with app.app_context():
        try:
            # Read messages data from ZIP file
            df = pd.read_csv('sampledata.zip', compression='zip')
            
            # Convert data to Messages objects
            messages = []
            for _, row in df.iterrows():
                message = Messages(
                    sender=row['sender'],
                    recipient=row['recipient'],
                    message=row['message'],
                    timestamp=datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S'),
                    is_read=bool(row['is_read'])
                )
                messages.append(message)

            # Add messages to database
            db.session.bulk_save_objects(messages)
            db.session.commit()
            print("Messages imported successfully!")
            
        except Exception as e:
            print(f"Error importing messages: {e}")
            db.session.rollback()

if __name__ == '__main__':
    import_messages_data()
