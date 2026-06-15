# Freedom Team Trading — Social Media Bot Setup (Zapier)

**How it works:** You paste a Fathom recording link into a Google Sheet →
the Zap picks it up, grabs the transcript from Fathom, sends it to Claude for
platform-specific copy, pushes the video to OpusClip for clip cutting, and
logs everything in a Drafts tab for your team to review.

---

## Before you start — accounts you need

| Account | What it's for | Where to get it |
|---------|--------------|-----------------|
| Zapier (Professional plan) | Runs the automation | zapier.com |
| Anthropic | Claude writes the captions | console.anthropic.com → API Keys |
| Fathom | Already have this ✅ | — |
| OpusClip | Cuts the short-form clips | opus.pro |
| Google account | Sheets + Drive | Already have this ✅ |

---

## Step 1 — Set up your Google Sheets

You need **two tabs** in one Google Sheet:

### Tab 1: "Videos" (where you paste links)

Create these columns exactly:

| A | B | C | D |
|---|---|---|---|
| Fathom URL | Video Title | Video Type | Status |

- **Fathom URL** — paste the Fathom share link here
- **Video Title** — what you want it called (e.g. "June 10 Live Session")
- **Video Type** — type one of: `live_trading` / `webinar` / `testimonial` / `course`
- **Status** — leave blank; the Zap fills this in automatically

### Tab 2: "Drafts" (where content lands)

Create these columns:

| A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|
| Date | Video Title | Platform | Format | Content | Hashtags | Status |

Leave this tab empty — Zapier fills it.

---

## Step 2 — Connect Fathom to Zapier

1. In Fathom, go to **Settings → Integrations → Zapier**
2. Click **Connect** and copy your Fathom API key
3. In Zapier, when you add a Fathom step, paste that key to authenticate

---

## Step 3 — Build Zap 1 (Copy + Clips)

In Zapier, click **Create Zap**.

---

### 🔵 Step 1 of Zap — Trigger: Google Sheets "New Spreadsheet Row"

- **App:** Google Sheets
- **Event:** New Spreadsheet Row
- **Account:** connect your Google account
- **Spreadsheet:** select your sheet
- **Worksheet:** Videos
- **Test:** add a row in the sheet with a real Fathom URL to test with

---

### 🟡 Step 2 of Zap — Filter (only run when Status is blank)

- **App:** Filter by Zapier
- **Condition:** `Status` **Does not exist** (or "is empty")
- This stops the Zap from re-running on rows it already processed

---

### 🟠 Step 3 of Zap — Fathom: "Find Recording"

- **App:** Fathom
- **Event:** Find Recording
- **Recording URL:** select `Fathom URL` from Step 1
- **What this gives you:** the full transcript text + the direct video download URL

---

### 🟣 Step 4 of Zap — Anthropic: "Send Message"

- **App:** Anthropic
- **Event:** Send Message
- **Model:** `claude-sonnet-4-6`
- **Max tokens:** `4000`
- **Message (user):** paste the prompt below, then use Zapier's field picker to
  insert the dynamic values where marked

```
You are the social media strategist for Freedom Team Trading, a forex and
futures trading education brand. Tone: energetic, educational, empowering.
Never make guaranteed-profit claims.

VIDEO TITLE: [insert Video Title from Step 1]
VIDEO TYPE: [insert Video Type from Step 1]
TRANSCRIPT:
[insert Transcript from Step 3 - Fathom]

Generate the following. Separate each section with ||| on its own line,
in this exact order. Output ONLY the sections, no intro text.

1. INSTAGRAM REEL
Hook (max 10 words for the first 3 seconds of the video)
Caption (with emojis, line breaks, and a CTA, max 2200 chars)
30 hashtags
Best clip moment: CLIP: "[exact quote from transcript]" — why it works

|||

2. INSTAGRAM CAROUSEL
Slide 1 headline
Slide 2 text
Slide 3 text
Slide 4 text
Slide 5 CTA
Caption for the post
30 hashtags

|||

3. X (TWITTER) TWEET
Single tweet under 280 characters with a scroll-stopping hook

|||

4. X (TWITTER) THREAD
1/ Opening tweet that creates curiosity
2/ Key insight
3/ Key insight
4/ Key insight
5/ Closing tweet with CTA and link placeholder

|||

5. TIKTOK
Spoken hook line (first 3 seconds, creates curiosity or shock)
Caption with emojis and CTA
20 hashtags
Best clip moment: CLIP: "[exact quote from transcript]" — why it works
3 b-roll ideas

|||

6. YOUTUBE SHORT
Title (under 60 characters)
Best clip moment: CLIP: "[exact quote from transcript]" — why it works

|||

7. YOUTUBE LONG-FORM
SEO title (under 70 characters)
Full description (include chapter timestamps, 2 link placeholders, and keywords)
8 tags separated by commas
Thumbnail text (max 6 bold words)
```

