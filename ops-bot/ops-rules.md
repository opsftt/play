# ops-rules

> **This is the Ops Bot's single source of truth for rates, roster, aliases, KPI definitions, tolerances and approvers.**
> The Ops Bot reads this doc at the start of **every** check and cites its version/last-updated date in each report.
>
> **Hard rule: no guessing.** Any value still marked `<< FILL IN >>` is NOT yet a rule. If a check needs a value that is missing or still a placeholder, the bot must STOP and ask a human — it must not infer the value from a past run or from what seems typical.
>
> **Status: DRAFT SCAFFOLD.** Section headings and field names are in place; FTT-specific values are not yet filled in. Do not run a live check against this doc until the sections a check depends on are complete.

---

## 0. Document metadata

| Field | Value |
|---|---|
| Version | `0.1-draft` |
| Last updated | `2026-11-19` |
| Updated by | `<< FILL IN: name >>` |
| Status | DRAFT — not yet ready for live runs |

**Versioning policy:** When a pay plan or KPI definition changes, bump the version, record the **effective date**, and keep the previous version in the Change log below so past periods can still be re-checked against the rules that were in force then.

### Change log
| Version | Effective date | Change | By |
|---|---|---|---|
| 0.1-draft | 2026-11-19 | Initial scaffold created | Ops Bot |

---

## 1. Pay periods & calendar

- **Commission pay cadence:** semi-monthly. Period 1 = `<< FILL IN: e.g. 1st–15th >>`, Period 2 = `<< FILL IN: e.g. 16th–end of month >>`.
- **How a deal is assigned to a period:** `<< FILL IN: by cash-collected date? deal-close date? which date column in the EOM Tracker? >>`
- **Pay dates:** Period 1 paid on `<< FILL IN >>`, Period 2 paid on `<< FILL IN >>`.
- **Items paid on a different cadence** (so they are NOT folded into the semi-monthly run): `<< FILL IN: e.g. monthly overrides, tier bonuses — and the date each is paid >>`

---

## 2. Active roster

> Start every payroll build from THIS roster, not from the deal rows. People on a flat base or an override are owed pay even in periods where they appear on no deal; a deal-row-driven build silently drops them.

| Name (canonical) | Role(s) | Pay plan (ref §5) | Base/flat? | Active from | Active to | Notes |
|---|---|---|---|---|---|---|
| `<< FILL IN >>` | closer / setter / DM setter / coach | | | | | |

Roles in use: closer, setter, DM setter, coach `<< confirm/extend >>`.

---

## 3. Name aliases

> The same person appears under different names across the EOM Tracker, Close, and the EOD forms. Match ONLY through this table. An unknown name goes to "could not check" for a human to confirm — never fuzzy-match on pay.

| Canonical name | EOM Tracker name(s) | Close name(s) | EOD form name(s) | Slack handle | Notes |
|---|---|---|---|---|---|
| `<< FILL IN >>` | | | | | |

---

## 4. Placeholders & special values

How to treat non-person values that appear in attribution columns:

| Value in a role column | Meaning | Treatment |
|---|---|---|
| `No Setter` | Legitimately no setter involved | Valid — do NOT flag |
| `Old Rep` | Unattributed | Flag; leave OUT of commission |
| `Old Setter` | Unattributed | Flag; leave OUT of commission |
| `No Closer` | Unattributed | Flag; leave OUT of commission |
| AI SMS bot / automated setter (name: `<< FILL IN exact string(s) >>`) | Automated setter, not a payable person | Flag; compute NO fee |
| `<< add any other FTT-specific placeholders >>` | | |

---

## 5. Commission & pay plans

> If any rate below is blank, the bot stops and asks. Rates are not transferable between roles or periods.

### 5.1 Closer
- Commission structure: `<< FILL IN: % of cash collected? flat per deal? tiered? >>`
- Rate(s): `<< FILL IN >>`
- Basis — which cash figure the % applies to: `<< FILL IN: EOM "cash collected"? net of fees? >>`

### 5.2 Setter
- Structure / rate: `<< FILL IN >>`
- Basis: `<< FILL IN >>`

### 5.3 DM setter
- Structure / rate: `<< FILL IN >>`
- Basis: `<< FILL IN >>`

