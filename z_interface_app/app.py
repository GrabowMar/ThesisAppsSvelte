"""
app.py
=======
A Flask-based AI Model Management System that:
- Manages Docker-based frontend/backend apps
- Uses the Python Docker library for container status checks
- Still uses 'docker-compose' for building and running containers (subprocess)
"""

import os
import random  # For cleanup probability in before_request
import logging
import time
import asyncio
from functools import wraps
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass

from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    jsonify,
    abort,
    session
)
from werkzeug.middleware.proxy_fix import ProxyFix

# Docker library import
import docker
from docker.errors import NotFound, DockerException


# -------------------------
# Logging Configuration
# -------------------------
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# -------------------------
# Flask Application Setup
# -------------------------
app = Flask(__name__)


class StatusEndpointFilter(logging.Filter):
    """
    A logging filter that prevents logging certain container status endpoint calls
    when they are successful (HTTP 200).
    """
    def filter(self, record):
        if (
            hasattr(record, 'args')
            and len(record.args) >= 3
            and isinstance(record.args[2], str)
            and 'GET /api/container/' in record.args[2]
            and record.args[2].endswith(' HTTP/1.1" 200 -')
        ):
            return False
        return True


# -------------------------
# Configuration
# -------------------------
class Config:
    """Load configuration from environment variables."""
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')
    BASE_DIR = Path(__file__).parent


app.config.from_object(Config)


# -------------------------
# AI Model Definitions
# -------------------------
@dataclass
class AIModel:
    """Holds basic info about each AI model (name, color)."""
    name: str
    color: str


AI_MODELS = [
    AIModel("ChatGPT", "#10a37f"),
    AIModel("ChatGPTo1", "#0ea47f"),
    AIModel("ClaudeSonnet", "#7b2bf9"),
    AIModel("CodeLlama", "#f97316"),
    AIModel("Gemini", "#1a73e8"),
    AIModel("Grok", "#ff4d4f"),
    AIModel("Mixtral", "#9333ea")
]


# -------------------------
# Create Docker Client
# -------------------------
# You can reuse this client throughout the application
try:
    docker_client = docker.from_env()
except DockerException as e:
    logger.error(f"Failed to create Docker client: {e}")
    docker_client = None


# -------------------------
# System Status & Checks
# -------------------------
class SystemStatus:
    """
    Manages system (Docker) status checks, including caching results
    to avoid frequent Docker commands.
    """
    def __init__(self):
        self.last_check = 0
        self.cache_duration = 30  # Cache system status for 30 seconds
        self.status_cache = None
        self._lock = asyncio.Lock()

    async def get_status(self) -> Dict:
        """Get system status with caching to prevent excessive Docker calls."""
        current_time = time.time()
        if self.status_cache and (current_time - self.last_check) < self.cache_duration:
            return self.status_cache

        async with self._lock:
            try:
                docker_status = await self.check_docker_service()
                container_stats = await self.get_container_statistics()

                status = {
                    "status": "healthy" if docker_status else "error",
                    "docker_service": docker_status,
                    "containers": container_stats,
                    "timestamp": current_time
                }

                self.status_cache = status
                self.last_check = current_time
                return status

            except Exception as e:
                logger.error(f"Error getting system status: {str(e)}")
                return {
                    "status": "error",
                    "message": str(e),
                    "timestamp": current_time
                }

    async def check_docker_service(self) -> bool:
        """
        Check if Docker service is running and responsive 
        by trying a simple client call (e.g., ping/info).
        """
        if not docker_client:
            return False
        try:
            # 'ping()' is the simplest check; will raise exception if not running
            docker_client.ping()
            return True
        except DockerException:
            return False

    async def get_container_statistics(self) -> Dict:
        """
        Retrieve a summary of container statistics using the Docker Python library.
        """
        if not docker_client:
            return {
                "total": 0,
                "running": 0,
                "stopped": 0,
                "error": "Docker client not available"
            }

        try:
            # List all containers
            all_containers = docker_client.containers.list(all=True)
            total = len(all_containers)
            running = sum(1 for c in all_containers if c.status == "running")

            return {
                "total": total,
                "running": running,
                "stopped": total - running
            }
        except DockerException as e:
            logger.error(f"Failed to get container statistics: {e}")
            return {
                "total": 0,
                "running": 0,
                "stopped": 0,
                "error": str(e)
            }


