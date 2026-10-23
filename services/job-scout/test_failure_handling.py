"""
Offline test for LLM failure handling: classification, pending queue, retry cap,
run abort and alert throttling. Mocks the LLM, email fetch and SMTP — no network.
"""
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from unittest import mock

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class _Tty:
    # main.py redirects output to scout.log when stdout isn't a terminal.
    def __init__(self, stream):
        self._stream = stream

    def isatty(self):
        return True

    def __getattr__(self, name):
        return getattr(self._stream, name)


sys.stdout = _Tty(sys.stdout)

import litellm

import db
import filter as filter_mod
import main
from filter import FilterError, _classify

BILLING_BODY = (
    'GeminiException - {\n  "error": {\n    "code": 402,\n    "message": "Your prepayment '
    'credits are depleted. Please go to AI Studio...",\n    "status": "RESOURCE_EXHAUSTED"\n  }\n}'
)


def _ok(verdict="RELEVANT"):
    resp = mock.Mock()
    resp.choices = [mock.Mock()]
    resp.choices[0].message.content = f"VERDICT: {verdict}\nSCOPE: Leads 3 EMs."
    return resp


def _billing():
    return litellm.APIConnectionError(message=BILLING_BODY, llm_provider="gemini", model="gemini-2.5-flash")


def _unavailable():
    return litellm.ServiceUnavailableError(message="overloaded", llm_provider="gemini", model="gemini-2.5-flash")


def _job(n):
    return {"url": f"https://www.linkedin.com/jobs/view/{n}/", "title": f"Director {n}",
            "company": f"Co{n}", "location": "Hungary (Remote)", "snippet": f"JD {n}",
            "source": "linkedin-email"}


class Harness:
    def __init__(self):
        fd, self.db = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        db.init_db(self.db)
        main._DB_PATH = self.db
        os.environ.setdefault("GOOGLE_API_KEY", "test")
        os.environ.setdefault("GMAIL_ADDRESS", "me@example.com")
        os.environ.setdefault("GMAIL_APP_PASSWORD", "x")

    def run(self, new_jobs, llm_effects):
        """Run main.run_once with mocked fetch/LLM/SMTP; returns (llm_calls, sent subjects, bodies)."""
        calls = []
        effects = list(llm_effects)

        def fake_completion(**kwargs):
            calls.append(kwargs)
            effect = effects.pop(0)
            if isinstance(effect, Exception):
                raise effect
            return effect

        sent = []

        def fake_send(self_, subject, body):
            sent.append((subject, body))

        with mock.patch.object(main, "fetch_jobs", return_value=list(new_jobs)), \
             mock.patch.object(filter_mod.litellm, "completion", side_effect=fake_completion), \
             mock.patch.object(main.Notifier, "_send", fake_send):
            main.run_once()
        return calls, [s for s, _ in sent], [b for _, b in sent]

    def pending(self):
        return {j["url"] for j in db.load_pending(self.db)}

    def attempts(self, url):
        import sqlite3
        with sqlite3.connect(self.db) as conn:
            row = conn.execute("SELECT attempts FROM pending_jobs WHERE url = ?", (url,)).fetchone()
        return row[0] if row else None

    def verdict(self, url):
        import sqlite3
        with sqlite3.connect(self.db) as conn:
            row = conn.execute("SELECT verdict FROM seen_jobs WHERE url = ?", (url,)).fetchone()
        return row[0] if row else None


def test_classification():
    assert (_classify(_billing()).kind, _classify(_billing()).reason) == ("fatal", "billing")
    old_429 = litellm.RateLimitError(message="Your prepayment credits are depleted.",
                                     llm_provider="gemini", model="m")
    assert _classify(old_429).reason == "billing"
    auth = litellm.AuthenticationError(message="API key not valid", llm_provider="gemini", model="m")
    assert (_classify(auth).kind, _classify(auth).reason) == ("fatal", "auth")
    for exc in [_unavailable(),
                litellm.RateLimitError(message="quota per minute", llm_provider="gemini", model="m"),
                litellm.Timeout(message="timed out", llm_provider="gemini", model="m")]:
        assert _classify(exc).kind == "transient", exc


def test_evaluate_raises_and_caps_thinking():
    f = filter_mod.RelevanceFilter(os.path.join(os.path.dirname(__file__), "profile.md"), "k")
    with mock.patch.object(filter_mod.litellm, "completion", side_effect=_billing()):
        try:
            f.evaluate(_job(1))
            assert False, "expected FilterError"
        except FilterError as e:
            assert e.kind == "fatal"
    with mock.patch.object(filter_mod.litellm, "completion", return_value=_ok()) as m:
        assert f.evaluate(_job(1)) == ("RELEVANT", "Leads 3 EMs.")
        assert m.call_args.kwargs["reasoning_effort"] == "low"


