import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import time

load_dotenv()

DB_HOST = "timescaledb" if "DOCKER" in os.environ else "localhost"
DATABASE_URL = os.getenv("DATABASE_URL", f"postgresql://postgres:password@{DB_HOST}:5432/solar_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Add Timescale hypertables/aggs (non-transactional matview conversion)."""
    with engine.connect() as conn:
        conn.execution_options(autocommit=True).execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb;"))
    
    # Hypertables
    for table in ['weather_data', 'device_data_historical', 'predictions', 'fault_logs', 'error_logs']:
        with engine.connect() as conn:
            conn.execution_options(autocommit=True).execute(text(f"SELECT create_hypertable('{table}', 'timestamp', if_not_exists => TRUE);"))
    
    # Matview: Create regular first, then continuous (no initial data refresh)
    # with engine.connect() as conn:
    #     conn.execution_options(autocommit=True).execute(text("""
    #         CREATE MATERIALIZED VIEW IF NOT EXISTS daily_device_summary
    #         AS SELECT time_bucket('1 day', timestamp) AS bucket,
    #                device_sn, AVG(total_power) AS avg_power, SUM(energy_today) AS total_energy
    #         FROM device_data_historical GROUP BY bucket, device_sn;
    #     """))
    # with engine.connect() as conn:
    #     conn.execution_options(autocommit=True).execute(text("""
    #         SELECT add_continuous_aggregate_policy('daily_device_summary',
    #             start_offset => INTERVAL '1 month', end_offset => INTERVAL '1 day', schedule_interval => INTERVAL '1 hour');
    #     """))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()