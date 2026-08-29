"""
Generates synthetic civic complaint records for development/testing when real
open-data records don't provide enough fields. Every record is stamped
is_synthetic=True so it can never be confused with real civic data downstream.

Usage:
    python generate_synthetic_complaints.py --count 5000 --out data/raw/synthetic_complaints.csv
"""
import argparse
import csv
import random
from datetime import datetime, timedelta
random.seed(42)
REFERENCE_DATE = datetime(2026, 8, 1)
NUM_WARDS = 10
LOCATIONS_PER_WARD = 5

CATEGORIES = ["POTHOLE", "STREETLIGHT", "GARBAGE", "WATER_LEAK", "DRAINAGE", "ILLEGAL_PARKING"]
WARDS = [f"W{n:03d}" for n in range(1, NUM_WARDS + 1)]
SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
STATUSES = ["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"]

# Rough bounding box — Bengaluru city extent, adjust for your target city.
LAT_RANGE = (12.85, 13.10)
LON_RANGE = (77.45, 77.75)


CATEGORY_DEPARTMENT_MAP = {
    "POTHOLE": "ROADS",
    "STREETLIGHT": "ELECTRICITY",
    "GARBAGE": "SANITATION",
    "WATER_LEAK": "WATER",
    "DRAINAGE": "DRAINAGE",
    "ILLEGAL_PARKING": "ROADS",
}
def generate_wards() -> list[dict]:
    wards = []

    for i, ward_code in enumerate(WARDS, start=1):
        wards.append({
            "ward_code": ward_code,
            "name": f"Ward {i}",
            "population": random.randint(40000, 120000),
        })

    return wards

def generate_locations(wards: list[dict]) -> list[dict]:
    locations = []

    for ward in wards:
        for i in range(1, LOCATIONS_PER_WARD + 1):
            locations.append({
                "ward_code": ward["ward_code"],
                "latitude": round(random.uniform(*LAT_RANGE), 6),
                "longitude": round(random.uniform(*LON_RANGE), 6),
                "address": f"{ward['name']} - Location {i}",
            })

    return locations


def generate_row(complaint_id: int, locations: list[dict]) -> dict:
    location = random.choice(locations)

    category = random.choice(CATEGORIES)
    severity = random.choice(SEVERITIES)
    status = random.choice(STATUSES)

    created = REFERENCE_DATE - timedelta(days=random.randint(0, 365))

    resolved = None

    if status in ("RESOLVED", "CLOSED"):
        resolved = created + timedelta(days=random.randint(1, 30))

    return {
        "complaint_id": complaint_id,
        "created_at": created.isoformat(),
        "category": category,
        "description": f"Synthetic {category.lower()} complaint.",
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "ward": location["ward_code"],
        "severity": severity,
        "status": status,
        "department": CATEGORY_DEPARTMENT_MAP[category],
        "resolved_at": resolved.isoformat() if resolved else "",
        "is_synthetic": True,
    }



def write_csv(rows: list[dict], out_path: str):
    if not rows:
        return

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)


def main(count: int, out_path: str):
    wards = generate_wards()
    locations = generate_locations(wards)

    complaints = [
        generate_row(i, locations)
        for i in range(1, count + 1)
    ]

    write_csv(
        wards,
        "data/raw/synthetic_wards.csv"
    )

    write_csv(
        locations,
        "data/raw/synthetic_locations.csv"
    )

    write_csv(
        complaints,
        out_path
    )

    print(f"Generated {len(wards)} wards")
    print(f"Generated {len(locations)} locations")
    print(f"Generated {len(complaints)} complaints")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=5000)
    parser.add_argument("--out", type=str, default="data/raw/synthetic_complaints.csv")
    args = parser.parse_args()
    main(args.count, args.out)
