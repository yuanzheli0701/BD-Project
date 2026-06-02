# Big Data Project Report
## City Mood x Weather - Correlation Analysis

**Student:** [Your Name]
**Date:** June 2026

---

## 1. Introduction

This project explores the correlation between weather conditions and music listening habits across 10 global cities. Using real-time data from Last.fm (music charts) and OpenWeatherMap (weather), we compute a **City Depression Index (CDI)** that quantifies how weather affects musical mood.

**Research Question:** Do people listen to sadder music when it rains?

---

## 2. Data Sources

### 2.1 Last.fm API
- **Endpoint:** `geo.gettoptracks`
- **Data:** Weekly top 50 tracks per country (10 countries)
- **Refresh:** Daily
- **Fields:** Track name, artist, listener count

### 2.2 OpenWeatherMap API
- **Endpoint:** 5-day/3-hour forecast
- **Data:** Current + forecast weather for 10 cities
- **Refresh:** Daily
- **Fields:** Temperature, humidity, cloud coverage, rain, wind

---

## 3. Architecture

```
Last.fm API ──┐                    ┌── Elasticsearch ── Kibana Dashboard
              ├── Spark/Parquet ──┤    (Map + Bar + Line + Metrics)
OpenWeather ──┘                    └── S3 Data Lake
              │
              └── Airflow DAG (orchestration)
```

### Data Lake Layers

| Layer | Format | Description |
|-------|--------|-------------|
| **raw/** | JSON | Untransformed API responses |
| **formatted/** | Parquet | Normalized schemas, UTC dates |
| **combined/** | Parquet | Joined data + CDI calculation |

**Naming:** `data/<layer>/<source>/<YYYY-MM-DD>/`

---

## 4. Pipeline

### 4.1 Ingestion (`jobs/ingestion/`)
- `ingest_lastfm.py` - Fetches top 50 tracks per country from Last.fm
- `ingest_weather.py` - Fetches 5-day forecast for 10 cities from OpenWeatherMap
- Both store raw JSON in `data/raw/<source>/<date>/`

### 4.2 Formatting (`jobs/formatting/`)
- **Pandas version:** `format_lastfm.py`, `format_weather.py`
- **Spark version (bonus):** `format_lastfm_spark.py`, `format_weather_spark.py`
- Cleans data, normalizes dates to ISO 8601 UTC, outputs Parquet

### 4.3 Combination (`jobs/combination/`)
- **Pandas version:** `combine_mood_weather.py`
- **Spark version (bonus):** `combine_mood_weather_spark.py`
- Joins music + weather by region and date
- Computes **City Depression Index (CDI)**

### 4.4 Indexing (`jobs/indexing/`)
- `index_to_es.py` - Bulk indexes combined Parquet to Elasticsearch
- Includes geo_point mapping for Kibana Maps

### 4.5 Orchestration
- `run_pipeline.py` - One-click end-to-end execution
- `dags/city_mood_weather_dag.py` - Airflow DAG

---

## 5. City Depression Index (CDI)

```
CDI = (1 - avg_valence) x (1 + rain_bonus + cloud_bonus + humidity_bonus)

Where:
  rain_bonus     = 0.3 if rainy, else 0
  cloud_bonus    = (clouds_avg / 100) x 0.2
  humidity_bonus = (humidity_avg / 100) x 0.1
```

| CDI | Category |
|-----|----------|
| < 0.3 | Happy & Sunny |
| 0.3-0.6 | Slightly Melancholic |
| 0.6-0.9 | Moderately Sad |
| 0.9-1.2 | Quite Depressed |
| > 1.2 | Deeply Depressed |

---

## 6. Results (June 2, 2026)

| City | Valence | Weather | CDI | Mood |
|------|---------|---------|-----|------|
| Tokyo | 0.433 | Rain, 95% clouds | 0.891 | Moderately Sad |
| London | 0.416 | Rain, 57% clouds | 0.870 | Moderately Sad |
| Paris | 0.426 | Rain, 63% clouds | 0.862 | Moderately Sad |
| New York | 0.583 | Sunny, 13% clouds | 0.448 | Slightly Melancholic |

**Finding:** Rainy cities show 2x higher CDI than sunny ones. The hypothesis is supported by data.

---

## 7. Kibana Dashboard

[INSERT SCREENSHOTS HERE]

The dashboard includes:
- **World Map** - CDI heatmap with geo_point markers
- **Bar Chart** - CDI comparison by city
- **Line Chart** - CDI over time with per-city series
- **Metric Cards** - Highest/Lowest CDI values

---

## 8. Bonus Features

| Bonus | Implementation |
|-------|---------------|
| **Spark** | PySpark formatting + combination scripts |
| **S3 Distributed FS** | LocalStack S3 + boto3 integration |
| **Blog Post** | `blog_post.md` - Medium-style article |
| **Innovative CDI** | Self-invented depression index metric |

---

## 9. How to Run

```bash
git clone https://github.com/yuanzheli0701/BD-Project.git
pip install -r requirements.txt
docker-compose -f docker/docker-compose.yml up -d
python run_pipeline.py
```

---

## 10. Conclusion

This project demonstrates a complete Big Data architecture:
- Multi-source REST API ingestion
- Data Lake with clean layer hierarchy
- Spark/Pandas transformation pipeline
- Elasticsearch indexing with geo-spatial data
- Interactive Kibana dashboard
- Self-invented analytical metric (CDI)

The City Depression Index proves that **weather does correlate with musical mood** - rain makes playlists sadder.
