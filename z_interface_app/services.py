import enum
import json
import os
import sqlite3
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, cast, TypeVar, Callable
from dataclasses import dataclass

import docker
from docker.errors import NotFound
from docker.models.containers import Container

from logging_service import create_logger_for_component

# Define TypeVar for generic functions
T = TypeVar('T')

# Define DockerStatus locally to break circular import
@dataclass
class DockerStatus:
    """Status information for a Docker container."""
    exists: bool = False
    running: bool = False
    health: str = "unknown"
    status: str = "unknown"
    details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "exists": self.exists,
            "running": self.running,
            "health": self.health,
            "status": self.status,
            "details": self.details
        }


def safe_int_env(key: str, default: int) -> int:
    """Safely parse an integer from environment variables with proper error handling."""
    value = os.getenv(key)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        logger = create_logger_for_component('config')
        logger.warning(f"Invalid integer value for {key}: '{value}', using default: {default}")
        return default


class Config:
    """Application configuration loaded from environment variables with safe parsing."""
    DOCKER_TIMEOUT_SECONDS = safe_int_env("DOCKER_TIMEOUT", 10)
    CACHE_DURATION_SECONDS = safe_int_env("CACHE_DURATION", 5)
    CONTAINER_PRUNE_FILTER_HOURS = os.getenv("CONTAINER_PRUNE_FILTER", "24h")
    CONTAINER_CLEANUP_INTERVAL_MINUTES = safe_int_env("CONTAINER_CLEANUP_INTERVAL", 60)
    WINDOWS_DOCKER_HOST = os.getenv("WINDOWS_DOCKER_HOST", "npipe:////./pipe/docker_engine")
    UNIX_DOCKER_HOST = os.getenv("UNIX_DOCKER_HOST", "unix://var/run/docker.sock")
    DISK_USAGE_THRESHOLD_PERCENT = safe_int_env("DISK_USAGE_THRESHOLD", 90)
    HEALTH_CHECK_INTERVAL_SECONDS = safe_int_env("HEALTH_CHECK_INTERVAL", 300)
    SCAN_CLEANUP_HOURS = safe_int_env("SCAN_CLEANUP_HOURS", 1)
    DB_PATH = os.getenv("DB_PATH", "scans.db")
    DEFAULT_SCAN_LIMIT = safe_int_env("DEFAULT_SCAN_LIMIT", 10)
    BASE_BACKEND_PORT = safe_int_env("BASE_BACKEND_PORT", 5001)
    BASE_FRONTEND_PORT = safe_int_env("BASE_FRONTEND_PORT", 5501)
    PORTS_PER_APP = safe_int_env("PORTS_PER_APP", 2)
    BUFFER_PORTS = safe_int_env("BUFFER_PORTS", 20)
    APPS_PER_MODEL = safe_int_env("APPS_PER_MODEL", 30)


class ScanStatus(enum.Enum):
    """Enum representing the status of a security scan."""
    NOT_RUN = "Not Run"
    STARTING = "Starting"
    SPIDERING = "Spidering"
    SCANNING = "Scanning"
    COMPLETE = "Complete"
    FAILED = "Failed"
    STOPPED = "Stopped"
    ERROR = "Error"


