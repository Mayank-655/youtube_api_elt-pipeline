import os
import sys
from pathlib import Path
from unittest import mock

# Allow `from datawarehouse...` / `from api...` when pytest runs from repo root or /opt/airflow/tests.
_dags_dir = Path(__file__).resolve().parent.parent / "dags"
if _dags_dir.is_dir():
    sys.path.insert(0, str(_dags_dir))

import psycopg2
import pytest
from airflow.models import Connection, DagBag, Variable


@pytest.fixture
def api_key():
    with mock.patch.dict("os.environ", AIRFLOW_VAR_API_KEY="MOCK_KEY1234"):
        yield Variable.get("API_KEY")


@pytest.fixture
def channel_handle():
    with mock.patch.dict("os.environ", AIRFLOW_VAR_CHANNEL_HANDLE="MRCHEESE"):
        yield Variable.get("CHANNEL_HANDLE")


@pytest.fixture
def mock_postgres_conn_vars():
    conn = Connection(
        conn_type="postgres",
        login="mock_username",
        password="mock_password",
        host="mock_host",
        port=1234,
        schema="mock_db_name",
    )
    conn_uri = conn.get_uri()
    with mock.patch.dict("os.environ", AIRFLOW_CONN_POSTGRES_DB_YT_ELT=conn_uri):
        yield Connection.get_connection_from_secrets(conn_id="postgres_db_yt_elt")


@pytest.fixture()
def dagbag():
    dag_folder = Path(__file__).resolve().parent.parent / "dags"
    yield DagBag(dag_folder=str(dag_folder), include_examples=False)


@pytest.fixture()
def airflow_variable():
    def get_airflow_variable(variable_name: str):
        env_var = f"AIRFLOW_VAR_{variable_name.upper()}"
        return os.getenv(env_var)

    return get_airflow_variable


@pytest.fixture
def real_postgres_connection():
    dbname = os.getenv("ELT_DATABASE_NAME")
    user = os.getenv("ELT_DATABASE_USERNAME")
    password = os.getenv("ELT_DATABASE_PASSWORD")
    host = os.getenv("POSTGRES_CONN_HOST")
    port = os.getenv("POSTGRES_CONN_PORT")
    if not all((dbname, user, password, host, port)):
        pytest.skip("ELT / Postgres environment variables are not set.")

    conn = psycopg2.connect(
        dbname=dbname, user=user, password=password, host=host, port=port
    )
    try:
        yield conn
    finally:
        conn.close()