# -------------------------
# Port Management
# -------------------------
class PortManager:
    """
    Manages port allocation for frontend and backend services.
    Each model can have up to APPS_PER_MODEL apps, each requiring 2 ports.
    """
    BASE_BACKEND_PORT = 5001
    BASE_FRONTEND_PORT = 5501
    PORTS_PER_APP = 2
    BUFFER_PORTS = 5
    APPS_PER_MODEL = 20

    @classmethod
    def get_port_range(cls, model_idx: int) -> Dict[str, Dict[str, int]]:
        """
        Calculate port ranges for a model based on its index in the AI_MODELS list.
        """
        ports_needed = cls.APPS_PER_MODEL * cls.PORTS_PER_APP + cls.BUFFER_PORTS
        return {
            'backend': {
                'start': cls.BASE_BACKEND_PORT + (model_idx * ports_needed),
                'end': cls.BASE_BACKEND_PORT + ((model_idx + 1) * ports_needed) - cls.BUFFER_PORTS
            },
            'frontend': {
                'start': cls.BASE_FRONTEND_PORT + (model_idx * ports_needed),
                'end': cls.BASE_FRONTEND_PORT + ((model_idx + 1) * ports_needed) - cls.BUFFER_PORTS
            }
        }

    @classmethod
    def get_app_ports(cls, model_idx: int, app_num: int) -> Dict[str, int]:
        """
        Given the model index and the app number, return the specific
        backend/frontend ports assigned to that app.
        """
        ranges = cls.get_port_range(model_idx)
        return {
            'backend': ranges['backend']['start'] + (app_num - 1) * 2,
            'frontend': ranges['frontend']['start'] + (app_num - 1) * 2
        }


