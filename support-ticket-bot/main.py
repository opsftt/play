"""Support ticket bot entrypoint.

Runs the Slack app over Socket Mode (no public URL needed) plus a background
scheduler for the weekly KPI digest and SLA breach checks.
"""

import logging
import threading
import time

import schedule
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import config
from bot import handlers
from metrics import digest

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


def run_scheduler(client):
    getattr(schedule.every(), config.DIGEST_DAY).at(config.DIGEST_TIME, config.TIMEZONE).do(
        digest.post_weekly_digest, client
    )
    schedule.every(config.SLA_CHECK_MINUTES).minutes.do(digest.check_sla_breaches, client)
    log.info(
        "scheduler running: digest %s %s, SLA check every %sm",
        config.DIGEST_DAY, config.DIGEST_TIME, config.SLA_CHECK_MINUTES,
    )
    while True:
        try:
            schedule.run_pending()
        except Exception:
            log.exception("scheduled job failed")
        time.sleep(30)


def main():
    app = App(token=config.SLACK_BOT_TOKEN)
    handlers.register(app)
    threading.Thread(target=run_scheduler, args=(app.client,), daemon=True).start()
    SocketModeHandler(app, config.SLACK_APP_TOKEN).start()


if __name__ == "__main__":
    main()
