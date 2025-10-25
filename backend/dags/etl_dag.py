from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
import os

# Add backend directory to Python path - this is where it's mounted in the container
sys.path.insert(0, '/opt/airflow')

# Import directly from modules
from backend.config.settings import settings
from backend.services.providers.solarman_client import SolarmanAPI
from backend.services.providers.shinemonitor_client import ShinemonitorAPI
from backend.services.providers.soliscloud_client import SolisCloudAPI
from backend.services.etl.etl_service import normalize_data_entry, insert_data_to_db
from backend.services.etl.api_fetcher import fetch_for_all_panels

default_args = {
    'owner': 'rayvolt',
    'depends_on_past': False,
    'start_date': datetime(2025, 10, 21),
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'solar_etl_dag',
    default_args=default_args,
    description='ETL for Solarman and Solis data',
    schedule_interval='@hourly',
    catchup=False,
    max_active_runs=1,
)

def run_etl_historical(**kwargs):
    fetch_for_all_panels(historical=True)  # Last 7 days historical

def run_etl_realtime(**kwargs):
    fetch_for_all_panels(historical=False)  # Current realtime

historical_task = PythonOperator(
    task_id='fetch_historical_data',
    python_callable=run_etl_historical,
    dag=dag,
)

realtime_task = PythonOperator(
    task_id='fetch_realtime_data',
    python_callable=run_etl_realtime,
    dag=dag,
)

historical_task >> realtime_task
