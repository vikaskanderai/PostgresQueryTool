# Development Framework & Rules

## 1. Architectural Integrity
*   **Strict Modularity:** Logic must remain in `backend/`, UI in `frontend/`, and shared state in `state.py`.
*   **Single Source of Truth:** All database metadata must flow through the `rx.State` class; do not store local component states for global data.

## 2. Coding Standards
*   **Async-First:** All database I/O and network scanning must use `async/await` with `asyncpg`. No blocking `psycopg2` calls in the main thread.
*   **Thread Safety:** Every state modification within a background task must be wrapped in `async with self:`.
*   **Type Hinting:** Use Python type hints for all function signatures to ensure clarity for AI and developers.

## 3. Database & Security
*   **Parameterized Queries:** No f-strings for SQL. Use `asyncpg` parameterization to prevent injection.
*   **Credential Safety:** Zero plain-text passwords in logs or `connections.json`. Use the `keyring` library for retrieval.
*   **Superuser Guard:** Every session must begin with a privilege check. If `usesuper` is false, the app must hard-lock.

## 4. Production Safety (Critical)
*   **The "Clean Exit" Rule:** Every `ALTER SYSTEM` command must have a corresponding `RESET` logic mapped to the `Stop` button and `cleanup.py`.
*   **Resource Throttling:** Network scans must use `asyncio.Semaphore(20)` to avoid socket exhaustion.
*   **Memory Guard:** Frontend lists must never exceed 1,000 items; slice data immediately upon ingestion.

## 5. UI & UX Logic
*   **Non-Blocking UI:** Long-running tasks (scanning/polling) must run in `@rx.background` to keep the interface responsive.
*   **Stateful Overlays:** System-critical states (Restart required, Inactivity pause) must use full-screen overlays that prevent user bypass.

## 6. Error Handling
*   **Graceful Degradation:** If the DB connection drops, the app must show a "Reconnecting" status rather than crashing.
*   **Regex Robustness:** The log parser must handle malformed lines or incomplete multi-line strings without breaking the streaming loop.