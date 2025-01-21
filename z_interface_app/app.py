"""
app.py - Refactored Flask-based AI Model Management System
A Flask application that:
- Manages Docker-based frontend/backend apps
- Uses the Python Docker library for container operations
- Handles both synchronous and asynchronous workflows
"""

import asyncio
import logging
import os
import queue
import random
import subprocess
import threading
import time
from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import docker
from docker.errors import DockerException, NotFound
from docker.models.containers import Container
from flask import (
    Flask,
    Response,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.middleware.proxy_fix import ProxyFix


# -------------------------
# Configuration
# -------------------------
@dataclass
class AppConfig:
    """Holds core Flask and service configurations."""
    DEBUG: bool
    SECRET_KEY: str
    BASE_DIR: Path
    LOG_LEVEL: str
    DOCKER_TIMEOUT: int
    CACHE_DURATION: int
    HOST: str
    PORT: int

    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Create configuration from environment variables with defaults."""
        return cls(
            DEBUG=True,  # or use os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
            SECRET_KEY=os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here'),
            BASE_DIR=Path(__file__).parent,
            LOG_LEVEL=os.getenv('LOG_LEVEL', 'ERROR'),
            DOCKER_TIMEOUT=int(os.getenv('DOCKER_TIMEOUT', '10')),
            CACHE_DURATION=int(os.getenv('CACHE_DURATION', '5')),
            HOST='0.0.0.0' if os.getenv('FLASK_ENV') == 'production' else '127.0.0.1',
            PORT=int(os.getenv('PORT', '5000'))
        )


# -------------------------
# Domain Models
# -------------------------
@dataclass
class AIModel:
    """Metadata for an AI model."""
    name: str
    color: str


@dataclass
class DockerStatus:
    """Stores container status information."""
    exists: bool = False
    running: bool = False
    health: str = "unknown"
    status: str = "unknown"
    details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exists": self.exists,
            "running": self.running,
            "health": self.health,
            "status": self.status,
            "details": self.details,
        }


# -------------------------
# Constants
# -------------------------
AI_MODELS = [
    AIModel("ChatGPT", "#10a37f"),
    AIModel("ChatGPTo1", "#0ea47f"),
    AIModel("ClaudeSonnet", "#7b2bf9"),
    AIModel("CodeLlama", "#f97316"),
    AIModel("Gemini", "#1a73e8"),
    AIModel("Grok", "#ff4d4f"),
    AIModel("Mixtral", "#9333ea"),
]


# -------------------------
# Logging & Filtering
# -------------------------
class LoggingService:
    """Central logging setup."""

    @staticmethod
    def configure(log_level: str) -> None:
        logging.basicConfig(
            level=getattr(logging, log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        logging.getLogger("werkzeug").addFilter(StatusEndpointFilter())


class StatusEndpointFilter(logging.Filter):
    """Filters out noisy 'status endpoint' logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "args") or len(record.args) < 3:
            return True
        msg = record.args[2] if isinstance(record.args[2], str) else ""
        return not ("GET /api/container/" in msg and msg.endswith(' HTTP/1.1" 200 -'))


# -------------------------
# Port Management
# -------------------------
class PortManager:
    """Calculates port ranges for each model/app pairing."""

    BASE_BACKEND_PORT = 5001
    BASE_FRONTEND_PORT = 5501
    PORTS_PER_APP = 2
    BUFFER_PORTS = 5
    APPS_PER_MODEL = 20

    @classmethod
    def get_port_range(cls, model_idx: int) -> Dict[str, Dict[str, int]]:
        """Compute start/end ports for a model's backend/frontends."""
        total_needed = cls.APPS_PER_MODEL * cls.PORTS_PER_APP + cls.BUFFER_PORTS
        return {
            "backend": {
                "start": cls.BASE_BACKEND_PORT + (model_idx * total_needed),
                "end": cls.BASE_BACKEND_PORT
                + ((model_idx + 1) * total_needed)
                - cls.BUFFER_PORTS,
            },
            "frontend": {
                "start": cls.BASE_FRONTEND_PORT + (model_idx * total_needed),
                "end": cls.BASE_FRONTEND_PORT
                + ((model_idx + 1) * total_needed)
                - cls.BUFFER_PORTS,
            },
        }

    @classmethod
    def get_app_ports(cls, model_idx: int, app_num: int) -> Dict[str, int]:
        """Return specific ports for a given model's app instance."""
        rng = cls.get_port_range(model_idx)
        return {
            "backend": rng["backend"]["start"] + (app_num - 1) * 2,
            "frontend": rng["frontend"]["start"] + (app_num - 1) * 2,
        }


