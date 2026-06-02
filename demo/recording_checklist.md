# Recording Checklist / 录制清单

## Before Recording / 录制前准备

1. Start Docker Desktop
2. Run in terminal: docker-compose -f docker/docker-compose.yml up -d
3. Wait for ES to be ready: curl http://localhost:9200
4. Wait for Kibana: open http://localhost:5601 (takes ~2 min first time)
5. Clean terminal: cls

## What to Record / 录制内容

Screen 1 - Terminal (2 min):
  cd "C:\Users\13968\Documents\New project"
  $env:PYTHONPATH="C:\Users\13968\Documents\New project"
  python run_pipeline.py
  → Show the CDI output table

Screen 2 - Kibana Dashboard (2 min):
  http://localhost:5601
  → Dashboard → City Mood Dashboard
  → Show Map, Bar, Line, Metrics
  → Switch dates to show 31 days of data

Screen 3 - Code Structure (2 min):
  VS Code → Open project folder
  → Show data/ folder hierarchy
  → Show jobs/ folder (ingestion, formatting, combination, indexing)
  → Show bonus: *_spark.py, s3_storage.py, Airflow DAG

Screen 4 - CDI Formula Explanation (1 min):
  → Show README.md CDI section
  → Explain the formula

## Software Needed / 需要的软件

- OBS Studio (free screen recorder) or Windows Game Bar (Win+G)
- VS Code
- Terminal (PowerShell)
- Browser (Kibana)

## After Recording / 录制后

1. Add subtitles: demo/subtitles.srt (import into video editor)
2. Trim to under 10 minutes
3. Export as MP4
