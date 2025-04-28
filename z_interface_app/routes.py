"""
Route handlers for the AI Model Management System.
"""

# =============================================================================
# Standard Library Imports
# =============================================================================
import http
import json
import subprocess
import threading
import time
import traceback
from dataclasses import asdict
from datetime import datetime
from enum import Enum # Added Enum import
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from zap_scanner import CodeContext, ZapVulnerability

# =============================================================================
# Third-Party Imports
# =============================================================================
try:
    import psutil
except ImportError:
    psutil = None

from flask import (
    Blueprint, Response, current_app, flash, jsonify,
    redirect, render_template, request, url_for, send_file
)
from werkzeug.exceptions import BadRequest, HTTPException, InternalServerError # Added InternalServerError

# =============================================================================
# Custom Module Imports
# =============================================================================
from logging_service import create_logger_for_component
from services import (
    DockerManager, ScanManager, SystemHealthMonitor, call_ai_service,
    create_scanner
)
# Removed unused: APIResponse (using APIResponse from utils now)
# Removed unused: CustomJSONEncoder (implicitly used by jsonify)
from utils import (
    AIModel, AI_MODELS, APIResponse,
    _AJAX_REQUEST_HEADER_NAME, _AJAX_REQUEST_HEADER_VALUE,
    ajax_compatible, get_all_apps, get_app_container_statuses,
    get_app_directory, get_app_info, get_apps_for_model,
    get_container_names, get_model_index, get_scan_manager,
    handle_docker_action, process_security_analysis, stop_zap_scanners,
    verify_container_health, PortManager # Added PortManager assuming it's in utils
)


# =============================================================================
# Scan State Enum Definition
# =============================================================================
class ScanState(Enum):
    """Defines the possible states for a ZAP scan."""
    NOT_RUN = "Not Run"         # Scan has never been initiated for this app
    STARTING = "Starting"       # Scan thread initiated, ZAP setup in progress
    SPIDERING = "Spidering"     # Spidering phase active (update ScanManager to set this)
    SCANNING = "Scanning"       # Active scanning phase active (update ScanManager to set this)
    COMPLETE = "Complete"       # Scan finished successfully
    FAILED = "Failed"           # Scan finished, but reported failure (e.g., ZAP error during scan)
    ERROR = "Error"             # Scan couldn't start/run due to setup/thread error (e.g., DirNotFound)
    STOPPED = "Stopped"         # Scan was explicitly stopped by user
    # Add other states like Initializing, Processing, etc. if needed by ScanManager logic


# =============================================================================
# Blueprint Definitions
# =============================================================================
main_bp = Blueprint("main", __name__)
api_bp = Blueprint("api", __name__, url_prefix="/api")
analysis_bp = Blueprint("analysis", __name__, url_prefix="/analysis") # Added url_prefix
performance_bp = Blueprint("performance", __name__, url_prefix="/performance")
gpt4all_bp = Blueprint("gpt4all", __name__, url_prefix="/gpt4all")
zap_bp = Blueprint("zap", __name__, url_prefix="/zap")

# =============================================================================
# Route Loggers
# =============================================================================
main_route_logger = create_logger_for_component('routes.main')
api_logger = create_logger_for_component('routes.api')
zap_logger = create_logger_for_component('routes.zap')
perf_logger = create_logger_for_component('routes.performance')
security_logger = create_logger_for_component('routes.security')
gpt4all_logger = create_logger_for_component('routes.gpt4all')
client_error_logger = create_logger_for_component('client_errors')


# =============================================================================
# Main Routes
# =============================================================================
@main_bp.route("/")
@ajax_compatible
def index():
    """
    Main dashboard index page showing all apps and their statuses.

    Returns:
        Rendered index template with apps and models.
    """
    main_route_logger.info("Rendering main dashboard")

    docker_manager: DockerManager = current_app.config["docker_manager"]
    apps = get_all_apps() # This already logs

    main_route_logger.debug(f"Found {len(apps)} apps, fetching statuses...")
    start_time = time.time()
    for app_info in apps:
        try:
            statuses = get_app_container_statuses(app_info["model"], app_info["app_num"], docker_manager)
            app_info["backend_status"] = statuses.get("backend", {})
            app_info["frontend_status"] = statuses.get("frontend", {})
            if statuses.get("error"):
                main_route_logger.warning(f"Error getting status for {app_info['model']}/{app_info['app_num']}: {statuses['error']}")
                # Add error indication to app_info if needed by template
                app_info["status_error"] = statuses['error']
        except Exception as e:
            main_route_logger.exception(f"Unexpected error getting status for {app_info['model']}/{app_info['app_num']}: {e}")
            app_info["status_error"] = str(e)
            app_info["backend_status"] = {}
            app_info["frontend_status"] = {}

    duration = time.time() - start_time
    main_route_logger.debug(f"Status fetch for {len(apps)} apps took {duration:.2f} seconds.")

    # Add autorefresh_enabled based on config
    autorefresh_enabled = request.cookies.get('autorefresh', 'false') == 'true'
    main_route_logger.debug(f"Autorefresh setting: {autorefresh_enabled}")

    return render_template(
        "index.html",
        apps=apps,
        models=AI_MODELS,
        autorefresh_enabled=autorefresh_enabled
    )

@main_bp.route("/docker-logs/<string:model>/<int:app_num>")
@ajax_compatible
def view_docker_logs(model: str, app_num: int):
    """
    View Docker compose logs and individual container logs.

    Args:
        model: Model name.
        app_num: App number (1-based).

    Returns:
        Rendered template with Docker logs or redirect on error.
    """
    main_route_logger.info(f"Fetching Docker logs for {model}/app{app_num}")
    compose_logs = "Could not retrieve docker-compose logs."
    backend_logs = "Could not retrieve backend logs."
    frontend_logs = "Could not retrieve frontend logs."

    try:
        # Use helper to get validated app directory path
        app_dir = get_app_directory(current_app, model, app_num)

        try:
            main_route_logger.debug(f"Running 'docker-compose logs' in {app_dir}")
            result = subprocess.run(
                ["docker-compose", "logs", "--no-color", "--tail", "200"], # Added tail limit
                cwd=str(app_dir),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=20 # Increased timeout slightly
            )
            if result.returncode == 0:
                compose_logs = result.stdout or "No logs output from docker-compose."
            else:
                compose_logs = f"Error running docker-compose logs (Code {result.returncode}):\n{result.stderr or result.stdout}"
                main_route_logger.error(compose_logs)

        except FileNotFoundError:
            compose_logs = "`docker-compose` command not found."
            main_route_logger.exception(compose_logs)
        except subprocess.TimeoutExpired:
            compose_logs = "Timed out fetching docker-compose logs."
            main_route_logger.error(compose_logs)
        except Exception as sub_err:
            compose_logs = f"Error fetching docker-compose logs: {sub_err}"
            main_route_logger.exception(compose_logs)

        # Get individual container logs
        b_name, f_name = get_container_names(model, app_num) # Raises ValueError if model/app invalid
        docker_manager: DockerManager = current_app.config["docker_manager"]

        main_route_logger.debug(f"Fetching container logs for {b_name} and {f_name}")
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

    except FileNotFoundError as e:
        main_route_logger.error(f"App directory not found for {model}/app{app_num}: {e}")
        flash(f"Application directory not found: {e}", "error")
        return redirect(url_for("main.index"))
    except ValueError as e: # Catch errors from get_container_names
        main_route_logger.error(f"Invalid model/app for log view {model}/app{app_num}: {e}")
        flash(f"Invalid application specified: {e}", "error")
        return redirect(url_for("main.index"))
    except Exception as e:
        main_route_logger.exception(f"Generic error fetching logs for {model}/app{app_num}: {e}")
        flash(f"Error fetching logs: {str(e)}", "error")
        return redirect(url_for("main.index"))


@main_bp.route("/status/<string:model>/<int:app_num>")
@ajax_compatible # Decorator handles AJAX JSON response automatically
def check_app_status(model: str, app_num: int):
    """
    Check and return container status for an app.
    """
    main_route_logger.debug(f"Checking status for {model}/app{app_num}")
    docker_manager: DockerManager = current_app.config["docker_manager"]
    status = get_app_container_statuses(model, app_num, docker_manager)
    return status


@main_bp.route("/batch/<action>/<string:model>", methods=["POST"])
@ajax_compatible # Handles JSON response / errors
def batch_docker_action(action: str, model: str):
    """
    Perform batch Docker operations on all apps for a specific model.
    """
    main_route_logger.info(f"Batch action '{action}' requested for model '{model}'")

    valid_actions = ["start", "stop", "restart", "build", "rebuild", "health-check"]
    if action not in valid_actions:
        main_route_logger.warning(f"Invalid batch action requested: {action}")
        return APIResponse(
            success=False,
            error=f"Invalid action: {action}",
            code=http.HTTPStatus.BAD_REQUEST
        )

    apps = get_apps_for_model(model)
    if not apps:
        main_route_logger.warning(f"No apps found for model '{model}' for batch action '{action}'")
        return APIResponse(
            success=False,
            error=f"No apps found for model {model}",
            code=http.HTTPStatus.NOT_FOUND
        )

    main_route_logger.info(f"Processing batch '{action}' for {len(apps)} apps of model '{model}'")
    results = []
    docker_manager: Optional[DockerManager] = current_app.config.get("docker_manager")

    for app in apps:
        app_num = app["app_num"]
        result_entry = {"app_num": app_num, "success": False, "message": "Action Skipped"}
        try:
            if action == "health-check":
                if docker_manager:
                    healthy, message = verify_container_health(docker_manager, model, app_num)
                    result_entry["success"] = healthy
                    result_entry["message"] = message
                else:
                    result_entry["message"] = "Docker manager unavailable for health check."
            else:
                success, message = handle_docker_action(action, model, app_num)
                result_entry["success"] = success
                result_entry["message"] = message
        except Exception as e:
            main_route_logger.exception(f"Error during batch action '{action}' for {model}/app{app_num}: {e}")
            result_entry["message"] = f"Unexpected error: {str(e)}"
        results.append(result_entry)

    success_count = sum(1 for r in results if r["success"])
    status = "success" if success_count == len(results) else "partial" if success_count > 0 else "error"
    main_route_logger.info(f"Batch action '{action}' for '{model}' completed: {status} ({success_count}/{len(results)} succeeded)")

    return {
        "status": status,
        "total": len(results),
        "success_count": success_count,
        "failure_count": len(results) - success_count,
        "results": results
    }


