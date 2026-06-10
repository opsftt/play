# Customer Success KPI Definitions

How each KPI is calculated, why it matters for a 1000+ student trading
education business, and what to do when it moves the wrong way. All KPIs are
computed from the `Tickets` Google Sheet by `metrics/kpi.py` and surfaced via
`/kpis` and the weekly digest.

Timestamps are recorded in your configured `TIMEZONE`. "Window" means tickets
*created* in the last N days (default 7).

---

## Volume

**Created / Resolved / Open backlog.** Backlog counts *all* unresolved
tickets regardless of window, with the age of the oldest one.

- **Why:** volume per 100 students is your support load signal. A spike in
  created tickets usually traces to a single event (Whop outage, course
  launch, billing run) — check the category mix to find it.
- **Red flag:** resolved consistently < created → backlog grows → response
  times will degrade two weeks later. Staff up or cut root causes.

## First Response Time (FRT)

**Created → claimed**, median and average. Claiming the ticket in Slack is
the measurement point; resolving an unclaimed ticket backfills it.

- **Why:** for students, speed of first human contact drives perceived
  quality more than resolution speed. Median is the honest number; a big
  average/median gap means a few tickets are rotting unclaimed.
- **Target:** < 4h median during business hours.

## Resolution Time

**Created → resolved**, median and average.

- **Why:** the end-to-end experience. Watch it per category — "Course
  Access / Whop" should resolve in minutes; "Trading Platform / Tools" may
  legitimately take longer.
- **Target:** < 24h median.

## SLA Compliance (first response & resolution, per priority)

% of tickets handled within the targets in `config.py`. Open tickets already
past their target count as **misses**; open tickets still inside the target
are excluded (outcome unknown), so the number never flatters you.

| Priority | First response | Resolution |
|---|---|---|
| urgent | 1h | 4h |
| high | 4h | 24h |
| normal | 24h | 48h |
| low | 48h | 5d |

- **Target:** ≥ 90% first response, ≥ 85% resolution.
- The bot also pings the triage channel in real time when an open ticket
  blows its first-response SLA, so misses get rescued instead of just counted.

## CSAT (Customer Satisfaction)

Average of the 1–5 star survey DM'd after resolution, plus **response rate**
(scores ÷ resolved tickets).

- **Why:** the only KPI students score themselves. Read every 1–2 star next
  to its resolution note — it's free coaching material.
- **Target:** ≥ 4.5 average. Response rates of 25–40% are normal; below that,
  the survey is arriving too late or feeling impersonal.

## Escalation Rate

% of window tickets escalated via the ⚠️ button.

- **Why:** measures how often front-line support can't finish the job —
  a proxy for documentation gaps, missing permissions, or training needs.
- **Target:** < 10%. Rising rate → audit what's escalating and write the
  missing playbook.

## Category Mix

Ticket counts per category, sorted.

- **Why:** this is your *root-cause elimination* list. If "Course Access /
  Whop" is 40% of volume, one onboarding video or a Whop settings fix can
  delete 40% of your support load. Review monthly; the best support ticket
  is the one that never gets opened.

---

## Reviewing cadence

- **Daily (2 min):** open backlog + SLA breach pings in the triage channel.
- **Weekly (digest):** trends vs. last week; read low CSAT comments.
- **Monthly:** category mix → pick ONE root cause to eliminate; re-tune SLA
  targets in `config.py` if you're consistently above 95% (tighten) or
  below 80% (they're fiction — fix staffing or loosen honestly).
