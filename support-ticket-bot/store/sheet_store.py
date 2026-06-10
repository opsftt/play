"""Google Sheets as the ticket database.

One worksheet ("Tickets") holds one row per ticket. The bot appends a row when
a ticket is created and updates cells in place as the ticket moves through its
lifecycle, so the sheet is always the live source of truth your team can
filter, pivot, and chart directly.
"""

import threading

import gspread
from google.oauth2.service_account import Credentials

import config
from timeutil import now_iso, parse_ts  # noqa: F401  (re-exported for callers)

WORKSHEET_NAME = "Tickets"

COLUMNS = [
    "ticket_id",
    "created_at",
    "student_id",
    "student_name",
    "source",            # modal | reaction
    "category",
    "priority",
    "subject",
    "description",
    "status",            # open | in_progress | resolved
    "assigned_to",
    "assigned_to_name",
    "first_response_at",
    "resolved_at",
    "resolution_note",
    "csat_score",        # 1-5, set by the student after resolution
    "csat_comment",
    "escalated",         # yes | (blank)
    "sla_breach_alerted",  # yes once the breach ping has fired, so we alert once
    "triage_channel",
    "triage_ts",         # ts of the ticket card in the triage channel
]

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

_lock = threading.Lock()
_worksheet = None


def _get_worksheet():
    global _worksheet
    if _worksheet is None:
        creds = Credentials.from_service_account_file(
            config.GOOGLE_SERVICE_ACCOUNT_JSON, scopes=SCOPES
        )
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(config.TICKETS_SHEET_ID)
        try:
            ws = spreadsheet.worksheet(WORKSHEET_NAME)
        except gspread.WorksheetNotFound:
            ws = spreadsheet.add_worksheet(WORKSHEET_NAME, rows=2000, cols=len(COLUMNS))
        if ws.row_values(1) != COLUMNS:
            ws.update("A1", [COLUMNS])
            ws.freeze(rows=1)
        _worksheet = ws
    return _worksheet


def next_ticket_id():
    ws = _get_worksheet()
    with _lock:
        count = len(ws.col_values(1))  # header + existing tickets
        return f"{config.TICKET_PREFIX}-{1000 + count}"


def create_ticket(ticket):
    """Append a ticket dict (keys from COLUMNS) as a new row."""
    ws = _get_worksheet()
    row = [str(ticket.get(col, "")) for col in COLUMNS]
    with _lock:
        ws.append_row(row, value_input_option="RAW")


def update_ticket(ticket_id, fields):
    """Update the given columns of the ticket's row. Returns the merged dict."""
    ws = _get_worksheet()
    with _lock:
        cell = ws.find(ticket_id, in_column=1)
        if cell is None:
            raise KeyError(f"ticket {ticket_id} not found in sheet")
        row_values = ws.row_values(cell.row)
        row_values += [""] * (len(COLUMNS) - len(row_values))
        ticket = dict(zip(COLUMNS, row_values))
        updates = []
        for key, value in fields.items():
            col_idx = COLUMNS.index(key) + 1
            updates.append(gspread.Cell(cell.row, col_idx, str(value)))
            ticket[key] = str(value)
        ws.update_cells(updates, value_input_option="RAW")
    return ticket


def get_ticket(ticket_id):
    ws = _get_worksheet()
    cell = ws.find(ticket_id, in_column=1)
    if cell is None:
        return None
    row_values = ws.row_values(cell.row)
    row_values += [""] * (len(COLUMNS) - len(row_values))
    return dict(zip(COLUMNS, row_values))


def get_all_tickets():
    """Return every ticket as a list of dicts keyed by COLUMNS."""
    ws = _get_worksheet()
    rows = ws.get_all_values()[1:]  # skip header
    tickets = []
    for row in rows:
        row += [""] * (len(COLUMNS) - len(row))
        tickets.append(dict(zip(COLUMNS, row)))
    return tickets
