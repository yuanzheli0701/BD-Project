import pandas as pd, json, requests, os, sys
from pathlib import Path
sys.path.insert(0, r"C:\Users\13968\Documents\New project")
from jobs.common import load_env, get_combined_path

load_env()
ES_HOST = os.environ.get("ES_HOST", "http://localhost:9200")
ES_INDEX = os.environ.get("ES_INDEX", "city_depression_index")

all_dates = ["2026-05-14","2026-05-15","2026-05-16","2026-05-17","2026-05-18","2026-05-19","2026-05-26"]
dfs = []
for d in all_dates:
    p = get_combined_path(d) / "combined.parquet"
    if p.exists():
        df = pd.read_parquet(p)
        dfs.append(df)
        print(f"{d}: {len(df)} records")

merged = pd.concat(dfs, ignore_index=True)
print(f"Total: {len(merged)} records")

for c in ["date", "computation_date"]:
    if c in merged.columns:
        merged[c] = pd.to_datetime(merged[c]).dt.strftime("%Y-%m-%d")

actions = []
for _, row in merged.iterrows():
    doc = row.dropna().to_dict()
    doc["location"] = {"lat": float(row["lat"]), "lon": float(row["lon"])}
    doc_id = f"{row['city']}_{row['date']}"
    actions.append(json.dumps({"index": {"_index": ES_INDEX, "_id": doc_id}}))
    actions.append(json.dumps(doc))

requests.delete(f"{ES_HOST}/{ES_INDEX}")
print("Deleted old index")

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
r = requests.put(f"{ES_HOST}/{ES_INDEX}", json=mapping)
print(f"Created index: {ES_INDEX} ({r.status_code})")

body = "\n".join(actions) + "\n"
r = requests.post(f"{ES_HOST}/_bulk", data=body.encode("utf-8"),
                   headers={"Content-Type": "application/x-ndjson"}, timeout=120)
resp = r.json()
items = resp.get("items", [])
if resp.get("errors"):
    errs = [i for i in items if "error" in i.get("index", {})]
    print(f"Indexed with {len(errs)} errors (out of {len(items)})")
    for e in errs[:2]:
        print(f"  Error: {e['index']['error']}")
else:
    print(f"Indexed {len(items)} documents successfully")

requests.post(f"{ES_HOST}/{ES_INDEX}/_refresh")
print("Done!")
