"""Extract audio from a video and transcribe it with OpenAI Whisper."""
import os
import subprocess
import whisper

_model_cache: dict = {}


def _get_model(model_name: str):
    if model_name not in _model_cache:
        _model_cache[model_name] = whisper.load_model(model_name)
    return _model_cache[model_name]


def extract_audio(video_path: str, out_dir: str) -> str:
    """Extract audio track to a 16kHz mono WAV file for Whisper."""
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(video_path))[0]
    audio_path = os.path.join(out_dir, f"{base}.wav")
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", video_path,
            "-ac", "1", "-ar", "16000",
            "-vn", audio_path,
        ],
        check=True,
        capture_output=True,
    )
    return audio_path


def transcribe(video_path: str, model_name: str = "base", out_dir: str = "/tmp") -> dict:
    """
    Transcribe a video file.

    Returns a dict with:
        text        – full transcript string
        segments    – list of {start, end, text} dicts (for clip suggestions)
        language    – detected language
    """
    audio_path = extract_audio(video_path, out_dir)
    model = _get_model(model_name)
    result = model.transcribe(audio_path, verbose=False)
    os.remove(audio_path)
    return {
        "text": result["text"].strip(),
        "segments": [
            {"start": s["start"], "end": s["end"], "text": s["text"].strip()}
            for s in result["segments"]
        ],
        "language": result.get("language", "en"),
    }
