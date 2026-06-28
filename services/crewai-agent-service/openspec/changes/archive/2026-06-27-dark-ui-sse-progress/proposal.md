## Why

The current UI uses a bright white theme that is uncomfortable for extended use, especially in low-light environments. The analysis also blocks silently with a plain "Analyzing..." message, giving no feedback during a multi-agent run that can take 30–90 seconds.

## What Changes

- Replace the current light theme with a warm dark palette across all UI elements (body, cards, inputs, buttons)
- Add real per-task progress feedback: a progress bar and step list that advances as each of the 4 CrewAI tasks completes
- Convert the `/analyze` endpoint from a blocking JSON response to a Server-Sent Events (SSE) stream that emits task completion events followed by the final result
- Replace the frontend `fetch` call with a streaming reader that consumes SSE events and updates the UI incrementally

## Capabilities

### New Capabilities

- `sse-progress`: Backend streams task completion events over SSE; frontend consumes them to drive a real-time progress bar and step status list
- `dark-theme`: Warm dark color palette applied to all UI elements for reduced eye strain

### Modified Capabilities

*(none — no existing spec files exist in this project)*

## Impact

- `main.py`: `/analyze` endpoint changes from `JSONResponse` to `StreamingResponse` with `text/event-stream`
- `agents.py`: `run_agents()` gains a `task_callback` parameter wired into `Crew`; callback puts events onto an `asyncio.Queue`
- `static/index.html`: Full CSS restyle + JS rewrite to consume SSE stream and render incremental progress
- New dependency pattern: `asyncio.Queue` bridge between the sync CrewAI thread and the async FastAPI generator
- No new packages required — FastAPI's `StreamingResponse` and browser `fetch` streaming are sufficient
