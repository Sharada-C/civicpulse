# CivicPulse — Architecture

## 1. Data flow

```
Public Data / CSV / Open Data Sources
              |
              v
        Data Ingestion (Python / API)
              |
              v
        Kafka (streaming layer)
              |
              v
        Airflow (ETL orchestration)
              |
              v
        PySpark (transformation, once volume justifies it)
              |
              v
        PostgreSQL (OLTP tables + star-schema warehouse)
         |                                  |
         v                                  v
   ML Models                          FastAPI Backend
   - severity classifier              - REST API + auth
   - resolution-time regressor        - serves OLTP + warehouse data
   - DBSCAN hotspot clusters
         |                                  |
         +----------------+-----------------+
                          |
                          v
                Intelligence Layer
                          |
              +-----------+-----------+
              v                       v
        Power BI Dashboard      Local AI Analyst (Ollama)
```

## 2. Component responsibilities

| Component | Responsibility | Does NOT do |
|---|---|---|
| Ingestion (`pipelines/ingestion`) | Read CSV/API sources, generate labeled synthetic records where fields are missing | Business logic, cleaning |
| Kafka | Carry real-time complaint events between producer and consumer | Persistence, transformation |
| Airflow | Schedule and sequence the daily ETL DAG, handle retries/failures | Actual transformation logic (that lives in `pipelines/` and `spark/jobs/`, Airflow just calls it) |
| PySpark | Distributed transform once row counts exceed what Pandas handles well (rule of thumb: single-digit millions+) | Small day-to-day transforms — those stay in Pandas |
| PostgreSQL OLTP (`sql/schema`) | Source-of-truth transactional tables the API reads/writes | Analytics queries at scale (that's the warehouse's job) |
| PostgreSQL warehouse (`sql/warehouse`) | Star-schema fact/dimension tables, written only by ETL | Being written to directly by the API |
| FastAPI (`backend/app`) | REST API, auth, request validation, calling ML inference and analytics queries | Training ML models (that's `ml/training`) |
| ML models (`ml/`) | Train and version severity/resolution-time/hotspot models offline; inference code is imported by the backend | Live in the request path during training |
| AI Analyst (`ai/`) | Resolve a natural-language question to a fixed set of grounded SQL/analytics tool calls, then explain the *retrieved* numbers via Ollama | Free-form SQL generation by the LLM, or answering from the LLM's own "knowledge" |
| Power BI | Read-only reporting against the warehouse | Write anything back |

## 3. Priority Engine

The Priority Score is a **weighted sum of min-max normalized factors**, not raw addition (raw addition breaks because e.g. complaint volume and a 0–1 severity score are on wildly different scales).

```
priority_score =
    0.30 × severity_norm
  + 0.20 × frequency_norm
  + 0.15 × growth_norm
  + 0.15 × repeat_norm
  + 0.10 × population_norm
  + 0.10 × delay_norm
```

Weights are illustrative starting points — the *rationale* (severity and frequency matter most because they represent immediate citizen impact; population and delay are secondary modifiers) is what should be defended in an interview, not the exact numbers. See `sql/analytics/priority_score.sql` for the implementation and `docs/decisions/priority-weights.md` (add as you tune this) for the reasoning log.

## 4. OLTP vs. warehouse — why both

`sql/schema/` (OLTP) is normalized for fast, correct writes as complaints come in and get updated. `sql/warehouse/` (star schema) is denormalized for fast analytical reads (dashboard queries, priority scoring, AI analyst tool calls). The ETL step (`pipelines/transformation/load_warehouse.py`, `spark/jobs/transform_complaints.py`) is the explicit, documented bridge between the two — this separation, and being able to explain *why* it exists, is standard data-warehousing practice and a natural DBMS interview topic.

## 5. What "real-time" actually means here

Kafka in this project simulates a real-time complaint stream (`kafka/producers/complaint_producer.py` publishes synthetic or replayed events) rather than connecting to a live production complaint system, since no such live feed is available. This should be stated plainly in any interview or demo — "I simulated real-time ingestion with a producer script to demonstrate the streaming pattern" is an honest and reasonable answer.
