import pandas as pd
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://civicpulse:changeme@localhost:5433/civicpulse"
)


def load_wards(csv_path: str):
    df = pd.read_csv(csv_path)

    engine = create_engine(DATABASE_URL)

    with engine.begin() as connection:
        for _, row in df.iterrows():
            connection.execute(
                text("""
                    INSERT INTO wards (ward_code, name, population)
                    VALUES (:ward_code, :name, :population)
                    ON CONFLICT (ward_code)
                    DO UPDATE SET
                        name = EXCLUDED.name,
                        population = EXCLUDED.population
                """),
                {
                    "ward_code": row["ward_code"],
                    "name": row["name"],
                    "population": int(row["population"]),
                },
            )

    print(f"Loaded {len(df)} wards")

def load_locations(csv_path: str):
    df = pd.read_csv(csv_path)

    engine = create_engine(DATABASE_URL)

    with engine.begin() as connection:
        for _, row in df.iterrows():

            result = connection.execute(
                text("""
                    SELECT ward_id
                    FROM wards
                    WHERE ward_code = :ward_code
                """),
                {
                    "ward_code": row["ward_code"]
                },
            )

            ward_id = result.scalar_one_or_none()

            if ward_id is None:
                raise ValueError(
                    f"Ward {row['ward_code']} does not exist"
                )

            connection.execute(
                text("""
                    INSERT INTO locations
                        (ward_id, latitude, longitude, address)
                    VALUES
                        (:ward_id, :latitude, :longitude, :address)
                """),
                {
                    "ward_id": ward_id,
                    "latitude": float(row["latitude"]),
                    "longitude": float(row["longitude"]),
                    "address": row["address"],
                },
            )

    print(f"Loaded {len(df)} locations")


if __name__ == "__main__":
    load_wards("data/raw/synthetic_wards.csv")
    load_locations("data/raw/synthetic_locations.csv")