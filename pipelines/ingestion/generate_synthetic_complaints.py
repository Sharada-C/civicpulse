"""
Generates realistic synthetic civic complaint records.

The synthetic data intentionally contains learnable relationships between:
    category -> severity
    historical repeats -> severity
    severity -> resolution time
    department -> resolution time
    ward workload -> resolution time

Complaint IDs are identifiers only and are not used to generate targets.

Usage:
    python pipelines/ingestion/generate_synthetic_complaints.py \
        --count 5000 \
        --out data/raw/synthetic_complaints.csv
"""

import argparse
import csv
import random
from datetime import datetime, timedelta


random.seed(42)

REFERENCE_DATE = datetime(2026, 8, 1)

NUM_WARDS = 10
LOCATIONS_PER_WARD = 5

CATEGORIES = [
    "POTHOLE",
    "STREETLIGHT",
    "GARBAGE",
    "WATER_LEAK",
    "DRAINAGE",
    "ILLEGAL_PARKING",
]

WARDS = [
    f"W{n:03d}"
    for n in range(1, NUM_WARDS + 1)
]

SEVERITIES = [
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
]

STATUSES = [
    "OPEN",
    "IN_PROGRESS",
    "RESOLVED",
    "CLOSED",
]

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


SEVERITY_WEIGHTS = {
    "POTHOLE": {
        "LOW": 0.35,
        "MEDIUM": 0.40,
        "HIGH": 0.20,
        "CRITICAL": 0.05,
    },
    "STREETLIGHT": {
        "LOW": 0.45,
        "MEDIUM": 0.35,
        "HIGH": 0.15,
        "CRITICAL": 0.05,
    },
    "GARBAGE": {
        "LOW": 0.40,
        "MEDIUM": 0.40,
        "HIGH": 0.15,
        "CRITICAL": 0.05,
    },
    "WATER_LEAK": {
        "LOW": 0.15,
        "MEDIUM": 0.35,
        "HIGH": 0.35,
        "CRITICAL": 0.15,
    },
    "DRAINAGE": {
        "LOW": 0.15,
        "MEDIUM": 0.30,
        "HIGH": 0.35,
        "CRITICAL": 0.20,
    },
    "ILLEGAL_PARKING": {
        "LOW": 0.50,
        "MEDIUM": 0.35,
        "HIGH": 0.12,
        "CRITICAL": 0.03,
    },
}


DEPARTMENT_PENALTY = {
    "ROADS": 2.0,
    "ELECTRICITY": 1.0,
    "SANITATION": 2.5,
    "WATER": 1.5,
    "DRAINAGE": 3.0,
}


SEVERITY_BASE_DAYS = {
    "LOW": 7,
    "MEDIUM": 5,
    "HIGH": 3,
    "CRITICAL": 1,
}


DESCRIPTIONS = {
    "POTHOLE": (
        "Large pothole causing traffic and vehicle damage."
    ),
    "STREETLIGHT": (
        "Streetlight not functioning and road is poorly illuminated."
    ),
    "GARBAGE": (
        "Garbage accumulation reported near residential area."
    ),
    "WATER_LEAK": (
        "Water leakage reported from damaged pipeline."
    ),
    "DRAINAGE": (
        "Drainage blockage causing water accumulation."
    ),
    "ILLEGAL_PARKING": (
        "Vehicle parked illegally and obstructing traffic."
    ),
}


def generate_wards() -> list[dict]:
    """Generate ward reference data."""

    wards = []

    for i, ward_code in enumerate(
        WARDS,
        start=1,
    ):
        wards.append(
            {
                "ward_code": ward_code,
                "name": f"Ward {i}",
                "population": random.randint(
                    40000,
                    120000,
                ),
            }
        )

    return wards


def generate_locations(
    wards: list[dict],
) -> list[dict]:
    """Generate five geographic locations per ward."""

    locations = []

    for ward in wards:
        for i in range(
            1,
            LOCATIONS_PER_WARD + 1,
        ):
            locations.append(
                {
                    "ward_code": ward["ward_code"],
                    "latitude": round(
                        random.uniform(
                            *LAT_RANGE
                        ),
                        6,
                    ),
                    "longitude": round(
                        random.uniform(
                            *LON_RANGE
                        ),
                        6,
                    ),
                    "address": (
                        f"{ward['name']} - Location {i}"
                    ),
                }
            )

    return locations


