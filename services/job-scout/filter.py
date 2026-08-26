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
Location: {location}

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
- Both technical EM roles and senior managing-managers roles are valid targets within the range defined in Role-scope rules below; do not skip a role solely for being technical, or solely for being senior short of the explicit Chief-level cap
- If the job description text is not written in English or Hungarian, return SKIP

Role-scope rules (target range is Senior Engineering Manager and above, capped at VP Engineering):
- Plain "Engineering Manager" and "Team Leader"/"Team Lead" titles are NOT sufficient on their own — judge seniority by the organizational scope described in the JD, not by title string alone, since titles both overstate and understate real seniority
- Treat a role as meeting the bar if the JD shows: managing other managers, owning multiple teams or a department, reporting to a VP/CTO/C-level position, or an explicit Director/Head/VP/Principal-equivalent title
- A plainly-titled "Engineering Manager" or "Team Lead" role showing one of the above scope signals SHALL NOT be skipped for its title alone
- A "Senior Engineering Manager" or similarly-titled role that only describes single-team, first-line management scope with no evidence of managing managers or department-level ownership should be treated as below the bar
- If the JD gives no usable scope signal at all (e.g. a very thin snippet, or "[limited info — JD not accessible]"), return UNSURE rather than guessing SKIP or RELEVANT
- CTO, Chief Technology Officer, Chief Engineering Officer, or other Chief-level titles are always SKIP — VP Engineering is the top of the target range
- Pure individual-contributor roles (e.g. Staff/Principal Software Engineer, Architect with no people-management scope, "Founding Engineer" hired as a hands-on IC) are SKIP regardless of technical domain fit
- Leadership roles outside the software engineering/development organization — Quality Assurance-only, Security-only, Data/Analytics-only, Program/PMO management, Governance/Risk/Compliance, general business Consulting, Talent/Learning & Development, or general "General Manager"/Operations roles — are SKIP unless the JD explicitly describes leading a software engineering or development team (roles like "Head of Platform Engineering" or "Director of SRE" are core engineering and are NOT covered by this rule)

Location rules (candidate is in Hungary, EU — not open to relocation):
- If the role names any specific single country other than Hungary as the required location, residency, work authorization, or physical presence, return SKIP. This includes:
  - Explicit restrictions — e.g. "for those based in the UK", "must be based in Germany", "must be a UK resident", "right to work in Ireland required"
  - A bare single-country remote label with no further restriction language — e.g. "Remote, UK", "Remote, Germany", "Remote, US"
  - A requirement of on-site or hybrid physical presence in that country — e.g. "on-site in Berlin required", "hybrid, San Francisco office"
  - A list of eligible countries that omits Hungary — e.g. "open to candidates based in Germany, Poland, or the Netherlands"
- If the role is "Remote UK/EU", "Remote EMEA", "Remote Europe", "Remote (global)", or any multi-region scope that includes the EU, location is NOT a basis for SKIP — evaluate on role fit only
- If Hungary is named as the required location, or as one of several eligible countries, location is NOT a basis for SKIP — evaluate on role fit only
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
            location=job.get("location", ""),
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
