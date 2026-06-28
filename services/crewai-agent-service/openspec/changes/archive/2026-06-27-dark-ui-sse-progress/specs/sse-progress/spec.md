## ADDED Requirements

### Requirement: Backend streams task progress over SSE
The `/analyze` endpoint SHALL return a `text/event-stream` response. It SHALL emit one `progress` event after each of the 4 CrewAI tasks completes, followed by a single `result` event containing the full combined output. If an error occurs during the crew run, it SHALL emit an `error` event and close the stream.

#### Scenario: Progress events emitted per task
- **WHEN** a client POSTs a valid CV and job description to `/analyze`
- **THEN** the server emits exactly 4 `progress` events in order, one per completed task, each containing `task`, `label`, `step` (1–4), and `total` (4)

#### Scenario: Result event closes the stream
- **WHEN** all 4 tasks have completed
- **THEN** the server emits one `result` event containing the full merged JSON output and then closes the stream

#### Scenario: Error event on crew failure
- **WHEN** an exception is raised during the crew run
- **THEN** the server emits an `error` event with a message field and closes the stream cleanly without leaving the client hanging

### Requirement: Frontend consumes SSE stream and shows per-task progress
The frontend SHALL use `fetch()` with `ReadableStream` to consume the SSE stream. It SHALL display a progress bar that advances 25% per completed task, and a step list showing each task's status as pending (·), in-progress (⟳), or complete (✓).

#### Scenario: Progress bar advances on each task completion
- **WHEN** a `progress` event is received with `step: N`
- **THEN** the progress bar fills to `N / total * 100`% and the Nth step in the list shows ✓

#### Scenario: In-progress indicator shown for active task
- **WHEN** step N has completed and step N+1 has not yet completed
- **THEN** step N+1 shows a spinner/in-progress indicator

#### Scenario: Result cards rendered on completion
- **WHEN** the `result` event is received
- **THEN** the progress UI is replaced by the 4 result cards (match, market, salary, career)

#### Scenario: Error shown to user on stream failure
- **WHEN** an `error` event is received
- **THEN** a visible error message is shown and the progress UI is cleared