---

### 🔵 Step 5 of Zap — Formatter: "Text → Split Text"

- **App:** Formatter by Zapier
- **Event:** Text → Split Text
- **Input:** select the Claude response text from Step 4
- **Separator:** `|||`
- **Segment Index:** All (this gives you 7 separate fields: Output 1 through Output 7)

---

### 🟢 Step 6 of Zap — Google Sheets: "Create Multiple Spreadsheet Rows"

- **App:** Google Sheets
- **Event:** Create Spreadsheet Row *(repeat this step 7 times, once per platform — or use "Create Multiple Rows" if your Zapier plan supports it)*
- **Spreadsheet:** your sheet
- **Worksheet:** Drafts

Map the rows like this:

| Row | Date | Video Title | Platform | Format | Content | Hashtags | Status |
|-----|------|-------------|----------|--------|---------|----------|--------|
| 1 | Now | Step 1 title | Instagram | Reel | Output 1 | (in Output 1) | DRAFT |
| 2 | Now | Step 1 title | Instagram | Carousel | Output 2 | (in Output 2) | DRAFT |
| 3 | Now | Step 1 title | X | Tweet | Output 3 | — | DRAFT |
| 4 | Now | Step 1 title | X | Thread | Output 4 | — | DRAFT |
| 5 | Now | Step 1 title | TikTok | Video | Output 5 | (in Output 5) | DRAFT |
| 6 | Now | Step 1 title | YouTube | Short | Output 6 | — | DRAFT |
| 7 | Now | Step 1 title | YouTube | Long-form | Output 7 | (in Output 7) | DRAFT |

---

### 🟠 Step 7 of Zap — OpusClip: "Create Project"

- **App:** OpusClip
- **Event:** Create Clip Project (or equivalent — check current OpusClip action name in Zapier)
- **Video URL:** select the **video download URL** from Fathom (Step 3)
- **Clip length settings:** enable both `< 60 seconds` and `< 90 seconds`
- **Title:** select Video Title from Step 1

> ⚠️ **Test this step first in isolation** — paste the Fathom video URL into
> OpusClip manually to confirm it accepts it before relying on the Zap.
> If Fathom's URL requires login, download the video to Drive and pass the
> Drive URL instead.

---

### ⚪ Step 8 of Zap — Google Sheets: "Update Spreadsheet Row"

- Update the original row in the **Videos** tab
- **Status** column → set to `PROCESSING`
- This prevents the filter in Step 2 from re-triggering the same row

---

### 🔔 Step 9 of Zap — Slack or Gmail: notify your team

- **Message:** `🎬 Content drafts ready for *[Video Title]*. Open the Drafts tab to review → [paste your sheet URL here]`

---

## Build Zap 2 — Log finished clips (3 steps)

OpusClip takes a few minutes to render. This second Zap logs clips when done.

**Step 1 — Trigger: OpusClip "New Clip Ready" (or "Project Completed")**

**Step 2 — Google Sheets: "Create Spreadsheet Row"**
- Worksheet: Drafts
- Map: clip link, duration, virality score, Status = `CLIP READY`

**Step 3 — Slack/Email**
- `✂️ [n] clips ready for [video title] → [OpusClip link]`

---

## How your team uses the Drafts tab

1. A new Fathom recording finishes → you paste the link into the **Videos** tab
2. Within ~5 minutes, the **Drafts** tab fills with 7 rows of copy (one per format)
3. Within ~15 minutes (webinars longer), clips appear as `CLIP READY` rows
4. Your team reads each row, changes **Status** from `DRAFT` → `APPROVED` or `SKIP`
5. Pair each approved caption with the matching OpusClip clip and post (or push to Buffer/Later)

---

## Quick-start checklist

- [ ] Create the two-tab Google Sheet (Videos + Drafts) with the columns above
- [ ] Get Anthropic API key → connect to Zapier
- [ ] Connect Fathom to Zapier (Settings → Integrations → Zapier in Fathom)
- [ ] Connect OpusClip to Zapier
- [ ] Build Zap 1 (9 steps) — test each step before turning on
- [ ] Build Zap 2 (3 steps)
- [ ] Do a full end-to-end test with one short Fathom recording
- [ ] Turn both Zaps on 🚀
