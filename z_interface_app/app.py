from flask import Flask, render_template, redirect, url_for, jsonify, abort
import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional
import datetime
import logging
from dataclasses import dataclass
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

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

class PortManager:
    """Manages port allocation for frontend and backend services."""
    
    BASE_BACKEND_PORT = 5001
    BASE_FRONTEND_PORT = 5501
    PORTS_PER_APP = 2
    BUFFER_PORTS = 5
    APPS_PER_MODEL = 20

    @classmethod
    def get_port_range(cls, model_idx: int) -> Dict[str, Dict[str, int]]:
        """
        Calculate port ranges for a model based on its index.
        
        Args:
            model_idx (int): Index of the AI model
            
        Returns:
            Dict containing port ranges for backend and frontend services
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
        Get specific ports for an app within a model.
        
        Args:
            model_idx (int): Index of the AI model
            app_num (int): Application number
            
        Returns:
            Dict containing backend and frontend ports
        """
        ranges = cls.get_port_range(model_idx)
        return {
            'backend': ranges['backend']['start'] + (app_num - 1) * 2,
            'frontend': ranges['frontend']['start'] + (app_num - 1) * 2
        }

class DockerManager:
    """Manages Docker container operations."""
    
    @staticmethod
    def get_container_logs(container_prefix: str, tail: int = 100) -> Dict[str, str]:
        """
        Retrieve logs from both frontend and backend containers.
        
        Args:
            container_prefix (str): Prefix for the container name
            tail (int): Number of log lines to retrieve
            
        Returns:
            Dict containing logs for both services
        """
        logs = {}
        for service in ['backend', 'frontend']:
            try:
                result = subprocess.run(
                    ["docker", "logs", f"{container_prefix}_{service}", f"--tail={tail}"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                logs[service] = result.stdout
            except subprocess.CalledProcessError as e:
                logger.error(f"Error getting logs for {container_prefix}_{service}: {str(e)}")
                logs[service] = f"Error retrieving logs: {str(e)}"
        return logs

    @staticmethod
    def get_container_status(container_name: str) -> Dict:
        """
        Get detailed status of a container.
        
        Args:
            container_name (str): Name of the container
            
        Returns:
            Dict containing container status information
        """
        try:
            result = subprocess.run(
                ["docker", "inspect", container_name],
                capture_output=True,
                text=True,
                check=True
            )
            container_info = json.loads(result.stdout)[0]
            return {
                "status": container_info["State"]["Status"],
                "running": container_info["State"]["Running"],
                "started_at": container_info["State"]["StartedAt"],
                "health": container_info["State"].get("Health", {}).get("Status", "N/A")
            }
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error getting container status for {container_name}: {str(e)}")
            return {
                "status": "not_found",
                "running": False,
                "started_at": None,
                "health": "N/A",
                "error": str(e)
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

# Application helper functions
def get_apps_for_model(model_name: str) -> List[Dict]:
    """
    Generate app metadata for a specific AI model.
    
    Args:
        model_name (str): Name of the AI model
        
    Returns:
        List of dictionaries containing app information
    """
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
    """
    Get all apps across all AI models.
    
    Returns:
        List of dictionaries containing all app information
    """
    all_apps = []
    for model in AI_MODELS:
        model_apps = get_apps_for_model(model.name)
        all_apps.extend(model_apps)
    return all_apps

# Routes
@app.route('/')
@error_handler
def index():
    """Home page showing all apps and their statuses."""
    apps = get_all_apps()
    return render_template('index.html', apps=apps, models=AI_MODELS)

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
    logs = DockerManager.get_container_logs(container_prefix)
    return render_template('logs.html', logs=logs, model=model, app_num=app_num)

@app.route('/api/container/<string:model>/<int:app_num>/status')
@error_handler
def container_status(model: str, app_num: int):
    """Get status of both containers for an app."""
    container_prefix = f"{model.lower()}_app{app_num}"
    return jsonify({
        "backend": DockerManager.get_container_status(f"{container_prefix}_backend"),
        "frontend": DockerManager.get_container_status(f"{container_prefix}_frontend")
    })

# Docker management routes
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

if __name__ == '__main__':
    app.run(debug=Config.DEBUG, port=5050)