"""
Main application state management.
Handles all shared state and background async tasks.
"""
from pickle import TRUE
import reflex as rx
import asyncio
from typing import List, Dict, Optional, Any
from .backend.discovery import DiscoveryEngine
from .backend.history_mgr import HistoryManager
from .backend.config_mgr import ConfigManager

# Global registry for backend connection managers
# keyed by client_token to prevent Reflex serialization issues
SESSION_CONFIGS: Dict[str, ConfigManager] = {}


class AppState(rx.State):
    """Main application state with async task handling."""
    
    # Discovery state
    discovered_hosts: List[Dict[str, Any]] = []
    is_scanning: bool = False
    scan_progress: str = ""
    
    # Connection history
    connection_history: List[Dict[str, str]] = []
    
    # Selected connection parameters
    selected_host: str = ""
    selected_port: int = 5432
    selected_database: str = ""
    selected_username: str = ""
    password_input: str = ""  # Temporary storage for form input only
    
    # Authentication state
    is_authenticated: bool = False
    is_connecting: bool = False
    connection_error: str = ""
    requires_restart: bool = False
    is_polling_restart: bool = False
    
    # Database connection (stored in global SESSION_CONFIGS)
    # _db_config property handles access to backend-only state
    backend_pid: int = 0
    
    # Streaming state (Phase 3)
    is_streaming: bool = False
    stream_status: str = "Stopped"
    current_log_file: str = ""
    log_offset: int = 0
    
    # Session state
    query_log: List[Dict[str, Any]] = []
    
    # Search and filter state (Phase 5)
    search_text: str = ""
    min_duration: float = 0.0
    
    def set_min_duration(self, value: str) -> None:
        """Set minimum duration filter from string input."""
        try:
            if not value:
                self.min_duration = 0.0
            else:
                self.min_duration = float(value)
        except ValueError:
            # Keep previous value or reset to 0 on invalid input
            pass
    
    @rx.var
    def filtered_query_log(self) -> List[Dict[str, Any]]:
        """
        Filter query log based on search criteria.
        Automatically recomputes when search_text, min_duration, or query_log change.
        
        Returns:
            Filtered list of query entries
        """
        filtered = self.query_log
        
        # Apply search text filter (case-insensitive)
        if self.search_text:
            search_lower = self.search_text.lower()
            filtered = [
                q for q in filtered
                if search_lower in q['sql'].lower()
                or search_lower in q['user'].lower()
                or search_lower in q['database'].lower()
            ]
        
        # Apply duration filter
        if self.min_duration > 0:
            filtered = [
                q for q in filtered
                if q.get('duration', 0) >= self.min_duration
            ]
        
        return filtered

    # ========== Backend State Accessors ==========

    @property
    def _db_config(self) -> Optional[ConfigManager]:
        """Retrieve connection config from global registry."""
        try:
            token = self.router.session.client_token
            return SESSION_CONFIGS.get(token)
        except:
            return None

    @_db_config.setter
    def _db_config(self, value: Optional[ConfigManager]):
        """Store connection config in global registry."""
        self.set_db_config(value)

    def set_db_config(self, value: Optional[ConfigManager]):
        """Explicit setter to bypass Reflex magic."""
        try:
            token = self.router.session.client_token
            if value is None:
                SESSION_CONFIGS.pop(token, None)
            else:
                SESSION_CONFIGS[token] = value
        except:
            pass
    
    # ========== Event Handlers ==========
    
    def on_load(self) -> None:
        """Called when the app loads - initialize state."""
        self.connection_error = "" # Clear stale errors
        self.is_connecting = False
        return AppState.load_history
    
    async def load_history(self) -> None:
        """Load connection history from disk."""
        history_mgr = HistoryManager()
        async with self:
            self.connection_history = history_mgr.load_connections()
    
    # ========== Discovery Methods ==========
    
    @rx.event(background=True)
    async def scan_network(self, port_start: int = 5432, port_end: int = 5436) -> None:
        """
        Background task to scan local subnet for PostgreSQL instances.
        Uses Semaphore(20) for concurrency control.
        
        Args:
            port_start: Starting port number (default: 5432)
            port_end: Ending port number exclusive (default: 5436)
        """
        async with self:
            self.is_scanning = True
            self.discovered_hosts = []
            self.scan_progress = "Detecting local subnet..."
        
        # Create discovery engine with Semaphore(20)
        discovery_engine = DiscoveryEngine(max_concurrent=20)
        
        # Get local subnet
        base_ip = discovery_engine.get_local_subnet()
        
        async with self:
            self.scan_progress = f"Scanning {base_ip}.0/24 on ports {port_start}-{port_end-1}..."
        
        # Perform scan (non-blocking, semaphore controls concurrency)
        results = await discovery_engine.scan_subnet(
            base_ip=base_ip,
            port_range=range(port_start, port_end)
        )
        
        async with self:  # Thread-safe state update
            self.discovered_hosts = results
            self.is_scanning = False
            self.scan_progress = f"Scan complete. Found {len(results)} instance(s)."
    
    def select_host(self, host: str, port: int) -> None:
        """
        Select a discovered host for connection.
        
        Args:
            host: IP address or hostname
            port: Port number
        """
        self.selected_host = host
        self.selected_port = port
    
    def select_from_history(self, index: int) -> None:
        """
        Load connection parameters from history.
        
        Args:
            index: Index in connection_history list
        """
        if 0 <= index < len(self.connection_history):
            conn = self.connection_history[index]
            self.selected_host = conn.get("host", "")
            self.selected_port = conn.get("port", 5432)
            self.selected_database = conn.get("database", "")
            self.selected_username = conn.get("username", "")
            
            # Try to retrieve password from keyring
            try:
                config_mgr = ConfigManager()
                password = config_mgr.retrieve_password(
                    self.selected_host,
                    self.selected_port,
                    self.selected_database,
                    self.selected_username
                )
                if password:
                    self.password_input = password
            except Exception as e:
                print(f"Could not retrieve password: {e}")
    
    def clear_discovered_hosts(self) -> None:
        """Clear the discovery results."""
        self.discovered_hosts = []
        self.scan_progress = ""
    
    # ========== Authentication Methods ==========
    
    def set_selected_host(self, value: str) -> None:
        """Update selected host."""
        self.selected_host = value
    
    def set_selected_port(self, value: str) -> None:
        """Update selected port."""
        try:
            self.selected_port = int(value)
        except ValueError:
            pass
    
    def set_selected_database(self, value: str) -> None:
        """Update selected database."""
        self.selected_database = value
    
    def set_selected_username(self, value: str) -> None:
        """Update selected username."""
        self.selected_username = value
    
    def set_password_input(self, value: str) -> None:
        """Update password input (temporary only)."""
        self.password_input = value
    
    @rx.event(background=True)
    async def connect_to_database(self) -> None:
        """
        Attempt to connect to database with full validation.
        Phase 2 implementation with asyncpg pool and keyring.
        """
        async with self:
            self.is_connecting = True
            self.connection_error = ""
        
        try:
            # Get password from state
            password = self.password_input
            
            # Create config manager
            config_mgr = ConfigManager()
            
            # Attempt connection (includes superuser validation)
            success = await config_mgr.connect(
                host=self.selected_host,
                port=self.selected_port,
                database=self.selected_database,
                username=self.selected_username,
                password=password
            )
            
            if not success:
                raise ConnectionError("Failed to connect to database")

            
            # Check logging_collector
            logging_enabled = await config_mgr.check_logging_collector()
            

            
            if not logging_enabled:
                # Enable it and trigger restart requirement
                await config_mgr.enable_logging_collector()
                async with self:
                    self.requires_restart = True
                    self.set_db_config(config_mgr)
                    self.is_connecting = False
                    self.password_input = ""  # Clear password from state
                # Start polling for restart
                return AppState.poll_logging_status
            
            # Get backend PID for log filtering
            pid = await config_mgr.get_backend_pid()
            
            # Save to history
            history = HistoryManager()
            history.add_connection(
                self.selected_host,
                self.selected_port,
                self.selected_database,
                self.selected_username
            )
            
            async with self:
                self.is_authenticated = True
                self.set_db_config(config_mgr)
                self.backend_pid = pid
                self.is_connecting = False
                self.password_input = ""  # Clear password from state
                
        except PermissionError as e:
            async with self:
                self.connection_error = str(e)
                self.is_connecting = False
                self.password_input = ""
        except ConnectionError as e:
            async with self:
                self.connection_error = str(e)
                self.is_connecting = False
                self.password_input = ""
        except Exception as e:
            async with self:
                self.connection_error = f"Connection failed: {e}"
                self.is_connecting = False
                self.password_input = ""
    
    @rx.event(background=True)
    async def poll_logging_status(self) -> None:
        """
        Poll logging_collector every 5 seconds until enabled.
        Runs when restart overlay is active.
        """
        async with self:
            self.is_polling_restart = True
        
        # Get the config manager from state
        config_mgr = self._db_config
        
        if not config_mgr:
            async with self:
                self.is_polling_restart = False
            return
        
        max_attempts = 120  # 10 minutes max
        attempt = 0
        
        while attempt < max_attempts:
            await asyncio.sleep(5)
            attempt += 1
            
            try:
                enabled = await config_mgr.check_logging_collector()
                if enabled:
                    # Restart detected!
                    pid = await config_mgr.get_backend_pid()
                    
                    # Save to history
                    state = self
                    history = HistoryManager()
                    history.add_connection(
                        state.selected_host,
                        state.selected_port,
                        state.selected_database,
                        state.selected_username
                    )
                    
                    async with self:
                        self.requires_restart = False
                        self.is_polling_restart = False
                        self.is_authenticated = True
                        self.backend_pid = pid
                    break
            except Exception:
                # Connection might be down during restart - continue polling
                continue
        
        # Timeout after max attempts
        if attempt >= max_attempts:
            async with self:
                self.is_polling_restart = False
                self.connection_error = "Restart detection timeout. Please try reconnecting."
    
    def reset_connection(self) -> None:
        """Reset connection state (logout)."""
        # Close database connection
        if self._db_config:
            # Note: asyncio.create_task to close in background
            try:
                asyncio.create_task(self._db_config.close())
            except:
                pass
            self.set_db_config(None)
        
        self.is_authenticated = False
        self.selected_host = ""
        self.selected_port = 5432
        self.selected_database = ""
        self.selected_username = ""
        self.password_input = ""
        self.connection_error = ""
        self.requires_restart = False
        self.is_polling_restart = False
        self.backend_pid = 0
    
    # ========== Streaming Control Methods (Phase 3) ==========
    
    @rx.event(background=True)
    async def toggle_stream(self) -> None:
        """
        Toggle query streaming on/off.
        
        Workflow when starting (is_streaming = False):
        1. Get database config from state
        2. Call set_streaming_params(True)
        3. Create LogEngine instance
        4. Initialize stream (get latest log + offset)
        5. Set is_streaming = True, store log file/offset
        6. Update stream_status
        
        Workflow when stopping (is_streaming = True):
        1. Get database config from state
        2. Call set_streaming_params(False)
        3. Set is_streaming = False
        4. Update stream_status
        """
        # Get current state
        current_streaming = self.is_streaming
        db_config = self._db_config
        
        if not db_config:
            async with self:
                self.connection_error = "Session expired. Please reconnect."
                self.is_authenticated = False
            return
        


        try:
            if not current_streaming:
                # START STREAMING
                async with self:
                    self.stream_status = "Starting stream..."

                # Apply SQL configuration
                await db_config.set_streaming_params(enable=True)
                db_config.streaming_active = True
                
                # Initialize log engine
                from .backend.log_engine import LogEngine
                log_engine = LogEngine(db_config.pool)
                
                # Find latest log file and set offset
                filename, offset = await log_engine.initialize_stream()
                
                async with self:
                    self.is_streaming = True
                    self.current_log_file = filename
                    self.log_offset = offset
                    self.stream_status = f"Streaming ({filename})"
                
                # Start background log reading task
                asyncio.create_task(self._stream_logs_loop())
                
            else:
                # STOP STREAMING
                async with self:
                    self.stream_status = "Stopping stream..."
                
                # Reset SQL configuration (clean exit rule)
                await db_config.set_streaming_params(enable=False)
                db_config.streaming_active = False
                
                # Reset streaming state
                async with self:
                    self.is_streaming = False
                    self.stream_status = "Stopped"
                    self.current_log_file = ""
                    self.log_offset = 0
                    
        except Exception as e:
            async with self:
                self.connection_error = f"Stream error: {e}"
                self.is_streaming = False
                self.stream_status = "Error"
    
    
    def clear_query_log(self) -> None:
        """Clear the query log feed."""
        self.query_log = []
    
    async def _stream_logs_loop(self) -> None:
        """
        Background task to continuously read and parse logs.
        Runs every 300ms while streaming is active.
        """
        from .backend.log_engine import LogEngine
        from .backend.log_parser import LogParser
        
        # Get state references
        db_config = self._db_config
        backend_pid = self.backend_pid
        
        if not db_config:
            return
        
        # Create log engine and parser
        log_engine = LogEngine(db_config.pool)
        
        # Initialize with stored state
        state = self
        log_engine.current_file = state.current_log_file
        log_engine.current_offset = state.log_offset
        
        parser = LogParser(backend_pid)
        
        # Polling loop
        while True:
            # Check if still streaming
            # Use backend flag from db_config for reliable state sharing
            # This avoids StateProxy.get_state() issues
            if not db_config.streaming_active:
                break
            
            try:
                # Read new log content
                content = await log_engine.read_new_logs()
                

                if content:
                    # Parse log lines

                    new_entries = parser.parse_log_lines(content)

                    if new_entries:
                        async with self:

                            # Append new queries
                            self.query_log.extend(new_entries)
                            
                            # Memory guard: Keep only last 1000 entries
                            self.query_log = self.query_log[-1000:]
                            
                            # Update offset
                            self.log_offset = log_engine.current_offset
                                
                # Check for log rotation
                rotated = await log_engine.check_rotation()
                if rotated:
                    # Switch to new file
                    filename, size = await log_engine.get_latest_log_file()
                    async with self:
                        self.current_log_file = filename
                        self.log_offset = size
                    log_engine.current_file = filename
                    log_engine.current_offset = size
            
            except Exception as e:
                print(f"Stream error: {e}")
            
            # Wait 700ms before next poll
            await asyncio.sleep(0.7)
