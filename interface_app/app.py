from flask import Flask, render_template, redirect, url_for
import os
import subprocess
from pathlib import Path

app = Flask(__name__)

# Define range and increment for port allocation
BACKEND_BASE_PORT = 5002
FRONTEND_BASE_PORT = 5171
PORT_INCREMENT = 2

# Generate app metadata for 20 apps with dynamic port assignments
apps = [{
    "name": f"App {i}",
    "backend_port": BACKEND_BASE_PORT + (i - 1) * PORT_INCREMENT,
    "frontend_port": FRONTEND_BASE_PORT + (i - 1) * PORT_INCREMENT,
    "app_num": i,
    "backend_url": f"http://localhost:{BACKEND_BASE_PORT + (i - 1) * PORT_INCREMENT}",
    "frontend_url": f"http://localhost:{FRONTEND_BASE_PORT + (i - 1) * PORT_INCREMENT}"
} for i in range(1, 21)]


@app.route('/')
def index():
    """
    Home page showing all apps and their statuses.
    """
    for app_info in apps:
        app_info["backend_status"] = is_service_running(app_info["backend_port"])
        app_info["frontend_status"] = is_service_running(app_info["frontend_port"])
    return render_template('index.html', apps=apps)


@app.route('/open/backend/<int:app_num>')
def open_backend(app_num):
    """
    Redirects to the backend URL of the specified app.
    """
    app = next((app for app in apps if app["app_num"] == app_num), None)
    return redirect(app["backend_url"]) if app else ("App not found", 404)


@app.route('/open/frontend/<int:app_num>')
def open_frontend(app_num):
    """
    Redirects to the frontend URL of the specified app.
    """
    app = next((app for app in apps if app["app_num"] == app_num), None)
    return redirect(app["frontend_url"]) if app else ("App not found", 404)


def build_app(app_num: int) -> bool:
    """
    Builds Docker images for the backend and frontend of a specific app.
    """
    try:
        app_dir = Path(f"ChatGPT/flask_apps/app{app_num}")
        if not app_dir.exists():
            return False

        # Build backend
        backend_dir = app_dir / "backend"
        subprocess.run(
            ["docker", "build", "-t", f"app{app_num}-backend", str(backend_dir)],
            check=True
        )

        # Build frontend
        frontend_dir = app_dir / "frontend"
        subprocess.run(
            ["docker", "build", "-t", f"app{app_num}-frontend", str(frontend_dir)],
            check=True
        )

        return True
    except subprocess.CalledProcessError:
        return False


@app.route('/build/<int:app_num>')
def build(app_num):
    """
    Triggers the build process for a specific app.
    """
    if build_app(app_num):
        return redirect(url_for('index'))
    return "Build failed", 500


@app.route('/start/<int:app_num>')
def start_app(app_num):
    """
    Starts the specified app using Docker Compose.
    """
    app_dir = Path(f"ChatGPT/flask_apps/app{app_num}")
    try:
        subprocess.run(
            ["docker-compose", "up", "-d"],
            cwd=app_dir,
            check=True
        )
    except subprocess.CalledProcessError:
        return "Failed to start the app", 500
    return redirect(url_for('index'))


@app.route('/stop/<int:app_num>')
def stop_app(app_num):
    """
    Stops the specified app using Docker Compose.
    """
    app_dir = Path(f"ChatGPT/flask_apps/app{app_num}")
    try:
        subprocess.run(
            ["docker-compose", "down"],
            cwd=app_dir,
            check=True
        )
    except subprocess.CalledProcessError:
        return "Failed to stop the app", 500
    return redirect(url_for('index'))


def is_service_running(port: int) -> bool:
    """
    Checks if a service is running on the specified Docker port.
    """
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
