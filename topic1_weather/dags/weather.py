from datetime import datetime

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator


def _process_weather(data_interval_end, api_key, city_name):
    import requests

    # cities and their lat and lon for API requests
    cities = {
        'Lviv': {'lat': 49.841952, 'lon': 24.0315921},
        'Kyiv':  {'lat': 50.4500336, 'lon': 30.5241361},
        'Kharkiv': {'lat': 49.9923181, 'lon': 36.2310146},
        'Odesa': {'lat': 46.4843023, 'lon': 30.7322878},
        'Zhmerynka': {'lat': 49.0354593, 'lon': 28.1147317}
    }

    # Use context DAG to backfill data correctly
    dt_timestamp = int(data_interval_end.timestamp())

    # Use API version 3.0
    # This endpoint return data for any datetime until now
    base_url = "https://api.openweathermap.org/data/3.0/onecall/timemachine"
    params = {
        'lat': cities[city_name]['lat'],
        'lon': cities[city_name]['lon'],
        'exclude': 'minutely,hourly,daily',
        'units': 'metric',
        'dt': dt_timestamp,
        'appid': api_key
    }

    response = requests.get(base_url, params=params)

    response_dict = response.json()
    metrics = response_dict['data'][0]
    return city_name, dt_timestamp, metrics['temp'], metrics['humidity'], metrics['clouds'], metrics['wind_speed']


with DAG(
        dag_id='weather',
        schedule_interval="0 5 * * *",
        start_date=datetime(2023, 4, 1),
        catchup=True
) as dag:

    create_table = PostgresOperator(
        task_id='create_table',
        sql="""
        CREATE TABLE IF NOT EXISTS public.measures(
            city    text,
            datetime timestamp,
            temp decimal(10,4),
            humidity decimal(10,4),
            clouds decimal(10,4),
            wind_speed decimal(10,4)
        );""",
        postgres_conn_id='local_postgres'
    )

    # Get weather for list of cities
    for city in ('Lviv', 'Kyiv', 'Kharkiv', 'Odesa', 'Zhmerynka'):

        extract_data = PythonOperator(
            task_id=f"extract_data_{city}",
            python_callable=_process_weather,
            op_kwargs={"api_key": Variable.get("WEATHER_API"),
                       "city_name": city}
        )
        insert_data = PostgresOperator(
            task_id=f"insert_data_{city}",
            sql=f"""
            INSERT INTO measures (city, datetime, temp, humidity, clouds, wind_speed) VALUES
            ('{{{{ti.xcom_pull(task_ids='extract_data_{city}')[0]}}}}',
            to_timestamp({{{{ti.xcom_pull(task_ids='extract_data_{city}')[1]}}}}),
            {{{{ti.xcom_pull(task_ids='extract_data_{city}')[2]}}}},
            {{{{ti.xcom_pull(task_ids='extract_data_{city}')[3]}}}},
            {{{{ti.xcom_pull(task_ids='extract_data_{city}')[4]}}}},
            {{{{ti.xcom_pull(task_ids='extract_data_{city}')[5]}}}});""",
            postgres_conn_id='local_postgres'
        )

        create_table >> extract_data >> insert_data


