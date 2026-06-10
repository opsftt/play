"""Cut highlight clips from a source video based on timestamp suggestions."""
import os
import subprocess


def cut_clip(
    source_path: str,
    start: float,
    end: float,
    out_dir: str,
    label: str = "clip",
) -> str:
    """
    Cut a clip from source_path between start and end seconds.
    Returns the path to the output file.
    Adds a 0.5-second buffer on each side when possible.
    """
    os.makedirs(out_dir, exist_ok=True)
    safe_label = label.replace(" ", "_").replace("/", "-")
    out_path = os.path.join(out_dir, f"{safe_label}_{start:.0f}-{end:.0f}.mp4")

    # Add small buffer so the clip doesn't start/end mid-word
    buf_start = max(0.0, start - 0.5)
    duration = (end + 0.5) - buf_start

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-ss", str(buf_start),
            "-i", source_path,
            "-t", str(duration),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            out_path,
        ],
        check=True,
        capture_output=True,
    )
    return out_path


def cut_all_suggestions(
    source_path: str,
    content_package: dict,
    out_dir: str,
    video_title: str,
) -> dict:
    """
    Walk the content package, cut every clip_suggestion, and return a mapping
    {platform_key: local_clip_path}.
    """
    clips = {}
    base = video_title.replace(" ", "_")[:40]

    targets = [
        ("instagram_reel", content_package["instagram"]["reel"].get("clip_suggestion")),
        ("x_tweet",        content_package["x"]["tweet"].get("clip_suggestion")),
        ("tiktok",         content_package["tiktok"].get("clip_suggestion")),
        ("youtube_short",  content_package["youtube"]["short"].get("clip_suggestion")),
    ]

    for label, suggestion in targets:
        if not suggestion:
            continue
        start = float(suggestion.get("start", 0))
        end = float(suggestion.get("end", 0))
        if end <= start:
            continue
        try:
            path = cut_clip(source_path, start, end, out_dir, f"{base}_{label}")
            clips[label] = path
        except subprocess.CalledProcessError as exc:
            clips[label] = f"ERROR: {exc.stderr.decode()[:200]}"

    return clips