# -------------------------
# Docker Management
# -------------------------
class DockerManager:
    """Handles Docker operations with caching and error handling."""

    def __init__(self, client: Optional[docker.DockerClient] = None) -> None:
        self.logger = logging.getLogger(__name__)
        self.client = client or self._create_docker_client()
        self._cache: Dict[str, Tuple[float, DockerStatus]] = {}
        self._cache_duration = AppConfig.from_env().CACHE_DURATION
        self._lock = asyncio.Lock()

    def _create_docker_client(self) -> Optional[docker.DockerClient]:
        try:
            docker_host = os.getenv("DOCKER_HOST", "npipe:////./pipe/docker_engine")
            return docker.DockerClient(
                base_url=docker_host, timeout=AppConfig.from_env().DOCKER_TIMEOUT
            )
        except DockerException as e:
            self.logger.error(f"Failed to create Docker client: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error creating Docker client: {e}")
        return None

    def get_container_status(self, container_name: str) -> DockerStatus:
        """Return container status (with caching)."""
        now = time.time()
        if container_name in self._cache:
            timestamp, status = self._cache[container_name]
            if now - timestamp < self._cache_duration:
                return status

        fresh_status = self._fetch_container_status(container_name)
        self._cache[container_name] = (now, fresh_status)
        return fresh_status

    def _fetch_container_status(self, container_name: str) -> DockerStatus:
        if not self.client:
            return DockerStatus(
                exists=False,
                status="error",
                health="error",
                details="Docker client not available",
            )
        try:
            container = self.client.containers.get(container_name)
            is_running = container.status == "running"
            health = (
                container.attrs["State"]["Health"]["Status"]
                if "Health" in container.attrs["State"]
                else ("healthy" if is_running else "stopped")
            )
            return DockerStatus(
                exists=True,
                running=is_running,
                health=health,
                status=container.status,
                details=container.attrs["State"]["Status"],
            )
        except NotFound:
            return DockerStatus(
                exists=False,
                status="no_container",
                health="not_found",
                details="Container does not exist",
            )
        except DockerException as e:
            self.logger.error(f"Docker error for {container_name}: {e}")
            return DockerStatus(
                exists=False, status="error", health="error", details=str(e)
            )

    def get_container_logs(self, container_name: str, tail: int = 100) -> str:
        if not self.client:
            return "Docker client not available"
        try:
            container = self.client.containers.get(container_name)
            return container.logs(tail=tail).decode("utf-8")
        except Exception as e:
            self.logger.error(f"Error getting logs for {container_name}: {e}")
            return f"Error retrieving logs: {e}"

    def cleanup_containers(self) -> None:
        """Remove stopped containers older than 24h."""
        if not self.client:
            return
        try:
            self.client.containers.prune(filters={"until": "24h"})
        except DockerException as e:
            self.logger.error(f"Container cleanup failed: {e}")


