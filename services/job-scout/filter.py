import os
import re
import litellm

_VERDICT_RE = re.compile(r'VERDICT:\s*(RELEVANT|UNSURE|SKIP)', re.IGNORECASE)
_EXPLANATION_RE = re.compile(r'EXPLANATION:\s*(.+)', re.IGNORECASE | re.DOTALL)

_SYSTEM = (
    "You are a job relevance filter. Evaluate job postings strictly against the candidate "
    "profile provided. Return structured output only."
)

_PROMPT_TEMPLATE = """\
## Candidate Profile

{profile}

## Job Posting

Title: {title}
URL: {url}

Description/Snippet:
{snippet}

## Task

Evaluate this job posting against the candidate profile.

Respond in EXACTLY this format — nothing else:
VERDICT: <RELEVANT|UNSURE|SKIP>
EXPLANATION: <one paragraph>

Rules:
- RELEVANT: strong match, candidate should read this immediately
- UNSURE: possible match but something is unclear (ambiguous role scope, borderline requirement)
- SKIP: clear disqualifier — a hard requirement the candidate demonstrably lacks
- When in doubt, use UNSURE — missed opportunities are worse than extra emails
- Both technical EM roles and senior managing-managers roles are valid targets; do not skip based on role being "too technical" or "too senior"
- If the job description text is not written in English or Hungarian, return SKIP

Location rules (candidate is in Hungary, EU — not open to relocation):
- If the role is explicitly restricted to UK residents — e.g. "for those based in the UK", "must be based in the UK", "must be a UK resident", "right to work in the UK required" — return SKIP
- If the role is listed as "Remote, UK" with no further restriction language, return UNSURE (company may hire internationally; restriction is not confirmed)
- If the role is "Remote UK/EU", "Remote EMEA", "Remote Europe", "Remote (global)", or any multi-region scope that includes the EU, location is NOT a basis for SKIP — evaluate on role fit only
"""


def _parse(text: str) -> tuple[str, str]:
    verdict_m = _VERDICT_RE.search(text)
    explanation_m = _EXPLANATION_RE.search(text)
    verdict = verdict_m.group(1).upper() if verdict_m else "UNSURE"
    explanation = explanation_m.group(1).strip() if explanation_m else text.strip()
    return verdict, explanation


class RelevanceFilter:
    def __init__(self, profile_path: str, google_api_key: str):
        if not os.path.exists(profile_path):
            raise FileNotFoundError(f"Candidate profile not found: {profile_path}")
        with open(profile_path, encoding="utf-8") as f:
            self._profile = f.read().strip()
        os.environ["GEMINI_API_KEY"] = google_api_key

    def evaluate(self, job: dict) -> tuple[str, str]:
        prompt = _PROMPT_TEMPLATE.format(
            profile=self._profile,
            title=job.get("title", ""),
            url=job.get("url", ""),
            snippet=job.get("snippet", ""),
        )
        try:
            response = litellm.completion(
                model="gemini/gemini-2.5-flash",
                messages=[
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
            )
            text = response.choices[0].message.content
            return _parse(text)
        except Exception as e:
            print(f"[filter] LLM call failed for {job.get('url')}: {e}")
            return "UNSURE", f"Filter unavailable ({e}) — review manually."
