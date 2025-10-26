    import sys
    import os
    import logging
    import csv
    import re
    from datetime import datetime
    from psycopg2 import connect, OperationalError
    from pytz import timezone
    from logging import handlers

    # Fix for container path: Add /app to Python path
    sys.path.insert(0, '/app')

    # Add the project root (/app) to sys.path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    
    from backend.config.settings import settings
    

    DATABASE_URL = settings.DATABASE_URL
    logger = logging.getLogger(__name__)

    # Logging setup (unchanged)
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 'current')
    os.makedirs(log_dir, exist_ok=True)
    log_date = datetime.now(timezone('Asia/Kolkata')).strftime('%Y%m%d')
    log_file = os.path.join(log_dir, f'load_credentials_{log_date}.log')

    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"Log file initialized at {datetime.now(timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S IST')}\n")
        logging.getLogger('').handlers = []
        file_handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger = logging.getLogger('')
        logger.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
        logger.info(f"Logging initialized. Log file: {log_file}")
    except Exception as e:
        print(f"Failed to configure logging: {str(e)}", file=sys.stderr)
        raise

    def get_db_connection():
        try:
            conn = connect(DATABASE_URL)
            conn.autocommit = True  # FIXED: Autocommit to avoid transaction aborts
            return conn
        except OperationalError as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def get_user_customer_by_email(conn, email):
        """Query user_id and customer_id by email (JOIN users and customers)."""
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT u.id as user_id, c.customer_id
                    FROM users u
                    LEFT JOIN customers c ON u.id = c.user_id
                    WHERE u.email = %s
                """, (email,))
                row = cur.fetchone()
                if row:
                    return row[0], row[1]
                return None, None
        except Exception as e:
            logger.error(f"Failed to query user/customer by email {email}: {e}")
            return None, None

    def log_error_to_db(conn, email, api_provider, field_name, field_value, error_message):
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO error_logs (customer_id, device_sn, timestamp, api_provider, field_name, field_value, error_message, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        None, None, datetime.now(timezone('Asia/Kolkata')),
                        api_provider, field_name, field_value, error_message,
                        datetime.now(timezone('Asia/Kolkata'))
                    )
                )
            logger.info("Error logged to DB.")
        except Exception as e:
            logger.warning(f"Failed to log error to DB (table may not exist): {e}")  # FIXED: Skip if table missing

    def load_credentials_to_db(conn, csv_path):
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                credentials = list(reader)

            if not credentials:
                logger.info("No credentials in CSV, exiting.")
                return []

            inserted_count = 0
            with conn.cursor() as cur:
                for credential in credentials:
                    email = credential.get('email', '').strip()
                    if not email:
                        logger.warning(f"Skipping row without email: {credential}")
                        continue

                    # Query user_id/customer_id by email
                    user_id, customer_id = get_user_customer_by_email(conn, email)
                    if not user_id:
                        logger.warning(f"Skipping credential for unknown email: {email}")
                        log_error_to_db(conn, email, credential.get('api_provider', 'unknown'), "email", email, "No user found for email")
                        continue
                    if not customer_id:
                        logger.warning(f"Skipping credential for email without customer: {email}")
                        log_error_to_db(conn, email, credential.get('api_provider', 'unknown'), "customer_id", None, "No customer linked to user")
                        continue

                    try:
                        cur.execute(
                            """
                            INSERT INTO api_credentials (
                                user_id, customer_id, api_provider, username, password, api_key, api_secret,
                                created_at, updated_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (user_id) DO NOTHING
                            """,
                            (
                                user_id, customer_id, credential['api_provider'],
                                credential['username'], credential['password'],
                                credential.get('api_key'), credential.get('api_secret'),
                                datetime.now(timezone('Asia/Kolkata')), datetime.now(timezone('Asia/Kolkata'))
                            )
                        )
                        inserted_count += cur.rowcount
                        logger.info(f"Inserted credential for email {email} (customer_id {customer_id})")
                    except Exception as e:
                        logger.error(f"Failed to insert credential for email {email}: {e}")
                        log_error_to_db(conn, email, credential.get('api_provider', 'unknown'), "insert_credential", user_id, str(e))
                        continue  # FIXED: No rollback (autocommit), continue to next
            logger.info(f"Inserted {inserted_count} credentials.")
        except Exception as e:
            logger.error(f"Failed to load credentials from CSV: {e}")
            raise

    if __name__ == "__main__":
        conn = get_db_connection()
        try:
            load_credentials_to_db(conn, "backend/data/users.csv")
        except Exception as e:
            logger.error(f"Error in load_credentials: {e}")
        finally:
            conn.close()