### 5.4 Bases, flat pay & overrides
- Who is on a base/draw, and the amount: `<< FILL IN (cross-ref roster §2) >>`
- Override structure (e.g. a manager's % of team cash): `<< FILL IN: who, rate, on what base >>`

### 5.5 Tier bonuses
- Thresholds and amounts: `<< FILL IN >>`
- Measured over what window (per period? monthly?): `<< FILL IN >>`
- Pay date (see §1): `<< FILL IN >>`

### 5.6 Dual-role rule
> Someone who is both closer AND setter on one deal is ONE deal for that person. Count cash and deals once per person however many role columns match.
- When one person fills two roles on a deal, they are paid: `<< FILL IN: both commissions? the higher one only? closer rate only? >>`

### 5.7 Payment plan vs new-deal cash
> Some rules treat these differently; do not assume one filter applies everywhere.
- Closer: payment-plan installments treated `<< FILL IN: same as / differently from >>` new-deal cash — detail: `<< FILL IN >>`
- Setter: `<< FILL IN >>`
- DM setter: `<< FILL IN >>`

### 5.8 Financed deals & deposits
> On a financed deal, EOM cash = Freedom Financing **Advanced Amount** + any holding deposit / down payment the client paid.
- Where to confirm a deposit: a card/Whop payment in Slack #successful-payment near the deal date, or an "NR HD" row for the client in this or last month's EOM tab.
- A deposit equal to the (EOM cash − Advanced Amount) difference means the EOM figure is right. If that deposit ALSO has its own EOM row → flag a double count. If there is NO deposit → the EOM figure is wrong.
- FTT-specific notes / exceptions: `<< FILL IN if any >>`

### 5.9 Pay timing
- Confirm which earnings land in the semi-monthly run vs a separate monthly/bonus run (cross-ref §1): `<< FILL IN >>`

### 5.10 Clawbacks
- A deal counted as cash whose Close status is not "won" (churned, still booked) is a possible clawback → flag for the approver.
- Clawback policy (if/when pay is reversed): `<< FILL IN >>`

---

## 6. KPI definitions

### 6.1 Total cash
- Components that sum to "total cash": `<< FILL IN: list each component and its source >>`
- Compared against: the dashboard figure AND the EOM Tracker's `TOTAL CC`.

### 6.2 Excluded items
- Items excluded from total cash (must be excluded on BOTH sides): `<< FILL IN: e.g. low-ticket downsells — list them >>`

### 6.3 ROAS
- Definition: total cash ÷ HYROS ad spend for the same window.
- Any adjustments to spend or cash before the ratio: `<< FILL IN if any >>`

---

## 7. Tolerances

| Comparison | Pass/fail tolerance |
|---|---|
| Per-person pay | `<< FILL IN: e.g. $0.00 exact, or ±$X >>` |
| Payroll grand total | `<< FILL IN >>` |
| KPI total cash tie-out | `<< FILL IN >>` |
| ROAS | `<< FILL IN >>` |

Anything outside tolerance is a MISMATCH, not a pass.

---

## 8. Approvers

> A proposed correction goes to a named approver who is NOT the person whose work is being checked.

| Area | Approver (name) | Notes |
|---|---|---|
| Commission payroll | `<< FILL IN >>` | |
| KPI / financials | `<< FILL IN >>` | |
| Attribution (EOM Tracker edits) | `<< FILL IN >>` | |

- Private ops channel for per-person pay detail: `<< FILL IN channel >>` (per-person pay NEVER goes to a public channel).

---

## 9. Coach pay (new check — TBD)

No FTT-specific rules yet. Results need a closer human look until this section is filled in and the check has run for at least two cycles with a human reviewing every flag.
- Structure / rate: `<< FILL IN >>`
- Basis: `<< FILL IN >>`

---

## 10. Source locations

Exact sheets/tabs the checks pull from (so the bot pulls fresh from the right range, not a screenshot):

| Source | File / sheet name | Tab(s) | Notes |
|---|---|---|---|
| Deals / cash / attribution | EOM TRACKER - Version 2.0 | the month's tab | main source of truth |
| Rep self-reported cash | FTT EOD FORM (Responses) | Closer Dashboard, Setter Dashboard | dashboards recalc from manual date cells — confirm they cover the period |
| Active roster | `<< FILL IN sheet >>` | EOD Roster | |
| Human pay run being checked | Payroll Checker | the pay period's tab | |
| Financing cross-check | Freedom Financing sheet | `<< FILL IN tab >>` | same underlying data as EOM — cross-check only, do not add as extra deals |
| Payment existence | Slack | #successful-payment | |
| CRM | Close | — | attribution cross-check only; never overrides EOM attribution in the math |
| Ad spend | HYROS | — | for ROAS |
