# FTT Support Ticket Bot

A Slack-native ticketing system + customer success KPI engine for Freedom Team
Trading. Students open tickets in the Slack community they already live in,
your team triages from a single channel, and every event lands in your
existing Google Sheet so you can measure (and improve) customer success
operations.

```
 Student                          Support team                    Ops/leadership
 ───────                          ────────────                    ──────────────
 /ticket  ──┐
 🎫 react ──┼─▶ ticket card in #support-tickets
            │     [👋 Claim] [✅ Resolve] [⚠️ Escalate]
            │            │
            │            ▼
            │   Google Sheet "Tickets" (source of truth)
            │            │
 CSAT ⭐⭐⭐⭐⭐ ◀──────────┤
 survey DM               ├──▶ /kpis report (on demand)
                         ├──▶ 📊 weekly digest (Mon 9am)
                         └──▶ 🚨 SLA breach alerts (every 30 min)
```

## What students see

- **`/ticket`** anywhere in Slack opens a modal: subject, category, urgency,
  details. They get a DM confirmation with their ticket number.
- **React with 🎫** on any message (theirs or one you spot in the community)
  to turn it into a ticket without making them re-type anything.
- DM updates when their ticket is claimed and when it's resolved.
- A **1–5 star CSAT survey** DM after resolution.

## What your team sees

- Every ticket posts a card to your triage channel with **Claim / Resolve /
  Escalate** buttons. Claiming timestamps "first response"; resolving asks for
  a resolution summary (which is sent to the student).
- **Escalate** pings `ESCALATION_MENTION` in the ticket thread.
- **SLA breach alerts**: every 30 minutes the bot scans open tickets and pings
  the triage channel once per ticket that has blown its first-response SLA.
- **`/kpis [days]`** (default 7) — on-demand KPI snapshot, visible only to you.
- **Weekly digest** every Monday 9am in your leadership channel.

## KPIs measured

| KPI | Definition | Suggested target |
|---|---|---|
| Ticket volume | Created / resolved / open backlog in window | Watch trend vs. student count |
| First response time | Created → claimed (median & avg) | < 4h median |
| Resolution time | Created → resolved (median & avg) | < 24h median |
| First-response SLA | % of tickets claimed within priority target | ≥ 90% |
| Resolution SLA | % resolved within priority target | ≥ 85% |
| CSAT | Avg of post-resolution 1–5 survey + response rate | ≥ 4.5, ≥ 30% response |
| Escalation rate | % of tickets escalated | < 10% |
| Category mix | Tickets per category | Spot recurring problems → fix root cause |

Full definitions, formulas, and how to act on each: [docs/KPI_DEFINITIONS.md](docs/KPI_DEFINITIONS.md).

SLA targets per priority are in [config.py](config.py)
(`FIRST_RESPONSE_SLA_MINUTES`, `RESOLUTION_SLA_MINUTES`) — tune them to your
team's reality, then hold the line.

## Setup (~20 minutes)

### 1. Create the Slack app

1. Go to https://api.slack.com/apps → **Create New App** → **From a manifest**
   → pick your workspace → paste [slack_app_manifest.yml](slack_app_manifest.yml).
2. **Basic Information → App-Level Tokens** → generate a token with the
   `connections:write` scope → this is your `SLACK_APP_TOKEN` (xapp-...).
3. **Install App** to the workspace → copy the **Bot User OAuth Token**
   (xoxb-...) → this is your `SLACK_BOT_TOKEN`.
4. Create (or pick) your triage channel, e.g. `#support-tickets`, and invite
   the bot: `/invite @FTT Support`. Copy the channel ID (channel details →
   bottom of the About tab).
5. Also `/invite` the bot to every community channel where the 🎫 reaction
   should work — Slack only delivers reaction events from channels the bot
   has joined. (`/ticket` works everywhere regardless.)

### 2. Google Sheet

1. Reuse the service account from `social-media-bot` (or create one in Google
   Cloud Console → IAM → Service Accounts → key as JSON) and put the JSON at
   `credentials/google_service_account.json`.
2. Create a Google Sheet (or use a tab in your existing tracking sheet's
   spreadsheet) and **share it with the service account email as Editor**.
3. Copy the sheet ID from the URL into `TICKETS_SHEET_ID`. The bot creates
   the `Tickets` worksheet and headers automatically on first run.

### 3. Run it

```bash
cd support-ticket-bot
cp .env.example .env   # fill in tokens, channel IDs, sheet ID
pip install -r requirements.txt
python main.py
```

Run it on any always-on box (the same place `social-media-bot` runs is fine —
Socket Mode means no public URL, port, or webhook config). For production,
wrap it in systemd/pm2/Docker so it restarts on failure.

### 4. Tell your students

Pin a message in your community channels:

> Need help? Type `/ticket` anywhere, or react to any message with 🎫 and
> our team will take it from there. You'll get DM updates the whole way.

## Tests

```bash
python -m unittest discover -s tests
```

## Extending with the rest of your stack

- **Whop**: use Zapier's Whop triggers to auto-create tickets for churn-risk
  events (failed payment, cancellation) — see
  [docs/ZAPIER_PLAYBOOK.md](docs/ZAPIER_PLAYBOOK.md).
- **Notion**: sync the weekly KPI snapshot into a Notion dashboard page via
  Zapier, same doc.
- **Google Sheet**: the `Tickets` tab is plain rows — add your own pivot
  tables/charts tab for visuals; the bot never touches other tabs.