@main_bp.route("/logs/<string:model>/<int:app_num>")
@ajax_compatible # Handles JSON response if needed, otherwise returns template
def view_logs(model: str, app_num: int):
    """
    View container logs for an app.
    """
    main_route_logger.info(f"Viewing container logs for {model}/app{app_num}")
    logs_data = {"backend": "Error retrieving logs.", "frontend": "Error retrieving logs."}
    try:
        docker_manager: DockerManager = current_app.config["docker_manager"]
        b_name, f_name = get_container_names(model, app_num)

        main_route_logger.debug(f"Fetching logs for containers: {b_name}, {f_name}")
        logs_data["backend"] = docker_manager.get_container_logs(b_name)
        logs_data["frontend"] = docker_manager.get_container_logs(f_name)

    except ValueError as e:
        main_route_logger.error(f"Invalid model/app for log view {model}/app{app_num}: {e}")
        flash(f"Invalid application specified: {e}", "error")
        if request.headers.get(_AJAX_REQUEST_HEADER_NAME) != _AJAX_REQUEST_HEADER_VALUE:
            return redirect(url_for("main.index"))
        else:
            raise BadRequest(f"Invalid application specified: {e}") from e
    except Exception as e:
        main_route_logger.exception(f"Error retrieving logs for {model}/app{app_num}: {e}")
        raise InternalServerError(f"Failed to retrieve logs: {e}") from e

    return render_template("logs.html", logs=logs_data, model=model, app_num=app_num)


@main_bp.route("/<action>/<string:model>/<int:app_num>", methods=["POST"])
@ajax_compatible # Handles JSON response / errors
def handle_docker_action_route(action: str, model: str, app_num: int):
    """
    Handle Docker action (start, stop, restart, build, rebuild) for an app via POST.
    """
    main_route_logger.info(f"Docker action '{action}' requested for {model}/app{app_num} via POST")

    try:
        success, message = handle_docker_action(action, model, app_num)

        response = APIResponse(
            success=success,
            message=message,
            code=http.HTTPStatus.OK if success else http.HTTPStatus.INTERNAL_SERVER_ERROR
        )

        if request.headers.get(_AJAX_REQUEST_HEADER_NAME) != _AJAX_REQUEST_HEADER_VALUE:
            flash(f"{'Success' if success else 'Error'}: {message[:500]}...", "success" if success else "error")
            return redirect(url_for("main.index"))
        else:
            return response

    except Exception as e:
        main_route_logger.exception(f"Unexpected error handling docker action '{action}' for {model}/app{app_num}: {e}")
        raise InternalServerError(f"Failed to execute action '{action}': {e}") from e


# =============================================================================
# API Routes (/api)
# =============================================================================
@api_bp.route("/system-info")
@ajax_compatible # Handles JSON response / errors
def system_info():
    """
    Get detailed system information for the dashboard.
    """
    api_logger.debug("System info requested")
    docker_manager: DockerManager = current_app.config["docker_manager"]
    system_health_metrics = {}
    docker_status = {"healthy": False, "client_available": False, "containers": {"running": 0, "stopped": 0, "total": 0}}
    app_stats = {"total": 0, "models": {}, "status": {"running": 0, "partial": 0, "stopped": 0}}

    # 1. Get basic system metrics
    if psutil:
        try:
            api_logger.debug("Getting system metrics using psutil")
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk_usage_root = psutil.disk_usage('/')

            system_health_metrics = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used": memory.used,
                "memory_total": memory.total,
                "disk_percent": disk_usage_root.percent,
                "disk_used": disk_usage_root.used,
                "disk_total": disk_usage_root.total,
                "uptime_seconds": int(time.time() - psutil.boot_time()),
            }
        except Exception as e:
            api_logger.exception(f"Failed to get psutil system metrics: {e}")
            system_health_metrics = {"error": "Failed to retrieve system metrics"}
    else:
        api_logger.warning("psutil not installed, cannot provide detailed system metrics.")
        system_health_metrics = {"error": "psutil not installed"}

    # 2. Get Docker status and container counts
    docker_status["client_available"] = bool(docker_manager and docker_manager.client)
    if docker_status["client_available"]:
        try:
            docker_status["healthy"] = SystemHealthMonitor.check_docker_connection(docker_manager.client)
            api_logger.debug("Getting container counts from Docker")
            containers = docker_manager.client.containers.list(all=True)
            docker_status["containers"] = {
                "running": sum(1 for c in containers if c.status == "running"),
                "stopped": sum(1 for c in containers if c.status != "running"),
                "total": len(containers)
            }
        except Exception as e:
            api_logger.exception(f"Error getting Docker info: {e}")
            docker_status["healthy"] = False
            docker_status["error"] = str(e)

    # 3. Get app overview stats
    try:
        apps = get_all_apps()
        app_stats["total"] = len(apps)
        app_stats["models"] = {model.name: 0 for model in AI_MODELS} # Ensure model.name here
        for app in apps:
            model_name = app["model"]
            if model_name in app_stats["models"]:
                app_stats["models"][model_name] += 1

        # Get app status counts (sampling)
        sample_size = 10
        api_logger.debug(f"Sampling app statuses for dashboard (sample size: {sample_size} apps)")
        sampled_apps = apps[:sample_size]
        running, partial, stopped = 0, 0, 0
        if docker_status["client_available"]:
            for app in sampled_apps:
                try:
                    statuses = get_app_container_statuses(app["model"], app["app_num"], docker_manager)
                    if statuses.get("error"): continue

                    backend_running = statuses.get("backend", {}).get("running", False)
                    frontend_running = statuses.get("frontend", {}).get("running", False)

                    if backend_running and frontend_running: running += 1
                    elif backend_running or frontend_running: partial += 1
                    else: stopped += 1
                except Exception as e:
                    api_logger.exception(f"Error getting status for sampled app {app['model']}/{app['app_num']}: {e}")

            if len(apps) > 0 and len(sampled_apps) > 0:
                scale_factor = len(apps) / len(sampled_apps)
                app_stats["status"]["running"] = int(running * scale_factor)
                app_stats["status"]["partial"] = int(partial * scale_factor)
                app_stats["status"]["stopped"] = app_stats["total"] - app_stats["status"]["running"] - app_stats["status"]["partial"]
            else:
                app_stats["status"]["stopped"] = app_stats["total"]
        else:
            app_stats["status"]["stopped"] = app_stats["total"]

    except Exception as e:
        api_logger.exception(f"Error calculating app stats: {e}")
        app_stats["error"] = str(e)


    # 4. Combine results
    return {
        "timestamp": datetime.now().isoformat(),
        "system": system_health_metrics,
        "docker": docker_status,
        "apps": app_stats
    }


@api_bp.route("/container/<string:model>/<int:app_num>/status")
@ajax_compatible # Handles JSON response
def container_status(model: str, app_num: int):
    """
    Get container status for a specific app.
    """
    api_logger.debug(f"Container status requested for {model}/app{app_num}")
    docker_manager: DockerManager = current_app.config["docker_manager"]
    status = get_app_container_statuses(model, app_num, docker_manager)
    return status


@api_bp.route("/debug/docker/<string:model>/<int:app_num>")
@ajax_compatible # Handles JSON response / errors
def debug_docker_environment(model: str, app_num: int):
    """
    Debug endpoint to inspect Docker environment for an app.
    """
    api_logger.info(f"Docker environment debug requested for {model}/app{app_num}")
    debug_info = {"error": None}
    try:
        app_dir = get_app_directory(current_app, model, app_num) # Raises FileNotFoundError if invalid
        debug_info["directory_exists"] = True
        debug_info["app_directory"] = str(app_dir)

        compose_file_path = None
        for filename in ["docker-compose.yml", "docker-compose.yaml"]:
            potential_path = app_dir / filename
            if potential_path.is_file():
                compose_file_path = potential_path
                break
        debug_info["compose_file_exists"] = bool(compose_file_path)
        debug_info["compose_file_path"] = str(compose_file_path) if compose_file_path else "Not Found"
        compose_content = ""
        if compose_file_path:
            try:
                compose_file_content = compose_file_path.read_text(encoding='utf-8', errors='replace')
                compose_content = compose_file_content[:1000] + ("..." if len(compose_file_content)>1000 else "")
            except Exception as read_err:
                compose_content = f"Error reading compose file: {read_err}"
        debug_info["compose_file_preview"] = compose_content

        try:
            api_logger.debug("Checking Docker version")
            docker_version = subprocess.run(
                ["docker", "--version"], capture_output=True, text=True,
                encoding='utf-8', errors='replace', check=True
            ).stdout.strip()
        except (FileNotFoundError, subprocess.CalledProcessError) as dv_err:
            docker_version = f"Error checking Docker version: {dv_err}"
            api_logger.error(docker_version)
        debug_info["docker_version"] = docker_version

        try:
            api_logger.debug("Checking Docker Compose version")
            try:
                compose_cmd = ["docker-compose", "--version"]
                docker_compose_version = subprocess.run(
                    compose_cmd, capture_output=True, text=True,
                    encoding='utf-8', errors='replace', check=True
                ).stdout.strip()
            except FileNotFoundError:
                compose_cmd = ["docker", "compose", "version"] # V2 command
                docker_compose_version = subprocess.run(
                    compose_cmd, capture_output=True, text=True,
                    encoding='utf-8', errors='replace', check=True
                ).stdout.strip()
        except (FileNotFoundError, subprocess.CalledProcessError) as dcv_err:
            docker_compose_version = f"Error checking Docker Compose version: {dcv_err}"
            api_logger.error(docker_compose_version)
        debug_info["docker_compose_version"] = docker_compose_version

        docker_manager: DockerManager = current_app.config["docker_manager"]
        container_statuses = get_app_container_statuses(model, app_num, docker_manager)
        debug_info["backend_container"] = container_statuses.get("backend", {"error": "Status unavailable"})
        debug_info["frontend_container"] = container_statuses.get("frontend", {"error": "Status unavailable"})
        if container_statuses.get("error"):
            debug_info["container_status_error"] = container_statuses["error"]

        debug_info["timestamp"] = datetime.now().isoformat()
        api_logger.debug(f"Debug data collected for {model}/app{app_num}")
        return debug_info

    except FileNotFoundError as e:
        api_logger.error(f"Error in debug endpoint for {model}/app{app_num}: {e}")
        return APIResponse(success=False, error=str(e), code=http.HTTPStatus.NOT_FOUND)
    except Exception as e:
        api_logger.exception(f"Error in debug endpoint for {model}/app{app_num}: {e}")
        raise InternalServerError(f"Failed to get debug info: {e}") from e


