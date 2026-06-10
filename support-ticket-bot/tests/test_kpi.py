import os
import unittest
from datetime import datetime

# Minimal env so config imports without a real .env
os.environ.setdefault("SLACK_BOT_TOKEN", "xoxb-test")
os.environ.setdefault("SLACK_APP_TOKEN", "xapp-test")
os.environ.setdefault("TRIAGE_CHANNEL", "C000")
os.environ.setdefault("TICKETS_SHEET_ID", "sheet-test")

import pytz  # noqa: E402

from metrics import kpi  # noqa: E402

TZ = pytz.timezone("America/New_York")
NOW = TZ.localize(datetime(2026, 6, 10, 12, 0, 0))

FR_SLA = {"urgent": 60, "high": 240, "normal": 1440, "low": 2880}
RES_SLA = {"urgent": 240, "high": 1440, "normal": 2880, "low": 7200}


def ticket(**kw):
    base = {
        "ticket_id": "FTT-1001",
        "created_at": "2026-06-10 09:00:00",
        "category": "Billing & Payments",
        "priority": "normal",
        "status": "open",
        "first_response_at": "",
        "resolved_at": "",
        "csat_score": "",
        "escalated": "",
        "sla_breach_alerted": "",
    }
    base.update(kw)
    return base


class ComputeKpisTest(unittest.TestCase):
    def compute(self, tickets, window_days=7):
        return kpi.compute_kpis(tickets, NOW, window_days, FR_SLA, RES_SLA)

    def test_empty(self):
        k = self.compute([])
        self.assertEqual(k["created"], 0)
        self.assertIsNone(k["avg_first_response_min"])
        self.assertIsNone(k["csat_avg"])

    def test_volume_and_window(self):
        tickets = [
            ticket(),
            ticket(created_at="2026-05-01 09:00:00"),  # outside 7d window
        ]
        k = self.compute(tickets)
        self.assertEqual(k["created"], 1)
        self.assertEqual(k["open_total"], 2)  # backlog counts everything

    def test_response_and_resolution_times(self):
        t = ticket(
            status="resolved",
            first_response_at="2026-06-10 09:30:00",   # 30 min
            resolved_at="2026-06-10 11:00:00",          # 120 min
        )
        k = self.compute([t])
        self.assertAlmostEqual(k["avg_first_response_min"], 30)
        self.assertAlmostEqual(k["median_resolution_min"], 120)

    def test_sla_met_and_missed(self):
        met = ticket(priority="urgent", first_response_at="2026-06-10 09:30:00",
                     status="in_progress")
        # urgent created 3h ago, never claimed → already past 60m target
        missed = ticket(ticket_id="FTT-1002", priority="urgent")
        # normal created 1h ago, unclaimed but inside 24h target → excluded
        pending = ticket(ticket_id="FTT-1003", priority="normal",
                         created_at="2026-06-10 11:00:00")
        k = self.compute([met, missed, pending])
        self.assertEqual(k["first_response_sla"]["urgent"], {"met": 1, "missed": 1, "rate": 0.5})
        self.assertNotIn("normal", k["first_response_sla"])

    def test_csat(self):
        tickets = [
            ticket(status="resolved", resolved_at="2026-06-10 10:00:00", csat_score="5"),
            ticket(ticket_id="FTT-1002", status="resolved",
                   resolved_at="2026-06-10 10:00:00", csat_score="3"),
            ticket(ticket_id="FTT-1003", status="resolved",
                   resolved_at="2026-06-10 10:00:00"),  # no survey response
        ]
        k = self.compute(tickets)
        self.assertAlmostEqual(k["csat_avg"], 4.0)
        self.assertAlmostEqual(k["csat_response_rate"], 2 / 3)

    def test_escalation_rate_and_categories(self):
        tickets = [
            ticket(escalated="yes"),
            ticket(ticket_id="FTT-1002", category="Course Access / Whop"),
        ]
        k = self.compute(tickets)
        self.assertEqual(k["escalated"], 1)
        self.assertAlmostEqual(k["escalation_rate"], 0.5)
        self.assertEqual(k["by_category"]["Billing & Payments"], 1)


class SlaBreachTest(unittest.TestCase):
    def test_finds_unalerted_open_breaches_only(self):
        breach = ticket(priority="urgent")  # 3h unclaimed vs 60m target
        already_alerted = ticket(ticket_id="FTT-1002", priority="urgent",
                                 sla_breach_alerted="yes")
        claimed = ticket(ticket_id="FTT-1003", priority="urgent",
                         status="in_progress",
                         first_response_at="2026-06-10 09:10:00")
        breaches = kpi.find_sla_breaches([breach, already_alerted, claimed], NOW, FR_SLA)
        self.assertEqual([t["ticket_id"] for t, _ in breaches], ["FTT-1001"])
        self.assertAlmostEqual(breaches[0][1], 120)  # 180m elapsed - 60m target


class FormatTest(unittest.TestCase):
    def test_fmt_minutes(self):
        self.assertEqual(kpi.fmt_minutes(None), "–")
        self.assertEqual(kpi.fmt_minutes(45), "45m")
        self.assertEqual(kpi.fmt_minutes(192), "3.2h")
        self.assertEqual(kpi.fmt_minutes(3024), "2.1d")


if __name__ == "__main__":
    unittest.main()
