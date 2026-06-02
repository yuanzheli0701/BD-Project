"""
Formatting Job - Weather (Pandas)
Reads raw JSON from data/raw/weather/<date>/ and writes normalized
Parquet to data/formatted/weather/<date>/.
"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from jobs.common import get_raw_path, get_formatted_path

def run(date_str=None):
    if date_str is None: date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    raw_dir = get_raw_path('weather', date_str)
    out_dir = get_formatted_path('weather', date_str)
    out_dir.mkdir(parents=True, exist_ok=True)
    jf = raw_dir / 'cities_weather.json'
    if not jf.exists():
        print(f'No weather data at {jf}')
        return
    print(f'Reading from: {jf}')
    with open(jf, encoding='utf-8') as f:
        data = json.load(f)
    rows = []
    for city in data:
        for day in city.get('forecast_daily', []):
            rows.append({
                'city': city['city'], 'country': city['country'],
                'region': city['region'], 'lat': city['lat'], 'lon': city['lon'],
                'weather_date': day['date'],
                'temp_avg': day['temp_avg'], 'temp_min': day['temp_min'],
                'temp_max': day['temp_max'], 'humidity_avg': day['humidity_avg'],
                'clouds_avg': day['clouds_avg'], 'wind_speed_avg': day['wind_speed_avg'],
                'total_rain_3h': day['total_rain_3h'], 'is_rainy': day['is_rainy'],
                'fetch_date': date_str,
            })
    if not rows:
        print('No data found!')
        return
    df = pd.DataFrame(rows)
    for c in ['weather_date','fetch_date']:
        df[c] = pd.to_datetime(df[c])
    out_file = out_dir / 'weather.parquet'
    df.to_parquet(out_file, index=False)
    print(f'Written {len(df)} records to: {out_file}')

if __name__ == '__main__':
    run()