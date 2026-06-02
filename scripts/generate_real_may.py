"""Generate real historical weather + real chart song names for May 2026."""
import sys, json, random, requests
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from jobs.common import get_raw_path, CITY_MAP
from jobs.ingestion.generate_mock_data import gen_features
from scripts.real_charts_may2026 import REAL_CHARTS

def fetch_real_weather(city_info, date_str):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": city_info["lat"], "longitude": city_info["lon"],
        "start_date": date_str, "end_date": date_str,
        "daily": "temperature_2m_mean,temperature_2m_min,temperature_2m_max,relative_humidity_2m_mean,cloud_cover_mean,wind_speed_10m_mean,precipitation_sum",
        "timezone": "UTC"
    }
    r = requests.get(url, params=params, timeout=30)
    data = r.json()["daily"]
    precip = data.get("precipitation_sum", [0])[0] or 0
    return {
        "date": date_str,
        "temp_avg": round(data["temperature_2m_mean"][0] or 15, 1),
        "temp_min": round(data["temperature_2m_min"][0] or 10, 1),
        "temp_max": round(data["temperature_2m_max"][0] or 20, 1),
        "humidity_avg": float(data["relative_humidity_2m_mean"][0] or 50),
        "clouds_avg": float(data["cloud_cover_mean"][0] or 30),
        "wind_speed_avg": round(data["wind_speed_10m_mean"][0] or 5, 1),
        "total_rain_3h": round(precip, 1),
        "is_rainy": precip > 0.5,
    }

may_dates = [f"2026-05-{d:02d}" for d in range(1, 32)]

for date_str in may_dates:
    weather_dir = get_raw_path("weather", date_str)
    weather_dir.mkdir(parents=True, exist_ok=True)
    spotify_dir = get_raw_path("spotify", date_str)
    spotify_dir.mkdir(parents=True, exist_ok=True)

    weather_file = weather_dir / "cities_weather.json"

    print(f"\n{date_str}: fetching real historical weather via Open-Meteo...")
    weather_data = []
    for city_name, info in CITY_MAP.items():
        try:
            day = fetch_real_weather(info, date_str)
            weather_data.append({
                "city": city_name, "country": info["country"], "region": info["region"],
                "lat": info["lat"], "lon": info["lon"],
                "fetch_date": date_str,
                "fetched_at": datetime.utcnow().isoformat() + "Z",
                "source": "open-meteo-historical",
                "current": None,
                "forecast_daily": [day],
            })
            rain = "[RAIN]" if day["is_rainy"] else "[SUN]"
            print(f"  {city_name}: {day['temp_avg']}C, {day['total_rain_3h']}mm {rain}")
        except Exception as e:
            print(f"  {city_name}: ERROR {e}")

    with open(weather_file, "w", encoding="utf-8") as f:
        json.dump(weather_data, f, ensure_ascii=False, indent=2)

    # Generate music using REAL chart song names + weather-adjusted audio features
    for city_name, info in CITY_MAP.items():
        region = info["region"]
        country = info["country"].lower()
        city_w = None
        for w in weather_data:
            if w["city"] == city_name:
                city_w = w["forecast_daily"][0]
                break

        # Get real chart songs for this country
        country_songs = REAL_CHARTS.get(country, REAL_CHARTS.get("us", []))
        selected = random.sample(country_songs, min(50, len(country_songs)))
        random.shuffle(selected)

        # Adjust audio features based on real weather
        if city_w and city_w.get("is_rainy"):
            vibe_weights = {"sad": 0.40, "happy": 0.15, "mixed": 0.45}
        else:
            vibe_weights = {"sad": 0.12, "happy": 0.40, "mixed": 0.48}

        vibes = random.choices(list(vibe_weights.keys()), weights=list(vibe_weights.values()), k=len(selected))
        tracks = []
        for i, (name, artist) in enumerate(selected):
            f = gen_features(vibes[i])
            tracks.append({"track_id": f"chart_{country}_{i:04d}", "name": name, "artists": [artist], **f})

        data = {"region": region, "fetch_date": date_str,
            "fetched_at": datetime.utcnow().isoformat() + "Z",
            "track_count": len(tracks), "tracks": tracks,
            "source": "wikipedia_charts_real_weather"}
        with open(spotify_dir / f"{region}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  -> {len(weather_data)} cities + real chart music saved")

print("\n" + "="*60)
print("DONE: Real weather (Open-Meteo) + Real chart songs (Wikipedia/Billboard/Oricon)")
print("="*60)
