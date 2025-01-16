from flask import Flask, render_template, redirect, url_for, jsonify, request
import docker
from docker.errors import DockerException
import os
from pathlib import Path
from typing import Dict, List, Optional
from functools import lru_cache
import datetime
from concurrent.futures import ThreadPoolExecutor
import yaml
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Initialize Docker client
docker_client = docker.from_env()

# Define models and their properties
AI_MODELS = [
    {"name": "ChatGPT", "color": "#10a37f"},
    {"name": "ChatGPTo1", "color": "#0ea47f"},
    {"name": "ClaudeSonnet", "color": "#7b2bf9"},
    {"name": "CodeLlama", "color": "#f97316"},
    {"name": "Gemini", "color": "#1a73e8"},
    {"name": "Grok", "color": "#ff4d4f"},
    {"name": "Mixtral", "color": "#9333ea"}
]

class PortManager:
    """Manages port allocation for applications"""
    BASE_BACKEND_PORT = 5001
    BASE_FRONTEND_PORT = 5501
    PORTS_PER_APP = 2
    BUFFER_PORTS = 5
    APPS_PER_MODEL = 20
    
    @classmethod
    @lru_cache(maxsize=128)
    def get_port_range(cls, model_idx: int) -> Dict[str, Dict[str, int]]:
        """Calculate port ranges for a model based on its index with caching"""
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
    @lru_cache(maxsize=256)
    def get_app_ports(cls, model_idx: int, app_num: int) -> Dict[str, int]:
        """Get specific ports for an app within a model with caching"""
        ranges = cls.get_port_range(model_idx)
        return {
            'backend': ranges['backend']['start'] + (app_num - 1) * 2,
            'frontend': ranges['frontend']['start'] + (app_num - 1) * 2
        }

class DockerManager:
    """Manages Docker container operations"""
    def __init__(self):
        self.client = docker_client
        self.executor = ThreadPoolExecutor(max_workers=4)

    def get_container_logs(self, container_prefix: str, tail: int = 100) -> Dict[str, str]:
        """Get logs from both frontend and backend containers using Docker SDK"""
        logs = {}
        for service in ['backend', 'frontend']:
            try:
                container = self.client.containers.get(f"{container_prefix}_{service}")
                logs[service] = container.logs(tail=tail, timestamps=True).decode('utf-8')
            except docker.errors.NotFound:
                logs[service] = "Container not found"
            except DockerException as e:
                logs[service] = f"Error retrieving logs: {str(e)}"
        return logs

    def get_container_status(self, container_name: str) -> Dict:
        """Get detailed status of a container using Docker SDK"""
        try:
            container = self.client.containers.get(container_name)
            inspection = container.attrs
            return {
                "status": inspection["State"]["Status"],
                "running": inspection["State"]["Running"],
                "started_at": inspection["State"]["StartedAt"],
                "health": inspection["State"].get("Health", {}).get("Status", "N/A"),
                "memory_usage": self._get_container_memory_usage(container),
                "cpu_usage": self._get_container_cpu_usage(container)
            }
        except docker.errors.NotFound:
            return {
                "status": "not_found",
                "running": False,
                "started_at": None,
                "health": "N/A",
                "memory_usage": 0,
                "cpu_usage": 0
            }

    def _get_container_memory_usage(self, container) -> float:
        """Get container memory usage in MB"""
        try:
            stats = container.stats(stream=False)
            return round(stats["memory_stats"]["usage"] / 1024 / 1024, 2)
        except:
            return 0.0

    def _get_container_cpu_usage(self, container) -> float:
        """Get container CPU usage percentage"""
        try:
            stats = container.stats(stream=False)
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                       stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                          stats["precpu_stats"]["system_cpu_usage"]
            num_cpus = len(stats["cpu_stats"]["cpu_usage"]["percpu_usage"])
            return round((cpu_delta / system_delta) * num_cpus * 100.0, 2)
        except:
            return 0.0

    def build_image(self, build_context: Path, dockerfile: str, tag: str) -> bool:
        """Build a Docker image"""
        try:
            self.client.images.build(
                path=str(build_context),
                dockerfile=dockerfile,
                tag=tag,
                rm=True
            )
            return True
        except DockerException as e:
            logger.error(f"Failed to build image {tag}: {str(e)}")
            return False

    def build_compose_services(self, app_dir: Path) -> bool:
        """Build all services defined in a docker-compose file"""
        try:
            compose_file = app_dir / "docker-compose.yml"
            if not compose_file.exists():
                logger.error(f"docker-compose.yml not found in {app_dir}")
                return False

            with open(compose_file, "r") as f:
                compose = yaml.safe_load(f)

            success = True
            for service_name, service_config in compose["services"].items():
                if "build" not in service_config:
                    continue

                build_context = app_dir
                dockerfile = "Dockerfile"

                if isinstance(service_config["build"], dict):
                    build_context = app_dir / service_config["build"].get("context", ".")
                    dockerfile = service_config["build"].get("dockerfile", "Dockerfile")
                elif isinstance(service_config["build"], str):
                    build_context = app_dir / service_config["build"]

                image_tag = f"{app_dir.parent.name.lower()}_{app_dir.name}_{service_name}:latest"
                if not self.build_image(build_context, dockerfile, image_tag):
                    success = False
                    continue

                service_config["image"] = image_tag

            if success:
                with open(compose_file, "w") as f:
                    yaml.dump(compose, f)

            return success

        except Exception as e:
            logger.error(f"Failed to build compose services: {str(e)}")
            return False

    def compose_operation(self, operation: str, app_dir: Path) -> bool:
        """Execute docker-compose operations using Docker SDK"""
        try:
            compose_file = app_dir / "docker-compose.yml"
            if not compose_file.exists():
                logger.error(f"docker-compose.yml not found in {app_dir}")
                return False

            with open(compose_file, "r") as f:
                compose = yaml.safe_load(f)

            project_name = app_dir.name

            if operation == "up":
                for service_name, service_config in compose["services"].items():
                    container_name = f"{project_name}_{service_name}"
                    try:
                        self.client.containers.get(container_name).remove(force=True)
                    except:
                        pass

                    try:
                        self.client.containers.run(
                            service_config["image"],
                            detach=True,
                            name=container_name,
                            ports=service_config.get("ports", {}),
                            environment=service_config.get("environment", {}),
                        )
                    except Exception as e:
                        logger.error(f"Failed to start {container_name}: {str(e)}")
                        return False

            elif operation == "down":
                for service_name in compose["services"].keys():
                    container_name = f"{project_name}_{service_name}"
                    try:
                        container = self.client.containers.get(container_name)
                        container.stop()
                        container.remove()
                    except docker.errors.NotFound:
                        continue
                    except Exception as e:
                        logger.error(f"Failed to stop {container_name}: {str(e)}")
                        return False

            return True
        except Exception as e:
            logger.error(f"Docker operation failed: {str(e)}")
            return False

    def is_service_running(self, port: int) -> bool:
        """Check if a service is running on the specified port using Docker SDK"""
        try:
            containers = self.client.containers.list(
                filters={
                    "status": "running",
                    "expose": [str(port)]
                }
            )
            return bool(containers)
        except DockerException:
            return False

