# 🐘 SPHURANA - Smart Postgres Helper for Unified Real-time Activity, Navigation, and Artifacts

A high-performance, real-time PostgreSQL query monitoring and script generation tool built with **Reflex** (Python web framework). Monitor live database activity, analyze query patterns, and generate DDL scripts—all through an elegant, modern web interface.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![PostgreSQL](https://img.shields.io/badge/postgresql-12+-316192.svg)

## ✨ Features

### 🔍 Real-Time Query Monitoring
- **Live Activity Feed** - Stream PostgreSQL queries with <300ms latency
- **Syntax Highlighting** - SQL keywords highlighted for instant readability
- **Smart Filtering** - Search by SQL text, username, database, or duration
- **Copy to Clipboard** - One-click SQL extraction for debugging
- **Echo Prevention** - Automatically filters out the app's own monitoring queries
- **Memory Protection** - Auto-limited to 1,000 most recent queries

### 🌐 Network Discovery
- **Subnet Scanner** - Automatically discover PostgreSQL instances on your network
- **Custom Port Ranges** - Scan non-standard ports (e.g., 5432-5435)
- **Connection History** - Quick access to previously used database connections
- **Concurrent Scanning** - Smart concurrency with 20-connection semaphore

### 🔧 Script Generation
- **DDL Generator** - Create table DDL scripts from existing databases
- **Batch Processing** - Generate scripts for multiple tables at once
- **Production-Ready** - Formatted SQL with proper indentation and comments

### 🔐 Security & Performance
- **Keyring Integration** - Secure OS-level password storage (no plaintext)
- **Async Architecture** - Built on `asyncio` and `asyncpg` for maximum performance
- **Auto-Safety Features** - Inactivity watchdog prevents disk space issues
- **Emergency Cleanup** - Standalone rollback script for crash recovery

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

The fastest way to try the application with a pre-configured test database:

```bash
# Clone the repository
git clone <repository-url>
cd "Postgres Logger/pg_logger"

# Start everything with docker-compose
docker-compose up --build

# Access the application
# Open browser: http://localhost:3000

# Use these test credentials:
#   Host: localhost
#   Port: 5432
#   Database: testdb
#   Username: postgres
#   Password: test123
```

The Docker setup includes:
- PostgreSQL 17 (Alpine) with pre-enabled logging
- Sample `testdb` database with seed data
- Fully configured Reflex application
- Health checks for database readiness

### Option 2: Manual Installation

For development or connecting to existing PostgreSQL instances:

```bash
# Prerequisites
# - Python 3.11+
# - Node.js 16+ (for Reflex compilation)
# - PostgreSQL 12+ (running separately)

# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
cd pg_logger
pip install -r requirements.txt

# 3. Initialize Reflex
reflex init

# 4. Run the application
reflex run

# Access at http://localhost:3000
```

---

## 📁 Project Structure

```
PostgresQueryTool/
└── Postgres Logger/
    ├── pg_logger/                      # Main application directory
    │   ├── pg_logger/                  # Core application code
    │   │   ├── backend/                # Business logic layer
    │   │   │   ├── discovery.py        # Network subnet scanning
    │   │   │   ├── history_mgr.py      # Connection history (JSON persistence)
    │   │   │   ├── config_mgr.py       # PostgreSQL config management + keyring
    │   │   │   ├── log_engine.py       # Log file tailing (pg_read_binary_file)
    │   │   │   ├── log_parser.py       # Multi-line SQL reconstruction
    │   │   │   ├── script_engine.py    # DDL generation engine
    │   │   │   └── ddl_template.sql    # DDL script template
    │   │   ├── frontend/               # UI components
    │   │   │   ├── styles.py           # Design system (colors, spacing, themes)
    │   │   │   ├── components.py       # Activity feed, search bar, controls
    │   │   │   ├── overlays.py         # Modals, warnings, restart notices
    │   │   │   ├── selector.py         # Feature selection UI
    │   │   │   └── script_ui.py        # Script generator interface
    │   │   ├── state.py                # Reflex state management + async tasks
    │   │   └── pg_logger.py            # App entry point & routing
    │   ├── assets/                     # Static files
    │   │   └── stylesheets.css         # Global CSS overrides
    │   ├── connections.json            # Connection history (auto-generated)
    │   ├── docker-compose.yml          # Docker orchestration
    │   ├── Dockerfile                  # App container definition
    │   ├── seed.sql                    # Test database schema
    │   ├── cleanup.py                  # Emergency rollback utility
    │   ├── requirements.txt            # Python dependencies
    │   └── rxconfig.py                 # Reflex configuration
    ├── Project_Specification.md        # Detailed technical specs
    ├── Development Framework & Rules.md
    └── README.md                       # This file
```

---

## 🎯 How It Works

### 1. **Authentication & Discovery**

When you launch the app, you can:
- **Scan your network** for PostgreSQL instances (port 5432 by default)
- **Select from connection history** for quick reconnection
- **Manually enter** connection details

**Security Note**: You must connect with a **superuser account** (typically `postgres`) to modify logging settings.

### 2. **Automatic Configuration**

Upon successful connection, the app:
1. Checks if `logging_collector` is enabled
2. If disabled, executes `ALTER SYSTEM SET logging_collector = on`
3. Displays a restart warning if configuration changes require service restart
4. Polls the server until restart is detected

### 3. **Real-Time Streaming**

When you click **Play**:
```sql
-- Enables comprehensive logging
ALTER SYSTEM SET log_min_duration_statement = 0;
ALTER SYSTEM SET log_line_prefix = '%m [%p] %u@%d ';
SELECT pg_reload_conf();
```

The backend then:
- Identifies the latest log file via `pg_ls_logdir()`
- Uses `pg_read_binary_file(filename, offset, length)` to tail the file
- Parses multi-line SQL statements using regex patterns
- Pushes updates to the frontend every 300ms via async background tasks

### 4. **Safety Features**

The app automatically:
- **Stops streaming** after 10 minutes of user inactivity
- **Resets configuration** when you click Stop or logout
- **Caps memory usage** to 1,000 most recent queries
- **Filters self-queries** to prevent infinite monitoring loops

**Emergency Cleanup**: If the app crashes, run `python cleanup.py` to reset PostgreSQL logging settings.

---

## 🔧 Usage Guide

### Query Monitoring

1. **Connect** to your PostgreSQL instance
2. Select **"Monitor"** from the feature menu
3. Click **Play** to start streaming
4. Use the **search bar** to filter by:
   - SQL text (e.g., `SELECT * FROM users`)
   - Username (e.g., `admin`)
   - Database name
   - Minimum duration (e.g., `>100ms`)
5. Click **Copy** on any query card to copy SQL to clipboard
6. Click **Clear** to purge the current feed (stream continues)
7. Click **Stop** when done (resets PostgreSQL config)

### Script Generation

1. **Connect** to your PostgreSQL instance
2. Select **"Script Generator"** from the feature menu
3. **Select schema** from dropdown
4. **Choose tables** you want to generate DDL for
5. Click **Generate Scripts**
6. **Download** or **copy** the generated SQL

---

## 🛠️ Configuration

### Environment Variables

For Docker deployments, customize `docker-compose.yml`:

```yaml
environment:
  - DATABASE_URL=postgresql://user:pass@host:5432/dbname
  - PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring  # Disable keyring in containers
```

### Reflex Configuration

Edit `rxconfig.py` to customize:

```python
config = rx.Config(
    app_name="pg_logger",
    port=3000,          # Frontend port
    backend_port=8000,  # Backend API port
)
```

### Logging Patterns

The app uses these regex patterns for log parsing (defined in `backend/log_parser.py`):

```python
LOG_PATTERNS = {
    'statement': r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) \[(\d+)\] (\w+)@(\w+) (.*)$',
    'duration': r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) \[(\d+)\] (\w+)@(\w+) LOG:\s+duration:\s+([\d.]+)\s+ms',
    'continuation': r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) \[(\d+)\] (\w+)@(\w+) \s+(.*)$'
}
```

---

## 🐳 Docker Details

### Services

- **`postgres`**: PostgreSQL 17-alpine with pre-configured logging
  - Port: `5433:5432` (mapped to avoid local conflicts)
  - Credentials: `postgres/test123`
  - Database: `testdb`
  - Persistent volume: `postgres_data`

- **`app`**: Reflex application
  - Ports: `3000` (frontend), `8000` (backend API)
  - Auto-restarts on code changes (volume mounted)
  - Waits for database health check before starting

### Commands

```bash
# Start in background
docker-compose up -d

# View logs
docker-compose logs -f app

# Rebuild after code changes
docker-compose up --build

# Stop everything
docker-compose down

# Remove volumes (clean slate)
docker-compose down -v
```

See [DOCKER_TESTING.md](pg_logger/DOCKER_TESTING.md) for comprehensive testing scenarios.

---

## 🔒 Security Considerations

### Keyring Storage

By default, the app uses the OS keyring to store passwords:
- **Linux**: `Secret Service API` or `gnome-keyring`
- **macOS**: `Keychain`
- **Windows**: `Windows Credential Locker`

To disable keyring (e.g., in Docker):
```bash
export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring
```

### Superuser Requirement

The app requires superuser privileges to:
- Execute `ALTER SYSTEM` commands
- Access `pg_read_binary_file()` function
- Query `pg_ls_logdir()` function

**Best Practice**: Create a dedicated monitoring superuser instead of using the main `postgres` account.

### Network Scanning

The subnet scanner uses `asyncio` to probe port 5432 on the local `/24` subnet. This may trigger IDS alerts in security-sensitive environments.

---

## 📊 Performance

### Benchmarks

- **Startup Time**: <2s (without network scan)
- **Query Latency**: <300ms from log write to UI display
- **Memory Usage**: ~50MB base + ~1KB per query (capped at 1,000 queries)
- **Network Scan**: ~10s for /24 subnet (254 IPs with 20 concurrent connections)

### Optimization Tips

1. **Reduce Polling Interval**: Edit `state.py` to adjust the 300ms background loop
2. **Increase Query Cap**: Modify `MAX_QUERIES = 1000` in `state.py`
3. **Filter at Source**: Use the database filter to reduce parsing overhead

---

## 🧪 Testing

### Manual Testing with Docker

1. Start the Docker environment:
   ```bash
   docker-compose up --build
   ```

2. Connect to `localhost:5432` with credentials from docker-compose.yml

3. Generate test activity:
   ```bash
   docker exec -it pg_logger_db psql -U postgres -d testdb -c "SELECT * FROM sample_table;"
   ```

4. Verify queries appear in the activity feed

### Testing Cleanup Script

If the app crashes while streaming is active:

```bash
cd pg_logger
python cleanup.py
# Enter connection details when prompted
# Verifies that logging settings are reset
```

---

## 🐛 Troubleshooting

### "Connection Refused" Error

**Cause**: PostgreSQL not running or wrong host/port

**Solution**:
```bash
# Check PostgreSQL status
sudo systemctl status postgresql  # Linux
brew services list                # macOS

# Verify port
netstat -nltp | grep 5432
```

### "Must be Superuser" Error

**Cause**: Connected user lacks superuser privileges

**Solution**: Connect with the `postgres` user or create a superuser:
```sql
CREATE USER monitor WITH SUPERUSER PASSWORD 'secure_password';
```

### "Restart Required" Warning Won't Dismiss

**Cause**: PostgreSQL service not restarted after config change

**Solution**:
```bash
# Linux
sudo systemctl restart postgresql

# Docker
docker-compose restart postgres

# macOS
brew services restart postgresql
```

### Logs Not Appearing in Feed

1. **Check logging is enabled**:
   ```sql
   SHOW logging_collector;  -- Should be 'on'
   SHOW log_min_duration_statement;  -- Should be '0'
   ```

2. **Verify log directory permissions**:
   ```sql
   SELECT setting FROM pg_settings WHERE name = 'log_directory';
   -- Default: 'log' (relative to data directory)
   ```

3. **Check for log rotation**:
   The app auto-detects new log files, but manual rotation during active streaming may cause delays.

---

## 🤝 Contributing

Contributions are welcome! This project follows a modular architecture:

### Adding a New Feature

1. **Backend Logic**: Add to `pg_logger/backend/`
2. **UI Component**: Add to `pg_logger/frontend/`
3. **State Management**: Update `pg_logger/state.py`
4. **Routing**: Modify `pg_logger/pg_logger.py`

### Code Style

- **Python**: Follow PEP 8
- **Reflex Components**: Use functional component style
- **Async Code**: Always use `async with self:` for state mutations in background tasks

---

## 📄 License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

## 📚 Additional Resources

- **[Project Specification](Project_Specification.md)**: Detailed technical requirements
- **[Development Framework](Development%20Framework%20&%20Rules.md)**: Coding standards and patterns
- **[Docker Testing Guide](pg_logger/DOCKER_TESTING.md)**: Comprehensive test scenarios
- **[Reflex Documentation](https://reflex.dev/docs)**: Official Reflex framework docs
- **[PostgreSQL Logging](https://www.postgresql.org/docs/current/runtime-config-logging.html)**: Official logging documentation

---

## 🙏 Acknowledgments

- Built with [Reflex](https://reflex.dev/) - Pure Python web framework
- Uses [asyncpg](https://github.com/MagicStack/asyncpg) (fastest PostgreSQL driver for Python)
- UI inspired by modern database monitoring tools

---

## 📧 Support

For questions, issues, or feature requests, please refer to the [Project Specification](Project_Specification.md) or open an issue in the repository.

---

**Happy Monitoring! 🚀**
