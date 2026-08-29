# CivicPulse

Open-source urban infrastructure intelligence platform. Ingests civic complaints and public datasets, detects problem hotspots, predicts severity and resolution time, and helps authorities prioritize limited resources.

> Status: scaffold generated from project blueprint. See `docs/roadmap.md` for build order and `docs/architecture.md` for system design.

## 1. Problem

Cities receive more infrastructure complaints than they can immediately resolve. CivicPulse answers: which problems should be addressed first, where, and why?

## 2. Architecture

```
Public Data / CSV --> Data Ingestion (Python) --> Kafka --> Airflow (ETL orchestration)
    --> PySpark (transform) --> PostgreSQL (OLTP + warehouse)
        --> ML Models (severity, resolution time, hotspots)
        --> FastAPI Backend (REST APIs, auth)
            --> Intelligence Layer --> Power BI Dashboard
                                    --> Local LLM AI Analyst (Ollama, tool-grounded)
```

Full diagram and rationale: `docs/architecture.md`.

## 3. Tech stack

Python, PostgreSQL, Pandas, FastAPI, SQLAlchemy, Pydantic, GeoPandas, scikit-learn, XGBoost, Power BI, Apache Airflow, PySpark, Apache Kafka, Ollama, Docker, GitHub Actions.

No paid APIs anywhere in the stack.

## 4. Repository layout

```
civicpulse/
├── backend/        FastAPI app (api / models / schemas / services / repositories / ml / db / core)
├── data/           raw + processed data (synthetic data clearly labeled)
├── pipelines/       ingestion / transformation / validation scripts
├── airflow/dags/    orchestration DAGs
├── spark/jobs/      PySpark transformation jobs
├── kafka/           producers + consumers for the real-time complaint stream
├── ml/              training, inference, saved models
├── sql/             OLTP schema, warehouse star schema, analytics queries
├── dashboard/powerbi/  Power BI dashboard notes/exports
├── ai/              tool-grounded LLM analyst: prompts + callable tools
├── docker/          Dockerfiles
└── docs/            architecture, ERD, roadmap
```

## 5. Getting started (local)

```bash
cp .env.example .env
docker compose up -d postgres        # start just the database first
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for the interactive API.

To bring up the full stack (Postgres + Kafka + Airflow + Ollama):

```bash
docker compose up -d
```

## 6. Build order

See `docs/roadmap.md` — the project is intentionally staged so early milestones (DB schema + SQL analytics, then FastAPI) are already interview-presentable before Kafka/Spark/Airflow are added.

## 7. What this is not

No paid LLM APIs, no Kubernetes, no unnecessary microservices, no framework added without a stated reason. See `docs/architecture.md` §"Decisions we didn't make" for the reasoning.
