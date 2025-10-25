import sys
sys.path.insert(0, '/opt/airflow')# backend/config/settings.py
# backend/config/settings.py
import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    # Core DB
    POSTGRES_URL: str = os.getenv("POSTGRES_URL", "postgresql://postgres:password@timescaledb:5432/solar_db")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@timescaledb:5432/solar_db")  # Alias for FastAPI
     # Auth/JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your_jwt_secret")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
    
    # Frontend/App
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    VITE_API_BASE_URL: str = os.getenv("VITE_API_BASE_URL", "http://localhost:8000")  # For frontend
    
    # ETL/Providers
    COMPANY_KEY: str = os.getenv("COMPANY_KEY", "your_shinemonitor_company_key")
    BATCH_SIZE: int = os.getenv("BATCH_SIZE", 100)
    
    # Solarman
    SOLARMAN_EMAIL: str = os.getenv("SOLARMAN_EMAIL", "example@email.com")
    SOLARMAN_PASSWORD_SHA256: str = os.getenv("SOLARMAN_PASSWORD_SHA256", "your-sha256-hashed-password")
    SOLARMAN_APP_ID: str = os.getenv("SOLARMAN_APP_ID", "your_app_id")
    SOLARMAN_APP_SECRET: str = os.getenv("SOLARMAN_APP_SECRET", "your_app_secret")
    
    # Other
    FLASK_ENV: str = os.getenv("FLASK_ENV", "development")  # Deprecated, but kept for compat
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "your_encryption_key")
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "your_sendgrid_key")  # For emails/OTP

    model_config = ConfigDict(
        extra='ignore',  # FIXED: Ignore unknown env vars to prevent errors
        env_file='.env',  # Load from .env
        env_ignore_empty=True  # Skip empty vars
    )

settings = Settings()