# Project Specification: Real-Time Postgres Log-Streamer GUI

## 1. Executive Summary
The goal is to build a high-performance, user-friendly GUI using **Reflex (Python)** that provides a live "Activity Feed" of PostgreSQL queries. Unlike standard monitors that poll system views, this application will dynamically configure Postgres to log all activity and stream those log files in real-time. It targets production-intensive environments where visibility into specific database activity is critical.

---

## 2. Technical Stack
*   **Frontend & Backend Framework:** [Reflex](https://reflex.dev/) (Pure Python web framework).
*   **Security:**  Python `keyring` library for secure credential storage
*   **Database Driver:** `asyncpg` (High-performance async driver).
*   **State Management:** Reflex State with `@rx.background` async tasks.
*   **Concurrency:** Python `asyncio` with  Semaphore (limit: 20)
*   **External Dependencies:** `Node.js` (for Reflex compilation), `psycopg2-binary` (optional fallback).

---

## 3. Modular Architecture
```text
pg_logger/
├── connections.json         # Stores IP, Port, DB, and Username history
├── rxconfig.py             # Reflex configuration
├── cleanup.py               # Standalone rollback script for emergency resets
└── pg_logger/
    ├── backend/
    │   ├── discovery.py     # Subnet scanning logic (Port 5432)
    │   ├── history_mgr.py   # CRUD for connections.json
    │   ├── log_parser.py    # Multi-line SQL reconstruction & Regex
    │   ├── log_engine.py    # Log tailing (pg_read_binary_file logic)
    │   └── config_mgr.py    # SQL execution (ALTER SYSTEM / SHOW)
    ├── frontend/
    │   ├── components.py    # Activity cards, Search bar, Play/Stop buttons
    │   ├── styles.py        # UI theme and layout constants
    │   └── overlays.py      # Restart warning & Login screens
    ├── state.py            # Main App State & Async background loops
    └── pg_logger.py        # App routing and entry point
```

---

## 4. Detailed Workflow & Requirements

### Phase 1: Instance Selection & Authentication
1.  **Discovery:** On launch, the app must:
    *   Load `connections.json` to show previous instances.
    *   Provide a "Scan Network" button to probe the local `/24` subnet.
    *   Uses Semaphore to limit concurrent probes to 20.
    **Flexible Scan:** Users can trigger a subnet scan. Added support for 
    **custom port ranges** (e.g., `5432-5435`) to identify instances on non-standard ports.
2.  **Authentication:**
    *   User selects an IP/Host and enters `Database Name`, `Username`, and `Password`.
    *   **Requirement:** Connection must be established as a **Superuser** (typically `postgres`).
    *   **Security:** Use OS Keyring to store/retrieve passwords.

### Phase 2: System Configuration Pre-Check (Step 1)
Upon successful login, the app must verify the logging state:
1.  **Check:** Run `SHOW logging_collector;`.
2.  **Logic:**
    *   If `on`: Proceed to Dashboard.
    *   If `off`: Execute `ALTER SYSTEM SET logging_collector = on;`.
3.  **UI Action:** If changed to `on`, display a persistent overlay: **"Critical: Restart Required. Please restart the Postgres service manually to enable logging."** Block all further actions until `SHOW logging_collector;` returns `on`.

### Phase 3: Query Stream Control (Step 2 & 4)
The Dashboard features a **Play/Stop** toggle:

**Play Button (Enable Streaming):**
*   Execute SQL:
    ```sql
    ALTER SYSTEM SET log_min_duration_statement = 0;
    ALTER SYSTEM SET log_line_prefix = '%m [%p] %u@%d ';
    SELECT pg_reload_conf();
    ```
*   **Backend Action:** Start an async background task to identify the latest log file via `pg_ls_logdir()` and begin tailing the file.
*   **Log Rotation Handling** Identify latest log and initialize 

**Stop Button (Disable Streaming):**
*   Execute SQL:
    ```sql
    ALTER SYSTEM RESET log_min_duration_statement;
    ALTER SYSTEM RESET log_line_prefix;
    SELECT pg_reload_conf();
    ```
*   **Backend Action:** Terminate the background log-reading task.

### Phase 4: Real-Time Stream Processing (Step 3)
1.  **Log Reader:**
*   **Tailing Logic:** Use `pg_read_binary_file` with byte offsets to read only new data, preventing memory issues with large log files.
*   **Multi-line Parsing:** Detect indented lines to append to previous SQL statements.
*   **Database Toggle:** Provide a "Show All Databases" vs "Current Database" filter.
*   **State Capping:** Limit frontend list to **1,000 entries** to prevent memory lag.

2.  **Filtering:** 
    *   **Database Filter:** Only show entries where the log's database name matches the user's initial selection.
    *   **Internal Filter:** Exclude the app’s own log-reading queries to prevent "infinite loop" noise.
3.  **UI Updates:** Push new queries to the top of the Reflex `rx.foreach` list.

### Phase 5: Inactivity Watchdog (Safety Trigger)
*   **Monitor:** Track user interaction (clicks/movements).
*   **Trigger:** If **10 minutes** pass without interaction:
    1.  Auto-execute **Stop Button** logic (Resets Postgres config).
    2.  Display **Popup:** "Session Paused: Logging disabled due to inactivity to protect disk space."
*   **Circuit Breaker:** Auto-stop if log growth exceeds **100MB/min** or disk space is **< 10%**.
*   **Hard Timeout:** Force-close session and reset config after **1 hour** total duration.
*   **Cleanup Script:** Standalone `cleanup.py` to reset Postgres settings if the main app crashes.

---

## 5. UI Features & UX Requirements
*   **Activity Feed:** Simplified cards showing `Timestamp`, `Username`, `Query Duration`, and a syntax-highlighted `SQL Snippet`.
*   **Clear Screen Button:** A button to purge the current frontend state list without stopping the stream.
*   **Find Module:** A real-time search input that filters the visible query list as the user types (matches against SQL text or User).
*   **Manual Restart Instructions:** Clear documentation or a modal explaining how to restart Postgres on common OS (Linux/Windows).
*   **Visual Feedback:** Syntax highlighting for SQL and status indicators for query duration.


---

## 6. Security & Performance Constraints
*   **Data Safety:** Ensure `ALTER SYSTEM RESET` is called on app exit or "Stop" to prevent logs from filling up server disk space.
*   **Performance:** Background polling must run at **200ms - 500ms** intervals using `asyncio` to ensure a "real-time" feel.
*   **Credential Handling:** Never save passwords in `connections.json`. Only store Host, Port, DB, and User.

---

## 7. Implementation Commands for Developers/AI
*   **Log Location:** `SELECT pg_ls_logdir();`
*   **File Reading:** `SELECT pg_read_binary_file(filename, offset, length);`
*   **Config Reload:** `SELECT pg_reload_conf();`
*   **Subnet Scan:** Use Python `socket` and `asyncio` for concurrent TCP probing.
*   **Log Pattern:** 
```
LOG_PATTERNS = {
    'statement': r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) \[(\d+)\] (\w+)@(\w+) (.*)$',
    'duration': r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) \[(\d+)\] (\w+)@(\w+) LOG:\s+duration:\s+([\d.]+)\s+ms',
    'continuation': r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) \[(\d+)\] (\w+)@(\w+) \s+(.*)$'
}
```
*   **Concurrency Handling:** Use `async with self:` in Reflex background tasks to ensure thread-safe state updates.
*   **Error Recovery:** Logic must handle Postgres restarts and connection drops during active streaming.
