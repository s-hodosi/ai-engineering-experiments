import argparse
import os
import signal
import sys

from dotenv import load_dotenv

_SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))

# When running without a terminal (Task Scheduler, pythonw), route all output to scout.log
if sys.stdout is None or not sys.stdout.isatty():
    _log_file = open(os.path.join(_SERVICE_DIR, "scout.log"), "a", buffering=1, encoding="utf-8")
    sys.stdout = _log_file
    sys.stderr = _log_file

load_dotenv(os.path.join(_SERVICE_DIR, "config.env"))

_REQUIRED_KEYS = ["TAVILY_API_KEY", "GOOGLE_API_KEY", "GMAIL_ADDRESS", "GMAIL_APP_PASSWORD"]


def _validate_config():
    missing = [k for k in _REQUIRED_KEYS if not os.getenv(k)]
    if missing:
        print(f"[main] Missing required config: {', '.join(missing)}")
        print("[main] Fill in config.env and restart.")
        sys.exit(1)


from adzuna_searcher import search as adzuna_search
from db import init_db, is_seen, mark_seen
from filter import RelevanceFilter
from notifier import Notifier
from searcher import search as tavily_search

_DB_PATH = os.path.join(_SERVICE_DIR, "jobs.db")
_PROFILE_PATH = os.path.join(_SERVICE_DIR, "profile.md")


def run_once():
    print("[main] Scout run starting...")

    max_age_days = int(os.getenv("FRESHNESS_MAX_AGE_DAYS", "3"))
    max_published_days = int(os.getenv("FRESHNESS_MAX_PUBLISHED_DAYS", "7"))

    tavily_jobs = tavily_search(os.getenv("TAVILY_API_KEY"), max_age_days=max_age_days, max_published_days=max_published_days)
    adzuna_jobs = adzuna_search(os.getenv("ADZUNA_APP_ID"), os.getenv("ADZUNA_APP_KEY"), max_age_days=max_age_days)
    all_jobs = {j["url"]: j for j in tavily_jobs + adzuna_jobs}.values()
    new_jobs = [j for j in all_jobs if not is_seen(j["url"], _DB_PATH)]
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

    interval_minutes = int(os.getenv("SCHEDULE_INTERVAL_MINUTES", "30"))
    print(f"[main] Starting scheduler (every {interval_minutes}min). Ctrl+C to stop.")

    scheduler = BlockingScheduler()
    scheduler.add_job(run_once, "interval", minutes=interval_minutes)

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
