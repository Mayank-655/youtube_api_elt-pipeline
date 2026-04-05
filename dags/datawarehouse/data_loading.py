import json
import logging
import os
from datetime import date

logger = logging.getLogger(__name__)


def _data_dir() -> str:
    base = os.environ.get("AIRFLOW_HOME", "/opt/airflow")
    return os.path.join(base, "data")


def load_data():
    """Load today's extract file produced by save_to_json (list of video dicts)."""
    file_path = os.path.join(_data_dir(), f"YT_data_{date.today()}.json")
    try:
        logger.info("Processing file: YT_data_%s.json", date.today())
        with open(file_path, encoding="utf-8") as raw_data:
            data = json.load(raw_data)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "videos" in data:
            return data["videos"]
        raise ValueError("Expected a JSON list of videos or an object with a 'videos' key.")
    except FileNotFoundError:
        logger.error("File not found: %s", file_path)
        raise
    except json.JSONDecodeError:
        logger.error("Invalid JSON in file: %s", file_path)
        raise
