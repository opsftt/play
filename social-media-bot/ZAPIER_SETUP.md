# Zapier-Based Social Media Content Bot (No-Code)

Full no-code content pipeline. One Zap turns every new video in Google Drive
into review-ready drafts for Instagram, X, TikTok, and YouTube — with
**OpusClip auto-cutting the short-form clips**.

---

## The full stack

| Capability | Tool | Notes |
|------------|------|-------|
| Watch Drive for new videos | Zapier | Native Google Drive trigger |
| Transcribe video audio | Zapier | OpenAI Whisper action (or Zapier's built-in transcription) |
| Generate captions/hooks/hashtags with AI | Zapier → Claude | Anthropic action |
| **Cut highlight clips with captions** | **OpusClip** | Official Zapier integration — auto-cuts viral-style shorts with burned-in captions and a virality score |
| Write drafts to Google Sheets | Zapier | Native action |
| Notify the team (Slack/email) | Zapier | Native actions |

---

## Zap 1 — Copy generation (7 steps)

### Step 1 — Trigger: Google Drive → "New File in Folder"
- Connect your Google account
- Select the folder where you drop trading videos
- Optional filter: only continue if file extension is `.mp4` / `.mov`

### Step 2 — Filter by file type (built-in Filter)
- Only continue if **File Extension** contains `mp4`, `mov`, or `mkv`

### Step 3 — Transcribe: OpenAI → "Create Transcription (Whisper)"
- Audio file: use the Drive file's **direct download link** from Step 1
- ⚠️ Whisper has a **25 MB file limit**. For long webinars, use one of:
  - **Zapier's "Transcribe Audio/Video" AI action** (handles larger files), or
  - A **Descript / Rev / AssemblyAI** Zapier integration, or
  - Drop a compressed audio-only export into the folder instead of full video

### Step 4 — Generate content: Anthropic (Claude) → "Send Message"
- Model: `claude-sonnet-4-6`
- Paste the **prompt template below**, mapping in the transcript from Step 3
  and the filename from Step 1

### Step 5 — Parse the response: Formatter → "Utilities: Line-item to Text" 
…or simpler: ask Claude to return content **separated by `|||` delimiters**
(the prompt below does this), then use **Formatter → Text → Split Text** on
`|||` to get each platform's content as its own field.

### Step 6 — Google Sheets → "Create Multiple Spreadsheet Rows"
- Map each split section to a row: Platform, Format, Hook, Caption, Hashtags,
  Clip Timestamps, Status = `DRAFT`

### Step 7 — OpusClip → "Create Project"
- Pass the Drive file's **shareable link** from Step 1
- OpusClip auto-detects the best moments, cuts vertical clips with captions,
  and scores each clip for virality
- Set clip length presets: <60s (Shorts/Reels) and <90s (TikTok)

### Step 8 — Slack or Email notification
- "🎬 New content drafts ready for review: {filename} — [open the sheet] —
  clips processing in OpusClip"

---

## Zap 2 — Log finished clips (3 steps)

OpusClip takes a few minutes to render, so a second small Zap logs results:

1. **Trigger: OpusClip → "Project Completed"**
2. **Google Sheets → "Create Spreadsheet Row(s)"** — one row per clip with
   the clip link, duration, and virality score, Status = `CLIP READY`
3. **Slack/Email** — "✂️ {n} clips ready for {video title}"

Your team then pairs each OpusClip clip with the matching Claude-written
caption from the Drafts sheet, approves, and posts (or pushes to Buffer/Later).

---

## The Claude prompt (paste into Step 4)

```
You are the social media strategist for Freedom Team Trading, a forex and
futures trading education brand. Tone: energetic, educational, empowering.
Never make guaranteed-profit claims.

VIDEO FILENAME: {{Step 1: File Name}}
TRANSCRIPT:
{{Step 3: Transcript}}

First, classify the video as one of: live_trading / webinar / testimonial / course
(based on filename and content).

Then generate the following, with each section separated by exactly "|||" on
its own line, in this exact order:

1. INSTAGRAM REEL — hook (max 10 words), caption (with emojis + CTA), 30 hashtags,
   and the best 30-60 second clip moment described as "CLIP: [quote from
   transcript to search for] — why it works"
|||
2. INSTAGRAM CAROUSEL — 5 slide texts + caption + hashtags
|||
3. X TWEET — single tweet under 280 characters with a strong hook
|||
4. X THREAD — 5 tweets, numbered 1/ through 5/, ending with a CTA
|||
5. TIKTOK — spoken hook line, caption, 20 hashtags, best clip moment
   (same CLIP format), and 3 b-roll ideas
|||
6. YOUTUBE SHORT — title under 60 chars + best clip moment (CLIP format)
|||
7. YOUTUBE LONG-FORM — SEO title under 70 chars, full description with
   chapter timestamps, 8 tags, and thumbnail text (max 6 words)

Output ONLY the content sections separated by |||, no preamble.
```

> The "CLIP: [quote]" lines are a quality-check: compare Claude's picks against
> what OpusClip auto-selected. When they agree, that clip is almost always your
> strongest post. When OpusClip misses a moment Claude flagged, cut that one
> manually in OpusClip's editor (search the transcript for the quote).

---

## Google Sheet columns

| Column | Source |
|--------|--------|
| Date | Zap meta: run timestamp |
| Video Title | Step 1 filename |
| Platform / Format | Static text per row |
| Content | Split sections from Step 5 |
| Status | `DRAFT` (your team flips to APPROVED/SKIP) |

---

## Plan & cost notes

- Multi-step Zaps need a **Zapier Professional plan**
- Each video ≈ 2 Zap runs + 1 Claude API call (a few cents) + 1 Whisper call
  + OpusClip processing minutes (check your OpusClip plan's monthly minutes
  against your video volume — webinars eat minutes fast)
- A 1-hour webinar transcript ≈ ~9k words — comfortably within Claude's context

---

## Quick-start checklist

- [ ] Create the Google Sheet with the columns above, tab named `Drafts`
- [ ] Get an Anthropic API key (console.anthropic.com)
- [ ] Get an OpenAI API key (for Whisper) — or use Zapier's built-in transcription
- [ ] Connect your OpusClip account to Zapier
- [ ] Build Zap 1 (copy generation + OpusClip kickoff)
- [ ] Build Zap 2 (log finished clips)
- [ ] Test with one short video first (under 25 MB)
- [ ] Turn on both Zaps and drop videos into the folder

**End-to-end flow:** video in Drive → transcript → Claude writes all copy →
OpusClip cuts captioned clips → everything lands in one review sheet → your
team approves and posts.
