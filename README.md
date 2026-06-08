# City Mood x Weather - Correlation Analysis

> 
> 
> Real-time music charts (Last.fm) x weather data (OpenWeatherMap)  City Depression Index  Kibana Dashboard

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/yuanzheli0701/BD-Project.git
cd BD-Project

# 2. Configure API keys
cp .env.example config/.env
# Edit config/.env with your keys:
#   LASTFM_API_KEY=xxx          (from https://www.last.fm/api)
#   OPENWEATHER_API_KEY=xxx     (from https://openweathermap.org/api)

# 3. Install
pip install -r requirements.txt

# 4. Start Elasticsearch + Kibana
docker-compose -f docker/docker-compose.yml up -d

# 5. Run pipeline
python run_pipeline.py              # Pandas version
python run_pipeline.py --spark     # Spark version (+1.5 bonus points)
python run_pipeline.py --s3        # With S3 distributed storage (+1 bonus)

# 6. Open Kibana
# http://localhost:5601
# Stack Management  Saved Objects  Import kibana/dashboard_export.ndjson
```

---

## Scoring Rubric Coverage

### Mandatory (Green Cells)

| Requirement | Points | Implementation | File |
|-------------|--------|---------------|------|
| Ingestion of 2+ data sources as files | 2 | Last.fm API + OpenWeatherMap API | `jobs/ingestion/ingest_lastfm.py`, `ingest_weather.py` |
| Transform to Parquet | 2 | Pandas + PySpark versions | `jobs/formatting/format_*.py` |
| Fields normalization (UTC dates) | 1 | ISO 8601 dates, Parquet schemas | `jobs/formatting/` |
| Join sources  value-added output | 2 | Join + City Depression Index (CDI) | `jobs/combination/combine_mood_weather.py` |
| Index to Elasticsearch | 2 | Bulk indexing with geo_point mapping | `jobs/indexing/index_to_es.py` |
| Kibana Dashboard | 2 | Map + Bar + Line + Metrics | `kibana/dashboard_export.ndjson` |
| Clean naming conventions | 1 | `data/<layer>/<source>/<date>/` | `data/` |
| Airflow DAG / run all at once | 1 | DAG + `run_pipeline.py` | `dags/`, `run_pipeline.py` |

### Bonus Points

| Bonus | Points | Implementation | File |
|-------|--------|---------------|------|
| Use Spark for transformations | 1.5 | PySpark formatting + combination | `jobs/*/*_spark.py` |
| Interesting/innovative result | 1.5-3 | CDI (self-invented metric) | `jobs/combination/` |
| S3 distributed file system | 1 | LocalStack + boto3 | `jobs/s3_storage.py` |
| Blog post | 1 | Medium-style article | `blog_post.md` |
| Video presentation | 0.5-1.5 | 10-min demo video | (separate file) |

---

## Architecture

```
     
  Last.fm API       OpenWeather      REST APIs
  Top Tracks           API       
     
                           
                           

            DATA LAKE                  
  raw/    formatted/    combined/   
  JSON     Parquet         Parquet    
         (Pandas/Spark)   (CDI calc)  

                   
                   

         Elasticsearch                
    (geo_point + full-text index)     

                   
                   

            KIBANA                    
   Map  Bars  Lines  Metrics       

```

### Data Lake Structure

```
data/
 raw/                        # Layer 0: Raw ingestion (JSON)
    lastfm/<YYYY-MM-DD>/    # Real top tracks per country
    weather/<YYYY-MM-DD>/   # Real weather per city
 formatted/                  # Layer 1: Normalized (Parquet)
    lastfm/<YYYY-MM-DD>/
    weather/<YYYY-MM-DD>/
 combined/                   # Layer 2: Joined + CDI (Parquet)
     <YYYY-MM-DD>/
```

---

## City Depression Index (CDI)

```
CDI = (1 - avg_valence) x (1 + rain_bonus + cloud_bonus + humidity_bonus)

rain_bonus     = 0.3 if rainy, else 0
cloud_bonus    = (clouds_avg / 100) x 0.2
humidity_bonus = (humidity_avg / 100) x 0.1
```

| CDI Range | Mood |
|-----------|------|
| < 0.3 | Happy & Sunny |
| 0.3-0.6 | Slightly Melancholic |
| 0.6-0.9 | Moderately Sad |
| 0.9-1.2 | Quite Depressed |
| > 1.2 | Deeply Depressed |

---

## Project Structure

```
 run_pipeline.py              # One-click full pipeline
 blog_post.md                 # Blog article
 dags/                        # Airflow DAG
 jobs/
    common.py                # Shared utils, city mapping
    s3_storage.py            # S3 distributed storage
    ingestion/
       ingest_lastfm.py     # Last.fm API integration
       ingest_weather.py    # OpenWeatherMap API
       generate_mock_data.py
    formatting/
       format_lastfm.py     # Pandas formatting
       format_lastfm_spark.py  # Spark formatting (+bonus)
       format_weather.py
       format_weather_spark.py
    combination/
       combine_mood_weather.py      # Pandas CDI calculation
       combine_mood_weather_spark.py # Spark CDI (+bonus)
    indexing/
        index_to_es.py       # Elasticsearch bulk index
 docker/
    docker-compose.yml       # ES + Kibana
 kibana/
    dashboard_export.ndjson  # Pre-built dashboard
 dashboard/                   # Standalone HTML dashboard (bonus)
 data/                        # Data Lake
```

---

## License

Educational project - Big Data course.
