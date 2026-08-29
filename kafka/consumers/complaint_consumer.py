"""
Consumes complaint events from Kafka, validates them, and writes them into the
staging table for the next Airflow run to pick up — matching README §24:
New Complaint -> Kafka Producer -> topic -> Kafka Consumer -> Validation -> PostgreSQL
"""
import json
import os

from kafka import KafkaConsumer
from sqlalchemy import create_engine, text

BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC = os.environ.get("KAFKA_COMPLAINTS_TOPIC", "complaints")
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg2://civicpulse:changeme@localhost:5432/civicpulse"
)

VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def is_valid(event: dict) -> bool:
    return (
        "complaint_id" in event
        and event.get("severity") in VALID_SEVERITIES
        and event.get("category") is not None
        and event.get("ward") is not None
    )


def run():
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        group_id="civicpulse-complaint-consumer",
    )
    engine = create_engine(DATABASE_URL)

    print(f"Listening on topic '{TOPIC}'...")
    for message in consumer:
        event = message.value
        if not is_valid(event):
            print(f"Dropped invalid event: {event}")
            continue

        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO staging_complaints_realtime (complaint_id, category, ward, severity, received_at)
                VALUES (:complaint_id, :category, :ward, :severity, now())
                ON CONFLICT (complaint_id) DO NOTHING
            """), event)

        print(f"Loaded: {event}")


if __name__ == "__main__":
    run()
