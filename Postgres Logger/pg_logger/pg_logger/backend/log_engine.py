"""
Log tailing and rotation handling.
Implements pg_ls_logdir() log detection and byte offset tracking.
"""
import asyncpg
from typing import Optional, Tuple


class LogEngine:
    """Handles PostgreSQL log file tailing and rotation detection."""
    
    def __init__(self, pool: asyncpg.Pool):
        """
        Initialize log engine.
        
        Args:
            pool: Active asyncpg connection pool
        """
        self.pool = pool
        self.current_file: str = ""
        self.current_offset: int = 0
    
    async def get_latest_log_file(self) -> Tuple[str, int]:
        """
        Query pg_ls_logdir() to find the latest log file.
        
        Returns:
            Tuple of (filename, size_bytes)
            
        Raises:
            RuntimeError: If no log files found or query fails
        """
        try:
            async with self.pool.acquire() as conn:
                # Query log directory for files
                # ORDER BY modification DESC to get latest first
                result = await conn.fetchrow("""
                    SELECT name, size
                    FROM pg_ls_logdir()
                    ORDER BY modification DESC
                    LIMIT 1
                """)
                
                if not result:
                    raise RuntimeError("No log files found in pg_ls_logdir()")
                
                filename = result['name']
                size = result['size']
                
                return (filename, size)
                
        except Exception as e:
            raise RuntimeError(f"Failed to get latest log file: {e}")
    
    async def get_file_size(self, filename: str) -> int:
        """
        Get the current size of a log file.
        
        Args:
            filename: Log file name from pg_ls_logdir()
            
        Returns:
            File size in bytes
        """
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("""
                    SELECT size
                    FROM pg_ls_logdir()
                    WHERE name = $1
                """, filename)
                
                return result if result else 0
                
        except Exception as e:
            raise RuntimeError(f"Failed to get file size: {e}")
    
    async def initialize_stream(self) -> Tuple[str, int]:
        """
        Initialize streaming by finding latest log and setting offset.
        
        Returns:
            Tuple of (filename, initial_offset)
        """
        filename, size = await self.get_latest_log_file()
        
        # Store current state
        self.current_file = filename
        self.current_offset = size  # Start at end (only read new content)
        
        return (filename, size)
    
    async def check_rotation(self) -> bool:
        """
        Check if log file has rotated.
        Phase 4 implementation.
        
        Returns:
            True if a new log file is active
        """
        try:
            latest_file, _ = await self.get_latest_log_file()
            return latest_file != self.current_file
        except:
            return False
    
    async def read_new_logs(self) -> str:
        """
        Read new content from the current log file using pg_read_binary_file.
        
        Returns:
            New log content as string (empty if no new content)
        """



        if not self.current_file:
            return ""
        
        try:
            # Get current file size
            current_size = await self.get_file_size(self.current_file)
            
            # Calculate bytes to read
            bytes_to_read = current_size - self.current_offset
            
            if bytes_to_read <= 0:
                return ""  # No new content
            
            # Limit read size to prevent memory issues (max 1MB per read)
            bytes_to_read = min(bytes_to_read, 1048576)
            
            async with self.pool.acquire() as conn:
                # Read binary data and convert to UTF-8
                # Note: pg_read_binary_file expects path relative to data directory
                # Log files are in 'log/' subdirectory
                content = await conn.fetchval("""
                    SELECT convert_from(
                        pg_read_binary_file($1, $2, $3),
                        'UTF8'
                    )
                """, 
                f'log/{self.current_file}',
                self.current_offset,
                bytes_to_read
                )
                
                # Update offset for next read
                self.current_offset += bytes_to_read

                return content if content else ""
                
        except Exception as e:
            print(f"Error reading log file: {e}")
            return ""
