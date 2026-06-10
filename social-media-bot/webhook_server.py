"""
Flask webhook server — lets n8n / Make.com / Zapier trigger the bot.

Endpoints:
  POST /process-drive-file   { "file_id": "...", "file_name": "..." }
  POST /poll                 {} (trigger a full Drive poll)
  GET  /health               healthcheck
"""
import hmac
import hashlib
import threading
from flask import Flask, request, jsonify
import config
from main import process_video, run_poll


def _verify_signature(payload: bytes, sig_header: str) -> bool:
    """Optional HMAC-SHA256 signature check for webhook security."""
    if not sig_header:
        return True  # skip if caller doesn't send a signature
    expected = hmac.new(
        config.WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", sig_header)


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "brand": config.BRAND_NAME})

    @app.post("/process-drive-file")
    def process_drive_file():
        sig = request.headers.get("X-Hub-Signature-256", "")
        if not _verify_signature(request.data, sig):
            return jsonify({"error": "invalid signature"}), 401

        body = request.get_json(silent=True) or {}
        file_id = body.get("file_id")
        file_name = body.get("file_name", "unknown.mp4")

        if not file_id:
            return jsonify({"error": "file_id is required"}), 400

        file_meta = {
            "id": file_id,
            "name": file_name,
            "description": body.get("description", ""),
        }

        # Run in a background thread so the webhook returns immediately
        def _run():
            result = process_video(file_meta)
            print(f"[webhook] Finished processing {file_name}: {result['status']}")

        threading.Thread(target=_run, daemon=True).start()
        return jsonify({"status": "queued", "file_name": file_name}), 202

    @app.post("/poll")
    def poll():
        sig = request.headers.get("X-Hub-Signature-256", "")
        if not _verify_signature(request.data, sig):
            return jsonify({"error": "invalid signature"}), 401

        threading.Thread(target=run_poll, daemon=True).start()
        return jsonify({"status": "poll started"}), 202

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=config.PORT, debug=True)
