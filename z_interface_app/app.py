"""
app.py - Refactored Flask-based AI Model Management System
========================================================
A Flask-based AI Model Management System that:
- Manages Docker-based frontend/backend apps
- Uses the Python Docker library for container ops
- Handles both sync and async operations
"""

import os
import random
import logging
import time
import asyncio
import subprocess
from functools import wraps
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass

from flask import (
    Flask, 
    render_template, 
    redirect, 
    url_for, 
    jsonify, 
    abort, 
    request, 
    Response
)
from werkzeug.middleware.proxy_fix import ProxyFix
import docker
from docker.errors import NotFound, DockerException
from docker.models.containers import Container

# -------------------------
# Configuration Management
# -------------------------
@dataclass
class AppConfig:
    """Application configuration with strong typing and validation."""
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
            DEBUG=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
            SECRET_KEY=os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here'),
            BASE_DIR=Path(__file__).parent,
            LOG_LEVEL=os.getenv('LOG_LEVEL', 'ERROR'),
            DOCKER_TIMEOUT=int(os.getenv('DOCKER_TIMEOUT', '10')),
            CACHE_DURATION=int(os.getenv('CACHE_DURATION', '5')),
            HOST='0.0.0.0' if os.getenv('FLASK_ENV') == 'production' else '127.0.0.1',
            PORT=int(os.getenv('PORT', '5050'))
        )

# -------------------------
# Domain Models
# -------------------------
@dataclass
class AIModel:
    """Represents an AI model with metadata."""
    name: str
    color: str

@dataclass
class DockerStatus:
    """Container status information with type safety."""
    exists: bool = False
    running: bool = False
    health: str = "unknown"
    status: str = "unknown"
    details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert status to dictionary for JSON responses."""
        return {
            "exists": self.exists,
            "running": self.running,
            "health": self.health,
            "status": self.status,
            "details": self.details
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
    AIModel("Mixtral", "#9333ea")
]

# -------------------------
# Service Classes
# -------------------------
class LoggingService:
    """Centralized logging configuration and management."""
    
    @staticmethod
    def configure(log_level: str) -> None:
        """Configure application-wide logging."""
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Add status endpoint filter
        logging.getLogger('werkzeug').addFilter(StatusEndpointFilter())

class StatusEndpointFilter(logging.Filter):
    """Filters out successful status endpoint calls from logs."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, 'args') or len(record.args) < 3:
            return True
        msg = record.args[2] if isinstance(record.args[2], str) else ''
        return not ('GET /api/container/' in msg and msg.endswith(' HTTP/1.1" 200 -'))

class PortManager:
    """Manages port allocation for services."""
    
    BASE_BACKEND_PORT = 5001
    BASE_FRONTEND_PORT = 5501
    PORTS_PER_APP = 2
    BUFFER_PORTS = 5
    APPS_PER_MODEL = 20

    @classmethod
    def get_port_range(cls, model_idx: int) -> Dict[str, Dict[str, int]]:
        """Calculate port ranges for a model."""
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
        """Get specific ports for an app."""
        ranges = cls.get_port_range(model_idx)
        return {
            'backend': ranges['backend']['start'] + (app_num - 1) * 2,
            'frontend': ranges['frontend']['start'] + (app_num - 1) * 2
        }

class DockerManager:
    """Manages Docker operations with improved error handling and caching."""
    
    def __init__(self, client: Optional[docker.DockerClient] = None) -> None:
        self.logger = logging.getLogger(__name__)
        try:
            self.client = client or self._create_docker_client()
        except Exception as e:
            self.logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None
        self._cache: Dict[str, Tuple[float, DockerStatus]] = {}
        self._cache_duration = AppConfig.from_env().CACHE_DURATION
        self._lock = asyncio.Lock()

    def _create_docker_client(self) -> Optional[docker.DockerClient]:
        """Create and configure Docker client."""
        try:
            # Add environment variable check for Docker host
            docker_host = os.getenv('DOCKER_HOST', 'npipe:////./pipe/docker_engine')
            return docker.DockerClient(
                base_url=docker_host,
                timeout=AppConfig.from_env().DOCKER_TIMEOUT
            )
        except DockerException as e:
            self.logger.error(f"Failed to create Docker client: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error creating Docker client: {e}")
            return None

    def get_container_status(self, container_name: str) -> DockerStatus:
        """Get container status with caching."""
        current_time = time.time()
        
        # Check cache first
        if container_name in self._cache:
            timestamp, status = self._cache[container_name]
            if current_time - timestamp < self._cache_duration:
                return status

        # Get fresh status
        status = self._fetch_container_status(container_name)
        self._cache[container_name] = (current_time, status)
        return status

    def _fetch_container_status(self, container_name: str) -> DockerStatus:
        """Fetch current container status from Docker with error handling."""
        if not self.client:
            return DockerStatus(
                exists=False,
                status="error",
                health="error",
                details="Docker client not available"
            )

        try:
            container: Container = self.client.containers.get(container_name)
            is_running = container.status == "running"
            
            health = "healthy" if is_running else "stopped"
            if "Health" in container.attrs["State"]:
                health = container.attrs["State"]["Health"]["Status"]

            return DockerStatus(
                exists=True,
                running=is_running,
                health=health,
                status=container.status,
                details=container.attrs["State"]["Status"]
            )

        except NotFound:
            return DockerStatus(
                exists=False,
                status="no_container",
                health="not_found",
                details="Container does not exist"
            )
        except DockerException as e:
            self.logger.error(f"Docker error for {container_name}: {e}")
            return DockerStatus(
                exists=False,
                status="error",
                health="error",
                details=str(e)
            )

    def get_container_logs(self, container_name: str, tail: int = 100) -> str:
        """Get container logs with error handling."""
        if not self.client:
            return "Docker client not available"

        try:
            container = self.client.containers.get(container_name)
            return container.logs(tail=tail).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Error getting logs for {container_name}: {e}")
            return f"Error retrieving logs: {str(e)}"

    def cleanup_containers(self) -> None:
        """Clean up stopped containers older than 24h."""
        if not self.client:
            return
            
        try:
            self.client.containers.prune(filters={"until": "24h"})
        except DockerException as e:
            self.logger.error(f"Container cleanup failed: {e}")

