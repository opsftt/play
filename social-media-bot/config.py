import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "credentials/google_service_account.json")
DRIVE_WATCH_FOLDER_IDS = [f.strip() for f in os.getenv("DRIVE_WATCH_FOLDER_IDS", "").split(",") if f.strip()]
GOOGLE_SHEET_ID = os.environ["GOOGLE_SHEET_ID"]
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "changeme")
PORT = int(os.getenv("PORT", 5050))
BRAND_NAME = os.getenv("BRAND_NAME", "Freedom Team Trading")
BRAND_VOICE = os.getenv("BRAND_VOICE", "energetic, educational, empowering, results-driven")
BRAND_NICHE = os.getenv("BRAND_NICHE", "forex and futures trading education")
NICHE_HASHTAGS = os.getenv("NICHE_HASHTAGS", "#forex #futurestrading #tradinglifestyle")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
TEMP_DIR = os.getenv("TEMP_DIR", "/tmp/smbot")

# Video type labels used to tailor prompts
VIDEO_TYPES = ["live_trading", "webinar", "testimonial", "course"]

# Platform character/duration limits
PLATFORM_LIMITS = {
    "instagram_reel":  {"max_seconds": 90,   "caption_chars": 2200},
    "instagram_post":  {"max_seconds": 60,   "caption_chars": 2200},
    "x_tweet":         {"max_seconds": 140,  "caption_chars": 280},
    "x_thread":        {"max_seconds": None, "caption_chars": 280},
    "tiktok":          {"max_seconds": 180,  "caption_chars": 2200},
    "youtube_short":   {"max_seconds": 60,   "caption_chars": 5000},
    "youtube_long":    {"max_seconds": None, "caption_chars": 5000},
}
