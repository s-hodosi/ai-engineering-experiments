import csv
import os
from dotenv import load_dotenv

# 1. Load and Force Overrides
load_dotenv(override=True)

from crewai import Agent, Task, Crew, LLM
from crewai_tools import TavilySearchTool
from models import JobMatch, MarketResearch, CareerEvaluation, SalaryEstimation

_SALARY_DB_PATH = os.path.join(os.path.dirname(__file__), "salary_db.csv")

def _load_salary_reference(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Salary reference file not found: {path}")
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return ""
    headers = list(rows[0].keys())
    header_row = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    data_rows = [
        "| " + " | ".join(str(row.get(h, "")).strip() for h in headers) + " |"
        for row in rows
    ]
    return "\n".join([header_row, separator] + data_rows)

SALARY_REFERENCE_TABLE = _load_salary_reference(_SALARY_DB_PATH)

search = TavilySearchTool()

llm = LLM(model="gemini/gemini-2.5-flash", temperature=0.7)
llm_salary = LLM(model="gemini/gemini-2.5-flash", temperature=0.1)


job_agent = Agent(
    role="Technical Recruiter",
    goal="Evaluate candidate fit for a role",
    backstory="Skeptical and realistic senior recruiter specialized in software engineering hiring.",
    llm=llm
)

market_agent = Agent(
    role="Market Analyst",
    goal="Research company background and company culture",
    backstory="Industry analyst specialized in tech hiring trends.",
    tools=[search],
    llm=llm
)

salary_agent = Agent(
    role="Compensation Analyst",
    goal="Estimate realistic salary ranges for the job using multiple sources.",
    backstory="Expert in tech compensation analysis using public salary data sources like Glassdoor, Levels.fyi, LinkedIn and market reports. Your are very realistic and skeptical.",
    tools=[search],
    llm=llm_salary
)

career_agent = Agent(
    role="Career Advisor",
    goal="Evaluate career upside and risks",
    backstory="Career advisor helping engineers evaluate job opportunities. Your are very realistic and skeptical.",
    llm=llm
)


TASK_LABELS = [
    "Job match analysis",
    "Market research",
    "Salary estimation",
    "Career evaluation",
]


def run_agents(cv: str, jd: str, on_task_complete=None):

    task_counter = [0]

    def task_callback(task_output):
        idx = task_counter[0]
        if on_task_complete and idx < len(TASK_LABELS):
            on_task_complete({
                "task": f"task{idx + 1}",
                "label": TASK_LABELS[idx],
                "step": idx + 1,
                "total": 4,
            })
        task_counter[0] += 1

    task1 = Task(
        description="""
Evaluate how well the following CV matches the job description.

CANDIDATE CV:
{cv}

JOB DESCRIPTION:
{job_description}

Return JSON with:
match_score
key_matches
skill_gaps
seniority_estimate

Return ONLY valid JSON.
""",
        expected_output="JSON job match analysis",
        output_pydantic=JobMatch,
        agent=job_agent
    )

    task2 = Task(
        description="""
Research the company and job market.

JOB DESCRIPTION:
{job_description}

Determine:
- company summary
- likely company name
- company financial health
- company culture

Return ONLY valid JSON.
""",
        expected_output="JSON market research",
        output_pydantic=MarketResearch,
        agent=market_agent,
        context=[task1]
    )

    task3 = Task(
        description=f"""
Estimate the monthly gross base salary range for this leadership role in Budapest, Hungary.

JOB DESCRIPTION:
{{job_description}}

## Step 1 — Anchor on the reference data (primary source)

Below is a table of real 2025–2026 Budapest market offers for leadership roles.
Units: million HUF, gross monthly base salary.

{SALARY_REFERENCE_TABLE}

Find the 1–3 closest matching rows by domain, role type, and seniority level.
Use those rows as your primary anchor for the estimate.
If NO close match exists (e.g. the role is highly niche or an IC role not covered here),
set confidence to "low" and explain the gap in your reasoning.

## Step 2 — Adjust with web search

Use web search ONLY to adjust for factors not captured in the reference table:
- Specific company size or funding stage premium
- Rare tech stack premium (if applicable)
- Very recent market shift (post-2026 data)

Do NOT use US-based salary sources (Glassdoor, Levels.fyi) as primary anchors.

## Step 3 — Return your estimate

Return salary_low and salary_high as FULL INTEGERS IN HUF (multiply millions by 1,000,000).
Example: 2.3M HUF → 2300000

Set unit to exactly "monthly gross HUF".
Populate reasoning with: which reference rows you matched, seniority/domain adjustments made,
and any web search findings used.

Return ONLY valid JSON.
""",
        expected_output="Salary estimation in monthly gross HUF with reasoning",
        output_pydantic=SalaryEstimation,
        agent=salary_agent,
        context=[task1, task2]
    )

    task4 = Task(
        description="""
Using the job match analysis, market research, and salary estimation from previous tasks, evaluate the career opportunity.

CV:
{cv}

JOB DESCRIPTION:
{job_description}

Return ONLY valid JSON with exactly these fields:
- "offer_probability": a string estimating the realistic chance of getting an offer (e.g. "50%")
- "career_value": a string describing the career growth potential
- "risks": a list of strings, each describing a risk (e.g. ["risk 1", "risk 2"])
- "recommendation": a string with your overall recommendation

Do NOT include any text, explanation, or markdown outside the JSON object.
Return ONLY a raw JSON object.
""",
        expected_output="JSON career evaluation with offer_probability, career_value, risks, and recommendation",
        output_pydantic=CareerEvaluation,
        agent=career_agent,
        context=[task1, task2, task3]
    )

    crew = Crew(
        agents=[job_agent, market_agent, salary_agent, career_agent],
        tasks=[task1, task2, task3, task4],
        task_callback=task_callback,
        verbose=True
    )

    result = crew.kickoff(inputs={
        "cv": cv,
        "job_description": jd
    })

    combined = {}
    for task_output in result.tasks_output:
        if task_output.pydantic:
            combined.update(task_output.pydantic.model_dump())

    return combined