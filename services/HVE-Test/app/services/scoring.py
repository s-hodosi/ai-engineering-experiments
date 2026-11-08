from __future__ import annotations

from typing import Any

WEIGHTS = {
    "salary_fit": 0.25,
    "role_alignment": 0.25,
    "location_flexibility": 0.15,
    "growth_potential": 0.15,
    "company_fit": 0.10,
    "effort_to_apply": 0.10,
}


def evaluate_job(data: dict[str, Any]) -> dict[str, Any]:
    raw_scores = {
        "salary_fit": int(data.get("salary_fit", 0)),
        "role_alignment": int(data.get("role_alignment", 0)),
        "location_flexibility": int(data.get("location_flexibility", 0)),
        "growth_potential": int(data.get("growth_potential", 0)),
        "company_fit": int(data.get("company_fit", 0)),
        "effort_to_apply": int(data.get("effort_to_apply", 0)),
    }

    total = 0.0
    for key, score in raw_scores.items():
        total += max(0, min(5, score)) * WEIGHTS[key]

    score = round(total * 20, 2)
    return {
        "title": data.get("title", "Untitled"),
        "company": data.get("company", "Unknown"),
        "location": data.get("location", "Unknown"),
        "summary": data.get("summary", ""),
        "raw_scores": raw_scores,
        "score": score,
        "recommendation": recommendation_for_score(score),
    }


def recommendation_for_score(score: float) -> str:
    if score >= 85:
        return "Strong fit"
    if score >= 65:
        return "Good fit"
    if score >= 45:
        return "Moderate fit"
    return "Low fit"
