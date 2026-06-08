
import os
from datetime import datetime, timezone
from pathlib import Path


def load_env():
    """Load environment variables from .env file."""
    env_path = Path(__file__).resolve().parent.parent / "config" / ".env"
    if not env_path.exists():
        env_path = Path(__file__).resolve().parent.parent / ".env"

    if env_path.exists():
        with open(env_path, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    if key.strip() not in os.environ:
                        os.environ[key.strip()] = value.strip()


def get_data_lake_root():
    """Return the absolute path to the Data Lake root."""
    root = os.environ.get("DATA_LAKE_ROOT", "data")
    base = Path(__file__).resolve().parent.parent
    return base / root


def get_raw_path(source: str, date_str: str = None) -> Path:
    """data/raw/<source>/<YYYY-MM-DD>/"""
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return get_data_lake_root() / "raw" / source / date_str


def get_formatted_path(source: str, date_str: str = None) -> Path:
    """data/formatted/<source>/<YYYY-MM-DD>/"""
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return get_data_lake_root() / "formatted" / source / date_str


def get_combined_path(date_str: str = None) -> Path:
    """data/combined/<YYYY-MM-DD>/"""
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return get_data_lake_root() / "combined" / date_str


# -- City mapping --

CITY_MAP = {
    "Paris":    {"country": "FR", "region": "fr", "lat": 48.8566, "lon": 2.3522},
    "London":   {"country": "GB", "region": "gb", "lat": 51.5074, "lon": -0.1278},
    "New York": {"country": "US", "region": "us", "lat": 40.7128, "lon": -74.0060},
    "Tokyo":    {"country": "JP", "region": "jp", "lat": 35.6762, "lon": 139.6503},
    "Berlin":   {"country": "DE", "region": "de", "lat": 52.5200, "lon": 13.4050},
    "Sydney":   {"country": "AU", "region": "au", "lat": -33.8688, "lon": 151.2093},
    "Mumbai":   {"country": "IN", "region": "in", "lat": 19.0760, "lon": 72.8777},
    "Sao Paulo":{"country": "BR", "region": "br", "lat": -23.5505, "lon": -46.6333},
    "Moscow":   {"country": "RU", "region": "ru", "lat": 55.7558, "lon": 37.6173},
    "Seoul":    {"country": "KR", "region": "kr", "lat": 37.5665, "lon": 126.9780},
}


def get_cities():
    """Return list of city names to track."""
    return list(CITY_MAP.keys())


def get_city_info(city_name: str) -> dict:
    """Return lat/lon/country/region for a city."""
    return CITY_MAP.get(city_name, {})