"""
Database configuration and connection management.
Implements asyncpg pool, keyring integration, and privilege validation.
"""
import asyncpg
from typing import Optional
import keyring


class ConfigManager:
    """Manages database connections and configuration validation."""
    
    def __init__(self):
        """Initialize configuration manager."""
        self.pool: Optional[asyncpg.Pool] = None
        self.is_superuser: bool = False
        self.backend_pid: Optional[int] = None
        self.host: str = ""
        self.port: int = 5432
        self.database: str = ""
        self.database: str = ""
        self.username: str = ""
        self.streaming_active: bool = False
    
    async def connect(
        self,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str
    ) -> bool:
        """
        Establish asyncpg connection pool and validate superuser status.
        
        Args:
            host: Database host
            port: Database port
            database: Database name
            username: Username
            password: Password (will be stored in keyring)
            
        Returns:
            True if connection successful and user is superuser
            
        Raises:
            ConnectionError: If connection fails
            PermissionError: If user is not superuser
        """
        try:
            # Store connection parameters
            self.host = host
            self.port = port
            self.database = database
            self.username = username
            
            # Create asyncpg connection pool
            self.pool = await asyncpg.create_pool(
                host=host,
                port=port,
                database=database,
                user=username,
                password=password,
                min_size=2,
                max_size=10,
                command_timeout=10
            )
            
            # Validate superuser status
            is_super = await self.check_superuser()
            if not is_super:
                await self.close()
                raise PermissionError(
                    "User must be a superuser to use this application. "
                    "Please connect with a superuser account (e.g., 'postgres')."
                )
            
            self.is_superuser = True
            
            # Get backend PID for log filtering
            self.backend_pid = await self.get_backend_pid()
            
            # Store password in keyring for future use
            try:
                self._store_password(host, port, database, username, password)
            except Exception as e:
                print(f"Warning: Failed to store password in keyring: {e}")
            
            return True
            
        except asyncpg.exceptions.InvalidPasswordError:
            raise ConnectionError("Invalid password")
        except asyncpg.exceptions.InvalidCatalogNameError:
            raise ConnectionError(f"Database '{database}' does not exist")
        except asyncpg.exceptions.PostgresError as e:
            raise ConnectionError(f"PostgreSQL error: {e}")
        except Exception as e:
            raise ConnectionError(f"Connection failed: {e}")
    
    async def check_superuser(self) -> bool:
        """
        Check if current user has superuser privileges.
        
        Returns:
            True if current user is superuser
        """
        if not self.pool:
            return False
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval(
                    "SELECT usesuper FROM pg_user WHERE usename = current_user"
                )
                return result is True
        except Exception as e:
            print(f"Error checking superuser status: {e}")
            return False
    
    async def check_logging_collector(self) -> bool:
        """
        Check if logging_collector is enabled.
        
        Returns:
            True if logging is enabled ('on')
        """
        if not self.pool:
            return False
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("SHOW logging_collector")
                return result == 'on'
        except Exception as e:
            print(f"Error checking logging_collector: {e}")
            return False
    
    async def enable_logging_collector(self) -> None:
        """
        Enable logging_collector via ALTER SYSTEM.
        
        Note: Requires PostgreSQL restart to take effect.
        """
        if not self.pool:
            raise ConnectionError("Not connected to database")
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("ALTER SYSTEM SET logging_collector = 'on'")
                await conn.execute("SELECT pg_reload_conf()")
        except Exception as e:
            raise RuntimeError(f"Failed to enable logging_collector: {e}")
    
    async def set_streaming_params(self, enable: bool) -> None:
        """
        Configure PostgreSQL logging for query streaming.
        
        Args:
            enable: True to enable streaming, False to reset
            
        When enable=True:
            - Sets log_min_duration_statement = 0 (log all queries)
            - Sets log_line_prefix = '%m [%p] %u@%d ' (timestamp, PID, user, db)
            - Reloads config
            
        When enable=False:
            - Resets both settings to defaults
            - Reloads config
        """

        
        if not self.pool:
            raise ConnectionError("Not connected to database")
        
        try:
            async with self.pool.acquire() as conn:
                if enable:
                    # Enable verbose logging
                    await conn.execute(
                        "ALTER SYSTEM SET log_min_duration_statement = 0"
                    )
                    await conn.execute(
                        "ALTER SYSTEM SET log_line_prefix = '%m [%p] %u@%d '"
                    )
                else:
                    # Reset to defaults (clean exit rule)
                    await conn.execute(
                        "ALTER SYSTEM RESET log_min_duration_statement"
                    )
                    await conn.execute(
                        "ALTER SYSTEM RESET log_line_prefix"
                    )
                
                # Reload configuration (immediate effect, no restart needed)
                await conn.execute("SELECT pg_reload_conf()")
                
        except Exception as e:
            raise RuntimeError(f"Failed to configure streaming: {e}")

    
    async def get_backend_pid(self) -> int:
        """
        Get the process ID of the current backend connection.
        Used for filtering out app's own queries from logs.
        
        Returns:
            Process ID of current backend
        """
        if not self.pool:
            return 0
        
        try:
            async with self.pool.acquire() as conn:
                pid = await conn.fetchval("SELECT pg_backend_pid()")
                return pid
        except Exception as e:
            print(f"Error getting backend PID: {e}")
            return 0
    
    def _store_password(
        self, 
        host: str, 
        port: int, 
        database: str, 
        username: str, 
        password: str
    ) -> None:
        """
        Store password in OS keyring.
        
        Args:
            host: Database host
            port: Database port
            database: Database name
            username: Username
            password: Password to store
        """
        account = f"{username}@{host}:{port}/{database}"
        keyring.set_password("pg_logger", account, password)
    
    def retrieve_password(
        self, 
        host: str, 
        port: int, 
        database: str, 
        username: str
    ) -> Optional[str]:
        """
        Retrieve password from OS keyring.
        
        Args:
            host: Database host
            port: Database port
            database: Database name
            username: Username
            
        Returns:
            Password if found, None otherwise
        """
        try:
            account = f"{username}@{host}:{port}/{database}"
            return keyring.get_password("pg_logger", account)
        except Exception as e:
            print(f"Warning: Failed to retrieve password from keyring: {e}")
            return None
    
    async def close(self) -> None:
        """Close connection pool and cleanup resources."""
        if self.pool:
            await self.pool.close()
            self.pool = None
        self.is_superuser = False
        self.backend_pid = None
