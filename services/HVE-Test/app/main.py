from fastapi import FastAPI, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.db import get_evaluation, list_evaluations, save_evaluation
from app.services.importer import extract_job_details
from app.services.scoring import evaluate_job, recommendation_for_score

app = FastAPI(title="Job Opportunity Evaluator")
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "result": None, "history": list_evaluations()},
    )


@app.post("/import")
def import_job(request: Request, url: str = Form(...)):
    import requests

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        details = extract_job_details(url, response.text)
    except Exception:
        details = {
            "title": "",
            "company": "",
            "location": "",
            "summary": "",
        }

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "result": None,
            "imported": details,
            "history": list_evaluations(),
        },
    )


@app.post("/evaluate")
def evaluate(
    request: Request,
    title: str = Form(...),
    company: str = Form(...),
    location: str = Form(...),
    summary: str = Form(default=""),
    salary_fit: int = Form(...),
    role_alignment: int = Form(...),
    location_flexibility: int = Form(...),
    growth_potential: int = Form(...),
    company_fit: int = Form(...),
    effort_to_apply: int = Form(...),
):
    result = evaluate_job(
        {
            "title": title,
            "company": company,
            "location": location,
            "summary": summary,
            "salary_fit": salary_fit,
            "role_alignment": role_alignment,
            "location_flexibility": location_flexibility,
            "growth_potential": growth_potential,
            "company_fit": company_fit,
            "effort_to_apply": effort_to_apply,
        }
    )
    save_evaluation(result)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "result": result,
            "recommendation": recommendation_for_score(result["score"]),
            "history": list_evaluations(),
        },
    )


@app.get("/history")
def history(request: Request):
    return templates.TemplateResponse(
        "history.html",
        {"request": request, "evaluations": list_evaluations()},
    )


@app.get("/history/{evaluation_id}")
def view_evaluation(request: Request, evaluation_id: int):
    evaluation = get_evaluation(evaluation_id)
    return templates.TemplateResponse(
        "history_detail.html",
        {"request": request, "evaluation": evaluation},
    )


@app.get("/health")
def health():
    return {"status": "ok"}
