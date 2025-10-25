# backend/services/etl/etl_service.py
import logging
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

def normalize_data_entry(entry: Dict, api_provider: str) -> Optional[Dict]:
    """
    Normalizes raw API data to standard schema format.
    Maps provider-specific keys, zeros nighttime generation (7pm-7am), filters invalid entries.
    """
    if not entry or 'timestamp' not in entry:
        logger.warning(f"Skipping invalid entry: {entry}")
        return None

    # Standard fields (common across providers)
    normalized = {
        'timestamp': entry.get('timestamp'),
        'device_id': entry.get('device_id') or entry.get('sn') or entry.get('deviceSn'),
        'total_power': float(entry.get('total_power') or entry.get('pac') or entry.get('tpg') or 0.0),
        'energy_today': float(entry.get('energy_today') or entry.get('eToday') or entry.get('etdy_ge1') or 0.0),
        'pr': float(entry.get('pr') or 0.0),
        'state': entry.get('state') or entry.get('status') or 'unknown',
        'faults': entry.get('faults') or [],
        'reactive_power': float(entry.get('reactive_power') or 0.0),
        'cuf': float(entry.get('cuf') or 0.0),
        'frequency': float(entry.get('frequency') or entry.get('fac') or entry.get('a_fo1') or 0.0),
        # Grid phases
        'r_voltage': float(entry.get('r_voltage') or entry.get('uAc1') or entry.get('av1') or 0.0),
        's_voltage': float(entry.get('s_voltage') or entry.get('uAc2') or entry.get('av2') or 0.0),
        't_voltage': float(entry.get('t_voltage') or entry.get('uAc3') or entry.get('av3') or 0.0),
        'r_current': float(entry.get('r_current') or entry.get('iAc1') or entry.get('ac1') or 0.0),
        's_current': float(entry.get('s_current') or entry.get('iAc2') or entry.get('ac2') or 0.0),
        't_current': float(entry.get('t_current') or entry.get('iAc3') or entry.get('ac3') or 0.0),
        'rs_voltage': float(entry.get('rs_voltage') or 0.0),
        'st_voltage': float(entry.get('st_voltage') or 0.0),
        'tr_voltage': float(entry.get('tr_voltage') or 0.0),
    }

    # PV strings (up to 12, as per schema/management)
    for i in range(1, 13):
        pv_num = f'pv{i:02d}'
        normalized[f'{pv_num}_voltage'] = float(entry.get(f'{pv_num}_voltage') or entry.get(f'uPv{i}') or entry.get(f'dv{i}') or entry.get(f'PV{i} voltage') or 0.0)
        normalized[f'{pv_num}_current'] = float(entry.get(f'{pv_num}_current') or entry.get(f'iPv{i}') or entry.get(f'dc{i}') or entry.get(f'PV{i} current') or 0.0)

    # Provider-specific adjustments
    if api_provider.lower() == 'soliscloud':
        normalized['battery_voltage'] = float(entry.get('battery_voltage') or entry.get('storageBatteryVoltage') or 0.0)
        normalized['battery_current'] = float(entry.get('battery_current') or entry.get('storageBatteryCurrent') or 0.0)
        normalized['inverter_temperature'] = float(entry.get('inverter_temperature') or 0.0)
    elif api_provider.lower() == 'shinemonitor':
        # Fault list already mapped
        pass
    elif api_provider.lower() == 'solarman':
        normalized['total_dc_input_power'] = float(entry.get('total_dc_input_power') or entry.get('dpi_t1') or 0.0)

    # Nighttime zeroing (7pm-7am, no solar generation)
    try:
        ts = datetime.strptime(normalized['timestamp'], '%Y-%m-%d %H:%M:%S')
        hour = ts.hour
        if 19 <= hour or hour < 7:
            normalized['total_power'] = 0.0
            normalized['energy_today'] = 0.0
            for i in range(1, 13):
                normalized[f'pv{i:02d}_voltage'] = 0.0
                normalized[f'pv{i:02d}_current'] = 0.0
    except ValueError as e:
        logger.warning(f"Invalid timestamp format in entry: {e}")

    return normalized if normalized.get('total_power') is not None else None  # Filter empty

