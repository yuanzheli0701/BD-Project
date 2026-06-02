"""Format Weather raw JSON -> Parquet using Spark"""
import sys
from datetime import datetime, timezone
from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from jobs.common import get_raw_path, get_formatted_path

def run(date_str=None):
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    spark = SparkSession.builder \
        .appName("FormatWeather") \
        .master("local[*]") \
        .getOrCreate()

    raw_dir = get_raw_path("weather", date_str)
    json_path = str(raw_dir / "cities_weather.json")

    if not Path(json_path).exists():
        print(f"No weather data at {json_path}")
        spark.stop()
        return

    print(f"Reading from: {json_path}")

    df = spark.read.option("multiline", "true").json(json_path)
    df = df.withColumn("day", explode(col("forecast_daily"))) \
        .select(
            col("city"),
            col("country"),
            col("region"),
            col("lat"),
            col("lon"),
            col("fetch_date"),
            col("day.date").alias("weather_date"),
            col("day.temp_avg"),
            col("day.temp_min"),
            col("day.temp_max"),
            col("day.humidity_avg"),
            col("day.clouds_avg"),
            col("day.wind_speed_avg"),
            col("day.total_rain_3h"),
            col("day.is_rainy"),
        )

    out_dir = get_formatted_path("weather", date_str)
    out_path = str(out_dir / "weather.parquet")
    df.write.mode("overwrite").parquet(out_path)
    print(f"Written {df.count()} records to: {out_path}")

    spark.stop()

if __name__ == "__main__":
    run()
