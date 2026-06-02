"""Format Last.fm raw JSON -> Parquet using Spark"""
import sys
from datetime import datetime, timezone
from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, ArrayType
from pyspark.sql.functions import col, lit, explode, when

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from jobs.common import get_raw_path, get_formatted_path

def run(date_str=None):
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    spark = SparkSession.builder \
        .appName("FormatLastfm") \
        .master("local[*]") \
        .config("spark.sql.adaptive.enabled", "true") \
        .getOrCreate()

    raw_dir = get_raw_path("lastfm", date_str)
    out_dir = get_formatted_path("lastfm", date_str)

    # Read all region JSON files
    json_paths = [str(p) for p in sorted(raw_dir.glob("*.json"))]
    if not json_paths:
        print("No data found!")
        spark.stop()
        return

    print(f"Reading from: {raw_dir}")

    # Use Spark's JSON reader with schema inference
    df = spark.read.option("multiline", "true").json(json_paths)

    # Explode tracks array
    df = df.withColumn("track", explode(col("tracks"))) \
        .select(
            col("region"),
            col("fetch_date"),
            col("track.track_id").alias("track_id"),
            col("track.name").alias("name"),
            col("track.artists").getItem(0).alias("artist"),
            when(col("track.danceability").isNull(), 0.5).otherwise(col("track.danceability")).alias("danceability"),
            when(col("track.energy").isNull(), 0.5).otherwise(col("track.energy")).alias("energy"),
            col("track.key"),
            col("track.loudness"),
            col("track.mode"),
            col("track.speechiness"),
            col("track.acousticness"),
            col("track.instrumentalness"),
            col("track.liveness"),
            when(col("track.valence").isNull(), 0.5).otherwise(col("track.valence")).alias("valence"),
            col("track.tempo"),
            col("track.duration_ms"),
            col("track.time_signature"),
            col("track.lastfm_listeners").alias("listeners"),
            lit(date_str).alias("ingestion_date"),
        )

    count = df.count()
    print(f"  {count} tracks processed")

    # Write Parquet
    out_path = str(out_dir / "lastfm.parquet")
    df.write.mode("overwrite").parquet(out_path)
    print(f"Written to: {out_path}")

    spark.stop()

if __name__ == "__main__":
    run()
