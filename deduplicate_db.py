from flask import Flask
from models import db, init_db
from utils import cleanup_database
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

def main():
    try:
        init_db(app)
        with app.app_context():
            total_cleaned = cleanup_database()
            logger.info(f"Database deduplication completed. Removed {total_cleaned} duplicate records.")
    except Exception as e:
        logger.error(f"Error during database deduplication: {str(e)}")
        return False
    return True

if __name__ == "__main__":
    main()