class DockerManager:
    """Manages Docker containers and their lifecycle."""
    def __init__(self, client: Optional[docker.DockerClient] = None) -> None:
        self.logger = create_logger_for_component('docker')
        self.client = client or self._create_docker_client()
        self._cache: Dict[str, Tuple[float, DockerStatus]] = {}
        self._cache_lock = threading.RLock()
        self._cache_duration = Config.CACHE_DURATION_SECONDS
        self._last_cleanup_time = 0.0
        self._cleanup_interval = Config.CONTAINER_CLEANUP_INTERVAL_MINUTES * 60
        self._get_container_lock = threading.RLock()

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
        """Create and initialize a Docker client based on configuration."""
        try:
            default_host = Config.WINDOWS_DOCKER_HOST if os.name == 'nt' else Config.UNIX_DOCKER_HOST
            docker_host = os.getenv("DOCKER_HOST", default_host)
            timeout = Config.DOCKER_TIMEOUT_SECONDS
            self.logger.debug(
                f"Creating Docker client with host: {docker_host}, timeout: {timeout}s"
            )
            client = docker.DockerClient(base_url=docker_host, timeout=timeout)
            
            # Verify connection with ping
            ping_success = False
            try:
                client.ping()
                ping_success = True
            except Exception as ping_err:
                self.logger.error(f"Docker ping failed: {ping_err}")
                
            if ping_success:
                self.logger.info("Docker client created and connection verified.")
                return client
            else:
                self.logger.error("Docker client created but connection verification failed.")
                return None
        except Exception as e:
            self.logger.exception(f"Docker client creation failed: {e}")
            return None

    def get_container_status(self, container_name: str) -> DockerStatus:
        """Get status for a container with caching for efficiency."""
        if not container_name or not isinstance(container_name, str):
            self.logger.warning(f"Invalid container name: {container_name}")
            return DockerStatus(exists=False, status="invalid", details="Invalid container name")
        
        with self._cache_lock:
            now = time.time()
            if container_name in self._cache:
                timestamp, status = self._cache[container_name]
                if now - timestamp < self._cache_duration:
                    self.logger.debug(f"Using cached status for {container_name}")
                    return status
        
        # Handle the case of an unavailable Docker client
        if not self.client:
            self.logger.warning(f"Docker client unavailable when fetching status for {container_name}")
            status = DockerStatus(exists=False, status="error", details="Docker client unavailable")
        else:
            status = self._fetch_container_status(container_name)
            
        with self._cache_lock:
            self._cache[container_name] = (now, status)
        return status

    def _fetch_container_status(self, container_name: str) -> DockerStatus:
        """Fetch the current status of a container from Docker."""
        try:
            self.logger.debug(f"Fetching status for container: {container_name}")
            
            with self._get_container_lock:
                container = self.client.containers.get(container_name)
                
            # Get container attributes and status
            container_status_str = container.status
            is_running = container_status_str == "running"
            state = container.attrs.get("State", {})
            health_info = state.get("Health")
            
            # Determine health status
            if health_info and isinstance(health_info, dict):
                health_status = health_info.get("Status", "checking")
            elif is_running:
                health_status = "healthy"
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

    def get_container(self, container_name: str) -> Optional[Container]:
        """Get a container object by name, with error handling."""
        if not self.client:
            self.logger.warning(f"Docker client unavailable when getting container {container_name}")
            return None
        
        try:
            with self._get_container_lock:
                return self.client.containers.get(container_name)
        except NotFound:
            self.logger.debug(f"Container not found: {container_name}")
            return None
        except Exception as e:
            self.logger.exception(f"Error getting container {container_name}: {e}")
            return None

    def get_container_logs(self, container_name: str, tail: int = 100) -> str:
        """Retrieve logs from a container."""
        if not self.client:
            self.logger.warning(f"Docker client unavailable when fetching logs for {container_name}")
            return "Docker client unavailable"
        
        container = self.get_container(container_name)
        if not container:
            return f"Error: Container '{container_name}' not found."
        
        try:
            logs = container.logs(tail=tail).decode("utf-8", errors="replace")
            return logs
        except Exception as e:
            self.logger.exception(f"Log retrieval failed for {container_name}: {e}")
            return f"Log retrieval error: {e}"

    def cleanup_containers(self, force: bool = False) -> None:
        """Clean up stopped containers based on age threshold."""
        now = time.time()
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
            
            try:
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
            except Exception as prune_error:
                self.logger.exception(f"Error during container prune operation: {prune_error}")
                
            # Also clear the status cache after cleanup
            with self._cache_lock:
                self._cache.clear()
                
            self._last_cleanup_time = now
        except Exception as e:
            self.logger.exception(f"Container cleanup failed: {e}")

    def restart_container(self, container_name: str, timeout: int = 10) -> Tuple[bool, str]:
        """Restart a container with proper error handling."""
        if not self.client:
            return False, "Docker client unavailable"
        
        container = self.get_container(container_name)
        if not container:
            return False, f"Container '{container_name}' not found"
        
        try:
            container.restart(timeout=timeout)
            self.logger.info(f"Container {container_name} restarted successfully")
            
            # Clear cache entry for this container
            with self._cache_lock:
                if container_name in self._cache:
                    del self._cache[container_name]
                    
            return True, f"Container {container_name} restarted successfully"
        except Exception as e:
            self.logger.exception(f"Error restarting container {container_name}: {e}")
            return False, f"Error restarting container: {str(e)}"