def get_apps_for_model(model_name: str) -> List[Dict]:
    """Generate app metadata for a specific AI model"""
    base_path = Path(f"{model_name}/flask_apps")
    if not base_path.exists():
        return []
    
    model_idx = next((i for i, m in enumerate(AI_MODELS) if m['name'] == model_name), 0)
    model_color = next((m['color'] for m in AI_MODELS if m['name'] == model_name), "#666666")
    
    apps = []
    try:
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
                
    except Exception as e:
        logger.error(f"Error getting apps for model {model_name}: {str(e)}")
        
    return apps

@lru_cache(maxsize=32)
def get_all_apps() -> List[Dict]:
    """Get all apps across all AI models"""
    all_apps = []
    for model in AI_MODELS:
        model_apps = get_apps_for_model(model['name'])
        all_apps.extend(model_apps)
    return all_apps

# Initialize Docker manager
docker_manager = DockerManager()

# Flask routes
@app.route('/')
def index():
    """Home page showing all apps and their statuses"""
    try:
        apps = get_all_apps()
        
        def check_app_status(app_info):
            try:
                app_info["backend_status"] = docker_manager.is_service_running(app_info["backend_port"])
                app_info["frontend_status"] = docker_manager.is_service_running(app_info["frontend_port"])
                return app_info
            except Exception as e:
                logger.error(f"Error checking app status: {str(e)}")
                app_info["backend_status"] = False
                app_info["frontend_status"] = False
                return app_info
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            apps = list(executor.map(check_app_status, apps))
        
        return render_template('index.html', apps=apps, models=AI_MODELS)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return "Internal Server Error", 500

@app.route('/logs/<string:model>/<int:app_num>')
def view_logs(model, app_num):
    """View logs for a specific app - supports both HTML and JSON responses"""
    try:
        container_prefix = f"{model.lower()}_app{app_num}"
        logs = docker_manager.get_container_logs(container_prefix)
        
        if request.headers.get('Accept') == 'application/json' or request.args.get('format') == 'json':
            return jsonify(logs)
        
        return render_template('logs.html', logs=logs, model=model, app_num=app_num)
    except Exception as e:
        logger.error(f"Error viewing logs: {str(e)}")
        return "Internal Server Error", 500

