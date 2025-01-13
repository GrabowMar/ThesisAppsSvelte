from flask import Flask, render_template, redirect, url_for, jsonify
import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional
import datetime

app = Flask(__name__)

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
    BASE_BACKEND_PORT = 5001
    BASE_FRONTEND_PORT = 5501  # Moved frontend ports to separate range
    PORTS_PER_APP = 2
    BUFFER_PORTS = 5
    APPS_PER_MODEL = 20

    @classmethod
    def get_port_range(cls, model_idx: int) -> Dict[str, Dict[str, int]]:
        """Calculate port ranges for a model based on its index"""
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
        """Get specific ports for an app within a model"""
        ranges = cls.get_port_range(model_idx)
        return {
            'backend': ranges['backend']['start'] + (app_num - 1) * 2,
            'frontend': ranges['frontend']['start'] + (app_num - 1) * 2
        }

def get_apps_for_model(model_name: str) -> List[Dict]:
    """Generate app metadata for a specific AI model"""
    base_path = Path(f"{model_name}/flask_apps")
    if not base_path.exists():
        return []
    
    model_idx = next((i for i, m in enumerate(AI_MODELS) if m['name'] == model_name), 0)
    model_color = next((m['color'] for m in AI_MODELS if m['name'] == model_name), "#666666")
    
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
        except ValueError:
            continue
            
    return apps

def get_all_apps() -> List[Dict]:
    """Get all apps across all AI models"""
    all_apps = []
    for model in AI_MODELS:
        model_apps = get_apps_for_model(model['name'])
        all_apps.extend(model_apps)
    return all_apps

def get_container_logs(container_prefix: str, tail: int = 100) -> Dict[str, str]:
    """Get logs from both frontend and backend containers"""
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
        except subprocess.CalledProcessError:
            logs[service] = "Error retrieving logs"
    return logs

def get_container_status(container_name: str) -> Dict:
    """Get detailed status of a container"""
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
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
        return {"status": "not_found", "running": False, "started_at": None, "health": "N/A"}

@app.route('/')
def index():
    """Home page showing all apps and their statuses"""
    apps = get_all_apps()
    for app_info in apps:
        app_info["backend_status"] = is_service_running(app_info["backend_port"])
        app_info["frontend_status"] = is_service_running(app_info["frontend_port"])
    return render_template('index.html', apps=apps, models=AI_MODELS)

@app.route('/api/model-info')
def get_model_info():
    """API endpoint to get information about all models"""
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

@app.route('/logs/<string:model>/<int:app_num>')
def view_logs(model, app_num):
    """View logs for a specific app"""
    container_prefix = f"{model.lower()}_app{app_num}"
    logs = get_container_logs(container_prefix)
    return render_template('logs.html', logs=logs, model=model, app_num=app_num)

@app.route('/api/container/<string:model>/<int:app_num>/status')
def container_status(model, app_num):
    """Get status of both containers for an app"""
    container_prefix = f"{model.lower()}_app{app_num}"
    return jsonify({
        "backend": get_container_status(f"{container_prefix}_backend"),
        "frontend": get_container_status(f"{container_prefix}_frontend")
    })

@app.route('/build/<string:model>/<int:app_num>')
def build(model, app_num):
    """Build Docker images for a specific app"""
    app_dir = Path(f"{model}/flask_apps/app{app_num}")
    try:
        subprocess.run(
            ["docker-compose", "build"],
            cwd=app_dir,
            check=True
        )
        return redirect(url_for('index'))
    except subprocess.CalledProcessError:
        return f"Build failed for {model} app {app_num}", 500

@app.route('/start/<string:model>/<int:app_num>')
def start_app(model, app_num):
    """Start the specified app"""
    app_dir = Path(f"{model}/flask_apps/app{app_num}")
    try:
        subprocess.run(
            ["docker-compose", "up", "-d"],
            cwd=app_dir,
            check=True
        )
        return redirect(url_for('index'))
    except subprocess.CalledProcessError:
        return f"Failed to start {model} app {app_num}", 500

@app.route('/stop/<string:model>/<int:app_num>')
def stop_app(model, app_num):
    """Stop the specified app"""
    app_dir = Path(f"{model}/flask_apps/app{app_num}")
    try:
        subprocess.run(
            ["docker-compose", "down"],
            cwd=app_dir,
            check=True
        )
        return redirect(url_for('index'))
    except subprocess.CalledProcessError:
        return f"Failed to stop {model} app {app_num}", 500

@app.route('/reload/<string:model>/<int:app_num>')
def reload_app(model, app_num):
    """Reload the specified app"""
    app_dir = Path(f"{model}/flask_apps/app{app_num}")
    try:
        subprocess.run(
            ["docker-compose", "restart"],
            cwd=app_dir,
            check=True
        )
        return redirect(url_for('index'))
    except subprocess.CalledProcessError:
        return f"Failed to reload {model} app {app_num}", 500

@app.route('/open/backend/<string:model>/<int:app_num>')
def open_backend(model, app_num):
    """Open backend URL"""
    apps = get_all_apps()
    app = next((app for app in apps if app["model"] == model and app["app_num"] == app_num), None)
    return redirect(app["backend_url"]) if app else ("App not found", 404)

@app.route('/open/frontend/<string:model>/<int:app_num>')
def open_frontend(model, app_num):
    """Open frontend URL"""
    apps = get_all_apps()
    app = next((app for app in apps if app["model"] == model and app["app_num"] == app_num), None)
    return redirect(app["frontend_url"]) if app else ("App not found", 404)

def is_service_running(port: int) -> bool:
    """Check if a service is running on the specified port"""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"publish={port}", "--format", "{{.Ports}}"],
            capture_output=True,
            text=True,
            check=True
        )
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        return False

if __name__ == '__main__':
    app.run(debug=True, port=5050)