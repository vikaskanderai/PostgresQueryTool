"""
Network discovery module for PostgreSQL instances.
Implements async subnet scanning with Semaphore(20) concurrency control.
"""
import asyncio
import socket
from typing import List, Dict, Optional
import time


class DiscoveryEngine:
    """Handles asynchronous network discovery of PostgreSQL instances."""
    
    def __init__(self, max_concurrent: int = 20, timeout: float = 1.5):
        """
        Initialize the discovery engine.
        
        Args:
            max_concurrent: Maximum concurrent connection attempts (default: 20)
            timeout: Connection timeout in seconds (default: 1.5)
        """
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    @staticmethod
    def get_local_subnet() -> str:
        """
        Extract the base /24 subnet from the local network interface.
        
        Returns:
            Base IP address (e.g., "192.168.1")
        """
        try:
            # Create a socket to determine the local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Connect to an external address (doesn't actually send data)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            # Extract base subnet (first 3 octets)
            parts = local_ip.split('.')
            return '.'.join(parts[:3])
        except Exception as e:
            # Fallback to common subnet if detection fails
            print(f"Failed to detect subnet: {e}. Using fallback 192.168.1")
            return "192.168.1"
    
    async def probe_host(self, host: str, port: int) -> Optional[Dict[str, any]]:
        """
        Probe a single host:port combination for PostgreSQL availability.
        
        Args:
            host: IP address to probe
            port: Port number to check
            
        Returns:
            Dictionary with {host, port, status, response_time} or None if failed
        """
        async with self.semaphore:  # Limit concurrent connections to prevent socket exhaustion
            start_time = time.time()
            try:
                # Attempt TCP connection with timeout
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port),
                    timeout=self.timeout
                )
                
                # Close connection immediately
                writer.close()
                await writer.wait_closed()
                
                response_time = time.time() - start_time
                return {
                    "host": host,
                    "port": port,
                    "status": "available",
                    "response_time": round(response_time * 1000, 2)  # Convert to ms
                }
            except (asyncio.TimeoutError, OSError, ConnectionRefusedError):
                # Host is unreachable or port is closed
                return None
    
    async def scan_subnet(
        self, 
        base_ip: Optional[str] = None, 
        port_range: range = range(5432, 5433)
    ) -> List[Dict[str, any]]:
        """
        Scan the entire /24 subnet for PostgreSQL instances.
        
        Args:
            base_ip: Base subnet IP (e.g., "192.168.1"), auto-detected if None
            port_range: Range of ports to scan (default: 5432)
            
        Returns:
            List of discovered instances with connection details
        """
        if base_ip is None:
            base_ip = self.get_local_subnet()
        
        # Create tasks for all combinations of IPs (1-254) and ports
        tasks = []
        for octet in range(1, 255):
            host = f"{base_ip}.{octet}"
            for port in port_range:
                tasks.append(self.probe_host(host, port))
        
        # Execute all probes concurrently (semaphore controls actual concurrency)
        results = await asyncio.gather(*tasks)
        
        # Filter out None values (failed connections) and return successful discoveries
        discovered = [r for r in results if r is not None]
        
        return discovered
    
    async def scan_custom_hosts(
        self, 
        hosts: List[str], 
        port_range: range = range(5432, 5433)
    ) -> List[Dict[str, any]]:
        """
        Scan a custom list of hosts for PostgreSQL instances.
        
        Args:
            hosts: List of IP addresses or hostnames to probe
            port_range: Range of ports to scan (default: 5432)
            
        Returns:
            List of discovered instances with connection details
        """
        tasks = []
        for host in hosts:
            for port in port_range:
                tasks.append(self.probe_host(host, port))
        
        results = await asyncio.gather(*tasks)
        discovered = [r for r in results if r is not None]
        
        return discovered