def generate_base_rows(
    count: int,
    locations: list[dict],
) -> list[dict]:
    """
    Generate complaint events without target-dependent fields.

    Dates, wards and categories are created first.
    This prevents complaint_id from influencing targets.
    """

    rows = []

    for complaint_id in range(
        1,
        count + 1,
    ):
        location = random.choice(locations)

        created = (
            REFERENCE_DATE
            - timedelta(
                days=random.randint(
                    0,
                    365,
                )
            )
            - timedelta(
                minutes=random.randint(
                    0,
                    1439,
                )
            )
        )

        category = random.choice(
            CATEGORIES
        )

        rows.append(
            {
                "complaint_id": complaint_id,
                "created_at": created,
                "category": category,
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "ward": location["ward_code"],
            }
        )

    # Historical processing must follow time,
    # not complaint ID.
    rows.sort(
        key=lambda row: row["created_at"]
    )

    return rows


def generate_targets(
    rows: list[dict],
) -> list[dict]:
    """
    Generate severity, status and resolution time
    using historical information available at complaint time.
    """

    ward_counts = {}
    ward_category_counts = {}

    for row in rows:

        ward = row["ward"]
        category = row["category"]

        historical_repeat_count = (
            ward_category_counts.get(
                (ward, category),
                0,
            )
        )

        current_ward_workload = (
            ward_counts.get(
                ward,
                0,
            )
        )

        # -----------------------------------------------------
        # Severity
        # -----------------------------------------------------

        weights = SEVERITY_WEIGHTS[
            category
        ]

        severity = random.choices(
            list(weights.keys()),
            weights=list(weights.values()),
            k=1,
        )[0]

        # Historical repeats increase severity.
        if (
            historical_repeat_count >= 3
            and random.random() < 0.45
        ):
            severity = random.choice(
                [
                    "HIGH",
                    "CRITICAL",
                ]
            )

        elif (
            historical_repeat_count >= 1
            and random.random() < 0.20
        ):
            severity = random.choice(
                [
                    "MEDIUM",
                    "HIGH",
                ]
            )

        # -----------------------------------------------------
        # Status
        # -----------------------------------------------------

        status = random.choices(
            STATUSES,
            weights=[
                0.15,
                0.20,
                0.50,
                0.15,
            ],
            k=1,
        )[0]

        # -----------------------------------------------------
        # Resolution time
        # -----------------------------------------------------

        resolved = None

        if status in (
            "RESOLVED",
            "CLOSED",
        ):

            base_days = (
                SEVERITY_BASE_DAYS[
                    severity
                ]
            )

            workload_penalty = min(
                current_ward_workload * 0.03,
                8,
            )

            repeat_penalty = min(
                historical_repeat_count * 0.5,
                5,
            )

            department = (
                CATEGORY_DEPARTMENT_MAP[
                    category
                ]
            )

            department_penalty = (
                DEPARTMENT_PENALTY[
                    department
                ]
            )

            noise = random.uniform(
                -1.5,
                1.5,
            )

            resolution_days = max(
                1,
                base_days
                + workload_penalty
                + repeat_penalty
                + department_penalty
                + noise,
            )

            resolved = (
                row["created_at"]
                + timedelta(
                    days=resolution_days
                )
            )

        # -----------------------------------------------------
        # Complete row
        # -----------------------------------------------------

        row["description"] = (
            DESCRIPTIONS[category]
        )

        row["severity"] = severity
        row["status"] = status

        row["department"] = (
            CATEGORY_DEPARTMENT_MAP[
                category
            ]
        )

        row["resolved_at"] = (
            resolved
            if resolved
            else None
        )

        row["is_synthetic"] = True

        # Update historical state AFTER
        # generating the current complaint.
        ward_counts[ward] = (
            ward_counts.get(
                ward,
                0,
            )
            + 1
        )

        key = (
            ward,
            category,
        )

        ward_category_counts[key] = (
            ward_category_counts.get(
                key,
                0,
            )
            + 1
        )

    return rows


def write_csv(
    rows: list[dict],
    out_path: str,
):
    """Write rows to CSV."""

    if not rows:
        return

    with open(
        out_path,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=list(
                rows[0].keys()
            ),
        )

        writer.writeheader()
        writer.writerows(rows)


def main(
    count: int,
    out_path: str,
):
    wards = generate_wards()

    locations = generate_locations(
        wards
    )

    complaints = generate_base_rows(
        count,
        locations,
    )

    complaints = generate_targets(
        complaints
    )

    write_csv(
        wards,
        "data/raw/synthetic_wards.csv",
    )

    write_csv(
        locations,
        "data/raw/synthetic_locations.csv",
    )

    write_csv(
        complaints,
        out_path,
    )

    print(
        f"Generated {len(wards)} wards"
    )

    print(
        f"Generated {len(locations)} locations"
    )

    print(
        f"Generated {len(complaints)} complaints"
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--count",
        type=int,
        default=5000,
    )

    parser.add_argument(
        "--out",
        type=str,
        default=(
            "data/raw/"
            "synthetic_complaints.csv"
        ),
    )

    args = parser.parse_args()

    main(
        args.count,
        args.out,
    )