@app.route('/build/<string:model>/<int:app_num>')
def build(model, app_num):
    """Build Docker images for a specific app"""
    try:
        app_dir = Path(f"{model}/flask_apps/app{app_num}")
        if not app_dir.exists():
            return f"App directory not found for {model} app {app_num}", 404
            
        if docker_manager.build_compose_services(app_dir):
            return redirect(url_for('index'))
        else:
            return f"Failed to build {model} app {app_num}", 500
    except Exception as e:
        logger.error(f"Error building app: {str(e)}")
        return "Internal Server Error", 500

@app.route('/api/model-info')
@lru_cache(maxsize=32)
def get_model_info():
    """Cached API endpoint to get information about all models"""
    try:
        model_info = []
        for idx, model in enumerate(AI_MODELS):
            port_range = PortManager.get_port_range(idx)
            model_info.append({
                "name": model['name'],
                "color": model['color'],
                "ports": port_range,
                "total_apps": len(get_apps_for_model(model['name']))
            })
        return jsonify(model_info)
    except Exception as e:
        logger.error(f"Error fetching model info: {str(e)}")
        return jsonify([])

@app.route('/api/container/<string:model>/<int:app_num>/status')
def container_status(model, app_num):
    """Get status of both containers for an app"""
    try:
        container_prefix = f"{model.lower()}_app{app_num}"
        return jsonify({
            "backend": docker_manager.get_container_status(f"{container_prefix}_backend"),
            "frontend": docker_manager.get_container_status(f"{container_prefix}_frontend")
        })
    except Exception as e:
        logger.error(f"Error getting container status: {str(e)}")
        return "Internal Server Error", 500

@app.route('/start/<string:model>/<int:app_num>')
def start_app(model, app_num):
    """Start the specified app"""
    try:
        app_dir = Path(f"{model}/flask_apps/app{app_num}")
        if not app_dir.exists():
            return f"App directory not found for {model} app {app_num}", 404

        success = docker_manager.compose_operation("up", app_dir)
        if success:
            logger.info(f"Successfully started {model} app {app_num}")
            return redirect(url_for('index'))
        else:
            logger.error(f"Failed to start {model} app {app_num}")
            return f"Failed to start {model} app {app_num}", 500
    except Exception as e:
        logger.error(f"Error starting app: {str(e)}")
        return "Internal Server Error", 500

@app.route('/stop/<string:model>/<int:app_num>')
def stop_app(model, app_num):
    """Stop the specified app"""
    try:
        app_dir = Path(f"{model}/flask_apps/app{app_num}")
        if not app_dir.exists():
            return f"App directory not found for {model} app {app_num}", 404

        success = docker_manager.compose_operation("down", app_dir)
        if success:
            logger.info(f"Successfully stopped {model} app {app_num}")
            return redirect(url_for('index'))
        else:
            logger.error(f"Failed to stop {model} app {app_num}")
            return f"Failed to stop {model} app {app_num}", 500
    except Exception as e:
        logger.error(f"Error stopping app: {str(e)}")
        return "Internal Server Error", 500

@app.route('/reload/<string:model>/<int:app_num>')
def reload_app(model, app_num):
    """Reload the specified app"""
    try:
        app_dir = Path(f"{model}/flask_apps/app{app_num}")
        if not app_dir.exists():
            return f"App directory not found for {model} app {app_num}", 404

        # Stop containers
        if not docker_manager.compose_operation("down", app_dir):
            return f"Failed to stop {model} app {app_num} during reload", 500

        # Start containers
        if not docker_manager.compose_operation("up", app_dir):
            return f"Failed to restart {model} app {app_num} during reload", 500

        logger.info(f"Successfully reloaded {model} app {app_num}")
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error reloading app: {str(e)}")
        return "Internal Server Error", 500

@app.route('/open/backend/<string:model>/<int:app_num>')
def open_backend(model, app_num):
    """Open backend URL"""
    try:
        apps = get_all_apps()
        app = next((app for app in apps if app["model"] == model and app["app_num"] == app_num), None)
        if app:
            return redirect(app["backend_url"])
        return "App not found", 404
    except Exception as e:
        logger.error(f"Error opening backend URL: {str(e)}")
        return "Internal Server Error", 500

@app.route('/open/frontend/<string:model>/<int:app_num>')
def open_frontend(model, app_num):
    """Open frontend URL"""
    try:
        apps = get_all_apps()
        app = next((app for app in apps if app["model"] == model and app["app_num"] == app_num), None)
        if app:
            return redirect(app["frontend_url"])
        return "App not found", 404
    except Exception as e:
        logger.error(f"Error opening frontend URL: {str(e)}")
        return "Internal Server Error", 500

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return render_template('500.html'), 500

# Create templates directory if it doesn't exist
templates_dir = Path('templates')
templates_dir.mkdir(exist_ok=True)

if __name__ == '__main__':
    # Ensure required directories exist
    for model in AI_MODELS:
        model_dir = Path(f"{model['name']}/flask_apps")
        model_dir.mkdir(parents=True, exist_ok=True)

    # Run the application
    app.run(debug=True, port=5050, host='0.0.0.0')