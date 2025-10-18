from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import os
from dotenv import load_dotenv
from .config.database import init_db, engine
from .controllers.auth import router as auth_router  # Add this
import time

load_dotenv()

app = FastAPI(title="Solar Dashboard API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router
app.include_router(auth_router)

# Retry init_db
def retry_init_db(max_retries=5, delay=5):
    for attempt in range(max_retries):
        try:
            init_db()
            print(f"DB initialized on attempt {attempt + 1}")
            return
        except Exception as e:
            print(f"DB init attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                raise

retry_init_db()

@app.get("/")
async def root():
    return {"message": "Solar Dashboard API Ready! 🚀", "date": "2025-10-18"}

@app.get("/health")
async def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM device_data_historical LIMIT 1"))
        return {"status": "healthy", "db": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")