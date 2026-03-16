import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()  # reads .env in the same folder

API_KEY = os.getenv("API_KEY")
CHANNEL_HANDLE = os.getenv("CHANNEL_HANDLE")

if not API_KEY or not CHANNEL_HANDLE:
    raise ValueError("Missing API_KEY or CHANNEL_HANDLE. Check your .env file.")

url = "https://youtube.googleapis.com/youtube/v3/channels"
params = {
    "part": "contentDetails",
    "forHandle": CHANNEL_HANDLE,
    "key": API_KEY,
}

response = requests.get(url, params=params)
print(response.status_code)
response.raise_for_status()

data = response.json()

channel_items = data["items"][0]
channel_playlist_id = channel_items["contentDetails"]["relatedPlaylists"]["uploads"]
print("Uploads playlist ID:", channel_playlist_id)

with open("video_stats.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("Saved to video_stats.json")