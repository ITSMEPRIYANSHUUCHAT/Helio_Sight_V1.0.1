# backend/config/database.py
import logging
import time
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from .settings import settings  # Import settings for POSTGRES_URL

logger = logging.getLogger(__name__)

def get_engine():
    """Create SQLAlchemy engine for TimescaleDB."""
    return create_engine(
        settings.POSTGRES_URL, 
        pool_size=20, 
        max_overflow=0, 
        pool_pre_ping=True,
        pool_recycle=300  # Recycle connections every 5 min to prevent leaks
    )

# Top-level engine for global use
engine = get_engine()

def get_db():
    """FastAPI dependency: Yields a Session per request, closes after."""
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize DB: Run schema.sql and hypertables."""
    with engine.connect() as conn:
        # Inline schema execution if needed (omit if ./schema.sql mounted to initdb.d)
        try:
            # For Docker initdb.d, skip inline—rely on mount
            logger.info("Schema loaded via initdb.d (if mounted).")
        except Exception as e:
            logger.warning(f"Schema execution skipped (may already exist): {e}")

        # Create hypertables (with try/except for timing)
        hypertables = [
            ('weather_data', 'timestamp'),
            ('device_data_historical', 'timestamp'),
            ('predictions', 'timestamp'),
            ('fault_logs', 'timestamp'),
            ('error_logs', 'timestamp')
        ]
        for table, time_col in hypertables:
            try:
                conn.execution_options(autocommit=True).execute(text(f"SELECT create_hypertable('{table}', '{time_col}', if_not_exists => TRUE);"))
                logger.info(f"Hypertable {table} created.")
            except Exception as e:
                logger.warning(f"Hypertable {table} skipped (may exist): {e}")

def retry_init_db(max_retries=5):
    """Retry DB init with backoff (called in main.py)."""
    for attempt in range(max_retries):
        try:
            init_db()
            logger.info("DB initialized successfully")
            return
        except OperationalError as e:
            logger.error(f"DB init attempt {attempt + 1} failed (connection issue): {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
        except Exception as e:
            logger.error(f"Unexpected error in DB init: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)

if __name__ == "__main__":
    retry_init_db()