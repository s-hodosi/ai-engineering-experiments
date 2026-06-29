"""
Smoke test: runs search → dedup → LLM filter, prints results.
Does not send email. Use this to verify the pipeline before setting up Gmail.
"""
import os
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from dotenv import load_dotenv

_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_DIR, "config.env"))

from adzuna_searcher import search as adzuna_search
from db import init_db, is_seen, mark_seen
from filter import RelevanceFilter
from searcher import search as tavily_search

DB_PATH = os.path.join(_DIR, "test_jobs.db")
init_db(DB_PATH)

print("=== Job Scout Smoke Test ===\n")

tavily_jobs = tavily_search(os.getenv("TAVILY_API_KEY"))
adzuna_jobs = adzuna_search(os.getenv("ADZUNA_APP_ID"), os.getenv("ADZUNA_APP_KEY"))
jobs = list({j["url"]: j for j in tavily_jobs + adzuna_jobs}.values())
print(f"Found {len(jobs)} jobs after pre-filter (Tavily: {len(tavily_jobs)}, Adzuna: {len(adzuna_jobs)})\n")

new_jobs = [j for j in jobs if not is_seen(j["url"], DB_PATH)]
print(f"{len(new_jobs)} not yet seen\n")

if not new_jobs:
    print("No new jobs to evaluate. Try deleting test_jobs.db to reset.")
    sys.exit(0)

f = RelevanceFilter(os.path.join(_DIR, "profile.md"), os.getenv("GOOGLE_API_KEY"))

for job in new_jobs[:3]:  # cap at 3 LLM calls for the smoke test
    verdict, explanation = f.evaluate(job)
    mark_seen(job["url"], job["title"], "", verdict, DB_PATH)
    print(f"[{verdict}] {job['title']}")
    print(f"  URL: {job['url']}")
    print(f"  {explanation[:200]}...")
    print()

print("=== Smoke test complete ===")
