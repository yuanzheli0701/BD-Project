"""
Formatting Job - Spotify (Pandas)
Reads raw JSON from data/raw/spotify/<date>/ and writes normalized
Parquet to data/formatted/spotify/<date>/.
"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from jobs.common import get_raw_path, get_formatted_path

def run(date_str=None):
    if date_str is None: date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    raw_dir = get_raw_path('spotify', date_str)
    out_dir = get_formatted_path('spotify', date_str)
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f'Reading from: {raw_dir}')
    rows = []
    for jf in sorted(raw_dir.glob('*.json')):
        region = jf.stem
        with open(jf, encoding='utf-8') as f:
            data = json.load(f)
        for t in data.get('tracks', []):
            rows.append({
                'track_id': t['track_id'], 'name': t['name'],
                'artists': ','.join(t.get('artists', [])),
                'danceability': max(0, min(1, t.get('danceability') or 0)),
                'energy': max(0, min(1, t.get('energy') or 0)),
                'key': t.get('key'), 'loudness': t.get('loudness'),
                'mode': t.get('mode'),
                'speechiness': max(0, min(1, t.get('speechiness') or 0)),
                'acousticness': max(0, min(1, t.get('acousticness') or 0)),
                'instrumentalness': max(0, min(1, t.get('instrumentalness') or 0)),
                'liveness': max(0, min(1, t.get('liveness') or 0)),
                'valence': max(0, min(1, t.get('valence') or 0)),
                'tempo': t.get('tempo'), 'duration_ms': t.get('duration_ms'),
                'time_signature': t.get('time_signature'),
                'region': region, 'fetch_date': date_str,
            })
        print(f'  {region}: {len(data.get("tracks",[]))} tracks')
    if not rows:
        print('No data found!')
        return
    df = pd.DataFrame(rows)
    df['fetch_date'] = pd.to_datetime(df['fetch_date'])
    out_file = out_dir / 'spotify.parquet'
    df.to_parquet(out_file, index=False)
    print(f'Written {len(df)} tracks to: {out_file}')

if __name__ == '__main__':
    run()