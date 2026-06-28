## 1. Backend — SSE streaming endpoint

- [x] 1.1 Add `task_callback` to `run_agents()` in `agents.py`: accept a callback parameter and pass it to `Crew(task_callback=...)`
- [x] 1.2 Define the 4 task labels map in `agents.py` (e.g. `{"task1": "Job match analysis", ...}`) used by the callback to emit human-readable labels
- [x] 1.3 Rewrite `POST /analyze` in `main.py` to return `StreamingResponse(media_type="text/event-stream")`
- [x] 1.4 Implement the async SSE generator: create `asyncio.Queue`, run `crew.kickoff()` in `run_in_executor`, wire `task_callback` to post `progress` events onto the queue via `call_soon_threadsafe`
- [x] 1.5 Emit `result` event after crew completes with the merged JSON payload
- [x] 1.6 Catch exceptions in the thread and emit an `error` event before closing the stream

## 2. Frontend — SSE consumer and progress UI

- [x] 2.1 Replace the `fetch` call in `run()` with a streaming reader: use `response.body.getReader()` and a `TextDecoder` to parse SSE lines
- [x] 2.2 Implement SSE line parser: accumulate chunks, split on `\n\n`, extract `event:` and `data:` fields
- [x] 2.3 On `progress` event: advance the progress bar to `step / total * 100`% and update the step list (· → ✓ for completed, ⟳ for current)
- [x] 2.4 On `result` event: hide the progress UI and render the 4 result cards (existing card rendering logic)
- [x] 2.5 On `error` event: display an error message and reset the UI

## 3. Frontend — Dark theme

- [x] 3.1 Define CSS custom properties on `:root` for the warm dark palette (`--bg`, `--surface`, `--surface-2`, `--border`, `--text`, `--muted`, `--accent`, `--success`)
- [x] 3.2 Apply palette to `body`, `.card`, `textarea`, `button`, `h1`, `h3`, `h4`, `ul li`, and `.loading`
- [x] 3.3 Style the progress bar container and fill using `--surface-2` / `--accent`
- [x] 3.4 Style the step list: pending (·, `--muted`), in-progress (⟳, `--accent`), complete (✓, `--success`)
- [x] 3.5 Add `textarea:focus` outline using `--accent` and remove default browser outline
