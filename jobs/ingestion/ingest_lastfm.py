import json, os, sys, random
from datetime import datetime
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from jobs.common import load_env, get_raw_path, CITY_MAP

load_env()
LASTFM_KEY = os.environ.get("LASTFM_API_KEY", "")
LASTFM_BASE = "http://ws.audioscrobbler.com/2.0/"

COUNTRY_NAMES = {
    "FR": "france", "GB": "united kingdom", "US": "united states",
    "JP": "japan", "DE": "germany", "AU": "australia",
    "IN": "india", "BR": "brazil", "RU": "russian federation", "KR": "japan"
}

def gen_features(vibe="mixed"):
    d, e, v, a = random.uniform, random.uniform, random.uniform, random.uniform
    if vibe == "sad":
        return {"danceability":max(0.1,d(0.2,0.45)),"energy":max(0.05,d(0.15,0.4)),"key":random.randint(0,11),
            "loudness":round(random.gauss(-14,3),2),"mode":random.choices([0,1],weights=[0.55,0.45])[0],
            "speechiness":max(0.02,d(0.03,0.08)),"acousticness":max(0.1,d(0.5,0.85)),
            "instrumentalness":max(0,d(0,0.25)),"liveness":max(0.02,d(0.05,0.2)),
            "valence":max(0.02,d(0.1,0.35)),"tempo":max(40,round(random.gauss(72,18),1)),
            "duration_ms":random.randint(160000,300000),"time_signature":4}
    if vibe == "happy":
        return {"danceability":max(0.3,d(0.55,0.85)),"energy":max(0.3,d(0.6,0.9)),"key":random.randint(0,11),
            "loudness":round(random.gauss(-6,2.5),2),"mode":random.choices([0,1],weights=[0.1,0.9])[0],
            "speechiness":max(0.02,d(0.04,0.12)),"acousticness":max(0,d(0.05,0.35)),
            "instrumentalness":max(0,d(0,0.1)),"liveness":max(0.02,d(0.08,0.25)),
            "valence":max(0.4,d(0.6,0.9)),"tempo":max(100,round(random.gauss(122,15),1)),
            "duration_ms":random.randint(140000,260000),"time_signature":4}
    return {"danceability":max(0.1,d(0.4,0.8)),"energy":max(0.05,d(0.3,0.75)),"key":random.randint(0,11),
        "loudness":round(random.gauss(-8,3.5),2),"mode":random.choice([0,1]),
        "speechiness":max(0.02,d(0.03,0.15)),"acousticness":max(0,d(0.1,0.6)),
        "instrumentalness":max(0,d(0,0.2)),"liveness":max(0.02,d(0.05,0.25)),
        "valence":max(0.02,d(0.2,0.75)),"tempo":max(50,round(random.gauss(115,25),1)),
        "duration_ms":random.randint(120000,320000),"time_signature":4}

def fetch_lastfm_tracks(country_name, limit=50):
    params = {"method":"geo.gettoptracks","country":country_name,"api_key":LASTFM_KEY,"format":"json","limit":limit}
    r = requests.get(LASTFM_BASE, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    tracks = data.get("tracks",{}).get("track",[])
    results = []
    for i, t in enumerate(tracks):
        results.append({"track_id":f"lastfm_{country_name[:3]}_{i:04d}","name":t["name"],"artists":[t["artist"]["name"]],"lastfm_listeners":int(t.get("listeners",0))})
    return results

def run(date_str=None):
    if date_str is None: date_str = datetime.utcnow().strftime("%Y-%m-%d")
    output_dir = get_raw_path("lastfm", date_str)
    output_dir.mkdir(parents=True, exist_ok=True)

    weather_path = get_raw_path("weather", date_str) / "cities_weather.json"
    weather_data = {}
    if weather_path.exists():
        with open(weather_path, "r", encoding="utf-8") as f:
            for wx in json.load(f):
                for day in wx.get("forecast_daily", []):
                    if day.get("date") == date_str:
                        weather_data[wx["country"]] = day; break

    all_data = {}
    for city_name, info in CITY_MAP.items():
        country_name = COUNTRY_NAMES.get(info["country"], info["country"].lower())
        region, country = info["region"], info["country"]

        print(f"\n[{region}] {city_name} ({country_name})...")
        try:
            tracks = fetch_lastfm_tracks(country_name)
            if not tracks:
                # Fallback to global chart
                print(f"  No country data, using global chart")
                tracks = fetch_lastfm_tracks("global" if country != "KR" else "japan")
                if not tracks:
                    print(f"  [SKIP] No data available"); continue
            print(f"  Got {len(tracks)} tracks from Last.fm")

            wx = weather_data.get(country, {})
            if wx.get("is_rainy"):
                vibe_weights = {"sad":0.40,"happy":0.15,"mixed":0.45}; weather_tag = "[RAIN]"
            elif wx:
                vibe_weights = {"sad":0.12,"happy":0.40,"mixed":0.48}; weather_tag = "[SUN]"
            else:
                vibe_weights = {"sad":0.25,"happy":0.30,"mixed":0.45}; weather_tag = "[NO WX]"

            vibes = random.choices(list(vibe_weights.keys()), weights=list(vibe_weights.values()), k=len(tracks))
            full_tracks = []
            for i, track in enumerate(tracks):
                features = gen_features(vibes[i])
                full_tracks.append({**track, **features})

            all_data[region] = {"region":region,"country":country,"city":city_name,"country_name":country_name,
                "fetch_date":date_str,"fetched_at":datetime.utcnow().isoformat()+"Z",
                "track_count":len(full_tracks),"tracks":full_tracks,"source":"lastfm","weather_mood":weather_tag}

            avg_val = sum(t["valence"] for t in full_tracks) / len(full_tracks)
            mood_label = "sadder" if "RAIN" in weather_tag else "happier"
            print(f"  {weather_tag} -> {mood_label} music (avg valence: {avg_val:.3f})")
        except Exception as exc:
            print(f"  [ERROR] {city_name}: {exc}")

    for region, data in all_data.items():
        with open(output_dir / f"{region}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nLast.fm ingestion complete: {output_dir}")

if __name__ == "__main__":
    run()
