"""
Log parsing with regex patterns for SQL extraction.
Handles multi-line SQL reconstruction and duration extraction.
"""
import re
from typing import List, Dict, Optional


# Regex Patterns
STATEMENT_PATTERN = re.compile(
    r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) \[(\d+)\] (\w+)@(\w+) (.*)$'
)

DURATION_PATTERN = re.compile(
    r'.*duration: ([\d.]+) ms.*'
)

# Continuation line: starts with whitespace (multi-line SQL)
CONTINUATION_PATTERN = re.compile(r'^\s+(.+)$')


class LogParser:
    """Parses PostgreSQL log files to extract query information."""
    
    def __init__(self, backend_pid: int):
        """
        Initialize parser with backend PID for filtering.
        
        Args:
            backend_pid: PID of app's own backend to filter out
        """
        self.backend_pid = backend_pid
        self.current_entry: Optional[Dict] = None
    
    def parse_log_lines(self, content: str) -> List[Dict[str, any]]:
        """
        Parse log content into structured query entries.
        
        Args:
            content: Raw log file content
            
        Returns:
            List of parsed query dictionaries:
            {
                'timestamp': '2024-01-10 20:30:45.123',
                'pid': 12345,
                'user': 'postgres',
                'database': 'mydb',
                'sql': 'SELECT * FROM users;',
                'duration': 15.5  # Optional, in milliseconds
            }
        """
        entries = []
        lines = content.split('\n')
        
        for line in lines:
            if not line.strip():
                continue
            
            try:
                # Check for statement start
                match = STATEMENT_PATTERN.match(line)
                if match:
                    # Save previous entry if exists
                    if self.current_entry:
                        if self._should_include_entry(self.current_entry):
                            entries.append(self.current_entry)
                    
                    # Start new entry
                    timestamp, pid, user, database, statement = match.groups()
                    
                    # Check for duration in statement
                    duration = None
                    duration_match = DURATION_PATTERN.match(statement)
                    if duration_match:
                        duration = float(duration_match.group(1))
                    
                    self.current_entry = {
                        'timestamp': timestamp,
                        'pid': int(pid),
                        'user': user,
                        'database': database,
                        'sql': statement,
                        'duration': duration
                    }
                
                # Check for continuation line (multi-line SQL)
                elif self.current_entry:
                    cont_match = CONTINUATION_PATTERN.match(line)
                    if cont_match:
                        continuation = cont_match.group(1)
                        self.current_entry['sql'] += ' ' + continuation
            
            except (re.error, AttributeError, ValueError) as e:
                # Log parsing error, skip this line and continue
                # This prevents crashes on malformed log lines
                continue
        
        # Don't forget the last entry
        if self.current_entry:
            if self._should_include_entry(self.current_entry):
                entries.append(self.current_entry)
            self.current_entry = None
        
        return entries
    
    def _should_include_entry(self, entry: Dict) -> bool:
        """
        Determine if entry should be included in results.
        Filters out app's own queries to prevent echo loops.
        
        Args:
            entry: Parsed log entry
            
        Returns:
            True if entry should be included
        """
        # Filter out our own backend
        if entry['pid'] == self.backend_pid:
            return False
        
        # Filter out system queries (optional)
        sql_lower = entry['sql'].lower()
        
        # Skip pg_ls_logdir, pg_read_binary_file, etc.
        if 'pg_ls_logdir' in sql_lower:
            return False
        if 'pg_read_binary_file' in sql_lower:
            return False
        if 'pg_reload_conf' in sql_lower:
            return False
        if 'alter system' in sql_lower:
            return False
        
        return True
