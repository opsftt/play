"""Block Kit builders for modals, ticket cards, CSAT surveys, and KPI reports."""

import config
from metrics.kpi import fmt_minutes, fmt_rate

PRIORITY_EMOJI = {"urgent": "🔴", "high": "🟠", "normal": "🟡", "low": "🟢"}
STATUS_LABEL = {"open": "🆕 Open", "in_progress": "👷 In progress", "resolved": "✅ Resolved"}


def ticket_modal():
    return {
        "type": "modal",
        "callback_id": "ticket_modal",
        "title": {"type": "plain_text", "text": "New support ticket"},
        "submit": {"type": "plain_text", "text": "Submit"},
        "blocks": [
            {
                "type": "input",
                "block_id": "subject",
                "label": {"type": "plain_text", "text": "Subject"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "value",
                    "max_length": 150,
                    "placeholder": {"type": "plain_text", "text": "One-line summary of the issue"},
                },
            },
            {
                "type": "input",
                "block_id": "category",
                "label": {"type": "plain_text", "text": "Category"},
                "element": {
                    "type": "static_select",
                    "action_id": "value",
                    "options": [
                        {"text": {"type": "plain_text", "text": c}, "value": c}
                        for c in config.CATEGORIES
                    ],
                },
            },
            {
                "type": "input",
                "block_id": "priority",
                "label": {"type": "plain_text", "text": "How urgent is this?"},
                "element": {
                    "type": "static_select",
                    "action_id": "value",
                    "initial_option": {
                        "text": {"type": "plain_text", "text": "🟡 Normal — within a day is fine"},
                        "value": "normal",
                    },
                    "options": [
                        {"text": {"type": "plain_text", "text": "🔴 Urgent — blocking me right now"}, "value": "urgent"},
                        {"text": {"type": "plain_text", "text": "🟠 High — need help today"}, "value": "high"},
                        {"text": {"type": "plain_text", "text": "🟡 Normal — within a day is fine"}, "value": "normal"},
                        {"text": {"type": "plain_text", "text": "🟢 Low — whenever you can"}, "value": "low"},
                    ],
                },
            },
            {
                "type": "input",
                "block_id": "description",
                "label": {"type": "plain_text", "text": "Details"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "value",
                    "multiline": True,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "What happened? What have you tried? Include links/screenshots info if relevant.",
                    },
                },
            },
        ],
    }


def resolve_modal(ticket_id):
    return {
        "type": "modal",
        "callback_id": "resolve_modal",
        "private_metadata": ticket_id,
        "title": {"type": "plain_text", "text": f"Resolve {ticket_id}"},
        "submit": {"type": "plain_text", "text": "Resolve"},
        "blocks": [
            {
                "type": "input",
                "block_id": "resolution_note",
                "label": {"type": "plain_text", "text": "Resolution summary (sent to the student)"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "value",
                    "multiline": True,
                    "placeholder": {"type": "plain_text", "text": "What was the fix or answer?"},
                },
            },
        ],
    }


def triage_card(ticket):
    """The ticket card posted in the triage channel, with lifecycle buttons."""
    tid = ticket["ticket_id"]
    status = ticket.get("status", "open")
    emoji = PRIORITY_EMOJI.get(ticket.get("priority", "normal"), "🟡")

    fields = [
        f"*Student:* <@{ticket['student_id']}>",
        f"*Category:* {ticket['category']}",
        f"*Priority:* {emoji} {ticket['priority']}",
        f"*Status:* {STATUS_LABEL.get(status, status)}",
    ]
    if ticket.get("assigned_to"):
        fields.append(f"*Assigned:* <@{ticket['assigned_to']}>")
    if ticket.get("escalated") == "yes":
        fields.append("*Escalated:* ⚠️ yes")

    blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*{tid}: {ticket['subject']}*"},
        },
        {
            "type": "section",
            "fields": [{"type": "mrkdwn", "text": f} for f in fields],
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f">{ticket['description'][:2500]}"},
        },
    ]

    buttons = []
    if status == "open":
        buttons.append(_button("👋 Claim", "claim_ticket", tid, style="primary"))
    if status in ("open", "in_progress"):
        buttons.append(_button("✅ Resolve", "resolve_ticket", tid))
        if ticket.get("escalated") != "yes":
            buttons.append(_button("⚠️ Escalate", "escalate_ticket", tid, style="danger"))
    if buttons:
        blocks.append({"type": "actions", "elements": buttons})

    footer = f"Opened {ticket['created_at']}"
    if ticket.get("resolved_at"):
        footer += f" · Resolved {ticket['resolved_at']}"
    if str(ticket.get("csat_score", "")).isdigit():
        footer += f" · CSAT {'⭐' * int(ticket['csat_score'])}"
    blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": footer}]})
    return blocks


def _button(text, action_id, value, style=None):
    btn = {
        "type": "button",
        "text": {"type": "plain_text", "text": text},
        "action_id": action_id,
        "value": value,
    }
    if style:
        btn["style"] = style
    return btn


def csat_blocks(ticket):
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"🎉 Your ticket *{ticket['ticket_id']}: {ticket['subject']}* has been resolved!\n"
                    f"> {ticket.get('resolution_note', '')}\n\n"
                    "How did we do? Your feedback keeps our support sharp:"
                ),
            },
        },
        {
            "type": "actions",
            "block_id": "csat_actions",
            "elements": [
                _button("⭐" * n, f"csat_{n}", ticket["ticket_id"]) for n in range(1, 6)
            ],
        },
    ]


def kpi_blocks(kpis, title):
    lines = [
        f"*🎫 Volume* — created: *{kpis['created']}* · resolved: *{kpis['resolved']}* · "
        f"open backlog: *{kpis['open_total']}*"
        + (f" (oldest {kpis['oldest_open_days']:.1f}d)" if kpis["oldest_open_days"] else ""),
        f"*⚡ First response* — median: *{fmt_minutes(kpis['median_first_response_min'])}* · "
        f"avg: *{fmt_minutes(kpis['avg_first_response_min'])}*",
        f"*🏁 Resolution* — median: *{fmt_minutes(kpis['median_resolution_min'])}* · "
        f"avg: *{fmt_minutes(kpis['avg_resolution_min'])}*",
        f"*😊 CSAT* — avg: *{kpis['csat_avg']:.2f}/5*" if kpis["csat_avg"] is not None else "*😊 CSAT* — no responses yet",
    ]
    if kpis["csat_avg"] is not None:
        lines[-1] += f" from {kpis['csat_responses']} surveys ({fmt_rate(kpis['csat_response_rate'])} response rate)"
    lines.append(f"*⚠️ Escalations* — {kpis['escalated']} ({fmt_rate(kpis['escalation_rate'])})")

    sla_lines = []
    for priority in config.PRIORITIES:
        fr = kpis["first_response_sla"].get(priority)
        res = kpis["resolution_sla"].get(priority)
        if fr or res:
            sla_lines.append(
                f"• *{priority}* — first response {fmt_rate(fr['rate']) if fr else '–'}"
                f" · resolution {fmt_rate(res['rate']) if res else '–'}"
            )

    cat_lines = [f"• {cat}: {count}" for cat, count in list(kpis["by_category"].items())[:8]]

    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": title}},
        {"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(lines)}},
    ]
    if sla_lines:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "*🎯 SLA compliance*\n" + "\n".join(sla_lines)}})
    if cat_lines:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "*📂 By category*\n" + "\n".join(cat_lines)}})
    return blocks