@api_bp.route("/health/<string:model>/<int:app_num>")
@ajax_compatible # Handles JSON response
def check_container_health(model: str, app_num: int):
    """
    Check if containers for a specific app are healthy after startup.
    """
    api_logger.debug(f"Health check requested for {model}/app{app_num}")
    docker_manager: DockerManager = current_app.config["docker_manager"]
    healthy, message = verify_container_health(docker_manager, model, app_num)
    api_logger.debug(f"Health check result for {model}/app{app_num}: {healthy} - {message}")
    return {"healthy": healthy, "message": message}


@api_bp.route("/status")
@ajax_compatible # Handles JSON response
def system_status():
    """
    Get overall system status (Docker and Disk).
    """
    api_logger.debug("System status check requested")
    docker_manager: DockerManager = current_app.config["docker_manager"]
    docker_ok = False
    disk_ok = False
    details = {}

    try:
        disk_ok = SystemHealthMonitor.check_disk_space()
        details["disk_space_ok"] = disk_ok

        if docker_manager and docker_manager.client:
            docker_ok = SystemHealthMonitor.check_docker_connection(docker_manager.client)
            details["docker_connection_ok"] = docker_ok
        else:
            details["docker_connection_ok"] = False
            details["docker_error"] = "Docker client not available"

    except Exception as e:
        api_logger.exception(f"Error during system status check: {e}")
        details["error"] = str(e)

    status = "healthy" if (disk_ok and docker_ok) else "warning" if (disk_ok or docker_ok) else "error"
    api_logger.debug(f"System status: {status} (disk: {disk_ok}, docker: {docker_ok})")

    return {
        "status": status,
        "details": details,
        "timestamp": datetime.now().isoformat(),
    }


@api_bp.route("/model-info")
@ajax_compatible # Handles JSON response
def get_model_info():
    """
    Get configuration information about all AI models.
    """
    api_logger.debug("Model information requested")
    model_info = []
    for idx, model in enumerate(AI_MODELS): # Assuming AI_MODELS holds objects/dicts with .name and .color
        model_name = model.name if hasattr(model, 'name') else str(model) # Handle simple list too
        model_color = model.color if hasattr(model, 'color') else "#FFFFFF" # Default color
        try:
            # Get app count without throwing error if dir missing
            apps_list = get_apps_for_model(model_name)
            app_count = len(apps_list)
            port_range = PortManager.get_port_range(idx) # Assumes PortManager exists
            model_info.append({
                "name": model_name,
                "color": model_color,
                "ports": port_range,
                "total_apps": app_count,
            })
        except Exception as e:
            api_logger.exception(f"Error getting info for model '{model_name}': {e}")
            model_info.append({
                "name": model_name,
                "color": model_color,
                "error": f"Failed to get details: {e}"
            })

    api_logger.debug(f"Returning information for {len(model_info)} models")
    return model_info


# =============================================================================
# Client-side Error Logging Endpoint
# =============================================================================
@api_bp.route("/log-client-error", methods=["POST"])
@ajax_compatible # Handles JSON response / errors
def log_client_error():
    """
    Endpoint for logging client-side JavaScript errors. Expects JSON payload.
    """
    try:
        data = request.get_json()
        if not data:
            client_error_logger.warning("Client error logging request received with no JSON data.")
            return APIResponse(
                success=False,
                error="No error data provided",
                code=http.HTTPStatus.BAD_REQUEST
            )

        error_context = {
            "message": data.get('message', 'No message provided'),
            "url": data.get('url', 'N/A'),
            "file_info": f"{data.get('filename', 'N/A')}:{data.get('lineno', 'N/A')}:{data.get('colno', 'N/A')}",
            "user_agent": request.headers.get('User-Agent', 'N/A')
        }
        if 'stack' in data: error_context['stack_preview'] = data['stack'][:500] + '...'
        if 'context' in data: error_context['extra_context'] = data['context']

        client_error_logger.error(
            "ClientError: %(message)s | URL: %(url)s | File: %(file_info)s | UA: %(user_agent)s",
            error_context
        )
        if 'stack' in data:
            client_error_logger.debug("Full Client Stack Trace:\n%s", data['stack'])

        return {"status": "logged"}

    except Exception as e:
        client_error_logger.exception("Error processing client error log request: %s", e)
        return APIResponse(
            success=False,
            error="Server error while logging client error.",
            code=http.HTTPStatus.INTERNAL_SERVER_ERROR
        )


# =============================================================================
# ZAP Routes (/zap)
# =============================================================================

def get_zap_results_path(app, model, app_num):
    """
    Get the path to the ZAP results file, checking multiple possible locations.
    
    Args:
        app: Flask application instance
        model: Model name (e.g. 'Llama')
        app_num: Application number
        
    Returns:
        Path object to the ZAP results file
    """
    # Try various potential locations for the ZAP results file
    base_dir = Path(app.config["BASE_DIR"])
    
    # Possible locations to check
    possible_paths = [
        # Direct model/app path in base directory
        base_dir / model / f"app{app_num}" / ".zap_results.json",
        
        # With z_interface_app in the path
        base_dir / "z_interface_app" / model / f"app{app_num}" / ".zap_results.json",
        
        # Base directory itself being z_interface_app
        base_dir.parent / model / f"app{app_num}" / ".zap_results.json",
        
        # Alternative filename (without leading dot)
        base_dir / model / f"app{app_num}" / "zap_results.json",
        
        # Inside z_interface_app with no dot in filename
        base_dir / "z_interface_app" / model / f"app{app_num}" / "zap_results.json"
    ]
    
    # Check each path and return the first one that exists
    for path in possible_paths:
        if path.exists():
            return path
    
    # If no file exists, return the default path (for future writing)
    return possible_paths[0]


@zap_bp.route("/<string:model>/<int:app_num>")
@ajax_compatible # Returns rendered template or handles errors
def zap_scan_page(model: str, app_num: int):
    """
    Display the ZAP scanner page for a specific app.
    """
    zap_logger.info(f"ZAP scan page requested for {model}/app{app_num}")
    alerts = []
    error_msg = None
    summary = {"high": 0, "medium": 0, "low": 0, "info": 0, "vulnerabilities_with_code": 0}
    results_exist = False

    try:
        # Get the correct path to the ZAP results file
        results_file = get_zap_results_path(current_app, model, app_num)
        results_exist = results_file.exists()
        
        if results_exist:
            zap_logger.info(f"Loading ZAP results from: {results_file}")
            
            try:
                with open(results_file, 'r', encoding='utf-8', errors='replace') as f:
                    data = json.load(f)
                
                # Extract alerts from the top-level "alerts" key
                if "alerts" in data and isinstance(data["alerts"], list):
                    alerts = data["alerts"]
                    
                    # Count risks by type
                    for alert in alerts:
                        risk = alert.get('risk', '')
                        if risk == 'High':
                            summary["high"] += 1
                        elif risk == 'Medium':
                            summary["medium"] += 1
                        elif risk == 'Low':
                            summary["low"] += 1
                        elif risk in ('Info', 'Informational'):
                            summary["info"] += 1
                            
                        # Count vulnerabilities with code
                        if alert.get('affected_code') and alert['affected_code'] is not None:
                            if isinstance(alert['affected_code'], dict) and 'snippet' in alert['affected_code'] and alert['affected_code']['snippet']:
                                summary["vulnerabilities_with_code"] += 1
                    
                    zap_logger.info(f"Loaded {len(alerts)} alerts: H={summary['high']}, M={summary['medium']}, L={summary['low']}, I={summary['info']}, with_code={summary['vulnerabilities_with_code']}")
                else:
                    zap_logger.warning(f"No alerts array found in results file")
                    error_msg = "No scan alerts found in results file."
            except json.JSONDecodeError as json_err:
                error_msg = f"Failed to parse JSON in results file: {json_err}"
                zap_logger.exception(error_msg)
            except Exception as e:
                error_msg = f"Failed to process results file: {e}"
                zap_logger.exception(error_msg)
        else:
            zap_logger.info(f"No ZAP results file found at: {results_file}")

    except Exception as e:
        error_msg = f"Error preparing ZAP page: {e}"
        zap_logger.exception(error_msg)

    return render_template(
        "zap_scan.html",
        model=model,
        app_num=app_num,
        alerts=alerts,
        error=error_msg,
        summary=summary,
        results_exist=results_exist
    )

