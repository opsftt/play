"""Slack listeners for the full ticket lifecycle.

Create:  /ticket modal, or react to any message with the ticket emoji.
Triage:  card in the triage channel with Claim / Resolve / Escalate buttons.
Measure: claim = first response, resolve = resolution, then a CSAT survey is
         DM'd to the student. Every transition is written to the Google Sheet.
"""

import logging
from datetime import datetime

import pytz

import config
from bot import views
from metrics import kpi
from store import sheet_store

log = logging.getLogger(__name__)


def register(app):
    app.command("/ticket")(open_ticket_modal)
    app.view("ticket_modal")(submit_ticket)
    app.event("reaction_added")(reaction_ticket)
    app.action("claim_ticket")(claim_ticket)
    app.action("resolve_ticket")(open_resolve_modal)
    app.view("resolve_modal")(submit_resolution)
    app.action("escalate_ticket")(escalate_ticket)
    for n in range(1, 6):
        app.action(f"csat_{n}")(record_csat)
    app.command("/kpis")(kpi_report)


# ── Creation ─────────────────────────────────────────────────────────────────

def open_ticket_modal(ack, body, client):
    ack()
    client.views_open(trigger_id=body["trigger_id"], view=views.ticket_modal())


def submit_ticket(ack, body, view, client):
    ack()
    values = view["state"]["values"]
    user_id = body["user"]["id"]
    user_name = body["user"].get("name", user_id)
    _create_ticket(
        client,
        student_id=user_id,
        student_name=user_name,
        source="modal",
        category=values["category"]["value"]["selected_option"]["value"],
        priority=values["priority"]["value"]["selected_option"]["value"],
        subject=values["subject"]["value"]["value"],
        description=values["description"]["value"]["value"],
    )


def reaction_ticket(event, client):
    """Turn any message into a ticket by reacting with the configured emoji."""
    if event.get("reaction") != config.TICKET_REACTION:
        return
    item = event.get("item", {})
    if item.get("type") != "message":
        return
    result = client.conversations_history(
        channel=item["channel"], latest=item["ts"], inclusive=True, limit=1
    )
    messages = result.get("messages", [])
    if not messages:
        return
    msg = messages[0]
    author = msg.get("user") or event["user"]
    text = (msg.get("text") or "(no text)").strip()
    ticket = _create_ticket(
        client,
        student_id=author,
        student_name="",
        source="reaction",
        category="Other",
        priority="normal",
        subject=text[:120],
        description=text,
    )
    client.chat_postMessage(
        channel=item["channel"],
        thread_ts=item["ts"],
        text=f"🎫 Tracked as ticket *{ticket['ticket_id']}* — the support team is on it.",
    )


def _create_ticket(client, **fields):
    ticket = {
        "ticket_id": sheet_store.next_ticket_id(),
        "created_at": sheet_store.now_iso(),
        "status": "open",
        **fields,
    }
    posted = client.chat_postMessage(
        channel=config.TRIAGE_CHANNEL,
        text=f"New ticket {ticket['ticket_id']}: {ticket['subject']}",
        blocks=views.triage_card(ticket),
    )
    ticket["triage_channel"] = posted["channel"]
    ticket["triage_ts"] = posted["ts"]
    sheet_store.create_ticket(ticket)
    client.chat_postMessage(
        channel=ticket["student_id"],
        text=(
            f"✅ Got it! Your ticket *{ticket['ticket_id']}: {ticket['subject']}* is in. "
            "Our team has been notified and you'll hear from us soon."
        ),
    )
    log.info("created ticket %s (%s)", ticket["ticket_id"], ticket["source"])
    return ticket


# ── Triage actions ───────────────────────────────────────────────────────────

