import asyncio
import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agents import run_agents

app = FastAPI()


class JobInput(BaseModel):
    cv: str
    job_description: str


@app.post("/analyze")
async def analyze(data: JobInput):
    async def event_stream():
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def on_task_complete(event):
            loop.call_soon_threadsafe(queue.put_nowait, ("progress", event))

        def run_in_thread():
            try:
                result = run_agents(data.cv, data.job_description, on_task_complete)
                loop.call_soon_threadsafe(queue.put_nowait, ("result", result))
            except Exception as e:
                loop.call_soon_threadsafe(queue.put_nowait, ("error", {"message": str(e)}))

        loop.run_in_executor(None, run_in_thread)

        while True:
            event_type, payload = await queue.get()
            yield f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"
            if event_type in ("result", "error"):
                break

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# mount static AFTER api routes
app.mount("/", StaticFiles(directory="static", html=True), name="static")
