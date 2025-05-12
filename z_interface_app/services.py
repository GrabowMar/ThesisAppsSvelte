"""
Service components for the AI Model Management System.
This module contains service classes that implement core business logic.

Optimized to reduce cleanup frequency and improve overall organization.
"""

# =============================================================================
# Standard Library Imports
# =============================================================================
import enum
import json
import os
import sqlite3
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, cast

# =============================================================================
# Third-Party Imports
# =============================================================================
import docker
from docker.errors import NotFound

# =============================================================================
# Custom Module Imports
# =============================================================================
from zap_scanner import create_scanner
from logging_service import create_logger_for_component

# =============================================================================
# Configuration Module
# =============================================================================
class Config:
    """Central configuration class for the application."""
    
    # Docker Manager Configuration
    DOCKER_TIMEOUT_SECONDS = int(os.getenv("DOCKER_TIMEOUT", "10"))
    CACHE_DURATION_SECONDS = int(os.getenv("CACHE_DURATION", "5"))
    CONTAINER_PRUNE_FILTER_HOURS = os.getenv("CONTAINER_PRUNE_FILTER", "24h")
    CONTAINER_CLEANUP_INTERVAL_MINUTES = int(os.getenv("CONTAINER_CLEANUP_INTERVAL", "60"))
    
    # Windows uses a different Docker socket path than Unix-based systems
    WINDOWS_DOCKER_HOST = os.getenv("WINDOWS_DOCKER_HOST", "npipe:////./pipe/docker_engine")
    UNIX_DOCKER_HOST = os.getenv("UNIX_DOCKER_HOST", "unix://var/run/docker.sock")
    
    # SystemHealthMonitor Configuration
    DISK_USAGE_THRESHOLD_PERCENT = int(os.getenv("DISK_USAGE_THRESHOLD", "90"))
    HEALTH_CHECK_INTERVAL_SECONDS = int(os.getenv("HEALTH_CHECK_INTERVAL", "300"))
    
    # ScanManager Configuration
    SCAN_CLEANUP_HOURS = int(os.getenv("SCAN_CLEANUP_HOURS", "1"))
    
    # DatabaseManager Configuration
    DB_PATH = os.getenv("DB_PATH", "scans.db")
    DEFAULT_SCAN_LIMIT = int(os.getenv("DEFAULT_SCAN_LIMIT", "10"))
    
    # Port Manager Configuration
    BASE_BACKEND_PORT = int(os.getenv("BASE_BACKEND_PORT", "5001"))
    BASE_FRONTEND_PORT = int(os.getenv("BASE_FRONTEND_PORT", "5501"))
    PORTS_PER_APP = int(os.getenv("PORTS_PER_APP", "2"))
    BUFFER_PORTS = int(os.getenv("BUFFER_PORTS", "20"))
    APPS_PER_MODEL = int(os.getenv("APPS_PER_MODEL", "30"))

