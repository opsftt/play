# Freedom Team Trading — Social Media Content Bot

Automatically turns your trading videos (live sessions, webinars, testimonials, course clips)
into ready-to-review social media drafts for **Instagram, X, TikTok, and YouTube**.

---

## What it does

| Step | Description |
|------|-------------|
| 1 | Watches Google Drive folder(s) for new videos |
| 2 | Downloads & transcribes audio with OpenAI Whisper |
| 3 | Sends transcript to Claude (Sonnet 4.6) for platform-specific copy |
| 4 | Cuts highlight clips with `ffmpeg` based on AI timestamp suggestions |
| 5 | Writes all drafts to a Google Sheet for human review |
| 6 | Uploads clips back to a Drive output folder |

---

## Generated content per video

| Platform | Format | What's generated |
|----------|--------|-----------------|
| Instagram | Reel | Hook, caption, 30 hashtags, clip suggestion |
| Instagram | Carousel Post | 5 slide texts + caption |
| X (Twitter) | Tweet | Hook tweet ≤ 280 chars + clip |
| X (Twitter) | Thread | 5-tweet breakdown |
| TikTok | Video | Hook line, caption, hashtags, b-roll ideas, clip |
| YouTube | Short | Title + clip suggestion |
| YouTube | Long-form | SEO title, full description, tags, thumbnail text, chapters |

---

## Setup

### 1. Prerequisites

```bash
# System dependencies
sudo apt-get install ffmpeg

# Python 3.11+
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Google Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com) → IAM & Admin → Service Accounts
2. Create a service account, download the JSON key
3. Save it to `credentials/google_service_account.json`
4. Share your Drive folder(s) and Google Sheet with the service account email (Editor access)
5. Enable these APIs: **Google Drive API**, **Google Sheets API**

### 3. Environment variables

```bash
cp .env.example .env
# Edit .env with your keys and folder IDs
```

Key values to fill in:

| Variable | Where to find it |
|----------|-----------------|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Path to downloaded JSON key |
| `DRIVE_WATCH_FOLDER_IDS` | Drive folder URL → the long ID after `/folders/` |
| `GOOGLE_SHEET_ID` | Sheet URL → the long ID after `/spreadsheets/d/` |

---

## Running the bot

### One-time poll (manual trigger)
```bash
python main.py --poll
```

### Scheduled (every 30 minutes)
```bash
python main.py --schedule 30
```

### Webhook server (for n8n / Make.com)
```bash
python main.py --webhook
# Server starts on port 5050 (configurable via PORT env var)
```

---

## n8n / Make.com Integration

### Option A — Scheduled trigger
Use a **Schedule** node → HTTP POST to `http://your-server:5050/poll`

### Option B — Drive trigger (instant)
1. Use n8n's **Google Drive Trigger** node (watches a folder for new files)
2. Add an **HTTP Request** node:
   - Method: `POST`
   - URL: `http://your-server:5050/process-drive-file`
   - Body:
     ```json
     {
       "file_id": "{{ $json.id }}",
       "file_name": "{{ $json.name }}",
       "description": "{{ $json.description }}"
     }
     ```

---

## Google Sheet structure

The bot writes to a **Drafts** tab with these columns:

`Timestamp | Video Title | Video Type | Platform | Format | Hook/Title | Caption/Body | Hashtags | Clip Start | Clip End | Clip Reason | Extra | Status`

Change **Status** from `DRAFT` → `APPROVED` / `SKIP` to track what your team has reviewed.

---

## Video type auto-detection

The bot infers type from the filename:

| Keywords in filename | Detected type |
|----------------------|--------------|
| testim, review, result | `testimonial` |
| webinar, workshop, session | `webinar` |
| course, lesson, tutorial, module | `course` |
| anything else | `live_trading` |

Override by adding a description in Drive's file details.

---

## Customising the brand voice

Edit these in `.env`:
```
BRAND_NAME=Freedom Team Trading
BRAND_VOICE=energetic, educational, empowering, results-driven
BRAND_NICHE=forex and futures trading education
NICHE_HASHTAGS=#forex #futurestrading #tradinglifestyle ...
```
