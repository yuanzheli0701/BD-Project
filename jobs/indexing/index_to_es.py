import os, json, sys
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from jobs.common import load_env, get_combined_path

load_env()
ES_HOST = os.environ.get("ES_HOST", "http://localhost:9200")
ES_INDEX = os.environ.get("ES_INDEX", "city_depression_index")

def run(date_str=None):
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    combined_path = get_combined_path(date_str) / "combined.parquet"
    if not combined_path.exists():
        print(f"File not found: {combined_path}")
        return
    print(f"Reading: {combined_path}")
    df = pd.read_parquet(combined_path)
    print(f"  {len(df)} records")

    for c in ["date", "computation_date"]:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c]).dt.strftime("%Y-%m-%d")

    actions = []
    for _, row in df.iterrows():
        doc = row.dropna().to_dict()
        doc["location"] = {"lat": float(row["lat"]), "lon": float(row["lon"])}
        doc_id = f"{row['city']}_{row['date']}"
        actions.append(json.dumps({"index": {"_index": ES_INDEX, "_id": doc_id}}))
        actions.append(json.dumps(doc))

    if not actions:
        print("No data to index.")
        return

    try:
        r = requests.get(ES_HOST, timeout=5)
        print(f"ES status: {r.status_code}")
    except Exception as e:
        print(f"Cannot connect to ES at {ES_HOST}: {e}")
        return

    if requests.head(f"{ES_HOST}/{ES_INDEX}").status_code == 200:
        requests.delete(f"{ES_HOST}/{ES_INDEX}")
        print(f"Deleted existing index: {ES_INDEX}")

    mapping = {
        "mappings": {
            "properties": {
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
            }
        }
    }
    requests.put(f"{ES_HOST}/{ES_INDEX}", json=mapping)
    print(f"Created index: {ES_INDEX}")

    body = "\n".join(actions) + "\n"
    r = requests.post(f"{ES_HOST}/_bulk", data=body.encode("utf-8"),
                       headers={"Content-Type": "application/x-ndjson"}, timeout=60)
    resp = r.json()
    items = resp.get("items", [])
    if resp.get("errors"):
        errs = [i for i in items if "error" in i.get("index", {})]
        print(f"Indexed with {len(errs)} errors (out of {len(items)})")
        for e in errs[:3]:
            print(f"  Error: {e['index']['error']}")
    else:
        print(f"Indexed {len(items)} documents successfully")

    requests.post(f"{ES_HOST}/{ES_INDEX}/_refresh")

if __name__ == "__main__":
    run()
