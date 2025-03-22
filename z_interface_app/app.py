"""
Refactored Flask-based AI Model Management System

This version organizes routes into blueprints, centralizes error handling,
improves logging configuration, and separates utility functions for clarity.
"""

# =============================================================================
# Standard Library Imports
# =============================================================================
import asyncio
import json
import logging
import os
import random
import sqlite3
import subprocess
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# =============================================================================
# Third-Party Imports
# =============================================================================
import docker
from docker.errors import NotFound
from flask import (
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
    Blueprint,
    current_app,
)
from werkzeug.exceptions import BadRequest
from werkzeug.middleware.proxy_fix import ProxyFix

# =============================================================================
# Custom Module Imports
# =============================================================================
from backend_security_analysis import BackendSecurityAnalyzer
from frontend_security_analysis import FrontendSecurityAnalyzer
from gpt4all_analysis import GPT4AllAnalyzer
from performance_analysis import PerformanceTester
from zap_scanner import ZAPScanner, create_scanner
from batch_frontend_analysis import init_batch_analysis, batch_analysis_bp

# =============================================================================
# Module-Level Logger
# =============================================================================
logger = logging.getLogger(__name__)

# =============================================================================
# Configuration & Domain Models
# =============================================================================
@dataclass
class AppConfig:
    DEBUG: bool = True
    SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "your-secret-key-here")
    BASE_DIR: Path = Path(__file__).parent
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "ERROR")
    DOCKER_TIMEOUT: int = int(os.getenv("DOCKER_TIMEOUT", "10"))
    CACHE_DURATION: int = int(os.getenv("CACHE_DURATION", "5"))
    HOST: str = "0.0.0.0" if os.getenv("FLASK_ENV") == "production" else "127.0.0.1"
    PORT: int = int(os.getenv("PORT", "5000"))

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls()


@dataclass
class AIModel:
    name: str
    color: str


@dataclass
class DockerStatus:
    exists: bool = False
    running: bool = False
    health: str = "unknown"
    status: str = "unknown"
    details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


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
# Enhanced Request Logging Middleware
# =============================================================================
class RequestLoggerMiddleware:
    """
    Middleware to enhance request logging with additional context information.
    Adds referrer, user agent, client IP, and a request ID to logs.
    """
    
    def __init__(self, app):
        self.app = app
        self.logger = app.logger
        
        # Apply the middleware
        @app.before_request
        def before_request():
            # Generate a unique ID for this request
            request_id = str(uuid.uuid4())[:8]
            g.request_id = request_id
            g.start_time = time.time()
            
            # Log the beginning of the request with context
            referrer = request.referrer or 'No referrer'
            user_agent = request.user_agent.string if request.user_agent else 'No user agent'
            
            self.logger.info(
                f"REQUEST START [{request_id}]: {request.method} {request.path} | "
                f"Referrer: {referrer} | "
                f"User-Agent: {user_agent} | "
                f"IP: {request.remote_addr}"
            )
            
            # For AJAX requests, log additional context
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                self.logger.info(
                    f"AJAX REQUEST [{request_id}]: {request.method} {request.path} | "
                    f"Content-Type: {request.content_type}"
                )
                
        @app.after_request
        def after_request(response):
            # Calculate the request duration
            duration = time.time() - g.get('start_time', time.time())
            
            # Get the request_id or generate a fallback
            request_id = g.get('request_id', 'unknown')
            
            # Log the end of the request with status and duration
            self.logger.info(
                f"REQUEST END [{request_id}]: {request.method} {request.path} | "
                f"Status: {response.status_code} | "
                f"Duration: {duration:.4f}s"
            )
            
            # Add the request ID to the response headers for debugging
            response.headers['X-Request-ID'] = request_id
            
            return response
        
        # Handle exceptions in requests
        @app.errorhandler(Exception)
        def handle_exception(e):
            request_id = g.get('request_id', 'unknown')
            self.logger.error(
                f"REQUEST ERROR [{request_id}]: {request.method} {request.path} | "
                f"Error: {str(e)}"
            )
            # Let the regular error handlers take care of the response
            raise e

# =============================================================================
# Logging Configuration
# =============================================================================
class StatusEndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Filter out routine container status messages from the logs.
        if not hasattr(record, "args") or len(record.args) < 3:
            return True
        msg = record.args[2] if isinstance(record.args[2], str) else ""
        return "GET /api/container/" not in msg or not msg.endswith(' HTTP/1.1" 200 -')


