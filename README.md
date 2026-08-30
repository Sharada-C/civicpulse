# CivicPulse

CivicPulse is an urban infrastructure intelligence platform that analyzes civic complaints, identifies problem hotspots, predicts complaint severity and resolution time, and helps prioritize limited municipal resources.

The project combines data engineering, machine learning, PostgreSQL analytics, REST APIs, Docker, Apache Airflow, and Power BI to turn raw civic complaint data into actionable insights.

---

## 1. Problem Statement

Cities receive large volumes of complaints related to infrastructure issues such as:

- Garbage
- Water leaks
- Drainage
- Illegal parking
- Streetlights
- Potholes

Simply counting complaints does not provide enough information to determine which problems should be addressed first.

CivicPulse addresses this by combining:

- Historical complaint data
- Geographic information
- Complaint severity
- Resolution performance
- Repeat complaint patterns
- Machine-learning predictions
- Explainable priority scoring

The goal is to answer:

> **Which civic problems should be addressed first, where are they occurring, and why?**

---

## 2. Architecture

```text
                         CivicPulse
                             |
              +--------------+--------------+
              |                             |
        Data / ETL Pipeline             ML Pipeline
              |                             |
              v                             v
        Source Complaint Data       Severity Prediction
              |                     Resolution Prediction
              v                             |
        Transformation                       |
              |                             |
              +-------------+---------------+
                            |
                            v
                    PostgreSQL Database
                    +------------------+
                    |     OLTP Data    |
                    +------------------+
                            |
                            v
                    Analytical Warehouse
                       Star Schema
                            |
                +-----------+-----------+
                |                       |
                v                       v
          SQL Analytics          Priority Engine
                |                       |
                +-----------+-----------+
                            |
                            v
                     FastAPI Backend
                            |
                     +------+------+
                     |             |
                     v             v
                 REST APIs     Power BI
                              Dashboard

Supporting Services:
- Apache Airflow
- Apache Kafka
- PySpark
- Ollama
- Docker Compose