# Task Plan: Advanced Background Running, Stop & Resume for Benchmark Runs

## Objective
Implement a robust, commercial-grade asynchronous task management system for benchmarking runs, including:
1. **Background Running:** Allowing users to switch pages while benchmarks run silently in the background, with a floating status indicator in the header of all pages.
2. **Graceful Stop:** Adding a Stop button in the History dashboard to cancel active benchmark runs.
3. **Smart Resume:** Adding a Continue button in the History dashboard to resume cancelled or interrupted runs, skipping already completed files.

## Phases of Implementation

### Phase 1: Database and Backend Support for Cancel & Resume
- [ ] Add `interrupted` and `cancelled` states in `database.py`.
- [ ] Implement backend endpoint `/api/benchmark/stop/{run_id}` to mark a run as `cancelled`.
- [ ] Implement backend endpoint `/api/benchmark/resume/{run_id}` to restart remaining (non-completed) files for a run.
- [ ] Update `run_benchmark` in `benchmark_runner.py` to check for cancellations before processing each file.

### Phase 2: Frontend Global Background Running & Awareness
- [ ] Add a floating background running status indicator in the header of all pages (`index.html`, `benchmark.html`, `history.html`, `config.html`).
- [ ] Create a shared JS logic/helper to check for active runs periodically (polling) and update the header indicator.
- [ ] In `benchmark.html`, show a confirmation dialog or toast if the user leaves the page while a run is active.

### Phase 3: History Page Stop & Continue Buttons
- [ ] Add `Stop` and `Continue` buttons in `history.html`'s benchmark runs table.
- [ ] Update `history.js` to implement click handlers for stopping and resuming.
- [ ] Make sure the modal results view reflects the correct status.

## Verification Checklist
- [ ] Syntax compilation check on changed Python files.
- [ ] Test stop functionality locally/syntactically.
- [ ] Verify database state changes under test inputs.
- [ ] Ensure all front-end assets load correctly without console errors.
