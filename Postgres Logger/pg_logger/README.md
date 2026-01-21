# PostgreSQL Log Streamer

Real-time PostgreSQL query monitoring application built with Reflex.

## Features

✅ **Network Discovery** - Scan local network for PostgreSQL instances  
✅ **Secure Authentication** - Keyring-based password storage  
✅ **Real-time Streaming** - Live query feed with 300ms latency  
✅ **Smart Filtering** - Search by SQL, user, database with duration filters  
✅ **Syntax Highlighting** - SQL keywords highlighted for readability  
✅ **Copy to Clipboard** - One-click SQL extraction  
✅ **Memory Protection** - Auto-limited to 1000 most recent queries  
✅ **Echo Prevention** - Filters out app's own monitoring queries  

## Quick Start with Docker (Recommended)

```bash
# Start everything
docker-compose up --build

# Access app
# Browser: http://localhost:3000

# Connect with these credentials:
# Host: localhost
# Port: 5432
# Database: testdb
# Username: postgres
# Password: test123
```

See [DOCKER_TESTING.md](DOCKER_TESTING.md) for full testing guide.

## Manual Installation

```bash
# Install dependencies
pip3 install -r requirements.txt

# Initialize Reflex
reflex init

# Run application
reflex run
```

## Project Structure

```
pg_logger/
├── pg_logger/
│   ├── backend/           # Core logic
│   │   ├── discovery.py   # Network scanner
│   │   ├── history_mgr.py # Connection history
│   │   ├── config_mgr.py  # DB config & keyring
│   │   ├── log_engine.py  # Log file tailing
│   │   └── log_parser.py  # Regex-based parsing
│   ├── frontend/          # UI components
│   │   ├── styles.py      # Colors & themes
│   │   ├── components.py  # Reusable components
│   │   └── overlays.py    # Modals & warnings
│   ├── state.py           # App state management
│   └── pg_logger.py       # Main entry point
├── docker-compose.yml     # Docker setup
├── Dockerfile             # App container
├── seed.sql               # Test database
└── cleanup.py             # Emergency reset script
```

## Testing

See [DOCKER_TESTING.md](DOCKER_TESTING.md) for comprehensive testing scenarios.

## Development

All implementation details in `/home/vikas-kanderai/.gemini/antigravity/brain/feb11b5a-a09b-4f96-be03-b7ab2ef0a1bb/`:
- `walkthrough.md` - Complete implementation breakdown
- `task.md` - Feature checklist
- `setup_and_testing_guide.md` - Manual setup instructions

## License

MIT
