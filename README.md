Solar Dashboard: Unified ML-Powered Solar Energy Monitoring




A modern, scalable web application for unifying solar panel data from multiple sources, providing real-time dashboards, and leveraging machine learning for energy yield forecasting and predictive maintenance. Built with React/TSX frontend for interactive visualizations, FastAPI backend for robust APIs, and TimescaleDB for efficient time-series storage and analytics.
🚀 Features

Data Unification: Ingest and normalize data from external dashboards (e.g., inverters, weather APIs) via RESTful endpoints or batch uploads.
Time-Series Analytics: Hypertables and continuous aggregates in TimescaleDB for fast queries on metrics like kWh production, irradiance, and temperature.
ML Forecasting: Prophet-based predictions for future energy output, fault detection, and optimization—integrated seamlessly into the UI.
Interactive Dashboard: Responsive React components with charts (e.g., via Recharts or Chart.js) for historical trends, live updates, and forecast overlays.
Scalable Deployment: Dockerized services for easy local dev or cloud scaling (e.g., on AWS ECS or Kubernetes).
Security & Extensibility: JWT auth ready, Pydantic validation, and hooks for custom ML models.

Ideal for solar farm operators, energy traders, or researchers tracking renewable performance.
🛠 Tech Stack

Frontend: React + TypeScript (TSX), with TanStack Query for API handling and Recharts for visualizations.
Backend: FastAPI (Python) with SQLAlchemy ORM, Prophet for ML.
Database: TimescaleDB (PostgreSQL extension) for hypertables and materialized views.
DevOps: Docker Compose for local setup, Alembic for migrations.

📁 Project Structure
textsolar-dashboard/
├── backend/                  # FastAPI app (from previous skeleton)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── database.py
│   │   ├── crud.py
│   │   ├── ml_predictor.py
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── ingest.py
│   │       └── dashboard.py
│   ├── alembic/              # Migrations
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/                 # React/TSX app (your ready files)
│   ├── public/
│   ├── src/
│   │   ├── components/       # Dashboard UI (e.g., ChartViewer.tsx, ForecastPanel.tsx)
│   │   ├── hooks/            # API queries (e.g., useSolarData.ts)
│   │   ├── pages/            # Routes (e.g., DashboardPage.tsx)
│   │   ├── utils/            # Config (e.g., api.ts for FastAPI calls)
│   │   ├── App.tsx
│   │   └── index.tsx
│   ├── package.json
│   ├── tsconfig.json
│   └── Dockerfile
├── docker-compose.yml        # Orchestrates backend, frontend, DB
├── README.md                 # This file
├── .gitignore
└── .env                      # Shared env vars
🚀 Quick Start

Clone & Setup:
textgit clone <your-repo> solar-dashboard
cd solar-dashboard
cp .env.example .env  # Fill in DB creds

Run Locally:
textdocker-compose up -d  # Starts TimescaleDB, backend, frontend

Backend: http://localhost:8000 (docs at /docs)
Frontend: http://localhost:3000
Seed data: Run docker-compose exec backend python -c "from app.crud import create_reading; ..." or use a script.


Development:

Backend: cd backend && uvicorn app.main:app --reload
Frontend: cd frontend && npm start
Test ML: POST to /dashboard/forecast with {"site_id": 1, "horizon_days": 7}.


Deploy:

Build images: docker build -t solar-backend ./backend and similarly for frontend.
Push to registry, then deploy via Kubernetes or Heroku.



🤝 Contributing
Fork, PRs welcome! Focus on adding features like WebSocket live updates or advanced ML (e.g., LSTM for anomalies). See CONTRIBUTING.md for guidelines.
📄 License
MIT © [Your Name/Org] 2025. See LICENSE for details.
