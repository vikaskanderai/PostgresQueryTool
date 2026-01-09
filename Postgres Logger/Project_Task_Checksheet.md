Here is the **Developer Checklist**

### **Phase 0: Prerequisites & Project Setup**
- [ ] Verify Python 3.8+, Node.js 14+, and Postgres 10+ are installed.
- [ ] Create and activate virtual environment: `python -m venv venv`.
- [ ] Initialize Reflex project: `reflex init`.
- [ ] Create `rxconfig.py` with app name, port 3000, and API URL.
- [ ] Install dependencies: `pip install reflex asyncpg keyring psycopg2-binary`.

### **Phase 1: Discovery & History**
- [ ] Implement `backend/discovery.py`:
    - [ ] Logic to extract base IP from local interface.
    - [ ] Async scanner with `asyncio.Semaphore(20)` and 1.5s timeout per host.
    - [ ] Return list of `{host, port, status}` dicts.
- [ ] Implement `backend/history_mgr.py`:
    - [ ] CRUD for `connections.json` (exclude passwords).

### **Phase 2: Core Backend, Auth & Overlays**
- [ ] Setup `backend/config_mgr.py`:
    - [ ] `asyncpg` pool with `keyring` integration.
    - [ ] Validate Superuser via `SELECT usesuper FROM pg_user WHERE usename = current_user`.
- [ ] Create `frontend/overlays.py`:
    - [ ] Implement Restart Warning, Inactivity Pause, and Circuit Breaker alert overlays.
- [ ] Implement **Step 1 Logic**:
    - [ ] Execute `ALTER SYSTEM SET logging_collector = on;` and poll every 5s until 'on'.

### **Phase 3: Query Stream Control**
- [ ] Implement **Play Button** logic:
    - [ ] Execute `ALTER SYSTEM` commands + `SELECT pg_reload_conf();`.
    - [ ] Store `session_start_timestamp` and identify starting log file/byte offset.
- [ ] Implement **Stop Button** logic:
    - [ ] Execute `ALTER SYSTEM RESET` commands + `SELECT pg_reload_conf();`.

### **Phase 4: Log Engine & Parsing**
- [ ] Implement `backend/log_engine.py`:
    - [ ] Log rotation handling (current file vs latest file check).
- [ ] Implement `backend/log_parser.py`:
    - [ ] Store `pg_backend_pid()` on connect to filter out app-specific queries.
    - [ ] Apply 3-pattern Regex and merge multi-line SQL strings.

### **Phase 5: State & Dashboard UI**
- [ ] Setup `state.py`:
    - [ ] `@rx.background` task with `async with self:` updates.
    - [ ] State Capping: `self.queries = self.queries[:1000]` applied after each batch.
- [ ] Create `frontend/styles.py`:
    - [ ] Define color palette, card styles, and duration-based status indicators.
- [ ] Build **Dashboard UI**:
    - [ ] `rx.foreach` feed with syntax highlighting.
    - [ ] Toggle for "Show All Databases" vs "Current Database".

### **Phase 6: Safety Rails & Watchdogs**
- [ ] Implement **Inactivity Watchdog**:
    - [ ] UI `on_click` handlers to update `last_activity` timestamp.
    - [ ] Auto-stop after 10 minutes of idle time.
- [ ] Implement **Circuit Breaker**:
    - [ ] Monitor bytes-per-minute (>100MB/min) and disk usage (>90%).
- [ ] Implement **Hard Timeout**:
    - [ ] Force-reset and logout after 1 hour session time.

### **Phase 7: Finalization**
- [ ] Create `cleanup.py` with SIGINT/SIGTERM handlers and CLI usage instructions.
- [ ] Implement `audit.log` to record all `ALTER SYSTEM` executions.

### **Phase 8: Validation (Final Testing)**
- [ ] **Critical Tests:** 
    - [ ] Non-superuser rejection.
    - [ ] Postgres 9.x version rejection.
    - [ ] Log rotation during active stream.
    - [ ] 10-minute inactivity auto-shutdown.
    - [ ] `cleanup.py` functionality after forced app crash.

### **Phase 9: Documentation**
- [ ] Create README.md with installation, venv setup, and OS-specific restart commands.
- [ ] Document Regex patterns and safety threshold rationale.

**This checklist is ready for handoff.**