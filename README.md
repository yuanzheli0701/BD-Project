# 🌧️ City Mood × Weather Correlation Analysis

> **Do people actually listen to sadder music when it rains?**
>
> We pull Spotify''s daily Top 50 audio features and local weather data, then
> compute a **City Depression Index (CDI)** mapped across cities on Kibana.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      AIRFLOW DAG                             │
│              (city_mood_weather_pipeline)                     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐     ┌─────────────────┐                │
│  │ ingest_spotify  │     │ ingest_weather  │   ← REST APIs  │
│  │  (Spotify API)  │     │  (OpenWeather)  │                │
│  └───────┬─────────┘     └───────┬─────────┘                │
│          │                       │                           │
│          ▼                       ▼                           │
│  ┌─────────────────┐     ┌─────────────────┐                │
│  │ format_spotify  │     │ format_weather  │   ← Spark      │
│  │ JSON → Parquet  │     │ JSON → Parquet  │                │
│  └───────┬─────────┘     └───────┬─────────┘                │
│          │                       │                           │
│          └───────────┬───────────┘                           │
│                      ▼                                       │
│           ┌──────────────────┐                               │
│           │  combine_mood   │   ← Spark (join + CDI)        │
│           │ Join + CDI calc │                               │
│           └────────┬─────────┘                               │
│                    ▼                                         │
│           ┌──────────────────┐                               │
│           │   index_to_es   │   ← Elasticsearch             │
│           │ Parquet → ES    │                               │
│           └────────┬─────────┘                               │
│                    ▼                                         │
│           ┌──────────────────┐                               │
│           │     KIBANA       │   ← Dashboard                │
│           │  City Mood Map   │                               │
│           └──────────────────┘                               │
└──────────────────────────────────────────────────────────────┘
```

### Data Lake Structure

```
data/
├── raw/                      # Layer 0: Raw ingestion
│   ├── spotify/
│   │   └── <YYYY-MM-DD>/
│   │       ├── global.json   # Global Top 50
│   │       ├── fr.json       # France Top 50
│   │       ├── us.json       # US Top 50
│   │       └── ...
│   └── weather/
│       └── <YYYY-MM-DD>/
│           └── cities_weather.json
│
├── formatted/                # Layer 1: Cleaned + Normalized (Parquet)
│   ├── spotify/
│   │   └── <YYYY-MM-DD>/
│   └── weather/
│       └── <YYYY-MM-DD>/
│
└── combined/                 # Layer 2: Joined + Enriched (Parquet)
    └── <YYYY-MM-DD>/
```

---

## City Depression Index (CDI)

The CDI combines Spotify''s **valence** (musical positivity, 0 = sad, 1 = happy)
with weather conditions:

```
CDI = (1 - avg_valence) × (1 + rain_bonus + cloud_bonus + humidity_bonus)

  rain_bonus    = 0.3 if rainy, else 0
  cloud_bonus   = (clouds_avg / 100) × 0.2
  humidity_bonus = (humidity_avg / 100) × 0.1
```

| CDI Range | Mood Category        |
|-----------|----------------------|
| < 0.3     | Happy & Sunny        |
| 0.3–0.6   | Slightly Melancholic |
| 0.6–0.9   | Moderately Sad       |
| 0.9–1.2   | Quite Depressed      |
| > 1.2     | Deeply Depressed     |

---

## Tracked Cities

| City       | Country | Region |
|------------|---------|--------|
| Paris      | FR 🇫🇷   | fr     |
| London     | GB 🇬🇧   | gb     |
| New York   | US 🇺🇸   | us     |
| Tokyo      | JP 🇯🇵   | jp     |
| Berlin     | DE 🇩🇪   | de     |
| Sydney     | AU 🇦🇺   | au     |
| Mumbai     | IN 🇮🇳   | in     |
| São Paulo  | BR 🇧🇷   | br     |
| Moscow     | RU 🇷🇺   | ru     |
| Seoul      | KR 🇰🇷   | kr     |

---

## Prerequisites

- **Python 3.9+**
- **Apache Spark 3.4+** (with `pyspark`)
- **Docker** + Docker Compose (for Elasticsearch + Kibana)
- **Apache Airflow 2.7+** (optional; can run scripts manually)

### API Keys Required

1. **Spotify Web API** — [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
   - Create an app → get Client ID + Client Secret
2. **OpenWeatherMap API** — [openweathermap.org/api](https://openweathermap.org/api)
   - Free tier: 5-day/3-hour forecast API
   - Paid tier: One Call API 3.0 for historical data

---

## Quick Start

### 1. Clone and configure

```bash
cd "City Mood x Weather"
cp .env.example .env
# Edit .env — add your Spotify and OpenWeather API keys
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start Elasticsearch + Kibana