def insert_data_to_db(session: Session, normalized_data: List[Dict], device_sn: str, customer_id: str, api_provider: str, realtime: bool = False):
    """
    Inserts normalized data to hypertable (historical or realtime).
    Uses raw SQL for speed; ON CONFLICT skips duplicates.
    """
    table_name = 'device_data_realtime' if realtime else 'device_data_historical'
    
    for entry in normalized_data:
        try:
            params = {
                'device_sn': device_sn,
                'customer_id': customer_id,  # For tracing
                'api_provider': api_provider,
                'timestamp': entry['timestamp'],
                'total_power': entry['total_power'],
                'energy_today': entry['energy_today'],
                'pr': entry['pr'],
                'state': entry['state'],
                'faults': entry['faults'],  # JSONB in schema
                'reactive_power': entry['reactive_power'],
                'cuf': entry['cuf'],
                'frequency': entry['frequency'],
                'r_voltage': entry['r_voltage'],
                's_voltage': entry['s_voltage'],
                't_voltage': entry['t_voltage'],
                'r_current': entry['r_current'],
                's_current': entry['s_current'],
                't_current': entry['t_current'],
                'rs_voltage': entry['rs_voltage'],
                'st_voltage': entry['st_voltage'],
                'tr_voltage': entry['tr_voltage'],
            }
            # Add PV fields
            for i in range(1, 13):
                pv_num = f'pv{i:02d}'
                params[f'{pv_num}_voltage'] = entry[f'{pv_num}_voltage']
                params[f'{pv_num}_current'] = entry[f'{pv_num}_current']
            
            # Provider extras (if schema has columns)
            if api_provider.lower() == 'soliscloud':
                params['battery_voltage'] = entry.get('battery_voltage', 0.0)
                params['battery_current'] = entry.get('battery_current', 0.0)
                params['inverter_temperature'] = entry.get('inverter_temperature', 0.0)
            params['total_dc_input_power'] = entry.get('total_dc_input_power', 0.0)  # For Solarman

            session.execute(text(f"""
                INSERT INTO {table_name} (
                    device_sn, customer_id, api_provider, timestamp,
                    total_power, energy_today, pr, state, faults, reactive_power, cuf, frequency,
                    r_voltage, s_voltage, t_voltage, r_current, s_current, t_current,
                    rs_voltage, st_voltage, tr_voltage,
                    pv01_voltage, pv01_current, pv02_voltage, pv02_current, pv03_voltage, pv03_current,
                    pv04_voltage, pv04_current, pv05_voltage, pv05_current, pv06_voltage, pv06_current,
                    pv07_voltage, pv07_current, pv08_voltage, pv08_current, pv09_voltage, pv09_current,
                    pv10_voltage, pv10_current, pv11_voltage, pv11_current, pv12_voltage, pv12_current,
                    total_dc_input_power, battery_voltage, battery_current, inverter_temperature
                ) VALUES (
                    :device_sn, :customer_id, :api_provider, :timestamp,
                    :total_power, :energy_today, :pr, :state, :faults, :reactive_power, :cuf, :frequency,
                    :r_voltage, :s_voltage, :t_voltage, :r_current, :s_current, :t_current,
                    :rs_voltage, :st_voltage, :tr_voltage,
                    :pv01_voltage, :pv01_current, :pv02_voltage, :pv02_current, :pv03_voltage, :pv03_current,
                    :pv04_voltage, :pv04_current, :pv05_voltage, :pv05_current, :pv06_voltage, :pv06_current,
                    :pv07_voltage, :pv07_current, :pv08_voltage, :pv08_current, :pv09_voltage, :pv09_current,
                    :pv10_voltage, :pv10_current, :pv11_voltage, :pv11_current, :pv12_voltage, :pv12_current,
                    :total_dc_input_power, :battery_voltage, :battery_current, :inverter_temperature
                ) ON CONFLICT (device_sn, timestamp) DO NOTHING
            """), params)
        except Exception as e:
            logger.error(f"Insert failed for {device_sn}: {e}")
            session.rollback()
            continue
    
    session.commit()
    logger.info(f"Inserted {len(normalized_data)} rows into {table_name}")