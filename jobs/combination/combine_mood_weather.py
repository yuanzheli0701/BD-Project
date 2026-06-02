"""
Combination Job - City Mood x Weather (Pandas)
Joins formatted Spotify + Weather data and computes the City Depression Index.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from jobs.common import get_formatted_path, get_combined_path

def run(date_str=None):
    if date_str is None: date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    spotify_path = get_formatted_path('spotify', date_str) / 'spotify.parquet'
    weather_path = get_formatted_path('weather', date_str) / 'weather.parquet'

    print(f'Reading Spotify: {spotify_path}')
    sp = pd.read_parquet(spotify_path)
    print(f'Reading Weather: {weather_path}')
    wx = pd.read_parquet(weather_path)

    print(f'  Spotify: {len(sp)} tracks, {sp["region"].nunique()} regions')
    print(f'  Weather: {len(wx)} records, {wx["city"].nunique()} cities')

    # Aggregate Spotify per region
    sp_agg = sp.groupby(['region','fetch_date']).agg(
        avg_valence=('valence','mean'),
        avg_energy=('energy','mean'),
        avg_danceability=('danceability','mean'),
        avg_acousticness=('acousticness','mean'),
        avg_tempo=('tempo','mean'),
        avg_loudness=('loudness','mean'),
        track_count=('track_id','count'),
    ).reset_index()
    sp_agg['fetch_date'] = pd.to_datetime(sp_agg['fetch_date'])

    # Join with weather
    combined = sp_agg.merge(
        wx, left_on=['region','fetch_date'], right_on=['region','weather_date'], how='inner'
    )

    # Compute City Depression Index
    rain_bonus = np.where(combined['is_rainy'], 0.3, 0.0)
    cloud_bonus = (combined['clouds_avg'] / 100.0) * 0.2
    humidity_bonus = (combined['humidity_avg'] / 100.0) * 0.1
    sadness = 1.0 - combined['avg_valence']
    weather_factor = 1.0 + rain_bonus + cloud_bonus + humidity_bonus
    combined['depression_index'] = sadness * weather_factor

    # Mood category
    bins = [-np.inf, 0.3, 0.6, 0.9, 1.2, np.inf]
    labels = ['Happy & Sunny','Slightly Melancholic','Moderately Sad','Quite Depressed','Deeply Depressed']
    combined['mood_category'] = pd.cut(combined['depression_index'], bins=bins, labels=labels)

    # Round
    for c in ['avg_valence','avg_energy','avg_danceability','avg_acousticness','avg_tempo','avg_loudness','depression_index']:
        combined[c] = combined[c].round(4)

    # Select output columns
    result = combined[[
        'city','country','region','weather_date','lat','lon',
        'temp_avg','temp_min','temp_max','humidity_avg','clouds_avg',
        'wind_speed_avg','total_rain_3h','is_rainy',
        'avg_valence','avg_energy','avg_danceability','avg_acousticness',
        'avg_tempo','avg_loudness','track_count',
        'depression_index','mood_category',
    ]].copy()
    result.rename(columns={'weather_date':'date'}, inplace=True)
    result['computation_date'] = date_str
    result['date'] = pd.to_datetime(result['date'])
    result['computation_date'] = pd.to_datetime(result['computation_date'])

    # Save
    out_dir = get_combined_path(date_str)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / 'combined.parquet'
    result.to_parquet(out_file, index=False)
    print(f'\nSaved {len(result)} records to: {out_file}')

    # Show results
    print(f'\n{"="*70}')
    print(f'City Depression Index Results - {date_str}')
    print(f'{"="*70}')
    print(f'{"City":<12} {"Valence":>8} {"Rainy":>6} {"Clouds":>7} {"CDI":>7}  Category')
    print(f'{"-"*60}')
    for _, r in result.iterrows():
        rain = 'Yes' if r['is_rainy'] else 'No'
        print(f'{r["city"]:<12} {r["avg_valence"]:>8.4f} {rain:>6} {r["clouds_avg"]:>6.0f}% {r["depression_index"]:>7.4f}  {r["mood_category"]}')

if __name__ == '__main__':
    run()