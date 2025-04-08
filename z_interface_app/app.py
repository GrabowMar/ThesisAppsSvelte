"""
Refactored Flask-based AI Model Management System

This version enhances jQuery compatibility, improves API responses,
centralizes error handling, and optimizes route organization with proper logging.
"""

# =============================================================================
# Standard Library Imports
# =============================================================================
import asyncio
import json
import os
import random
import sqlite3
import subprocess
import tempfile
import threading
import time
import uuid
import functools
from collections import namedtuple
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Union

# =============================================================================
# Third-Party Imports
# =============================================================================
import docker
import gevent
import pandas as pd
import matplotlib.pyplot as plt
import requests
from docker.errors import NotFound
from flask import (
    Blueprint,
    Flask,
    Response,
    current_app,
    flash,
    g,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from locust import HttpUser, User, task, constant, events, between
from locust.env import Environment
from locust.stats import stats_printer, StatsEntry
from locust.runners import Runner, LocalRunner, MasterRunner, WorkerRunner
from werkzeug.exceptions import BadRequest, HTTPException, NotFound as WerkzeugNotFound, InternalServerError
from werkzeug.middleware.proxy_fix import ProxyFix

# =============================================================================
# Custom Module Imports
# =============================================================================
from backend_security_analysis import BackendSecurityAnalyzer
from batch_analysis import init_batch_analysis, batch_analysis_bp
from frontend_security_analysis import FrontendSecurityAnalyzer
from gpt4all_analysis import GPT4AllAnalyzer
from path_utils import PathUtils
from performance_analysis import LocustPerformanceTester, PerformanceResult, EndpointStats, ErrorStats
from zap_scanner import ZAPScanner, create_scanner
from logging_service import initialize_logging, create_logger_for_component

# Create the main application logger
logger = create_logger_for_component('app')

# =============================================================================
# Enhanced Configuration & Domain Models
# =============================================================================
@dataclass
class AppConfig:
    """Application configuration with environment variable fallbacks."""
    DEBUG: bool = True
    SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "your-secret-key-here")
    BASE_DIR: Path = Path(__file__).parent
    DOCKER_TIMEOUT: int = int(os.getenv("DOCKER_TIMEOUT", "10"))
    CACHE_DURATION: int = int(os.getenv("CACHE_DURATION", "5"))
    HOST: str = "0.0.0.0" if os.getenv("FLASK_ENV") == "production" else "127.0.0.1"
    PORT: int = int(os.getenv("PORT", "5000"))
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # CORS settings for API endpoints
    CORS_ENABLED: bool = os.getenv("CORS_ENABLED", "false").lower() == "true"
    CORS_ORIGINS: List[str] = field(default_factory=lambda: ["http://localhost:5000"])
    # jQuery Ajax specific settings
    JSONP_ENABLED: bool = os.getenv("JSONP_ENABLED", "false").lower() == "true"
    AJAX_TIMEOUT: int = int(os.getenv("AJAX_TIMEOUT", "30"))

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create a configuration instance from environment variables."""
        return cls()


@dataclass
class AIModel:
    """Represents an AI model with display properties"""
    name: str
    color: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class DockerStatus:
    """Represents the status of a Docker container."""
    exists: bool = False
    running: bool = False
    health: str = "unknown"
    status: str = "unknown"
    details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert status to dictionary for JSON serialization."""
        return asdict(self)
    
    
@dataclass
class APIResponse:
    """Standard API response format for jQuery AJAX compatibility."""
    success: bool = True
    message: Optional[str] = None
    data: Any = None
    error: Optional[str] = None
    code: int = 200
    
    def to_response(self) -> Tuple[Response, int]:
        """Convert to Flask response with appropriate status code."""
        response_data = {
            "success": self.success,
            "message": self.message,
        }
        
        if self.data is not None:
            response_data["data"] = self.data
            
        if self.error is not None:
            response_data["error"] = self.error
            
        return jsonify(response_data), self.code