@zap_bp.route("/scan/<string:model>/<int:app_num>", methods=["POST"])
@ajax_compatible # Handles JSON response / errors
def start_zap_scan(model: str, app_num: int):
    """
    Start a comprehensive ZAP scan in a background thread.
    """
    zap_logger.info(f"Request received to start ZAP scan for {model}/app{app_num}")
    scan_manager = get_scan_manager()

    latest_scan_info = scan_manager.get_latest_scan_for_app(model, app_num)
    if latest_scan_info:
        _, latest_scan = latest_scan_info
        # Use ScanState Enum for checking status
        active_statuses = {
            ScanState.STARTING.value, ScanState.SPIDERING.value, ScanState.SCANNING.value
        }
        if latest_scan.get("status") in active_statuses:
            zap_logger.warning(f"ZAP scan already in progress for {model}/app{app_num}: Status={latest_scan['status']}")
            return APIResponse(success=False, error="A scan is already running for this app.", code=http.HTTPStatus.CONFLICT)

    scan_id = scan_manager.create_scan(model, app_num, {})
    zap_logger.info(f"Created new scan entry with ID: {scan_id}")

    def run_scan_thread(app_context, scan_id_thread, model_thread, app_num_thread):
        """Target function for the background scan thread."""
        with app_context:
            scan_thread_logger = create_logger_for_component(f'zap.thread.{model_thread}-{app_num_thread}')
            scan_thread_logger.info(f"Background scan thread starting for scan ID: {scan_id_thread}")
            scanner = None
            try:
                base_dir_thread = Path(current_app.config["BASE_DIR"])
                app_dir_thread = get_app_directory(current_app, model_thread, app_num_thread)

                scan_thread_logger.info(f"Initializing ZAP scanner instance for {model_thread}/app{app_num_thread}")
                scanner = create_scanner(base_dir_thread) # Use base dir for scanner logs/tmp

                scan_thread_logger.info(f"Setting source code root directory to {app_dir_thread}")
                scanner.set_source_code_root(str(app_dir_thread)) # Pass app dir for code mapping

                current_scan_manager = get_scan_manager()
                current_scan_manager.update_scan(
                    scan_id_thread,
                    scanner=scanner, # Store scanner instance if stop is needed
                    # Use ScanState Enum value for status
                    status=ScanState.STARTING.value,
                    progress=0,
                    spider_progress=0, passive_progress=0, active_progress=0, ajax_progress=0,
                    start_time=datetime.now().isoformat(),
                    end_time=None,
                    results=None
                )

                scan_thread_logger.info(f"Starting comprehensive ZAP scan for {model_thread}/app{app_num_thread}")
                success = scanner.start_scan(model_thread, app_num_thread) # Blocks until scan finishes

                scan_thread_logger.info(f"Scan finished for {scan_id_thread}. Success reported by scanner: {success}")
                # Determine final status based on scanner's return and potential prior errors
                # Scan manager state might have been updated if scan_target failed critically
                current_state = current_scan_manager.get_scan_status(scan_id_thread)
                if current_state and current_state.get("status") == ScanState.ERROR.value:
                     final_status = ScanState.ERROR.value # Keep Error status if set during scan
                else:
                     final_status = ScanState.COMPLETE.value if success else ScanState.FAILED.value

                final_progress = 100 # Mark as 100% done

                results_file = app_dir_thread / ".zap_results.json"
                summary_data = {}
                risk_counts = {}
                duration = None
                vuln_with_code = 0
                if results_file.exists() and results_file.stat().st_size > 10:
                    try:
                        with open(results_file, 'r', encoding='utf-8') as f:
                            results_json = json.load(f)
                        summary_data = results_json.get("summary", {})
                        risk_counts = summary_data.get("risk_counts", {})
                        duration = summary_data.get("duration_seconds")
                        vuln_with_code = summary_data.get("vulnerabilities_with_code", 0)
                    except Exception as read_err:
                        scan_thread_logger.error(f"Failed to read final summary from results file {results_file}: {read_err}")

                current_scan_manager.update_scan(
                    scan_id_thread,
                    status=final_status,
                    progress=final_progress,
                    spider_progress=final_progress, passive_progress=final_progress,
                    active_progress=final_progress, ajax_progress=final_progress, # Mark all 100%
                    end_time=datetime.now().isoformat(),
                    duration_seconds=duration,
                    vulnerabilities_with_code=vuln_with_code,
                    # Update risk counts from file summary
                    high_count=risk_counts.get("High", 0),
                    medium_count=risk_counts.get("Medium", 0),
                    low_count=risk_counts.get("Low", 0),
                    info_count=risk_counts.get("Info", 0),
                )
                scan_thread_logger.info(f"Scan {scan_id_thread} final status updated to {final_status}")

            except FileNotFoundError as e:
                scan_thread_logger.error(f"Cannot start scan {scan_id_thread}, directory not found: {e}")
                # Use ScanState Enum value for status
                get_scan_manager().update_scan(scan_id_thread, status=ScanState.ERROR.value, progress=0, error=f"Directory not found: {e}")
            except Exception as e:
                scan_thread_logger.exception(f"Error during background scan {scan_id_thread}: {e}")
                # Use ScanState Enum value for status
                get_scan_manager().update_scan(scan_id_thread, status=ScanState.ERROR.value, progress=0, error=str(e))
            finally:
                # Scanner's start_scan should handle its own cleanup, but we ensure manager state is updated
                get_scan_manager().cleanup_old_scans() # Clean up old entries if needed
                scan_thread_logger.info(f"Background scan thread finished for scan ID: {scan_id_thread}")

    thread = threading.Thread(
        target=run_scan_thread,
        args=(current_app.app_context(), scan_id, model, app_num),
        daemon=True
    )
    thread.name = f"zap-scan-{model}-{app_num}"
    thread.start()
    zap_logger.info(f"Background scan thread '{thread.name}' started for scan ID {scan_id}.")

    return {"status": "started", "scan_id": scan_id}


