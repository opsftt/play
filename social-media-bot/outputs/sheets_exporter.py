"""Write content drafts to a Google Sheet for review."""
import json
from datetime import datetime
import gspread
from google.oauth2 import service_account

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

# Column headers for the Drafts sheet
HEADERS = [
    "Timestamp", "Video Title", "Video Type", "Platform", "Format",
    "Hook / Title", "Caption / Body", "Hashtags", "Clip Start (s)", "Clip End (s)",
    "Clip Reason", "Extra (slides / thread / tags)", "Status",
]


def _get_sheet(credentials_path: str, sheet_id: str):
    creds = service_account.Credentials.from_service_account_file(
        credentials_path, scopes=SCOPES
    )
    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id)


def _ensure_worksheet(spreadsheet, title: str):
    try:
        ws = spreadsheet.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=title, rows=1000, cols=len(HEADERS))
        ws.append_row(HEADERS, value_input_option="USER_ENTERED")
    return ws


def _clip_info(clip_suggestion: dict | None):
    if not clip_suggestion:
        return "", "", ""
    return (
        str(clip_suggestion.get("start", "")),
        str(clip_suggestion.get("end", "")),
        clip_suggestion.get("reason", ""),
    )


def export_drafts(
    credentials_path: str,
    sheet_id: str,
    video_title: str,
    video_type: str,
    content_package: dict,
):
    """Append all generated drafts to the 'Drafts' worksheet."""
    spreadsheet = _get_sheet(credentials_path, sheet_id)
    ws = _ensure_worksheet(spreadsheet, "Drafts")
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    rows = []

    ig = content_package.get("instagram", {})
    reel = ig.get("reel", {})
    cs, ce, cr = _clip_info(reel.get("clip_suggestion"))
    rows.append([
        now, video_title, video_type, "Instagram", "Reel",
        reel.get("hook", ""), reel.get("caption", ""), reel.get("hashtags", ""),
        cs, ce, cr, "", "DRAFT",
    ])

    carousel = ig.get("carousel_post", {})
    rows.append([
        now, video_title, video_type, "Instagram", "Carousel Post",
        carousel.get("slide_texts", [""])[0],
        carousel.get("caption", ""),
        carousel.get("hashtags", ""),
        "", "", "",
        json.dumps(carousel.get("slide_texts", []), ensure_ascii=False),
        "DRAFT",
    ])

    x = content_package.get("x", {})
    tweet = x.get("tweet", {})
    cs, ce, cr = _clip_info(tweet.get("clip_suggestion"))
    rows.append([
        now, video_title, video_type, "X (Twitter)", "Tweet",
        "", tweet.get("text", ""), "", cs, ce, cr, "", "DRAFT",
    ])

    thread = x.get("thread", {})
    rows.append([
        now, video_title, video_type, "X (Twitter)", "Thread",
        thread.get("tweets", [""])[0], "",  "", "", "", "",
        json.dumps(thread.get("tweets", []), ensure_ascii=False),
        "DRAFT",
    ])

    tt = content_package.get("tiktok", {})
    cs, ce, cr = _clip_info(tt.get("clip_suggestion"))
    rows.append([
        now, video_title, video_type, "TikTok", "Video",
        tt.get("hook", ""), tt.get("caption", ""), tt.get("hashtags", ""),
        cs, ce, cr,
        json.dumps(tt.get("b_roll_ideas", []), ensure_ascii=False),
        "DRAFT",
    ])

    yt = content_package.get("youtube", {})
    short = yt.get("short", {})
    cs, ce, cr = _clip_info(short.get("clip_suggestion"))
    rows.append([
        now, video_title, video_type, "YouTube", "Short",
        short.get("title", ""), "", "", cs, ce, cr, "", "DRAFT",
    ])

    long_form = yt.get("long_form", {})
    rows.append([
        now, video_title, video_type, "YouTube", "Long-form",
        long_form.get("title", ""),
        long_form.get("description", ""),
        json.dumps(long_form.get("tags", []), ensure_ascii=False),
        "", "", "",
        json.dumps({
            "thumbnail_text": long_form.get("thumbnail_text", ""),
            "chapters": long_form.get("chapters", []),
        }, ensure_ascii=False),
        "DRAFT",
    ])

    ws.append_rows(rows, value_input_option="USER_ENTERED")
    print(f"[sheets] Wrote {len(rows)} draft rows for '{video_title}'")
