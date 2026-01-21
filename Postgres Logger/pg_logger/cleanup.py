#!/usr/bin/env python3
"""
Emergency cleanup script for PostgreSQL Log Streamer.
Resets all ALTER SYSTEM changes if the main app crashes.

Usage:
    python cleanup.py --host <host> --port <port> --database <db> --username <user>
"""
import asyncio
import asyncpg
import argparse
import sys


async def reset_postgres_config(host: str, port: int, database: str, username: str, password: str) -> bool:
    """
    Reset PostgreSQL logging configuration to defaults.
    
    Args:
        host: Database host
        port: Database port
        database: Database name
        username: Superuser username
        password: Password
        
    Returns:
        True if successful
    """
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password
        )
        
        print("✓ Connected to PostgreSQL")
        
        # Reset log settings
        await conn.execute("ALTER SYSTEM RESET log_min_duration_statement;")
        print("✓ Reset log_min_duration_statement")
        
        await conn.execute("ALTER SYSTEM RESET log_line_prefix;")
        print("✓ Reset log_line_prefix")
        
        # Reload configuration
        await conn.execute("SELECT pg_reload_conf();")
        print("✓ Reloaded PostgreSQL configuration")
        
        await conn.close()
        print("\n✓ Cleanup completed successfully!")
        print("Note: Restart PostgreSQL if logging_collector was changed.")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during cleanup: {e}", file=sys.stderr)
        return False


def main():
    """Parse arguments and run cleanup."""
    parser = argparse.ArgumentParser(
        description="Emergency cleanup for PostgreSQL Log Streamer"
    )
    parser.add_argument("--host", required=True, help="Database host")
    parser.add_argument("--port", type=int, default=5432, help="Database port")
    parser.add_argument("--database", required=True, help="Database name")
    parser.add_argument("--username", required=True, help="Superuser username")
    
    args = parser.parse_args()
    
    # Prompt for password (don't pass via CLI for security)
    import getpass
    password = getpass.getpass("Password: ")
    
    print("\nStarting PostgreSQL configuration cleanup...")
    print(f"Target: {args.username}@{args.host}:{args.port}/{args.database}\n")
    
    # Run cleanup
    success = asyncio.run(reset_postgres_config(
        host=args.host,
        port=args.port,
        database=args.database,
        username=args.username,
        password=password
    ))
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