# =============================================================================
# Module Constants
# =============================================================================
# ScanManager Status Enum
class ScanStatus(enum.Enum):
    """Enumeration for ZAP scan statuses."""
    STARTING = "Starting"
    SPIDERING = "Spidering"
    SCANNING = "Scanning"
    COMPLETE = "Complete"
    FAILED = "Failed"
    STOPPED = "Stopped"
    ERROR = "Error"

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
        self._cache_duration = Config.CACHE_DURATION_SECONDS
        
        # Add last cleanup timestamp to implement throttling
        self._last_cleanup_time = 0.0
        self._cleanup_interval = Config.CONTAINER_CLEANUP_INTERVAL_MINUTES * 60  # Convert to seconds
        
        if self.client:
            self.logger.info(
                f"Docker manager initialized (Cache: {self._cache_duration}s, "
                f"Cleanup interval: {Config.CONTAINER_CLEANUP_INTERVAL_MINUTES}m)"
            )
        else:
            self.logger.warning(
                "Docker manager initialized WITHOUT a valid client."
            )

    def _create_docker_client(self) -> Optional[docker.DockerClient]:
        """
        Create a Docker client with configured timeout.

        Returns:
            Docker client instance or None if creation fails
        """
        try:
            default_host = Config.WINDOWS_DOCKER_HOST if os.name == 'nt' else Config.UNIX_DOCKER_HOST
            docker_host = os.getenv("DOCKER_HOST", default_host)
            timeout = Config.DOCKER_TIMEOUT_SECONDS

            self.logger.debug(
                f"Creating Docker client with host: {docker_host}, timeout: {timeout}s"
            )
            client = docker.DockerClient(base_url=docker_host, timeout=timeout)
            # Test connection immediately
            client.ping()
            self.logger.info("Docker client created and connection verified.")
            return client
        except Exception as e:
            self.logger.exception(f"Docker client creation or connection failed: {e}")
            return None

    def get_container_status(self, container_name: str) -> 'DockerStatus':
        """
        Get the status of a container with caching.

        Args:
            container_name: Name of the container

        Returns:
            DockerStatus object with container status details
        """
        # Imported locally to avoid circular dependency with utils.py
        from utils import DockerStatus

        now = time.time()
        if container_name in self._cache:
            timestamp, status = self._cache[container_name]
            if now - timestamp < self._cache_duration:
                self.logger.debug(f"Using cached status for {container_name}")
                return status

        # If client is unavailable after init, return error status immediately
        if not self.client:
            self.logger.warning(f"Docker client unavailable when fetching status for {container_name}")
            status = DockerStatus(exists=False, status="error", details="Docker client unavailable")
        else:
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
        # Imported locally to avoid circular dependency with utils.py
        from utils import DockerStatus

        # This check is redundant if get_container_status checks first,
        # but kept for safety if called directly.
        if not self.client:
            self.logger.warning(f"Docker client unavailable when fetching status for {container_name}")
            return DockerStatus(exists=False, status="error", details="Docker client unavailable")

        try:
            self.logger.debug(f"Fetching status for container: {container_name}")
            container = self.client.containers.get(container_name)
            container_status_str = container.status
            is_running = container_status_str == "running"

            # Simplified health status extraction
            state = container.attrs.get("State", {})
            health_info = state.get("Health")
            
            if health_info and isinstance(health_info, dict):
                health_status = health_info.get("Status", "checking")
            elif is_running:
                health_status = "healthy"  # Default for running containers without health check
            else:
                health_status = container_status_str

            self.logger.debug(
                f"Status for {container_name}: running={is_running}, "
                f"health='{health_status}', docker_status='{container_status_str}'"
            )
            
            return DockerStatus(
                exists=True,
                running=is_running,
                health=health_status,
                status=container_status_str,
                details=state.get("Status", "unknown"),
            )
        except NotFound:
            self.logger.debug(f"Container not found: {container_name}")
            return DockerStatus(exists=False, status="no_container", details="Container not found")
        except Exception as e:
            self.logger.exception(f"Docker error fetching status for {container_name}: {e}")
            return DockerStatus(exists=False, status="error", details=str(e))

    def get_container_logs(self, container_name: str, tail: int = 100) -> str:
        """
        Get the logs from a container.

        Args:
            container_name: Name of the container
            tail: Number of log lines to retrieve

        Returns:
            String containing container logs or an error message.
        """
        if not self.client:
            self.logger.warning(f"Docker client unavailable when fetching logs for {container_name}")
            return "Docker client unavailable"
        try:
            container = self.client.containers.get(container_name)
            self.logger.debug(f"Retrieving {tail} log lines from {container_name}")
            logs = container.logs(tail=tail).decode("utf-8", errors="replace")
            return logs
        except NotFound:
            self.logger.warning(f"Cannot get logs, container not found: {container_name}")
            return f"Error: Container '{container_name}' not found."
        except Exception as e:
            self.logger.exception(f"Log retrieval failed for {container_name}: {e}")
            return f"Log retrieval error: {e}"

    def cleanup_containers(self, force: bool = False) -> None:
        """
        Remove stopped containers older than the configured duration.
        
        Args:
            force: If True, ignore the time throttling and perform cleanup anyway
        """
        now = time.time()
        # Only clean up if enough time has passed since last cleanup or if forced
        if not force and (now - self._last_cleanup_time < self._cleanup_interval):
            self.logger.debug(
                f"Skipping container cleanup, last performed {int((now - self._last_cleanup_time) / 60)} minutes ago"
            )
            return

        if not self.client:
            self.logger.warning("Docker client unavailable for container cleanup")
            return
            
        try:
            filter_duration = Config.CONTAINER_PRUNE_FILTER_HOURS
            self.logger.info(f"Cleaning up stopped containers older than {filter_duration}")
            result = self.client.containers.prune(filters={"until": filter_duration})
            containers_deleted = result.get('ContainersDeleted', [])
            space_reclaimed = result.get('SpaceReclaimed', 0)

            if containers_deleted:
                self.logger.info(
                   f"Removed {len(containers_deleted)} containers, "
                   f"reclaimed approx {space_reclaimed or 0} bytes."
                )
            else:
                self.logger.info("No containers found matching the cleanup criteria.")
                
            # Update the last cleanup time
            self._last_cleanup_time = now
        except Exception as e:
            self.logger.exception(f"Container cleanup failed: {e}")

