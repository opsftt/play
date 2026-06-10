"""Poll Google Drive folders for new video files and return metadata."""
import os
import io
import json
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
VIDEO_MIME_TYPES = [
    "video/mp4", "video/quicktime", "video/x-msvideo",
    "video/x-matroska", "video/webm", "video/mpeg",
]
STATE_FILE = Path(".drive_state.json")


def _build_service(credentials_path: str):
    creds = service_account.Credentials.from_service_account_file(
        credentials_path, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)


def _load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"seen": []}


def _save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def poll_new_videos(credentials_path: str, folder_ids: list[str]) -> list[dict]:
    """Return list of new video file metadata dicts not yet processed."""
    service = _build_service(credentials_path)
    state = _load_state()
    seen = set(state["seen"])
    new_files = []

    mime_filter = " or ".join(f"mimeType='{m}'" for m in VIDEO_MIME_TYPES)
    folder_filter = " or ".join(f"'{fid}' in parents" for fid in folder_ids)
    query = f"({mime_filter}) and ({folder_filter}) and trashed=false"

    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType, modifiedTime, parents, description)",
        orderBy="modifiedTime desc",
        pageSize=50,
    ).execute()

    for f in results.get("files", []):
        if f["id"] not in seen:
            new_files.append(f)

    return new_files


def download_video(credentials_path: str, file_id: str, dest_dir: str) -> str:
    """Download a Drive file to dest_dir and return the local path."""
    service = _build_service(credentials_path)
    meta = service.files().get(fileId=file_id, fields="name").execute()
    dest_path = os.path.join(dest_dir, meta["name"])
    os.makedirs(dest_dir, exist_ok=True)

    request = service.files().get_media(fileId=file_id)
    with open(dest_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

    return dest_path


def mark_seen(file_id: str):
    state = _load_state()
    state["seen"].append(file_id)
    _save_state(state)