@zap_bp.route("/scan/<string:model>/<int:app_num>/status")
@ajax_compatible # Handles JSON response
def zap_scan_status(model: str, app_num: int):
    """
    Get the status of the latest ZAP scan for an app.
    """
    zap_logger.debug(f"Scan status requested for {model}/app{app_num}")
    scan_manager = get_scan_manager()
    latest_scan_info = scan_manager.get_latest_scan_for_app(model, app_num)

    default_status = {
        "status": ScanState.NOT_RUN.value, "progress": 0, "spider_progress": 0, "passive_progress": 0,
        "active_progress": 0, "ajax_progress": 0, "high_count": 0, "medium_count": 0,
        "low_count": 0, "info_count": 0, "vulnerabilities_with_code": 0, "scan_id": None,
        "start_time": None, "end_time": None, "duration_seconds": None, "error": None
    }

    if not latest_scan_info:
        zap_logger.debug(f"No scan history found for {model}/app{app_num}")
        return default_status

    scan_id, scan_state = latest_scan_info
    # Start with defaults and overlay current state
    response = default_status.copy()
    response.update({key: scan_state.get(key) for key in default_status if key in scan_state}) # Update only existing keys
    response["scan_id"] = scan_id # Ensure scan_id is correct

    # If scan state indicates completion/failure, try reading counts/duration from the file
    # This covers cases where the final update might have been missed or is richer
    # Use ScanState Enum values for checking
    terminal_states = {
        ScanState.COMPLETE.value, ScanState.FAILED.value,
        ScanState.STOPPED.value, ScanState.ERROR.value
    }
    if response["status"] in terminal_states:
        try:
            app_dir = get_app_directory(current_app, model, app_num)
            results_file = app_dir / ".zap_results.json"
            if results_file.exists() and results_file.stat().st_size > 10:
                with open(results_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                summary = data.get("summary", {})
                risk_counts = summary.get("risk_counts", {})
                # Update response with counts from file
                response.update({
                    "high_count": risk_counts.get("High", 0),
                    "medium_count": risk_counts.get("Medium", 0),
                    "low_count": risk_counts.get("Low", 0),
                    "info_count": risk_counts.get("Info", 0),
                    "vulnerabilities_with_code": summary.get("vulnerabilities_with_code", 0),
                    "duration_seconds": summary.get("duration_seconds"),
                    # Ensure status from file reflects reality if different from manager state
                    "status": summary.get("status", response["status"]).capitalize()
                })
                zap_logger.debug(f"Updated final counts/duration from results file for scan {scan_id}")

        except FileNotFoundError:
            zap_logger.warning(f"Cannot read final counts for {scan_id}, app directory not found.")
        except Exception as e:
            zap_logger.exception(f"Error reading final results file for scan {scan_id}: {e}")

    return response


@zap_bp.route("/scan/<string:model>/<int:app_num>/stop", methods=["POST"])
@ajax_compatible # Handles JSON response / errors
def stop_zap_scan(model: str, app_num: int):
    """
    Stop a running ZAP scan for a specific app.
    """
    zap_logger.info(f"Request to stop ZAP scan for {model}/app{app_num}")
    scan_manager = get_scan_manager()
    latest_scan_info = scan_manager.get_latest_scan_for_app(model, app_num)

    if not latest_scan_info:
        zap_logger.warning(f"Stop request failed: No scan found for {model}/app{app_num}")
        return APIResponse(success=False, error="No scan found for this app", code=http.HTTPStatus.NOT_FOUND)

    scan_id, scan_state = latest_scan_info
    # Use ScanState Enum values for checking
    active_statuses = {ScanState.STARTING.value, ScanState.SPIDERING.value, ScanState.SCANNING.value}

    if scan_state.get("status") not in active_statuses:
        current_status = scan_state.get("status", "Unknown")
        zap_logger.warning(f"Stop request ignored: Scan {scan_id} is not running (status: {current_status})")
        return APIResponse(success=False, error=f"Scan is not running (status: {current_status})", code=http.HTTPStatus.BAD_REQUEST)

    try:
        zap_logger.info(f"Attempting to stop scan ID {scan_id} ({model}/app{app_num})")
        # Logic to actually stop the ZAP instance needs to be implemented,
        # perhaps by getting the scanner instance from scan_state and calling a method on it.
        # For now, just update the state in the manager.

        # TODO: Implement actual ZAP process stop logic here.
        # Example:
        # scanner = scan_state.get("scanner")
        # if scanner and hasattr(scanner, "stop_scan"):
        #     scanner.stop_scan() # Assumes scanner has a stop method
        # else:
        #     # Maybe find process ID and terminate? Risky.
        #     zap_logger.warning(f"Cannot automatically stop ZAP instance for scan {scan_id}. Manual cleanup might be needed.")
        stop_zap_scanners() # Call the utility function to attempt cleanup

        scan_manager.update_scan(
            scan_id,
            # Use ScanState Enum value
            status=ScanState.STOPPED.value,
            progress=0, # Reset progress
            spider_progress=0, passive_progress=0, active_progress=0, ajax_progress=0,
            end_time=datetime.now().isoformat(),
            error="Scan stopped by user request." # Add note
        )

        zap_logger.info(f"Scan {scan_id} for {model}/app{app_num} marked as stopped.")
        return {"status": "stopped", "message": "Scan stop request processed (cleanup attempted)."}

    except Exception as e:
        error_msg = f"Failed to process stop scan request for {scan_id} ({model}/app{app_num}): {str(e)}"
        zap_logger.exception(error_msg)
        # Update status to error even if stop fails
        # Use ScanState Enum value
        scan_manager.update_scan(scan_id, status=ScanState.ERROR.value, error=f"Failed during stop: {e}")
        return APIResponse(success=False, error=error_msg, code=http.HTTPStatus.INTERNAL_SERVER_ERROR)


@zap_bp.route("/code_report/<string:model>/<int:app_num>")
def download_code_report(model: str, app_num: int):
    """
    Download the generated ZAP code analysis report (Markdown).
    """
    zap_logger.info(f"Code report download requested for {model}/app{app_num}")
    try:
        app_dir = get_app_directory(current_app, model, app_num)
        report_file = app_dir / ".zap_code_report.md"

        if not report_file.is_file():
            zap_logger.warning(f"Code report file not found: {report_file}")
            flash("Code analysis report not found. Please run a ZAP scan first.", "error")
            return redirect(url_for('zap.zap_scan_page', model=model, app_num=app_num))

        zap_logger.info(f"Sending code report file: {report_file}")
        return send_file(
            report_file,
            mimetype="text/markdown; charset=utf-8", # Specify charset
            as_attachment=True,
            download_name=f"security_code_report_{model}_app{app_num}.md"
        )
    except FileNotFoundError as e:
        zap_logger.error(f"App directory not found for report download {model}/app{app_num}: {e}")
        flash(f"Application directory not found: {e}", "error")
        return redirect(url_for('zap.zap_scan_page', model=model, app_num=app_num))
    except Exception as e:
        error_msg = f"Failed to send code report for {model}/app{app_num}: {e}"
        zap_logger.exception(error_msg)
        flash(f"Error downloading report: {e}", "error")
        return redirect(url_for('zap.zap_scan_page', model=model, app_num=app_num))


@zap_bp.route("/regenerate_code_report/<string:model>/<int:app_num>", methods=["POST"])
@ajax_compatible # Handles JSON response / errors
def regenerate_code_report(model: str, app_num: int):
    """
    Regenerate the code analysis report from existing ZAP scan results JSON.
    """
    zap_logger.info(f"Code report regeneration requested for {model}/app{app_num}")
    try:
        base_dir = Path(current_app.config["BASE_DIR"])
        app_dir = get_app_directory(current_app, model, app_num)
        results_file = app_dir / ".zap_results.json"
        report_file_path = app_dir / ".zap_code_report.md"

        if not results_file.is_file() or results_file.stat().st_size < 10:
            msg = f"Valid ZAP results file not found at {results_file}. Cannot regenerate report."
            zap_logger.warning(msg)
            return APIResponse(success=False, error="Scan results not found or empty.", code=http.HTTPStatus.NOT_FOUND)

        zap_logger.info(f"Reading scan results from {results_file}")
        with open(results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract alerts, handling potential structure variations
        alerts_raw = data.get("alerts", [])
        if not alerts_raw and "summary" in data and "alerts" in data["summary"]:
             alerts_raw = data["summary"]["alerts"] # Check older format maybe?

        if not alerts_raw:
            zap_logger.warning(f"No alerts array found in scan results for {model}/app{app_num}")

        # Re-create ZapVulnerability objects from the raw alert dictionaries
        vulnerabilities_obj = []
        for alert_dict in alerts_raw:
             try:
                  # Reconstruct CodeContext if present
                  affected_code_dict = alert_dict.get("affected_code")
                  affected_code_obj = None
                  if affected_code_dict and isinstance(affected_code_dict, dict):
                       affected_code_obj = CodeContext(**affected_code_dict)

                  # Remove affected_code dict before passing to ZapVulnerability constructor
                  alert_dict_copy = alert_dict.copy()
                  alert_dict_copy.pop("affected_code", None)

                  vuln_obj = ZapVulnerability(
                      affected_code=affected_code_obj, # Pass reconstructed object
                      **alert_dict_copy # Pass remaining fields
                  )
                  vulnerabilities_obj.append(vuln_obj)
             except TypeError as te:
                  zap_logger.warning(f"Skipping alert due to TypeError during reconstruction: {te} | Alert data: {alert_dict}")
             except Exception as recon_err:
                  zap_logger.warning(f"Skipping alert due to unexpected error during reconstruction: {recon_err} | Alert data: {alert_dict}")


        if not vulnerabilities_obj:
             zap_logger.warning(f"No valid vulnerabilities could be reconstructed for {model}/app{app_num}")
             # Allow generating an empty report

        # Create scanner instance (only needed for report generation method)
        scanner = create_scanner(base_dir)

        zap_logger.info(f"Generating code report content for {model}/app{app_num}")
        report_content = scanner.generate_affected_code_report(vulnerabilities_obj, str(report_file_path))

        # Count vulnerabilities with code from the *reconstructed objects*
        vulnerabilities_with_code = sum(1 for v in vulnerabilities_obj if v.affected_code and v.affected_code.snippet)

        zap_logger.info(f"Code report regenerated to '{report_file_path}' with {vulnerabilities_with_code} code-related findings.")
        return {
            "success": True,
            "message": f"Code report regenerated successfully with {vulnerabilities_with_code} code-related findings.",
            "vulnerabilities_with_code": vulnerabilities_with_code
        }
    except FileNotFoundError as e:
        zap_logger.error(f"App directory not found for report regeneration {model}/app{app_num}: {e}")
        return APIResponse(success=False, error=str(e), code=http.HTTPStatus.NOT_FOUND)
    except Exception as e:
        error_msg = f"Failed to regenerate code report for {model}/app{app_num}: {e}"
        zap_logger.exception(error_msg)
        raise InternalServerError(error_msg) from e


# =============================================================================
# Analysis Routes (/analysis)
# =============================================================================
@analysis_bp.route("/backend-security/<string:model>/<int:app_num>")
@ajax_compatible # Handles response formatting / errors
def security_analysis(model: str, app_num: int):
    """
    Run backend security analysis for an app and display results.
    """
    security_logger.info(f"Backend security analysis requested for {model}/app{app_num}")
    full_scan = request.args.get("full", "false").lower() == "true"

    if not hasattr(current_app, 'backend_security_analyzer'):
        security_logger.error("Backend security analyzer not available.")
        flash("Backend security analyzer is not configured.", "error")
        return render_template("security_analysis.html", model=model, app_num=app_num, error="Analyzer not configured")

    analyzer = current_app.backend_security_analyzer
    return process_security_analysis(
        template="security_analysis.html",
        analyzer=analyzer,
        # Assuming the method name is consistent, adjust if needed
        analysis_method=analyzer.run_security_analysis, # Check method name in analyzer
        model=model,
        app_num=app_num,
        full_scan=full_scan,
        no_issue_message="No significant backend security issues found."
    )


@analysis_bp.route("/frontend-security/<string:model>/<int:app_num>")
@ajax_compatible # Handles response formatting / errors
def frontend_security_analysis(model: str, app_num: int):
    """
    Run frontend security analysis for an app and display results.
    """
    security_logger.info(f"Frontend security analysis requested for {model}/app{app_num}")
    full_scan = request.args.get("full", "false").lower() == "true"

    if not hasattr(current_app, 'frontend_security_analyzer'):
        security_logger.error("Frontend security analyzer not available.")
        flash("Frontend security analyzer is not configured.", "error")
        return render_template("security_analysis.html", model=model, app_num=app_num, error="Analyzer not configured")

    analyzer = current_app.frontend_security_analyzer
    return process_security_analysis(
        template="security_analysis.html", # Can use the same template?
        analyzer=analyzer,
        analysis_method=analyzer.run_security_analysis, # Assuming same method name
        model=model,
        app_num=app_num,
        full_scan=full_scan,
        no_issue_message="No significant frontend security issues found."
    )


@analysis_bp.route("/analyze", methods=["POST"])
@ajax_compatible # Handles JSON response / errors
def analyze_security_issues():
    """
    Analyze a list of security issues (provided in JSON body) using an AI service.
    """
    security_logger.info("AI security analysis requested via POST")
    try:
        data = request.get_json()
        if not data or not isinstance(data.get("issues"), list):
            security_logger.warning("No 'issues' list provided in JSON for AI security analysis")
            raise BadRequest("Request body must be JSON with an 'issues' list.")

        issues = data["issues"]
        model_name = data.get("model", "default-model") # AI model to use
        app_context_info = data.get("app_context", {}) # Optional context

        security_logger.info(f"Analyzing {len(issues)} security issues using AI model '{model_name}'. App Context: {app_context_info}")

        # --- Build structured prompt ---
        prompt = f"# Security Analysis Request for {app_context_info.get('model', 'App')} / {app_context_info.get('app_num', '')}\n\n"
        prompt += f"## Issues ({len(issues)} total):\n"
        issues.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.get('severity', 'low').lower(), 3))
        for i, issue in enumerate(issues[:20]): # Limit prompt length
            prompt += f"\n### Issue {i+1}: {issue.get('issue_type', 'Unknown Type')} ({issue.get('severity', 'N/A')})\n"
            prompt += f"- **Tool:** {issue.get('tool', 'N/A')}\n"
            prompt += f"- **Description:** {issue.get('issue_text', 'N/A')}\n"
            if issue.get('filename'): prompt += f"- **File:** {issue.get('filename')}\n"
            if issue.get('code'): prompt += f"- **Code Snippet:** ```\n{issue['code'][:200]}\n```\n"

        if len(issues) > 20: prompt += "\n...(additional issues truncated)..."

        prompt += """
## Analysis Tasks:
1. Summarize the key security risks based on the provided issues.
2. Provide prioritized recommendations for remediation (Top 3-5).
3. Briefly explain the potential impact if these issues are not addressed.
Please format the response clearly using Markdown."""
        # --- End Prompt Building ---

        security_logger.debug(f"Sending security analysis prompt (length: {len(prompt)}) to AI service '{model_name}'")
        analysis_result = call_ai_service(model_name, prompt) # Assuming this function exists
        security_logger.info("Received security analysis response from AI service")

        return APIResponse(success=True, data={"response": analysis_result})

    except BadRequest as e:
        security_logger.warning(f"Bad request in AI security analysis: {e}")
        raise e
    except Exception as e:
        security_logger.exception(f"Error during AI security analysis: {e}")
        raise InternalServerError("Failed to perform AI security analysis") from e


