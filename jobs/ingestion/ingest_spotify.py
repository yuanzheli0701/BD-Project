"""
Spotify Ingestion Job
Fetches daily Top 50 tracks and their audio features per region.
Writes raw JSON to data/raw/spotify/<YYYY-MM-DD>/

Spotify API endpoints used:
  GET /v1/playlists/{playlist_id}/tracks   — Top 50 chart per region
  GET /v1/audio-features?ids=...           — Audio features (valence, energy, etc.)
"""
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

# Allow running as script or Airflow task
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from jobs.common import load_env, get_raw_path, CITY_MAP

load_env()


# Spotify regional Top 50 playlist IDs
# These are Spotify-curated "Top 50" playlists. IDs may change;
# verify at https://open.spotify.com/genre/top-lists
SPOTIFY_PLAYLISTS = {
    "global": "37i9dQZEVXbMDoHDwVN2tF",
    "fr":     "37i9dQZEVXbIPWwFssbupI",
    "gb":     "37i9dQZEVXbLnolsZ8PSNw",
    "us":     "37i9dQZEVXbLRQDuF5jeBp",
    "jp":     "37i9dQZEVXbKXQ4mDTEBXq",
    "de":     "37i9dQZEVXbJiZcmkrIHGU",
    "au":     "37i9dQZEVXbJPcfkRz0wJ0",
    "in":     "37i9dQZEVXbLZ52Xm3S8gG",
    "br":     "37i9dQZEVXbMXbN3EUU8Oc",
    "ru":     "37i9dQZEVXbL8l7ra6Uvrx",
    "kr":     "37i9dQZEVXbNxNM4DBI6LH",
}


class SpotifyClient:
    """Simple Spotify Web API client with client-credentials auth."""

    BASE = "https://api.spotify.com/v1"

    def __init__(self):
        self._token = None
        self._token_expires = 0

    def _get_token(self):
        if self._token and time.time() < self._token_expires:
            return self._token

        resp = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(os.environ["SPOTIFY_CLIENT_ID"], os.environ["SPOTIFY_CLIENT_SECRET"]),
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._token_expires = time.time() + data["expires_in"] - 60
        return self._token

    def _headers(self):
        return {"Authorization": f"Bearer {self._get_token()}"}

    def get_playlist_tracks(self, playlist_id: str) -> list:
        """Fetch all tracks from a playlist (handles pagination)."""
        tracks = []
        url = f"{self.BASE}/playlists/{playlist_id}/tracks"
        params = {"limit": 50, "fields": "items(track(id,name,artists(name))),next"}

        while url:
            resp = requests.get(url, headers=self._headers(), params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("items", []):
                t = item.get("track")
                if t and t.get("id"):
                    tracks.append({
                        "track_id": t["id"],
                        "name": t["name"],
                        "artists": [a["name"] for a in t.get("artists", [])],
                    })
            url = data.get("next")
            params = {}  # next URL already includes params

        return tracks

    def get_audio_features(self, track_ids: list) -> list:
        """Fetch audio features for up to 100 track IDs per call."""
        features = []
        for i in range(0, len(track_ids), 100):
            batch = track_ids[i:i + 100]
            resp = requests.get(
                f"{self.BASE}/audio-features",
                headers=self._headers(),
                params={"ids": ",".join(batch)},
                timeout=30,
            )
            resp.raise_for_status()
            batch_features = resp.json().get("audio_features", [])
            features.extend([f for f in batch_features if f is not None])
        return features


def fetch_spotify_data(region: str, playlist_id: str, date_str: str) -> dict:
    """Fetch Top 50 + audio features for one region."""
    client = SpotifyClient()

    print(f"  [{region}] Fetching playlist tracks...")
    tracks = client.get_playlist_tracks(playlist_id)
    print(f"  [{region}] Got {len(tracks)} tracks")

    track_ids = [t["track_id"] for t in tracks]

    print(f"  [{region}] Fetching audio features...")
    features = client.get_audio_features(track_ids)
    print(f"  [{region}] Got {len(features)} audio features")

    # Merge track info with audio features
    track_dict = {t["track_id"]: t for t in tracks}
    merged = []
    for feat in features:
        tid = feat["id"]
        merged.append({
            "track_id": tid,
            "name": track_dict[tid]["name"],
            "artists": track_dict[tid]["artists"],
            "danceability": feat.get("danceability"),
            "energy": feat.get("energy"),
            "key": feat.get("key"),
            "loudness": feat.get("loudness"),
            "mode": feat.get("mode"),
            "speechiness": feat.get("speechiness"),
            "acousticness": feat.get("acousticness"),
            "instrumentalness": feat.get("instrumentalness"),
            "liveness": feat.get("liveness"),
            "valence": feat.get("valence"),
            "tempo": feat.get("tempo"),
            "duration_ms": feat.get("duration_ms"),
            "time_signature": feat.get("time_signature"),
        })

    return {
        "region": region,
        "fetch_date": date_str,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "track_count": len(merged),
        "tracks": merged,
    }


def run(date_str: str = None):
    """Main entry point - fetches Spotify data for all regions."""
    if date_str is None:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")

    output_dir = get_raw_path("spotify", date_str)
    output_dir.mkdir(parents=True, exist_ok=True)

    for region, playlist_id in SPOTIFY_PLAYLISTS.items():
        print(f"\n{'='*60}")
        print(f"Processing region: {region}")
        print(f"{'='*60}")

        try:
            data = fetch_spotify_data(region, playlist_id, date_str)
            output_file = output_dir / f"{region}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"  -> Saved: {output_file}")
        except Exception as exc:
            print(f"  [ERROR] {region}: {exc}")

    print(f"\nSpotify ingestion complete. Data saved to: {output_dir}")


if __name__ == "__main__":
    run()
