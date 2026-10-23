import argparse
import os
import signal
import sys
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

_SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))

# When running without a terminal (Task Scheduler, pythonw), route all output to scout.log
if sys.stdout is None or not sys.stdout.isatty():
    _log_file = open(os.path.join(_SERVICE_DIR, "scout.log"), "a", buffering=1, encoding="utf-8")
    sys.stdout = _log_file
    sys.stderr = _log_file

load_dotenv(os.path.join(_SERVICE_DIR, "config.env"))

_REQUIRED_KEYS = ["GOOGLE_API_KEY", "GMAIL_ADDRESS", "GMAIL_APP_PASSWORD"]


def _validate_config():
    missing = [k for k in _REQUIRED_KEYS if not os.getenv(k)]
    if missing:
        print(f"[main] Missing required config: {', '.join(missing)}")
        print("[main] Fill in config.env and restart.")
        sys.exit(1)


from db import (
    count_pending,
    defer_job,
    get_state,
    init_db,
    load_pending,
    mark_seen,
    remove_pending,
    set_state,
)
from filter import FilterError, RelevanceFilter
from linkedin_email_source import fetch_jobs
from notifier import Notifier

_DB_PATH = os.path.join(_SERVICE_DIR, "jobs.db")
_PROFILE_PATH = os.path.join(_SERVICE_DIR, "profile.md")

# Recruiter-aggregator accounts that repost the same generic listing under a
# new job ID repeatedly, evading URL-based dedup. Extend as new offenders show up.
_BLOCKLISTED_COMPANIES = {
    "jobs ai",
    "hire feed",
    "quik hire staffing",
}


_MAX_TRANSIENT_ATTEMPTS = 5
_ALERT_INTERVAL = timedelta(hours=24)
_GAVE_UP_NOTE = "Could not be evaluated by the filter after repeated errors — review manually."


def _is_blocklisted(company: str) -> bool:
    return company.strip().lower() in _BLOCKLISTED_COMPANIES


def _update_outage_state(aborted: FilterError | None, any_success: bool, notifier: Notifier):
    if aborted:
        last_alert = get_state("last_alert_at", _DB_PATH)
        ongoing = get_state("outage_reason", _DB_PATH) is not None
        now = datetime.now(timezone.utc)
        if not ongoing or not last_alert or now - datetime.fromisoformat(last_alert) >= _ALERT_INTERVAL:
            notifier.send_alert(aborted.reason, count_pending(_DB_PATH))
            set_state("last_alert_at", now.isoformat(), _DB_PATH)
        set_state("outage_reason", aborted.reason, _DB_PATH)
    elif any_success:
        set_state("outage_reason", None, _DB_PATH)
        set_state("last_alert_at", None, _DB_PATH)


def run_once():
    print(f"[main] {datetime.now().isoformat(timespec='seconds')} Scout run starting...")

    # Pending jobs first: they were deferred by an earlier LLM failure, and their
    # alert emails are already marked processed, so this is their only way back.
    pending = load_pending(_DB_PATH)
    jobs = pending + fetch_jobs(
        os.getenv("GMAIL_ADDRESS"),
        os.getenv("GMAIL_APP_PASSWORD"),
        _DB_PATH,
    )

    if not jobs:
        print("[main] Nothing new. Done.")
        return

    print(f"[main] {len(jobs)} jobs to evaluate ({len(pending)} pending from earlier runs)")

    relevance_filter = RelevanceFilter(_PROFILE_PATH, os.getenv("GOOGLE_API_KEY"))
    notifier = Notifier(os.getenv("GMAIL_ADDRESS"), os.getenv("GMAIL_APP_PASSWORD"))

    entries = []
    aborted: FilterError | None = None
    any_success = False
    deferred = 0
    for job in jobs:
        company = job.get("company", "")

        if _is_blocklisted(company):
            print(f"[main] Blocklisted: {job['title']} @ {company}")
            mark_seen(job["url"], job["title"], company, "SKIP", _DB_PATH)
            remove_pending(job["url"], _DB_PATH)
            continue

        if aborted:
            defer_job(job, aborted.detail, count_attempt=False, path=_DB_PATH)
            deferred += 1
            continue

        try:
            verdict, scope = relevance_filter.evaluate(job)
        except FilterError as e:
            deferred += 1
            if e.kind == "fatal":
                print(f"[main] Filter down ({e.reason}); deferring remaining jobs without LLM calls")
                aborted = e
                defer_job(job, e.detail, count_attempt=False, path=_DB_PATH)
                continue
            attempts = defer_job(job, e.detail, count_attempt=True, path=_DB_PATH)
            if attempts >= _MAX_TRANSIENT_ATTEMPTS:
                print(f"[main] Giving up after {attempts} attempts: {job['url']}")
                mark_seen(job["url"], job["title"], company, "ERROR", _DB_PATH)
                remove_pending(job["url"], _DB_PATH)
                entries.append((job, "ERROR", _GAVE_UP_NOTE))
            continue

        any_success = True
        mark_seen(job["url"], job["title"], company, verdict, _DB_PATH)
        remove_pending(job["url"], _DB_PATH)
        if verdict in ("RELEVANT", "UNSURE"):
            entries.append((job, verdict, scope))

    if entries:
        notifier.send_digest(entries)
        print(f"[main] 1 digest email sent covering {len(entries)} of {len(jobs)} jobs.")
    else:
        print(f"[main] No matches, no digest sent ({len(jobs)} jobs).")
    if deferred:
        print(f"[main] {deferred} job(s) deferred to a later run.")

    _update_outage_state(aborted, any_success, notifier)
    print("[main] Done.")


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