def test_db_helpers():
    h = Harness()
    job = _job(1)
    assert db.defer_job(job, "e", count_attempt=False, path=h.db) == 0
    assert db.defer_job(job, "e", count_attempt=True, path=h.db) == 1
    assert db.defer_job(job, "e", count_attempt=False, path=h.db) == 1
    loaded = db.load_pending(h.db)
    assert len(loaded) == 1
    assert {k: loaded[0][k] for k in ("url", "title", "company", "location", "snippet")} == \
        {k: job[k] for k in ("url", "title", "company", "location", "snippet")}
    assert db.is_pending(job["url"], h.db)
    db.mark_seen(job["url"], job["title"], job["company"], "SKIP", h.db)
    assert db.load_pending(h.db) == [] and not db.is_pending(job["url"], h.db)
    db.set_state("k", "v", h.db)
    assert db.get_state("k", h.db) == "v"
    db.set_state("k", None, h.db)
    assert db.get_state("k", h.db) is None
    db.init_db(h.db)  # idempotent


def test_outage_lifecycle():
    h = Harness()
    jobs = [_job(n) for n in range(1, 7)]

    # Billing error on job 3 of 6: jobs 1–2 delivered, 3–6 pending, no more LLM calls, one alert.
    calls, subjects, bodies = h.run(jobs, [_ok(), _ok("UNSURE"), _billing()])
    assert len(calls) == 3
    assert subjects == ["[Job Scout] 2 new matches", "[Job Scout] Filter down: billing"]
    assert "4 job(s) pending" in bodies[1] and "aistudio" in bodies[1] and "402" not in bodies[1]
    assert "Filter unavailable" not in bodies[0] and "GeminiException" not in bodies[0]
    assert h.verdict(jobs[0]["url"]) == "RELEVANT" and h.verdict(jobs[2]["url"]) is None
    assert h.pending() == {j["url"] for j in jobs[2:]}
    assert all(h.attempts(j["url"]) == 0 for j in jobs[2:])

    # Still down an hour later: no alert, attempts unchanged, only one LLM call.
    calls, subjects, _ = h.run([], [_billing()])
    assert len(calls) == 1 and subjects == []
    assert all(h.attempts(j["url"]) == 0 for j in jobs[2:])

    # Still down after 24h: re-alert.
    db.set_state("last_alert_at", (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat(), h.db)
    _, subjects, _ = h.run([], [_billing()])
    assert subjects == ["[Job Scout] Filter down: billing"]

    # Recovery: backlog evaluated, queue empty, outage state cleared.
    calls, subjects, _ = h.run([], [_ok(), _ok("SKIP"), _ok(), _ok()])
    assert len(calls) == 4 and subjects == ["[Job Scout] 3 new matches"]
    assert h.pending() == set()
    assert db.get_state("outage_reason", h.db) is None

    # New outage right after recovery alerts immediately.
    _, subjects, _ = h.run([_job(7)], [_billing()])
    assert subjects == ["[Job Scout] Filter down: billing"]


def test_transient_defers_only_that_job_and_caps_retries():
    h = Harness()
    jobs = [_job(n) for n in range(1, 4)]
    calls, subjects, _ = h.run(jobs, [_ok(), _unavailable(), _ok()])
    assert len(calls) == 3 and subjects == ["[Job Scout] 2 new matches"]
    assert h.pending() == {jobs[1]["url"]} and h.attempts(jobs[1]["url"]) == 1
    assert db.get_state("outage_reason", h.db) is None

    # Pending job is retried even with no new jobs; gives up on the 5th transient failure.
    for _ in range(3):
        _, subjects, _ = h.run([], [_unavailable()])
        assert subjects == []
    _, subjects, bodies = h.run([], [_unavailable()])
    assert subjects == ["[Job Scout] 1 new match"]
    assert main._GAVE_UP_NOTE in bodies[0] and "overloaded" not in bodies[0]
    assert h.verdict(jobs[1]["url"]) == "ERROR" and h.pending() == set()


def test_pending_only_run_is_evaluated():
    h = Harness()
    db.defer_job(_job(9), "e", count_attempt=False, path=h.db)
    calls, subjects, _ = h.run([], [_ok()])
    assert len(calls) == 1 and subjects == ["[Job Scout] 1 new match"]


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    print(f"=== {len(tests)} tests passed ===")
