## Context

The service runs 4 sequential CrewAI tasks (job match → market research → salary estimation → career evaluation). Currently `POST /analyze` blocks until all 4 complete and returns a single JSON response. The frontend shows a static "Analyzing..." message during the entire wait, which can be 30–90 seconds. Users have no feedback on whether the system is working or stuck.

The frontend is a single `index.html` with inline CSS and JS — no build toolchain, no framework. Changes must be self-contained in that file plus `main.py` / `agents.py`.

## Goals / Non-Goals

**Goals:**
- Stream per-task progress events from backend to frontend as each CrewAI task completes
- Show a progress bar advancing 25% per task, with a labeled step list showing ✓/⟳/· states
- Apply a warm dark color palette to all UI elements
- No new Python packages required

**Non-Goals:**
- Streaming partial text output from individual LLM calls (would require deeper CrewAI hooks)
- Persisting analysis history or results
- Authentication, multi-user sessions, or job queuing
- Light/dark theme toggle

## Decisions

### D1: SSE via `StreamingResponse` + `fetch` streaming (not `EventSource`)

**Decision**: Use `POST /analyze` returning `StreamingResponse(media_type="text/event-stream")`, consumed on the frontend with `fetch()` + `ReadableStream`.

**Why not `EventSource`**: Native `EventSource` only supports GET requests. CVs and job descriptions are large text blobs — passing them as query parameters is impractical and unreliable.

**Why not a session/poll pattern**: Would require server-side state (storing job results keyed by ID), adding complexity with no benefit for a single-user local tool.

**Tradeoff**: `fetch` streaming is slightly more verbose JS than `EventSource`, but well-supported in all modern browsers.

### D2: `asyncio.Queue` bridge between sync CrewAI thread and async FastAPI generator

**Decision**: Run `crew.kickoff()` in a `ThreadPoolExecutor` via `asyncio.get_event_loop().run_in_executor()`. Pass a `task_callback` that calls `loop.call_soon_threadsafe(queue.put_nowait, event)` to safely post events from the sync thread into the async event loop.

**Why**: CrewAI's `kickoff()` is synchronous and blocking. FastAPI's SSE generator must be async to yield events while the crew runs. A `Queue` is the standard bridge.

**Sentinel value**: When the thread finishes, put a sentinel (`None` or a special `done` event) on the queue so the generator knows to close the stream.

### D3: Warm dark palette — no CSS framework

**Decision**: Define CSS custom properties (`--bg`, `--surface`, `--text`, etc.) on `:root` and reference them throughout. No Tailwind, no external stylesheet.

**Why**: The file is already self-contained inline CSS. CSS variables keep the palette in one place without adding a build step or external dependency.

**Chosen palette**:
```
--bg:        #1a1714   dark warm brown (body)
--surface:   #242220   warm charcoal (cards)
--surface-2: #2e2b28   slightly lighter (inputs, hover)
--border:    #3a3530   earthy separator
--text:      #ede8e0   warm white (primary)
--muted:     #9a9088   warm gray (labels, secondary)
--accent:    #60a5fa   lighter blue (button, progress)
--success:   #4ade80   green (completed steps)
```

### D4: SSE event format

Two event types over the stream:

```
event: progress
data: {"task": "job_match", "label": "Job match analysis", "step": 1, "total": 4}

event: result
data: {"match_score": 72, "key_matches": [...], ...}
```

The frontend accumulates `progress` events to drive the bar and step list, then on `result` renders the cards and clears the progress UI.

## Risks / Trade-offs

- **Long-running request timeout** → If a proxy (nginx, etc.) sits in front, it may close SSE connections after its default timeout. Mitigation: send a heartbeat comment (`: keep-alive\n\n`) every 15s. Not needed for local dev.
- **CrewAI `task_callback` API stability** → This is a supported `Crew` parameter in 1.x but could change. Mitigation: it's a thin wrapper; easy to swap for a step_callback if needed.
- **Browser `fetch` streaming** → Fully supported in all modern browsers. Not an issue for a personal tool.
- **Error handling** → If the crew throws mid-run, the exception must be caught in the thread and emitted as an `event: error` before closing the stream, otherwise the frontend hangs.