# =============================================================================
# Cleanup Scheduler
# =============================================================================
class CleanupScheduler:
    """Scheduler for periodic cleanup tasks."""

    def __init__(self, docker_manager: DockerManager):
        """
        Initialize the cleanup scheduler.
        
        Args:
            docker_manager: Docker manager instance to use for cleanup operations
        """
        self.docker_manager = docker_manager
        self.logger = create_logger_for_component('cleanup_scheduler')
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        """Start the cleanup scheduler thread."""
        if self._thread is not None and self._thread.is_alive():
            self.logger.warning("Cleanup scheduler already running")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._scheduler_loop)
        self._thread.daemon = True
        self._thread.start()
        self.logger.info("Cleanup scheduler started")

    def stop(self):
        """Stop the cleanup scheduler thread."""
        if self._thread is None or not self._thread.is_alive():
            return

        self.logger.info("Stopping cleanup scheduler")
        self._stop_event.set()
        self._thread.join(timeout=5.0)
        self._thread = None
        self.logger.info("Cleanup scheduler stopped")

    def _scheduler_loop(self):
        """Main scheduler loop that runs cleanup tasks periodically."""
        interval_seconds = Config.CONTAINER_CLEANUP_INTERVAL_MINUTES * 60  # Convert to seconds
        
        while not self._stop_event.is_set():
            try:
                # Run container cleanup with force=True to bypass throttling
                self.docker_manager.cleanup_containers(force=True)
                
                # Sleep for the interval or until stopped
                self._stop_event.wait(interval_seconds)
            except Exception as e:
                self.logger.exception(f"Error in cleanup scheduler: {e}")
                # Sleep a bit after an error to avoid tight loop
                time.sleep(10)

