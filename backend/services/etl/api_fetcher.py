from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Fix for container path: Add /opt/airflow to Python path (where backend is mounted)
import sys
sys.path.insert(0, '/opt/airflow')

from backend.config.settings import settings
from backend.services.providers.solarman_client import SolarmanAPI
from backend.services.providers.shinemonitor_client import ShinemonitorAPI
from backend.services.providers.soliscloud_client import SolisCloudAPI
from backend.services.etl.etl_service import normalize_data_entry, insert_data_to_db
import logging
from datetime import datetime, timedelta

engine = create_engine(settings.POSTGRES_URL)
Session = sessionmaker(bind=engine)
logger = logging.getLogger(__name__)

def get_client(api_provider: str, credential: dict):
    api_provider = api_provider.lower()
    if api_provider == 'solarman':
        return SolarmanAPI(
            email=credential.get('username', ''),  # Assuming username is email for Solarman
            password_sha256=credential.get('password', ''),
            app_id=credential.get('api_key', ''),
            app_secret=credential.get('api_secret', '')
        )
    elif api_provider == 'shinemonitor':
        return ShinemonitorAPI(company_key=settings.COMPANY_KEY)
    elif api_provider == 'soliscloud':
        return SolisCloudAPI(
            api_key=credential.get('api_key', ''),
            api_secret=credential.get('api_secret', '')
        )
    raise ValueError(f"Unknown API provider: {api_provider}")

def fetch_for_all_panels(historical: bool = False):
    with Session() as session:
        result = session.execute(text("SELECT * FROM api_credentials"))
        credentials = [dict(row) for row in result.fetchall()]

        logger.info(f"Processing {len(credentials)} credentials (historical={historical})")

        for credential in credentials:
            uid = credential.get('user_id', 'unknown')
            prov = credential.get('api_provider', 'unknown').lower()

            try:
                client = get_client(prov, credential)
                username = credential.get('username', '')
                password = credential.get('password', '')

                # Fetch plants/stations
                if prov == 'solarman':
                    plants = client.get_plant_list(uid, username, password)
                elif prov == 'shinemonitor':
                    plants = client.fetch_plant_list(uid, username, password)
                elif prov == 'soliscloud':
                    plants = client.get_all_stations(uid)
                else:
                    logger.warning(f"Skipping unknown provider: {prov}")
                    continue

                logger.info(f"Fetched {len(plants)} plants for user {uid} ({prov})")

                for plant in plants:
                    plant_id = plant.get('plant_id') or plant.get('pid') or plant.get('id') or plant.get('station_id')
                    if not plant_id:
                        logger.warning(f"Skipping plant without ID: {plant}")
                        continue

                    # Fetch devices
                    if prov == 'solarman':
                        devices = client.get_all_devices(uid, username, password, plant_id)
                    elif prov == 'shinemonitor':
                        devices = client.fetch_plant_devices(uid, username, password, plant_id)
                    elif prov == 'soliscloud':
                        devices = client.get_all_inverters(uid, station_id=plant_id)

                    logger.info(f"Fetched {len(devices)} devices for plant {plant_id}")

                    for device in devices:
                        device_sn = device.get('sn') or device.get('deviceSn')
                        if not device_sn:
                            logger.warning(f"Skipping device without SN: {device}")
                            continue

                        # Fetch data
                        if historical:
                            end_date = datetime.now().strftime('%Y-%m-%d')
                            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                            if prov == 'solarman':
                                data = client.get_historical_data(uid, username, password, device, start_date, end_date)
                            elif prov == 'shinemonitor':
                                data = client.fetch_historical_data(uid, username, password, device, start_date, end_date)
                            elif prov == 'soliscloud':
                                data = client.get_inverter_historical_data(uid, device=device, start_date=start_date, end_date=end_date, station_id=plant_id)
                        else:
                            if prov == 'solarman':
                                data = client.get_realtime_data(uid, username, password, device)
                            elif prov == 'shinemonitor':
                                data = client.fetch_current_data(uid, username, password, device)
                            elif prov == 'soliscloud':
                                data = client.get_inverter_current_data(uid, device=device, station_id=plant_id)

                        if not data:
                            logger.info(f"No data fetched for device {device_sn} (historical={historical})")
                            continue

                        normalized = []
                        for entry in data:
                            norm = normalize_data_entry(entry, prov)
                            if norm:
                                normalized.append(norm)

                        if normalized:
                            insert_data_to_db(
                                session,
                                normalized,
                                device_sn,
                                credential['customer_id'],
                                prov,
                                realtime=not historical
                            )
                            logger.info(f"Inserted {len(normalized)} entries for device {device_sn}")

                session.commit()

            except Exception as e:
                logger.error(f"Error processing credential for user {uid} ({prov}): {str(e)}", exc_info=True)
                session.rollback()
                continue

        logger.info("ETL process completed successfully.")
