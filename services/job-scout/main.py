import argparse
import os
import signal
import sys

from dotenv import load_dotenv

_SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(_SERVICE_DIR, "config.env"))

_REQUIRED_KEYS = ["TAVILY_API_KEY", "GOOGLE_API_KEY", "GMAIL_ADDRESS", "GMAIL_APP_PASSWORD"]


def _validate_config():
    missing = [k for k in _REQUIRED_KEYS if not os.getenv(k)]
    if missing:
        print(f"[main] Missing required config: {', '.join(missing)}")
        print("[main] Fill in config.env and restart.")
        sys.exit(1)


from db import init_db, is_seen, mark_seen
from filter import RelevanceFilter
from notifier import Notifier
from searcher import search

_DB_PATH = os.path.join(_SERVICE_DIR, "jobs.db")
_PROFILE_PATH = os.path.join(_SERVICE_DIR, "profile.md")


def run_once():
    print("[main] Scout run starting...")

    jobs = search(os.getenv("TAVILY_API_KEY"))
    new_jobs = [j for j in jobs if not is_seen(j["url"], _DB_PATH)]
    print(f"[main] {len(new_jobs)} unseen jobs to evaluate")

    if not new_jobs:
        print("[main] Nothing new. Done.")
        return

    relevance_filter = RelevanceFilter(_PROFILE_PATH, os.getenv("GOOGLE_API_KEY"))
    notifier = Notifier(os.getenv("GMAIL_ADDRESS"), os.getenv("GMAIL_APP_PASSWORD"))

    sent = 0
    for job in new_jobs:
        verdict, explanation = relevance_filter.evaluate(job)
        mark_seen(job["url"], job["title"], "", verdict, _DB_PATH)
        if verdict in ("RELEVANT", "UNSURE"):
            notifier.send(job, verdict, explanation)
            sent += 1

    print(f"[main] Done. {sent} emails sent out of {len(new_jobs)} evaluated.")


def main():
    parser = argparse.ArgumentParser(description="Job Scout — LinkedIn job notifier")
    parser.add_argument("--once", action="store_true", help="Run once and exit (no scheduler)")
    args = parser.parse_args()

    _validate_config()
    init_db(_DB_PATH)

    if args.once:
        run_once()
        return

    from apscheduler.schedulers.blocking import BlockingScheduler

    interval_hours = int(os.getenv("SCHEDULE_INTERVAL_HOURS", "6"))
    print(f"[main] Starting scheduler (every {interval_hours}h). Ctrl+C to stop.")

    scheduler = BlockingScheduler()
    scheduler.add_job(run_once, "interval", hours=interval_hours)

    def _shutdown(signum, frame):
        print("[main] Shutting down...")
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    run_once()
    scheduler.start()


if __name__ == "__main__":
    main()
