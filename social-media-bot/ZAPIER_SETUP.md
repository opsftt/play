# Zapier-Based Social Media Content Bot (No-Code)

Full no-code replacement for the Python bot. One Zap turns every new video in
Google Drive into review-ready drafts for Instagram, X, TikTok, and YouTube.

---

## What Zapier can and can't do

| Capability | Zapier? | Notes |
|------------|---------|-------|
| Watch Drive for new videos | ✅ | Native Google Drive trigger |
| Transcribe video audio | ✅ | OpenAI Whisper action (or Zapier's built-in transcription) |
| Generate captions/hooks/hashtags with AI | ✅ | Anthropic (Claude) or ChatGPT action |
| Write drafts to Google Sheets | ✅ | Native action |
| Notify the team (Slack/email) | ✅ | Native actions |
| **Cut highlight clips from video** | ❌ | Zapier can't edit video. Claude still outputs *timestamps*, your editor cuts in CapCut/Descript — or add the OpusClip integration (see bottom) |

---

## The Zap (7 steps)

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

### Step 7 — Slack or Email notification
- "🎬 New content drafts ready for review: {filename} — [open the sheet]"

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

> Why "quote to search for" instead of timestamps? Whisper-in-Zapier returns
> plain text without timestamps, so Claude flags the exact sentence — your
> editor searches for it in CapCut/Descript (both have transcript search) and
> cuts there. If you use AssemblyAI instead, you get timestamps and can map
> them directly.

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

- This Zap uses **7 steps** → needs a **Zapier Professional plan** (multi-step Zaps + premium apps)
- Each video ≈ 1 Zap run + 1 Claude API call (a few cents) + 1 Whisper call
- A 1-hour webinar transcript ≈ ~9k words — comfortably within Claude's context

---

## Optional upgrade: auto-clipping with OpusClip

If you want actual clips cut without an editor:

1. Add a step: **OpusClip → "Create Project"** (official Zapier integration),
   passing the Drive video link
2. OpusClip auto-cuts viral-style shorts with captions and a virality score
3. Add its webhook back into a second Zap to log finished clips in your sheet

OpusClip + this Zap = fully hands-off: video in Drive → transcripts → AI copy
→ cut clips → everything in one review sheet.

---

## Quick-start checklist

- [ ] Create the Google Sheet with the columns above, tab named `Drafts`
- [ ] Get an Anthropic API key (console.anthropic.com)
- [ ] Get an OpenAI API key (for Whisper) — or use Zapier's built-in transcription
- [ ] Build the 7-step Zap as described
- [ ] Test with one short video first (under 25 MB)
- [ ] Turn on the Zap and drop videos into the folder
