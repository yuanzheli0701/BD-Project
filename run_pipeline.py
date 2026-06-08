
import sys, os, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

def main():
    parser = argparse.ArgumentParser(description="City Mood Weather Pipeline")
    parser.add_argument("--date", default=None)
    parser.add_argument("--source", default="lastfm", choices=["spotify", "lastfm"])
    parser.add_argument("--s3", action="store_true", help="Use S3 distributed storage")
    parser.add_argument("--spark", action="store_true", help="Use Spark for transformations")
    args = parser.parse_args()

    date_arg = [args.date] if args.date else []

    print("=" * 60)
    print("CITY MOOD x WEATHER - FULL PIPELINE")
    print("=" * 60)

    # Step 1: Ingestion
    print("\n[1/4] INGESTION")
    os.system(f"python -m jobs.ingestion.ingest_weather {' '.join(date_arg)}")
    os.system(f"python -m jobs.ingestion.ingest_lastfm {' '.join(date_arg)}")

    if args.s3:
        print("  -> Syncing to S3...")
        from jobs.s3_storage import sync_to_s3
        sync_to_s3()

    # Step 2: Formatting
    print("\n[2/4] FORMATTING")
    if args.spark:
        os.system(f"spark-submit jobs/formatting/format_{args.source}_spark.py")
        os.system(f"spark-submit jobs/formatting/format_weather_spark.py")
    else:
        os.system(f"python jobs/formatting/format_{args.source}.py")
        os.system(f"python jobs/formatting/format_weather.py")

    # Step 3: Combination
    print("\n[3/4] COMBINATION (CDI Calculation)")
    if args.spark:
        os.system(f"spark-submit jobs/combination/combine_mood_weather_spark.py --source {args.source} {' '.join(date_arg)}")
    else:
        os.system(f"python jobs/combination/combine_mood_weather.py --source {args.source} {' '.join(date_arg)}")

    # Step 4: Indexing
    print("\n[4/4] INDEXING TO ELASTICSEARCH")
    from jobs.indexing.index_to_es import run as index_run
    if args.date:
        index_run(args.date)
    else:
        index_run()

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE!")
    print(f"Data saved to: data/raw/, data/formatted/, data/combined/")
    print("Open http://localhost:5601 for Kibana Dashboard")
    print("=" * 60)

if __name__ == "__main__":
    main()