class SystemHealthMonitor:
    """Monitors system health and resources."""

    @staticmethod
    def check_disk_space() -> bool:
        """Check if disk space usage is below threshold."""
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
                                        logging.warning(
                                            f"Critical disk usage: {parts[0]} at {usage_percent:.1f}%"
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
                                logging.warning(f"Critical disk usage: {fields[5]} at {usage}%")
                                return False
        except subprocess.CalledProcessError as e:
            logging.error(f"Disk space check failed: {e}")
            return False

        return True

    @staticmethod
    def check_health(docker_client: Optional[docker.DockerClient]) -> bool:
        """Perform system health check."""
        if not docker_client:
            logging.error("No Docker client available")
            return False
            
        try:
            # Check Docker connectivity
            docker_client.ping()
            
            # Check disk space
            if not SystemHealthMonitor.check_disk_space():
                return False
                
            return True
        except Exception as e:
            logging.error(f"Health check failed: {e}")
            return False

# -------------------------
# Utility Functions
# -------------------------
def error_handler(f):
    """Handles exceptions in routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs) -> Union[Response, Tuple[Response, int]]:
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error in {f.__name__}: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"error": str(e)}), 500
            return render_template('500.html'), 500
    return decorated_function

def get_model_index(model_name: str) -> int:
    """Get index of model in AI_MODELS list."""
    return next((i for i, m in enumerate(AI_MODELS) if m.name == model_name), 0)

def get_container_names(model: str, app_num: int) -> Tuple[str, str]:
    """Generate container names for an app."""
    model_idx = get_model_index(model)
    ports = PortManager.get_app_ports(model_idx, app_num)
    base = model.lower()
    return (
        f"{base}_backend_{ports['backend']}",
        f"{base}_frontend_{ports['frontend']}"
    )

def get_app_info(model_name: str, app_num: int) -> Dict[str, Any]:
    """Get app metadata including ports and URLs."""
    model_idx = get_model_index(model_name)
    model_color = next((m.color for m in AI_MODELS if m.name == model_name), "#666666")
    ports = PortManager.get_app_ports(model_idx, app_num)
    
    return {
        "name": f"{model_name} App {app_num}",
        "model": model_name,
        "color": model_color,
        "backend_port": ports['backend'],
        "frontend_port": ports['frontend'],
        "app_num": app_num,
        "backend_url": f"http://localhost:{ports['backend']}",
        "frontend_url": f"http://localhost:{ports['frontend']}",
        "container_prefix": f"{model_name.lower()}_app{app_num}"
    }

def get_apps_for_model(model_name: str) -> List[Dict[str, Any]]:
    """Get all apps for a specific model."""
    base_path = Path(f"{model_name}/flask_apps")
    if not base_path.exists():
        return []

    apps = []
    app_dirs = sorted(
        [d for d in base_path.iterdir() if d.is_dir() and d.name.startswith("app")],
        key=lambda x: int(x.name.replace("app", ""))
    )

    for app_dir in app_dirs:
        try:
            app_num = int(app_dir.name.replace("app", ""))
            apps.append(get_app_info(model_name, app_num))
        except ValueError as e:
            logging.error(f"Error processing {app_dir}: {e}")
            continue

    return apps

def get_all_apps() -> List[Dict[str, Any]]:
    """Get all apps across all models."""
    return [
        app for model in AI_MODELS
        for app in get_apps_for_model(model.name)
    ]

def run_docker_compose(
    command: List[str],
    model: str,
    app_num: int,
    check: bool = True
) -> bool:
    """Execute docker-compose command with error handling."""
    app_dir = Path(f"{model}/flask_apps/app{app_num}")
    
    try:
        subprocess.run(["docker-compose"] + command, cwd=app_dir, check=check)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Docker-compose {' '.join(command)} failed: {e}")
        return False

# -------------------------
# Flask Application Factory
# -------------------------
def create_app(config: Optional[AppConfig] = None) -> Flask:
    """Create and configure Flask application instance."""
    app = Flask(__name__)
    
    # Load configuration
    config = config or AppConfig.from_env()
    app.config.from_object(config)
    
    # Configure logging first
    LoggingService.configure(config.LOG_LEVEL)
    
    # Create logger for app creation
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize services
        docker_manager = DockerManager()
        
        # Apply middleware
        app.wsgi_app = ProxyFix(app.wsgi_app)
        
        # Register blueprints and routes
        register_routes(app, docker_manager)
        
        # Register error handlers
        register_error_handlers(app)
        
        # Register request hooks
        register_request_hooks(app, docker_manager)
        
    except Exception as e:
        logger.error(f"Error during app initialization: {e}")
        # Continue with limited functionality
    
    return app

# -------------------------
# Route Registration
# -------------------------
def register_routes(app: Flask, docker_manager: DockerManager) -> None:
    """Register application routes."""
    
    @app.route('/')
    @error_handler
    def index() -> str:
        """Home page showing all apps and their statuses."""
        apps = get_all_apps()
        
        # Add container statuses
        for app_info in apps:
            backend_name, frontend_name = get_container_names(
                app_info["model"],
                app_info["app_num"]
            )
            app_info["backend_status"] = docker_manager.get_container_status(backend_name)
            app_info["frontend_status"] = docker_manager.get_container_status(frontend_name)

        return render_template('index.html', apps=apps, models=AI_MODELS)

    @app.route('/api/container/<string:model>/<int:app_num>/status')
    @error_handler
    def container_status(model: str, app_num: int) -> Response:
        """Get status of both containers for an app."""
        backend_name, frontend_name = get_container_names(model, app_num)
        
        return jsonify({
            "backend": docker_manager.get_container_status(backend_name).to_dict(),
            "frontend": docker_manager.get_container_status(frontend_name).to_dict()
        })

    @app.route('/logs/<string:model>/<int:app_num>')
    @error_handler
    def view_logs(model: str, app_num: int) -> str:
        """View container logs."""
        backend_name, frontend_name = get_container_names(model, app_num)
        
        logs = {
            'backend': docker_manager.get_container_logs(backend_name),
            'frontend': docker_manager.get_container_logs(frontend_name)
        }
        
        return render_template('logs.html', logs=logs, model=model, app_num=app_num)

    @app.route('/api/model-info')
    @error_handler
    def get_model_info() -> Response:
        """Get port ranges and metadata for all models."""
        return jsonify([{
            "name": model.name,
            "color": model.color,
            "ports": PortManager.get_port_range(idx),
            "total_apps": len(get_apps_for_model(model.name))
        } for idx, model in enumerate(AI_MODELS)])

    @app.route('/<action>/<string:model>/<int:app_num>')
    @error_handler
    def handle_docker_action(action: str, model: str, app_num: int) -> Union[Response, str]:
        """Handle various docker-compose actions."""
        commands = {
            'start': ['up', '-d'],
            'stop': ['down'],
            'reload': ['restart'],
            'rebuild': ['down', 'build', 'up', '-d'],
            'build': ['build']
        }
        
        if action not in commands:
            return jsonify({"error": "Invalid action"}), 400
            
        success = True
        for cmd in commands[action]:
            if not run_docker_compose([cmd], model, app_num):
                success = False
                break
                
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if success:
                return jsonify({"status": "success"})
            return jsonify({"status": "error"}), 500
                
        return redirect(url_for('index'))

def register_error_handlers(app: Flask) -> None:
    """Register application error handlers."""
    
    @app.errorhandler(404)
    def not_found_error(error) -> Tuple[str, int]:
        """Handle 404 errors."""
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error) -> Tuple[str, int]:
        """Handle 500 errors."""
        return render_template('500.html'), 500

def register_request_hooks(app: Flask, docker_manager: DockerManager) -> None:
    """Register request hooks for the application."""
    
    @app.before_request
    def before_request() -> None:
        """Pre-request processing."""
        # Periodic container cleanup (1% chance)
        if random.random() < 0.01:
            docker_manager.cleanup_containers()

    @app.after_request
    def after_request(response: Response) -> Response:
        """Post-request processing."""
        # Add security headers
        response.headers.update({
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'SAMEORIGIN',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
        })
        return response

# -------------------------
# Main Entry Point
# -------------------------
if __name__ == '__main__':
    # Configure logging first
    logging.basicConfig(
        level=getattr(logging, AppConfig.from_env().LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        app = create_app()
        
        # Perform initial health check
        docker_manager = DockerManager()
        if docker_manager.client:
            try:
                if not SystemHealthMonitor.check_health(docker_manager.client):
                    logger.warning("System health check failed - starting with reduced functionality")
            except Exception as e:
                logger.error(f"Health check error: {e}")
        else:
            logger.warning("Docker client not available - starting with reduced functionality")
        
        # Start the application
        app.run(
            host=app.config['HOST'],
            port=app.config['PORT'],
            debug=app.config['DEBUG']
        )
    except Exception as e:
        logger.critical(f"Failed to start application: {e}")
        raise