class LoggingService:
    @staticmethod
    def configure(log_level: str) -> None:
        # More detailed log format that includes thread info
        log_format = (
            "%(asctime)s - %(name)s - [%(levelname)s] - "
            "%(threadName)s - %(message)s"
        )
        
        # Configure the basic logging
        logging.basicConfig(
            level=getattr(logging, log_level.upper(), logging.ERROR),
            format=log_format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Configure werkzeug to be more verbose by removing the filter
        werkzeug_logger = logging.getLogger("werkzeug")
        
        # Set specific log levels for various components
        logging.getLogger("zap_scanner").setLevel(logging.INFO)
        logging.getLogger("owasp_zap").setLevel(logging.WARNING)
        
        # Create a file handler for important logs
        try:
            file_handler = logging.FileHandler("app_requests.log")
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(logging.Formatter(log_format))
            
            # Add the file handler to the werkzeug logger and root logger
            werkzeug_logger.addHandler(file_handler)
            logging.getLogger().addHandler(file_handler)
            
            logging.info("File logging initialized successfully")
        except (IOError, PermissionError) as e:
            logging.warning(f"Could not initialize file logging: {e}")

# =============================================================================
# Port Management
# =============================================================================
class PortManager:
    BASE_BACKEND_PORT = 5001
    BASE_FRONTEND_PORT = 5501
    PORTS_PER_APP = 2
    BUFFER_PORTS = 20
    APPS_PER_MODEL = 30

    @classmethod
    def get_port_range(cls, model_idx: int) -> Dict[str, Dict[str, int]]:
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
        rng = cls.get_port_range(model_idx)
        return {
            "backend": rng["backend"]["start"] + (app_num - 1) * cls.PORTS_PER_APP,
            "frontend": rng["frontend"]["start"] + (app_num - 1) * cls.PORTS_PER_APP,
        }

# =============================================================================
# Docker Management
# =============================================================================
class DockerManager:
    def __init__(self, client: Optional[docker.DockerClient] = None) -> None:
        self.logger = logging.getLogger(__name__)
        self.client = client or self._create_docker_client()
        self._cache: Dict[str, Tuple[float, DockerStatus]] = {}
        self._cache_duration = AppConfig.from_env().CACHE_DURATION

    def _create_docker_client(self) -> Optional[docker.DockerClient]:
        try:
            docker_host = os.getenv("DOCKER_HOST", "npipe:////./pipe/docker_engine")
            return docker.DockerClient(
                base_url=docker_host,
                timeout=AppConfig.from_env().DOCKER_TIMEOUT,
            )
        except Exception as e:
            self.logger.error(f"Docker client creation failed: {e}")
            return None

    def get_container_status(self, container_name: str) -> DockerStatus:
        now = time.time()
        if container_name in self._cache:
            timestamp, status = self._cache[container_name]
            if now - timestamp < self._cache_duration:
                return status
        status = self._fetch_container_status(container_name)
        self._cache[container_name] = (now, status)
        return status

    def _fetch_container_status(self, container_name: str) -> DockerStatus:
        if not self.client:
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
            return DockerStatus(exists=False, status="no_container", details="Container not found")
        except Exception as e:
            self.logger.error(f"Docker error for {container_name}: {e}")
            return DockerStatus(exists=False, status="error", details=str(e))

    def get_container_logs(self, container_name: str, tail: int = 100) -> str:
        if not self.client:
            return "Docker client unavailable"
        try:
            container = self.client.containers.get(container_name)
            return container.logs(tail=tail).decode("utf-8")
        except Exception as e:
            self.logger.error(f"Log retrieval failed for {container_name}: {e}")
            return f"Log retrieval error: {e}"

    def cleanup_containers(self) -> None:
        if not self.client:
            return
        try:
            self.client.containers.prune(filters={"until": "24h"})
        except Exception as e:
            self.logger.error(f"Container cleanup failed: {e}")

# =============================================================================
# System Health Monitoring
# =============================================================================
class SystemHealthMonitor:
    @staticmethod
    def check_disk_space() -> bool:
        try:
            if os.name == "nt":
                result = subprocess.run(
                    ["wmic", "logicaldisk", "get", "size,freespace,caption"],
                    capture_output=True, text=True, check=True,
                )
                lines = result.stdout.strip().split("\n")[1:]
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            free = int(parts[1])
                            total = int(parts[2])
                            if total > 0 and (total - free) / total * 100 > 90:
                                logging.warning(f"Disk usage critical: {parts[0]}")
                                return False
                        except ValueError:
                            continue
            else:
                result = subprocess.run(
                    ["df", "-h"], capture_output=True, text=True, check=True
                )
                lines = result.stdout.split("\n")[1:]
                for line in lines:
                    if line and (fields := line.split()) and len(fields) >= 5:
                        if int(fields[4].rstrip("%")) > 90:
                            logging.warning(f"Disk usage critical: {fields[5]}")
                            return False
        except Exception as e:
            logging.error(f"Disk check failed: {e}")
            return False
        return True

    @staticmethod
    def check_health(docker_client: Optional[docker.DockerClient]) -> bool:
        if not docker_client:
            logging.error("No Docker client")
            return False
        try:
            docker_client.ping()
            return SystemHealthMonitor.check_disk_space()
        except Exception as e:
            logging.error(f"Health check failed: {e}")
            return False

# =============================================================================
# Utility Functions & Decorators
# =============================================================================
def error_handler(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {e}")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"error": str(e)}), 500
            return render_template("500.html", error=str(e)), 500
    return wrapped


def get_model_index(model_name: str) -> int:
    return next((i for i, m in enumerate(AI_MODELS) if m.name == model_name), 0)


def get_container_names(model: str, app_num: int) -> Tuple[str, str]:
    idx = get_model_index(model)
    ports = PortManager.get_app_ports(idx, app_num)
    base = model.lower()
    return (f"{base}_backend_{ports['backend']}", f"{base}_frontend_{ports['frontend']}")


def get_app_info(model_name: str, app_num: int) -> Dict[str, Any]:
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
    base_path = Path(model_name)
    if not base_path.exists():
        return []
    apps = []
    app_dirs = sorted(
        (d for d in base_path.iterdir() if d.is_dir() and d.name.startswith("app")),
        key=lambda x: int(x.name.replace("app", ""))
    )
    for app_dir in app_dirs:
        try:
            app_num = int(app_dir.name.replace("app", ""))
            apps.append(get_app_info(model_name, app_num))
        except ValueError as e:
            logger.error(f"Error processing {app_dir}: {e}")
    return apps


def get_all_apps() -> List[Dict[str, Any]]:
    return [app_info for model in AI_MODELS for app_info in get_apps_for_model(model.name)]


def run_docker_compose(
    command: List[str],
    model: str,
    app_num: int,
    timeout: int = 60,
    check: bool = True,
) -> Tuple[bool, str]:
    app_dir = Path(f"{model}/app{app_num}")
    if not app_dir.exists():
        logger.error(f"Directory not found: {app_dir}")
        return False, f"Directory not found: {app_dir}"
    
    # Check for compose file existence
    compose_file = app_dir / "docker-compose.yml"
    compose_yaml = app_dir / "docker-compose.yaml"
    if not compose_file.exists() and not compose_yaml.exists():
        logger.error(f"No docker-compose.yml/yaml file found in {app_dir}")
        return False, f"No docker-compose file found in {app_dir}"
    
    # Build the custom project name
    project_name = f"{model}_app{app_num}".lower()

    
    # Include the -p option to rename the compose stack
    cmd = ["docker-compose", "-p", project_name] + command
    logger.info(f"Running command: {' '.join(cmd)} in {app_dir} with timeout {timeout}s")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(app_dir),  # Ensure string path for compatibility
            check=check,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout or result.stderr
        success = result.returncode == 0
        
        if success:
            logger.info(f"Command succeeded: {' '.join(cmd)}")
        else:
            logger.error(f"Command failed with code {result.returncode}: {' '.join(cmd)}")
            logger.error(f"Error output: {output[:500]}")
        
        return success, output
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout}s: {' '.join(cmd)}")
        return False, f"Command timed out after {timeout}s"
    except Exception as e:
        logger.error(f"Error running {' '.join(cmd)}: {str(e)}")
        return False, str(e)

def handle_docker_action(action: str, model: str, app_num: int) -> Tuple[bool, str]:
    commands = {
        "start": [("up", "-d", 120)],
        "stop": [("down", None, 30)],
        "reload": [("restart", None, 90)],
        "rebuild": [("down", None, 30), ("build", None, 600), ("up", "-d", 120)],  # Increased build timeout
        "build": [("build", None, 600)],  # Increased build timeout
    }
    
    if action not in commands:
        logger.error(f"Invalid action: {action}")
        return False, f"Invalid action: {action}"
    
    logger.info(f"Starting {action} for {model}/app{app_num}")
    
    # Execute each command step
    for i, (base_cmd, extra_arg, timeout) in enumerate(commands[action]):
        cmd = [base_cmd] + ([extra_arg] if extra_arg else [])
        step_desc = f"Step {i+1}/{len(commands[action])}: {' '.join(cmd)}"
        logger.info(f"{step_desc} for {model}/app{app_num}")
        
        success, msg = run_docker_compose(cmd, model, app_num, timeout=timeout)
        
        if not success:
            error_msg = f"{action.capitalize()} failed during {base_cmd}: {msg}"
            logger.error(f"Docker {action} failed: {error_msg}")
            return False, error_msg
    
    logger.info(f"Successfully completed {action} for {model}/app{app_num}")
    return True, f"Successfully completed {action}"


def verify_container_health(
    docker_manager: DockerManager, model: str, app_num: int, max_retries: int = 10, retry_delay: int = 3
) -> Tuple[bool, str]:
    backend_name, frontend_name = get_container_names(model, app_num)
    for _ in range(max_retries):
        backend = docker_manager.get_container_status(backend_name)
        frontend = docker_manager.get_container_status(frontend_name)
        if backend.health == "healthy" and frontend.health == "healthy":
            return True, "All containers healthy"
        time.sleep(retry_delay)
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
    try:
        issues, tool_status, tool_output_details = analysis_method(
            model, app_num, use_all_tools=full_scan
        )
        summary = analyzer.get_analysis_summary(issues) if issues else analyzer.get_analysis_summary([])
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
        logger.warning(f"No files to analyze: {e}")
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
        logger.error(f"Security analysis failed: {e}")
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
    b_name, f_name = get_container_names(model, app_num)
    return {
        "backend": docker_manager.get_container_status(b_name).to_dict(),
        "frontend": docker_manager.get_container_status(f_name).to_dict(),
    }


def get_app_directory(app: Flask, model: str, app_num: int) -> Path:
    return app.config["BASE_DIR"] / f"{model}/app{app_num}"


def stop_zap_scanners(scans: Dict[str, Any]) -> None:
    for scan_key, scanner in scans.items():
        if hasattr(scanner, "stop_scan") and callable(scanner.stop_scan):
            try:
                model, app_num = scan_key.split("-")[:2]
                scanner.stop_scan(model=model, app_num=int(app_num))
            except Exception as e:
                logger.error(f"Error stopping scan for {scan_key}: {e}")
        else:
            logger.warning(
                f"Invalid scanner for key {scan_key}: expected a ZAPScanner instance but got {type(scanner)}"
            )

# =============================================================================
# ZAP Scanner Integration
# =============================================================================
class ScanManager:
    """Manages ZAP scans and their states."""
    def __init__(self):
        self.scans: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create_scan(self, model: str, app_num: int, options: dict) -> str:
        """Create a new scan entry."""
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
        return scan_id

    def get_scan(self, model: str, app_num: int) -> Optional[dict]:
        """Get the latest scan for a given model/app combination."""
        with self._lock:
            matching_scans = [
                (sid, scan) for sid, scan in self.scans.items()
                if sid.startswith(f"{model}-{app_num}-")
            ]
            if not matching_scans:
                return None
            return max(matching_scans, key=lambda x: x[0])[1]

    def update_scan(self, scan_id: str, **kwargs):
        """Update scan details."""
        with self._lock:
            if scan_id in self.scans:
                self.scans[scan_id].update(kwargs)

    def cleanup_old_scans(self):
        """Remove completed scans older than 1 hour."""
        current_time = time.time()
        with self._lock:
            self.scans = {
                sid: scan for sid, scan in self.scans.items()
                if scan["status"] not in ("Complete", "Failed", "Stopped") or
                current_time - int(sid.split("-")[-1]) < 3600
            }


def get_scan_manager():
    """Retrieve or initialize the scan manager."""
    if not hasattr(current_app, 'scan_manager'):
        current_app.scan_manager = ScanManager()
    return current_app.scan_manager

# =============================================================================
# Custom JSON Encoder
# =============================================================================
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return super().default(obj)

# =============================================================================
# Dummy AI Service Integration Function
# =============================================================================
def call_ai_service(model: str, prompt: str) -> str:
    # Replace with actual integration logic
    return "AI analysis result"

# =============================================================================
# Blueprints for Routes
# =============================================================================
main_bp = Blueprint("main", __name__)
api_bp = Blueprint("api", __name__)
analysis_bp = Blueprint("analysis", __name__)
performance_bp = Blueprint("performance", __name__)
gpt4all_bp = Blueprint("gpt4all", __name__)
zap_bp = Blueprint("zap", __name__)

# ----- Main Routes -----
@main_bp.route("/")
@error_handler
def index():
    docker_manager: DockerManager = current_app.config["docker_manager"]
    apps = get_all_apps()
    for app_info in apps:
        statuses = get_app_container_statuses(app_info["model"], app_info["app_num"], docker_manager)
        app_info["backend_status"] = statuses["backend"]
        app_info["frontend_status"] = statuses["frontend"]
    return render_template("index.html", apps=apps, models=AI_MODELS)

@main_bp.route("/docker-logs/<string:model>/<int:app_num>")
@error_handler
def view_docker_logs(model: str, app_num: int):
    """View Docker compose logs for debugging."""
    app_dir = Path(f"{model}/app{app_num}")
    if not app_dir.exists():
        flash(f"Directory not found: {app_dir}", "error")
        return redirect(url_for("main.index"))
    
    try:
        # Get docker-compose logs
        result = subprocess.run(
            ["docker-compose", "logs", "--no-color"],
            cwd=str(app_dir),
            capture_output=True,
            text=True,
            timeout=10
        )
        compose_logs = result.stdout or "No docker-compose logs available"
        
        # Get individual container logs
        b_name, f_name = get_container_names(model, app_num)
        docker_manager: DockerManager = current_app.config["docker_manager"]
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
        flash(f"Error fetching logs: {str(e)}", "error")
        return redirect(url_for("main.index"))

@main_bp.route("/status/<string:model>/<int:app_num>")
@error_handler
def check_app_status(model: str, app_num: int):
    docker_manager: DockerManager = current_app.config["docker_manager"]
    status = get_app_container_statuses(model, app_num, docker_manager)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(status)
    flash(f"Status checked for {model} App {app_num}", "info")
    return redirect(url_for("main.index"))

@main_bp.route("/batch/<action>/<string:model>", methods=["POST"])
@error_handler
def batch_docker_action(action: str, model: str):
    """
    Perform batch operations on all apps for a specific model.
    
    Args:
        action: The action to perform (start, stop, reload, rebuild)
        model: The model name to target
    
    Returns:
        JSON response with results
    """
    # Get all apps for the model
    apps = get_apps_for_model(model)
    if not apps:
        return jsonify({"status": "error", "message": f"No apps found for model {model}"}), 404
    
    # Validate the action
    valid_actions = ["start", "stop", "reload", "rebuild", "health-check"]
    if action not in valid_actions:
        return jsonify({"status": "error", "message": f"Invalid action: {action}"}), 400
    
    # Process all apps
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
            logger.error(f"Error during batch {action} for {model} app {app_num}: {e}")
            results.append({
                "app_num": app_num,
                "success": False,
                "message": str(e)
            })
    
    # Summarize results
    success_count = sum(1 for r in results if r["success"])
    
    return jsonify({
        "status": "success" if success_count == len(results) else "partial" if success_count > 0 else "error",
        "total": len(results),
        "success_count": success_count,
        "failure_count": len(results) - success_count,
        "results": results
    })

@main_bp.route("/logs/<string:model>/<int:app_num>")
@error_handler
def view_logs(model: str, app_num: int):
    docker_manager: DockerManager = current_app.config["docker_manager"]
    b_name, f_name = get_container_names(model, app_num)
    logs_data = {
        "backend": docker_manager.get_container_logs(b_name),
        "frontend": docker_manager.get_container_logs(f_name),
    }
    return render_template("logs.html", logs=logs_data, model=model, app_num=app_num)


@main_bp.route("/<action>/<string:model>/<int:app_num>")
@error_handler
def handle_docker_action_route(action: str, model: str, app_num: int):
    success, message = handle_docker_action(action, model, app_num)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        status_code = 200 if success else 500
        return jsonify({"status": "success" if success else "error", "message": message}), status_code
    flash(f"{'Success' if success else 'Error'}: {message}", "success" if success else "error")
    return redirect(url_for("main.index"))

# ----- API Routes -----
@api_bp.route("/container/<string:model>/<int:app_num>/status")
@error_handler
def container_status(model: str, app_num: int):
    docker_manager: DockerManager = current_app.config["docker_manager"]
    status = get_app_container_statuses(model, app_num, docker_manager)
    return jsonify(status)

@api_bp.route("/debug/docker/<string:model>/<int:app_num>")
@error_handler
def debug_docker_environment(model: str, app_num: int):
    """Debug endpoint to inspect docker environment for an app."""
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
            compose_content = compose_file.read_text(errors='replace')[:500] + "..."
        elif compose_yaml.exists():
            compose_content = compose_yaml.read_text(errors='replace')[:500] + "..."
        
        # Check docker installation
        docker_version = subprocess.run(
            ["docker", "--version"], 
            capture_output=True, 
            text=True
        ).stdout.strip()
        
        # Check docker-compose installation
        try:
            docker_compose_version = subprocess.run(
                ["docker-compose", "--version"], 
                capture_output=True, 
                text=True
            ).stdout.strip()
        except:
            docker_compose_version = "Not available or error"
        
        # Get list of running containers related to this app
        b_name, f_name = get_container_names(model, app_num)
        container_info = []
        
        docker_manager: DockerManager = current_app.config["docker_manager"]
        backend_status = docker_manager.get_container_status(b_name)
        frontend_status = docker_manager.get_container_status(f_name)
        
        return jsonify({
            "directory_exists": dir_exists,
            "compose_file_exists": compose_file_exists,
            "compose_file_preview": compose_content,
            "docker_version": docker_version,
            "docker_compose_version": docker_compose_version,
            "backend_container": backend_status.to_dict(),
            "frontend_container": frontend_status.to_dict(),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route("/health/<string:model>/<int:app_num>")
@error_handler
def check_container_health(model: str, app_num: int):
    docker_manager: DockerManager = current_app.config["docker_manager"]
    healthy, message = verify_container_health(docker_manager, model, app_num)
    return jsonify({"healthy": healthy, "message": message})


@api_bp.route("/status")
@error_handler
def system_status():
    docker_manager: DockerManager = current_app.config["docker_manager"]
    disk_ok = SystemHealthMonitor.check_disk_space()
    docker_ok = SystemHealthMonitor.check_health(docker_manager.client)
    return jsonify({
        "status": "healthy" if (disk_ok and docker_ok) else "warning",
        "details": {"disk_space": disk_ok, "docker_health": docker_ok},
    })


@api_bp.route("/model-info")
@error_handler
def get_model_info():
    return jsonify([
        {
            "name": model.name,
            "color": model.color,
            "ports": PortManager.get_port_range(idx),
            "total_apps": len(get_apps_for_model(model.name)),
        }
        for idx, model in enumerate(AI_MODELS)
    ])

# ----- Client-side Error Logging Endpoint -----
@api_bp.route("/log-client-error", methods=["POST"])
@error_handler
def log_client_error():
    """
    Endpoint to log client-side errors that might be causing
    undefined route requests.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No error data provided"}), 400
            
        # Log the client error with detailed context
        logger.error(
            f"CLIENT ERROR: {data.get('message')} | "
            f"URL: {data.get('url')} | "
            f"File: {data.get('filename')}:{data.get('lineno')}:{data.get('colno')} | "
            f"User-Agent: {data.get('userAgent')}"
        )
        
        # Log stack trace at debug level
        if 'stack' in data:
            logger.debug(f"Error stack trace: {data.get('stack')}")
            
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Error in client error logger: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ----- ZAP Routes -----
@zap_bp.route("/<string:model>/<int:app_num>")
@error_handler
def zap_scan(model: str, app_num: int):
    base_dir: Path = current_app.config["BASE_DIR"]
    results_file = base_dir / f"{model}/app{app_num}/.zap_results.json"
    alerts = []
    error_msg = None
    if results_file.exists():
        try:
            with open(results_file) as f:
                data = json.load(f)
                alerts = data.get("alerts", [])
        except Exception as e:
            error_msg = f"Failed to load previous results: {e}"
            logger.error(error_msg)
    return render_template("zap_scan.html", model=model, app_num=app_num, alerts=alerts, error=error_msg)


@zap_bp.route("/scan/<string:model>/<int:app_num>", methods=["POST"])
@error_handler
def start_zap_scan(model: str, app_num: int):
    data = request.get_json()
    base_dir: Path = current_app.config["BASE_DIR"]
    scan_manager = get_scan_manager()
    existing_scan = scan_manager.get_scan(model, app_num)
    if existing_scan and existing_scan["status"] not in ("Complete", "Failed", "Stopped"):
        return jsonify({"error": "A scan is already running"}), 409
    scan_id = scan_manager.create_scan(model, app_num, data)
    def run_scan():
        try:
            scanner = create_scanner(base_dir)
            scan_manager.update_scan(scan_id, scanner=scanner)
            frontend_port = 5501 + ((app_num - 1) * 2)
            target_url = f"http://localhost:{frontend_port}"
            vulnerabilities, summary = scanner.scan_target(target_url, scan_policy=data.get("scanPolicy"))
            results_file = base_dir / f"{model}/app{app_num}/.zap_results.json"
            results_file.parent.mkdir(parents=True, exist_ok=True)
            with open(results_file, "w") as f:
                json.dump({
                    "alerts": [asdict(v) for v in vulnerabilities],
                    "summary": summary,
                    "scan_time": datetime.now().isoformat(),
                }, f, indent=2)
            scan_manager.update_scan(scan_id, status="Complete", progress=100)
        except Exception as e:
            logger.error(f"Scan error: {e}")
            scan_manager.update_scan(scan_id, status=f"Failed: {e}", progress=0)
        finally:
            scanner._cleanup_existing_zap()
            scan_manager.cleanup_old_scans()
    threading.Thread(target=run_scan, daemon=True).start()
    return jsonify({"status": "started", "scan_id": scan_id})


@zap_bp.route("/scan/<string:model>/<int:app_num>/status")
@error_handler
def zap_scan_status(model: str, app_num: int):
    scan_manager = get_scan_manager()
    scan = scan_manager.get_scan(model, app_num)
    if not scan:
        return jsonify({"status": "Not Started", "progress": 0})
    results_file = current_app.config["BASE_DIR"] / f"{model}/app{app_num}/.zap_results.json"
    counts = {"high": 0, "medium": 0, "low": 0, "info": 0}
    if results_file.exists():
        try:
            with open(results_file) as f:
                data = json.load(f)
                for alert in data.get("alerts", []):
                    risk = alert.get("risk", "").lower()
                    if risk in counts:
                        counts[risk] += 1
        except Exception as e:
            logger.error(f"Error reading results file: {e}")
    return jsonify({
        "status": scan["status"],
        "progress": scan["progress"],
        "high_count": counts["high"],
        "medium_count": counts["medium"],
        "low_count": counts["low"],
        "info_count": counts["info"],
    })


@zap_bp.route("/scan/<string:model>/<int:app_num>/stop", methods=["POST"])
@error_handler
def stop_zap_scan(model: str, app_num: int):
    scan_manager = get_scan_manager()
    scan = scan_manager.get_scan(model, app_num)
    if not scan:
        return jsonify({"error": "No running scan found"}), 404
    if scan["status"] in ("Complete", "Failed", "Stopped"):
        return jsonify({"error": "Scan is not running"}), 400
    try:
        if scan["scanner"]:
            scan["scanner"]._cleanup_existing_zap()
        scan_manager.update_scan(next(sid for sid, s in scan_manager.scans.items() if s == scan),
                                 status="Stopped", progress=0)
        return jsonify({"status": "stopped"})
    except Exception as e:
        logger.error(f"Failed to stop scan: {e}")
        return jsonify({"error": str(e)}), 500

# ----- Analysis Routes -----
@analysis_bp.route("/backend-security/<string:model>/<int:app_num>")
@error_handler
def security_analysis(model: str, app_num: int):
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
@error_handler
def frontend_security_analysis(model: str, app_num: int):
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
@error_handler
def analyze_security_issues():
    try:
        data = request.get_json()
        if not data or "issues" not in data:
            raise BadRequest("No issues provided for analysis")
        model = data.get("model", "default-model")
        issues = data["issues"]
        severity_groups = {"HIGH": [], "MEDIUM": [], "LOW": []}
        for issue in issues:
            severity = issue.get("severity", "LOW").upper()
            severity_groups.setdefault(severity, []).append(issue)
        prompt = "Analyze the following security issues:\n\n"
        for level in ["HIGH", "MEDIUM", "LOW"]:
            if severity_groups.get(level):
                prompt += f"\n{level} Severity Issues:\n"
                for issue in severity_groups[level]:
                    prompt += f"- {issue['type']}: {issue['text']}\n"
                    if issue.get('code'):
                        prompt += f"  Code: {issue['code']}\n"
        prompt += (
            "\nPlease provide:\n"
            "1. A high-level summary of the security concerns\n"
            "2. Prioritized recommendations\n"
            "3. Potential security implications if unaddressed\n"
            "4. Best practices to prevent future issues"
        )
        analysis_result = call_ai_service(model, prompt)
        return jsonify({"status": "success", "response": analysis_result})
    except BadRequest as e:
        logger.warning(f"Bad request in security analysis: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error in security analysis: {e}")
        return jsonify({"error": "Analysis failed"}), 500


@analysis_bp.route("/security/summary/<string:model>/<int:app_num>")
@error_handler
def get_security_summary(model: str, app_num: int):
    try:
        backend_issues, backend_status, _ = current_app.backend_security_analyzer.analyze_security(
            model, app_num, use_all_tools=False
        )
        backend_summary = current_app.backend_security_analyzer.get_analysis_summary(backend_issues)
        frontend_issues, frontend_status, _ = current_app.frontend_security_analyzer.run_security_analysis(
            model, app_num, use_all_tools=False
        )
        frontend_summary = current_app.frontend_security_analyzer.get_analysis_summary(frontend_issues)
        combined_summary = {
            "backend": {"summary": backend_summary, "status": backend_status},
            "frontend": {"summary": frontend_summary, "status": frontend_status},
            "total_issues": backend_summary["total_issues"] + frontend_summary["total_issues"],
            "severity_counts": {
                "HIGH": backend_summary["severity_counts"]["HIGH"] + frontend_summary["severity_counts"]["HIGH"],
                "MEDIUM": backend_summary["severity_counts"]["MEDIUM"] + frontend_summary["severity_counts"]["MEDIUM"],
                "LOW": backend_summary["severity_counts"]["LOW"] + frontend_summary["severity_counts"]["LOW"],
            },
            "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        return jsonify(combined_summary)
    except Exception as e:
        logger.error(f"Error getting security summary: {e}")
        return jsonify({"error": "Failed to get security summary", "details": str(e)}), 500


@analysis_bp.route("/security/analyze-file", methods=["POST"])
@error_handler
def analyze_single_file():
    try:
        data = request.get_json()
        if not data or "file_path" not in data:
            raise BadRequest("No file path provided")
        file_path = Path(data["file_path"])
        is_frontend = data.get("is_frontend", False)
        analyzer = current_app.frontend_security_analyzer if is_frontend else current_app.backend_security_analyzer
        if is_frontend:
            issues, tool_status, tool_output = analyzer._run_eslint(file_path.parent)
        else:
            issues, tool_status, tool_output = analyzer._run_bandit(file_path.parent)
        file_issues = [issue for issue in issues if Path(issue.filename).name == file_path.name]
        return jsonify({
            "status": "success",
            "issues": [asdict(issue) for issue in file_issues],
            "tool_status": tool_status,
            "tool_output": tool_output,
        })
    except BadRequest as e:
        logger.warning(f"Bad request in file analysis: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error analyzing file: {e}")
        return jsonify({"error": "File analysis failed"}), 500

# ----- Performance Testing Routes -----
@performance_bp.route("/<string:model>/<int:port>", methods=["GET", "POST"])
@error_handler
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
    tester = PerformanceTester(current_app.config["BASE_DIR"])
    
    if request.method == "POST":
        try:
            data = request.get_json()
            num_users = int(data.get("num_users", 10))
            duration = int(data.get("duration", 30))
            spawn_rate = int(data.get("spawn_rate", 1))
            endpoints = data.get("endpoints", ["/"])
            
            result, info = tester.run_test(
                model=model,
                port=port,
                num_users=num_users,
                duration=duration,
                spawn_rate=spawn_rate,
                endpoints=endpoints
            )
            
            if result:
                # Convert the result object to a dictionary for JSON serialization
                return jsonify({
                    "status": "success",
                    "data": result.to_dict(),
                    "report_path": info.get("report_path", "")
                })
            else:
                return jsonify({
                    "status": "error", 
                    "error": info.get("error", "Unknown error"),
                    "command": info.get("command", "")
                }), 500
        except Exception as e:
            logger.exception(f"Performance test error: {e}")
            return jsonify({"status": "error", "error": str(e)}), 500
    
    return render_template("performance_test.html", model=model, port=port)


@performance_bp.route("/<string:model>/<int:port>/stop", methods=["POST"])
@error_handler
def stop_performance_test(model: str, port: int):
    """Stop a running performance test."""
    try:
        # For now, we'll just return success
        return jsonify({"status": "success", "message": "Test stopped successfully"})
    except Exception as e:
        logger.exception(f"Error stopping performance test: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500


@performance_bp.route("/<string:model>/<int:port>/reports", methods=["GET"])
@error_handler
def list_performance_reports(model: str, port: int):
    """List available performance reports for a specific model/port."""
    try:
        report_dir = current_app.config["BASE_DIR"] / "performance_reports"
        if not report_dir.exists():
            return jsonify({"reports": []})
            
        # Find all reports for this model/port
        reports = []
        for report_file in report_dir.glob(f"report_{model}_{port}_*.html"):
            timestamp = report_file.stem.split("_")[-1]
            reports.append({
                "filename": report_file.name,
                "path": f"/static/performance_reports/{report_file.name}",
                "timestamp": timestamp,
                "created": datetime.fromtimestamp(report_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
            
        return jsonify({"reports": sorted(reports, key=lambda x: x["timestamp"], reverse=True)})
    except Exception as e:
        logger.exception(f"Error listing performance reports: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500


@performance_bp.route("/<string:model>/<int:port>/reports/<path:report_name>", methods=["GET"])
@error_handler
def view_performance_report(model: str, port: int, report_name: str):
    """View a specific performance report."""
    try:
        report_path = current_app.config["BASE_DIR"] / "performance_reports" / report_name
        if not report_path.exists():
            return render_template("404.html"), 404
            
        # For security, verify this is a report for the requested model/port
        if not report_name.startswith(f"report_{model}_{port}_"):
            return render_template("404.html"), 404
            
        with open(report_path, "r") as f:
            report_content = f.read()
            
        return render_template(
            "performance_report_viewer.html", 
            model=model, 
            port=port, 
            report_name=report_name,
            report_content=report_content
        )
    except Exception as e:
        logger.exception(f"Error viewing performance report: {e}")
        return render_template("500.html", error=str(e)), 500

# ----- GPT4All Routes -----
@gpt4all_bp.route("/analyze-gpt4all/<string:analysis_type>", methods=["POST"])
@error_handler
def analyze_gpt4all(analysis_type: str):
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
            summary = get_analysis_summary(issues)
        return jsonify({"issues": [asdict(issue) for issue in issues], "summary": summary})
    except Exception as e:
        logger.error(f"GPT4All analysis failed: {e}")
        return jsonify({"error": str(e)}), 500

@gpt4all_bp.route("/gpt4all-analysis", methods=["GET", "POST"])
@error_handler
def gpt4all_analysis():
    """Flask route for checking requirements against code."""
    try:
        # Extract parameters
        model = request.args.get("model") or request.form.get("model")
        app_num = request.args.get("app_num") or request.form.get("app_num")
        
        # Validate required parameters
        if not model or not app_num:
            return render_template(
                "requirements_check.html",
                model=None,
                app_num=None,
                requirements=[],
                results=None,
                error="Model and app number are required"
            )
            
        # Find the application directory
        directory = get_app_directory(current_app, model, app_num)
        if not directory.exists():
            return render_template(
                "requirements_check.html",
                model=model,
                app_num=app_num,
                requirements=[],
                results=None,
                error=f"Directory not found: {directory}"
            )
        
        # Setup for requirements analysis
        req_list = []
        results = None
        
        # Handle requirements from POST
        if request.method == "POST" and "requirements" in request.form:
            requirements_text = request.form.get("requirements", "")
            req_list = [r.strip() for r in requirements_text.strip().splitlines() if r.strip()]
            
            if req_list:
                # Initialize analyzer
                analyzer = GPT4AllAnalyzer(directory)
                
                # Run check for each requirement using proper asyncio handling in Flask
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(analyzer.check_requirements(directory, req_list))
                loop.close()
        
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
    @app.errorhandler(404)
    def not_found(error):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"error": "Not found"}), 404
        return render_template("404.html", error=error), 404

    @app.errorhandler(500)
    def server_error(error):
        logger.error(f"Server error: {error}")
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"error": "Internal server error"}), 500
        return render_template("500.html", error=error), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.error(f"Unhandled exception: {error}")
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"error": str(error)}), 500
        return render_template("500.html", error=error), 500


def register_request_hooks(app: Flask, docker_manager: DockerManager) -> None:
    @app.before_request
    def before():
        if random.random() < 0.01:
            docker_manager.cleanup_containers()
            if "ZAP_SCANS" in app.config:
                stop_zap_scanners(app.config["ZAP_SCANS"])

    @app.after_request
    def after(response):
        response.headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        })
        return response

    @app.teardown_appcontext
    def teardown(exception=None):
        if "ZAP_SCANS" in app.config:
            stop_zap_scanners(app.config["ZAP_SCANS"])

# =============================================================================
# Flask App Factory
# =============================================================================
def create_app(config: Optional[AppConfig] = None) -> Flask:
    app = Flask(__name__)
    app_config = config or AppConfig.from_env()
    app.config.from_object(app_config)
    app.config["BASE_DIR"] = app_config.BASE_DIR
    
    # Configure enhanced logging
    LoggingService.configure(app_config.LOG_LEVEL)
    
    # Apply request logger middleware
    RequestLoggerMiddleware(app)
    
    app.json_encoder = CustomJSONEncoder

    base_path = app_config.BASE_DIR.parent
    logger.info(f"Initializing analyzers with base path: {base_path}")

    # Initialize analyzers and other services.
    app.backend_security_analyzer = BackendSecurityAnalyzer(base_path)
    app.frontend_security_analyzer = FrontendSecurityAnalyzer(base_path)
    app.gpt4all_analyzer = GPT4AllAnalyzer(base_path)
    app.performance_tester = PerformanceTester(base_path)
    app.zap_scanner = create_scanner(app_config.BASE_DIR)

    docker_manager = DockerManager()
    app.config["docker_manager"] = docker_manager

    app.wsgi_app = ProxyFix(app.wsgi_app)

    # Register blueprints.
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(analysis_bp)
    app.register_blueprint(performance_bp, url_prefix="/performance")
    app.register_blueprint(gpt4all_bp)  # This registers both the original and new routes
    app.register_blueprint(zap_bp, url_prefix="/zap")

    # Initialize batch analysis module
    init_batch_analysis(app)
    # Register batch analysis blueprint
    app.register_blueprint(batch_analysis_bp, url_prefix="/batch-analysis")

    register_error_handlers(app)
    register_request_hooks(app, docker_manager)
    
    logger.info("Application initialization complete")
    return app

# =============================================================================
# Main Entry Point
# =============================================================================
if __name__ == "__main__":
    config = AppConfig.from_env()
    LoggingService.configure(config.LOG_LEVEL)
    try:
        app = create_app(config)
        docker_manager = DockerManager()
        if docker_manager.client and not SystemHealthMonitor.check_health(docker_manager.client):
            logger.warning("System health check failed - reduced functionality expected.")
        elif not docker_manager.client:
            logger.warning("Docker client unavailable - reduced functionality expected.")
        app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
    except Exception as e:
        logger.critical(f"Failed to start: {e}")
        raise e

# =============================================================================
# Optional: Database Manager for Storing Scan Data
# =============================================================================
class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect("your_database.db")
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS security_scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_type TEXT NOT NULL,
                model TEXT NOT NULL,
                app_num INTEGER NOT NULL,
                issues TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')