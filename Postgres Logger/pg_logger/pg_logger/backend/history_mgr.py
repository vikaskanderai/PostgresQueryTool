"""
Connection history manager.
Handles CRUD operations for connections.json (excludes passwords).
"""
import json
from typing import List, Dict, Optional
from pathlib import Path


class HistoryManager:
    """Manages connection history persistence."""
    
    def __init__(self, filepath: str = "connections.json"):
        """
        Initialize with storage file path.
        
        Args:
            filepath: Path to connections.json file
        """
        self.filepath = Path(filepath)
        self._ensure_file_exists()
    
    def _ensure_file_exists(self) -> None:
        """Create connections.json if it doesn't exist."""
        if not self.filepath.exists():
            self.save_connections([])
    
    def load_connections(self) -> List[Dict[str, str]]:
        """
        Load connection history from JSON file.
        
        Returns:
            List of connection dictionaries (no passwords)
        """
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
                return data.get("connections", [])
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading connections: {e}")
            return []
    
    def save_connections(self, connections: List[Dict[str, str]]) -> None:
        """
        Save connection history to JSON file.
        
        Args:
            connections: List of connection dicts (must exclude passwords)
        """
        try:
            # Ensure passwords are never saved
            sanitized = []
            for conn in connections:
                clean_conn = {
                    "host": conn.get("host", ""),
                    "port": conn.get("port", 5432),
                    "database": conn.get("database", ""),
                    "username": conn.get("username", "")
                }
                # Explicitly exclude password field
                if "password" in clean_conn:
                    del clean_conn["password"]
                sanitized.append(clean_conn)
            
            with open(self.filepath, 'w') as f:
                json.dump({"connections": sanitized}, f, indent=2)
        except Exception as e:
            print(f"Error saving connections: {e}")
    
    def add_connection(
        self, 
        host: str, 
        port: int, 
        database: str, 
        username: str
    ) -> None:
        """
        Add a new connection to history (no duplicates).
        
        Args:
            host: Database host/IP
            port: Database port
            database: Database name
            username: Username (password NEVER stored)
        """
        connections = self.load_connections()
        
        # Check for duplicates (same host, port, database, username)
        for conn in connections:
            if (conn.get("host") == host and 
                conn.get("port") == port and
                conn.get("database") == database and
                conn.get("username") == username):
                # Already exists, move to front
                connections.remove(conn)
                connections.insert(0, conn)
                self.save_connections(connections)
                return
        
        # Add new connection at the front
        new_connection = {
            "host": host,
            "port": port,
            "database": database,
            "username": username
        }
        connections.insert(0, new_connection)
        
        # Limit history to 20 entries
        if len(connections) > 20:
            connections = connections[:20]
        
        self.save_connections(connections)
    
    def remove_connection(self, host: str, database: str, username: str) -> bool:
        """
        Remove a connection from history.
        
        Args:
            host: Database host/IP
            database: Database name
            username: Username
            
        Returns:
            True if removed, False if not found
        """
        connections = self.load_connections()
        
        for conn in connections:
            if (conn.get("host") == host and 
                conn.get("database") == database and
                conn.get("username") == username):
                connections.remove(conn)
                self.save_connections(connections)
                return True
        
        return False
    
    def clear_history(self) -> None:
        """Clear all connection history."""
        self.save_connections([])
