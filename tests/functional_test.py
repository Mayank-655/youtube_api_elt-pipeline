"""Tests for warehouse helper functions without the Airflow runtime."""

import json
from datetime import date, time
from pathlib import Path

import pytest

from datawarehouse.data_loading import load_data
from datawarehouse.data_transformation import parse_duration, transform_data


@pytest.mark.functional
def test_parse_duration_minutes_seconds():
    td = parse_duration("PT2M30S")
    assert td.total_seconds() == 150


@pytest.mark.functional
def test_transform_data_sets_time_and_video_type():
    row = {
        "Video_ID": "abc12345678",
        "Video_Title": "t",
        "Upload_Date": "2025-01-01T00:00:00Z",
        "Duration": "PT1M30S",
        "Video_Views": 1,
        "Likes_Count": 0,
        "Comments_Count": 0,
    }
    out = transform_data(dict(row))
    assert out["Video_Type"] == "Normal"
    assert isinstance(out["Duration"], time)


@pytest.mark.functional
def test_transform_data_shorts_under_sixty_seconds():
    row = {
        "Video_ID": "abc12345678",
        "Video_Title": "short",
        "Upload_Date": "2025-01-01T00:00:00Z",
        "Duration": "PT45S",
        "Video_Views": 1,
        "Likes_Count": 0,
        "Comments_Count": 0,
    }
    out = transform_data(dict(row))
    assert out["Video_Type"] == "Shorts"


@pytest.mark.functional
def test_load_data_reads_json_list(tmp_path, monkeypatch):
    monkeypatch.setenv("AIRFLOW_HOME", str(tmp_path))
    data_dir = Path(tmp_path) / "data"
    data_dir.mkdir()
    payload = [{"video_id": "x", "title": "T", "publishedAt": "2025-01-01T00:00:00Z"}]
    (data_dir / f"YT_data_{date.today()}.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    assert load_data() == payload


@pytest.mark.functional
def test_load_data_reads_wrapped_videos_key(tmp_path, monkeypatch):
    monkeypatch.setenv("AIRFLOW_HOME", str(tmp_path))
    data_dir = Path(tmp_path) / "data"
    data_dir.mkdir()
    inner = [{"video_id": "y"}]
    (data_dir / f"YT_data_{date.today()}.json").write_text(
        json.dumps({"videos": inner}), encoding="utf-8"
    )
    assert load_data() == inner