# Supported AI models with their display colors.
AI_MODELS: List[AIModel] = [
    AIModel("Llama", "#f97316"),
    AIModel("Mistral", "#9333ea"),
    AIModel("DeepSeek", "#ff5555"),
    AIModel("GPT4o", "#10a37f"),
    AIModel("Claude", "#7b2bf9"),
    AIModel("Gemini", "#1a73e8"),
    AIModel("Grok", "#ff4d4f"),
    AIModel("R1", "#fa541c"),
    AIModel("O3", "#0ca57f")
]

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
        self._cache: Dict[str, Tuple[float, DockerStatus]] = {}
        self._cache_duration = AppConfig.from_env().CACHE_DURATION
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
                timeout=AppConfig.from_env().DOCKER_TIMEOUT,
            )
        except Exception as e:
            self.logger.exception(f"Docker client creation failed: {e}")
            return None

    def get_container_status(self, container_name: str) -> DockerStatus:
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

    def _fetch_container_status(self, container_name: str) -> DockerStatus:
        """
        Fetch the current status of a container from Docker.
        
        Args:
            container_name: Name of the container
            
        Returns:
            DockerStatus object with container status details
        """
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
# Utility Functions & Decorators
# =============================================================================
def ajax_compatible(f):
    """
    Decorator to make endpoints compatible with jQuery AJAX.
    Ensures proper error handling and response formatting.
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        function_logger = create_logger_for_component('ajax')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        try:
            result = f(*args, **kwargs)
            
            # If already a response, return it
            if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], (dict, Response)):
                return result
                
            # If result is already an APIResponse, convert it
            if isinstance(result, APIResponse):
                return result.to_response()
                
            # For AJAX calls, ensure we return JSON
            if is_ajax:
                if isinstance(result, dict):
                    return jsonify(result)
                elif not isinstance(result, str) and hasattr(result, '__dict__'):
                    return jsonify(asdict(result))
                else:
                    return jsonify({"success": True, "data": result})
                    
            # Otherwise return original result
            return result
                
        except Exception as e:
            function_logger.exception(f"Error in {f.__name__}: {e}")
            
            if is_ajax:
                error_response = APIResponse(
                    success=False,
                    error=str(e),
                    code=500 if not isinstance(e, HTTPException) else e.code
                )
                return error_response.to_response()
                
            # For regular requests, render error template
            return render_template("500.html", error=str(e)), 500
    return wrapped


def get_model_index(model_name: str) -> int:
    """
    Get the index of a model in the AI_MODELS list.
    
    Args:
        model_name: Name of the model
        
    Returns:
        Index in the AI_MODELS list or 0 if not found
    """
    return next((i for i, m in enumerate(AI_MODELS) if m.name == model_name), 0)


def get_container_names(model: str, app_num: int) -> Tuple[str, str]:
    """
    Get the container names for a given model and app number.
    
    Args:
        model: Model name
        app_num: Application number
        
    Returns:
        Tuple of (backend_container_name, frontend_container_name)
    """
    idx = get_model_index(model)
    ports = PortManager.get_app_ports(idx, app_num)
    base = model.lower()
    return (f"{base}_backend_{ports['backend']}", f"{base}_frontend_{ports['frontend']}")


def get_app_info(model_name: str, app_num: int) -> Dict[str, Any]:
    """
    Get detailed information for a specific app.
    
    Args:
        model_name: Name of the AI model
        app_num: Application number
        
    Returns:
        Dictionary with app details
    """
    idx = get_model_index(model_name)
    model_color = next((m.color for m in AI_MODELS if m.name == model_name), "#666666")
    ports = PortManager.get_app_ports(idx, app_num)
    return {
        "name": f"{model_name} App {app_num}",
        "model": model_name,
        "color": model_color,
        "backend_port": ports["backend"],
        "frontend_port": ports["frontend"],
        "app_num": app_num,
        "backend_url": f"http://localhost:{ports['backend']}",
        "frontend_url": f"http://localhost:{ports['frontend']}",
    }


def get_apps_for_model(model_name: str) -> List[Dict[str, Any]]:
    """
    Get all apps for a specific model.
    
    Args:
        model_name: Name of the model
        
    Returns:
        List of app information dictionaries
    """
    base_path = Path(model_name)
    util_logger = create_logger_for_component('utils')
    
    if not base_path.exists():
        util_logger.debug(f"Model directory does not exist: {base_path}")
        return []
    
    apps = []
    try:
        app_dirs = sorted(
            (d for d in base_path.iterdir() if d.is_dir() and d.name.startswith("app")),
            key=lambda x: int(x.name.replace("app", ""))
        )
        
        for app_dir in app_dirs:
            try:
                app_num = int(app_dir.name.replace("app", ""))
                apps.append(get_app_info(model_name, app_num))
            except ValueError as e:
                util_logger.error(f"Error processing {app_dir}: {e}")
    except Exception as e:
        util_logger.exception(f"Error scanning apps for model {model_name}: {e}")
    
    util_logger.debug(f"Found {len(apps)} apps for model {model_name}")
    return apps


def get_all_apps() -> List[Dict[str, Any]]:
    """
    Get all apps for all models.
    
    Returns:
        List of app information dictionaries for all models
    """
    all_apps = []
    for model in AI_MODELS:
        model_apps = get_apps_for_model(model.name)
        all_apps.extend(model_apps)
    
    logger.debug(f"Retrieved {len(all_apps)} apps across all models")
    return all_apps


def run_docker_compose(
    command: List[str],
    model: str,
    app_num: int,
    timeout: int = 60,
    check: bool = True,
) -> Tuple[bool, str]:
    """
    Run a docker-compose command for a specific app.
    
    Args:
        command: The docker-compose command to run
        model: The model name
        app_num: The application number
        timeout: Command timeout in seconds
        check: Whether to check the command's return code
        
    Returns:
        Tuple of (success, output)
    """
    compose_logger = create_logger_for_component('docker_compose')
    app_dir = Path(f"{model}/app{app_num}")
    
    if not app_dir.exists():
        compose_logger.error(f"Directory not found: {app_dir}")
        return False, f"Directory not found: {app_dir}"
    
    # Check for compose file existence
    compose_file = app_dir / "docker-compose.yml"
    compose_yaml = app_dir / "docker-compose.yaml"
    if not compose_file.exists() and not compose_yaml.exists():
        compose_logger.error(f"No docker-compose.yml/yaml file found in {app_dir}")
        return False, f"No docker-compose file found in {app_dir}"
    
    # Build the custom project name
    project_name = f"{model}_app{app_num}".lower()

    
    # Include the -p option to rename the compose stack
    cmd = ["docker-compose", "-p", project_name] + command
    compose_logger.info(f"Running command: {' '.join(cmd)} in {app_dir} with timeout {timeout}s")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(app_dir),  # Ensure string path for compatibility
            check=check,
            capture_output=True,
            text=True,
            encoding='utf-8',  # Explicitly set UTF-8 encoding
            errors='replace',   # Replace invalid characters instead of failing
            timeout=timeout,
        )
        output = result.stdout or result.stderr
        success = result.returncode == 0
        
        if success:
            compose_logger.info(f"Command succeeded: {' '.join(cmd)}")
        else:
            compose_logger.error(
                f"Command failed with code {result.returncode}: {' '.join(cmd)}\n"
                f"Error output: {output[:500]}"
            )
        
        return success, output
    except subprocess.TimeoutExpired:
        compose_logger.error(f"Command timed out after {timeout}s: {' '.join(cmd)}")
        return False, f"Command timed out after {timeout}s"
    except Exception as e:
        compose_logger.exception(f"Error running {' '.join(cmd)}: {str(e)}")
        return False, str(e)


def handle_docker_action(action: str, model: str, app_num: int) -> Tuple[bool, str]:
    """
    Handle Docker actions (start, stop, reload, rebuild, build).
    
    Args:
        action: The action to perform
        model: The model name
        app_num: The application number
        
    Returns:
        Tuple of (success, message)
    """
    docker_logger = create_logger_for_component('docker')
    commands = {
        "start": [("up", "-d", 120)],
        "stop": [("down", None, 30)],
        "reload": [("restart", None, 90)],
        "rebuild": [("down", None, 30), ("build", None, 600), ("up", "-d", 120)],  # Increased build timeout
        "build": [("build", None, 600)],  # Increased build timeout
    }
    
    if action not in commands:
        docker_logger.error(f"Invalid action: {action}")
        return False, f"Invalid action: {action}"
    
    docker_logger.info(f"Starting {action} for {model}/app{app_num}")
    
    # Execute each command step
    for i, (base_cmd, extra_arg, timeout) in enumerate(commands[action]):
        cmd = [base_cmd] + ([extra_arg] if extra_arg else [])
        step_desc = f"Step {i+1}/{len(commands[action])}: {' '.join(cmd)}"
        docker_logger.info(f"{step_desc} for {model}/app{app_num}")
        
        success, msg = run_docker_compose(cmd, model, app_num, timeout=timeout)
        
        if not success:
            error_msg = f"{action.capitalize()} failed during {base_cmd}: {msg}"
            docker_logger.error(f"Docker {action} failed: {error_msg}")
            return False, error_msg
    
    docker_logger.info(f"Successfully completed {action} for {model}/app{app_num}")
    return True, f"Successfully completed {action}"


def verify_container_health(
    docker_manager: DockerManager, model: str, app_num: int, max_retries: int = 10, retry_delay: int = 3
) -> Tuple[bool, str]:
    """
    Verify that containers for an app are healthy.
    
    Args:
        docker_manager: Docker manager instance
        model: Model name
        app_num: App number
        max_retries: Maximum number of retries
        retry_delay: Delay between retries in seconds
        
    Returns:
        Tuple of (is_healthy, message)
    """
    health_logger = create_logger_for_component('health')
    backend_name, frontend_name = get_container_names(model, app_num)
    
    health_logger.info(f"Verifying health for {model}/app{app_num} ({backend_name}, {frontend_name})")
    
    for attempt in range(1, max_retries + 1):
        backend = docker_manager.get_container_status(backend_name)
        frontend = docker_manager.get_container_status(frontend_name)
        
        backend_status = f"{backend.status} ({backend.health})"
        frontend_status = f"{frontend.status} ({frontend.health})"
        health_logger.debug(
            f"Health check attempt {attempt}/{max_retries}: "
            f"Backend: {backend_status}, Frontend: {frontend_status}"
        )
        
        if backend.health == "healthy" and frontend.health == "healthy":
            health_logger.info(f"All containers healthy for {model}/app{app_num}")
            return True, "All containers healthy"
        
        time.sleep(retry_delay)
    
    health_logger.warning(
        f"Containers failed to reach healthy state for {model}/app{app_num} "
        f"after {max_retries} attempts"
    )
    return False, "Containers failed to reach healthy state"


def process_security_analysis(
    template: str,
    analyzer,
    analysis_method,
    model: str,
    app_num: int,
    full_scan: bool,
    no_issue_message: str,
):
    """
    Common logic for running security analysis and returning template.
    
    Args:
        template: Template name to render
        analyzer: Security analyzer instance
        analysis_method: Method to call for analysis
        model: Model name
        app_num: App number
        full_scan: Whether to run a full scan
        no_issue_message: Message to show when no issues found
        
    Returns:
        Rendered template with analysis results
    """
    sec_logger = create_logger_for_component('security')
    try:
        sec_logger.info(f"Running {template.split('.')[0]} analysis for {model}/app{app_num} (full_scan={full_scan})")
        
        issues, tool_status, tool_output_details = analysis_method(
            model, app_num, use_all_tools=full_scan
        )
        
        summary = analyzer.get_analysis_summary(issues) if issues else analyzer.get_analysis_summary([])
        sec_logger.info(
            f"Security analysis complete for {model}/app{app_num}: "
            f"Found {len(issues) if issues else 0} issues"
        )
        
        return render_template(
            template,
            model=model,
            app_num=app_num,
            issues=issues or [],
            summary=summary,
            error=None,
            message=no_issue_message if not issues else None,
            full_scan=full_scan,
            tool_status=tool_status,
            tool_output_details=tool_output_details,
        )
    except ValueError as e:
        sec_logger.warning(f"No files to analyze for {model}/app{app_num}: {e}")
        return render_template(
            template,
            model=model,
            app_num=app_num,
            issues=None,
            error=str(e),
            full_scan=full_scan,
            tool_status={},
            tool_output_details={},
        )
    except Exception as e:
        sec_logger.exception(f"Security analysis failed for {model}/app{app_num}: {e}")
        return render_template(
            template,
            model=model,
            app_num=app_num,
            issues=None,
            error=f"Security analysis failed: {e}",
            full_scan=full_scan,
            tool_status={},
            tool_output_details={},
        )


def get_app_container_statuses(model: str, app_num: int, docker_manager: DockerManager) -> Dict[str, Any]:
    """
    Get container statuses for an app's backend and frontend.
    
    Args:
        model: Model name
        app_num: App number
        docker_manager: Docker manager instance
        
    Returns:
        Dictionary with backend and frontend status
    """
    b_name, f_name = get_container_names(model, app_num)
    return {
        "backend": docker_manager.get_container_status(b_name).to_dict(),
        "frontend": docker_manager.get_container_status(f_name).to_dict(),
    }


def get_app_directory(app: Flask, model: str, app_num: int) -> Path:
    """
    Get the directory for a specific app.
    
    Args:
        app: Flask app instance
        model: Model name
        app_num: App number
        
    Returns:
        Path to the app directory
    """
    return app.config["BASE_DIR"] / f"{model}/app{app_num}"


def stop_zap_scanners(scans: Dict[str, Any]) -> None:
    """
    Stop all active ZAP scanners.
    
    Args:
        scans: Dictionary of scan_key -> scanner mappings
    """
    zap_logger = create_logger_for_component('zap_scanner')
    stopped_count = 0
    
    for scan_key, scanner in scans.items():
        if hasattr(scanner, "stop_scan") and callable(scanner.stop_scan):
            try:
                model, app_num = scan_key.split("-")[:2]
                zap_logger.info(f"Stopping ZAP scan for {model}/app{app_num}")
                scanner.stop_scan(model=model, app_num=int(app_num))
                stopped_count += 1
            except Exception as e:
                zap_logger.exception(f"Error stopping scan for {scan_key}: {e}")
        else:
            zap_logger.warning(
                f"Invalid scanner for key {scan_key}: expected a ZAPScanner instance but got {type(scanner)}"
            )
    
    if stopped_count > 0:
        zap_logger.info(f"Stopped {stopped_count} ZAP scans")

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


def get_scan_manager():
    """
    Retrieve or initialize the scan manager.
    
    Returns:
        ScanManager instance from current app or a new one if not present
    """
    if not hasattr(current_app, 'scan_manager'):
        logger.debug("Creating new ScanManager instance")
        current_app.scan_manager = ScanManager()
    return current_app.scan_manager

# =============================================================================
# Enhanced JSON Encoder
# =============================================================================
class CustomJSONEncoder(json.JSONEncoder):
    """Extended JSON encoder that can handle dataclasses and objects with __dict__."""
    
    def default(self, obj):
        """
        Custom encoding for special types.
        
        Args:
            obj: Object to encode
            
        Returns:
            JSON serializable representation
        """
        # Handle dataclasses
        if hasattr(obj, "__dataclass_fields__"):
            return asdict(obj)
        # Handle objects with __dict__
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        # Handle datetime objects
        if isinstance(obj, datetime):
            return obj.isoformat()
        # Handle Path objects
        if isinstance(obj, Path):
            return str(obj)
        # Default behavior
        return super().default(obj)

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
# Blueprints for Routes
# =============================================================================
main_bp = Blueprint("main", __name__)
api_bp = Blueprint("api", __name__)
analysis_bp = Blueprint("analysis", __name__)
performance_bp = Blueprint("performance", __name__, url_prefix="/performance")
gpt4all_bp = Blueprint("gpt4all", __name__)
zap_bp = Blueprint("zap", __name__)

# ----- Main Routes -----
@main_bp.route("/")
@ajax_compatible
def index():
    """
    Main dashboard index page showing all apps and their statuses.
    
    Returns:
        Rendered index template with apps and models
    """
    route_logger = create_logger_for_component('routes')
    route_logger.info("Rendering main dashboard")
    
    docker_manager: DockerManager = current_app.config["docker_manager"]
    apps = get_all_apps()
    
    # Log the number of apps found
    route_logger.debug(f"Found {len(apps)} apps to display")
    
    for app_info in apps:
        statuses = get_app_container_statuses(app_info["model"], app_info["app_num"], docker_manager)
        app_info["backend_status"] = statuses["backend"]
        app_info["frontend_status"] = statuses["frontend"]
    
    # Add autorefresh_enabled based on config
    autorefresh_enabled = request.cookies.get('autorefresh', 'false') == 'true'
    route_logger.debug(f"Autorefresh setting: {autorefresh_enabled}")
    
    return render_template("index.html", 
                         apps=apps, 
                         models=AI_MODELS, 
                         autorefresh_enabled=autorefresh_enabled)

@main_bp.route("/docker-logs/<string:model>/<int:app_num>")
@ajax_compatible
def view_docker_logs(model: str, app_num: int):
    """
    View Docker compose logs for debugging.
    
    Args:
        model: Model name
        app_num: App number
        
    Returns:
        Rendered template with Docker logs
    """
    route_logger = create_logger_for_component('routes')
    route_logger.info(f"Fetching Docker logs for {model}/app{app_num}")
    
    app_dir = Path(f"{model}/app{app_num}")
    if not app_dir.exists():
        route_logger.warning(f"Directory not found: {app_dir}")
        flash(f"Directory not found: {app_dir}", "error")
        return redirect(url_for("main.index"))
    
    try:
        # Get docker-compose logs
        route_logger.debug(f"Running docker-compose logs for {model}/app{app_num}")
        result = subprocess.run(
            ["docker-compose", "logs", "--no-color"],
            cwd=str(app_dir),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=10
        )
        compose_logs = result.stdout or "No docker-compose logs available"
        
        # Get individual container logs
        b_name, f_name = get_container_names(model, app_num)
        docker_manager: DockerManager = current_app.config["docker_manager"]
        
        route_logger.debug(f"Fetching container logs for {b_name} and {f_name}")
        backend_logs = docker_manager.get_container_logs(b_name, tail=100)
        frontend_logs = docker_manager.get_container_logs(f_name, tail=100)
        
        return render_template(
            "docker_logs.html",
            model=model,
            app_num=app_num,
            compose_logs=compose_logs,
            backend_logs=backend_logs,
            frontend_logs=frontend_logs
        )
    except Exception as e:
        route_logger.exception(f"Error fetching logs for {model}/app{app_num}: {str(e)}")
        flash(f"Error fetching logs: {str(e)}", "error")
        return redirect(url_for("main.index"))

@main_bp.route("/status/<string:model>/<int:app_num>")
@ajax_compatible
def check_app_status(model: str, app_num: int):
    """
    Check and return container status for an app.
    
    Args:
        model: Model name
        app_num: App number
        
    Returns:
        JSON status for AJAX or redirect with flash for regular requests
    """
    route_logger = create_logger_for_component('routes')
    route_logger.debug(f"Checking status for {model}/app{app_num}")
    
    docker_manager: DockerManager = current_app.config["docker_manager"]
    status = get_app_container_statuses(model, app_num, docker_manager)
    
    # For AJAX requests, return JSON
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return status
    
    # For regular requests, redirect with flash message
    flash(f"Status checked for {model} App {app_num}", "info")
    return redirect(url_for("main.index"))

@main_bp.route("/batch/<action>/<string:model>", methods=["POST"])
@ajax_compatible
def batch_docker_action(action: str, model: str):
    """
    Perform batch operations on all apps for a specific model.
    
    Args:
        action: The action to perform (start, stop, reload, rebuild)
        model: The model name to target
    
    Returns:
        JSON response with results
    """
    route_logger = create_logger_for_component('routes')
    route_logger.info(f"Batch {action} requested for model {model}")
    
    # Get all apps for the model
    apps = get_apps_for_model(model)
    if not apps:
        route_logger.warning(f"No apps found for model {model}")
        return APIResponse(
            success=False,
            error=f"No apps found for model {model}",
            code=404
        )
    
    # Validate the action
    valid_actions = ["start", "stop", "reload", "rebuild", "health-check"]
    if action not in valid_actions:
        route_logger.warning(f"Invalid batch action requested: {action}")
        return APIResponse(
            success=False,
            error=f"Invalid action: {action}",
            code=400
        )
    
    # Process all apps
    route_logger.info(f"Processing batch {action} for {len(apps)} apps of model {model}")
    results = []
    for app in apps:
        app_num = app["app_num"]
        try:
            if action == "health-check":
                docker_manager: DockerManager = current_app.config["docker_manager"]
                healthy, message = verify_container_health(docker_manager, model, app_num)
                results.append({
                    "app_num": app_num,
                    "success": healthy,
                    "message": message
                })
            else:
                success, message = handle_docker_action(action, model, app_num)
                results.append({
                    "app_num": app_num, 
                    "success": success,
                    "message": message
                })
        except Exception as e:
            route_logger.exception(f"Error during batch {action} for {model} app {app_num}: {e}")
            results.append({
                "app_num": app_num,
                "success": False,
                "message": str(e)
            })
    
    # Summarize results
    success_count = sum(1 for r in results if r["success"])
    route_logger.info(f"Batch {action} for {model} completed: {success_count}/{len(results)} succeeded")
    
    return {
        "status": "success" if success_count == len(results) else "partial" if success_count > 0 else "error",
        "total": len(results),
        "success_count": success_count,
        "failure_count": len(results) - success_count,
        "results": results
    }

@main_bp.route("/logs/<string:model>/<int:app_num>")
@ajax_compatible
def view_logs(model: str, app_num: int):
    """
    View container logs for an app.
    
    Args:
        model: Model name
        app_num: App number
        
    Returns:
        Rendered template with logs
    """
    route_logger = create_logger_for_component('routes')
    route_logger.info(f"Viewing container logs for {model}/app{app_num}")
    
    docker_manager: DockerManager = current_app.config["docker_manager"]
    b_name, f_name = get_container_names(model, app_num)
    
    route_logger.debug(f"Fetching logs for containers: {b_name}, {f_name}")
    logs_data = {
        "backend": docker_manager.get_container_logs(b_name),
        "frontend": docker_manager.get_container_logs(f_name),
    }
    return render_template("logs.html", logs=logs_data, model=model, app_num=app_num)


@main_bp.route("/<action>/<string:model>/<int:app_num>")
@ajax_compatible
def handle_docker_action_route(action: str, model: str, app_num: int):
    """
    Handle Docker action (start, stop, reload, rebuild) for an app.
    
    Args:
        action: Action to perform
        model: Model name
        app_num: App number
        
    Returns:
        JSON response or redirect with flash message
    """
    route_logger = create_logger_for_component('routes')
    route_logger.info(f"Docker action '{action}' requested for {model}/app{app_num}")
    
    success, message = handle_docker_action(action, model, app_num)
    
    # For AJAX requests, return JSON
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return APIResponse(
            success=success,
            message=message,
            code=200 if success else 500
        )
    
    # For regular requests, redirect with flash message
    flash(f"{'Success' if success else 'Error'}: {message}", "success" if success else "error")
    return redirect(url_for("main.index"))

# ----- API Routes -----
@api_bp.route("/system-info")
@ajax_compatible
def system_info():
    """
    Get detailed system information for the dashboard.
    
    Returns:
        JSON with system metrics, health status, and resource utilization
    """
    api_logger = create_logger_for_component('api')
    api_logger.debug("System info requested")
    
    docker_manager: DockerManager = current_app.config["docker_manager"]
    
    # Get basic system metrics
    try:
        import psutil
        api_logger.debug("Getting system metrics using psutil")
        
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Get disk usage
        disk_usage = psutil.disk_usage('/')
        disk_percent = disk_usage.percent
        
        # Get system uptime
        uptime_seconds = int(time.time() - psutil.boot_time())
        
        system_health = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "memory_used": memory.used,
            "memory_total": memory.total,
            "disk_percent": disk_percent,
            "disk_used": disk_usage.used,
            "disk_total": disk_usage.total,
            "uptime_seconds": uptime_seconds,
        }
    except ImportError:
        # Fallback if psutil is not available
        api_logger.warning("psutil not available, using mock system metrics")
        system_health = {
            "cpu_percent": random.randint(10, 40),  # Mock data
            "memory_percent": random.randint(30, 70),
            "memory_used": 4 * 1024 * 1024 * 1024,  # 4GB mock
            "memory_total": 16 * 1024 * 1024 * 1024,  # 16GB mock
            "disk_percent": random.randint(30, 60),
            "disk_used": 100 * 1024 * 1024 * 1024,  # 100GB mock
            "disk_total": 500 * 1024 * 1024 * 1024,  # 500GB mock
            "uptime_seconds": 3600 * 24 * 3,  # 3 days mock
        }
    
    # Get docker status
    docker_status = {
        "healthy": SystemHealthMonitor.check_health(docker_manager.client),
        "containers": {
            "running": 0,
            "stopped": 0,
            "total": 0
        }
    }
    
    # Try to get actual container counts if docker client is available
    if docker_manager.client:
        try:
            api_logger.debug("Getting container counts from Docker")
            containers = docker_manager.client.containers.list(all=True)
            docker_status["containers"] = {
                "running": sum(1 for c in containers if c.status == "running"),
                "stopped": sum(1 for c in containers if c.status != "running"),
                "total": len(containers)
            }
        except Exception as e:
            api_logger.exception(f"Error getting container counts: {e}")
    
    # Get app overview
    apps = get_all_apps()
    app_stats = {
        "total": len(apps),
        "models": {model.name: 0 for model in AI_MODELS},
        "status": {
            "running": 0,
            "partial": 0,
            "stopped": 0
        }
    }
    
    # Count apps per model
    for app in apps:
        model_name = app["model"]
        if model_name in app_stats["models"]:
            app_stats["models"][model_name] += 1
    
    # Get app status counts (limited to 10 apps for performance)
    api_logger.debug("Sampling app statuses for dashboard (limited to 10 apps)")
    for app in apps[:10]:  # Limit to 10 apps to avoid overloading
        try:
            statuses = get_app_container_statuses(app["model"], app["app_num"], docker_manager)
            backend_running = statuses["backend"].get("running", False)
            frontend_running = statuses["frontend"].get("running", False)
            
            if backend_running and frontend_running:
                app_stats["status"]["running"] += 1
            elif backend_running or frontend_running:
                app_stats["status"]["partial"] += 1
            else:
                app_stats["status"]["stopped"] += 1
        except Exception as e:
            api_logger.exception(f"Error getting app status for {app['model']}/app{app['app_num']}: {e}")
    
    # Scale up the counts based on sampling
    if len(apps) > 10:
        scale_factor = len(apps) / 10
        app_stats["status"]["running"] = int(app_stats["status"]["running"] * scale_factor)
        app_stats["status"]["partial"] = int(app_stats["status"]["partial"] * scale_factor)
        app_stats["status"]["stopped"] = int(app_stats["status"]["stopped"] * scale_factor)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "system": system_health,
        "docker": docker_status,
        "apps": app_stats
    }

@api_bp.route("/container/<string:model>/<int:app_num>/status")
@ajax_compatible
def container_status(model: str, app_num: int):
    """
    Get container status for an app.
    
    Args:
        model: Model name
        app_num: App number
        
    Returns:
        JSON with container statuses
    """
    api_logger = create_logger_for_component('api')
    api_logger.debug(f"Container status requested for {model}/app{app_num}")
    
    docker_manager: DockerManager = current_app.config["docker_manager"]
    status = get_app_container_statuses(model, app_num, docker_manager)
    return status

@api_bp.route("/debug/docker/<string:model>/<int:app_num>")
@ajax_compatible
def debug_docker_environment(model: str, app_num: int):
    """
    Debug endpoint to inspect docker environment for an app.
    
    Args:
        model: Model name
        app_num: App number
        
    Returns:
        JSON with docker environment details
    """
    api_logger = create_logger_for_component('api')
    api_logger.info(f"Docker environment debug requested for {model}/app{app_num}")
    
    app_dir = Path(f"{model}/app{app_num}")
    
    try:
        # Check directory existence
        dir_exists = app_dir.exists()
        
        # Check docker-compose file
        compose_file = app_dir / "docker-compose.yml"
        compose_yaml = app_dir / "docker-compose.yaml"
        compose_file_exists = compose_file.exists() or compose_yaml.exists()
        compose_content = ""
        if compose_file.exists():
            compose_content = compose_file.read_text(encoding='utf-8', errors='replace')[:500] + "..."
        elif compose_yaml.exists():
            compose_content = compose_yaml.read_text(encoding='utf-8', errors='replace')[:500] + "..."
        
        # Check docker installation
        api_logger.debug("Checking Docker version")
        docker_version = subprocess.run(
            ["docker", "--version"], 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='replace'
        ).stdout.strip()
        
        # Check docker-compose installation
        try:
            api_logger.debug("Checking Docker Compose version")
            docker_compose_version = subprocess.run(
                ["docker-compose", "--version"], 
                capture_output=True, 
                text=True,
                encoding='utf-8',
                errors='replace'
            ).stdout.strip()
        except:
            docker_compose_version = "Not available or error"
        
        # Get container statuses
        b_name, f_name = get_container_names(model, app_num)
        docker_manager: DockerManager = current_app.config["docker_manager"]
        backend_status = docker_manager.get_container_status(b_name)
        frontend_status = docker_manager.get_container_status(f_name)
        
        api_logger.debug(f"Debug data collected for {model}/app{app_num}")
        
        return {
            "directory_exists": dir_exists,
            "compose_file_exists": compose_file_exists,
            "compose_file_preview": compose_content,
            "docker_version": docker_version,
            "docker_compose_version": docker_compose_version,
            "backend_container": backend_status.to_dict(),
            "frontend_container": frontend_status.to_dict(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        api_logger.exception(f"Error in debug endpoint for {model}/app{app_num}: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            code=500
        )

@api_bp.route("/health/<string:model>/<int:app_num>")
@ajax_compatible
def check_container_health(model: str, app_num: int):
    """
    Check if containers for an app are healthy.
    
    Args:
        model: Model name
        app_num: App number
        
    Returns:
        JSON with health status
    """
    api_logger = create_logger_for_component('api')
    api_logger.debug(f"Health check requested for {model}/app{app_num}")
    
    docker_manager: DockerManager = current_app.config["docker_manager"]
    healthy, message = verify_container_health(docker_manager, model, app_num)
    api_logger.debug(f"Health check result for {model}/app{app_num}: {healthy} - {message}")
    return {"healthy": healthy, "message": message}


@api_bp.route("/status")
@ajax_compatible
def system_status():
    """
    Get overall system status.
    
    Returns:
        JSON with system status overview
    """
    api_logger = create_logger_for_component('api')
    api_logger.debug("System status check requested")
    
    docker_manager: DockerManager = current_app.config["docker_manager"]
    disk_ok = SystemHealthMonitor.check_disk_space()
    docker_ok = SystemHealthMonitor.check_health(docker_manager.client)
    
    status = "healthy" if (disk_ok and docker_ok) else "warning"
    api_logger.debug(f"System status: {status} (disk: {disk_ok}, docker: {docker_ok})")
    
    return {
        "status": status,
        "details": {"disk_space": disk_ok, "docker_health": docker_ok},
        "timestamp": datetime.now().isoformat(),
    }


@api_bp.route("/model-info")
@ajax_compatible
def get_model_info():
    """
    Get information about all AI models.
    
    Returns:
        JSON list with model information
    """
    api_logger = create_logger_for_component('api')
    api_logger.debug("Model information requested")
    
    model_info = [
        {
            "name": model.name,
            "color": model.color,
            "ports": PortManager.get_port_range(idx),
            "total_apps": len(get_apps_for_model(model.name)),
        }
        for idx, model in enumerate(AI_MODELS)
    ]
    
    api_logger.debug(f"Returning information for {len(model_info)} models")
    return model_info

# ----- Client-side Error Logging Endpoint -----
@api_bp.route("/log-client-error", methods=["POST"])
@ajax_compatible
def log_client_error():
    """
    Endpoint to log client-side errors that might be causing
    undefined route requests.
    
    Returns:
        JSON status response
    """
    client_logger = create_logger_for_component('client_errors')
    
    try:
        data = request.get_json()
        if not data:
            client_logger.warning("Client error logging request with no data")
            return APIResponse(
                success=False,
                error="No error data provided",
                code=400
            )
            
        # Log the client error with detailed context
        client_logger.error(
            f"CLIENT ERROR: {data.get('message')} | "
            f"URL: {data.get('url')} | "
            f"File: {data.get('filename')}:{data.get('lineno')}:{data.get('colno')} | "
            f"User-Agent: {data.get('userAgent')}"
        )
        
        # Log stack trace at debug level
        if 'stack' in data:
            client_logger.debug(f"Error stack trace: {data.get('stack')}")
            
        return {"status": "success"}
    except Exception as e:
        client_logger.exception(f"Error in client error logger: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            code=500
        )

# ----- ZAP Routes -----
@zap_bp.route("/<string:model>/<int:app_num>")
@ajax_compatible
def zap_scan(model: str, app_num: int):
    """
    ZAP scanner page for a specific app.
    
    Args:
        model: Model name
        app_num: App number
        
    Returns:
        Rendered template with scan results
    """
    zap_logger = create_logger_for_component('zap')
    zap_logger.info(f"ZAP scan page requested for {model}/app{app_num}")
    
    base_dir: Path = current_app.config["BASE_DIR"]
    results_file = base_dir / f"{model}/app{app_num}/.zap_results.json"
    alerts = []
    error_msg = None
    
    if results_file.exists():
        try:
            zap_logger.debug(f"Loading previous scan results from {results_file}")
            with open(results_file, encoding='utf-8', errors='replace') as f:
                data = json.load(f)
                alerts = data.get("alerts", [])
                zap_logger.info(f"Loaded {len(alerts)} alerts from previous scan for {model}/app{app_num}")
                
                # Count alerts with affected code for statistics
                alerts_with_code = sum(1 for alert in alerts if alert.get('affected_code') and 
                                       alert.get('affected_code', {}).get('snippet'))
                zap_logger.info(f"Found {alerts_with_code} alerts with affected code")
        except Exception as e:
            error_msg = f"Failed to load previous results: {e}"
            zap_logger.exception(f"Error loading ZAP results for {model}/app{app_num}: {e}")
    else:
        zap_logger.debug(f"No previous scan results file found at {results_file}")
    
    return render_template("zap_scan.html", model=model, app_num=app_num, alerts=alerts, error=error_msg)


@zap_bp.route("/scan/<string:model>/<int:app_num>", methods=["POST"])
@ajax_compatible
def start_zap_scan(model: str, app_num: int):
    """
    Start a comprehensive ZAP scan for a specific app using the optimized scanner.
    
    Args:
        model: Model name
        app_num: App number
        
    Returns:
        JSON response with scan status
    """
    zap_logger = create_logger_for_component('zap')
    zap_logger.info(f"Starting ZAP scan for {model}/app{app_num}")
    
    base_dir: Path = current_app.config["BASE_DIR"]
    scan_manager = get_scan_manager()
    
    # Check for existing scan
    existing_scan = scan_manager.get_scan(model, app_num)
    if existing_scan and existing_scan["status"] not in ("Complete", "Failed", "Stopped"):
        zap_logger.warning(f"ZAP scan already in progress for {model}/app{app_num}: {existing_scan['status']}")
        return APIResponse(
            success=False,
            error="A scan is already running",
            code=409
        )
    
    scan_id = scan_manager.create_scan(model, app_num, {})
    zap_logger.info(f"Created new scan with ID: {scan_id} for {model}/app{app_num}")
    
    def run_scan():
        scan_thread_logger = create_logger_for_component('zap')
        try:
            # Create scanner with its streamlined configuration
            scan_thread_logger.info(f"Initializing ZAP scanner for {model}/app{app_num}")
            scanner = create_scanner(base_dir)
            
            # Set source code root directory for code analysis
            app_path = base_dir / f"{model}/app{app_num}"
            if app_path.exists() and app_path.is_dir():
                scan_thread_logger.info(f"Setting source code root directory to {app_path}")
                scanner.set_source_code_root(str(app_path))
            
            scan_manager.update_scan(
                scan_id, 
                scanner=scanner, 
                status="Starting", 
                progress=0,
                spider_progress=0,
                passive_progress=0,
                active_progress=0,
                start_time=datetime.now().isoformat()
            )
            
            # Start the scan with simplified interface
            scan_thread_logger.info(f"Starting comprehensive scan for {model}/app{app_num}")
            success = scanner.start_scan(model, app_num)
            
            if not success:
                scan_thread_logger.error(f"Scan failed to complete successfully for {model}/app{app_num}")
                scan_manager.update_scan(scan_id, status="Failed", progress=0)
            else:
                scan_thread_logger.info(f"Scan completed successfully for {model}/app{app_num}")
                
                # Get information about code analysis
                results_file = base_dir / f"{model}/app{app_num}/.zap_results.json"
                vulnerabilities_with_code = 0
                if results_file.exists():
                    try:
                        with open(results_file, encoding='utf-8') as f:
                            data = json.load(f)
                            summary = data.get("summary", {})
                            vulnerabilities_with_code = summary.get("vulnerabilities_with_code", 0)
                    except Exception as e:
                        scan_thread_logger.error(f"Error reading code analysis stats: {str(e)}")
                
                scan_manager.update_scan(
                    scan_id, 
                    status="Complete", 
                    progress=100, 
                    spider_progress=100,
                    passive_progress=100,
                    active_progress=100,
                    end_time=datetime.now().isoformat(),
                    vulnerabilities_with_code=vulnerabilities_with_code
                )
        except Exception as e:
            scan_thread_logger.exception(f"Scan error for {model}/app{app_num}: {str(e)}")
            scan_manager.update_scan(scan_id, status=f"Failed: {str(e)}", progress=0)
        finally:
            # Ensure ZAP resources are properly cleaned up
            try:
                if scanner:
                    scan_thread_logger.info(f"Cleaning up ZAP resources for {model}/app{app_num}")
                    scanner._cleanup_existing_zap()
                    scan_thread_logger.info(f"ZAP resources cleaned up for {model}/app{app_num}")
            except Exception as cleanup_error:
                scan_thread_logger.exception(f"Error cleaning up ZAP resources for {model}/app{app_num}: {str(cleanup_error)}")
            
            scan_manager.cleanup_old_scans()
    
    # Start scan in background thread
    thread = threading.Thread(target=run_scan, daemon=True)
    thread.name = f"zap-scan-{model}-{app_num}"
    thread.start()
    zap_logger.info(f"Scan thread started for {model}/app{app_num}")
    
    return {"status": "started", "scan_id": scan_id}


@zap_bp.route("/scan/<string:model>/<int:app_num>/status")
@ajax_compatible
def zap_scan_status(model: str, app_num: int):
    """
    Get the status of a ZAP scan with detailed progress information.
    Handles cases where results file may not exist or is empty.
    
    Args:
        model: Model name
        app_num: App number
        
    Returns:
        JSON with scan status and detailed progress metrics
    """
    zap_logger = create_logger_for_component('zap')
    zap_logger.debug(f"Scan status requested for {model}/app{app_num}")
    
    scan_manager = get_scan_manager()
    scan = scan_manager.get_scan(model, app_num)
    
    if not scan:
        zap_logger.debug(f"No scan found for {model}/app{app_num}")
        return {
            "status": "Not Started", 
            "progress": 0,
            "spider_progress": 0,
            "passive_progress": 0,
            "active_progress": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "info_count": 0,
            "vulnerabilities_with_code": 0
        }
    
    # Get risk counts from results file
    results_file = current_app.config["BASE_DIR"] / f"{model}/app{app_num}/.zap_results.json"
    counts = {"high": 0, "medium": 0, "low": 0, "info": 0}
    vulnerabilities_with_code = 0
    
    if results_file.exists():
        try:
            # Check if file is empty or has minimal content
            if results_file.stat().st_size < 10:  # Less than 10 bytes
                zap_logger.warning(f"Results file for {model}/app{app_num} exists but is empty or too small")
            else:
                with open(results_file) as f:
                    try:
                        data = json.load(f)
                        
                        # Count alerts by risk level
                        for alert in data.get("alerts", []):
                            risk = alert.get("risk", "").lower()
                            if risk in counts:
                                counts[risk] += 1
                            
                            # Count alerts with affected code
                            if alert.get('affected_code') and alert.get('affected_code', {}).get('snippet'):
                                vulnerabilities_with_code += 1
                        
                        # If the scan is complete, get duration information
                        summary = data.get("summary", {})
                        if summary.get("status") == "success" and "start_time" in summary and "end_time" in summary:
                            scan["duration_seconds"] = summary.get("duration_seconds", 0)
                            # Also get code analysis data from summary if available
                            if "vulnerabilities_with_code" in summary:
                                vulnerabilities_with_code = summary.get("vulnerabilities_with_code", 0)
                    except json.JSONDecodeError as e:
                        zap_logger.error(f"Invalid JSON in results file for {model}/app{app_num}: {str(e)}")
        except Exception as e:
            zap_logger.exception(f"Error reading results file for {model}/app{app_num}: {str(e)}")
            # Continue with default counts, don't fail the request
    
    # Build response with detailed status info
    # Include default values for all fields to prevent client-side errors
    response = {
        "status": scan.get("status", "Unknown"),
        "progress": scan.get("progress", 0),
        "high_count": counts["high"],
        "medium_count": counts["medium"],
        "low_count": counts["low"],
        "info_count": counts["info"],
        "spider_progress": scan.get("spider_progress", 0),
        "passive_progress": scan.get("passive_progress", 0),
        "active_progress": scan.get("active_progress", 0),
        "ajax_progress": scan.get("ajax_progress", 0),
        "vulnerabilities_with_code": scan.get("vulnerabilities_with_code", vulnerabilities_with_code)
    }
    
    # Add timestamps if available
    if "start_time" in scan:
        response["start_time"] = scan["start_time"]
    if "end_time" in scan:
        response["end_time"] = scan["end_time"]
    if "duration_seconds" in scan:
        response["duration_seconds"] = scan["duration_seconds"]
    
    return response


@zap_bp.route("/scan/<string:model>/<int:app_num>/stop", methods=["POST"])
@ajax_compatible
def stop_zap_scan(model: str, app_num: int):
    """
    Stop a running ZAP scan.
    
    Args:
        model: Model name
        app_num: App number
        
    Returns:
        JSON with stop operation result
    """
    zap_logger = create_logger_for_component('zap')
    zap_logger.info(f"Request to stop ZAP scan for {model}/app{app_num}")
    
    scan_manager = get_scan_manager()
    scan = scan_manager.get_scan(model, app_num)
    
    if not scan:
        zap_logger.warning(f"Stop request failed: No scan found for {model}/app{app_num}")
        return APIResponse(
            success=False,
            error="No running scan found",
            code=404
        )
    
    if scan["status"] in ("Complete", "Failed", "Stopped"):
        zap_logger.warning(f"Stop request ignored: Scan for {model}/app{app_num} is already in state {scan['status']}")
        return APIResponse(
            success=False,
            error=f"Scan is not running (current status: {scan['status']})",
            code=400
        )
    
    try:
        zap_logger.info(f"Stopping scan for {model}/app{app_num}")
        
        # Attempt to gracefully clean up ZAP resources
        if "scanner" in scan and scan["scanner"]:
            zap_logger.debug(f"Cleaning up ZAP resources for {model}/app{app_num}")
            scan["scanner"]._cleanup_existing_zap()
            zap_logger.info(f"ZAP resources cleaned up for {model}/app{app_num}")
        
        # Update scan status
        scan_id = next(sid for sid, s in scan_manager.scans.items() if s == scan)
        scan_manager.update_scan(
            scan_id,
            status="Stopped", 
            progress=0,
            end_time=datetime.now().isoformat()
        )
        
        zap_logger.info(f"Scan for {model}/app{app_num} successfully stopped")
        return {"status": "stopped"}
    except Exception as e:
        error_msg = f"Failed to stop scan for {model}/app{app_num}: {str(e)}"
        zap_logger.exception(error_msg)
        return APIResponse(
            success=False,
            error=error_msg,
            code=500
        )


@zap_bp.route("/code_report/<string:model>/<int:app_num>")
def download_code_report(model: str, app_num: int):
    """
    Download the code analysis report for a specific app.
    
    Args:
        model: Model name
        app_num: App number
        
    Returns:
        Markdown file download or error response
    """
    zap_logger = create_logger_for_component('zap')
    zap_logger.info(f"Code report download requested for {model}/app{app_num}")
    
    base_dir: Path = current_app.config["BASE_DIR"]
    report_file = base_dir / f"{model}/app{app_num}/.zap_code_report.md"
    
    if not report_file.exists():
        zap_logger.warning(f"Code report file not found for {model}/app{app_num}")
        return APIResponse(
            success=False,
            error="Code analysis report not found. Please run a scan first.",
            code=404
        )
    
    try:
        zap_logger.info(f"Sending code report file for {model}/app{app_num}")
        return send_file(
            report_file,
            mimetype="text/markdown",
            as_attachment=True,
            download_name=f"security_code_report_{model}_app{app_num}.md"
        )
    except Exception as e:
        error_msg = f"Failed to send code report for {model}/app{app_num}: {str(e)}"
        zap_logger.exception(error_msg)
        return APIResponse(
            success=False,
            error=error_msg,
            code=500
        )


@zap_bp.route("/regenerate_code_report/<string:model>/<int:app_num>", methods=["POST"])
@ajax_compatible
def regenerate_code_report(model: str, app_num: int):
    """
    Regenerate the code analysis report for a specific app from existing scan results.
    Useful when modifying the report format without rescanning.
    
    Args:
        model: Model name
        app_num: App number
        
    Returns:
        JSON response indicating success or failure
    """
    zap_logger = create_logger_for_component('zap')
    zap_logger.info(f"Code report regeneration requested for {model}/app{app_num}")
    
    base_dir: Path = current_app.config["BASE_DIR"]
    results_file = base_dir / f"{model}/app{app_num}/.zap_results.json"
    report_file = base_dir / f"{model}/app{app_num}/.zap_code_report.md"
    
    if not results_file.exists():
        zap_logger.warning(f"Results file not found for {model}/app{app_num}")
        return APIResponse(
            success=False,
            error="Scan results not found. Please run a scan first.",
            code=404
        )
    
    try:
        zap_logger.info(f"Reading scan results to regenerate code report for {model}/app{app_num}")
        with open(results_file, encoding='utf-8') as f:
            data = json.load(f)
            vulnerabilities = data.get("alerts", [])
        
        if not vulnerabilities:
            zap_logger.warning(f"No vulnerabilities found in scan results for {model}/app{app_num}")
            return APIResponse(
                success=False,
                error="No vulnerabilities found in scan results.",
                code=404
            )
        
        # Create scanner instance for report generation only
        scanner = create_scanner(base_dir)
        
        # Generate report
        zap_logger.info(f"Generating code report for {model}/app{app_num}")
        report_content = scanner.generate_affected_code_report(vulnerabilities, str(report_file))
        
        vulnerabilities_with_code = sum(1 for v in vulnerabilities if v.get('affected_code') and 
                                      v.get('affected_code', {}).get('snippet'))
        
        zap_logger.info(f"Code report generated successfully with {vulnerabilities_with_code} code-related findings")
        return {
            "success": True, 
            "message": f"Code report regenerated with {vulnerabilities_with_code} code-related findings.",
            "vulnerabilities_with_code": vulnerabilities_with_code
        }
    except Exception as e:
        error_msg = f"Failed to regenerate code report for {model}/app{app_num}: {str(e)}"
        zap_logger.exception(error_msg)
        return APIResponse(
            success=False,
            error=error_msg,
            code=500
        )
# ----- Analysis Routes -----
@analysis_bp.route("/backend-security/<string:model>/<int:app_num>")
@ajax_compatible
def security_analysis(model: str, app_num: int):
    """
    Run backend security analysis for an app.
    
    Args:
        model: Model name
        app_num: App number
        
    Returns:
        Rendered template with security analysis results
    """
    security_logger = create_logger_for_component('security')
    security_logger.info(f"Backend security analysis requested for {model}/app{app_num}")
    
    full_scan = request.args.get("full", "").lower() == "true"
    analyzer = current_app.backend_security_analyzer
    return process_security_analysis(
        template="security_analysis.html",
        analyzer=analyzer,
        analysis_method=analyzer.run_security_analysis,
        model=model,
        app_num=app_num,
        full_scan=full_scan,
        no_issue_message="No security issues found in the codebase."
    )


@analysis_bp.route("/frontend-security/<string:model>/<int:app_num>")
@ajax_compatible
def frontend_security_analysis(model: str, app_num: int):
    """
    Run frontend security analysis for an app.
    
    Args:
        model: Model name
        app_num: App number
        
    Returns:
        Rendered template with security analysis results
    """
    security_logger = create_logger_for_component('security')
    security_logger.info(f"Frontend security analysis requested for {model}/app{app_num}")
    
    full_scan = request.args.get("full", "").lower() == "true"
    analyzer = current_app.frontend_security_analyzer
    return process_security_analysis(
        template="security_analysis.html",
        analyzer=analyzer,
        analysis_method=analyzer.run_security_analysis,
        model=model,
        app_num=app_num,
        full_scan=full_scan,
        no_issue_message="No security issues found in frontend code."
    )


@api_bp.route("/analyze-security", methods=["POST"])
@ajax_compatible
def analyze_security_issues():
    """
    Analyze security issues with AI.
    
    Returns:
        JSON with AI analysis results
    """
    security_logger = create_logger_for_component('security')
    
    try:
        data = request.get_json()
        if not data or "issues" not in data:
            security_logger.warning("No issues provided for security analysis")
            raise BadRequest("No issues provided for analysis")
        
        model_name = data.get("model", "default-model")
        issues = data["issues"]
        
        security_logger.info(f"Analyzing {len(issues)} security issues using AI for model {model_name}")
        
        # Group issues by tool first
        tool_groups = {}
        for issue in issues:
            tool = issue.get("tool", "unknown")
            if tool not in tool_groups:
                tool_groups[tool] = []
            tool_groups[tool].append(issue)
        
        # Build a structured prompt for the AI
        prompt = "# Security Analysis of Frontend Code\n\n"
        
        # Add overall summary
        prompt += f"## Overview\n"
        prompt += f"Total issues detected: {len(issues)}\n"
        
        # Add tool-specific sections
        for tool, tool_issues in tool_groups.items():
            tool_display_name = {
                "pattern_scan": "Pattern-based Security Scanner",
                "dependency_check": "Dependency Vulnerability Checker",
                "semgrep": "Semgrep Static Analysis",
                "jshint": "JSHint Code Quality"
            }.get(tool, tool.title())
            
            prompt += f"\n## Issues from {tool_display_name}\n"
            
            # Group by severity
            severity_groups = {}
            for issue in tool_issues:
                severity = issue.get('severity', 'unknown')
                if severity not in severity_groups:
                    severity_groups[severity] = []
                severity_groups[severity].append(issue)
            
            # Sort severities: high > medium > low > others
            severity_order = ["high", "medium", "low"]
            other_severities = [s for s in severity_groups.keys() if s not in severity_order]
            ordered_severities = [s for s in severity_order if s in severity_groups] + other_severities
            
            # Add each severity group
            for severity in ordered_severities:
                issues_in_group = severity_groups[severity]
                prompt += f"\n### {severity.title()} severity issues ({len(issues_in_group)})\n"
                
                for issue in issues_in_group:
                    issue_type = issue.get('issue_type', 'Unknown issue')
                    issue_text = issue.get('issue_text', '')
                    file_name = issue.get('filename', 'unknown file')
                    
                    prompt += f"- **{issue_type}**: {issue_text}\n"
                    if file_name and file_name != "unknown file":
                        prompt += f"  - File: {file_name}\n"
                    
                    code = issue.get('code', '')
                    if code and len(code) > 0:
                        # Truncate long code snippets
                        if len(code) > 200:
                            code = code[:197] + "..."
                        prompt += f"  - Code: `{code}`\n"
        
        # Add guidance for the analysis
        prompt += """
