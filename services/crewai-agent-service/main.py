from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from agents import run_agents

app = FastAPI()

class JobInput(BaseModel):
    cv: str
    job_description: str


@app.post("/analyze")
def analyze(data: JobInput):

    result = run_agents(
        data.cv,
        data.job_description
    )

    return {"result": result}

# mount static AFTER api routes
app.mount("/", StaticFiles(directory="static", html=True), name="static")