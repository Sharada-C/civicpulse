"""
PySpark equivalent of pipelines/transformation/load_warehouse.py, for volumes where
Pandas stops being appropriate (README §23 — tens of millions of rows).

Run with:
    spark-submit spark/jobs/transform_complaints.py \
        --input data/raw/complaints.csv --output data/processed/fact_complaints_parquet
"""
import argparse

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def build_spark_session(app_name: str = "civicpulse-transform") -> SparkSession:
    return SparkSession.builder.appName(app_name).getOrCreate()


def transform(spark: SparkSession, input_path: str):
    df = spark.read.option("header", True).option("inferSchema", True).csv(input_path)

    # Normalize category (same rule as pipelines/validation/validate_complaints.py)
    df = df.withColumn(
        "category",
        F.upper(F.regexp_replace(F.trim(F.col("category")), r"[\s-]+", "_")),
    )

    # Filter obviously invalid coordinates
    df = df.filter(
        (F.col("latitude").between(-90, 90)) & (F.col("longitude").between(-180, 180))
    )

    # Derive date_key for the warehouse join
    df = df.withColumn("date_key", F.date_format(F.col("created_at"), "yyyyMMdd").cast("int"))

    # Aggregate example: complaints per ward per day (feeds fact_complaints / dashboard)
    ward_daily = (
        df.groupBy("ward", "date_key")
        .agg(
            F.count("*").alias("complaint_count"),
            F.avg("resolution_time_days").alias("avg_resolution_days"),
        )
        .orderBy(F.desc("complaint_count"))
    )

    return df, ward_daily


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    spark = build_spark_session()
    clean_df, ward_daily = transform(spark, args.input)

    clean_df.write.mode("overwrite").parquet(f"{args.output}/complaints")
    ward_daily.write.mode("overwrite").parquet(f"{args.output}/ward_daily_summary")

    print(f"Wrote transformed data to {args.output}")
    spark.stop()


if __name__ == "__main__":
    main()
