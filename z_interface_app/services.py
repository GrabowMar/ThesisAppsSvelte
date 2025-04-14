"""
Service components for the AI Model Management System.
This module contains service classes that implement core business logic.
"""

# =============================================================================
# Standard Library Imports
# =============================================================================
import asyncio
import json
import os
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# =============================================================================
# Third-Party Imports
# =============================================================================
import docker
from docker.errors import NotFound
import pandas as pd
import matplotlib.pyplot as plt
import requests

# =============================================================================
# Custom Module Imports
# =============================================================================
from backend_security_analysis import BackendSecurityAnalyzer
from frontend_security_analysis import FrontendSecurityAnalyzer
from zap_scanner import create_scanner
from logging_service import create_logger_for_component
from performance_analysis import LocustPerformanceTester

# =============================================================================
# Docker Management
# =============================================================================
class DockerManager:
    """Manages Docker containers and their statuses with caching."""
    
    def __init__(self, client: Optional[docker.DockerClient] = None) -> None:
        """
        Initialize Docker manager with optional client.
        
        Args:
            client: Optional pre-configured Docker client
        """
        self.logger = create_logger_for_component('docker')
        self.client = client or self._create_docker_client()
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._cache_duration = int(os.getenv("CACHE_DURATION", "5"))
        self.logger.info("Docker manager initialized")

    def _create_docker_client(self) -> Optional[docker.DockerClient]:
        """
        Create a Docker client with configured timeout.
        
        Returns:
            Docker client instance or None if creation fails
        """
        try:
            docker_host = os.getenv("DOCKER_HOST", "npipe:////./pipe/docker_engine")
            self.logger.debug(f"Creating Docker client with host: {docker_host}")
            return docker.DockerClient(
                base_url=docker_host,
                timeout=int(os.getenv("DOCKER_TIMEOUT", "10")),
            )
        except Exception as e:
            self.logger.exception(f"Docker client creation failed: {e}")
            return None

    def get_container_status(self, container_name: str) -> 'DockerStatus':
        """
        Get the status of a container with caching.
        
        Args:
            container_name: Name of the container
            
        Returns:
            DockerStatus object with container status details
        """
        now = time.time()
        if container_name in self._cache:
            timestamp, status = self._cache[container_name]
            if now - timestamp < self._cache_duration:
                self.logger.debug(f"Using cached status for {container_name}")
                return status
        status = self._fetch_container_status(container_name)
        self._cache[container_name] = (now, status)
        return status

    def _fetch_container_status(self, container_name: str) -> 'DockerStatus':
        """
        Fetch the current status of a container from Docker.
        
        Args:
            container_name: Name of the container
            
        Returns:
            DockerStatus object with container status details
        """
        from utils import DockerStatus  # Import here to avoid circular imports
        
        if not self.client:
            self.logger.warning(f"Docker client unavailable when fetching status for {container_name}")
            return DockerStatus(exists=False, status="error", details="Docker client unavailable")
        try:
            container = self.client.containers.get(container_name)
            is_running = container.status == "running"
            state = container.attrs.get("State", {})
            health = state.get("Health", {}).get("Status", "healthy" if is_running else "stopped")
            return DockerStatus(
                exists=True,
                running=is_running,
                health=health,
                status=container.status,
                details=state.get("Status", "unknown"),
            )
        except NotFound:
            self.logger.debug(f"Container not found: {container_name}")
            return DockerStatus(exists=False, status="no_container", details="Container not found")
        except Exception as e:
            self.logger.exception(f"Docker error for {container_name}: {e}")
            return DockerStatus(exists=False, status="error", details=str(e))

    def get_container_logs(self, container_name: str, tail: int = 100) -> str:
        """
        Get the logs from a container.
        
        Args:
            container_name: Name of the container
            tail: Number of log lines to retrieve
            
        Returns:
            String containing container logs
        """
        if not self.client:
            self.logger.warning(f"Docker client unavailable when fetching logs for {container_name}")
            return "Docker client unavailable"
        try:
            container = self.client.containers.get(container_name)
            self.logger.debug(f"Retrieving {tail} log lines from {container_name}")
            return container.logs(tail=tail).decode("utf-8")
        except Exception as e:
            self.logger.exception(f"Log retrieval failed for {container_name}: {e}")
            return f"Log retrieval error: {e}"

    def cleanup_containers(self) -> None:
        """Remove stopped containers older than 24 hours."""
        if not self.client:
            self.logger.warning("Docker client unavailable for container cleanup")
            return
        try:
            self.logger.info("Cleaning up stopped containers older than 24 hours")
            result = self.client.containers.prune(filters={"until": "24h"})
            if 'ContainersDeleted' in result and result['ContainersDeleted']:
                self.logger.info(f"Removed {len(result['ContainersDeleted'])} containers")
        except Exception as e:
            self.logger.exception(f"Container cleanup failed: {e}")

