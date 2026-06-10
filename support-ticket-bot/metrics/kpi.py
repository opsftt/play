"""Customer-success KPI calculations.

Pure functions over ticket dicts (as returned by store.sheet_store) so they
can be unit-tested without Slack or Google credentials.

KPIs produced:
  - volume: created / resolved / still open in the window, plus total backlog
  - speed: average & median first-response and resolution times
  - SLA: first-response and resolution compliance per priority
  - quality: CSAT average and survey response rate, escalation rate
  - mix: ticket counts per category
"""

from datetime import timedelta
from statistics import median

from timeutil import parse_ts


def _minutes_between(start, end):
    return (end - start).total_seconds() / 60.0


def _avg(values):
    return sum(values) / len(values) if values else None


def _median(values):
    return median(values) if values else None


def compute_kpis(tickets, now, window_days, first_response_sla, resolution_sla):
    """Compute the KPI snapshot for tickets created in the last window_days.

    Backlog metrics (open_total, oldest_open_days) consider ALL tickets, not
    just the window, since an old unresolved ticket is still your problem.
    """
    window_start = now - timedelta(days=window_days) if window_days else None

    created_in_window = []
    for t in tickets:
        created = parse_ts(t.get("created_at"))
        if created is None:
            continue
        t = dict(t, _created=created)
        if window_start is None or created >= window_start:
            created_in_window.append(t)

    resolved = [t for t in created_in_window if t.get("status") == "resolved"]
    open_in_window = [t for t in created_in_window if t.get("status") != "resolved"]

    # Backlog across all time
    all_open = []
    for t in tickets:
        if t.get("status") != "resolved":
            created = parse_ts(t.get("created_at"))
            if created:
                all_open.append(created)
    oldest_open_days = max(((now - c).total_seconds() / 86400 for c in all_open), default=None)

    # Speed
    first_response_minutes = []
    resolution_minutes = []
    for t in created_in_window:
        fr = parse_ts(t.get("first_response_at"))
        if fr:
            first_response_minutes.append(_minutes_between(t["_created"], fr))
        rs = parse_ts(t.get("resolved_at"))
        if rs:
            resolution_minutes.append(_minutes_between(t["_created"], rs))

    # SLA compliance per priority. Open tickets that have already blown past
    # the target count as misses; open tickets still inside the target are
    # excluded (their outcome is unknown).
    fr_sla = _sla_compliance(created_in_window, now, first_response_sla, "first_response_at")
    res_sla = _sla_compliance(created_in_window, now, resolution_sla, "resolved_at")

    # CSAT
    scores = [int(t["csat_score"]) for t in resolved if str(t.get("csat_score", "")).isdigit()]
    csat_avg = _avg(scores)
    csat_response_rate = (len(scores) / len(resolved)) if resolved else None

    # Escalations
    escalated = [t for t in created_in_window if t.get("escalated") == "yes"]

    # Category mix
    by_category = {}
    for t in created_in_window:
        cat = t.get("category") or "Uncategorized"
        by_category[cat] = by_category.get(cat, 0) + 1

    return {
        "window_days": window_days,
        "created": len(created_in_window),
        "resolved": len(resolved),
        "open_in_window": len(open_in_window),
        "open_total": len(all_open),
        "oldest_open_days": oldest_open_days,
        "avg_first_response_min": _avg(first_response_minutes),
        "median_first_response_min": _median(first_response_minutes),
        "avg_resolution_min": _avg(resolution_minutes),
        "median_resolution_min": _median(resolution_minutes),
        "first_response_sla": fr_sla,
        "resolution_sla": res_sla,
        "csat_avg": csat_avg,
        "csat_responses": len(scores),
        "csat_response_rate": csat_response_rate,
        "escalated": len(escalated),
        "escalation_rate": (len(escalated) / len(created_in_window)) if created_in_window else None,
        "by_category": dict(sorted(by_category.items(), key=lambda kv: -kv[1])),
    }


def _sla_compliance(tickets, now, sla_minutes, timestamp_field):
    """Per-priority {met, missed, rate} for the given lifecycle timestamp."""
    result = {}
    for t in tickets:
        priority = t.get("priority") or "normal"
        target = sla_minutes.get(priority)
        if target is None:
            continue
        done_at = parse_ts(t.get(timestamp_field))
        if done_at is not None:
            met = _minutes_between(t["_created"], done_at) <= target
        elif _minutes_between(t["_created"], now) > target:
            met = False  # still waiting and already past target
        else:
            continue  # still inside target, outcome unknown
        bucket = result.setdefault(priority, {"met": 0, "missed": 0})
        bucket["met" if met else "missed"] += 1
    for bucket in result.values():
        total = bucket["met"] + bucket["missed"]
        bucket["rate"] = bucket["met"] / total if total else None
    return result


def find_sla_breaches(tickets, now, first_response_sla):
    """Open tickets past their first-response SLA that haven't been alerted yet."""
    breaches = []
    for t in tickets:
        if t.get("status") != "open" or t.get("sla_breach_alerted") == "yes":
            continue
        created = parse_ts(t.get("created_at"))
        target = first_response_sla.get(t.get("priority") or "normal")
        if created is None or target is None:
            continue
        overdue = _minutes_between(created, now) - target
        if overdue > 0:
            breaches.append((t, overdue))
    return breaches


def fmt_minutes(minutes):
    """Human-friendly duration: 45m, 3.2h, 2.1d."""
    if minutes is None:
        return "–"
    if minutes < 90:
        return f"{minutes:.0f}m"
    hours = minutes / 60
    if hours < 36:
        return f"{hours:.1f}h"
    return f"{hours / 24:.1f}d"


def fmt_rate(rate):
    return "–" if rate is None else f"{rate * 100:.0f}%"
