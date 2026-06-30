"""
Smoke test: runs email fetch → LLM filter, prints results.
Does not send email. Use this to verify the pipeline before running the scheduler.
"""
import os
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from dotenv import load_dotenv

_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_DIR, "config.env"))

from db import init_db, is_seen, mark_seen
from filter import RelevanceFilter
from linkedin_email_source import fetch_jobs

DB_PATH = os.path.join(_DIR, "test_jobs.db")
init_db(DB_PATH)

print("=== Job Scout Smoke Test ===\n")

jobs = fetch_jobs(os.getenv("GMAIL_ADDRESS"), os.getenv("GMAIL_APP_PASSWORD"), DB_PATH)
print(f"Found {len(jobs)} new jobs from LinkedIn alerts\n")

if not jobs:
    print("No new jobs to evaluate. Try deleting test_jobs.db to reset.")
    sys.exit(0)

f = RelevanceFilter(os.path.join(_DIR, "profile.md"), os.getenv("GOOGLE_API_KEY"))

for job in jobs[:3]:  # cap at 3 LLM calls for the smoke test
    verdict, explanation = f.evaluate(job)
    mark_seen(job["url"], job["title"], job.get("company", ""), verdict, DB_PATH)
    print(f"[{verdict}] {job['title']} @ {job.get('company', '?')}")
    print(f"  URL: {job['url']}")
    print(f"  Snippet: {job['snippet'][:200]}...")
    print(f"  {explanation[:200]}...")
    print()

print("=== Smoke test complete ===")
