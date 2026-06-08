
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.models import Variable
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

default_args = {
    'owner':'data-team','depends_on_past':False,
    'retries':2,'retry_delay':timedelta(minutes=5),
    'start_date':datetime(2024,1,1),
}

with DAG(
    dag_id='city_mood_weather_pipeline',
    default_args=default_args,
    description='Spotify Top 50 x Weather -> City Depression Index -> Kibana',
    schedule_interval='0 2 * * *',
    catchup=False, max_active_runs=1,
    tags=['spotify','weather','big-data'],
) as dag:

    ingest_spotify = BashOperator(
        task_id='ingest_spotify',
        bash_command=f'cd {PROJECT_ROOT} && python -m jobs.ingestion.ingest_spotify',
        env={
            'SPOTIFY_CLIENT_ID': Variable.get('SPOTIFY_CLIENT_ID',''),
            'SPOTIFY_CLIENT_SECRET': Variable.get('SPOTIFY_CLIENT_SECRET',''),
            'PYTHONPATH': PROJECT_ROOT,
        },
    )

    ingest_weather = BashOperator(
        task_id='ingest_weather',
        bash_command=f'cd {PROJECT_ROOT} && python -m jobs.ingestion.ingest_weather',
        env={
            'OPENWEATHER_API_KEY': Variable.get('OPENWEATHER_API_KEY',''),
            'PYTHONPATH': PROJECT_ROOT,
        },
    )

    format_spotify = BashOperator(
        task_id='format_spotify',
        bash_command=f'cd {PROJECT_ROOT} && python jobs/formatting/format_spotify.py',
        env={'PYTHONPATH': PROJECT_ROOT},
    )

    format_weather = BashOperator(
        task_id='format_weather',
        bash_command=f'cd {PROJECT_ROOT} && python jobs/formatting/format_weather.py',
        env={'PYTHONPATH': PROJECT_ROOT},
    )

    combine_mood = BashOperator(
        task_id='combine_mood',
        bash_command=f'cd {PROJECT_ROOT} && python jobs/combination/combine_mood_weather.py',
        env={'PYTHONPATH': PROJECT_ROOT},
    )

    index_to_es = BashOperator(
        task_id='index_to_es',
        bash_command=f'cd {PROJECT_ROOT} && python jobs/indexing/index_to_es.py',
        env={'PYTHONPATH': PROJECT_ROOT},
    )

    ingest_spotify >> format_spotify
    ingest_weather >> format_weather
    [format_spotify, format_weather] >> combine_mood >> index_to_es