## Analysis Request

Please provide:

1. A **tool-by-tool analysis** of the security issues found, with focus on the most critical issues
2. A **prioritized list of recommendations** for addressing these issues, ordered by importance
3. **Potential security implications** if these issues aren't addressed
4. **Best practices** to prevent similar issues in frontend code

Format your response with clear headings and concise explanations suitable for a technical team.
"""
        
        # Call AI service for analysis
        security_logger.info(f"Sending security analysis prompt to AI service (length: {len(prompt)} chars)")
        analysis_result = call_ai_service(model_name, prompt)
        security_logger.info("Received security analysis from AI service")
        
        return APIResponse(
            success=True,
            data={"response": analysis_result}
        )
        
    except BadRequest as e:
        security_logger.warning(f"Bad request in security analysis: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            code=400
        )
    except Exception as e:
        security_logger.exception(f"Error in security analysis: {e}")
        return APIResponse(
            success=False,
            error="Analysis failed",
            code=500
        )

@analysis_bp.route("/security/summary/<string:model>/<int:app_num>")
@ajax_compatible
def get_security_summary(model: str, app_num: int):
    """
    Get security analysis summary for an app.
    
    Args:
        model: Model name
        app_num: App number
        
    Returns:
        JSON with security summary
    """
    security_logger = create_logger_for_component('security')
    security_logger.info(f"Security summary requested for {model}/app{app_num}")
    
    try:
        security_logger.debug(f"Running backend security analysis for {model}/app{app_num}")
        backend_issues, backend_status, _ = current_app.backend_security_analyzer.analyze_security(
            model, app_num, use_all_tools=False
        )
        backend_summary = current_app.backend_security_analyzer.get_analysis_summary(backend_issues)
        
        security_logger.debug(f"Running frontend security analysis for {model}/app{app_num}")
        frontend_issues, frontend_status, _ = current_app.frontend_security_analyzer.run_security_analysis(
            model, app_num, use_all_tools=False
        )
        frontend_summary = current_app.frontend_security_analyzer.get_analysis_summary(frontend_issues)
        
        total_issues = backend_summary["total_issues"] + frontend_summary["total_issues"]
        security_logger.info(f"Security summary for {model}/app{app_num}: {total_issues} total issues found")
        
        combined_summary = {
            "backend": {"summary": backend_summary, "status": backend_status},
            "frontend": {"summary": frontend_summary, "status": frontend_status},
            "total_issues": total_issues,
            "severity_counts": {
                "HIGH": backend_summary["severity_counts"]["HIGH"] + frontend_summary["severity_counts"]["HIGH"],
                "MEDIUM": backend_summary["severity_counts"]["MEDIUM"] + frontend_summary["severity_counts"]["MEDIUM"],
                "LOW": backend_summary["severity_counts"]["LOW"] + frontend_summary["severity_counts"]["LOW"],
            },
            "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        return combined_summary
    except Exception as e:
        security_logger.exception(f"Error getting security summary for {model}/app{app_num}: {e}")
        return APIResponse(
            success=False,
            error="Failed to get security summary",
            details=str(e),
            code=500
        )


@analysis_bp.route("/security/analyze-file", methods=["POST"])
@ajax_compatible
def analyze_single_file():
    """
    Analyze a single file for security issues.
    
    Returns:
        JSON with analysis results
    """
    security_logger = create_logger_for_component('security')
    
    try:
        data = request.get_json()
        if not data or "file_path" not in data:
            security_logger.warning("No file path provided for file analysis")
            raise BadRequest("No file path provided")
        
        file_path = Path(data["file_path"])
        is_frontend = data.get("is_frontend", False)
        file_type = "frontend" if is_frontend else "backend"
        
        security_logger.info(f"Analyzing single {file_type} file: {file_path}")
        analyzer = current_app.frontend_security_analyzer if is_frontend else current_app.backend_security_analyzer
        
        if is_frontend:
            security_logger.debug(f"Running ESLint on {file_path.parent}")
            issues, tool_status, tool_output = analyzer._run_eslint(file_path.parent)
        else:
            security_logger.debug(f"Running Bandit on {file_path.parent}")
            issues, tool_status, tool_output = analyzer._run_bandit(file_path.parent)
            
        file_issues = [issue for issue in issues if Path(issue.filename).name == file_path.name]
        security_logger.info(f"Found {len(file_issues)} issues in {file_path.name}")
        
        return {
            "status": "success",
            "issues": [asdict(issue) for issue in file_issues],
            "tool_status": tool_status,
            "tool_output": tool_output,
        }
    except BadRequest as e:
        security_logger.warning(f"Bad request in file analysis: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            code=400
        )
    except Exception as e:
        security_logger.exception(f"Error analyzing file: {e}")
        return APIResponse(
            success=False,
            error="File analysis failed",
            code=500
        )

# ----- Performance Testing Routes -----
@performance_bp.route("/<string:model>/<int:port>", methods=["GET", "POST"])
@ajax_compatible
def performance_test(model: str, port: int):
    """
    Route for performance testing a specific model application.
    
    Args:
        model: The model identifier
        port: The port to test
        
    Returns:
        On GET: Renders the performance test page
        On POST: Runs the test and returns JSON results
    """
    perf_logger = create_logger_for_component('performance')
    
    # Get the base directory from app config for storing test results
    base_dir = current_app.config.get("BASE_DIR", Path("."))
    output_dir = base_dir / "performance_reports"
    
    if request.method == "POST":
        perf_logger.info(f"Starting performance test for {model} on port {port}")
        try:
            # Create the tester instance
            tester = LocustPerformanceTester(output_dir=output_dir)
            
            data = request.get_json()
            num_users = int(data.get("num_users", 10))
            duration = int(data.get("duration", 30))
            spawn_rate = int(data.get("spawn_rate", 1))
            endpoints = data.get("endpoints", ["/"])
            
            perf_logger.info(
                f"Test parameters: users={num_users}, duration={duration}s, "
                f"spawn_rate={spawn_rate}, endpoints={len(endpoints)}"
            )
            
            # Convert simple endpoint strings to endpoint dictionaries
            formatted_endpoints = []
            for endpoint in endpoints:
                if isinstance(endpoint, str):
                    formatted_endpoints.append({
                        "path": endpoint,
                        "method": "GET",
                        "weight": 1
                    })
                else:
                    formatted_endpoints.append(endpoint)
            
            # Generate a unique test name
            test_name = f"{model}_{port}"
            
            # Run the test using the CLI approach (easier for web integration)
            perf_logger.info(f"Running test: {test_name} against http://localhost:{port}")
            result = tester.run_test_cli(
                test_name=test_name,
                host=f"http://localhost:{port}",
                endpoints=formatted_endpoints,
                user_count=num_users,
                spawn_rate=spawn_rate,
                run_time=f"{duration}s",
                html_report=True
            )
            
            # If test completed successfully
            if result:
                perf_logger.info(f"Test completed successfully: {test_name}")
                # Find the generated report file
                report_files = list(output_dir.glob(f"{test_name}_*/*_report.html"))
                report_path = report_files[0] if report_files else None
                
                relative_path = str(report_path.relative_to(base_dir)) if report_path else ""
                perf_logger.info(f"Report generated at: {relative_path}")
                
                return {
                    "status": "success",
                    "data": result.to_dict(),
                    "report_path": f"/static/{relative_path}"
                }
            else:
                perf_logger.error(f"Test execution failed for {test_name}")
                return APIResponse(
                    success=False,
                    error="Test execution failed. Check server logs for details.",
                    code=500
                )
        except Exception as e:
            perf_logger.exception(f"Performance test error for {model} on port {port}: {e}")
            return APIResponse(
                success=False,
                error=str(e),
                code=500
            )
    else:
        # GET request - render the test form
        perf_logger.info(f"Rendering performance test form for {model} on port {port}")
        return render_template("performance_test.html", model=model, port=port)


@performance_bp.route("/<string:model>/<int:port>/stop", methods=["POST"])
@ajax_compatible
def stop_performance_test(model: str, port: int):
    """
    Stop a running performance test.
    
    Args:
        model: Model name
        port: Port number
        
    Returns:
        JSON with stop operation result
    """
    perf_logger = create_logger_for_component('performance')
    perf_logger.info(f"Request to stop performance test for {model} on port {port}")
    
    try:
        # In a real implementation, you would:
        # 1. Check if there's a running test for this model/port
        # 2. Use subprocess to kill the Locust process or terminate the test
        
        # For now, we'll tell the user this is a placeholder
        perf_logger.warning(f"Performance test stop not fully implemented for {model} on port {port}")
        return {
            "status": "success", 
            "message": "Test stop requested. Note: Actual test stopping depends on your environment setup."
        }
    except Exception as e:
        perf_logger.exception(f"Error stopping performance test for {model} on port {port}: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            code=500
        )


@performance_bp.route("/<string:model>/<int:port>/reports", methods=["GET"])
@ajax_compatible
def list_performance_reports(model: str, port: int):
    """
    List available performance reports for a specific model/port.
    
    Args:
        model: Model name
        port: Port number
        
    Returns:
        JSON with available reports
    """
    perf_logger = create_logger_for_component('performance')
    perf_logger.info(f"Listing performance reports for {model} on port {port}")
    
    try:
        base_dir = current_app.config.get("BASE_DIR", Path("."))
        report_dir = base_dir / "performance_reports"
        if not report_dir.exists():
            perf_logger.debug(f"Report directory does not exist: {report_dir}")
            return {"reports": []}
        
        # Search for test directories with this model/port pattern
        reports = []
        test_name = f"{model}_{port}"
        
        # First, find all test directories
        perf_logger.debug(f"Searching for test directories with pattern: {test_name}")
        test_dirs = [d for d in report_dir.iterdir() if d.is_dir() and d.name.startswith(test_name)]
        
        for test_dir in test_dirs:
            # Extract timestamp from directory name
            try:
                timestamp = test_dir.name.split('_')[-1]
                formatted_time = datetime.strptime(timestamp, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, IndexError):
                timestamp = ""
                formatted_time = "Unknown date"
            
            # Find HTML report in this directory
            html_reports = list(test_dir.glob("*_report.html"))
            if html_reports:
                report_file = html_reports[0]
                
                # Also look for any graphs
                graphs = []
                for graph_file in test_dir.glob("*.png"):
                    graphs.append({
                        "name": graph_file.stem,
                        "path": f"/static/performance_reports/{test_dir.name}/{graph_file.name}"
                    })
                
                reports.append({
                    "id": test_dir.name,
                    "test_name": test_name,
                    "filename": report_file.name,
                    "path": f"/static/performance_reports/{test_dir.name}/{report_file.name}",
                    "timestamp": timestamp,
                    "created": formatted_time,
                    "graphs": graphs
                })
        
        perf_logger.info(f"Found {len(reports)} performance reports for {model} on port {port}")
        return {"reports": sorted(reports, key=lambda x: x.get("timestamp", ""), reverse=True)}
    except Exception as e:
        perf_logger.exception(f"Error listing performance reports for {model} on port {port}: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            code=500
        )


@performance_bp.route("/<string:model>/<int:port>/reports/<path:report_id>", methods=["GET"])
@ajax_compatible
def view_performance_report(model: str, port: int, report_id: str):
    """
    View a specific performance report.
    
    Args:
        model: Model name
        port: Port number
        report_id: Report directory ID (usually contains timestamp)
        
    Returns:
        Rendered template with report content
    """
    perf_logger = create_logger_for_component('performance')
    perf_logger.info(f"Viewing performance report {report_id} for {model} on port {port}")
    
    try:
        base_dir = current_app.config.get("BASE_DIR", Path("."))
        report_dir = base_dir / "performance_reports" / report_id
        
        if not report_dir.exists():
            perf_logger.warning(f"Report directory not found: {report_dir}")
            return render_template("404.html", message="Report not found"), 404
        
        # For security, verify this is a report for the requested model/port
        test_name = f"{model}_{port}"
        if not report_id.startswith(test_name):
            perf_logger.warning(f"Invalid report ID requested: {report_id} (expected pattern: {test_name})")
            return render_template("404.html", message="Invalid report ID"), 404
        
        # Find HTML report in this directory
        html_reports = list(report_dir.glob("*_report.html"))
        if not html_reports:
            perf_logger.warning(f"No HTML report file found in directory: {report_dir}")
            return render_template("404.html", message="Report file not found"), 404
        
        report_file = html_reports[0]
        perf_logger.debug(f"Loading report content from: {report_file}")
        with open(report_file, "r", encoding='utf-8', errors='replace') as f:
            report_content = f.read()
        
        # Find CSV files for additional data
        csv_files = {}
        for csv_file in report_dir.glob("*.csv"):
            with open(csv_file, "r", encoding='utf-8', errors='replace') as f:
                csv_files[csv_file.stem] = f.read()
        
        # Find graph images
        graphs = []
        for graph_file in report_dir.glob("*.png"):
            graphs.append({
                "name": graph_file.stem.replace("_", " ").title(),
                "path": f"/static/performance_reports/{report_id}/{graph_file.name}"
            })
        
        perf_logger.info(f"Rendering report with {len(graphs)} graphs and {len(csv_files)} CSV files")
        return render_template(
            "performance_report_viewer.html", 
            model=model, 
            port=port, 
            report_id=report_id,
            report_content=report_content,
            csv_files=csv_files,
            graphs=graphs
        )
    except Exception as e:
        perf_logger.exception(f"Error viewing performance report {report_id}: {e}")
        return render_template("500.html", error=str(e)), 500


@performance_bp.route("/<string:model>/<int:port>/results/<path:report_id>", methods=["GET"])
@ajax_compatible
def get_performance_results(model: str, port: int, report_id: str):
    """
    Get the raw JSON results for a specific test.
    
    Args:
        model: Model name
        port: Port number
        report_id: Report directory ID
        
    Returns:
        JSON with test results
    """
    perf_logger = create_logger_for_component('performance')
    perf_logger.info(f"Getting raw performance results for {report_id}")
    
    try:
        base_dir = current_app.config.get("BASE_DIR", Path("."))
        report_dir = base_dir / "performance_reports" / report_id
        
        if not report_dir.exists():
            perf_logger.warning(f"Results directory not found: {report_dir}")
            return APIResponse(
                success=False,
                error="Report not found",
                code=404
            )
        
        # Look for a JSON results file
        json_files = list(report_dir.glob("*_results.json"))
        if json_files:
            perf_logger.debug(f"Loading JSON results from: {json_files[0]}")
            with open(json_files[0], "r", encoding='utf-8', errors='replace') as f:
                return json.load(f)
        
        # If no JSON file, try to parse the stats CSV
        stats_files = list(report_dir.glob("*_stats.csv"))
        if stats_files:
            perf_logger.debug(f"No JSON results file found. Using CSV file: {stats_files[0]}")
            # This would require a function to parse the CSV into a result object
            # For now, we'll return a simplified structure
            return {
                "status": "success",
                "message": "Raw results not available, but CSV files exist",
                "csv_file": f"/static/performance_reports/{report_id}/{stats_files[0].name}"
            }
        
        perf_logger.warning(f"No result data found in directory: {report_dir}")
        return APIResponse(
            success=False,
            error="No result data found",
            code=404
        )
    except Exception as e:
        perf_logger.exception(f"Error getting performance results for {report_id}: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            code=500
        )


@performance_bp.route("/<string:model>/<int:port>/reports/<path:report_id>/delete", methods=["POST"])
@ajax_compatible
def delete_performance_report(model: str, port: int, report_id: str):
    """
    Delete a specific performance report.
    
    Args:
        model: Model name
        port: Port number
        report_id: Report directory ID
        
    Returns:
        JSON with deletion result
    """
    perf_logger = create_logger_for_component('performance')
    perf_logger.info(f"Request to delete performance report {report_id}")
    
    try:
        base_dir = current_app.config.get("BASE_DIR", Path("."))
        report_dir = base_dir / "performance_reports" / report_id
        
        if not report_dir.exists():
            perf_logger.warning(f"Report directory not found for deletion: {report_dir}")
            return APIResponse(
                success=False,
                error="Report not found",
                code=404
            )
        
        # For security, verify this is a report for the requested model/port
        test_name = f"{model}_{port}"
        if not report_id.startswith(test_name):
            perf_logger.warning(f"Invalid report ID for deletion: {report_id}")
            return APIResponse(
                success=False,
                error="Invalid report ID",
                code=400
            )
        
        # Delete all files in the directory
        file_count = 0
        for file in report_dir.iterdir():
            file.unlink()
            file_count += 1
        
        # Remove the directory
        report_dir.rmdir()
        perf_logger.info(f"Successfully deleted report {report_id} with {file_count} files")
        
        return {
            "status": "success",
            "message": f"Report {report_id} deleted successfully"
        }
    except Exception as e:
        perf_logger.exception(f"Error deleting performance report {report_id}: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            code=500
        )
    

# ----- GPT4All Routes -----
@gpt4all_bp.route("/analyze-gpt4all/<string:analysis_type>", methods=["POST"])
@ajax_compatible
def analyze_gpt4all(analysis_type: str):
    """
    Run GPT4All analysis on code.
    
    Args:
        analysis_type: Type of analysis to run
        
    Returns:
        JSON with analysis results
    """
    try:
        data = request.get_json()
        directory = Path(data.get("directory", current_app.config["BASE_DIR"]))
        file_patterns = data.get("file_patterns", ["*.py", "*.js", "*.ts", "*.react"])
        analyzer = GPT4AllAnalyzer(directory)
        
        # Handle asyncio in Flask properly
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        issues, summary = loop.run_until_complete(analyzer.analyze_directory(
            directory=directory, file_patterns=file_patterns, analysis_type=analysis_type
        ))
        loop.close()
        
        if not isinstance(summary, dict):
            summary = analyzer.get_analysis_summary(issues)
            
        return {
            "issues": [asdict(issue) for issue in issues], 
            "summary": summary
        }
    except Exception as e:
        logger.error(f"GPT4All analysis failed: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            code=500
        )

@gpt4all_bp.route("/gpt4all-analysis", methods=["GET", "POST"])
def gpt4all_analysis():
    """Flask route for checking requirements against code."""
    try:
        # Extract parameters
        model = request.args.get("model") or request.form.get("model")
        app_num_str = request.args.get("app_num") or request.form.get("app_num")
        
        # Validate required parameters
        if not model or not app_num_str:
            return render_template(
                "requirements_check.html",
                model=None,
                app_num=None,
                requirements=[],
                results=None,
                error="Model and app number are required"
            )
            
        try:
            app_num = int(app_num_str)
        except ValueError:
            return render_template(
                "requirements_check.html",
                model=model,
                app_num=None,
                requirements=[],
                results=None,
                error=f"Invalid app number: {app_num_str}"
            )
            
        # Find the application directory using the enhanced path handling
        base_dir = current_app.config.get("BASE_DIR", Path.cwd())
        directory = PathUtils.find_app_directory(base_dir, model, app_num)
        
        if not directory:
            # Try harder to find a valid directory
            all_possible_dirs = [
                get_app_directory(current_app, model, app_num),
                base_dir / f"{model}/app{app_num}",
                base_dir / f"{model.lower()}/app{app_num}",
                base_dir / "z_interface_app" / f"{model}/app{app_num}",
                base_dir / "z_interface_app" / f"{model.lower()}/app{app_num}"
            ]
            
            # Show more informative error
            error_msg = f"Directory not found: Tried paths: {', '.join(str(p) for p in all_possible_dirs)}"
            return render_template(
                "requirements_check.html",
                model=model,
                app_num=app_num,
                requirements=[],
                results=None,
                error=error_msg
            )
        
        # Setup for requirements analysis
        req_list = []
        results = None
        
        # Handle requirements from POST
        if request.method == "POST" and "requirements" in request.form:
            requirements_text = request.form.get("requirements", "")
            req_list = [r.strip() for r in requirements_text.strip().splitlines() if r.strip()]
            
            if req_list:
                # Initialize analyzer with the correct directory
                analyzer = GPT4AllAnalyzer(directory)
                
                # Run check for each requirement using proper asyncio handling in Flask
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(analyzer.check_requirements(directory, req_list))
                loop.close()
                
                # Log success
                logger.info(f"Successfully analyzed requirements for {model}/app{app_num}")
        
        # Render template with form or results
        return render_template(
            "requirements_check.html",
            model=model,
            app_num=app_num,
            requirements=req_list,
            results=results,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Requirements check failed: {e}")
        return render_template(
            "requirements_check.html",
            model=model if "model" in locals() else None,
            app_num=app_num if "app_num" in locals() else None,
            requirements=[],
            results=None,
            error=str(e)
        )



# =============================================================================
# Error Handlers & Request Hooks
# =============================================================================
def register_error_handlers(app: Flask) -> None:
    """Register Flask error handlers."""
    error_logger = create_logger_for_component('errors')
    
    @app.errorhandler(404)
    def not_found(error):
        error_logger.warning(f"404 error: {request.path} - {error}")
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({
                "success": False,
                "error": "Not found",
                "message": str(error)
            }), 404
        return render_template("404.html", error=error), 404

    @app.errorhandler(500)
    def server_error(error):
        error_logger.error(f"500 error: {request.path} - {error}")
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({
                "success": False,
                "error": "Internal server error",
                "message": str(error)
            }), 500
        return render_template("500.html", error=error), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        error_logger.exception(f"Unhandled exception: {request.path} - {error}")
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({
                "success": False,
                "error": str(error),
            }), 500
        return render_template("500.html", error=error), 500


def register_request_hooks(app: Flask, docker_manager: DockerManager) -> None:
    """
    Register Flask request hooks.
    
    Args:
        app: Flask app instance
        docker_manager: Docker manager instance
    """
    hooks_logger = create_logger_for_component('hooks')
    
    @app.before_request
    def before():
        # Occasional cleanup
        if random.random() < 0.01:
            hooks_logger.debug("Running occasional cleanup tasks")
            try:
                docker_manager.cleanup_containers()
                if "ZAP_SCANS" in app.config:
                    stop_zap_scanners(app.config["ZAP_SCANS"])
            except Exception as e:
                hooks_logger.exception(f"Error during cleanup tasks: {e}")

    @app.after_request
    def after(response):
        # Security headers
        response.headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        })
        
        # Add cache control for AJAX requests
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            
        return response

    @app.teardown_appcontext
    def teardown(exception=None):
        if exception:
            hooks_logger.warning(f"Context teardown with exception: {exception}")
            
        if "ZAP_SCANS" in app.config:
            hooks_logger.debug("Stopping active ZAP scans during teardown")
            stop_zap_scanners(app.config["ZAP_SCANS"])

# =============================================================================
# Flask App Factory
# =============================================================================
def create_app(config: Optional[AppConfig] = None) -> Flask:
    """
    Create and configure the Flask application.
    
    Args:
        config: Optional configuration object
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    app_config = config or AppConfig.from_env()
    app.config.from_object(app_config)
    app.config["BASE_DIR"] = app_config.BASE_DIR
    
    # Initialize the enhanced logging system
    initialize_logging(app)
    app_logger = create_logger_for_component('app')
    app_logger.info("Starting application setup")
    
    # Use enhanced JSON encoder
    app.json_encoder = CustomJSONEncoder
    
    # Log base path information
    base_path = app_config.BASE_DIR.parent
    app_logger.info(f"Application base path: {app_config.BASE_DIR}")
    app_logger.info(f"Parent base path: {base_path}")

    # Initialize analyzers and other services
    app_logger.info("Initializing security analyzers")
    app.backend_security_analyzer = BackendSecurityAnalyzer(base_path)
    app.frontend_security_analyzer = FrontendSecurityAnalyzer(base_path)
    
    app_logger.info("Initializing GPT4All analyzer")
    app.gpt4all_analyzer = GPT4AllAnalyzer(base_path)
    
    app_logger.info("Initializing performance tester")
    app.performance_tester = LocustPerformanceTester(base_path)
    
    app_logger.info("Initializing ZAP scanner")
    app.zap_scanner = create_scanner(app_config.BASE_DIR)

    app_logger.info("Creating Docker manager")
    docker_manager = DockerManager()
    app.config["docker_manager"] = docker_manager

    app_logger.info("Configuring proxy fix middleware")
    app.wsgi_app = ProxyFix(app.wsgi_app)

    # Register blueprints
    app_logger.info("Registering application blueprints")
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(analysis_bp)
    app.register_blueprint(performance_bp, url_prefix="/performance")
    app.register_blueprint(gpt4all_bp)
    app.register_blueprint(zap_bp, url_prefix="/zap")

    # Initialize batch analysis module
    app_logger.info("Initializing batch analysis module")
    init_batch_analysis(app)
    
    # Register batch analysis blueprint
    app.register_blueprint(batch_analysis_bp, url_prefix="/batch-analysis")

    app_logger.info("Registering error handlers and request hooks")
    register_error_handlers(app)
    register_request_hooks(app, docker_manager)
    
    app_logger.info("Application initialization complete")
    return app

