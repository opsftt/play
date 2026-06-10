import os
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]
TRIAGE_CHANNEL = os.environ["TRIAGE_CHANNEL"]
DIGEST_CHANNEL = os.getenv("DIGEST_CHANNEL", TRIAGE_CHANNEL)
ESCALATION_MENTION = os.getenv("ESCALATION_MENTION", "<!here>")
TICKET_REACTION = os.getenv("TICKET_REACTION", "ticket")

GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "credentials/google_service_account.json")
TICKETS_SHEET_ID = os.environ["TICKETS_SHEET_ID"]

TIMEZONE = os.getenv("TIMEZONE", "America/New_York")
DIGEST_DAY = os.getenv("DIGEST_DAY", "monday").lower()
DIGEST_TIME = os.getenv("DIGEST_TIME", "09:00")
SLA_CHECK_MINUTES = int(os.getenv("SLA_CHECK_MINUTES", 30))
TICKET_PREFIX = os.getenv("TICKET_PREFIX", "FTT")

# Ticket taxonomy shown in the /ticket modal
CATEGORIES = [
    "Course Access / Whop",
    "Billing & Payments",
    "Trading Platform / Tools",
    "Course Content Question",
    "Community / Slack",
    "Account & Login",
    "Feedback / Suggestion",
    "Other",
]

PRIORITIES = ["urgent", "high", "normal", "low"]

# First-response SLA targets in minutes, per priority. "First response" is
# when a team member claims the ticket.
FIRST_RESPONSE_SLA_MINUTES = {
    "urgent": 60,        # 1 hour
    "high": 4 * 60,      # 4 hours
    "normal": 24 * 60,   # 1 business day
    "low": 48 * 60,      # 2 days
}

# Resolution SLA targets in minutes, per priority.
RESOLUTION_SLA_MINUTES = {
    "urgent": 4 * 60,
    "high": 24 * 60,
    "normal": 48 * 60,
    "low": 5 * 24 * 60,
}
