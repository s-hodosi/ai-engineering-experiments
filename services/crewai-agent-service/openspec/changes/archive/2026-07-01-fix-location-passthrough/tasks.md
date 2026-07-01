## 1. Thread location through email parsing

- [x] 1.1 In `services/job-scout/linkedin_email_source.py::fetch_jobs()`, add `"location": job["location"]` to the dict appended to `results` (around the existing `results.append({...})` block)
- [x] 1.2 Confirm `_parse_jobs_from_email` always sets `location` to a string (empty if unparsed) so the new key is never missing

## 2. Use location in the relevance filter prompt

- [x] 2.1 In `services/job-scout/filter.py`, add a `Location: {location}` line to `_PROMPT_TEMPLATE` near the existing `Title:`/`URL:` lines
- [x] 2.2 In `RelevanceFilter.evaluate()`, pass `location=job.get("location", "")` when formatting the prompt

## 3. Verify

- [x] 3.1 Run `services/job-scout/test_smoke.py` (or equivalent manual `--once` run) against a sample LinkedIn alert email containing a location string (e.g. the EPAM Systems / "Hungary (Remote)" case) and confirm the resulting notification subject shows the real location instead of "Location unclear"
- [x] 3.2 Manually trace a UK-only-restricted JD with a populated `location` field through the updated prompt and confirm the filter still returns the correct verdict (no regression from the prior `fix-location-filtering` change)