# =============================================================================
# Main Entry Point
# =============================================================================
if __name__ == "__main__":
    # Create loggers without relying on flask context
    import logging
    main_logger = logging.getLogger('main')
    main_logger.setLevel(logging.INFO)
    
    # Add a simple handler that doesn't rely on request context
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
    main_logger.addHandler(handler)
    
    main_logger.info("Application starting")
    
    config = AppConfig.from_env()
    
    try:
        main_logger.info(f"Creating application with LOG_LEVEL={config.LOG_LEVEL}")
        app = create_app(config)
        
        # System health checks should be done within app context
        with app.app_context():
            docker_manager = DockerManager()
            system_health = True
            
            if docker_manager.client:
                system_health = SystemHealthMonitor.check_health(docker_manager.client)
                if not system_health:
                    main_logger.warning("System health check failed - reduced functionality expected")
            else:
                main_logger.warning("Docker client unavailable - reduced functionality expected")
        
        main_logger.info(f"Starting Flask server on {config.HOST}:{config.PORT} (debug={config.DEBUG})")
        app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
    except Exception as e:
        main_logger.critical(f"Failed to start application: {e}", exc_info=True)
        raise e
# =============================================================================
# Optional: Database Manager for Storing Scan Data
# =============================================================================
class DatabaseManager:
    """Manages database operations for storing scan results."""
    
    def __init__(self, db_path="scans.db"):
        """
        Initialize database connection and tables.
        
        Args:
            db_path: Path to the SQLite database file
        """
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