```bash
cd docker
docker-compose up -d

# Verify:
curl http://localhost:9200     # Elasticsearch
# Open http://localhost:5601   # Kibana
```

### 4. Run the pipeline

**Option A: Run each step manually**

```bash
# Step 1: Ingest data
python -m jobs.ingestion.ingest_spotify
python -m jobs.ingestion.ingest_weather

# Step 2: Format (raw → Parquet)
spark-submit jobs/formatting/format_spotify.py
spark-submit jobs/formatting/format_weather.py

# Step 3: Combine + compute CDI
spark-submit jobs/combination/combine_mood_weather.py

# Step 4: Index to Elasticsearch
spark-submit jobs/indexing/index_to_es.py
```

**Option B: Run via Airflow**

```bash
# Copy the DAG to your Airflow DAGs folder
cp dags/city_mood_weather_dag.py $AIRFLOW_HOME/dags/

# Set Airflow Variables for API keys:
airflow variables set SPOTIFY_CLIENT_ID "your_id"
airflow variables set SPOTIFY_CLIENT_SECRET "your_secret"
airflow variables set OPENWEATHER_API_KEY "your_key"

# Trigger the DAG
airflow dags trigger city_mood_weather_pipeline
```

### 5. View the Kibana Dashboard

1. Open **http://localhost:5601**
2. Go to **Stack Management → Index Patterns** → create pattern `city_depression_index`
3. Go to **Analytics → Dashboard** → create a new dashboard
4. Add visualizations:
   - **Maps**: Geo-point of cities colored by `depression_index`
   - **Bar chart**: CDI by city
   - **Line chart**: CDI over time (if running daily)
   - **Metric**: Highest/Lowest CDI city today
   - **Data table**: Full city × date records

---

## Scoring Rubric Coverage

| Requirement                          | Points | Implementation                          |
|--------------------------------------|--------|-----------------------------------------|
| Ingestion of N data sources as files | 2      | Spotify + Weather → raw JSON            |
| Fields normalization (UTC, etc.)     | 1      | Dates in ISO 8601 UTC, Parquet schema   |
| Transform → Parquet (Spark)          | 2      | `format_spotify.py` + `format_weather.py`|
| Join sources → value-added output    | 2      | `combine_mood_weather.py` + CDI formula |
| Index to Elasticsearch               | 2      | `index_to_es.py` with geo_point mapping |
| Kibana Dashboard                     | 2      | Maps, charts, metrics on CDI data       |
| Clean naming conventions             | 1      | `data/<layer>/<source>/<date>/` pattern |
| **Total (base)**                     | **12** |                                         |

**Bonus opportunities:**
- Use DBT instead of Spark (+1.5)
- Machine learning for CDI (+1)
- Distributed FS / S3 (+1)
- Kafka realtime (+1)
- Airbyte ingestion (+1)
- Deploy to cloud (+1)
- Blog post (+1)

---

## Project Structure

```
City Mood x Weather/
├── .env.example                  # API key template
├── requirements.txt              # Python dependencies
├── README.md                     # This file
│
├── config/
│   └── .env                      # Your actual API keys (gitignored)
│
├── docker/
│   └── docker-compose.yml        # Elasticsearch + Kibana
│
├── dags/
│   └── city_mood_weather_dag.py  # Airflow DAG
│
├── jobs/
│   ├── __init__.py
│   ├── common.py                 # Shared utils, city config, env loader
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── ingest_spotify.py     # Spotify Top 50 + audio features
│   │   └── ingest_weather.py     # OpenWeatherMap API
│   ├── formatting/
│   │   ├── __init__.py
│   │   ├── format_spotify.py     # Raw JSON → Parquet (Spark)
│   │   └── format_weather.py     # Raw JSON → Parquet (Spark)
│   ├── combination/
│   │   ├── __init__.py
│   │   └── combine_mood_weather.py  # Join + CDI (Spark)
│   └── indexing/
│       ├── __init__.py
│       └── index_to_es.py        # Parquet → Elasticsearch
│
└── data/                         # Data Lake (gitignored)
    ├── raw/
    ├── formatted/
    └── combined/
```

---

## License

Educational project — Big Data course.