# =============================================================================
# System Health Monitoring
# =============================================================================
class SystemHealthMonitor:
    """Monitors system health metrics including disk space and Docker status."""
    
    _logger = create_logger_for_component('system_health')
    
    @classmethod
    def check_disk_space(cls) -> bool:
        """
        Check if disk space is sufficient (< 90% used).
        
        Returns:
            True if disk space is sufficient, False otherwise
        """
        try:
            if os.name == "nt":
                cls._logger.debug("Checking disk space on Windows")
                result = subprocess.run(
                    ["wmic", "logicaldisk", "get", "size,freespace,caption"],
                    capture_output=True, text=True, encoding='utf-8', errors='replace', check=True,
                )
                lines = result.stdout.strip().split("\n")[1:]
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            free = int(parts[1])
                            total = int(parts[2])
                            usage_percent = (total - free) / total * 100 if total > 0 else 0
                            if total > 0 and usage_percent > 90:
                                cls._logger.warning(f"Disk usage critical for {parts[0]}: {usage_percent:.1f}%")
                                return False
                        except ValueError:
                            continue
            else:
                cls._logger.debug("Checking disk space on Unix")
                result = subprocess.run(
                    ["df", "-h"], capture_output=True, text=True, check=True
                )
                lines = result.stdout.split("\n")[1:]
                critical_disks = []
                for line in lines:
                    if line and (fields := line.split()) and len(fields) >= 5:
                        usage_percent = int(fields[4].rstrip("%"))
                        if usage_percent > 90:
                            critical_disks.append(f"{fields[5]} ({usage_percent}%)")
                
                if critical_disks:
                    cls._logger.warning(f"Disk usage critical: {', '.join(critical_disks)}")
                    return False
            
            cls._logger.debug("Disk space check passed")
            return True
        except Exception as e:
            cls._logger.exception(f"Disk check failed: {e}")
            return False

    @classmethod
    def check_health(cls, docker_client: Optional[docker.DockerClient]) -> bool:
        """
        Check overall system health including Docker connectivity.
        
        Args:
            docker_client: Docker client to check
            
        Returns:
            True if system is healthy, False otherwise
        """
        if not docker_client:
            cls._logger.error("Docker client unavailable for health check")
            return False
        try:
            cls._logger.debug("Pinging Docker daemon")
            docker_client.ping()
            return cls.check_disk_space()
        except Exception as e:
            cls._logger.exception(f"Docker health check failed: {e}")
            return False

# =============================================================================
# Port Management
# =============================================================================
class PortManager:
    """Manages port allocations for application containers."""
    
    BASE_BACKEND_PORT = 5001
    BASE_FRONTEND_PORT = 5501
    PORTS_PER_APP = 2
    BUFFER_PORTS = 20
    APPS_PER_MODEL = 30
    
    _logger = create_logger_for_component('port_manager')

    @classmethod
    def get_port_range(cls, model_idx: int) -> Dict[str, Dict[str, int]]:
        """
        Get the port range for a model's applications.
        
        Args:
            model_idx: The index of the model in AI_MODELS
            
        Returns:
            Dictionary with start and end ports for backend and frontend
        """
        total_needed = cls.APPS_PER_MODEL * cls.PORTS_PER_APP + cls.BUFFER_PORTS
        return {
            "backend": {
                "start": cls.BASE_BACKEND_PORT + (model_idx * total_needed),
                "end": cls.BASE_BACKEND_PORT + ((model_idx + 1) * total_needed) - cls.BUFFER_PORTS,
            },
            "frontend": {
                "start": cls.BASE_FRONTEND_PORT + (model_idx * total_needed),
                "end": cls.BASE_FRONTEND_PORT + ((model_idx + 1) * total_needed) - cls.BUFFER_PORTS,
            },
        }

    @classmethod
    def get_app_ports(cls, model_idx: int, app_num: int) -> Dict[str, int]:
        """
        Get the specific ports for an application.
        
        Args:
            model_idx: The index of the model in AI_MODELS
            app_num: The application number
            
        Returns:
            Dictionary with backend and frontend port numbers
        """
        rng = cls.get_port_range(model_idx)
        ports = {
            "backend": rng["backend"]["start"] + (app_num - 1) * cls.PORTS_PER_APP,
            "frontend": rng["frontend"]["start"] + (app_num - 1) * cls.PORTS_PER_APP,
        }
        cls._logger.debug(f"Allocated ports for model_idx={model_idx}, app_num={app_num}: {ports}")
        return ports