def claim_ticket(ack, body, client):
    ack()
    ticket_id = body["actions"][0]["value"]
    claimer = body["user"]["id"]
    ticket = sheet_store.update_ticket(ticket_id, {
        "status": "in_progress",
        "assigned_to": claimer,
        "assigned_to_name": body["user"].get("name", claimer),
        "first_response_at": sheet_store.now_iso(),
    })
    _refresh_card(client, ticket)
    client.chat_postMessage(
        channel=ticket["student_id"],
        text=f"👋 <@{claimer}> from our team has picked up your ticket *{ticket_id}* and is looking into it.",
    )


def open_resolve_modal(ack, body, client):
    ack()
    ticket_id = body["actions"][0]["value"]
    client.views_open(trigger_id=body["trigger_id"], view=views.resolve_modal(ticket_id))


def submit_resolution(ack, body, view, client):
    ack()
    ticket_id = view["private_metadata"]
    note = view["state"]["values"]["resolution_note"]["value"]["value"]
    fields = {
        "status": "resolved",
        "resolved_at": sheet_store.now_iso(),
        "resolution_note": note,
    }
    # A resolve without a prior claim still counts as the first response.
    existing = sheet_store.get_ticket(ticket_id)
    if existing and not existing.get("first_response_at"):
        fields["first_response_at"] = fields["resolved_at"]
        fields["assigned_to"] = body["user"]["id"]
        fields["assigned_to_name"] = body["user"].get("name", "")
    ticket = sheet_store.update_ticket(ticket_id, fields)
    _refresh_card(client, ticket)
    client.chat_postMessage(
        channel=ticket["student_id"],
        text=f"Your ticket {ticket_id} has been resolved!",
        blocks=views.csat_blocks(ticket),
    )


def escalate_ticket(ack, body, client):
    ack()
    ticket_id = body["actions"][0]["value"]
    ticket = sheet_store.update_ticket(ticket_id, {"escalated": "yes"})
    _refresh_card(client, ticket)
    client.chat_postMessage(
        channel=config.TRIAGE_CHANNEL,
        thread_ts=ticket.get("triage_ts") or None,
        text=(
            f"{config.ESCALATION_MENTION} ⚠️ *{ticket_id}* escalated by <@{body['user']['id']}> — "
            f"{ticket['subject']} (priority: {ticket['priority']})"
        ),
    )


def record_csat(ack, body, client):
    ack()
    action = body["actions"][0]
    score = int(action["action_id"].split("_")[1])
    ticket_id = action["value"]
    sheet_store.update_ticket(ticket_id, {"csat_score": score})
    ticket = sheet_store.get_ticket(ticket_id)
    if ticket:
        _refresh_card(client, ticket)
    client.chat_update(
        channel=body["channel"]["id"],
        ts=body["message"]["ts"],
        text=f"Thanks for rating {ticket_id}!",
        blocks=[{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{'⭐' * score} Thanks for the feedback on *{ticket_id}* — it helps us improve! 🙏",
            },
        }],
    )


def _refresh_card(client, ticket):
    if not ticket.get("triage_ts"):
        return
    client.chat_update(
        channel=ticket.get("triage_channel") or config.TRIAGE_CHANNEL,
        ts=ticket["triage_ts"],
        text=f"Ticket {ticket['ticket_id']}: {ticket['subject']}",
        blocks=views.triage_card(ticket),
    )


# ── KPI report ───────────────────────────────────────────────────────────────

def kpi_report(ack, body, respond):
    ack()
    arg = (body.get("text") or "").strip()
    window_days = int(arg) if arg.isdigit() else 7
    tickets = sheet_store.get_all_tickets()
    now = datetime.now(pytz.timezone(config.TIMEZONE))
    kpis = kpi.compute_kpis(
        tickets, now, window_days,
        config.FIRST_RESPONSE_SLA_MINUTES, config.RESOLUTION_SLA_MINUTES,
    )
    respond(
        response_type="ephemeral",
        text=f"KPI report — last {window_days} days",
        blocks=views.kpi_blocks(kpis, f"📊 Customer Success KPIs — last {window_days} days"),
    )