# -------------------------
# Error Handling Decorator
# -------------------------
def error_handler(f):
    """
    A decorator that wraps route functions in a try-except block
    to return JSON error responses instead of unhandled exceptions.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            return jsonify({"error": str(e)}), 500
    return decorated_function


# -------------------------
# Container Status Helpers
# -------------------------
def batch_container_status(container_names: List[str]) -> Dict[str, Dict]:
    """
    Get status for multiple containers in a single batch using the Docker library,
    thereby avoiding direct subprocess calls.

    Args:
        container_names (List[str]): List of container names to check status for

    Returns:
        Dict[str, Dict]: A mapping of each container name to its status info
    """
    if not docker_client:
        # Docker client not available
        return {
            name: {
                "status": "error",
                "running": False,
                "health": "error",
                "details": "Docker client not available",
                "exists": False
            }
            for name in container_names
        }

    status_map = {}
    for name in container_names:
        try:
            container = docker_client.containers.get(name)
            # Container exists, gather status
            is_running = (container.status == "running")

            # Default health is "healthy" if running, "stopped" otherwise
            health = "healthy" if is_running else "stopped"

            # If container has health info, override
            if "Health" in container.attrs["State"]:
                health_state = container.attrs["State"]["Health"]["Status"]
                # Could be 'healthy', 'unhealthy', 'starting', etc.
                health = health_state

            status_map[name] = {
                "status": "running" if is_running else "stopped",
                "running": is_running,
                "health": health,
                "details": container.attrs["State"]["Status"],
                "exists": True
            }

        except NotFound:
            status_map[name] = {
                "status": "no_container",     # instead of "not_built"
                "running": False,
                "health": "not_found",
                "details": "No container exists yet",
                "exists": False
            }
        except DockerException as e:
            # Some other Docker-related error
            error_msg = f"Error fetching container status: {e}"
            logger.error(error_msg)
            status_map[name] = {
                "status": "error",
                "running": False,
                "health": "error",
                "details": error_msg,
                "exists": False
            }
    return status_map


def get_apps_for_model(model_name: str) -> List[Dict]:
    """
    Generate app metadata (ports, URLs, container prefix, etc.) for a specific AI model.
    Looks for subdirectories named 'appN' under [model_name]/flask_apps.
    """
    base_path = Path(f"{model_name}/flask_apps")
    if not base_path.exists():
        return []

    # Find model index and color
    model_idx = next((i for i, m in enumerate(AI_MODELS) if m.name == model_name), 0)
    model_color = next((m.color for m in AI_MODELS if m.name == model_name), "#666666")

    apps = []
    # Get directories like "app1", "app2", etc., sorted by the numeric part
    app_dirs = sorted(
        [d for d in base_path.iterdir() if d.is_dir() and d.name.startswith("app")],
        key=lambda x: int(x.name.replace("app", ""))
    )

    for app_dir in app_dirs:
        try:
            app_num = int(app_dir.name.replace("app", ""))

            # Calculate ports
            ports = PortManager.get_app_ports(model_idx, app_num)

            apps.append({
                "name": f"{model_name} App {app_num}",
                "model": model_name,
                "color": model_color,
                "backend_port": ports['backend'],
                "frontend_port": ports['frontend'],
                "app_num": app_num,
                "backend_url": f"http://localhost:{ports['backend']}",
                "frontend_url": f"http://localhost:{ports['frontend']}",
                "container_prefix": f"{model_name.lower()}_app{app_num}"
            })
        except ValueError as e:
            logger.error(f"Error processing app directory {app_dir}: {str(e)}")
            continue

    return apps


def get_all_apps() -> List[Dict]:
    """Collect all apps across all AI models."""
    all_apps = []
    for model in AI_MODELS:
        model_apps = get_apps_for_model(model.name)
        all_apps.extend(model_apps)
    return all_apps


# Create a global instance of SystemStatus
system_status = SystemStatus()


# -------------------------
# Flask Routes
# -------------------------

@app.route('/')
@error_handler
def index():
    """
    Home page showing all apps and their statuses.
    """
    apps = get_all_apps()

    # For each app, fetch both backend and frontend container statuses
    for app_info in apps:
        container_prefix = app_info["container_prefix"]
        status = batch_container_status([
            f"{container_prefix}_backend",
            f"{container_prefix}_frontend"
        ])
        app_info["backend_status"] = status[f"{container_prefix}_backend"]["running"]
        app_info["frontend_status"] = status[f"{container_prefix}_frontend"]["running"]

    return render_template('index.html', apps=apps, models=AI_MODELS)


@app.route('/api/status')
@error_handler
def get_system_status():
    """
    API endpoint to get system status (cached Docker checks).
    """
    status = asyncio.run(system_status.get_status())
    return jsonify(status)


@app.route('/api/model-info')
@error_handler
def get_model_info():
    """
    API endpoint to retrieve port ranges, colors, and total apps for all models.
    """
    model_info = []
    for idx, model in enumerate(AI_MODELS):
        port_range = PortManager.get_port_range(idx)
        model_info.append({
            "name": model.name,
            "color": model.color,
            "ports": port_range,
            "total_apps": len(get_apps_for_model(model.name))
        })
    return jsonify(model_info)


@app.route('/logs/<string:model>/<int:app_num>')
@error_handler
def view_logs(model: str, app_num: int):
    """
    View logs (last 100 lines) for a specific app's containers.

    NOTE: This still calls 'docker logs' via subprocess. You could 
    migrate to the Docker library: container.logs(tail=100).
    """
    import subprocess  # Only needed for the logs endpoint

    container_prefix = f"{model.lower()}_app{app_num}"
    try:
        logs = {
            service: subprocess.run(
                ["docker", "logs", f"{container_prefix}_{service}", "--tail=100"],
                capture_output=True,
                text=True,
                check=True
            ).stdout
            for service in ['backend', 'frontend']
        }
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting logs for {container_prefix}: {str(e)}")
        logs = {
            'backend': 'Error retrieving logs',
            'frontend': 'Error retrieving logs'
        }
    return render_template('logs.html', logs=logs, model=model, app_num=app_num)


@app.route('/api/container/<string:model>/<int:app_num>/status')
@error_handler
def container_status(model: str, app_num: int):
    """
    Get status of both containers for an app using batch processing.
    """
    container_prefix = f"{model.lower()}"
    # container_prefix = f"{model.lower()}_app{app_num}"
    model_idx = next((i for i, m in enumerate(AI_MODELS) if m.name == model), 0)
    ports = PortManager.get_app_ports(model_idx, app_num)
    backend_port_postfix = ports['backend']
    frontend_port_postfix = ports['frontend']
    container_names = [
        f"{container_prefix}_backend_{backend_port_postfix}",
        f"{container_prefix}_frontend_{frontend_port_postfix}"
    ]
    
    status = batch_container_status(container_names)
    print(status)
    aa = jsonify({
        "backend": status[f"{container_prefix}_backend_{backend_port_postfix}"],
        "frontend": status[f"{container_prefix}_frontend_{frontend_port_postfix}"]
    })
    return aa



# -----------------------------------------------------------
# Routes that still invoke 'docker-compose' via subprocess
# -----------------------------------------------------------

@app.route('/build/<string:model>/<int:app_num>')
@error_handler
def build(model: str, app_num: int):
    """
    Build Docker images for a specific app via Docker Compose.
    If you want to use the Docker library for building images 
    directly, consider docker_client.images.build().
    """
    import subprocess
    app_dir = Path(f"{model}/flask_apps/app{app_num}")
    try:
        subprocess.run(
            ["docker-compose", "build"],
            cwd=app_dir,
            check=True
        )
        return redirect(url_for('index'))
    except subprocess.CalledProcessError as e:
        logger.error(f"Build failed for {model} app {app_num}: {str(e)}")
        abort(500)


@app.route('/start/<string:model>/<int:app_num>')
@error_handler
def start_app(model: str, app_num: int):
    """
    Start the specified app via Docker Compose (up -d).
    """
    import subprocess
    app_dir = Path(f"{model}/flask_apps/app{app_num}")
    try:
        subprocess.run(
            ["docker-compose", "up", "-d"],
            cwd=app_dir,
            check=True
        )
        return redirect(url_for('index'))
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start {model} app {app_num}: {str(e)}")
        abort(500)


@app.route('/stop/<string:model>/<int:app_num>')
@error_handler
def stop_app(model: str, app_num: int):
    """
    Stop the specified app via Docker Compose (down).
    """
    import subprocess
    app_dir = Path(f"{model}/flask_apps/app{app_num}")
    try:
        subprocess.run(
            ["docker-compose", "down"],
            cwd=app_dir,
            check=True
        )
        return redirect(url_for('index'))
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to stop {model} app {app_num}: {str(e)}")
        abort(500)


@app.route('/reload/<string:model>/<int:app_num>')
@error_handler
def reload_app(model: str, app_num: int):
    """
    Restart the specified app via Docker Compose (restart).
    """
    import subprocess
    app_dir = Path(f"{model}/flask_apps/app{app_num}")
    try:
        subprocess.run(
            ["docker-compose", "restart"],
            cwd=app_dir,
            check=True
        )
        return redirect(url_for('index'))
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to reload {model} app {app_num}: {str(e)}")
        abort(500)


# -------------------------
# Error Handlers
# -------------------------
@app.errorhandler(404)
def not_found_error(error):
    """Custom 404 page."""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Custom 500 page for server errors."""
    logger.error(f"Internal server error: {str(error)}")
    return render_template('500.html'), 500


