from flask import Flask, render_template, redirect, url_for, jsonify, abort, session
import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass
import asyncio
import time
from functools import wraps
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class StatusEndpointFilter(logging.Filter):
    def filter(self, record):
        # Skip logging for successful container status endpoint calls
        if (hasattr(record, 'args') and len(record.args) >= 3 and 
            isinstance(record.args[2], str) and 
            'GET /api/container/' in record.args[2] and 
            record.args[2].endswith(' HTTP/1.1" 200 -')):
            return False
        return True

# Load configuration from environment variables
class Config:
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')
    BASE_DIR = Path(__file__).parent

app.config.from_object(Config)

# Define models and their properties
@dataclass
class AIModel:
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

class SystemStatus:
    def __init__(self):
        self.last_check = 0
        self.cache_duration = 30  # Cache status for 30 seconds
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
        """Check if Docker service is running and responsive."""
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["docker", "info"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.returncode == 0
        except subprocess.CalledProcessError:
            return False

    async def get_container_statistics(self) -> Dict:
        """Get summary statistics for all containers."""
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
                capture_output=True,
                text=True,
                check=True
            )
            
            containers = result.stdout.strip().split('\n')
            running = 0
            total = len(containers) if containers[0] else 0
            
            for container in containers:
                if container and 'Up' in container:
                    running += 1
                        
            return {
                "total": total,
                "running": running,
                "stopped": total - running
            }
            
        except subprocess.CalledProcessError:
            return {
                "total": 0,
                "running": 0,
                "stopped": 0,
                "error": "Failed to get container statistics"
            }

class PortManager:
    """Manages port allocation for frontend and backend services."""
    
    BASE_BACKEND_PORT = 5001
    BASE_FRONTEND_PORT = 5501
    PORTS_PER_APP = 2
    BUFFER_PORTS = 5
    APPS_PER_MODEL = 20

    @classmethod
    def get_port_range(cls, model_idx: int) -> Dict[str, Dict[str, int]]:
        """Calculate port ranges for a model based on its index."""
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
        """Get specific ports for an app within a model."""
        ranges = cls.get_port_range(model_idx)
        return {
            'backend': ranges['backend']['start'] + (app_num - 1) * 2,
            'frontend': ranges['frontend']['start'] + (app_num - 1) * 2
        }

