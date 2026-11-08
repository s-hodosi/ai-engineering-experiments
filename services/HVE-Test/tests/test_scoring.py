from app.services.scoring import evaluate_job, recommendation_for_score


def test_recommendation_for_score():
    assert recommendation_for_score(90) == "Strong fit"
    assert recommendation_for_score(75) == "Good fit"
    assert recommendation_for_score(55) == "Moderate fit"
    assert recommendation_for_score(20) == "Low fit"


def test_evaluate_job_uses_weighted_score():
    result = evaluate_job(
        {
            "title": "Engineer",
            "company": "Contoso",
            "location": "Remote",
            "summary": "A great role",
            "salary_fit": 5,
            "role_alignment": 5,
            "location_flexibility": 3,
            "growth_potential": 4,
            "company_fit": 3,
            "effort_to_apply": 2,
        }
    )

    assert result["score"] == 81.0
    assert result["recommendation"] == "Good fit"
