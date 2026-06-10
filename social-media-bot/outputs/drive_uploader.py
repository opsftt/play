"""Upload generated clips back to a Google Drive output folder."""
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def _build_service(credentials_path: str):
    creds = service_account.Credentials.from_service_account_file(
        credentials_path, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)


def upload_clips(
    credentials_path: str,
    clips: dict,
    parent_folder_id: str,
    video_title: str,
) -> dict:
    """
    Upload each clip in {platform: local_path} to a Drive subfolder.
    Returns {platform: drive_file_id}.
    """
    service = _build_service(credentials_path)

    # Create a subfolder for this video's clips
    folder_meta = {
        "name": f"[Clips] {video_title[:60]}",
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_folder_id],
    }
    folder = service.files().create(body=folder_meta, fields="id").execute()
    folder_id = folder["id"]

    uploaded = {}
    for platform, path in clips.items():
        if not isinstance(path, str) or not os.path.exists(path):
            continue
        file_meta = {
            "name": os.path.basename(path),
            "parents": [folder_id],
        }
        media = MediaFileUpload(path, mimetype="video/mp4", resumable=True)
        result = service.files().create(
            body=file_meta, media_body=media, fields="id"
        ).execute()
        uploaded[platform] = result["id"]
        print(f"[drive] Uploaded {platform} clip → {result['id']}")

    return uploaded