@analysis_bp.route("/summary/<string:model>/<int:app_num>")
@ajax_compatible # Handles JSON response / errors
def get_security_summary(model: str, app_num: int):
    """
    Get a combined security analysis summary (backend & frontend) for an app.
    """
    security_logger.info(f"Combined security summary requested for {model}/app{app_num}")
    backend_summary = {"total_issues": 0, "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0}}
    backend_status = {}
    frontend_summary = {"total_issues": 0, "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0}}
    frontend_status = {}
    error_details = []

    try:
        if hasattr(current_app, 'backend_security_analyzer'):
            analyzer = current_app.backend_security_analyzer
            security_logger.debug(f"Running backend security analysis for summary...")
            # Adjust method call based on actual analyzer implementation
            # Assuming run_security_analysis returns: issues, tool_status, tool_output
            backend_issues, backend_status, _ = analyzer.run_security_analysis(model, app_num, use_all_tools=False)
            backend_summary = analyzer.get_analysis_summary(backend_issues)
            security_logger.debug(f"Backend summary: {backend_summary['total_issues']} issues.")
        else:
            error_details.append("Backend analyzer unavailable.")
            security_logger.warning("Backend security analyzer unavailable for summary.")

        if hasattr(current_app, 'frontend_security_analyzer'):
            analyzer = current_app.frontend_security_analyzer
            security_logger.debug(f"Running frontend security analysis for summary...")
            frontend_issues, frontend_status, _ = analyzer.run_security_analysis(model, app_num, use_all_tools=False)
            frontend_summary = analyzer.get_analysis_summary(frontend_issues)
            security_logger.debug(f"Frontend summary: {frontend_summary['total_issues']} issues.")
        else:
            error_details.append("Frontend analyzer unavailable.")
            security_logger.warning("Frontend security analyzer unavailable for summary.")

        total_issues = backend_summary["total_issues"] + frontend_summary["total_issues"]
        security_logger.info(f"Combined security summary for {model}/app{app_num}: {total_issues} total issues found.")

        combined_summary = {
            "backend": {"summary": backend_summary, "status": backend_status},
            "frontend": {"summary": frontend_summary, "status": frontend_status},
            "total_issues": total_issues,
            "severity_counts": {
                "HIGH": backend_summary["severity_counts"]["HIGH"] + frontend_summary["severity_counts"]["HIGH"],
                "MEDIUM": backend_summary["severity_counts"]["MEDIUM"] + frontend_summary["severity_counts"]["MEDIUM"],
                "LOW": backend_summary["severity_counts"]["LOW"] + frontend_summary["severity_counts"]["LOW"],
            },
            "scan_time": datetime.now().isoformat(),
            "errors": error_details if error_details else None
        }
        return combined_summary

    except Exception as e:
        security_logger.exception(f"Error generating combined security summary for {model}/app{app_num}: {e}")
        raise InternalServerError("Failed to generate security summary") from e


@analysis_bp.route("/analyze-file", methods=["POST"])
@ajax_compatible # Handles JSON response / errors
def analyze_single_file():
    """
    Analyze a single code file using the appropriate analyzer (backend/frontend).
    """
    security_logger.info("Single file analysis requested via POST")
    try:
        data = request.get_json()
        if not data or "file_path" not in data:
            raise BadRequest("Request body must be JSON with a 'file_path' field.")

        # TODO: IMPORTANT SECURITY VALIDATION NEEDED HERE!
        # Ensure file_path is within allowed project boundaries before processing.
        file_path = Path(data["file_path"])
        is_frontend = data.get("is_frontend", False)
        file_type = "frontend" if is_frontend else "backend"
        security_logger.info(f"Analyzing single {file_type} file: {file_path}")

        analyzer = None
        if is_frontend:
            if hasattr(current_app, 'frontend_security_analyzer'): analyzer = current_app.frontend_security_analyzer
            else: raise RuntimeError("Frontend analyzer not available.")
        else:
            if hasattr(current_app, 'backend_security_analyzer'): analyzer = current_app.backend_security_analyzer
            else: raise RuntimeError("Backend analyzer not available.")

        # Use a more specific method if available
        if hasattr(analyzer, 'analyze_single_file') and callable(analyzer.analyze_single_file):
            security_logger.debug(f"Running analyzer.analyze_single_file on {file_path}")
            issues, tool_status, tool_output = analyzer.analyze_single_file(file_path)
        else:
            # Fallback logic requires specific implementation based on analyzer tools
            security_logger.error(f"Analyzer {type(analyzer).__name__} missing 'analyze_single_file' method and fallback not implemented.")
            raise NotImplementedError("Single file analysis fallback not implemented.")

        security_logger.info(f"Found {len(issues)} issues in {file_path.name}")

        # Assuming 'issues' contains objects with asdict or are directly serializable
        return {
            "status": "success",
            "issues": [asdict(issue) if hasattr(issue, '__dataclass_fields__') else issue for issue in issues],
            "tool_status": tool_status,
            "tool_output": tool_output,
        }
    except BadRequest as e:
        security_logger.warning(f"Bad request in single file analysis: {e}")
        raise e
    except FileNotFoundError as e:
        security_logger.error(f"File not found for analysis: {e}")
        return APIResponse(success=False, error=f"File not found: {e}", code=http.HTTPStatus.NOT_FOUND)
    except (RuntimeError, NotImplementedError) as e:
        security_logger.error(f"Configuration or implementation error during file analysis: {e}")
        raise InternalServerError(f"Analysis error: {e}") from e
    except Exception as e:
        security_logger.exception(f"Unexpected error analyzing file: {e}")
        raise InternalServerError("File analysis failed due to an unexpected error.") from e


# =============================================================================
# Performance Testing Routes (/performance)
# =============================================================================
# Update the performance_test function in routes.py to pass model and app_num

@performance_bp.route("/<string:model>/<int:port>", methods=["GET", "POST"])
@ajax_compatible # Handles response formatting / errors
def performance_test(model: str, port: int):
    """
    Display performance test page (GET) or run a test (POST).
    """
    if not hasattr(current_app, 'performance_tester'):
        msg = "Performance tester service is not available."
        perf_logger.error(msg)
        if request.method == "POST":
            raise RuntimeError(msg)
        else:
            flash(msg, "error")
            return render_template("performance_test.html", model=model, port=port, error=msg)

    tester = current_app.performance_tester
    base_dir = Path(current_app.config.get("BASE_DIR", "."))

    # Get app_num from port (derive it based on port configuration)
    app_num = None
    try:
        # Simple extraction based on port convention
        # Assuming BASE_FRONTEND_PORT is 5501
        BASE_FRONTEND_PORT = 5501
        port_offset = port - BASE_FRONTEND_PORT
        if port_offset >= 0:
            # Calculate app_num (add 1 because app_num is 1-based)
            # Assuming PORTS_PER_APP is 2
            PORTS_PER_APP = 2
            app_num = (port_offset // PORTS_PER_APP) + 1
            perf_logger.debug(f"Derived app_num={app_num} from port={port}")
    except Exception as e:
        perf_logger.warning(f"Could not derive app_num from port {port}: {e}")

    if request.method == "POST":
        perf_logger.info(f"Starting performance test POST request for {model} on port {port}")
        try:
            data = request.get_json()
            if not data: raise BadRequest("Missing JSON request body.")

            num_users = int(data.get("num_users", 10))
            duration = int(data.get("duration", 30))
            spawn_rate = int(data.get("spawn_rate", 1))
            endpoints_raw = data.get("endpoints", ["/"]) # Default to root path

            if not (num_users > 0 and duration > 0 and spawn_rate > 0):
                raise BadRequest("Number of users, duration, and spawn rate must be positive integers.")
            if not endpoints_raw:
                raise BadRequest("At least one endpoint path must be provided.")

            perf_logger.info(
                f"Test parameters: users={num_users}, duration={duration}s, "
                f"spawn_rate={spawn_rate}, raw_endpoints={endpoints_raw}"
            )

            formatted_endpoints = []
            for ep in endpoints_raw:
                if isinstance(ep, str): formatted_endpoints.append({"path": ep, "method": "GET", "weight": 1})
                elif isinstance(ep, dict) and "path" in ep: formatted_endpoints.append(ep)
                else: raise BadRequest(f"Invalid endpoint format: {ep}")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            test_name = f"{model}_{port}_{timestamp}"
            host_url = f"http://localhost:{port}" # Assuming localhost for now

            perf_logger.info(f"Running performance test '{test_name}' against {host_url}")
            result_data = tester.run_test_cli(
                test_name=test_name, host=host_url, endpoints=formatted_endpoints,
                user_count=num_users, spawn_rate=spawn_rate, run_time=f"{duration}s",
                html_report=True,
                model=model,  # Pass model name for consolidated results
                app_num=app_num  # Pass app_num for consolidated results
            )

            perf_logger.info(f"Test '{test_name}' completed.")
            
            # Check for consolidated results file
            result_file_path = None
            if app_num:
                app_dir = base_dir / model / f"app{app_num}"
                result_file = app_dir / ".locust_result.json"
                if result_file.exists():
                    result_file_path = result_file
                    perf_logger.info(f"Consolidated results saved to {result_file}")
            
            # Check for HTML report
            report_path_rel = None
            try:
                # First check in the model/app directory
                if app_num:
                    app_dir = base_dir / model / f"app{app_num}"
                    report_files = list(app_dir.glob("*_report.html"))
                
                # Then check in the performance_reports directory
                if not report_files:
                    test_dir = base_dir / "performance_reports" / test_name
                    if test_dir.exists():
                        report_files = list(test_dir.glob("*_report.html"))
                
                if report_files:
                    report_path = report_files[0]
                    # Make path relative to Flask static folder
                    static_base = base_dir
                    report_path_rel = report_path.relative_to(static_base)
                    perf_logger.info(f"Report path: {report_path_rel}")
            except Exception as report_err:
                perf_logger.warning(f"Could not determine report path: {report_err}")

            return {
                "status": "success", 
                "message": f"Test '{test_name}' completed.",
                "data": result_data, # Raw results from tester
                "report_url": url_for('static', filename=str(report_path_rel).replace('\\', '/')) if report_path_rel else None,
                "result_file": str(result_file_path) if result_file_path else None
            }

        except BadRequest as e:
            perf_logger.warning(f"Bad request for performance test: {e}")
            raise e
        except Exception as e:
            perf_logger.exception(f"Performance test execution error for {model} on port {port}: {e}")
            raise InternalServerError("Test execution failed") from e
    else:
        # GET request
        perf_logger.info(f"Rendering performance test form for {model} on port {port}")
        return render_template("performance_test.html", model=model, port=port)


@performance_bp.route("/<string:model>/<int:port>/stop", methods=["POST"])
@ajax_compatible # Handles JSON response / errors
def stop_performance_test(model: str, port: int):
    """
    Stop a running performance test (Placeholder).
    """
    perf_logger.info(f"Request to stop performance test for {model} on port {port}")
    try:
        # TODO: Implement actual test stopping logic
        perf_logger.warning("Performance test stopping is not yet implemented.")
        return {
            "status": "success",
            "message": "Test stop request received (implementation pending)."
        }
    except Exception as e:
        perf_logger.exception(f"Error processing stop performance test request for {model} on port {port}: {e}")
        raise InternalServerError("Failed to process stop request.") from e


@performance_bp.route("/<string:model>/<int:port>/reports", methods=["GET"])
@ajax_compatible # Handles JSON response / errors
def list_performance_reports(model: str, port: int):
    """
    List available performance test reports for a specific model/port.
    """
    perf_logger.info(f"Listing performance reports for {model} on port {port}")
    reports = []
    try:
        base_dir = Path(current_app.config.get("BASE_DIR", "."))
        report_base_dir = base_dir / "performance_reports"
        if not report_base_dir.is_dir():
            perf_logger.debug(f"Report directory does not exist: {report_base_dir}")
            return {"reports": []}

        test_name_prefix = f"{model}_{port}_"

        for test_dir in report_base_dir.iterdir():
            if test_dir.is_dir() and test_dir.name.startswith(test_name_prefix):
                report_id = test_dir.name
                timestamp_str = report_id.replace(test_name_prefix, "")
                formatted_time = "Unknown"
                try:
                    dt_obj = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    formatted_time = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    perf_logger.warning(f"Could not parse timestamp from report directory: {report_id}")

                html_report_path = next(test_dir.glob("*_report.html"), None)
                report_url = None
                if html_report_path:
                    # URL relative to static folder
                    static_base = base_dir # Assuming reports are served from under static/performance_reports
                    relative_path = html_report_path.relative_to(static_base)
                    report_url = url_for('static', filename=str(relative_path).replace('\\', '/'))

                graphs = []
                for graph_file in test_dir.glob("*.png"):
                    graph_rel_path = graph_file.relative_to(static_base)
                    graphs.append({
                        "name": graph_file.stem.replace("_", " ").title(),
                        "url": url_for('static', filename=str(graph_rel_path).replace('\\', '/'))
                    })

                reports.append({
                    "id": report_id, "timestamp_str": timestamp_str, "created": formatted_time,
                    "report_url": report_url, "graphs": graphs
                })

        reports.sort(key=lambda x: x.get("timestamp_str", ""), reverse=True)
        perf_logger.info(f"Found {len(reports)} performance reports for {model} on port {port}")
        return {"reports": reports}

    except Exception as e:
        perf_logger.exception(f"Error listing performance reports for {model} on port {port}: {e}")
        raise InternalServerError("Failed to list reports.") from e


@performance_bp.route("/<string:model>/<int:port>/reports/<path:report_id>", methods=["GET"])
def view_performance_report(model: str, port: int, report_id: str):
    """
    View a specific performance test report HTML page.
    """
    perf_logger.info(f"Viewing performance report {report_id} for {model} on port {port}")
    try:
        base_dir = Path(current_app.config.get("BASE_DIR", "."))
        report_dir = base_dir / "performance_reports" / report_id

        expected_prefix = f"{model}_{port}_"
        if not report_id.startswith(expected_prefix) or ".." in report_id or "/" in report_id or "\\" in report_id:
            perf_logger.warning(f"Invalid or potentially unsafe report ID requested: {report_id}")
            return render_template("404.html", message="Invalid Report ID"), http.HTTPStatus.BAD_REQUEST

        if not report_dir.is_dir():
            perf_logger.warning(f"Report directory not found: {report_dir}")
            return render_template("404.html", message="Report not found"), http.HTTPStatus.NOT_FOUND

        html_report_path = next(report_dir.glob("*_report.html"), None)
        if not html_report_path or not html_report_path.is_file():
            perf_logger.warning(f"No HTML report file found in directory: {report_dir}")
            return render_template("404.html", message="Report file not found"), http.HTTPStatus.NOT_FOUND

        perf_logger.debug(f"Loading report content from: {html_report_path}")
        with open(html_report_path, "r", encoding='utf-8', errors='replace') as f:
            report_content = f.read()

        graphs = []
        static_base = base_dir # Assuming reports are served from under static/performance_reports
        for graph_file in report_dir.glob("*.png"):
            graph_rel_path = graph_file.relative_to(static_base)
            graphs.append({
                "name": graph_file.stem.replace("_", " ").title(),
                "url": url_for('static', filename=str(graph_rel_path).replace('\\', '/'))
            })

        perf_logger.info(f"Rendering report {report_id} with {len(graphs)} graphs.")
        return render_template(
            "performance_report_viewer.html",
            model=model, port=port, report_id=report_id,
            report_content=report_content, graphs=graphs
        )
    except Exception as e:
        perf_logger.exception(f"Error viewing performance report {report_id}: {e}")
        return render_template("500.html", error=f"Failed to load report: {e}"), http.HTTPStatus.INTERNAL_SERVER_ERROR


@performance_bp.route("/<string:model>/<int:port>/results/<path:report_id>", methods=["GET"])
@ajax_compatible # Handles JSON response / errors
def get_performance_results(model: str, port: int, report_id: str):
    """
    Get raw JSON or parsed CSV results for a specific performance test run.
    """
    perf_logger.info(f"Getting raw performance results data for {report_id}")
    try:
        base_dir = Path(current_app.config.get("BASE_DIR", "."))
        report_dir = base_dir / "performance_reports" / report_id

        expected_prefix = f"{model}_{port}_"
        if not report_id.startswith(expected_prefix) or ".." in report_id or "/" in report_id or "\\" in report_id:
            perf_logger.warning(f"Invalid or potentially unsafe report ID for results: {report_id}")
            raise BadRequest("Invalid Report ID")

        if not report_dir.is_dir():
            perf_logger.warning(f"Results directory not found: {report_dir}")
            raise FileNotFoundError("Report not found")

        json_file = next(report_dir.glob("*_results.json"), None)
        if json_file and json_file.is_file():
            perf_logger.debug(f"Loading JSON results from: {json_file}")
            with open(json_file, "r", encoding='utf-8', errors='replace') as f:
                return json.load(f)

        stats_file = next(report_dir.glob("*_stats.csv"), None)
        if stats_file and stats_file.is_file():
            perf_logger.warning(f"No JSON results file found for {report_id}. CSV parsing not implemented.")
            static_base = base_dir # Assuming reports are served from under static/performance_reports
            csv_rel_path = stats_file.relative_to(static_base)
            return {
                "status": "partial", "message": "Raw JSON results not found. CSV data available.",
                "csv_url": url_for('static', filename=str(csv_rel_path).replace('\\', '/'))
            }

        perf_logger.warning(f"No suitable result data file (JSON or CSV) found in directory: {report_dir}")
        raise FileNotFoundError("No result data found for this report")

    except BadRequest as e: raise e
    except FileNotFoundError as e: return APIResponse(success=False, error=str(e), code=http.HTTPStatus.NOT_FOUND)
    except json.JSONDecodeError as e:
        perf_logger.exception(f"Error decoding JSON results for {report_id}: {e}")
        raise InternalServerError(f"Failed to parse result data: {e}") from e
    except Exception as e:
        perf_logger.exception(f"Error getting performance results for {report_id}: {e}")
        raise InternalServerError("Failed to retrieve performance results.") from e


@performance_bp.route("/<string:model>/<int:port>/reports/<path:report_id>/delete", methods=["POST"])
@ajax_compatible # Handles JSON response / errors
def delete_performance_report(model: str, port: int, report_id: str):
    """
    Delete a specific performance test report directory.
    """
    perf_logger.info(f"Request to delete performance report directory {report_id}")
    try:
        base_dir = Path(current_app.config.get("BASE_DIR", "."))
        report_dir = base_dir / "performance_reports" / report_id

        expected_prefix = f"{model}_{port}_"
        if not report_id.startswith(expected_prefix) or ".." in report_id or "/" in report_id or "\\" in report_id:
            perf_logger.warning(f"Invalid or potentially unsafe report ID for deletion: {report_id}")
            raise BadRequest("Invalid Report ID")

        if not report_dir.is_dir():
            perf_logger.warning(f"Report directory not found for deletion: {report_dir}")
            raise FileNotFoundError("Report not found")

        import shutil
        perf_logger.warning(f"Recursively deleting report directory: {report_dir}") # Log clearly!
        shutil.rmtree(report_dir)
        perf_logger.info(f"Successfully deleted report directory {report_id}")

        return {"status": "success", "message": f"Report {report_id} deleted successfully"}

    except BadRequest as e: raise e
    except FileNotFoundError as e: return APIResponse(success=False, error=str(e), code=http.HTTPStatus.NOT_FOUND)
    except Exception as e:
        perf_logger.exception(f"Error deleting performance report {report_id}: {e}")
        raise InternalServerError(f"Failed to delete report: {e}") from e


# =============================================================================
# GPT4All Routes (/gpt4all)
# =============================================================================
@gpt4all_bp.route("/analysis", methods=["GET", "POST"])
@ajax_compatible # Handles response formatting / errors
def gpt4all_analysis():
    """
    Main route for requirements analysis using GPT4All.
    """
    gpt4all_logger.info(f"Received {request.method} request for GPT4All analysis page/action")
    results = None
    requirements = []
    template_name = None
    error = None
    model = request.args.get("model") or request.form.get("model")
    app_num_str = request.args.get("app_num") or request.form.get("app_num")
    app_num = None

    if not model or not app_num_str:
        error = "Model and App Number are required parameters."
        gpt4all_logger.warning(error)
        if request.method == "POST": raise BadRequest(error)
    else:
        try:
            app_num = int(app_num_str)
            if app_num <= 0: raise ValueError("App number must be positive.")
        except ValueError as e:
            error = f"Invalid App Number: {app_num_str}. {e}"
            gpt4all_logger.warning(error)
            if request.method == "POST": raise BadRequest(error)

    if error and request.method == "GET":
        flash(error, "error")
        return render_template(
            "requirements_check.html", model=model, app_num=None,
            requirements=[], results=None, error=error
        )

    if not hasattr(current_app, 'gpt4all_analyzer'):
        error = "GPT4All analyzer service is not available."
        gpt4all_logger.error(error)
        if request.method == "POST": raise RuntimeError(error)
        flash(error, "error")
        return render_template("requirements_check.html", model=model, app_num=app_num, error=error)

    analyzer = current_app.gpt4all_analyzer

    try:
        gpt4all_logger.debug("Checking GPT4All server availability...")
        if not analyzer.client or not analyzer.client.check_server():
            error = "GPT4All server is not available or not responding. Please ensure it is running."
            gpt4all_logger.error(error)
            if request.method == "POST": raise ConnectionError(error)
            flash(error, "error")
            return render_template("requirements_check.html", model=model, app_num=app_num, error=error)
        gpt4all_logger.debug("GPT4All server is available.")
    except Exception as server_error:
        error = f"Error checking GPT4All server: {server_error}"
        gpt4all_logger.exception(error)
        if request.method == "POST": raise ConnectionError(error) from server_error
        flash(error, "error")
        return render_template("requirements_check.html", model=model, app_num=app_num, error=error)

    try:
        requirements, template_name = analyzer.get_requirements_for_app(app_num)
        gpt4all_logger.info(f"Loaded {len(requirements)} default requirements for {model}/app{app_num} from template '{template_name}'")
    except Exception as req_error:
        error = f"Could not load default requirements: {req_error}"
        gpt4all_logger.exception(error)
        flash(error, "warning")
        requirements = []

    if request.method == "POST":
        gpt4all_logger.info(f"Processing analysis POST request for {model}/app{app_num}")
        if "requirements" in request.form:
            custom_requirements_text = request.form.get("requirements", "").strip()
            if custom_requirements_text:
                custom_requirements = [r.strip() for r in custom_requirements_text.splitlines() if r.strip()]
                if custom_requirements:
                    requirements = custom_requirements
                    gpt4all_logger.info(f"Using {len(requirements)} custom requirements provided in form.")
                else: gpt4all_logger.warning("Custom requirements field was present but empty after stripping.")

        selected_ai_model = request.form.get("gpt4all_model")
        if selected_ai_model:
            gpt4all_logger.info(f"Using selected AI model for analysis: {selected_ai_model}")
            analyzer.client.preferred_model = selected_ai_model

        if not requirements:
            gpt4all_logger.warning("No requirements available to perform analysis.")
            flash("No requirements found or provided. Cannot run analysis.", "error")
            return render_template(
                "requirements_check.html", model=model, app_num=app_num, requirements=[],
                template_name=template_name, results=None, error="No requirements available."
            )

        try:
            gpt4all_logger.info(f"Starting requirements analysis for {model}/app{app_num}...")
            start_timer = time.time()
            results = analyzer.check_requirements(model, app_num, requirements)
            duration = time.time() - start_timer
            gpt4all_logger.info(f"Analysis completed in {duration:.2f} seconds with {len(results)} results.")
            if not results: flash("Analysis ran but returned no results.", "warning")
            else: flash("Analysis completed successfully.", "success")
        except Exception as analysis_error:
            error = f"Analysis failed: {analysis_error}"
            gpt4all_logger.exception(error)
            flash(error, "error")

    return render_template(
        "requirements_check.html",
        model=model, app_num=app_num, requirements=requirements,
        template_name=template_name, results=results, error=error
    )

@gpt4all_bp.route("/api/requirements-check", methods=["POST"])
@ajax_compatible # Handles JSON response / errors
def api_requirements_check():
    """
    API endpoint for checking requirements against code (JSON request/response).
    """
    gpt4all_logger.info("API requirements check received via POST")
    try:
        data = request.get_json()
        if not data: raise BadRequest("Request body must be JSON.")

        model = data.get("model")
        app_num_str = data.get("app_num")
        requirements = data.get("requirements")
        selected_ai_model = data.get("gpt4all_model")

        if not model or app_num_str is None: raise BadRequest("Missing required fields: 'model' and 'app_num'.")
        try:
            app_num = int(app_num_str)
            if app_num <= 0: raise ValueError("App number must be positive.")
        except (ValueError, TypeError) as e: raise BadRequest(f"Invalid 'app_num': {app_num_str}. Must be a positive integer.") from e
        if requirements is not None and not isinstance(requirements, list): raise BadRequest("'requirements' field must be a list of strings.")

        if not hasattr(current_app, 'gpt4all_analyzer'): raise RuntimeError("GPT4All analyzer service is not available.")
        analyzer = current_app.gpt4all_analyzer
        if not analyzer.client or not analyzer.client.check_server(): raise ConnectionError("GPT4All server is not available or not responding.")

        if not requirements:
            gpt4all_logger.debug(f"No requirements in request for {model}/{app_num}, fetching defaults.")
            try:
                requirements, _ = analyzer.get_requirements_for_app(app_num)
                if not requirements: raise ValueError("No default requirements found.")
                gpt4all_logger.info(f"Using {len(requirements)} default requirements.")
            except Exception as req_error:
                gpt4all_logger.exception(f"Failed to get default requirements for {model}/{app_num}: {req_error}")
                raise RuntimeError(f"Could not load requirements: {req_error}") from req_error
        else:
            requirements = [r.strip() for r in requirements if isinstance(r, str) and r.strip()]
            if not requirements: raise BadRequest("Provided 'requirements' list was empty after cleanup.")
            gpt4all_logger.info(f"Using {len(requirements)} requirements from request.")

        if selected_ai_model:
            gpt4all_logger.info(f"Using selected AI model for analysis: {selected_ai_model}")
            analyzer.client.preferred_model = selected_ai_model

        gpt4all_logger.info(f"Starting API requirements analysis for {model}/app{app_num}...")
        start_timer = time.time()
        results = analyzer.check_requirements(model, app_num, requirements)
        duration = time.time() - start_timer
        gpt4all_logger.info(f"API Analysis completed in {duration:.2f} seconds with {len(results)} results.")

        result_dicts = []
        for check in results:
            result_dict = {"requirement": check.requirement}
            if hasattr(check.result, 'to_dict') and callable(check.result.to_dict): result_dict["result"] = check.result.to_dict()
            elif hasattr(check.result, "__dataclass_fields__"): result_dict["result"] = asdict(check.result)
            else: result_dict["result"] = check.result
            result_dicts.append(result_dict)

        return {"status": "success", "results": result_dicts}

    except (BadRequest, ValueError, ConnectionError, RuntimeError) as e:
        gpt4all_logger.warning(f"API requirements check failed: {e}")
        raise e
    except Exception as e:
        gpt4all_logger.exception(f"Unexpected error in API requirements check: {e}")
        raise InternalServerError("An unexpected error occurred during analysis.") from e


@gpt4all_bp.route("/models", methods=["GET"])
@ajax_compatible # Handles JSON response / errors
def get_available_models():
    """
    Get the list of available models from the configured GPT4All server.
    """
    gpt4all_logger.info("Request for available GPT4All models")
    if not hasattr(current_app, 'gpt4all_analyzer'): raise RuntimeError("GPT4All analyzer service is not available.")
    analyzer = current_app.gpt4all_analyzer
    if not analyzer.client: raise RuntimeError("GPT4All client not configured within analyzer.")

    try:
        if analyzer.client.check_server():
            models = analyzer.client.available_models
            gpt4all_logger.info(f"Returning {len(models)} available models.")
            return {"status": "success", "models": models}
        else:
            raise ConnectionError("GPT4All server is not available or not responding.")
    except ConnectionError as e:
        gpt4all_logger.error(f"Failed to connect to GPT4All server for models: {e}")
        raise e
    except Exception as e:
        gpt4all_logger.exception(f"Unexpected error getting available models: {e}")
        raise InternalServerError("Failed to retrieve available models.") from e


@gpt4all_bp.route("/server-status", methods=["GET"])
@ajax_compatible # Handles JSON response / errors
def check_server_status():
    """
    Check the availability of the configured GPT4All server.
    """
    gpt4all_logger.info("Request for GPT4All server status")
    status_info = {"available": False, "server_url": None, "error": None}
    http_code = http.HTTPStatus.OK

    if not hasattr(current_app, 'gpt4all_analyzer'):
        status_info["error"] = "GPT4All analyzer service is not configured."
        gpt4all_logger.error(status_info["error"])
        http_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
        return APIResponse(success=False, error=status_info["error"], code=http_code)

    analyzer = current_app.gpt4all_analyzer
    if not analyzer.client:
        status_info["error"] = "GPT4All client is not configured within analyzer."
        gpt4all_logger.error(status_info["error"])
        http_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
        return APIResponse(success=False, error=status_info["error"], code=http_code)

    status_info["server_url"] = analyzer.client.api_url
    try:
        is_available = analyzer.client.check_server()
        status_info["available"] = is_available
        if not is_available:
            status_info["error"] = "Server did not respond or is unavailable."
            http_code = http.HTTPStatus.SERVICE_UNAVAILABLE
            gpt4all_logger.warning(f"GPT4All server check failed: {status_info['server_url']}")
        else:
            gpt4all_logger.info(f"GPT4All server check successful: {status_info['server_url']}")

    except Exception as e:
        status_info["error"] = f"Error during server check: {str(e)}"
        http_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
        gpt4all_logger.exception(f"Error checking GPT4All server status: {e}")

    return APIResponse(
        success=status_info["available"], error=status_info["error"],
        data={"available": status_info["available"], "server_url": status_info["server_url"]},
        code=http_code
    )


@gpt4all_bp.route("/gpt4all-analysis", methods=["GET", "POST"])
def legacy_analysis_redirect():
    """Redirects legacy URL to the new /analysis endpoint."""
    gpt4all_logger.info("Redirecting from legacy /gpt4all-analysis to /gpt4all/analysis")
    return redirect(url_for('gpt4all.gpt4all_analysis', **request.args))


@gpt4all_bp.route("/ping", methods=["GET"])
@ajax_compatible
def ping():
    """Simple health check endpoint for the GPT4All blueprint."""
    gpt4all_logger.info("Ping request received for gpt4all blueprint.")
    return {"status": "success", "message": "GPT4All routes are active."}