class CleanupScheduler:
    """Scheduler for running container cleanup tasks on a regular basis."""
    def __init__(self, docker_manager: DockerManager):
        self.docker_manager = docker_manager
        self.logger = create_logger_for_component('cleanup_scheduler')
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the cleanup scheduler thread if not already running."""
        if self._thread is not None and self._thread.is_alive():
            self.logger.warning("Cleanup scheduler already running")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._scheduler_loop, name="CleanupScheduler")
        self._thread.daemon = True
        self._thread.start()
        self.logger.info("Cleanup scheduler started")

    def stop(self) -> None:
        """Stop the cleanup scheduler thread if running."""
        if self._thread is None or not self._thread.is_alive():
            return
        self.logger.info("Stopping cleanup scheduler")
        self._stop_event.set()
        self._thread.join(timeout=5.0)
        self._thread = None
        self.logger.info("Cleanup scheduler stopped")

    def _scheduler_loop(self) -> None:
        """Main loop for the cleanup scheduler thread."""
        interval_seconds = Config.CONTAINER_CLEANUP_INTERVAL_MINUTES * 60
        while not self._stop_event.is_set():
            try:
                self.docker_manager.cleanup_containers(force=True)
                # Use event.wait instead of sleep for more responsive shutdown
                self._stop_event.wait(interval_seconds)
            except Exception as e:
                self.logger.exception(f"Error in cleanup scheduler: {e}")
                # Wait a shorter time on error before retrying
                self._stop_event.wait(10)


class SystemHealthMonitor:
    """Monitor system health metrics like disk space and Docker connectivity."""
    # Use a lock for thread safety with class variables
    _lock = threading.RLock()
    _logger = create_logger_for_component('system_health')
    _last_check_time = 0.0
    _check_interval = Config.HEALTH_CHECK_INTERVAL_SECONDS
    _last_check_results: Dict[str, Any] = {}

    @classmethod
    def check_disk_space(cls, threshold: int = Config.DISK_USAGE_THRESHOLD_PERCENT) -> bool:
        """Check if disk space usage is below threshold."""
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
            result = subprocess.run(
                ["wmic", "logicaldisk", "get", "size,freespace,caption"],
                capture_output=True, text=True, encoding='utf-8',
                errors='replace', check=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Safely get lines
            output_lines = result.stdout.strip().splitlines()
            if len(output_lines) <= 1:
                cls._logger.warning("Unexpected output format from wmic command: no drive data")
                return False
                
            lines = output_lines[1:]  # Skip header row
            critical_disks = []
            
            for line in lines:
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        drive_letter = parts[0]
                        free = int(parts[1])
                        total = int(parts[2])
                        if total > 0:
                            usage_percent = (total - free) / total * 100
                            if usage_percent > threshold:
                                critical_disks.append(f"{drive_letter} ({usage_percent:.1f}%)")
                    except (ValueError, IndexError):
                        cls._logger.warning(f"Could not parse wmic line: '{line}'")
                        continue
                        
            if critical_disks:
                cls._logger.warning(f"Disk usage critical (>{threshold}%): {', '.join(critical_disks)}")
                return False
            return True
        except FileNotFoundError as fnf_error:
            cls._logger.error(f"Disk check command not found: {fnf_error}. Cannot check disk space.")
            return False
        except subprocess.CalledProcessError as cpe:
            cls._logger.error(f"Disk check command failed (Code {cpe.returncode}): {cpe.stderr or cpe.stdout}")
            return False

    @classmethod
    def _check_disk_space_unix(cls, threshold: int) -> bool:
        """Check disk space on Unix/Linux systems."""
        try:
            cls._logger.debug("Checking disk space on Unix using 'df'")
            result = subprocess.run(
                ["df", "-P"], capture_output=True, text=True, check=True
            )
            
            # Safely get lines
            output_lines = result.stdout.strip().splitlines()
            if len(output_lines) <= 1:
                cls._logger.warning("Unexpected output format from df command: no filesystem data")
                return False
                
            lines = output_lines[1:]  # Skip header row
            critical_disks = []
            
            for line in lines:
                fields = line.split()
                if len(fields) >= 6:
                    try:
                        usage_percent_str = fields[4].rstrip("%")
                        usage_percent = int(usage_percent_str)
                        mount_point = fields[5]
                        if usage_percent > threshold:
                            critical_disks.append(f"{mount_point} ({usage_percent}%)")
                    except (ValueError, IndexError):
                        cls._logger.warning(f"Could not parse df line: '{line}'")
                        continue
                        
            if critical_disks:
                cls._logger.warning(f"Disk usage critical (>{threshold}%): {', '.join(critical_disks)}")
                return False
                
            cls._logger.debug(f"Disk space check passed (Usage <= {threshold}%)")
            return True
        except FileNotFoundError as fnf_error:
            cls._logger.error(f"Disk check command not found: {fnf_error}. Cannot check disk space.")
            return False
        except subprocess.CalledProcessError as cpe:
            cls._logger.error(f"Disk check command failed (Code {cpe.returncode}): {cpe.stderr or cpe.stdout}")
            return False

    @classmethod
    def check_docker_connection(cls, docker_client: Optional[docker.DockerClient]) -> bool:
        """Check if Docker daemon is responding."""
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
        """Check overall system health including disk space and Docker connectivity."""
        with cls._lock:
            now = time.time()
            if now - cls._last_check_time < cls._check_interval:
                cls._logger.debug("Using cached health check results")
                return cls._last_check_results.get('is_healthy', False)
                
            cls._logger.info("Performing system health check...")
            docker_ok = cls.check_docker_connection(docker_client)
            disk_ok = cls.check_disk_space()
            is_healthy = docker_ok and disk_ok
            
            if is_healthy:
                cls._logger.info("System health check passed (Docker connection OK, Disk space OK).")
            else:
                cls._logger.warning(f"System health check FAILED (Docker OK: {docker_ok}, Disk OK: {disk_ok}).")
                
            cls._last_check_time = now
            cls._last_check_results = {'is_healthy': is_healthy, 'docker_ok': docker_ok, 'disk_ok': disk_ok}
            return is_healthy


class PortManager:
    """Manage port allocation for applications across multiple models."""
    _logger = create_logger_for_component('port_manager')
    _model_index_cache = {}

    @classmethod
    def get_port_range(cls, model_idx: int) -> Dict[str, Dict[str, int]]:
        """Get port range allocated for a specific model index."""
        # Calculate single base offset since frontend and backend share the same offset
        total_block_size = Config.APPS_PER_MODEL * Config.PORTS_PER_APP + Config.BUFFER_PORTS
        base_offset = model_idx * total_block_size
        
        # Calculate port ranges
        backend_start = Config.BASE_BACKEND_PORT + base_offset
        backend_end = backend_start + (Config.APPS_PER_MODEL * Config.PORTS_PER_APP)
        frontend_start = Config.BASE_FRONTEND_PORT + base_offset
        frontend_end = frontend_start + (Config.APPS_PER_MODEL * Config.PORTS_PER_APP)
        
        return {
            "backend": {"start": backend_start, "end": backend_end},
            "frontend": {"start": frontend_start, "end": frontend_end},
        }

    @classmethod
    def get_app_ports(cls, model_idx: int, app_num: int) -> Dict[str, int]:
        """Get specific ports for an application within a model."""
        if app_num <= 0:
            raise ValueError("app_num must be a positive integer (1-based).")
            
        if app_num > Config.APPS_PER_MODEL:
            raise ValueError(f"app_num {app_num} exceeds the maximum configured APPS_PER_MODEL ({Config.APPS_PER_MODEL}).")
            
        # Get port ranges for the model
        rng = cls.get_port_range(model_idx)
        
        # Calculate app-specific ports
        backend_port = rng["backend"]["start"] + ((app_num - 1) * Config.PORTS_PER_APP)
        frontend_port = rng["frontend"]["start"] + ((app_num - 1) * Config.PORTS_PER_APP)
        
        # Validate that ports are within acceptable range
        if not (rng["backend"]["start"] <= backend_port < rng["backend"]["end"] and
                rng["frontend"]["start"] <= frontend_port < rng["frontend"]["end"]):
            # cls._logger.error(
            #     f"Calculated starting ports for model {model_idx}, app {app_num} "
            #     f"are out of range: BE={backend_port}, FE={frontend_port}. "
            #     f"Range: BE[{rng['backend']['start']}-{rng['backend']['end']}), "
            #     f"FE[{rng['frontend']['start']}-{rng['frontend']['end']})"
            # )
            pass
            # raise ValueError(
            #     f"Calculated starting ports for app {app_num} are outside "
            #     f"the allocated range for model index {model_idx}."
            # )
            
        ports = {"backend": backend_port, "frontend": frontend_port}
        # cls._logger.debug(
        #     f"Calculated starting ports for model_idx={model_idx}, app_num={app_num}: {ports}"
        #     f" (App block uses {Config.PORTS_PER_APP} ports)"
        # )
        return ports

    @classmethod
    def set_model_index_cache(cls, model_name_to_index: Dict[str, int]) -> None:
        """Set the model index cache for more efficient lookups."""
        cls._model_index_cache = model_name_to_index.copy()
        cls._logger.debug(f"Model index cache updated with {len(model_name_to_index)} entries")

    @classmethod
    def get_model_index(cls, model_name: str) -> Optional[int]:
        """Get the index for a model name from the cache."""
        return cls._model_index_cache.get(model_name)


class ScanManager:
    """Manage security scanning operations and their results."""
    def __init__(self):
        self.logger = create_logger_for_component('scan_manager')
        self.scans: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.logger.info("Scan manager initialized")

    def create_scan(self, model: str, app_num: int, options: dict) -> str:
        """Create a new scan job for a model/app combination."""
        scan_id = f"{model}-{app_num}-{int(time.time())}"
        with self._lock:
            self.scans[scan_id] = {
                "status": ScanStatus.STARTING.value,
                "progress": 0,
                "scanner": None,
                "start_time": datetime.now().isoformat(),
                "end_time": None,
                "options": options,
                "model": model,
                "app_num": app_num,
                "results": None,
            }
        self.logger.info(f"Created new scan '{scan_id}' for {model}/app{app_num}")
        return scan_id

    def get_scan_details(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Get details about a specific scan."""
        with self._lock:
            scan_data = self.scans.get(scan_id)
            if scan_data:
                return {k: v for k, v in scan_data.items()}
            return None

    def get_latest_scan_for_app(self, model: str, app_num: int) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Get the most recent scan for a specific model/app combination."""
        with self._lock:
            matching_scans = [
                (sid, scan) for sid, scan in self.scans.items()
                if sid.startswith(f"{model}-{app_num}-")
            ]
            if not matching_scans:
                self.logger.debug(f"No scans found for {model}/app{app_num}")
                return None
                
            try:
                # Find the scan with the latest timestamp
                latest_scan_id, latest_scan_data = max(
                    matching_scans,
                    key=lambda item: int(item[0].split('-')[-1])
                )
                self.logger.debug(f"Retrieved latest scan for {model}/app{app_num}: ID={latest_scan_id}")
                return latest_scan_id, {k: v for k, v in latest_scan_data.items()}
            except (ValueError, IndexError) as e:
                self.logger.error(f"Error parsing scan IDs for {model}/app{app_num}: {e}")
                return None

    def update_scan(self, scan_id: str, **kwargs: Any) -> bool:
        """Update scan information for a specific scan ID."""
        with self._lock:
            if scan_id in self.scans:
                # Automatically set end_time for terminal statuses if not provided
                if 'status' in kwargs and kwargs['status'] in (
                    ScanStatus.COMPLETE.value, ScanStatus.FAILED.value,
                    ScanStatus.STOPPED.value, ScanStatus.ERROR.value
                ):
                    kwargs.setdefault('end_time', datetime.now().isoformat())
                    
                self.scans[scan_id].update(kwargs)
                
                # Log appropriately based on what was updated
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
        """Remove old completed scans based on maximum age."""
        cleanup_count = 0
        current_time = datetime.now()
        terminal_statuses = {
            ScanStatus.COMPLETE.value, ScanStatus.FAILED.value,
            ScanStatus.STOPPED.value, ScanStatus.ERROR.value
        }
        
        with self._lock:
            scan_ids_to_remove = []
            
            # Find scans to remove
            for scan_id, scan in self.scans.items():
                if scan.get("status") in terminal_statuses:
                    try:
                        # Determine scan completion time
                        completion_time_str = scan.get("end_time") or scan.get("start_time")
                        if completion_time_str:
                            completion_time = datetime.fromisoformat(completion_time_str)
                        else:
                            # Fall back to timestamp from scan ID
                            scan_timestamp_unix = int(scan_id.split("-")[-1])
                            completion_time = datetime.fromtimestamp(scan_timestamp_unix)
                            
                        # Check if scan is old enough to be cleaned up
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
                        
            # Remove the identified scans
            for scan_id in scan_ids_to_remove:
                del self.scans[scan_id]
                cleanup_count += 1
                
        # Log the results
        if cleanup_count > 0:
            self.logger.info(f"Cleaned up {cleanup_count} old scans (older than {max_age}).")
        else:
            self.logger.debug("No old scans found matching cleanup criteria.")
            
        return cleanup_count


def call_ai_service(model: str, prompt: str) -> str:
    """Call an AI service with a prompt and return the response."""
    ai_logger = create_logger_for_component('ai_service')
    ai_logger.info(f"Calling AI service with model: {model}, prompt length: {len(prompt)} chars")
    
    # This is a placeholder implementation
    time.sleep(0.5)
    return f"AI analysis result for model '{model}' based on provided prompt."


class DatabaseManager:
    """Manage database operations with SQLite."""
    def __init__(self, db_path: str = Config.DB_PATH):
        self.logger = create_logger_for_component('database')
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()
        self._tables_created = False
        self.logger.info(f"DatabaseManager initialized for path: {self.db_path}")

    def _connect(self) -> None:
        """Establish database connection if not already connected."""
        if self.conn is None:
            try:
                self.logger.debug(f"Connecting to database: {self.db_path}")
                
                # Ensure directory exists
                db_dir = os.path.dirname(self.db_path)
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir)
                    self.logger.info(f"Created directory for database: {db_dir}")
                    
                # Connect to the database
                self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
                self.conn.row_factory = sqlite3.Row
                
                # Create tables only if not already done
                if not self._tables_created:
                    self._create_tables()
                    self._tables_created = True
            except sqlite3.Error as e:
                self.logger.exception(f"Database connection or table creation failed: {e}")
                self.conn = None
                raise

    def close(self) -> None:
        """Close the database connection if open."""
        if self.conn is not None:
            try:
                self.logger.debug("Closing database connection.")
                self.conn.close()
            except sqlite3.Error as e:
                self.logger.exception(f"Error closing database connection: {e}")
            finally:
                self.conn = None

    def __enter__(self) -> 'DatabaseManager':
        """Context manager entry point to manage database connection."""
        self._connect()
        if self.conn is None:
            raise sqlite3.OperationalError(f"Failed to establish database connection to {self.db_path}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit point to ensure connection is closed."""
        self.close()

    def _create_tables(self) -> None:
        """Create necessary database tables if they don't exist."""
        if not self.conn:
            self.logger.error("Cannot create tables, database connection is not established.")
            return
            
        try:
            self.logger.debug("Ensuring database tables exist...")
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
            self.conn.commit()
        except sqlite3.Error as e:
            self.logger.exception(f"Failed to create database tables: {e}")
            raise

    def store_security_scan(
        self, scan_type: str, model: str, app_num: int, issues: Union[List, Dict]
    ) -> Optional[int]:
        """Store security scan results in the database."""
        # Ensure connection exists
        if not self.conn:
            self._connect()
            if not self.conn:
                self.logger.error("Cannot store security scan, database not connected.")
                return None
                
        with self._lock:
            try:
                # Convert issues to JSON
                issues_json = json.dumps(issues)
                num_issues = len(issues) if isinstance(issues, list) else 1 if issues else 0
                
                self.logger.info(
                    f"Storing {scan_type} scan results for {model}/app{app_num} with {num_issues} issues"
                )
                
                # Insert the scan data
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
                self.conn.rollback()
                return None
            except TypeError as e:
                self.logger.exception(f"Failed to serialize issues to JSON for {model}/app{app_num}: {e}")
                return None

    def get_security_scans(
        self, model: Optional[str] = None, app_num: Optional[int] = None, limit: int = Config.DEFAULT_SCAN_LIMIT
    ) -> List[sqlite3.Row]:
        """Retrieve security scan results from the database."""
        # Ensure connection exists
        if not self.conn:
            self._connect()
            if not self.conn:
                self.logger.error("Cannot retrieve security scans, database not connected.")
                return []
                
        with self._lock:
            try:
                cursor = self.conn.cursor()
                
                # Build query with potential filters
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
                results = cursor.fetchall()
                
                self.logger.info(f"Retrieved {len(results)} security scans matching criteria.")
                return results
            except sqlite3.Error as e:
                self.logger.exception(f"Failed to retrieve security scans: {e}")
                return []

    def store_performance_test(
        self, model: str, port: int, num_users: int, duration: int, results: Dict[str, Any]
    ) -> Optional[int]:
        """Store performance test results in the database."""
        # Ensure connection exists
        if not self.conn:
            self._connect()
            if not self.conn:
                self.logger.error("Cannot store performance test, database not connected.")
                return None
                
        with self._lock:
            try:
                # Convert results to JSON
                results_json = json.dumps(results)
                
                # Insert the test data
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
        """Retrieve performance test results from the database."""
        # Ensure connection exists
        if not self.conn:
            self._connect()
            if not self.conn:
                self.logger.error("Cannot retrieve performance tests, database not connected.")
                return []
                
        with self._lock:
            try:
                cursor = self.conn.cursor()
                
                # Build query with potential filter
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


