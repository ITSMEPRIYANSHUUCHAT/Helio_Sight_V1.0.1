```markdown
# 🌞 Solar Dashboard Backend Documentation

## Overview
This document details the **backend structure** for the **Solar Dashboard API**, built with **FastAPI** and **TimescaleDB**.  
It covers the files created, their roles, data flow, and setup/testing.

The system unifies solar data from multiple sources — **ShineMonitor**, **Solarman**, and **SolisCloud** — via ETL (future **Airflow**), stores it in hypertables for time-series efficiency, and serves via REST for the React frontend.

- **Version:** 1.0.0 (Beta)  
- **Date:** October 18, 2025  
- **Tech Stack:** FastAPI (API), SQLAlchemy (ORM), TimescaleDB (DB), Docker Compose (local dev)

---

## 📂 Project Structure (Relevant Backend Files)
```

SOLAR_SOFT/
├── backend/
│   ├── main.py                  # App entrypoint
│   ├── config/
│   │   ├── **init**.py          # Sub-package
│   │   └── database.py          # DB config/init
│   ├── **init**.py              # Package
│   └── requirements.txt         # Dependencies
├── schema.sql                   # Base DB schema
├── docker-compose.yml           # Local stack
└── .env                         # Config vars

````

---

## 📘 File Details

### 1. `backend/main.py` (Entrypoint – ~80 lines)

**Purpose:**  
Bootstraps the FastAPI app, configures middleware, initializes DB on startup, and provides basic endpoints (`/` and `/health`).  
Ensures the app is ready for frontend integration.

**Key Features:**
- CORS for `localhost:3000` (frontend)
- Retry logic for DB init (handles startup race conditions)
- Health check queries a schema table to verify connectivity

**How It Works:**
- Imports DB engine from `.config.database`
- Calls `retry_init_db()` at module level (runs when uvicorn imports)
- Routes requests:
  - `/` → Welcome message  
  - `/health` → Tests DB `SELECT`

**Example Code Snippet (Retry Logic):**
```python
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
````

---

### 2. `backend/config/database.py` (~60 lines)

**Purpose:**
Manages PostgreSQL/TimescaleDB connection, installs extensions/hypertables, and provides ORM sessions.
Optimized for time-series data (e.g., solar readings).

**Key Features:**

* Host fallback (`timescaledb` in Docker, `localhost` local)
* Idempotent DDL (`IF NOT EXISTS`)
* Session dependency for endpoints

**How It Works:**

* Engine built from `DATABASE_URL` (env)
* `init_db()`:

  * Runs `CREATE EXTENSION`
  * Adds hypertables for schema tables (e.g. `weather_data`, `device_data_historical`)
  * Creates continuous aggregates for daily summaries
* `get_db()` yields session for CRUD

**Example Code Snippet (Hypertable Addition):**

```python
for table in ['weather_data', 'device_data_historical', 'predictions', 'fault_logs', 'error_logs']:
    with engine.connect() as conn:
        conn.execution_options(autocommit=True).execute(
            text(f"SELECT create_hypertable('{table}', 'timestamp', if_not_exists => TRUE);")
        )
```

---

### 3. `backend/__init__.py` (0 lines)

**Purpose:**
Makes `backend/` importable as a package.

**How It Works:**
Empty file—Python standard for directories to be modules.
Enables `from backend.main import app` in CMD.

---

### 4. `backend/config/__init__.py` (0 lines)

**Purpose:**
Makes `config/` importable as sub-package.

**How It Works:**
Empty—enables relative imports like `from .config.database import engine` in `main.py`.

---

### 5. `schema.sql` (~300 lines)

**Purpose:**
Defines core DB schema (`users`, `customers`, `devices`, hypertables for data).
Runs on DB startup via Docker volume.

**Key Features:**

* TEXT PK for users (UUID-ready)
* Enums (`api_provider_type`, `severity_type`)
* Hypertables (`device_data_historical`, `weather_data`, etc.)
* Triggers for `updated_at`, demo data insert

**How It Works:**
Docker mounts `schema.sql` to `/docker-entrypoint-initdb.d/schema.sql` — Postgres runs it on first boot.
Creates tables, FKs, triggers, and inserts demo data.

**Example Snippet (Users Table):**

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    usertype TEXT NOT NULL CHECK (usertype IN ('customer', 'installer')),
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO users (id, username, name, email, password_hash, usertype, verified) VALUES 
('507f1f77bcf86cd799439011', 'demo', 'Demo User', 'demo@example.com',
 '$2b$12$mcZLDV4fPyhoKsGIUyk03eQxkANE0ifIFYJpITZAAb1s61BE.Z9Oe', 'customer', TRUE);
```

---

## 🔁 Data Flow

### 🧩 Startup Sequence

1. **Docker Compose** starts TimescaleDB → `schema.sql` runs (creates tables, enums, triggers, demo data).
2. **FastAPI** starts → `main.py` calls `retry_init_db()` → `database.py` adds Timescale features (hypertables, matview for summaries).
3. **Frontend** starts (Vite dev server).

---

### ⚙️ Ingestion (ETL - Future)

1. Airflow DAG pulls from APIs (e.g. Solarman via `api_credentials`).
2. Normalize fields → `device_sn`, `timestamp`, `kwh`.
3. Insert into `device_data_historical`/`weather_data` (hypertables auto-partition by time).
4. Triggers update `updated_at`; errors logged in `error_logs`.

---

### 📊 API Query (Dashboard)

* Frontend calls `/dashboard/summary` (future endpoint).
* Uses `get_db()` session → SQL query on `device_data_historical`.
* Example:

  ```sql
  SELECT AVG(kwh)
  FROM device_data_historical
  WHERE timestamp > NOW() - INTERVAL '1 day';
  ```
* Returns JSON:

  ```json
  {
    "date": "2025-10-18",
    "avg_kwh": 12.5
  }
  ```

---

### 🤖 ML Forecasting (Future)

* Query historical data from hypertables.
* Prophet model in `services/ml_predictor.py`.
* Insert predictions into `predictions` (hypertable).

---

### 🔐 Auth Flow (Future)

* `/auth/register` → Insert user (`verified = false`).
* Send OTP (via Redis store).
* `/auth/verify-otp` → Update `verified = true`, issue JWT.

---

## ⚡ Scalability

* Hypertables partition data (e.g., monthly chunks).
* Aggregates precomputed → low latency (<50ms queries).
* For 1000+ users → add read replicas.

---

## 🧪 Setup & Testing

**Run:**

```bash
docker compose up --build -d
```

**Logs:**

```bash
docker compose logs fastapi
# Expect: "DB initialized"
```

**Test API:**

```bash
curl http://localhost:8000/health
# {"status": "healthy"}
```

**Frontend:**

```
http://localhost:3000
```

**DB (pgAdmin):**

* URL: `http://localhost:5050`
* Server: `timescaledb:5432`
* User: `postgres`
* Password: `password`

Run:

```sql
SELECT * FROM users;
```

→ Should show demo data.

---

## 🧾 Summary

* Backend modular, Dockerized, and Timescale-optimized.
* Ready for ETL + ML extensions.
* Frontend integration supported via REST endpoints.
* Beta version ensures core DB + API reliability.

---

**End of Document**


