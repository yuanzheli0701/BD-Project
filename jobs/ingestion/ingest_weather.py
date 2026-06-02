"""
Weather Ingestion Job
Fetches current + historical weather data from OpenWeatherMap API.
Writes raw JSON to data/raw/weather/<YYYY-MM-DD>/

OpenWeatherMap API endpoints used:
  GET /data/3.0/onecall/timemachine  — Historical weather by lat/lon + timestamp
  (Free-tier fallback: /data/2.5/weather for current conditions)
"""
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from jobs.common import load_env, get_raw_path, CITY_MAP

load_env()

API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")


def fetch_weather_onecall(lat: float, lon: float, dt: int) -> dict:
    """
    Fetch historical weather using OpenWeatherMap One Call API 3.0
    (requires paid subscription). Falls back gracefully.
    """
    url = "https://api.openweathermap.org/data/3.0/onecall/timemachine"
    params = {
        "lat": lat,
        "lon": lon,
        "dt": dt,
        "appid": API_KEY,
        "units": "metric",
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_weather_current(lat: float, lon: float) -> dict:
    """
    Fetch current weather (free tier fallback).
    """
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,
        "units": "metric",
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    # Normalize to a consistent format
    return {
        "lat": lat,
        "lon": lon,
        "timezone": data.get("timezone", 0),
        "data": [{
            "dt": data["dt"],
            "temp": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "pressure": data["main"]["pressure"],
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"],
            "wind_deg": data["wind"].get("deg", 0),
            "clouds": data["clouds"]["all"],
            "weather": data["weather"],
            "rain": data.get("rain", {}).get("1h", 0),
        }],
    }


def fetch_historical_5day(lat: float, lon: float) -> dict:
    """
    Fetch 5-day/3-hour forecast as approximate daily data (free tier).
    We aggregate min/max/avg and rainfall from the 8 data points per day.
    """
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,
        "units": "metric",
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    # Group by day
    daily = {}
    for entry in data.get("list", []):
        day = datetime.utcfromtimestamp(entry["dt"]).strftime("%Y-%m-%d")
        if day not in daily:
            daily[day] = {
                "temps": [],
                "humidities": [],
                "clouds": [],
                "wind_speeds": [],
                "rain_3h": [],
                "weather_codes": [],
            }
        d = daily[day]
        d["temps"].append(entry["main"]["temp"])
        d["humidities"].append(entry["main"]["humidity"])
        d["clouds"].append(entry["clouds"]["all"])
        d["wind_speeds"].append(entry["wind"]["speed"])
        d["rain_3h"].append(entry.get("rain", {}).get("3h", 0))
        d["weather_codes"].append(entry["weather"][0]["id"])

    records = []
    for day, vals in sorted(daily.items()):
        records.append({
            "date": day,
            "temp_avg": round(sum(vals["temps"]) / len(vals["temps"]), 1),
            "temp_min": round(min(vals["temps"]), 1),
            "temp_max": round(max(vals["temps"]), 1),
            "humidity_avg": round(sum(vals["humidities"]) / len(vals["humidities"]), 1),
            "clouds_avg": round(sum(vals["clouds"]) / len(vals["clouds"]), 1),
            "wind_speed_avg": round(sum(vals["wind_speeds"]) / len(vals["wind_speeds"]), 1),
            "total_rain_3h": round(sum(vals["rain_3h"]), 1),
            "is_rainy": any(w < 800 for w in vals["weather_codes"]),
        })

    return records


def run(date_str: str = None):
    """Main entry point - fetches weather for all configured cities."""
    if date_str is None:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")

    output_dir = get_raw_path("weather", date_str)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_data = []

    for city_name, info in CITY_MAP.items():
        print(f"\nFetching weather for {city_name} ({info['lat']}, {info['lon']})...")

        try:
            # Try the free 5-day forecast approach
            daily_records = fetch_historical_5day(info["lat"], info["lon"])

            # Also get current conditions as fallback
            try:
                current = fetch_weather_current(info["lat"], info["lon"])
            except Exception:
                current = None

            city_record = {
                "city": city_name,
                "country": info["country"],
                "region": info["region"],
                "lat": info["lat"],
                "lon": info["lon"],
                "fetch_date": date_str,
                "fetched_at": datetime.utcnow().isoformat() + "Z",
                "current": current,
                "forecast_daily": daily_records,
            }
            all_data.append(city_record)
            print(f"  -> Got {len(daily_records)} forecast days for {city_name}")

        except Exception as exc:
            print(f"  [ERROR] {city_name}: {exc}")

    # Save all cities in one file per day
    output_file = output_dir / "cities_weather.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"\nWeather ingestion complete. Saved to: {output_file}")


if __name__ == "__main__":
    run()
