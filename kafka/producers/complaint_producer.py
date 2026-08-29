"""
Publishes new-complaint events to the 'complaints' Kafka topic.

Honest note (see docs/architecture.md "Kafka" section): civic complaints don't
arrive as a real live event stream by default. In production this would be
triggered by the citizen-facing complaint-submission endpoint (app/api/complaints.py
POST handler calling this producer). For local development/demo, run this script
standalone to simulate a live stream of incoming complaints.
"""
import json
import os
import random
import time

from kafka import KafkaProducer

BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC = os.environ.get("KAFKA_COMPLAINTS_TOPIC", "complaints")

CATEGORIES = ["POTHOLE", "STREETLIGHT", "GARBAGE", "WATER_LEAK", "DRAINAGE"]
WARDS = [f"W{n}" for n in range(1, 21)]
SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def build_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )


def make_event(complaint_id: int) -> dict:
    return {
        "complaint_id": complaint_id,
        "category": random.choice(CATEGORIES),
        "ward": random.choice(WARDS),
        "severity": random.choice(SEVERITIES),
        "timestamp": time.time(),
    }


def run(n_events: int = 100, delay_seconds: float = 1.0):
    producer = build_producer()
    for i in range(1, n_events + 1):
        event = make_event(i)
        producer.send(TOPIC, value=event)
        print(f"Produced: {event}")
        time.sleep(delay_seconds)
    producer.flush()


if __name__ == "__main__":
    run()