# =============================================================================
# System Health Monitoring
# =============================================================================
class SystemHealthMonitor:
    """Monitors system health metrics including disk space and Docker status."""

    _logger = create_logger_for_component('system_health')
    _last_check_time = 0.0
    _check_interval = Config.HEALTH_CHECK_INTERVAL_SECONDS
    _last_check_results = {}

    @classmethod
    def check_disk_space(cls, threshold: int = Config.DISK_USAGE_THRESHOLD_PERCENT) -> bool:
        """
        Check if disk space usage is below a threshold.

        Args:
            threshold: The percentage threshold for disk usage.

        Returns:
            True if disk space is sufficient on all relevant drives, False otherwise.
        """
        try:
            if os.name == "nt":
                return cls._check_disk_space_windows(threshold)
            else:
                return cls._check_disk_space_unix(threshold)
        except Exception as e:
            cls._logger.exception(f"Unexpected error during disk check: {e}")
            return False
    
    @classmethod
    def _check_disk_space_windows(cls, threshold: int) -> bool:
        """Check disk space on Windows systems."""
        try:
            cls._logger.debug("Checking disk space on Windows using 'wmic'")
            # Expected `wmic` output columns: Caption FreeSpace Size
            result = subprocess.run(
                ["wmic", "logicaldisk", "get", "size,freespace,caption"],
                capture_output=True, text=True, encoding='utf-8',
                errors='replace', check=True, 
                creationflags=subprocess.CREATE_NO_WINDOW  # Hide console window
            )
            lines = result.stdout.strip().splitlines()[1:]
            critical_disks = []
            
            for line in lines:
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        # WMIC provides Caption, FreeSpace, Size
                        drive_letter = parts[0]
                        free = int(parts[1])
                        total = int(parts[2])
                        if total > 0:
                            usage_percent = (total - free) / total * 100
                            if usage_percent > threshold:
                                critical_disks.append(f"{drive_letter} ({usage_percent:.1f}%)")
                    except (ValueError, IndexError):
                        cls._logger.warning(f"Could not parse wmic line: '{line}'")
                        continue  # Skip malformed lines
                        
            if critical_disks:
                cls._logger.warning(f"Disk usage critical (>{threshold}%): {', '.join(critical_disks)}")
                return False
                
            return True
            
        except FileNotFoundError as fnf_error:
            cls._logger.error(f"Disk check command not found: {fnf_error}. Cannot check disk space.")
            return False  # Cannot verify, assume unhealthy
        except subprocess.CalledProcessError as cpe:
            cls._logger.error(f"Disk check command failed (Code {cpe.returncode}): {cpe.stderr or cpe.stdout}")
            return False
    
    @classmethod
    def _check_disk_space_unix(cls, threshold: int) -> bool:
        """Check disk space on Unix-based systems."""
        try:
            cls._logger.debug("Checking disk space on Unix using 'df'")
            # Expected `df` output relevant columns (POSIX): Use% Mounted on
            # Use -P flag for POSIX standard output format, avoiding line wrapping issues.
            result = subprocess.run(
                ["df", "-P"], capture_output=True, text=True, check=True
            )
            lines = result.stdout.strip().splitlines()[1:]
            critical_disks = []
            
            for line in lines:
                # Fields typically: Filesystem Size Used Avail Use% Mounted on
                fields = line.split()
                if len(fields) >= 6:
                    try:
                        # Use% is the 5th field (index 4), Mounted on is 6th (index 5)
                        usage_percent_str = fields[4].rstrip("%")
                        usage_percent = int(usage_percent_str)
                        mount_point = fields[5]
                        if usage_percent > threshold:
                            critical_disks.append(f"{mount_point} ({usage_percent}%)")
                    except (ValueError, IndexError):
                        cls._logger.warning(f"Could not parse df line: '{line}'")
                        continue  # Skip malformed lines

            if critical_disks:
                cls._logger.warning(f"Disk usage critical (>{threshold}%): {', '.join(critical_disks)}")
                return False
                
            cls._logger.debug(f"Disk space check passed (Usage <= {threshold}%)")
            return True
            
        except FileNotFoundError as fnf_error:
            cls._logger.error(f"Disk check command not found: {fnf_error}. Cannot check disk space.")
            return False  # Cannot verify, assume unhealthy
        except subprocess.CalledProcessError as cpe:
            cls._logger.error(f"Disk check command failed (Code {cpe.returncode}): {cpe.stderr or cpe.stdout}")
            return False

    @classmethod
    def check_docker_connection(cls, docker_client: Optional[docker.DockerClient]) -> bool:
        """Checks if the Docker daemon is reachable."""
        if not docker_client:
            cls._logger.warning("Docker client is None, cannot check connection.")
            return False
        try:
            cls._logger.debug("Pinging Docker daemon...")
            docker_client.ping()
            cls._logger.debug("Docker daemon ping successful.")
            return True
        except Exception as e:
            cls._logger.error(f"Docker daemon ping failed: {e}")
            return False

    @classmethod
    def check_health(cls, docker_client: Optional[docker.DockerClient]) -> bool:
        """
        Check overall system health including Docker connectivity and disk space.
        Uses cached results if checked recently.

        Args:
            docker_client: Docker client instance to check.

        Returns:
            True if system is considered healthy, False otherwise.
        """
        now = time.time()
        if now - cls._last_check_time < cls._check_interval:
            # Use cached results if we checked recently
            cls._logger.debug("Using cached health check results")
            return cls._last_check_results.get('is_healthy', False)

        cls._logger.info("Performing system health check...")
        docker_ok = cls.check_docker_connection(docker_client)
        disk_ok = cls.check_disk_space()  # Uses default threshold

        is_healthy = docker_ok and disk_ok
        if is_healthy:
            cls._logger.info("System health check passed (Docker connection OK, Disk space OK).")
        else:
            cls._logger.warning(f"System health check FAILED (Docker OK: {docker_ok}, Disk OK: {disk_ok}).")

        # Update cache
        cls._last_check_time = now
        cls._last_check_results = {
            'is_healthy': is_healthy,
            'docker_ok': docker_ok,
            'disk_ok': disk_ok
        }

        return is_healthy

