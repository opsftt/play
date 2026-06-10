"""Scheduled jobs: weekly KPI digest and SLA breach alerts."""

import logging
from datetime import datetime

import pytz

import config
from bot import views
from metrics import kpi
from store import sheet_store

log = logging.getLogger(__name__)


def post_weekly_digest(client):
    tickets = sheet_store.get_all_tickets()
    now = datetime.now(pytz.timezone(config.TIMEZONE))
    kpis = kpi.compute_kpis(
        tickets, now, 7,
        config.FIRST_RESPONSE_SLA_MINUTES, config.RESOLUTION_SLA_MINUTES,
    )
    client.chat_postMessage(
        channel=config.DIGEST_CHANNEL,
        text="Weekly customer success KPI digest",
        blocks=views.kpi_blocks(kpis, "📊 Weekly Customer Success Digest"),
    )
    log.info("posted weekly digest")


def check_sla_breaches(client):
    """Ping the triage channel once per ticket that blows its first-response SLA."""
    tickets = sheet_store.get_all_tickets()
    now = datetime.now(pytz.timezone(config.TIMEZONE))
    breaches = kpi.find_sla_breaches(tickets, now, config.FIRST_RESPONSE_SLA_MINUTES)
    for ticket, overdue_min in breaches:
        sheet_store.update_ticket(ticket["ticket_id"], {"sla_breach_alerted": "yes"})
        client.chat_postMessage(
            channel=config.TRIAGE_CHANNEL,
            thread_ts=ticket.get("triage_ts") or None,
            text=(
                f"{config.ESCALATION_MENTION} 🚨 SLA breach: *{ticket['ticket_id']}* "
                f"({ticket['priority']}) has had no response for "
                f"{kpi.fmt_minutes(overdue_min)} past its target — {ticket['subject']}"
            ),
        )
        log.warning("SLA breach alerted for %s", ticket["ticket_id"])