# -------------------------
# Health Monitoring
# -------------------------
class SystemHealthMonitor:
    """Checks system resources and Docker connectivity."""

    @staticmethod
    def check_disk_space() -> bool:
        """Return True if disk usage is below critical thresholds."""
        try:
            if os.name == "nt":  # Windows
                df = subprocess.run(
                    ["wmic", "logicaldisk", "get", "size,freespace,caption"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                lines = df.stdout.strip().split("\n")[1:]
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            free_space = int(parts[1])
                            total_size = int(parts[2])
                            if total_size > 0:
                                used_pct = (total_size - free_space) / total_size * 100
                                if used_pct > 90:
                                    logging.warning(
                                        f"Critical disk usage: {parts[0]} at {used_pct:.1f}%"
                                    )
                                    return False
                        except ValueError:
                            continue
            else:  # Unix/Linux
                df = subprocess.run(["df", "-h"], capture_output=True, text=True, check=True)
                for line in df.stdout.split("\n")[1:]:
                    if line:
                        fields = line.split()
                        if len(fields) >= 5:
                            usage = int(fields[4].rstrip("%"))
                            if usage > 90:
                                logging.warning(f"Critical disk usage: {fields[5]} at {usage}%")
                                return False
        except subprocess.CalledProcessError as e:
            logging.error(f"Disk space check failed: {e}")
            return False
        return True

    @staticmethod
    def check_health(docker_client: Optional[docker.DockerClient]) -> bool:
        """Ping Docker and check disk space."""
        if not docker_client:
            logging.error("No Docker client available.")
            return False
        try:
            docker_client.ping()
            return SystemHealthMonitor.check_disk_space()
        except Exception as e:
            logging.error(f"Health check failed: {e}")
            return False


# -------------------------
# Utility & Decorators
# -------------------------
def error_handler(f):
    """Decorator to standardize error handling in routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs) -> Union[Response, Tuple[Response, int]]:
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error in {f.__name__}: {e}")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"error": str(e)}), 500
            return render_template("500.html"), 500
    return decorated_function


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
    base_path = Path(f"{model_name}/flask_apps")
    if not base_path.exists():
        return []
    apps = []
    app_dirs = sorted(
        (d for d in base_path.iterdir() if d.is_dir() and d.name.startswith("app")),
        key=lambda x: int(x.name.replace("app", "")),
    )
    for app_dir in app_dirs:
        try:
            app_num = int(app_dir.name.replace("app", ""))
            apps.append(get_app_info(model_name, app_num))
        except ValueError as e:
            logging.error(f"Error processing {app_dir}: {e}")
    return apps


def get_all_apps() -> List[Dict[str, Any]]:
    return [app for model in AI_MODELS for app in get_apps_for_model(model.name)]


def run_docker_compose_with_timeout(
    command: List[str],
    model: str,
    app_num: int,
    timeout: int = 60,
    check: bool = True
) -> Tuple[bool, str]:
    """Run a docker-compose command in a separate thread with a timeout."""
    app_dir = Path(f"{model}/flask_apps/app{app_num}")
    if not app_dir.exists():
        return False, f"Directory not found: {app_dir}"

    output_queue = queue.Queue()

    def target_func():
        try:
            result = subprocess.run(
                ["docker-compose"] + command,
                cwd=app_dir,
                check=check,
                capture_output=True,
                text=True,
            )
            output_queue.put((result.returncode == 0, result.stdout or result.stderr))
        except subprocess.CalledProcessError as e:
            output_queue.put((False, f"Command failed: {e.stderr}"))
        except Exception as ex:
            output_queue.put((False, f"Error: {ex}"))

    thread = threading.Thread(target=target_func)
    thread.daemon = True
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        return False, f"Command timed out after {timeout} seconds"

    try:
        return output_queue.get_nowait()
    except queue.Empty:
        return False, "No output received from command"


def handle_docker_action(action: str, model: str, app_num: int) -> Tuple[bool, str]:
    """High-level docker-compose action handler."""
    commands = {
        "start": [("up", "-d", 120)],
        "stop": [("stop", None, 30)],
        "reload": [("restart", None, 90)],
        "rebuild": [
            ("down", None, 30),
            ("build", None, 300),
            ("up", "-d", 120),
        ],
        "build": [("build", None, 300)],
    }
    if action not in commands:
        return False, f"Invalid action: {action}"

    for cmd_tuple in commands[action]:
        base_cmd, extra_arg, cmd_timeout = cmd_tuple
        cmd = [base_cmd] + ([extra_arg] if extra_arg else [])
        success, msg = run_docker_compose_with_timeout(cmd, model, app_num, timeout=cmd_timeout)
        if not success:
            logging.error(f"Docker action '{action}' failed on {cmd}: {msg}")
            return False, msg
    return True, f"Successfully completed {action} action"


def verify_container_health(
    docker_manager: DockerManager, model: str, app_num: int, max_retries: int = 10, retry_delay: int = 3
) -> Tuple[bool, str]:
    """Verify container health with retry logic."""
    backend_name, frontend_name = get_container_names(model, app_num)
    for _ in range(max_retries):
        backend_status = docker_manager.get_container_status(backend_name)
        frontend_status = docker_manager.get_container_status(frontend_name)
        if backend_status.health == "healthy" and frontend_status.health == "healthy":
            return True, "All containers healthy"
        time.sleep(retry_delay)
    return False, "Containers failed to reach healthy state"


# -------------------------
# Flask App Factory
# -------------------------
def create_app(config: Optional[AppConfig] = None) -> Flask:
    """Initialize and configure the Flask application."""
    app = Flask(__name__)
    config = config or AppConfig.from_env()
    app.config.from_object(config)
    LoggingService.configure(config.LOG_LEVEL)

    docker_manager = DockerManager()
    app.wsgi_app = ProxyFix(app.wsgi_app)
    register_routes(app, docker_manager)
    register_error_handlers(app)
    register_request_hooks(app, docker_manager)
    return app


# -------------------------
# Route Registration
# -------------------------
def register_routes(app: Flask, docker_manager: DockerManager) -> None:
    @app.route("/")
    @error_handler
    def index() -> str:
        """Home page showing apps and statuses."""
        apps = get_all_apps()
        for app_info in apps:
            b_name, f_name = get_container_names(app_info["model"], app_info["app_num"])
            app_info["backend_status"] = docker_manager.get_container_status(b_name)
            app_info["frontend_status"] = docker_manager.get_container_status(f_name)
        return render_template("index.html", apps=apps, models=AI_MODELS)

    @app.route("/api/container/<string:model>/<int:app_num>/status")
    @error_handler
    def container_status(model: str, app_num: int) -> Response:
        """API endpoint for container status."""
        b_name, f_name = get_container_names(model, app_num)
        return jsonify(
            {
                "backend": docker_manager.get_container_status(b_name).to_dict(),
                "frontend": docker_manager.get_container_status(f_name).to_dict(),
            }
        )

    @app.route("/logs/<string:model>/<int:app_num>")
    @error_handler
    def view_logs(model: str, app_num: int) -> str:
        """View logs for both containers."""
        b_name, f_name = get_container_names(model, app_num)
        logs = {
            "backend": docker_manager.get_container_logs(b_name),
            "frontend": docker_manager.get_container_logs(f_name),
        }
        return render_template("logs.html", logs=logs, model=model, app_num=app_num)

    @app.route("/api/status")
    @error_handler
    def system_status() -> Response:
        """Check overall system status."""
        disk_ok = SystemHealthMonitor.check_disk_space()
        docker_ok = SystemHealthMonitor.check_health(docker_manager.client)
        status = "healthy" if (disk_ok and docker_ok) else "warning"
        return jsonify({"status": status, "details": {"disk_space": disk_ok, "docker_health": docker_ok}})

    @app.route("/api/model-info")
    @error_handler
    def get_model_info() -> Response:
        """Get port ranges and metadata for all models."""
        info = []
        for idx, model in enumerate(AI_MODELS):
            info.append({
                "name": model.name,
                "color": model.color,
                "ports": PortManager.get_port_range(idx),
                "total_apps": len(get_apps_for_model(model.name)),
            })
        return jsonify(info)

    @app.route("/<action>/<string:model>/<int:app_num>")
    @error_handler
    def handle_docker_action_route(action: str, model: str, app_num: int) -> Union[Response, str]:
        """Run docker actions: start/stop/reload/rebuild/build."""
        success, message = handle_docker_action(action, model, app_num)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"status": "success" if success else "error", "message": message}), (200 if success else 500)
        flash(f"{'Success' if success else 'Error'}: {message}", "success" if success else "error")
        return redirect(url_for("index"))

    @app.route("/api/health/<string:model>/<int:app_num>")
    @error_handler
    def check_container_health(model: str, app_num: int) -> Response:
        """Check container health with optional retries."""
        healthy, message = verify_container_health(docker_manager, model, app_num)
        return jsonify({"healthy": healthy, "message": message})


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found_error(_error) -> Tuple[str, int]:
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(_error) -> Tuple[str, int]:
        return render_template("500.html"), 500


def register_request_hooks(app: Flask, docker_manager: DockerManager) -> None:
    @app.before_request
    def before_request() -> None:
        if random.random() < 0.01:
            docker_manager.cleanup_containers()

    @app.after_request
    def after_request(response: Response) -> Response:
        response.headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        })
        return response


# -------------------------
# Main Entry Point
# -------------------------
if __name__ == "__main__":
    logging.basicConfig(
        level=getattr(logging, AppConfig.from_env().LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    try:
        app = create_app()
        docker_manager = DockerManager()
        if docker_manager.client:
            if not SystemHealthMonitor.check_health(docker_manager.client):
                logger.warning("System health check failed - reduced functionality expected.")
        else:
            logger.warning("Docker client unavailable - reduced functionality expected.")

        app.run(
            host=app.config["HOST"],
            port=app.config["PORT"],
            debug=app.config["DEBUG"],
        )
    except Exception as exc:
        logger.critical(f"Failed to start application: {exc}")
        raise
