# City Mood x Weather: When Rain Makes Your Playlist Sad

*A Big Data project correlating Spotify charts with weather to compute a City Depression Index*

---

## The Question

Do people really listen to sadder music when it rains? We set out to answer this with data.

## The Architecture

We built an end-to-end Data Lake pipeline:

```
Last.fm API                      Elasticsearch  Kibana
               Spark/Parquet 
OpenWeather                      S3 Data Lake
```

**4 layers:**
- **Raw**  JSON from REST APIs
- **Formatted**  Normalized Parquet (Spark)
- **Combined**  Joined + CDI calculation
- **Exposition**  Kibana Dashboard

## The Formula: City Depression Index

```
CDI = (1 - avg_valence) x (1 + rain_bonus + cloud_bonus + humidity_bonus)
```

- **valence**: Spotify audio feature (0 = sad, 1 = happy)
- **rain**: +0.3 multiplier when raining
- **clouds**: up to +0.2 for overcast skies
- **humidity**: up to +0.1 for high humidity

## Key Findings (June 2026)

| City | Valence | Weather | CDI | Mood |
|------|---------|---------|-----|------|
| Tokyo | 0.433 | Rain 95% clouds | 0.8909 | Moderately Sad |
| London | 0.416 | Rain 57% clouds | 0.8701 | Moderately Sad |
| Paris | 0.426 | Rain 63% clouds | 0.8616 | Moderately Sad |
| New York | 0.583 | Sunny 13% clouds | 0.4475 | Slightly Melancholic |

**Rainy cities consistently show 2x higher depression index than sunny ones.**

## Tech Stack

- **Ingestion**: Last.fm API (real top tracks) + OpenWeatherMap API
- **Transformation**: Apache Spark + Parquet
- **Storage**: S3-compatible Data Lake (LocalStack/local)
- **Orchestration**: Apache Airflow DAG
- **Indexing**: Elasticsearch 8.11
- **Visualization**: Kibana (Map, Bar, Line, Metrics)

## Try It Yourself

```bash
git clone https://github.com/yuanzheli0701/BD-Project.git
pip install -r requirements.txt
docker-compose -f docker/docker-compose.yml up -d
python run_pipeline.py --s3
```

Open http://localhost:5601 and import `kibana/dashboard_export.ndjson`

---

*Built as part of the Big Data course at [University]. 2026.*
