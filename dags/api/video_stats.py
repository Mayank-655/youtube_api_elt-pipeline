import json
import os
from datetime import date
from typing import Any

import requests
from airflow.decorators import task
from airflow.models import Variable

REQUEST_TIMEOUT_SECONDS = 30


def _data_dir() -> str:
    """Writable folder visible on the host: compose mounts ./data -> /opt/airflow/data."""
    base = os.environ.get("AIRFLOW_HOME", "/opt/airflow")
    out = os.path.join(base, "data")
    os.makedirs(out, exist_ok=True)
    return out


def _data_path(filename: str) -> str:
    return os.path.join(_data_dir(), filename)


def _api_key() -> str:
    try:
        return Variable.get("API_KEY")
    except Exception:
        key = os.getenv("API_KEY")
        if key:
            return key
        raise ValueError("Missing API_KEY (Airflow Variable or env).") from None


def _channel_handle() -> str:
    try:
        return Variable.get("CHANNEL_HANDLE")
    except Exception:
        handle = os.getenv("CHANNEL_HANDLE")
        if handle:
            return handle
        raise ValueError("Missing CHANNEL_HANDLE (Airflow Variable or env).") from None


def chunked(seq: list[str], size: int) -> list[list[str]]:
    return [seq[i : i + size] for i in range(0, len(seq), size)]


@task
def get_playlist_id() -> str:
    """Resolve channel handle → uploads playlist id; save raw channels response."""
    api_key = _api_key()
    channel_handle = _channel_handle()

    url = "https://youtube.googleapis.com/youtube/v3/channels"
    params = {
        "part": "contentDetails",
        "forHandle": channel_handle,
        "key": api_key,
    }

    response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    print("channels status:", response.status_code)
    response.raise_for_status()
    data = response.json()

    channel_path = _data_path("channel_response.json")
    with open(channel_path, "w", encoding="utf-8") as channel_file:
        json.dump(data, channel_file, ensure_ascii=False, indent=2)
    print(f"Saved to {channel_path}")

    return data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]


@task
def get_video_ids(playlist_id: str) -> dict[str, Any]:
    """Paginate playlistItems; return uploads playlist id and unique video ids."""
    api_key = _api_key()
    url = "https://youtube.googleapis.com/youtube/v3/playlistItems"
    collected: list[str] = []
    page_token: str | None = None

    while True:
        params = {
            "part": "contentDetails",
            "playlistId": playlist_id,
            "maxResults": 50,
            "key": api_key,
        }
        if page_token:
            params["pageToken"] = page_token

        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        print("playlistItems status:", response.status_code)
        response.raise_for_status()
        data = response.json()

        for item in data.get("items", []):
            vid = (item.get("contentDetails") or {}).get("videoId")
            if vid:
                collected.append(vid)

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    seen: set[str] = set()
    unique: list[str] = []
    for vid in collected:
        if vid not in seen:
            seen.add(vid)
            unique.append(vid)

    return {"uploads_playlist_id": playlist_id, "video_ids": unique}


@task
def extract_video_data(video_ids: dict[str, Any]) -> dict[str, Any]:
    """videos.list in batches; output one dict for save_to_json(extract_data)."""
    uploads_playlist_id = video_ids["uploads_playlist_id"]
    ids: list[str] = video_ids["video_ids"]

    api_key = _api_key()
    url = "https://youtube.googleapis.com/youtube/v3/videos"
    rows: list[dict] = []

    for batch in chunked(ids, 50):
        params = {
            "part": "snippet,contentDetails,statistics",
            "id": ",".join(batch),
            "key": api_key,
            "maxResults": 50,
        }

        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        print("videos status:", response.status_code)
        response.raise_for_status()
        data = response.json()

        for item in data.get("items", []):
            snippet = item.get("snippet") or {}
            content_details = item.get("contentDetails") or {}
            stats = item.get("statistics") or {}

            rows.append(
                {
                    "video_id": item.get("id"),
                    "title": snippet.get("title"),
                    "publishedAt": snippet.get("publishedAt"),
                    "duration": content_details.get("duration"),
                    "viewCount": stats.get("viewCount"),
                    "likeCount": stats.get("likeCount"),
                    "commentCount": stats.get("commentCount"),
                }
            )

    return {
        "uploads_playlist_id": uploads_playlist_id,
        "video_ids": ids,
        "videos": rows,
    }


@task
def save_to_json(extract_data: dict[str, Any]) -> None:
    """Persist extract payload to JSON files under the Airflow data directory."""
    channel_handle = _channel_handle()
    uploads_playlist_id = extract_data["uploads_playlist_id"]
    video_ids: list[str] = extract_data["video_ids"]
    video_data: list[dict] = extract_data["videos"]

    print("Uploads playlist ID:", uploads_playlist_id)
    print(f"Fetched {len(video_ids)} videoIds.")

    ids_path = _data_path("video_ids.json")
    with open(ids_path, "w", encoding="utf-8") as ids_file:
        json.dump(
            {
                "channel_handle": channel_handle,
                "uploads_playlist_id": uploads_playlist_id,
                "video_ids": video_ids,
            },
            ids_file,
            ensure_ascii=False,
            indent=2,
        )
    print(f"Saved to {ids_path}")

    print(f"Fetched video data for {len(video_data)} videos.")
    data_path = _data_path("video_data.json")
    with open(data_path, "w", encoding="utf-8") as video_file:
        json.dump(
            {
                "channel_handle": channel_handle,
                "uploads_playlist_id": uploads_playlist_id,
                "count": len(video_data),
                "videos": video_data,
            },
            video_file,
            ensure_ascii=False,
            indent=2,
        )
    print(f"Saved to {data_path}")

    # Daily flat list consumed by datawarehouse.load_data().
    yt_daily = _data_path(f"YT_data_{date.today()}.json")
    with open(yt_daily, "w", encoding="utf-8") as daily_file:
        json.dump(video_data, daily_file, ensure_ascii=False, indent=2)
    print(f"Saved to {yt_daily}")