# =============================================================================
# Port Management
# =============================================================================
class PortManager:
    """Manages port allocations for application containers."""

    _logger = create_logger_for_component('port_manager')

    @classmethod
    def get_port_range(cls, model_idx: int) -> Dict[str, Dict[str, int]]:
        """
        Get the port range for a model's applications.

        Args:
            model_idx: The index of the model (0-based).

        Returns:
            Dictionary with start and end ports for backend and frontend.
        """
        # Calculate the total span needed for one model's apps + buffer
        total_block_size = Config.APPS_PER_MODEL * Config.PORTS_PER_APP + Config.BUFFER_PORTS
        base_backend_offset = model_idx * total_block_size
        base_frontend_offset = model_idx * total_block_size

        backend_start = Config.BASE_BACKEND_PORT + base_backend_offset
        # End is the start of the *next* model's block, minus the buffer.
        # Or more simply, start + number of ports allocated for apps in this block.
        backend_end = backend_start + Config.APPS_PER_MODEL * Config.PORTS_PER_APP

        frontend_start = Config.BASE_FRONTEND_PORT + base_frontend_offset
        frontend_end = frontend_start + Config.APPS_PER_MODEL * Config.PORTS_PER_APP

        return {
            "backend": {"start": backend_start, "end": backend_end},
            "frontend": {"start": frontend_start, "end": frontend_end},
        }

    @classmethod
    def get_app_ports(cls, model_idx: int, app_num: int) -> Dict[str, int]:
        """
        Get the specific starting ports for an application instance's block.

        Args:
            model_idx: The index of the model (0-based).
            app_num: The application instance number (1-based index).

        Returns:
            Dictionary with the starting backend and frontend port numbers for this app instance.
            It's assumed this app might use ports starting from these up to
            port + cls.PORTS_PER_APP - 1.
        """
        if app_num <= 0:
            raise ValueError("app_num must be a positive integer (1-based).")
        if app_num > Config.APPS_PER_MODEL:
            raise ValueError(f"app_num {app_num} exceeds the maximum configured APPS_PER_MODEL ({Config.APPS_PER_MODEL}).")

        rng = cls.get_port_range(model_idx)

        # Calculate the starting port for the app's block
        # Offset is based on the 0-based index (app_num - 1) times the block size per app.
        backend_port = rng["backend"]["start"] + (app_num - 1) * Config.PORTS_PER_APP
        frontend_port = rng["frontend"]["start"] + (app_num - 1) * Config.PORTS_PER_APP

        # Validate the *starting* port is within the calculated range END.
        # The app might use ports up to start + PORTS_PER_APP - 1.
        # The range 'end' marks the start of the next block or buffer.
        if not (rng["backend"]["start"] <= backend_port < rng["backend"]["end"] and
                rng["frontend"]["start"] <= frontend_port < rng["frontend"]["end"]):
            cls._logger.error(
                f"Calculated starting ports for model {model_idx}, app {app_num} "
                f"are out of range: BE={backend_port}, FE={frontend_port}. "
                f"Range: BE[{rng['backend']['start']}-{rng['backend']['end']}), "
                f"FE[{rng['frontend']['start']}-{rng['frontend']['end']})"
            )
            # Raise error if the *start* port is already >= the end marker
            raise ValueError(
                f"Calculated starting ports for app {app_num} are outside "
                f"the allocated range for model index {model_idx}."
            )
            
        ports = {"backend": backend_port, "frontend": frontend_port}
        cls._logger.debug(
            f"Calculated starting ports for model_idx={model_idx}, app_num={app_num}: {ports}"
            f" (App block uses {Config.PORTS_PER_APP} ports)"
        )
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
        self._lock = threading.Lock()  # Protects access to self.scans
        self.logger.info("Scan manager initialized")

    def create_scan(self, model: str, app_num: int, options: dict) -> str:
        """
        Create a new scan entry and return its unique ID.

        Args:
            model: Model name
            app_num: App number
            options: Scan options (e.g., target URL, scan type)

        Returns:
            Generated scan ID
        """
        # Generate a unique scan ID including a timestamp
        scan_id = f"{model}-{app_num}-{int(time.time())}"
        with self._lock:
            self.scans[scan_id] = {
                "status": ScanStatus.STARTING.value,
                "progress": 0,
                "scanner": None,  # ZAP scanner instance will be stored here
                "start_time": datetime.now().isoformat(),
                "end_time": None,
                "options": options,
                "model": model,
                "app_num": app_num,
                "results": None,  # Store results here when complete
            }
        self.logger.info(f"Created new scan '{scan_id}' for {model}/app{app_num}")
        return scan_id

    def get_scan_details(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve details for a specific scan ID."""
        with self._lock:
            scan_data = self.scans.get(scan_id)
            if scan_data:
                # Return a copy to prevent external modification
                return {k: v for k, v in scan_data.items()}
            return None

    def get_latest_scan_for_app(self, model: str, app_num: int) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Get the ID and details of the latest scan for a given model/app.

        Args:
            model: Model name
            app_num: App number

        Returns:
            A tuple (scan_id, scan_details) or None if no scan exists.
        """
        with self._lock:
            # Find all scans matching the model and app number prefix
            matching_scans = [
                (sid, scan) for sid, scan in self.scans.items()
                if sid.startswith(f"{model}-{app_num}-")
            ]
            if not matching_scans:
                self.logger.debug(f"No scans found for {model}/app{app_num}")
                return None

            # Find the latest scan based on the timestamp in the ID (last part)
            try:
                # Sort by the integer timestamp part of the scan ID descending
                latest_scan_id, latest_scan_data = max(
                    matching_scans, 
                    key=lambda item: int(item[0].split('-')[-1])
                )
                self.logger.debug(f"Retrieved latest scan for {model}/app{app_num}: ID={latest_scan_id}")
                # Return a copy of the details dict
                return latest_scan_id, {k: v for k, v in latest_scan_data.items()}
            except (ValueError, IndexError) as e:
                self.logger.error(f"Error parsing scan IDs for {model}/app{app_num}: {e}")
                return None

    def update_scan(self, scan_id: str, **kwargs: Any) -> bool:
        """
        Update scan details (status, progress, results, etc.).

        Args:
            scan_id: ID of the scan to update.
            **kwargs: Fields and values to update (e.g., status="Running", progress=50).
            
        Returns:
            True if update was successful, False if scan_id not found
        """
        with self._lock:
            if scan_id in self.scans:
                # Update timestamp if status changes to a terminal state
                if 'status' in kwargs and kwargs['status'] in (
                    ScanStatus.COMPLETE.value,
                    ScanStatus.FAILED.value,
                    ScanStatus.STOPPED.value,
                    ScanStatus.ERROR.value
                ):
                    kwargs.setdefault('end_time', datetime.now().isoformat())

                self.scans[scan_id].update(kwargs)
                # Log significant updates like status changes
                status_update = kwargs.get('status')
                progress_update = kwargs.get('progress')
                
                if status_update:
                    self.logger.info(f"Updated scan '{scan_id}' status to: {status_update}")
                elif progress_update is not None:
                    self.logger.debug(f"Updated scan '{scan_id}' progress to: {progress_update}%")
                    
                return True
            else:
                self.logger.warning(f"Attempted to update non-existent scan ID: {scan_id}")
                return False

    def cleanup_old_scans(self, max_age: timedelta = timedelta(hours=Config.SCAN_CLEANUP_HOURS)) -> int:
        """
        Remove completed or failed scans older than max_age.
        
        Args:
            max_age: Maximum age for scans to keep
            
        Returns:
            Number of cleaned up scans
        """
        cleanup_count = 0
        current_time = datetime.now()
        terminal_statuses = {
            ScanStatus.COMPLETE.value,
            ScanStatus.FAILED.value,
            ScanStatus.STOPPED.value,
            ScanStatus.ERROR.value
        }

        with self._lock:
            scan_ids_to_remove = []
            for scan_id, scan in self.scans.items():
                # Check if scan is in a terminal state
                if scan.get("status") in terminal_statuses:
                    try:
                        # Try parsing end_time first, fallback to start_time/ID timestamp
                        completion_time_str = scan.get("end_time") or scan.get("start_time")
                        
                        if completion_time_str:
                            completion_time = datetime.fromisoformat(completion_time_str)
                        else:
                            # Fallback: Extract timestamp from ID if times are missing
                            # Assumes scan_id format is "model-app_num-timestamp"
                            scan_timestamp_unix = int(scan_id.split("-")[-1])
                            completion_time = datetime.fromtimestamp(scan_timestamp_unix)

                        if current_time - completion_time > max_age:
                            scan_ids_to_remove.append(scan_id)
                            self.logger.debug(
                                f"Marking old scan '{scan_id}' for removal "
                                f"(age: {current_time - completion_time})"
                            )

                    except (ValueError, IndexError, TypeError) as e:
                        self.logger.warning(
                            f"Could not determine age for scan '{scan_id}', "
                            f"skipping cleanup check: {e}"
                        )

            for scan_id in scan_ids_to_remove:
                del self.scans[scan_id]
                cleanup_count += 1

        if cleanup_count > 0:
            self.logger.info(f"Cleaned up {cleanup_count} old scans (older than {max_age}).")
        else:
            self.logger.debug("No old scans found matching cleanup criteria.")
            
        return cleanup_count

# =============================================================================
# AI Service Integration Placeholder
# =============================================================================
def call_ai_service(model: str, prompt: str) -> str:
    """
    Placeholder function to call an external AI service.

    Args:
        model: AI model identifier.
        prompt: Prompt to send to the model.

    Returns:
        AI-generated response string (placeholder).
    """
    ai_logger = create_logger_for_component('ai_service')
    ai_logger.info(f"Calling AI service with model: {model}, prompt length: {len(prompt)} chars")
    # TODO: Replace with actual integration logic
    # Example:
    # try:
    #     response = requests.post("YOUR_AI_SERVICE_ENDPOINT", json={"model": model, "prompt": prompt}, timeout=30)
    #     response.raise_for_status() # Raise exception for bad status codes
    #     return response.json().get("response", "Error: No response field found")
    # except requests.exceptions.RequestException as e:
    #     ai_logger.exception(f"AI service call failed: {e}")
    #     return f"Error: AI service call failed - {e}"
    time.sleep(0.5)  # Simulate network delay
    return f"AI analysis result for model '{model}' based on provided prompt."

# =============================================================================
# Database Management
# =============================================================================
class DatabaseManager:
    """
    Manages database operations for storing scan results using SQLite.

    Implements context manager protocol for reliable connection handling.
    """

    def __init__(self, db_path: str = Config.DB_PATH):
        """
        Initialize database manager. Connection is established in __enter__.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.logger = create_logger_for_component('database')
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()  # Add lock to protect database operations
        self.logger.info(f"DatabaseManager initialized for path: {self.db_path}")

    def _connect(self) -> None:
        """Establish the database connection and create tables if needed."""
        if self.conn is None:
            try:
                self.logger.debug(f"Connecting to database: {self.db_path}")
                # Ensure directory exists
                db_dir = os.path.dirname(self.db_path)
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir)
                    self.logger.info(f"Created directory for database: {db_dir}")

                self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
                self.conn.row_factory = sqlite3.Row  # Access columns by name
                self._create_tables()
            except sqlite3.Error as e:
                self.logger.exception(f"Database connection or table creation failed: {e}")
                self.conn = None  # Ensure conn is None if connection failed
                raise  # Re-raise the exception

    def close(self) -> None:
        """Closes the database connection if it's open."""
        if self.conn is not None:
            try:
                self.logger.debug("Closing database connection.")
                self.conn.close()
            except sqlite3.Error as e:
                self.logger.exception(f"Error closing database connection: {e}")
            finally:
                self.conn = None  # Mark as closed

    def __enter__(self) -> 'DatabaseManager':
        """Context manager entry: establish connection."""
        self._connect()
        if self.conn is None:
            # If connection failed in _connect, raise an error
            raise sqlite3.OperationalError(f"Failed to establish database connection to {self.db_path}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit: close connection."""
        self.close()

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        if not self.conn:
            self.logger.error("Cannot create tables, database connection is not established.")
            return
        try:
            self.logger.debug("Ensuring database tables exist...")
            # Use TEXT for JSON data and DATETIME for timestamps
            self.conn.executescript('''
                CREATE TABLE IF NOT EXISTS security_scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_type TEXT NOT NULL,
                    model TEXT NOT NULL,
                    app_num INTEGER NOT NULL,
                    issues TEXT NOT NULL, -- Store as JSON text
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS performance_tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    num_users INTEGER NOT NULL,
                    duration INTEGER NOT NULL,
                    results TEXT NOT NULL, -- Store as JSON text
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            self.logger.exception(f"Failed to create database tables: {e}")
            raise  # Propagate error

    def store_security_scan(
        self, scan_type: str, model: str, app_num: int, issues: Union[List, Dict]
    ) -> Optional[int]:
        """
        Store security scan results in the database.

        Args:
            scan_type: Type of security scan (e.g., "Backend", "Frontend", "ZAP").
            model: Model name.
            app_num: App number.
            issues: List or Dict representing issues found (will be stored as JSON).

        Returns:
            The ID of the newly inserted record, or None if storage failed.
        """
        if not self.conn:
            self.logger.error("Cannot store security scan, database not connected.")
            return None
            
        with self._lock:  # Ensure thread safety
            try:
                issues_json = json.dumps(issues)
                num_issues = len(issues) if isinstance(issues, list) else 1 if issues else 0
                self.logger.info(
                    f"Storing {scan_type} scan results for {model}/app{app_num} with {num_issues} issues"
                )

                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT INTO security_scans (scan_type, model, app_num, issues) VALUES (?, ?, ?, ?)",
                    (scan_type, model, app_num, issues_json)
                )
                self.conn.commit()
                last_id = cursor.lastrowid
                self.logger.debug(f"Security scan stored with ID: {last_id}")
                return last_id
            except sqlite3.Error as e:
                self.logger.exception(f"Failed to store security scan for {model}/app{app_num}: {e}")
                self.conn.rollback()  # Rollback transaction on error
                return None
            except TypeError as e:
                self.logger.exception(f"Failed to serialize issues to JSON for {model}/app{app_num}: {e}")
                return None

    def get_security_scans(
        self, model: Optional[str] = None, app_num: Optional[int] = None, limit: int = Config.DEFAULT_SCAN_LIMIT
    ) -> List[sqlite3.Row]:
        """
        Retrieve security scan results with optional filters, ordered by newest first.

        Args:
            model: Optional model name filter.
            app_num: Optional app number filter.
            limit: Maximum number of records to return.

        Returns:
            A list of scan results (as sqlite3.Row objects), or an empty list on error/no results.
        """
        if not self.conn:
            self.logger.error("Cannot retrieve security scans, database not connected.")
            return []
            
        with self._lock:  # Ensure thread safety
            try:
                cursor = self.conn.cursor()
                query = "SELECT id, scan_type, model, app_num, issues, timestamp FROM security_scans"
                params: List[Any] = []

                filter_conditions = []
                if model is not None:
                    filter_conditions.append("model = ?")
                    params.append(model)
                if app_num is not None:
                    filter_conditions.append("app_num = ?")
                    params.append(app_num)

                if filter_conditions:
                    query += " WHERE " + " AND ".join(filter_conditions)

                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)

                self.logger.debug(f"Executing query: {query} with params: {params}")
                cursor.execute(query, params)
                results = cursor.fetchall()  # Returns list of Row objects

                self.logger.info(f"Retrieved {len(results)} security scans matching criteria.")
                return results

            except sqlite3.Error as e:
                self.logger.exception(f"Failed to retrieve security scans: {e}")
                return []

    def store_performance_test(
        self, model: str, port: int, num_users: int, duration: int, results: Dict[str, Any]
    ) -> Optional[int]:
        """
        Stores performance test results.
        
        Args:
            model: Model name
            port: Port number
            num_users: Number of simulated users
            duration: Test duration in seconds
            results: Test results as a dictionary
            
        Returns:
            The ID of the newly inserted record, or None if storage failed
        """
        if not self.conn:
            self.logger.error("Cannot store performance test, database not connected.")
            return None
            
        with self._lock:  # Ensure thread safety
            try:
                results_json = json.dumps(results)
                cursor = self.conn.cursor()
                cursor.execute(
                    """INSERT INTO performance_tests
                       (model, port, num_users, duration, results)
                       VALUES (?, ?, ?, ?, ?)""",
                    (model, port, num_users, duration, results_json)
                )
                self.conn.commit()
                last_id = cursor.lastrowid
                self.logger.debug(f"Performance test stored with ID: {last_id}")
                return last_id
            except sqlite3.Error as e:
                self.logger.exception(f"Failed to store performance test for {model}: {e}")
                self.conn.rollback()
                return None
            except TypeError as e:
                self.logger.exception(f"Failed to serialize performance results to JSON for {model}: {e}")
                return None

    def get_performance_tests(
        self, model: Optional[str] = None, limit: int = Config.DEFAULT_SCAN_LIMIT
    ) -> List[sqlite3.Row]:
        """
        Retrieves performance test results.
        
        Args:
            model: Optional model name filter
            limit: Maximum number of records to return
            
        Returns:
            A list of test results, or an empty list on error/no results
        """
        if not self.conn:
            self.logger.error("Cannot retrieve performance tests, database not connected.")
            return []
            
        with self._lock:  # Ensure thread safety
            try:
                cursor = self.conn.cursor()
                query = "SELECT * FROM performance_tests"
                params: List[Any] = []
                
                if model is not None:
                    query += " WHERE model = ?"
                    params.append(model)
                    
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                self.logger.info(f"Retrieved {len(results)} performance tests for model: {model or 'any'}")
                return results
                
            except sqlite3.Error as e:
                self.logger.exception(f"Failed to retrieve performance tests: {e}")
                return []

# =============================================================================
# Application Initialization
# =============================================================================
def initialize_application():
    """Initialize the application components and start background services."""
    logger = create_logger_for_component('app_init')
    logger.info("Initializing application components...")
    
    # Create Docker manager
    docker_manager = DockerManager()
    
    # Set up cleanup scheduler
    cleanup_scheduler = CleanupScheduler(docker_manager)
    cleanup_scheduler.start()
    
    # Perform initial health check
    health_ok = SystemHealthMonitor.check_health(docker_manager.client)
    if not health_ok:
        logger.warning("Initial health check failed, but continuing startup")
    
    # Initialize scan manager
    scan_manager = ScanManager()
    
    # Initialize database
    with DatabaseManager() as db:
        db._create_tables()
    
    # Return initialized components for use in the application
    return {
        "docker_manager": docker_manager,
        "cleanup_scheduler": cleanup_scheduler,
        "scan_manager": scan_manager
    }

# =============================================================================
# Modified Teardown Logic (to be used in Flask or similar web frameworks)
# =============================================================================
def teardown():
    """
    Perform resource cleanup during teardown.
    This function should be registered with the web framework's teardown handler.
    """
    logger = create_logger_for_component('teardown')
    logger.debug("Performing resource cleanup during teardown")
    
    # No Docker container cleanup on every request
    # Other necessary cleanup that should happen on each request can be added here
    
    # Close any other resources that need to be cleaned up per request
    pass  # No operation needed for basic teardown