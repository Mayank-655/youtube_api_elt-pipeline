import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()  # reads .env in the same folder

API_KEY = os.getenv("API_KEY")
CHANNEL_HANDLE = os.getenv("CHANNEL_HANDLE")

if not API_KEY or not CHANNEL_HANDLE:
    raise ValueError("Missing API_KEY or CHANNEL_HANDLE. Check your .env file.")


def get_uploads_playlist_id(*, api_key: str, channel_handle: str) -> str:
    url = "https://youtube.googleapis.com/youtube/v3/channels"
    params = {
        "part": "contentDetails",
        "forHandle": channel_handle,
        "key": api_key,
    }

    resp = requests.get(url, params=params)
    print("channels status:", resp.status_code)
    resp.raise_for_status()
    data = resp.json()

    with open("channel_response.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Saved to channel_response.json")

    return data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]


def get_all_video_ids_from_playlist(*, api_key: str, playlist_id: str) -> list[str]:
    url = "https://youtube.googleapis.com/youtube/v3/playlistItems"
    video_ids: list[str] = []
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

        resp = requests.get(url, params=params)
        print("playlistItems status:", resp.status_code)
        resp.raise_for_status()
        data = resp.json()

        for item in data.get("items", []):
            vid = (item.get("contentDetails") or {}).get("videoId")
            if vid:
                video_ids.append(vid)

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    # preserve stable ordering while deduping
    seen: set[str] = set()
    unique: list[str] = []
    for vid in video_ids:
        if vid not in seen:
            seen.add(vid)
            unique.append(vid)
    return unique


def chunked(seq: list[str], size: int) -> list[list[str]]:
    return [seq[i : i + size] for i in range(0, len(seq), size)]


def get_video_data(*, api_key: str, video_ids: list[str]) -> list[dict]:
    """
    Fetches video variables needed for analysis:
    video_id, title, publishedAt, duration, viewCount, likeCount, commentCount
    """

    url = "https://youtube.googleapis.com/youtube/v3/videos"
    rows: list[dict] = []

    for batch in chunked(video_ids, 50):  # API allows up to 50 IDs per call
        params = {
            "part": "snippet,contentDetails,statistics",
            "id": ",".join(batch),
            "key": api_key,
            "maxResults": 50,
        }

        resp = requests.get(url, params=params)
        print("videos status:", resp.status_code)
        resp.raise_for_status()
        data = resp.json()

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

    return rows


uploads_playlist_id = get_uploads_playlist_id(api_key=API_KEY, channel_handle=CHANNEL_HANDLE)
print("Uploads playlist ID:", uploads_playlist_id)

video_ids = get_all_video_ids_from_playlist(api_key=API_KEY, playlist_id=uploads_playlist_id)
print(f"Fetched {len(video_ids)} videoIds.")

with open("video_ids.json", "w", encoding="utf-8") as f:
    json.dump(
        {
            "channel_handle": CHANNEL_HANDLE,
            "uploads_playlist_id": uploads_playlist_id,
            "video_ids": video_ids,
        },
        f,
        ensure_ascii=False,
        indent=2,
    )

print("Saved to video_ids.json")

video_data = get_video_data(api_key=API_KEY, video_ids=video_ids)
print(f"Fetched video data for {len(video_data)} videos.")

with open("video_data.json", "w", encoding="utf-8") as f:
    json.dump(
        {
            "channel_handle": CHANNEL_HANDLE,
            "uploads_playlist_id": uploads_playlist_id,
            "count": len(video_data),
            "videos": video_data,
        },
        f,
        ensure_ascii=False,
        indent=2,
    )

print("Saved to video_data.json")