# -------------------------
# Utility Functions
# -------------------------
def cleanup_containers():
    """
    Clean up stopped containers that are older than 24 hours.
    Using the Docker client for container pruning is possible via:
        docker_client.containers.prune(filters={"until": "24h"})
    """
    import subprocess
    try:
        subprocess.run(
            ["docker", "container", "prune", "-f", "--filter", "until=24h"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Error cleaning up containers: {str(e)}")


def health_check() -> bool:
    """
    Perform a basic health check of the system (Docker + disk usage).
    Uses the Docker client for a simple check, then disk usage via subprocess.
    """
    # 1) Check Docker via docker_client
    if not docker_client:
        logger.error("No Docker client available for health check.")
        return False
    try:
        docker_client.ping()
    except DockerException as e:
        logger.error(f"Health check failed (Docker not responding): {e}")
        return False

    # 2) Check disk space
    import subprocess
    try:
        if os.name == 'nt':  # Windows
            df = subprocess.run(
                ["wmic", "logicaldisk", "get", "size,freespace,caption"],
                capture_output=True,
                text=True,
                check=True
            )
            lines = df.stdout.strip().split('\n')[1:]
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            free_space = int(parts[1])
                            total_size = int(parts[2])
                            if total_size > 0:
                                usage_percent = ((total_size - free_space) / total_size) * 100
                                if usage_percent > 90:
                                    logger.warning(
                                        f"Disk usage critical: {parts[0]} is at {usage_percent:.1f}%"
                                    )
                                    return False
                        except (IndexError, ValueError):
                            continue
        else:  # Unix/Linux
            df = subprocess.run(["df", "-h"], capture_output=True, text=True, check=True)
            for line in df.stdout.split('\n')[1:]:
                if line:
                    fields = line.split()
                    if len(fields) >= 5:
                        usage = int(fields[4].rstrip('%'))
                        if usage > 90:
                            logger.warning(
                                f"Disk usage critical: {fields[5]} is at {usage}%"
                            )
                            return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Health check disk usage failed: {e}")
        return False

    return True


# -------------------------
# Pre/Post Request Hooks
# -------------------------
@app.before_request
def before_request():
    """
    Hook that runs before each request.
    Periodically cleans up containers with a small probability (1%).
    """
    if random.random() < 0.01:
        cleanup_containers()


@app.after_request
def after_request(response):
    """
    Hook that runs after each request to add security headers.
    """
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response


# -------------------------
# Main Entry Point
# -------------------------
if __name__ == '__main__':
    app.wsgi_app = ProxyFix(app.wsgi_app)  # Use ProxyFix for correct request IP forwarding
    logger.info("Starting AI Model Management System")

    try:
        ok = health_check()
        if not ok:
            logger.warning("System health check failed - starting anyway with reduced functionality")
    except Exception as e:
        logger.error(f"Health check error: {str(e)} - continuing startup")

    app.run(
        host='0.0.0.0' if os.getenv('FLASK_ENV') == 'production' else '127.0.0.1',
        port=int(os.getenv('PORT', 5050)),
        debug=Config.DEBUG
    )
