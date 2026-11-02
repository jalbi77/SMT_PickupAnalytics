"""Ausschliesslich lesende Abfragen auf profiler; keine Archivdaten."""
import json
import os
from pathlib import Path
import tomllib
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

ROOT = Path(__file__).resolve().parent


def load_data():
    settings_path = Path(os.environ.get('SMT_PICKUP_SETTINGS', ROOT / '.streamlit/settings.toml')).resolve()
    with settings_path.open('rb') as stream:
        settings = tomllib.load(stream)
    credentials = Path(settings['credentials_file'])
    if not credentials.is_absolute():
        credentials = settings_path.parent / credentials
    with credentials.open(encoding='utf-8-sig') as stream:
        creds = json.load(stream)['nexim_database']
    url = URL.create('mssql+pyodbc', username=creds['user'], password=creds['password'],
                     host=creds['server'], database='profiler', query={
                         'driver': 'ODBC Driver 18 for SQL Server',
                         'Encrypt': 'yes', 'TrustServerCertificate': 'yes'})
    engine = create_engine(url, connect_args={'timeout': 15})
    try:
        with engine.connect() as conn:
            conn.connection.driver_connection.timeout = 120
            device = pd.read_sql(text((ROOT / 'device.sql').read_text(encoding='utf-8')), conn)
            nozzle = pd.read_sql(text((ROOT / 'nozzle.sql').read_text(encoding='utf-8')), conn)
        return device, nozzle
    finally:
        engine.dispose()