# =============================================================================
# ZAP Scanner Integration
# =============================================================================
class ScanManager:
    """Manages ZAP scans and their states."""
    
    def __init__(self):
        """Initialize scan manager with empty scan dictionary."""
        self.logger = create_logger_for_component('scan_manager')
        self.scans: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.logger.info("Scan manager initialized")

    def create_scan(self, model: str, app_num: int, options: dict) -> str:
        """
        Create a new scan entry.
        
        Args:
            model: Model name
            app_num: App number
            options: Scan options
            
        Returns:
            Generated scan ID
        """
        scan_id = f"{model}-{app_num}-{int(time.time())}"
        with self._lock:
            self.scans[scan_id] = {
                "status": "Starting",
                "progress": 0,
                "scanner": None,
                "start_time": datetime.now().isoformat(),
                "options": options,
                "model": model,
                "app_num": app_num,
            }
        self.logger.info(f"Created new scan with ID: {scan_id} for {model}/app{app_num}")
        return scan_id

    def get_scan(self, model: str, app_num: int) -> Optional[dict]:
        """
        Get the latest scan for a given model/app combination.
        
        Args:
            model: Model name
            app_num: App number
            
        Returns:
            Latest scan details or None if no scan exists
        """
        with self._lock:
            matching_scans = [
                (sid, scan) for sid, scan in self.scans.items()
                if sid.startswith(f"{model}-{app_num}-")
            ]
            if not matching_scans:
                return None
            latest_scan = max(matching_scans, key=lambda x: x[0])[1]
            self.logger.debug(f"Retrieved latest scan for {model}/app{app_num}: {latest_scan.get('status', 'Unknown')}")
            return latest_scan

    def update_scan(self, scan_id: str, **kwargs):
        """
        Update scan details.
        
        Args:
            scan_id: ID of the scan to update
            **kwargs: Fields to update
        """
        with self._lock:
            if scan_id in self.scans:
                self.scans[scan_id].update(kwargs)
                status_update = kwargs.get('status', None)
                if status_update:
                    self.logger.info(f"Updated scan {scan_id} status to: {status_update}")

    def cleanup_old_scans(self):
        """Remove completed scans older than 1 hour."""
        current_time = time.time()
        with self._lock:
            before_count = len(self.scans)
            self.scans = {
                sid: scan for sid, scan in self.scans.items()
                if scan["status"] not in ("Complete", "Failed", "Stopped") or
                current_time - int(sid.split("-")[-1]) < 3600
            }
            after_count = len(self.scans)
            
            if before_count > after_count:
                self.logger.info(f"Cleaned up {before_count - after_count} old scans")

# =============================================================================
# AI Service Integration 
# =============================================================================
def call_ai_service(model: str, prompt: str) -> str:
    """
    Call an AI service with a prompt and return the response.
    
    Args:
        model: AI model to use
        prompt: Prompt to send to the model
        
    Returns:
        AI-generated response
    """
    ai_logger = create_logger_for_component('ai_service')
    ai_logger.info(f"Calling AI service with model: {model}, prompt length: {len(prompt)} chars")
    # Replace with actual integration logic
    return "AI analysis result"

# =============================================================================
# Database Management
# =============================================================================
class DatabaseManager:
    """Manages database operations for storing scan results."""
    
    def __init__(self, db_path="scans.db"):
        """
        Initialize database connection and tables.
        
        Args:
            db_path: Path to the SQLite database file
        """
        import sqlite3
        self.logger = create_logger_for_component('database')
        self.logger.info(f"Initializing database connection: {db_path}")
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self):
        """Create database tables if they don't exist."""
        self.logger.debug("Creating database tables if they don't exist")
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS security_scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_type TEXT NOT NULL,
                model TEXT NOT NULL,
                app_num INTEGER NOT NULL,
                issues TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS performance_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT NOT NULL,
                port INTEGER NOT NULL,
                num_users INTEGER NOT NULL,
                duration INTEGER NOT NULL,
                results TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
    def store_security_scan(self, scan_type, model, app_num, issues):
        """
        Store security scan results.
        
        Args:
            scan_type: Type of security scan
            model: Model name
            app_num: App number
            issues: Issues found in the scan
            
        Returns:
            ID of the new database record
        """
        issues_json = json.dumps(issues)
        self.logger.info(f"Storing {scan_type} scan results for {model}/app{app_num} with {len(issues)} issues")
        
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO security_scans (scan_type, model, app_num, issues) VALUES (?, ?, ?, ?)",
            (scan_type, model, app_num, issues_json)
        )
        self.conn.commit()
        last_id = cursor.lastrowid
        
        self.logger.debug(f"Security scan stored with ID: {last_id}")
        return last_id
        
    def get_security_scans(self, model=None, app_num=None, limit=10):
        """
        Retrieve security scan results with optional filters.
        
        Args:
            model: Optional model filter
            app_num: Optional app number filter
            limit: Maximum number of records to return
            
        Returns:
            List of scan results
        """
        cursor = self.conn.cursor()
        query = "SELECT * FROM security_scans"
        params = []
        
        filter_conditions = []
        if model:
            filter_conditions.append("model = ?")
            params.append(model)
        if app_num:
            filter_conditions.append("app_num = ?")
            params.append(app_num)
            
        if filter_conditions:
            query += " WHERE " + " AND ".join(filter_conditions)
                
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        self.logger.debug(f"Executing query: {query} with params: {params}")
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        self.logger.info(f"Retrieved {len(results)} security scans")
        return results
        
    def __del__(self):
        """Close database connection when object is deleted."""
        if hasattr(self, 'conn'):
            self.logger.debug("Closing database connection")
            self.conn.close()