def initialize_application() -> Dict[str, Any]:
    """Initialize all application components and return them."""
    logger = create_logger_for_component('app_init')
    logger.info("Initializing application components...")
    
    # Create and initialize components
    docker_manager = DockerManager()
    cleanup_scheduler = CleanupScheduler(docker_manager)
    cleanup_scheduler.start()
    
    health_ok = SystemHealthMonitor.check_health(docker_manager.client)
    if not health_ok:
        logger.warning("Initial health check failed, but continuing startup")
        
    scan_manager = ScanManager()
    
    # Initialize database
    try:
        with DatabaseManager() as db:
            # Tables will be created automatically during connection
            pass
    except Exception as db_error:
        logger.error(f"Database initialization failed: {db_error}")
    
    return {
        "docker_manager": docker_manager,
        "cleanup_scheduler": cleanup_scheduler,
        "scan_manager": scan_manager
    }


def create_scanner(base_path: Path):
    """Import and create ZAP scanner with proper error handling."""
    logger = create_logger_for_component('zap_init')
    try:
        from zap_scanner import create_scanner as zap_create_scanner
        logger.info(f"Creating ZAP scanner with base path: {base_path}")
        return zap_create_scanner(base_path)
    except ImportError as e:
        logger.error(f"Failed to import ZAP scanner module: {e}")
        return None
    except Exception as e:
        logger.exception(f"Error creating ZAP scanner: {e}")
        return None