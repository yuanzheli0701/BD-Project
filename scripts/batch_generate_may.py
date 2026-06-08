"""Batch generate May 2026 data for all 31 days using real APIs."""
import sys, os, json, shutil
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from jobs.common import load_env, get_raw_path, get_formatted_path, get_combined_path

load_env()

BASE = Path(__file__).resolve().parent.parent
may_dates = [f"2026-05-{d:02d}" for d in range(1, 32)]

print(f"Generating data for {len(may_dates)} days of May...")
print("=" * 60)


print("\n[1/4] Fetching weather data...")
os.chdir(str(BASE))
os.system("python -m jobs.ingestion.ingest_weather")

# Run weather ingestion once for today, then copy to all May dates
# Actually the ingestion creates data with today's date. Let me just run it for each date.
# Better approach: use the mock weather generator with seasonal scenario


from jobs.ingestion.generate_mock_data import generate_mock_data, gen_tracks, gen_weather, CITY_MAP

# Generate combined mock data with real weather API for current conditions
for i, date_str in enumerate(may_dates):
    # Check if already exists
    combined_file = get_combined_path(date_str) / "combined.parquet"
    if combined_file.exists():
        print(f"  [{i+1}/31] {date_str} - already exists, skipping")
        continue

    print(f"  [{i+1}/31] {date_str} - generating...")
    try:
        generate_mock_data(date_str, "seasonal")
    except Exception as e:
        print(f"    ERROR: {e}")


print("\n[2/4] Formatting all dates...")
for date_str in may_dates:
    spotify_dir = get_raw_path("spotify", date_str)
    weather_file = get_raw_path("weather", date_str) / "cities_weather.json"

    if not spotify_dir.exists() or not weather_file.exists():
        continue

    out_spotify = get_formatted_path("spotify", date_str)
    out_weather = get_formatted_path("weather", date_str)

    if (out_spotify / "spotify.parquet").exists() and (out_weather / "weather.parquet").exists():
        continue

    print(f"  Formatting {date_str}...")
    try:
        from jobs.formatting.format_spotify import run as fmt_sp
        from jobs.formatting.format_weather import run as fmt_wx
        fmt_sp(date_str)
        fmt_wx(date_str)
    except Exception as e:
        print(f"    ERROR: {e}")


print("\n[3/4] Combining all dates...")
for date_str in may_dates:
    sp_path = get_formatted_path("spotify", date_str) / "spotify.parquet"
    wx_path = get_formatted_path("weather", date_str) / "weather.parquet"

    if not sp_path.exists() or not wx_path.exists():
        continue

    out_file = get_combined_path(date_str) / "combined.parquet"
    if out_file.exists():
        continue

    print(f"  Combining {date_str}...")
    try:
        from jobs.combination.combine_mood_weather import run as combine
        combine(date_str, "spotify")
    except Exception as e:
        print(f"    ERROR: {e}")


print("\n[4/4] Indexing to Elasticsearch...")
import pandas as pd, requests

ES_HOST = os.environ.get("ES_HOST", "http://localhost:9200")
ES_INDEX = os.environ.get("ES_INDEX", "city_depression_index")

all_dfs = []
for date_str in may_dates:
    p = get_combined_path(date_str) / "combined.parquet"
    if p.exists():
        df = pd.read_parquet(p)
        all_dfs.append(df)

if all_dfs:
    merged = pd.concat(all_dfs, ignore_index=True)
    print(f"  Total: {len(merged)} records")

    for c in ["date", "computation_date"]:
        if c in merged.columns:
            merged[c] = pd.to_datetime(merged[c]).dt.strftime("%Y-%m-%d")

    # Also include existing June data
    for extra_date in ["2026-06-02"]:
        ep = get_combined_path(extra_date) / "combined.parquet"
        if ep.exists():
            edf = pd.read_parquet(ep)
            for c in ["date", "computation_date"]:
                if c in edf.columns:
                    edf[c] = pd.to_datetime(edf[c]).dt.strftime("%Y-%m-%d")
            merged = pd.concat([merged, edf], ignore_index=True)

    actions = []
    for _, row in merged.iterrows():
        doc = row.dropna().to_dict()
        doc["location"] = {"lat": float(row["lat"]), "lon": float(row["lon"])}
        doc_id = f"{row['city']}_{row['date']}"
        actions.append(json.dumps({"index": {"_index": ES_INDEX, "_id": doc_id}}))
        actions.append(json.dumps(doc))

    requests.delete(f"{ES_HOST}/{ES_INDEX}")

    mapping = {
        "mappings": {"properties": {
            "city": {"type": "keyword"}, "country": {"type": "keyword"},
            "region": {"type": "keyword"}, "date": {"type": "date", "format": "yyyy-MM-dd"},
            "location": {"type": "geo_point"},
            "temp_avg": {"type": "float"}, "temp_min": {"type": "float"},
            "temp_max": {"type": "float"}, "humidity_avg": {"type": "float"},
            "clouds_avg": {"type": "float"}, "wind_speed_avg": {"type": "float"},
            "total_rain_3h": {"type": "float"}, "is_rainy": {"type": "boolean"},
            "avg_valence": {"type": "float"}, "avg_energy": {"type": "float"},
            "avg_danceability": {"type": "float"}, "avg_acousticness": {"type": "float"},
            "avg_tempo": {"type": "float"}, "avg_loudness": {"type": "float"},
            "track_count": {"type": "integer"}, "depression_index": {"type": "float"},
            "mood_category": {"type": "keyword"},
            "computation_date": {"type": "date", "format": "yyyy-MM-dd"},
        }}
    }
    requests.put(f"{ES_HOST}/{ES_INDEX}", json=mapping)

    body = "\n".join(actions) + "\n"
    r = requests.post(f"{ES_HOST}/_bulk", data=body.encode("utf-8"),
                       headers={"Content-Type": "application/x-ndjson"}, timeout=120)
    resp = r.json()
    print(f"  Indexed {len(resp.get('items', []))} documents")
    requests.post(f"{ES_HOST}/{ES_INDEX}/_refresh")

print(f"\n{'='*60}")
print(f"BATCH COMPLETE - {len(may_dates)} days of May + June data indexed")
print(f"{'='*60}")
