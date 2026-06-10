"""
Social Media Content Bot — main orchestration pipeline.

Flow:
  1. Poll Google Drive for new videos (or receive one via webhook)
  2. Download the video locally
  3. Transcribe with Whisper
  4. Generate platform content with Claude
  5. Cut highlight clips with ffmpeg
  6. Export drafts to Google Sheet
  7. Upload clips back to Drive output folder
  8. Mark video as processed
"""
import os
import sys
import json
import time
import shutil
import traceback
from pathlib import Path

import config
from processors.drive_watcher import poll_new_videos, download_video, mark_seen
from processors.transcriber import transcribe
from processors.content_generator import generate_all_platforms
from processors.video_processor import cut_all_suggestions
from outputs.sheets_exporter import export_drafts
from outputs.drive_uploader import upload_clips

# Drive folder where output clips are uploaded (defaults to first watch folder)
OUTPUT_FOLDER_ID = os.getenv("DRIVE_OUTPUT_FOLDER_ID") or (
    config.DRIVE_WATCH_FOLDER_IDS[0] if config.DRIVE_WATCH_FOLDER_IDS else None
)


def _detect_video_type(filename: str, description: str = "") -> str:
    """Infer video type from filename or Drive description field."""
    text = (filename + " " + description).lower()
    if "testim" in text or "review" in text or "result" in text:
        return "testimonial"
    if "webinar" in text or "workshop" in text or "session" in text:
        return "webinar"
    if "course" in text or "lesson" in text or "tutorial" in text or "module" in text:
        return "course"
    return "live_trading"


def process_video(file_meta: dict) -> dict:
    """Full pipeline for a single Drive video file. Returns a summary dict."""
    file_id = file_meta["id"]
    file_name = file_meta["name"]
    description = file_meta.get("description", "")
    video_type = _detect_video_type(file_name, description)

    tmp_dir = os.path.join(config.TEMP_DIR, file_id)
    clips_dir = os.path.join(tmp_dir, "clips")
    os.makedirs(tmp_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"[bot] Processing: {file_name}  (type={video_type})")

    try:
        # ── 1. Download ──────────────────────────────────────────────
        print("[bot] Downloading from Drive…")
        video_path = download_video(config.GOOGLE_SERVICE_ACCOUNT_JSON, file_id, tmp_dir)
        duration = _get_duration(video_path)
        print(f"[bot] Downloaded → {video_path}  ({duration:.0f}s)")

        # ── 2. Transcribe ────────────────────────────────────────────
        print(f"[bot] Transcribing with Whisper ({config.WHISPER_MODEL})…")
        transcription = transcribe(video_path, config.WHISPER_MODEL, tmp_dir)
        word_count = len(transcription["text"].split())
        print(f"[bot] Transcription complete: {word_count} words")

        # ── 3. Generate content ──────────────────────────────────────
        print("[bot] Generating content with Claude…")
        content_package = generate_all_platforms(
            transcript=transcription["text"],
            segments=transcription["segments"],
            video_type=video_type,
            video_title=Path(file_name).stem,
            duration_seconds=duration,
        )
        print("[bot] Content package generated")

        # ── 4. Cut clips ─────────────────────────────────────────────
        print("[bot] Cutting highlight clips…")
        clips = cut_all_suggestions(
            video_path, content_package, clips_dir, Path(file_name).stem
        )
        print(f"[bot] Clips: {list(clips.keys())}")

        # ── 5. Export drafts to Sheets ───────────────────────────────
        print("[bot] Exporting drafts to Google Sheet…")
        export_drafts(
            config.GOOGLE_SERVICE_ACCOUNT_JSON,
            config.GOOGLE_SHEET_ID,
            video_title=Path(file_name).stem,
            video_type=video_type,
            content_package=content_package,
        )

        # ── 6. Upload clips to Drive ─────────────────────────────────
        if OUTPUT_FOLDER_ID and clips:
            print("[bot] Uploading clips to Drive…")
            uploaded = upload_clips(
                config.GOOGLE_SERVICE_ACCOUNT_JSON,
                clips,
                OUTPUT_FOLDER_ID,
                Path(file_name).stem,
            )
        else:
            uploaded = {}

        # ── 7. Mark as seen so we don't re-process ───────────────────
        mark_seen(file_id)

        return {
            "status": "ok",
            "file": file_name,
            "video_type": video_type,
            "clips_generated": list(clips.keys()),
            "drive_clips": uploaded,
        }

    except Exception as exc:
        traceback.print_exc()
        return {"status": "error", "file": file_name, "error": str(exc)}
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _get_duration(video_path: str) -> float:
    import subprocess
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path,
        ],
        capture_output=True, text=True
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def run_poll():
    """Poll Drive for new videos and process each one."""
    if not config.DRIVE_WATCH_FOLDER_IDS:
        print("[bot] No DRIVE_WATCH_FOLDER_IDS configured. Exiting.")
        sys.exit(1)

    print(f"[bot] Polling {len(config.DRIVE_WATCH_FOLDER_IDS)} folder(s)…")
    new_videos = poll_new_videos(
        config.GOOGLE_SERVICE_ACCOUNT_JSON,
        config.DRIVE_WATCH_FOLDER_IDS,
    )

    if not new_videos:
        print("[bot] No new videos found.")
        return []

    print(f"[bot] Found {len(new_videos)} new video(s)")
    results = []
    for video in new_videos:
        result = process_video(video)
        results.append(result)
        time.sleep(2)  # be polite to APIs between videos

    print("\n[bot] Done.")
    print(json.dumps(results, indent=2))
    return results


def run_scheduler(interval_minutes: int = 30):
    """Run the poll loop on a schedule."""
    import schedule
    print(f"[bot] Scheduler started — polling every {interval_minutes} minutes")
    schedule.every(interval_minutes).minutes.do(run_poll)
    run_poll()  # run immediately on start
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Social Media Content Bot")
    parser.add_argument("--poll", action="store_true", help="Run one poll cycle")
    parser.add_argument("--schedule", type=int, metavar="MINUTES",
                        help="Run on a schedule every N minutes")
    parser.add_argument("--webhook", action="store_true",
                        help="Start the webhook server (for n8n / Make.com)")
    args = parser.parse_args()

    if args.schedule:
        run_scheduler(args.schedule)
    elif args.webhook:
        from webhook_server import create_app
        app = create_app()
        app.run(host="0.0.0.0", port=config.PORT, debug=False)
    else:
        run_poll()
