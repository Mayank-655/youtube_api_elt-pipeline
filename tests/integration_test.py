import psycopg2
import pytest
import requests


@pytest.mark.integration
def test_youtube_api_response(airflow_variable):
    api_key = airflow_variable("API_KEY")
    channel_handle = airflow_variable("CHANNEL_HANDLE")
    if not api_key or not channel_handle:
        pytest.skip("API_KEY / CHANNEL_HANDLE not set (e.g. local run without env).")

    url = (
        "https://youtube.googleapis.com/youtube/v3/channels"
        "?part=contentDetails"
        f"&forHandle={channel_handle}&key={api_key}"
    )
    try:
        response = requests.get(url, timeout=30)
        assert response.status_code == 200
    except requests.RequestException as e:
        pytest.fail(f"Request to YouTube API failed: {e}")


@pytest.mark.integration
def test_real_postgres_connection(real_postgres_connection):
    cursor = None
    try:
        cursor = real_postgres_connection.cursor()
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()
        assert result[0] == 1
    except psycopg2.Error as e:
        pytest.fail(f"Database query failed: {e}")
    finally:
        if cursor is not None:
            cursor.close()
