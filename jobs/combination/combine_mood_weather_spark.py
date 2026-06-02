"""Combine Last.fm + Weather -> CDI using Spark"""
import sys
from datetime import datetime, timezone
from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, avg, count, round as sround, when, lit, concat, expr
)
from pyspark.sql.types import FloatType

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from jobs.common import get_formatted_path, get_combined_path

def run(date_str=None, source="lastfm"):
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    spark = SparkSession.builder \
        .appName("CombineMoodWeather") \
        .master("local[*]") \
        .config("spark.sql.adaptive.enabled", "true") \
        .getOrCreate()

    music_path = str(get_formatted_path(source, date_str) / f"{source}.parquet")
    weather_path = str(get_formatted_path("weather", date_str) / "weather.parquet")

    print(f"Reading {source}: {music_path}")
    music = spark.read.parquet(music_path)
    print(f"Reading Weather: {weather_path}")
    wx = spark.read.parquet(weather_path)

    # Aggregate Spotify per region
    music_agg = music.groupBy("region", "fetch_date").agg(
        avg("valence").alias("avg_valence"),
        avg("energy").alias("avg_energy"),
        avg("danceability").alias("avg_danceability"),
        avg("acousticness").alias("avg_acousticness"),
        avg("tempo").alias("avg_tempo"),
        avg("loudness").alias("avg_loudness"),
        count("track_id").alias("track_count"),
    )

    # Join with weather
    combined = music_agg.join(
        wx,
        (music_agg.region == wx.region) &
            (music_agg.fetch_date == wx.weather_date),
        "inner"
    )

    # Compute CDI
    rain_bonus = when(col("is_rainy") == True, lit(0.3)).otherwise(lit(0.0))
    cloud_bonus = (col("clouds_avg") / lit(100.0)) * lit(0.2)
    humidity_bonus = (col("humidity_avg") / lit(100.0)) * lit(0.1)
    sadness = lit(1.0) - col("avg_valence")
    weather_factor = lit(1.0) + rain_bonus + cloud_bonus + humidity_bonus

    combined = combined.withColumn("depression_index", sadness * weather_factor)

    # Mood category
    combined = combined.withColumn("mood_category",
        when(col("depression_index") < 0.3, "Happy & Sunny")
        .when(col("depression_index") < 0.6, "Slightly Melancholic")
        .when(col("depression_index") < 0.9, "Moderately Sad")
        .when(col("depression_index") < 1.2, "Quite Depressed")
        .otherwise("Deeply Depressed")
    )

    # Round numeric columns
    for c in ["avg_valence", "avg_energy", "avg_danceability", "avg_acousticness",
              "avg_tempo", "avg_loudness", "depression_index"]:
        combined = combined.withColumn(c, sround(col(c), 4))

    # Select output
    result = combined.select(
        col("city"), col("country"), col("region"),
        col("weather_date").alias("date"),
        col("lat"), col("lon"),
        col("temp_avg"), col("temp_min"), col("temp_max"),
        col("humidity_avg"), col("clouds_avg"),
        col("wind_speed_avg"), col("total_rain_3h"), col("is_rainy"),
        col("avg_valence"), col("avg_energy"), col("avg_danceability"),
        col("avg_acousticness"), col("avg_tempo"), col("avg_loudness"),
        col("track_count"), col("depression_index"), col("mood_category"),
        lit(date_str).alias("computation_date"),
        lit(source).alias("source"),
    )

    # Save
    out_dir = get_combined_path(date_str)
    out_path = str(out_dir / "combined.parquet")
    result.write.mode("overwrite").parquet(out_path)
    print(f"\nSaved {result.count()} records to: {out_path}")

    # Show results
    print(f"\n{'='*70}")
    print(f"City Depression Index - {date_str} (source: {source})")
    print(f"{'='*70}")
    result.orderBy(col("depression_index").desc()).select(
        "city", "avg_valence", "is_rainy", "clouds_avg", "depression_index", "mood_category"
    ).show(10, truncate=False)

    spark.stop()

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--date", default=None)
    p.add_argument("--source", default="lastfm", choices=["spotify", "lastfm"])
    args = p.parse_args()
    run(args.date, args.source)
