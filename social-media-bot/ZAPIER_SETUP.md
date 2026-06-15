# Zapier-Based Social Media Content Bot (No-Code)

Full no-code content pipeline. A new row in your Fathom tracking sheet (or a
new Fathom recording) triggers everything: transcript → AI copy → clip cutting
→ draft review sheet, with **no manual transcription step needed**.

---

## The full stack

| Capability | Tool | Notes |
|------------|------|-------|
| Detect new content to process | Zapier | Google Sheets trigger (new row with Fathom link) |
| Fetch transcript | Fathom → Zapier | Fathom's Zapier action returns the full transcript — no Whisper needed |
| Generate captions/hooks/hashtags with AI | Zapier → Claude | Anthropic action (claude-sonnet-4-6) |
| Cut highlight clips with captions | OpusClip | Official Zapier integration — auto-cuts vertical clips with burned-in captions and a virality score |
| Write drafts to Google Sheets | Zapier | Writes to a separate Drafts tab |
| Notify the team (Slack/email) | Zapier | Native actions |

---

## Trigger option A — Google Sheet (recommended if you manage videos in a sheet)

**Your sheet needs these columns:**

| Column | What you fill in | Used by |
|--------|-----------------|---------|
| Fathom Recording URL | Paste the Fathom share link | Zapier fetches transcript + video URL |
| Video Title | e.g. "June 10 Live Session" | Claude prompt, Sheet labels |
| Video Type | live_trading / webinar / testimonial / course | Tailors the Claude prompt |
| Status | Leave blank — Zapier fills this | Bot sets to `PROCESSING` then `DONE` |

**Trigger setup in Zapier:**
- App: **Google Sheets**
- Event: **New Spreadsheet Row** (or "New or Updated Row" filtered on Status = blank)
- Sheet: your tracking sheet, the tab where you paste Fathom links

---

## Trigger option B — Fathom directly (simplest, fully automatic)

Skip the tracking sheet entirely. Fathom fires the Zap the moment a recording
is ready.

- App: **Fathom**
- Event: **New Recording**
- Zapier gets the transcript AND the video download URL automatically — no
  extra "fetch" step needed

Downside: you lose the manual control of the tracking sheet (every Fathom
recording triggers the bot, including internal calls you may not want posted).
A Zapier **Filter** step (only continue if meeting title contains "trading" /
"webinar" / "session") solves this.

---

## Zap 1 — Copy generation (6 steps)

### Step 1 — Trigger
*(Choose Option A or B above)*

### Step 2 — Fathom: "Find Recording" *(Option A only — skip for Option B)*
- Search by: **Recording URL** (from the sheet column)
- This returns the full transcript text and the direct video download URL
- Mark the tracking sheet row Status = `PROCESSING` here with a Sheets update step

### Step 3 — Anthropic (Claude): "Send Message"
- Model: `claude-sonnet-4-6`
- Paste the prompt template below, mapping in:
  - Transcript → from Fathom (Step 2 or Step 1 depending on option)
  - Video Title → from your sheet / Fathom meeting title
  - Video Type → from your sheet column (or let Claude detect it)

### Step 4 — Formatter: "Text → Split Text"
- Split on `|||`
- This turns Claude's response into 7 separate fields (one per platform format)

### Step 5 — Google Sheets: "Create Multiple Spreadsheet Rows" (Drafts tab)
- Create one row per platform format with caption, hook, hashtags, clip moment
- Status = `DRAFT`

### Step 6 — OpusClip: "Create Project"
- Video URL: the **direct download URL** from Fathom (NOT the share page link)
- Clip length: set presets for <60s and <90s to cover Shorts, Reels, and TikTok
- ⚠️ This only works if Fathom returns a direct `.mp4` URL in Zapier. Test this
  first with one recording — if Fathom's URL is a webpage, see the note below.

> **OpusClip + Fathom URL note:** Fathom's Zapier integration returns a
> `video_url` field that is a direct downloadable link (not the browser share
> page). OpusClip accepts this. If your test shows it's redirecting to a login
> page, the workaround is to download the Fathom video to Google Drive first
> (Fathom has a native Drive export), then pass the Drive URL to OpusClip — one
> extra step but it's reliable.

### Step 7 — Slack/Email + update tracking sheet
- Message: "🎬 Drafts ready for *{Video Title}* — [open sheet]"
- Update the tracking sheet row Status → `DONE`

---

## Zap 2 — Log finished clips (3 steps)

OpusClip takes a few minutes to render, so a second Zap logs results:

1. **Trigger: OpusClip → "Project Completed"**
2. **Google Sheets → "Create Spreadsheet Row(s)"** — one row per clip with
   clip link, duration, and virality score, Status = `CLIP READY`
3. **Slack/Email** — "✂️ {n} clips ready for *{video title}*"

---

## The Claude prompt (paste into Step 3)

```
You are the social media strategist for Freedom Team Trading, a forex and
futures trading education brand. Tone: energetic, educational, empowering.
Never make guaranteed-profit claims.

VIDEO TITLE: {{Video Title}}
VIDEO TYPE: {{Video Type}}
TRANSCRIPT:
{{Fathom Transcript}}

Generate the following, with each section separated by exactly "|||" on
its own line, in this exact order:

1. INSTAGRAM REEL — hook (max 10 words), caption (with emojis + CTA), 30
   hashtags, and the best 30–60 second clip moment as:
   CLIP: "[exact quote from transcript to find]" — why it works
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

Output ONLY the 7 sections separated by |||. No preamble.
```

> **CLIP quotes tip:** Claude picks exact phrases from the Fathom transcript.
> Compare these to what OpusClip auto-selects. When they agree, that clip is
> almost always your strongest post. When they differ, both are worth testing.

---

## Drafts tab — Google Sheet columns

| Column | Source |
|--------|--------|
| Date | Zap run timestamp |
| Video Title | From tracking sheet / Fathom meeting title |
| Video Type | From tracking sheet / Claude detection |
| Platform | Static per row (Instagram, X, TikTok, YouTube) |
| Format | Reel / Carousel / Tweet / Thread / TikTok / Short / Long-form |
| Content | Split output from Step 4 |
| Status | `DRAFT` → team changes to `APPROVED` or `SKIP` |

---

## Quick-start checklist

- [ ] Set up your tracking sheet (columns above) or decide to use Fathom trigger directly
- [ ] Get an Anthropic API key — console.anthropic.com
- [ ] Connect Fathom to Zapier (Settings → Integrations in Fathom)
- [ ] Connect OpusClip to Zapier
- [ ] Build Zap 1 (6–7 steps)
- [ ] Build Zap 2 (clip logger, 3 steps)
- [ ] Test with one short Fathom recording
- [ ] Check that Fathom's video URL works directly in OpusClip (see note in Step 6)
- [ ] Turn on both Zaps

**End-to-end time from recording to draft sheet: ~5 minutes for short videos,
~15 minutes for long webinars (OpusClip render time is the variable).**