def error_handler(f):
    """Decorator for handling errors in routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            return jsonify({"error": str(e)}), 500
    return decorated_function

def batch_container_status(container_names: List[str]) -> Dict[str, Dict]:
    """Get status for multiple containers in a batch to reduce Docker calls.
    
    Args:
        container_names: List of container names to check status for
        
    Returns:
        Dictionary mapping container names to their status information
    """
    try:
        # First check if containers exist using docker container inspect
        # This handles non-existent containers more reliably than 'ps'
        existing_containers = set()
        for name in container_names:
            try:
                result = subprocess.run(
                    ["docker", "container", "inspect", name],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    existing_containers.add(name)
            except subprocess.CalledProcessError:
                continue

        # Get status for existing containers
        format_str = '{{.Names}}\t{{.Status}}'
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", format_str],
            capture_output=True,
            text=True,
            check=True
        )
        
        status_map = {}
        containers = result.stdout.strip().split('\n')
        
        # Create lookup dictionary for quick container status lookup
        container_lookup = {}
        for container in containers:
            if not container:  # Skip empty lines
                continue
                
            try:
                # Split status fields
                name, status = container.split('\t')
                
                # Analyze status string for detailed state
                is_running = status.startswith('Up')
                
                # Parse additional status information
                status_details = {
                    "status": "running" if is_running else "stopped",
                    "running": is_running,
                    "health": "healthy" if is_running else "stopped",
                    "details": status,
                    "exists": True
                }
                
                # Check for specific states in status string
                if '(healthy)' in status:
                    status_details["health"] = "healthy"
                elif '(unhealthy)' in status:
                    status_details["health"] = "unhealthy"
                elif 'starting' in status.lower():
                    status_details["health"] = "starting"
                elif 'created' in status.lower():
                    status_details["status"] = "created"
                    status_details["health"] = "not_started"
                    
                container_lookup[name] = status_details
                
            except ValueError as e:
                logger.error(f"Error processing container status line '{container}': {str(e)}")
                continue
        
        # Map requested container names to their statuses
        for name in container_names:
            if name in container_lookup:
                status_map[name] = container_lookup[name]
            elif name in existing_containers:
                # Container exists but might be in an intermediate state
                status_map[name] = {
                    "status": "created",
                    "running": False,
                    "health": "not_started",
                    "details": "Container created but not yet started",
                    "exists": True
                }
            else:
                # Container doesn't exist yet
                status_map[name] = {
                    "status": "not_built",
                    "running": False,
                    "health": "not_found",
                    "details": "Container not yet built",
                    "exists": False
                }
        
        return status_map
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to get container status: {str(e)}"
        logger.error(error_msg)
        return {name: {
            "status": "error",
            "running": False,
            "health": "error",
            "details": error_msg,
            "exists": False
        } for name in container_names}
    except Exception as e:
        error_msg = f"Unexpected error in batch_container_status: {str(e)}"
        logger.error(error_msg)
        return {name: {
            "status": "error",
            "running": False,
            "health": "error",
            "details": error_msg,
            "exists": False
        } for name in container_names}

def get_apps_for_model(model_name: str) -> List[Dict]:
    """Generate app metadata for a specific AI model."""
    base_path = Path(f"{model_name}/flask_apps")
    if not base_path.exists():
        return []
    
    model_idx = next((i for i, m in enumerate(AI_MODELS) if m.name == model_name), 0)
    model_color = next((m.color for m in AI_MODELS if m.name == model_name), "#666666")
    
    apps = []
    app_dirs = sorted(
        [d for d in base_path.iterdir() if d.is_dir() and d.name.startswith("app")],
        key=lambda x: int(x.name.replace("app", ""))
    )
    
    for app_dir in app_dirs:
        try:
            app_num = int(app_dir.name.replace("app", ""))
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
    """Get all apps across all AI models."""
    all_apps = []
    for model in AI_MODELS:
        model_apps = get_apps_for_model(model.name)
        all_apps.extend(model_apps)
    return all_apps

# Create global instance of SystemStatus
system_status = SystemStatus()

# Routes

# Add this route to app.py
@app.route('/api/settings/autorefresh/<string:state>')
@error_handler
def toggle_autorefresh(state):
    """Toggle the auto-refresh setting."""
    enabled = state.lower() == 'true'
    session['autorefresh_enabled'] = enabled
    return jsonify({"status": "success", "autorefresh": enabled})


# Modify the index route to include the autorefresh setting
@app.route('/')
@error_handler
def index():
    """Home page showing all apps and their statuses."""
    apps = get_all_apps()
    for app_info in apps:
        container_prefix = app_info["container_prefix"]
        status = batch_container_status([
            f"{container_prefix}_backend",
            f"{container_prefix}_frontend"
        ])
        app_info["backend_status"] = status[f"{container_prefix}_backend"]["running"]
        app_info["frontend_status"] = status[f"{container_prefix}_frontend"]["running"]
    
    # Get autorefresh setting from session, default to True
    autorefresh_enabled = session.get('autorefresh_enabled', False)
    
    return render_template('index.html', 
                         apps=apps, 
                         models=AI_MODELS, 
                         autorefresh_enabled=autorefresh_enabled)

@app.route('/api/status')
@error_handler
def get_system_status():
    """API endpoint to get system status."""
    # Run the asynchronous task in an event loop
    status = asyncio.run(system_status.get_status())
    return jsonify(status)


@app.route('/api/model-info')
@error_handler
def get_model_info():
    """API endpoint to get information about all models."""
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
    """View logs for a specific app."""
    container_prefix = f"{model.lower()}_app{app_num}"
    try:
        logs = {
            service: subprocess.run(
                ["docker", "logs", f"{container_prefix}_{service}", "--tail=100"],
                capture_output=True,
                text=True,
                check=True
            ).stdout for service in ['backend', 'frontend']
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
    """Get status of both containers for an app using batch processing."""
    container_prefix = f"{model.lower()}_app{app_num}"
    container_names = [
        f"{container_prefix}_backend",
        f"{container_prefix}_frontend"
    ]
    
    status = batch_container_status(container_names)
    return jsonify({
        "backend": status[f"{container_prefix}_backend"],
        "frontend": status[f"{container_prefix}_frontend"]
    })

@app.route('/build/<string:model>/<int:app_num>')
@error_handler
def build(model: str, app_num: int):
    """Build Docker images for a specific app."""
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
    """Start the specified app."""
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
    """Stop the specified app."""
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

@app.route('/open/backend/<string:model>/<int:app_num>')
@error_handler
def open_backend(model: str, app_num: int):
    """Open backend URL."""
    apps = get_all_apps()
    app = next((app for app in apps if app["model"] == model and app["app_num"] == app_num), None)
    return redirect(app["backend_url"]) if app else ("App not found", 404)

@app.route('/open/frontend/<string:model>/<int:app_num>')
@error_handler
def open_frontend(model: str, app_num: int):
    """Open frontend URL."""
    apps = get_all_apps()
    app = next((app for app in apps if app["model"] == model and app["app_num"] == app_num), None)
    return redirect(app["frontend_url"]) if app else ("App not found", 404)

@app.route('/reload/<string:model>/<int:app_num>')
@error_handler
def reload_app(model: str, app_num: int):
    """Reload the specified app."""
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

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(error)}")
    return render_template('500.html'), 500

def is_port_available(port: int) -> bool:
    """Check if a port is available for use."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"publish={port}", "--format", "{{.Ports}}"],
            capture_output=True,
            text=True,
            check=True
        )
        return not bool(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        logger.error(f"Error checking port availability: {str(e)}")
        return False

def verify_docker_compose(app_dir: Path) -> bool:
    """Verify that the docker-compose.yml file exists and is valid."""
    try:
        compose_file = app_dir / "docker-compose.yml"
        if not compose_file.exists():
            logger.error(f"docker-compose.yml not found in {app_dir}")
            return False
            
        result = subprocess.run(
            ["docker-compose", "config", "-q"],
            cwd=app_dir,
            capture_output=True,
            check=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Invalid docker-compose configuration in {app_dir}: {str(e)}")
        return False

def cleanup_containers():
    """Clean up stopped containers that are older than 24 hours."""
    try:
        subprocess.run(
            ["docker", "container", "prune", "-f", "--filter", "until=24h"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Error cleaning up containers: {str(e)}")

def health_check() -> bool:
    """Perform a health check of the management system."""
    try:
        # Check if Docker daemon is running
        docker_status = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            check=True
        )
        
        # Check disk space on Windows using wmic
        if os.name == 'nt':  # Windows systems
            df = subprocess.run(
                ["wmic", "logicaldisk", "get", "size,freespace,caption"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse the output
            lines = df.stdout.strip().split('\n')[1:]  # Skip header
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
                                    logger.warning(f"Disk usage critical: {parts[0]} is at {usage_percent:.1f}%")
                                    return False
                        except (IndexError, ValueError):
                            continue
        else:  # Unix/Linux systems
            df = subprocess.run(
                ["df", "-h"],
                capture_output=True,
                text=True,
                check=True
            )
            
            for line in df.stdout.split('\n')[1:]:
                if line:
                    fields = line.split()
                    if len(fields) >= 5:
                        usage = int(fields[4].rstrip('%'))
                        if usage > 90:
                            logger.warning(f"Disk usage critical: {fields[5]} is at {usage}%")
                            return False
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Health check failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in health check: {str(e)}")
        return False

@app.before_request
def before_request():
    """Perform operations before each request."""
    # Perform cleanup operations periodically
    if random.random() < 0.01:  # 1% chance to run cleanup
        cleanup_containers()

@app.after_request
def after_request(response):
    """Perform operations after each request."""
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

if __name__ == '__main__':
    app.wsgi_app = ProxyFix(app.wsgi_app)
    logger.info("Starting AI Model Management System")
    
    try:
        health_status = health_check()
        if not health_status:
            logger.warning("System health check failed - starting anyway with reduced functionality")
    except Exception as e:
        logger.error(f"Health check error: {str(e)} - continuing startup")
    
    import random  # For cleanup probability in before_request
    
    app.run(
        host='0.0.0.0' if os.getenv('FLASK_ENV') == 'production' else '127.0.0.1',
        port=int(os.getenv('PORT', 5050)),
        debug=Config.DEBUG
    )
app = Flask(__name__)

class StatusEndpointFilter(logging.Filter):
    def filter(self, record):
        # Skip logging for successful container status endpoint calls
        if (hasattr(record, 'args') and len(record.args) >= 3 and 
            isinstance(record.args[2], str) and 
            'GET /api/container/' in record.args[2] and 
            record.args[2].endswith(' HTTP/1.1" 200 -')):
            return False
        return True

# Load configuration from environment variables
class Config:
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')
    BASE_DIR = Path(__file__).parent

app.config.from_object(Config)

# Define models and their properties
@dataclass
class AIModel:
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

class SystemStatus:
    def __init__(self):
        self.last_check = 0
        self.cache_duration = 30  # Cache status for 30 seconds
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
        """Check if Docker service is running and responsive."""
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["docker", "info"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.returncode == 0
        except subprocess.CalledProcessError:
            return False

    async def get_container_statistics(self) -> Dict:
        """Get summary statistics for all containers."""
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
                capture_output=True,
                text=True,
                check=True
            )
            
            containers = result.stdout.strip().split('\n')
            running = 0
            total = len(containers) if containers[0] else 0
            
            for container in containers:
                if container and 'Up' in container:
                    running += 1
                        
            return {
                "total": total,
                "running": running,
                "stopped": total - running
            }
            
        except subprocess.CalledProcessError:
            return {
                "total": 0,
                "running": 0,
                "stopped": 0,
                "error": "Failed to get container statistics"
            }

class PortManager:
    """Manages port allocation for frontend and backend services."""
    
    BASE_BACKEND_PORT = 5001
    BASE_FRONTEND_PORT = 5501
    PORTS_PER_APP = 2
    BUFFER_PORTS = 5
    APPS_PER_MODEL = 20

    @classmethod
    def get_port_range(cls, model_idx: int) -> Dict[str, Dict[str, int]]:
        """Calculate port ranges for a model based on its index."""
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
        """Get specific ports for an app within a model."""
        ranges = cls.get_port_range(model_idx)
        return {
            'backend': ranges['backend']['start'] + (app_num - 1) * 2,
            'frontend': ranges['frontend']['start'] + (app_num - 1) * 2
        }

def error_handler(f):
    """Decorator for handling errors in routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            return jsonify({"error": str(e)}), 500
    return decorated_function

def batch_container_status(container_names: List[str]) -> Dict[str, Dict]:
    """Get status for multiple containers in a batch to reduce Docker calls.
    
    Args:
        container_names: List of container names to check status for
        
    Returns:
        Dictionary mapping container names to their status information
    """
    try:
        # First check if containers exist using docker container inspect
        # This handles non-existent containers more reliably than 'ps'
        existing_containers = set()
        for name in container_names:
            try:
                result = subprocess.run(
                    ["docker", "container", "inspect", name],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    existing_containers.add(name)
            except subprocess.CalledProcessError:
                continue

        # Get status for existing containers
        format_str = '{{.Names}}\t{{.Status}}'
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", format_str],
            capture_output=True,
            text=True,
            check=True
        )
        
        status_map = {}
        containers = result.stdout.strip().split('\n')
        
        # Create lookup dictionary for quick container status lookup
        container_lookup = {}
        for container in containers:
            if not container:  # Skip empty lines
                continue
                
            try:
                # Split status fields
                name, status = container.split('\t')
                
                # Analyze status string for detailed state
                is_running = status.startswith('Up')
                
                # Parse additional status information
                status_details = {
                    "status": "running" if is_running else "stopped",
                    "running": is_running,
                    "health": "healthy" if is_running else "stopped",
                    "details": status,
                    "exists": True
                }
                
                # Check for specific states in status string
                if '(healthy)' in status:
                    status_details["health"] = "healthy"
                elif '(unhealthy)' in status:
                    status_details["health"] = "unhealthy"
                elif 'starting' in status.lower():
                    status_details["health"] = "starting"
                elif 'created' in status.lower():
                    status_details["status"] = "created"
                    status_details["health"] = "not_started"
                    
                container_lookup[name] = status_details
                
            except ValueError as e:
                logger.error(f"Error processing container status line '{container}': {str(e)}")
                continue
        
        # Map requested container names to their statuses
        for name in container_names:
            if name in container_lookup:
                status_map[name] = container_lookup[name]
            elif name in existing_containers:
                # Container exists but might be in an intermediate state
                status_map[name] = {
                    "status": "created",
                    "running": False,
                    "health": "not_started",
                    "details": "Container created but not yet started",
                    "exists": True
                }
            else:
                # Container doesn't exist yet
                status_map[name] = {
                    "status": "not_built",
                    "running": False,
                    "health": "not_found",
                    "details": "Container not yet built",
                    "exists": False
                }
        
        return status_map
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to get container status: {str(e)}"
        logger.error(error_msg)
        return {name: {
            "status": "error",
            "running": False,
            "health": "error",
            "details": error_msg,
            "exists": False
        } for name in container_names}
    except Exception as e:
        error_msg = f"Unexpected error in batch_container_status: {str(e)}"
        logger.error(error_msg)
        return {name: {
            "status": "error",
            "running": False,
            "health": "error",
            "details": error_msg,
            "exists": False
        } for name in container_names}

def get_apps_for_model(model_name: str) -> List[Dict]:
    """Generate app metadata for a specific AI model."""
    base_path = Path(f"{model_name}/flask_apps")
    if not base_path.exists():
        return []
    
    model_idx = next((i for i, m in enumerate(AI_MODELS) if m.name == model_name), 0)
    model_color = next((m.color for m in AI_MODELS if m.name == model_name), "#666666")
    
    apps = []
    app_dirs = sorted(
        [d for d in base_path.iterdir() if d.is_dir() and d.name.startswith("app")],
        key=lambda x: int(x.name.replace("app", ""))
    )
    
    for app_dir in app_dirs:
        try:
            app_num = int(app_dir.name.replace("app", ""))
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
    """Get all apps across all AI models."""
    all_apps = []
    for model in AI_MODELS:
        model_apps = get_apps_for_model(model.name)
        all_apps.extend(model_apps)
    return all_apps

# Create global instance of SystemStatus
system_status = SystemStatus()

# Routes
@app.route('/')
@error_handler
def index():
    """Home page showing all apps and their statuses."""
    apps = get_all_apps()
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
    """API endpoint to get system status."""
    # Run the asynchronous task in an event loop
    status = asyncio.run(system_status.get_status())
    return jsonify(status)


@app.route('/api/model-info')
@error_handler
def get_model_info():
    """API endpoint to get information about all models."""
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
    """View logs for a specific app."""
    container_prefix = f"{model.lower()}_app{app_num}"
    try:
        logs = {
            service: subprocess.run(
                ["docker", "logs", f"{container_prefix}_{service}", "--tail=100"],
                capture_output=True,
                text=True,
                check=True
            ).stdout for service in ['backend', 'frontend']
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
    """Get status of both containers for an app using batch processing."""
    container_prefix = f"{model.lower()}_app{app_num}"
    container_names = [
        f"{container_prefix}_backend",
        f"{container_prefix}_frontend"
    ]
    
    status = batch_container_status(container_names)
    return jsonify({
        "backend": status[f"{container_prefix}_backend"],
        "frontend": status[f"{container_prefix}_frontend"]
    })

@app.route('/build/<string:model>/<int:app_num>')
@error_handler
def build(model: str, app_num: int):
    """Build Docker images for a specific app."""
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
    """Start the specified app."""
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
    """Stop the specified app."""
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

@app.route('/open/backend/<string:model>/<int:app_num>')
@error_handler
def open_backend(model: str, app_num: int):
    """Open backend URL."""
    apps = get_all_apps()
    app = next((app for app in apps if app["model"] == model and app["app_num"] == app_num), None)
    return redirect(app["backend_url"]) if app else ("App not found", 404)

@app.route('/open/frontend/<string:model>/<int:app_num>')
@error_handler
def open_frontend(model: str, app_num: int):
    """Open frontend URL."""
    apps = get_all_apps()
    app = next((app for app in apps if app["model"] == model and app["app_num"] == app_num), None)
    return redirect(app["frontend_url"]) if app else ("App not found", 404)

@app.route('/reload/<string:model>/<int:app_num>')
@error_handler
def reload_app(model: str, app_num: int):
    """Reload the specified app."""
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

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(error)}")
    return render_template('500.html'), 500

def is_port_available(port: int) -> bool:
    """Check if a port is available for use."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"publish={port}", "--format", "{{.Ports}}"],
            capture_output=True,
            text=True,
            check=True
        )
        return not bool(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        logger.error(f"Error checking port availability: {str(e)}")
        return False

def verify_docker_compose(app_dir: Path) -> bool:
    """Verify that the docker-compose.yml file exists and is valid."""
    try:
        compose_file = app_dir / "docker-compose.yml"
        if not compose_file.exists():
            logger.error(f"docker-compose.yml not found in {app_dir}")
            return False
            
        result = subprocess.run(
            ["docker-compose", "config", "-q"],
            cwd=app_dir,
            capture_output=True,
            check=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Invalid docker-compose configuration in {app_dir}: {str(e)}")
        return False

def cleanup_containers():
    """Clean up stopped containers that are older than 24 hours."""
    try:
        subprocess.run(
            ["docker", "container", "prune", "-f", "--filter", "until=24h"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Error cleaning up containers: {str(e)}")

def health_check() -> bool:
    """Perform a health check of the management system."""
    try:
        # Check if Docker daemon is running
        docker_status = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            check=True
        )
        
        # Check disk space on Windows using wmic
        if os.name == 'nt':  # Windows systems
            df = subprocess.run(
                ["wmic", "logicaldisk", "get", "size,freespace,caption"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse the output
            lines = df.stdout.strip().split('\n')[1:]  # Skip header
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
                                    logger.warning(f"Disk usage critical: {parts[0]} is at {usage_percent:.1f}%")
                                    return False
                        except (IndexError, ValueError):
                            continue
        else:  # Unix/Linux systems
            df = subprocess.run(
                ["df", "-h"],
                capture_output=True,
                text=True,
                check=True
            )
            
            for line in df.stdout.split('\n')[1:]:
                if line:
                    fields = line.split()
                    if len(fields) >= 5:
                        usage = int(fields[4].rstrip('%'))
                        if usage > 90:
                            logger.warning(f"Disk usage critical: {fields[5]} is at {usage}%")
                            return False
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Health check failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in health check: {str(e)}")
        return False

@app.before_request
def before_request():
    """Perform operations before each request."""
    # Perform cleanup operations periodically
    if random.random() < 0.01:  # 1% chance to run cleanup
        cleanup_containers()

@app.after_request
def after_request(response):
    """Perform operations after each request."""
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

if __name__ == '__main__':
    app.wsgi_app = ProxyFix(app.wsgi_app)
    logger.info("Starting AI Model Management System")
    
    try:
        health_status = health_check()
        if not health_status:
            logger.warning("System health check failed - starting anyway with reduced functionality")
    except Exception as e:
        logger.error(f"Health check error: {str(e)} - continuing startup")
    
    import random  # For cleanup probability in before_request
    
    app.run(
        host='0.0.0.0' if os.getenv('FLASK_ENV') == 'production' else '127.0.0.1',
        port=int(os.getenv('PORT', 5050)),
        debug=Config.DEBUG
    )