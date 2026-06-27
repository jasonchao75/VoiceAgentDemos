# Findings & Research Log

## Asynchronous Task Cancellation in Python
- FastAPI background tasks run in the server event loop. To cancel them gracefully, we check a cancellation flag in the database before starting each file's transcription. This ensures that stopping a run of 100 files will immediately prevent the remaining files from starting, without violently interrupting the currently running websocket connection of the active 3-5 concurrent files (which avoids corrupting connections or leaving databases in invalid states).

## Smart Resume Mechanism
- To resume a benchmark run, the endpoint `/api/benchmark/resume/{run_id}` will:
  1. Retrieve all file results associated with the `run_id`.
  2. Find files whose status is `pending`, `error`, or `interrupted`.
  3. Filter out files that are already `completed`.
  4. Trigger `run_benchmark` with the filtered list, allowing it to continue right where it left off.
