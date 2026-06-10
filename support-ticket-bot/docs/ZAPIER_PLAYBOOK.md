# Zapier Playbook: Whop + Notion + Sheets around the ticket bot

The bot handles the Slack ↔ Google Sheets core. These optional Zaps wire in
the rest of your stack. None of them are required to run the bot.

## 1. Whop churn-risk → auto-ticket (highest ROI)

Catch revenue problems before the student even messages you.

- **Trigger:** Whop → *Payment Failed* (and a second Zap for *Membership
  Canceled*).
- **Action:** Google Sheets → *Create Spreadsheet Row* in the `Tickets` tab:
  - `ticket_id`: `ZAP-{{zap_meta_id}}`
  - `created_at`: `{{zap_meta_human_now}}` formatted `YYYY-MM-DD HH:mm:ss`
    (set your Zap timezone to match the bot's `TIMEZONE`)
  - `student_id`: leave blank (or map Slack user ID if you store it in Whop
    metadata), `student_name`: Whop username/email
  - `source`: `whop`, `category`: `Billing & Payments`, `priority`: `high`,
    `status`: `open`
  - `subject`: `Payment failed — {{member_email}}`
- **Action 2:** Slack → *Send Channel Message* to your triage channel so the
  team sees it immediately (Zap-created rows don't get a bot card).

These rows flow into `/kpis` and the weekly digest automatically — they're
just sheet rows.

## 2. Whop new member → proactive welcome touchpoint

- **Trigger:** Whop → *New Membership*.
- **Action:** Slack → *Send Direct Message*: welcome them, point at the
  getting-started module, and include the pinned support instructions
  ("`/ticket` or react 🎫"). Proactive onboarding measurably cuts
  "Course Access / Whop" ticket volume — watch that category drop in the
  digest after you turn this on.

## 3. Weekly KPIs → Notion dashboard

Keep leadership reporting in Notion without copy-paste.

- **Trigger:** Schedule by Zapier → *Every Week* (Monday, after the bot's
  digest time).
- **Action 1:** Google Sheets → *Lookup/Get Many Spreadsheet Rows* from
  `Tickets` (or simpler: maintain a `KPI_Snapshots` tab — see below).
- **Action 2:** Notion → *Create Page* in your "CS Weekly Reports" database
  with the numbers as properties (created, resolved, backlog, median FRT,
  CSAT). Notion database = trend charts over weeks for free.

Tip: if mapping raw ticket rows in Zapier gets fiddly, add a `KPI_Snapshots`
tab in the same spreadsheet with `=COUNTIFS(...)` / `=MEDIAN(...)` formulas
over the `Tickets` tab, and have the Zap read that single row instead.

## 4. Low CSAT → instant alert

- **Trigger:** Google Sheets → *New or Updated Spreadsheet Row* on `Tickets`,
  trigger column = `csat_score`.
- **Filter:** `csat_score` less than 3.
- **Action:** Slack → DM the ops manager with ticket id, subject, resolution
  note, and assigned agent. A same-day personal follow-up after a bad rating
  is the cheapest retention play you have.
