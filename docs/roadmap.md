# CivicPulse — Roadmap

## 12-stage build order

| Stage | Builds | Main learning |
|---|---|---|
| 1 | Problem definition + architecture | System design |
| 2 | PostgreSQL OLTP schema | DBMS + SQL |
| 3 | Data ingestion (CSV/API → Postgres) | Python + Pandas |
| 4 | Analytics engine (warehouse + SQL) | Advanced SQL |
| 5 | FastAPI backend | Backend architecture |
| 6 | Power BI dashboard | Data analytics / BI |
| 7 | ML models (severity, resolution time, hotspots) | Machine learning |
| 8 | Airflow orchestration | Data engineering |
| 9 | PySpark | Distributed processing |
| 10 | Kafka | Streaming |
| 11 | AI analyst (Ollama, grounded tool calls) | LLM + tool use |
| 12 | Docker + CI/CD | DevOps |

## Milestones (push to GitHub incrementally — do not wait for stage 12)

- **Milestone 1** — PostgreSQL schema + SQL analytics queries. *Already interview-ready on its own.*
- **Milestone 2** — Python ETL + FastAPI backend.
- **Milestone 3** — Power BI + ML models.
- **Milestone 4** — Airflow + PySpark.
- **Milestone 5** — Kafka + AI analyst + Docker Compose (full stack).

## Current status

Repository scaffold generated: directory structure, OLTP + warehouse SQL, FastAPI skeleton (complaints/analytics/predictions/priorities/auth routers, SQLAlchemy models, repository/service layers), Airflow DAG skeleton, Kafka producer stub, PySpark job stub, ML training/inference stubs, AI tool-calling skeleton, Docker Compose, CI workflow, pytest skeleton.

**Not yet done:** loading real or synthetic data, training actual models, building the Power BI report against real numbers, writing the Ollama tool-selection prompt, filling in the ETL logic body, running the full Docker stack end-to-end.

## Future improvements (post-MVP)

- Expand data sources beyond the initial open dataset once the pipeline is proven.
- Add SLA-breach alerting (email/notification when a complaint crosses its target resolution time).
- Add a lightweight public-facing complaint submission form (kept out of MVP scope deliberately — see README "what this deliberately does not include").
- Explore a free-tier cloud deployment for demo purposes once local development is stable.
