# Docker Testing Guide - PostgreSQL Log Streamer

## Quick Start

### Prerequisites
- Docker Desktop installed
- Docker Compose installed (usually bundled with Docker Desktop)

### Start Everything

```bash
cd "/home/vikas-kanderai/Antigravity/PostgresQueryTool/Postgres Logger/pg_logger"

# Build and start containers
docker-compose up --build
```

**Access**:
- **App**: http://localhost:3000
- **PostgreSQL**: `localhost:5432`

### Stop Everything

```bash
# Stop containers (keeps data)
docker-compose stop

# Stop and remove containers (keeps data in volume)
docker-compose down

# Complete cleanup (removes data)
docker-compose down -v
```

---

## Connection Details

**IMPORTANT**: When connecting through the app's connection form in the browser:

- **Host**: `postgres` (Docker service name - the app container uses this to find the DB on the internal network)
- **Port**: `5432`
- **Database**: `testdb`
- **Username**: `postgres`
- **Password**: `test123`

> [!NOTE]
> Use `postgres` as the host, NOT `localhost`. Inside the app container, `localhost` refers to the container itself, not your machine.

---

## Pre-configured Setup

The Docker environment comes with:

✅ **PostgreSQL 17** (latest) with `logging_collector=on` (no restart needed!)  
✅ **Test database** `testdb` with sample tables  
✅ **Sample data**: users, products, orders  
✅ **Reflex app** auto-connected to PostgreSQL  

---

## Testing Workflow

### 1. Start Services

```bash
docker-compose up
```

Wait for:
```
pg_logger_db  | database system is ready to accept connections
pg_logger_app | App running at: http://localhost:3000
```

### 2. Access Application

Open browser → http://localhost:3000

### 3. Connect to Database

Use the connection form:
- Host: `postgres` ⚠️ **Important: Use 'postgres', not 'localhost'**
- Port: `5432`
- Database: `testdb`
- Username: `postgres`
- Password: `test123`

**Expected**: Direct to dashboard (no restart needed - logging already configured!)

### 4. Start Streaming

Click "▶️ Start Streaming"

### 5. Run Test Queries

Open a new terminal:

```bash
# Connect to PostgreSQL in Docker
docker-compose exec postgres psql -U postgres -d testdb

# Or from your host (if psql installed)
psql -h localhost -U postgres -d testdb
# Password: test123
```

Then execute test queries:

```sql
-- Simple queries
SELECT * FROM users;
SELECT * FROM products WHERE category = 'Electronics';

-- Joins
SELECT u.username, COUNT(o.id) as orders
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.username;

-- Slow query (for duration testing)
SELECT pg_sleep(0.1);

-- Multi-line query (for parsing test)
SELECT 
    p.name,
    p.price,
    p.category
FROM 
    products p
WHERE 
    p.stock > 50
ORDER BY 
    p.price DESC;

-- Function call
SELECT get_user_order_count('alice');

-- View query
SELECT * FROM user_order_summary;
```

Check the app - queries should appear in real-time!

---

## Test Scenarios

### Scenario 1: Search & Filter

1. Execute 10+ different queries
2. Search for "SELECT" → See only SELECT queries
3. Search for "alice" → See queries with user alice
4. Set min duration 50ms → Execute `SELECT pg_sleep(0.05)` → Verify appears
5. Clear filters → All queries return

### Scenario 2: Copy Functionality

1. Execute: `SELECT * FROM users WHERE username = 'alice';`
2. Click "📋 Copy" on the query card
3. Paste in text editor → Verify exact SQL copied

### Scenario 3: Syntax Highlighting

1. Execute: `SELECT id, username FROM users WHERE active = true;`
2. Verify in **Dashboard** activity feed:
   - `SELECT`, `FROM`, `WHERE` → Blue + Bold
   - `id`, `username`, `active`, `true` → Default color

> [!NOTE]
> Make sure you're viewing the Dashboard page where the activity feed is displayed.

### Scenario 4: Memory Guard

Execute many queries quickly:

```sql
DO $$
BEGIN
    FOR i IN 1..1500 LOOP
        PERFORM 1;
    END LOOP;
END $$;
```

Verify feed shows max 1000 entries.

---

## Useful Docker Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Just PostgreSQL
docker-compose logs -f postgres

# Just app
docker-compose logs -f app
```

### Access PostgreSQL CLI

```bash
docker-compose exec postgres psql -U postgres -d testdb
```

### Restart Services

```bash
# Restart PostgreSQL only
docker-compose restart postgres

# Restart app only
docker-compose restart app

# Restart everything
docker-compose restart
```

### Rebuild After Code Changes

```bash
# Rebuild app container
docker-compose up --build app

# Full rebuild
docker-compose down
docker-compose up --build
```

### Inspect Database

```bash
# List tables
docker-compose exec postgres psql -U postgres -d testdb -c "\dt"

# Check logging_collector
docker-compose exec postgres psql -U postgres -d testdb -c "SHOW logging_collector;"

# View current logs directory
docker-compose exec postgres ls -la /var/lib/postgresql/data/log/
```

---

## Troubleshooting

### Issue: Port 5432 already in use

**Solution**: Stop local PostgreSQL or change port in `docker-compose.yml`:

```yaml
ports:
  - "5433:5432"  # Use 5433 on host
```

Then connect with port `5433`.

### Issue: App can't connect to database

**Solution**: Wait for PostgreSQL health check to pass:

```bash
docker-compose logs postgres
# Look for: "database system is ready"
```

### Issue: Changes not reflected in app

**Solution**: Rebuild the container:

```bash
docker-compose up --build app
```

### Issue: Keyring / "No recommended backend" error

**Solution**: Ensure the app environment in `docker-compose.yml` includes:

```yaml
environment:
  - PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring
```

This is already configured in the provided `docker-compose.yml`.

### Issue: Reset everything

```bash
# Nuclear option - removes all data
docker-compose down -v
docker-compose up --build
```

---

## Development Workflow

### Edit Code While Running

With the volume mount, code changes are reflected immediately:

1. Edit files in your editor
2. Reflex auto-reloads (watch logs)
3. Refresh browser

**Note**: If you edit `requirements.txt`, rebuild:

```bash
docker-compose up --build app
```

---

## Sample Test Session

```bash
# Terminal 1: Start services
docker-compose up

# Terminal 2: Execute test queries
docker-compose exec postgres psql -U postgres -d testdb

# In psql:
testdb=# SELECT * FROM users;
testdb=# SELECT * FROM products WHERE price > 100;
testdb=# SELECT pg_sleep(0.05);

# Browser: http://localhost:3000
# - Connect with credentials
# - Start streaming
# - See queries appear
# - Test search/filter
# - Test copy button
```

---

## Cleanup

When done testing:

```bash
# Stop and remove containers (keep data)
docker-compose down

# Complete cleanup (remove data too)
docker-compose down -v
```

---

## Next Steps

After verifying everything works in Docker:

1. **Production Deployment**: Use `docker-compose -f docker-compose.prod.yml`
2. **CI/CD Integration**: Use this for automated testing
3. **Team Sharing**: Share `docker-compose.yml` for consistent environments

Enjoy testing! 🚀
