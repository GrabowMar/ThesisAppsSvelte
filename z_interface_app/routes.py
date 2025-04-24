"""
Route handlers for the AI Model Management System.
"""

# =============================================================================
# Standard Library Imports
# =============================================================================
# import asyncio # Removed: Appears unused
import http # Added
import json
# import random # Removed: Appears unused
import subprocess # Moved from local imports
import threading
import time # Moved from __import__
import traceback # Kept for gpt4all_analysis exception logging
from dataclasses import asdict # Moved from local imports
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple # Kept necessary typing

# =============================================================================
# Third-Party Imports
# =============================================================================
# Note: psutil is optional, used in system_info
try:
    import psutil
except ImportError:
    psutil = None # Make psutil None if not installed

from flask import (
    Blueprint, Response, current_app, flash, jsonify,
    redirect, render_template, request, url_for, send_file # Added send_file here
    # Removed unused: make_response, send_from_directory, g
)
from werkzeug.exceptions import BadRequest, HTTPException
# Removed unused: InternalServerError, ServiceUnavailable

# =============================================================================
# Custom Module Imports
# =============================================================================
from logging_service import create_logger_for_component
from services import (
    DockerManager, ScanManager, SystemHealthMonitor, call_ai_service, # Kept SystemHealthMonitor
    create_scanner
)
from utils import (
    AIModel, AI_MODELS, APIResponse, CustomJSONEncoder, # Added CustomJSONEncoder (implicitly used by jsonify)
    _AJAX_REQUEST_HEADER_NAME, _AJAX_REQUEST_HEADER_VALUE, # Added AJAX constants
    ajax_compatible, get_all_apps, get_app_container_statuses,
    get_app_directory, get_app_info, get_apps_for_model,
    get_container_names, get_model_index, get_scan_manager,
    handle_docker_action, process_security_analysis, stop_zap_scanners, # Added stop_zap_scanners (was missing)
    verify_container_health
)

# =============================================================================
# Blueprint Definitions
# =============================================================================
main_bp = Blueprint("main", __name__)
api_bp = Blueprint("api", __name__, url_prefix="/api") # Added url_prefix for consistency
analysis_bp = Blueprint("analysis", __name__)
performance_bp = Blueprint("performance", __name__, url_prefix="/performance")
gpt4all_bp = Blueprint("gpt4all", __name__, url_prefix="/gpt4all") # Added url_prefix
zap_bp = Blueprint("zap", __name__, url_prefix="/zap") # Added url_prefix

# =============================================================================
# Route Loggers
# =============================================================================
# It's often better to create loggers per blueprint or section if needed frequently
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
            # Get docker-compose logs using helper for consistency
            # Note: run_docker_compose uses -p and -f flags, which might differ slightly
            # from a raw 'docker-compose logs' command if setup relies on CWD only.
            # Sticking to subprocess here for raw 'logs' command if intended.
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

    Args:
        model: Model name.
        app_num: App number (1-based).

    Returns:
        JSON status for AJAX requests.
        For regular requests, the decorator might return an error or simple response
        if the return value isn't suitable for non-AJAX.
        Consider adding specific non-AJAX handling if needed beyond AJAX.
    """
    main_route_logger.debug(f"Checking status for {model}/app{app_num}")
    docker_manager: DockerManager = current_app.config["docker_manager"]
    status = get_app_container_statuses(model, app_num, docker_manager)
    # Let the decorator handle returning JSON for AJAX.
    # For non-AJAX, returning the dict might not be useful.
    # If non-AJAX support is needed, consider returning a redirect/flash explicitly.
    # However, this endpoint is likely only called via AJAX based on previous logic.
    return status


@main_bp.route("/batch/<action>/<string:model>", methods=["POST"])
@ajax_compatible # Handles JSON response / errors
def batch_docker_action(action: str, model: str):
    """
    Perform batch Docker operations on all apps for a specific model.

    Args:
        action: The action ('start', 'stop', 'restart', 'build', 'rebuild', 'health-check').
        model: The model name.

    Returns:
        JSON response with batch results.
    """
    main_route_logger.info(f"Batch action '{action}' requested for model '{model}'")

    # Validate the action
    valid_actions = ["start", "stop", "restart", "build", "rebuild", "health-check"]
    if action not in valid_actions:
        main_route_logger.warning(f"Invalid batch action requested: {action}")
        # Return APIResponse for decorator to handle
        return APIResponse(
            success=False,
            error=f"Invalid action: {action}",
            code=http.HTTPStatus.BAD_REQUEST
        )

    # Get all apps for the model
    apps = get_apps_for_model(model)
    if not apps:
        main_route_logger.warning(f"No apps found for model '{model}' for batch action '{action}'")
        return APIResponse(
            success=False,
            error=f"No apps found for model {model}",
            code=http.HTTPStatus.NOT_FOUND
        )

    # Process all apps
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
                 # Pass check=False to handle_docker_action via run_docker_compose if needed,
                 # otherwise handle_docker_action's run_docker_compose call defaults check=True
                 success, message = handle_docker_action(action, model, app_num)
                 result_entry["success"] = success
                 result_entry["message"] = message
        except Exception as e:
            main_route_logger.exception(f"Error during batch action '{action}' for {model}/app{app_num}: {e}")
            result_entry["message"] = f"Unexpected error: {str(e)}"
        results.append(result_entry)

    # Summarize results
    success_count = sum(1 for r in results if r["success"])
    status = "success" if success_count == len(results) else "partial" if success_count > 0 else "error"
    main_route_logger.info(f"Batch action '{action}' for '{model}' completed: {status} ({success_count}/{len(results)} succeeded)")

    # Return raw dict - decorator will jsonify
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

    Args:
        model: Model name.
        app_num: App number (1-based).

    Returns:
        Rendered template with logs.
    """
    main_route_logger.info(f"Viewing container logs for {model}/app{app_num}")
    logs_data = {"backend": "Error retrieving logs.", "frontend": "Error retrieving logs."}
    try:
        docker_manager: DockerManager = current_app.config["docker_manager"]
        b_name, f_name = get_container_names(model, app_num)

        main_route_logger.debug(f"Fetching logs for containers: {b_name}, {f_name}")
        logs_data["backend"] = docker_manager.get_container_logs(b_name)
        logs_data["frontend"] = docker_manager.get_container_logs(f_name)

    except ValueError as e: # Catch errors from get_container_names
        main_route_logger.error(f"Invalid model/app for log view {model}/app{app_num}: {e}")
        flash(f"Invalid application specified: {e}", "error")
        # Redirect only for non-AJAX, decorator handles AJAX error
        if request.headers.get(_AJAX_REQUEST_HEADER_NAME) != _AJAX_REQUEST_HEADER_VALUE:
             return redirect(url_for("main.index"))
        else:
             # Let decorator handle error conversion for AJAX
             raise BadRequest(f"Invalid application specified: {e}") from e
    except Exception as e:
         main_route_logger.exception(f"Error retrieving logs for {model}/app{app_num}: {e}")
         # Let decorator handle error conversion
         raise InternalServerError(f"Failed to retrieve logs: {e}") from e

    return render_template("logs.html", logs=logs_data, model=model, app_num=app_num)


@main_bp.route("/<action>/<string:model>/<int:app_num>", methods=["POST"]) # Added POST method restriction
@ajax_compatible # Handles JSON response / errors
def handle_docker_action_route(action: str, model: str, app_num: int):
    """
    Handle Docker action (start, stop, restart, build, rebuild) for an app via POST.

    Args:
        action: Action to perform.
        model: Model name.
        app_num: App number (1-based).

    Returns:
        APIResponse object (decorator handles conversion).
    """
    main_route_logger.info(f"Docker action '{action}' requested for {model}/app{app_num} via POST")

    try:
        success, message = handle_docker_action(action, model, app_num)

        # Return APIResponse - decorator handles AJAX/non-AJAX conversion
        # (Though for non-AJAX POST, redirect is usually better)
        response = APIResponse(
            success=success,
            message=message,
            code=http.HTTPStatus.OK if success else http.HTTPStatus.INTERNAL_SERVER_ERROR
        )

        # If it's NOT an AJAX request, flash message and redirect instead of returning APIResponse directly
        if request.headers.get(_AJAX_REQUEST_HEADER_NAME) != _AJAX_REQUEST_HEADER_VALUE:
             flash(f"{'Success' if success else 'Error'}: {message[:500]}...", "success" if success else "error") # Limit flash message length
             return redirect(url_for("main.index"))
        else:
             # Let decorator handle the APIResponse for AJAX
             return response

    except Exception as e:
         main_route_logger.exception(f"Unexpected error handling docker action '{action}' for {model}/app{app_num}: {e}")
         # Let decorator handle exception conversion
         raise InternalServerError(f"Failed to execute action '{action}': {e}") from e


# =============================================================================
# API Routes (/api)
# =============================================================================
@api_bp.route("/system-info")
@ajax_compatible # Handles JSON response / errors
def system_info():
    """
    Get detailed system information for the dashboard.

    Returns:
        Dictionary with system metrics, health status, and resource utilization.
    """
    api_logger.debug("System info requested")
    docker_manager: DockerManager = current_app.config["docker_manager"]
    system_health_metrics = {}
    docker_status = {"healthy": False, "client_available": False, "containers": {"running": 0, "stopped": 0, "total": 0}}
    app_stats = {"total": 0, "models": {}, "status": {"running": 0, "partial": 0, "stopped": 0}}

    # 1. Get basic system metrics (CPU, Mem, Disk, Uptime)
    if psutil:
        try:
            api_logger.debug("Getting system metrics using psutil")
            cpu_percent = psutil.cpu_percent(interval=0.1) # Shorter interval
            memory = psutil.virtual_memory()
            # Get disk usage for root ('/') and potentially BASE_DIR parent if different
            disk_usage_root = psutil.disk_usage('/')
            # base_dir_parent = current_app.config['BASE_DIR'].parent
            # disk_usage_base = psutil.disk_usage(str(base_dir_parent)) # Needs error handling if path invalid

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
            docker_status["healthy"] = False # Assume unhealthy if error occurs
            docker_status["error"] = str(e)

    # 3. Get app overview stats
    try:
        apps = get_all_apps()
        app_stats["total"] = len(apps)
        app_stats["models"] = {model.name: 0 for model in AI_MODELS}
        for app in apps:
            model_name = app["model"]
            if model_name in app_stats["models"]:
                app_stats["models"][model_name] += 1

        # Get app status counts (sampling)
        # NOTE: Sampling might give inaccurate counts if first 10 aren't representative.
        sample_size = 10
        api_logger.debug(f"Sampling app statuses for dashboard (sample size: {sample_size} apps)")
        sampled_apps = apps[:sample_size]
        running, partial, stopped = 0, 0, 0
        if docker_status["client_available"]: # Only check statuses if Docker is available
             for app in sampled_apps:
                 try:
                     statuses = get_app_container_statuses(app["model"], app["app_num"], docker_manager)
                     if statuses.get("error"): continue # Skip apps where status failed

                     backend_running = statuses.get("backend", {}).get("running", False)
                     frontend_running = statuses.get("frontend", {}).get("running", False)

                     if backend_running and frontend_running: running += 1
                     elif backend_running or frontend_running: partial += 1
                     else: stopped += 1
                 except Exception as e:
                     api_logger.exception(f"Error getting status for sampled app {app['model']}/{app['app_num']}: {e}")

             # Scale up the counts based on sampling
             if len(apps) > 0 and len(sampled_apps) > 0:
                 scale_factor = len(apps) / len(sampled_apps)
                 app_stats["status"]["running"] = int(running * scale_factor)
                 app_stats["status"]["partial"] = int(partial * scale_factor)
                 # Calculate stopped based on total to avoid rounding errors exceeding total
                 app_stats["status"]["stopped"] = app_stats["total"] - app_stats["status"]["running"] - app_stats["status"]["partial"]
             else: # Handle case with no apps or sample error
                 app_stats["status"]["stopped"] = app_stats["total"]
        else:
             # If docker isn't available, assume all are stopped for the overview
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

    Args:
        model: Model name.
        app_num: App number (1-based).

    Returns:
        Dictionary with container statuses or error info.
    """
    api_logger.debug(f"Container status requested for {model}/app{app_num}")
    docker_manager: DockerManager = current_app.config["docker_manager"]
    # get_app_container_statuses handles errors internally
    status = get_app_container_statuses(model, app_num, docker_manager)
    return status


@api_bp.route("/debug/docker/<string:model>/<int:app_num>")
@ajax_compatible # Handles JSON response / errors
def debug_docker_environment(model: str, app_num: int):
    """
    Debug endpoint to inspect Docker environment for an app.

    Args:
        model: Model name.
        app_num: App number (1-based).

    Returns:
        Dictionary with docker environment details.
    """
    api_logger.info(f"Docker environment debug requested for {model}/app{app_num}")
    debug_info = {"error": None}
    try:
        app_dir = get_app_directory(current_app, model, app_num) # Raises FileNotFoundError if invalid
        debug_info["directory_exists"] = True
        debug_info["app_directory"] = str(app_dir)

        # Check docker-compose file
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
                  compose_content = compose_file_path.read_text(encoding='utf-8', errors='replace')[:1000] + ("..." if len(compose_content)>1000 else "")
             except Exception as read_err:
                  compose_content = f"Error reading compose file: {read_err}"
        debug_info["compose_file_preview"] = compose_content

        # Check docker installation
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

        # Check docker-compose installation
        try:
             api_logger.debug("Checking Docker Compose version")
             # Try 'docker-compose' first, then 'docker compose'
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

        # Get container statuses
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
         # Let decorator handle conversion
         raise InternalServerError(f"Failed to get debug info: {e}") from e


@api_bp.route("/health/<string:model>/<int:app_num>")
@ajax_compatible # Handles JSON response
def check_container_health(model: str, app_num: int):
    """
    Check if containers for a specific app are healthy after startup.

    Args:
        model: Model name.
        app_num: App number (1-based).

    Returns:
        Dictionary with health status and message.
    """
    api_logger.debug(f"Health check requested for {model}/app{app_num}")
    docker_manager: DockerManager = current_app.config["docker_manager"]
    # verify_container_health handles internal errors and logging
    healthy, message = verify_container_health(docker_manager, model, app_num)
    api_logger.debug(f"Health check result for {model}/app{app_num}: {healthy} - {message}")
    return {"healthy": healthy, "message": message}


@api_bp.route("/status")
@ajax_compatible # Handles JSON response
def system_status():
    """
    Get overall system status (Docker and Disk).

    Returns:
        Dictionary with system status overview.
    """
    api_logger.debug("System status check requested")
    docker_manager: DockerManager = current_app.config["docker_manager"]
    docker_ok = False
    disk_ok = False
    details = {}

    try:
        # Check disk space first
        disk_ok = SystemHealthMonitor.check_disk_space()
        details["disk_space_ok"] = disk_ok

        # Check docker health
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

    Returns:
        List of dictionaries with model information.
    """
    api_logger.debug("Model information requested")
    model_info = []
    for idx, model in enumerate(AI_MODELS):
        try:
            # Get app count without throwing error if dir missing
            apps_list = get_apps_for_model(model.name) # Uses potentially bad get_app_directory
            app_count = len(apps_list)
            port_range = PortManager.get_port_range(idx)
            model_info.append({
                "name": model.name,
                "color": model.color,
                "ports": port_range,
                "total_apps": app_count,
            })
        except Exception as e:
             api_logger.exception(f"Error getting info for model '{model.name}': {e}")
             # Optionally include error status for this model
             model_info.append({
                 "name": model.name,
                 "color": model.color,
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

    Returns:
        JSON status response.
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

        # Create a structured error message from expected fields
        error_context = {
            "message": data.get('message', 'No message provided'),
            "url": data.get('url', 'N/A'),
            "file_info": f"{data.get('filename', 'N/A')}:{data.get('lineno', 'N/A')}:{data.get('colno', 'N/A')}",
            "user_agent": request.headers.get('User-Agent', 'N/A') # Get from headers
        }
        # Add extra details if available
        if 'stack' in data: error_context['stack_preview'] = data['stack'][:500] + '...' # Preview stack
        if 'context' in data: error_context['extra_context'] = data['context']

        # Log the client error with structured data
        client_error_logger.error(
            "ClientError: %(message)s | URL: %(url)s | File: %(file_info)s | UA: %(user_agent)s",
            error_context
        )
        # Log full stack separately at debug level if needed
        if 'stack' in data:
             client_error_logger.debug("Full Client Stack Trace:\n%s", data['stack'])

        return {"status": "logged"} # Simple success response

    except Exception as e:
        # Log error in the logger itself
        client_error_logger.exception("Error processing client error log request: %s", e)
        # Return generic server error to client
        # Avoid sending back detailed exception info from here
        return APIResponse(
            success=False,
            error="Server error while logging client error.",
            code=http.HTTPStatus.INTERNAL_SERVER_ERROR
        )


# =============================================================================
# ZAP Routes (/zap)
# =============================================================================
@zap_bp.route("/<string:model>/<int:app_num>")
@ajax_compatible # Returns rendered template or handles errors
def zap_scan_page(model: str, app_num: int):
    """
    Display the ZAP scanner page for a specific app, showing previous results if available.

    Args:
        model: Model name.
        app_num: App number (1-based).

    Returns:
        Rendered ZAP scan template.
    """
    zap_logger.info(f"ZAP scan page requested for {model}/app{app_num}")
    alerts = []
    error_msg = None
    summary = {"high":0, "medium":0, "low":0, "info":0, "vulnerabilities_with_code": 0}
    results_exist = False

    try:
        base_dir = Path(current_app.config["BASE_DIR"])
        # Use helper to get validated app directory path
        app_dir = get_app_directory(current_app, model, app_num)
        results_file = app_dir / ".zap_results.json"
        results_exist = results_file.exists()

        if results_exist:
            zap_logger.debug(f"Loading previous scan results from {results_file}")
            try:
                if results_file.stat().st_size > 10: # Basic check for content
                    with open(results_file, 'r', encoding='utf-8', errors='replace') as f:
                         data = json.load(f)
                    alerts = data.get("alerts", [])
                    # Recalculate summary from loaded alerts
                    for alert in alerts:
                         risk = alert.get("risk", "").lower()
                         if risk in summary: summary[risk] += 1
                         if alert.get('affected_code') and alert.get('affected_code', {}).get('snippet'):
                              summary["vulnerabilities_with_code"] += 1
                    zap_logger.info(f"Loaded {len(alerts)} alerts ({summary['high']}H/{summary['medium']}M/{summary['low']}L) from previous scan.")
                else:
                     zap_logger.warning(f"Previous results file exists but is empty: {results_file}")
                     error_msg = "Previous scan results file is empty."
            except json.JSONDecodeError as json_err:
                error_msg = f"Failed to parse previous results file: {json_err}"
                zap_logger.exception(error_msg)
            except Exception as e:
                error_msg = f"Failed to load previous results: {e}"
                zap_logger.exception(error_msg)
        else:
            zap_logger.debug(f"No previous scan results file found at {results_file}")

    except FileNotFoundError as e:
         error_msg = f"Application directory not found: {e}"
         zap_logger.error(error_msg)
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

    Args:
        model: Model name.
        app_num: App number (1-based).

    Returns:
        JSON response indicating scan start status.
    """
    zap_logger.info(f"Request received to start ZAP scan for {model}/app{app_num}")
    scan_manager = get_scan_manager()

    # Check for existing *active* scan
    latest_scan_info = scan_manager.get_latest_scan_for_app(model, app_num)
    if latest_scan_info:
        _, latest_scan = latest_scan_info
        active_statuses = {
            ScanStatus.STARTING.value, ScanStatus.SPIDERING.value, ScanStatus.SCANNING.value
        }
        if latest_scan.get("status") in active_statuses:
            zap_logger.warning(f"ZAP scan already in progress for {model}/app{app_num}: Status={latest_scan['status']}")
            return APIResponse(success=False, error="A scan is already running for this app.", code=http.HTTPStatus.CONFLICT)

    # Create new scan entry
    # Pass empty options for now, could add scan type etc. later
    scan_id = scan_manager.create_scan(model, app_num, {})
    zap_logger.info(f"Created new scan entry with ID: {scan_id}")

    def run_scan_thread(app_context, scan_id_thread, model_thread, app_num_thread):
        """Target function for the background scan thread."""
        # Push context for access to current_app.config etc.
        with app_context:
            scan_thread_logger = create_logger_for_component(f'zap.thread.{model_thread}-{app_num_thread}')
            scan_thread_logger.info(f"Background scan thread starting for scan ID: {scan_id_thread}")
            scanner = None # Initialize scanner to None
            try:
                base_dir_thread = Path(current_app.config["BASE_DIR"])
                app_dir_thread = get_app_directory(current_app, model_thread, app_num_thread) # Raises FileNotFoundError

                scan_thread_logger.info(f"Initializing ZAP scanner instance for {model_thread}/app{app_num_thread}")
                # Ensure create_scanner uses appropriate base path if needed
                scanner = create_scanner(base_dir_thread)

                # Set source code root (relative to app_dir or absolute?)
                # Assuming scanner needs absolute path to source code within app dir
                scan_thread_logger.info(f"Setting source code root directory to {app_dir_thread}")
                scanner.set_source_code_root(str(app_dir_thread))

                # Update scan manager with scanner instance and initial status
                current_scan_manager = get_scan_manager() # Get manager within context
                current_scan_manager.update_scan(
                    scan_id_thread,
                    scanner=scanner, # Store the scanner instance if needed later (e.g., for stop)
                    status=ScanStatus.STARTING.value,
                    progress=0, # Reset progress fields
                    spider_progress=0, passive_progress=0, active_progress=0, ajax_progress=0,
                    start_time=datetime.now().isoformat(),
                    end_time=None, # Clear end time
                    results=None # Clear previous results info if any
                )

                # Start the actual scan
                scan_thread_logger.info(f"Starting comprehensive ZAP scan for {model_thread}/app{app_num_thread}")
                # The start_scan method should handle internal progress updates via callbacks or internal logic
                success = scanner.start_scan(model_thread, app_num_thread) # This call blocks until scan finishes or fails

                # Process results after scan finishes
                scan_thread_logger.info(f"Scan finished for {scan_id_thread}. Success: {success}")
                final_status = ScanStatus.COMPLETE.value if success else ScanStatus.FAILED.value
                final_progress = 100 if success else 0 # Or get final progress from scanner if possible

                # Read results file for final summary info
                results_file = app_dir_thread / ".zap_results.json"
                summary_data = {}
                if results_file.exists() and results_file.stat().st_size > 10:
                     try:
                          with open(results_file, 'r', encoding='utf-8') as f:
                               results_json = json.load(f)
                          summary_data = results_json.get("summary", {})
                     except Exception as read_err:
                          scan_thread_logger.error(f"Failed to read summary from results file {results_file}: {read_err}")

                current_scan_manager.update_scan(
                    scan_id_thread,
                    status=final_status,
                    progress=final_progress, # Mark as 100% if complete
                    # Assume sub-progress also 100% on success, 0 on fail? Or get from scanner?
                    spider_progress=final_progress, passive_progress=final_progress, active_progress=final_progress, ajax_progress=final_progress,
                    end_time=datetime.now().isoformat(),
                    # Extract summary details if available
                    duration_seconds=summary_data.get("duration_seconds"),
                    vulnerabilities_with_code=summary_data.get("vulnerabilities_with_code")
                )
                scan_thread_logger.info(f"Scan {scan_id_thread} final status updated to {final_status}")

            except FileNotFoundError as e:
                 scan_thread_logger.error(f"Cannot start scan {scan_id_thread}, directory not found: {e}")
                 get_scan_manager().update_scan(scan_id_thread, status=ScanStatus.ERROR.value, progress=0, error=f"Directory not found: {e}")
            except Exception as e:
                scan_thread_logger.exception(f"Error during background scan {scan_id_thread}: {e}")
                # Update scan status to Failed with error message
                get_scan_manager().update_scan(scan_id_thread, status=ScanStatus.FAILED.value, progress=0, error=str(e))
            finally:
                # Ensure ZAP resources associated with this scan are cleaned up
                if scanner and hasattr(scanner, '_cleanup_existing_zap'):
                    try:
                        scan_thread_logger.info(f"Cleaning up ZAP resources for scan {scan_id_thread}")
                        # Call internal cleanup method directly if needed and safe
                        scanner._cleanup_existing_zap()
                        scan_thread_logger.info(f"ZAP resources cleanup finished for scan {scan_id_thread}")
                    except Exception as cleanup_error:
                        scan_thread_logger.exception(f"Error cleaning up ZAP resources for scan {scan_id_thread}: {cleanup_error}")
                # Optionally clean up old completed/failed scans from manager state
                get_scan_manager().cleanup_old_scans()
            scan_thread_logger.info(f"Background scan thread finished for scan ID: {scan_id_thread}")

    # Start scan in background thread, passing necessary data and app context
    thread = threading.Thread(
        target=run_scan_thread,
        args=(current_app.app_context(), scan_id, model, app_num), # Pass context and args
        daemon=True # Allow app to exit even if thread hangs (maybe False is safer?)
    )
    thread.name = f"zap-scan-{model}-{app_num}"
    thread.start()
    zap_logger.info(f"Background scan thread '{thread.name}' started for scan ID {scan_id}.")

    # Return immediate success response, client will poll for status
    return {"status": "started", "scan_id": scan_id}


@zap_bp.route("/scan/<string:model>/<int:app_num>/status")
@ajax_compatible # Handles JSON response
def zap_scan_status(model: str, app_num: int):
    """
    Get the status of the latest ZAP scan for an app, including progress and alert counts.

    Args:
        model: Model name.
        app_num: App number (1-based).

    Returns:
        Dictionary with detailed scan status.
    """
    zap_logger.debug(f"Scan status requested for {model}/app{app_num}")
    scan_manager = get_scan_manager()
    latest_scan_info = scan_manager.get_latest_scan_for_app(model, app_num)

    # Default response if no scan found
    default_status = {
        "status": "Not Run", "progress": 0, "spider_progress": 0, "passive_progress": 0,
        "active_progress": 0, "ajax_progress": 0, "high_count": 0, "medium_count": 0,
        "low_count": 0, "info_count": 0, "vulnerabilities_with_code": 0, "scan_id": None,
        "start_time": None, "end_time": None, "duration_seconds": None, "error": None
    }

    if not latest_scan_info:
        zap_logger.debug(f"No scan history found for {model}/app{app_num}")
        return default_status

    scan_id, scan_state = latest_scan_info
    response = default_status.copy() # Start with defaults
    response.update({ # Update with current state from ScanManager
        "status": scan_state.get("status", "Unknown"),
        "progress": scan_state.get("progress", 0),
        "spider_progress": scan_state.get("spider_progress", 0),
        "passive_progress": scan_state.get("passive_progress", 0),
        "active_progress": scan_state.get("active_progress", 0),
        "ajax_progress": scan_state.get("ajax_progress", 0),
        "scan_id": scan_id,
        "start_time": scan_state.get("start_time"),
        "end_time": scan_state.get("end_time"),
        "duration_seconds": scan_state.get("duration_seconds"),
        "error": scan_state.get("error"),
        "vulnerabilities_with_code": scan_state.get("vulnerabilities_with_code", 0) # Get from state if available
    })


    # If scan is complete or failed, try reading counts from the results file
    # This ensures final counts are shown even if state update was missed
    if response["status"] in (ScanStatus.COMPLETE.value, ScanStatus.FAILED.value, ScanStatus.STOPPED.value, ScanStatus.ERROR.value):
        try:
            app_dir = get_app_directory(current_app, model, app_num) # Raises FileNotFoundError
            results_file = app_dir / ".zap_results.json"
            if results_file.exists() and results_file.stat().st_size > 10:
                with open(results_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                alerts = data.get("alerts", [])
                counts = {"high": 0, "medium": 0, "low": 0, "info": 0}
                vuln_with_code = 0
                for alert in alerts:
                    risk = alert.get("risk", "").lower()
                    if risk in counts: counts[risk] += 1
                    if alert.get('affected_code') and alert.get('affected_code', {}).get('snippet'):
                        vuln_with_code += 1
                # Update response with counts from file
                response.update({
                    "high_count": counts["high"],
                    "medium_count": counts["medium"],
                    "low_count": counts["low"],
                    "info_count": counts["info"],
                    "vulnerabilities_with_code": vuln_with_code
                })
                # Update duration from summary if present
                summary = data.get("summary", {})
                if "duration_seconds" in summary:
                     response["duration_seconds"] = summary["duration_seconds"]

                zap_logger.debug(f"Updated final counts/duration from results file for scan {scan_id}")

        except FileNotFoundError:
             zap_logger.warning(f"Cannot read final counts for {scan_id}, app directory not found.")
        except Exception as e:
            zap_logger.exception(f"Error reading final results file for scan {scan_id}: {e}")
            # Keep counts from scan_state if file reading fails

    return response


@zap_bp.route("/scan/<string:model>/<int:app_num>/stop", methods=["POST"])
@ajax_compatible # Handles JSON response / errors
def stop_zap_scan(model: str, app_num: int):
    """
    Stop a running ZAP scan for a specific app.

    Args:
        model: Model name.
        app_num: App number (1-based).

    Returns:
        JSON response indicating stop operation result.
    """
    zap_logger.info(f"Request to stop ZAP scan for {model}/app{app_num}")
    scan_manager = get_scan_manager()
    latest_scan_info = scan_manager.get_latest_scan_for_app(model, app_num)

    if not latest_scan_info:
        zap_logger.warning(f"Stop request failed: No scan found for {model}/app{app_num}")
        return APIResponse(success=False, error="No scan found for this app", code=http.HTTPStatus.NOT_FOUND)

    scan_id, scan_state = latest_scan_info
    active_statuses = {ScanStatus.STARTING.value, ScanStatus.SPIDERING.value, ScanStatus.SCANNING.value}

    if scan_state.get("status") not in active_statuses:
        current_status = scan_state.get("status", "Unknown")
        zap_logger.warning(f"Stop request ignored: Scan {scan_id} is not running (status: {current_status})")
        return APIResponse(success=False, error=f"Scan is not running (status: {current_status})", code=http.HTTPStatus.BAD_REQUEST)

    try:
        zap_logger.info(f"Attempting to stop scan ID {scan_id} ({model}/app{app_num})")
        scanner = scan_state.get("scanner") # Get the scanner instance associated with the scan

        if scanner and hasattr(scanner, "stop_scan") and callable(scanner.stop_scan):
             # Call the scanner's stop method - this might trigger cleanup internally
             zap_logger.debug(f"Calling scanner.stop_scan() for scan {scan_id}")
             # The stop_scan method should ideally handle ZAP shutdown/cleanup
             scanner.stop_scan(model=model, app_num=app_num) # Pass context if needed
             zap_logger.info(f"Scanner stop method called for scan {scan_id}")
        else:
             zap_logger.warning(f"No active scanner instance found or stop_scan method missing for scan {scan_id}. Attempting ZAP shutdown directly if possible.")
             # Fallback: Try generic cleanup if scanner instance isn't right, but this is less reliable
             # Consider adding a generic stop_zap_instance function if needed

        # Update scan manager state immediately to reflect stop request
        scan_manager.update_scan(
            scan_id,
            status=ScanStatus.STOPPED.value,
            progress=0, # Reset progress
            spider_progress=0, passive_progress=0, active_progress=0, ajax_progress=0,
            end_time=datetime.now().isoformat(),
            error="Scan stopped by user request." # Add note
        )

        zap_logger.info(f"Scan {scan_id} for {model}/app{app_num} marked as stopped.")
        return {"status": "stopped", "message": "Scan stop request processed."}

    except Exception as e:
        error_msg = f"Failed to stop scan {scan_id} for {model}/app{app_num}: {str(e)}"
        zap_logger.exception(error_msg)
        # Update status to error even if stop fails
        scan_manager.update_scan(scan_id, status=ScanStatus.ERROR.value, error=f"Failed during stop: {e}")
        return APIResponse(success=False, error=error_msg, code=http.HTTPStatus.INTERNAL_SERVER_ERROR)


@zap_bp.route("/code_report/<string:model>/<int:app_num>")
# @ajax_compatible - This returns a file download, not JSON
def download_code_report(model: str, app_num: int):
    """
    Download the generated ZAP code analysis report (Markdown).

    Args:
        model: Model name.
        app_num: App number (1-based).

    Returns:
        Markdown file download or Flask Response with error.
    """
    zap_logger.info(f"Code report download requested for {model}/app{app_num}")
    try:
        # Use helper to get validated app directory path
        app_dir = get_app_directory(current_app, model, app_num)
        report_file = app_dir / ".zap_code_report.md"

        if not report_file.is_file():
            zap_logger.warning(f"Code report file not found: {report_file}")
            flash("Code analysis report not found. Please run a ZAP scan first.", "error")
            return redirect(url_for('zap.zap_scan_page', model=model, app_num=app_num)) # Redirect back

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
         # Redirect to ZAP page or main index?
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

    Args:
        model: Model name.
        app_num: App number (1-based).

    Returns:
        JSON response indicating success or failure.
    """
    zap_logger.info(f"Code report regeneration requested for {model}/app{app_num}")
    try:
        base_dir = Path(current_app.config["BASE_DIR"])
        # Use helper to get validated app directory path
        app_dir = get_app_directory(current_app, model, app_num)
        results_file = app_dir / ".zap_results.json"
        report_file_path = app_dir / ".zap_code_report.md" # Define path for generation

        if not results_file.is_file() or results_file.stat().st_size < 10:
            msg = f"Valid ZAP results file not found at {results_file}. Cannot regenerate report."
            zap_logger.warning(msg)
            return APIResponse(success=False, error="Scan results not found or empty.", code=http.HTTPStatus.NOT_FOUND)

        zap_logger.info(f"Reading scan results from {results_file}")
        with open(results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        vulnerabilities = data.get("alerts", [])

        if not vulnerabilities:
            zap_logger.warning(f"No vulnerabilities found in scan results for {model}/app{app_num}")
            # Still generate an empty report? Or return error? Let's generate empty.
            # return APIResponse(success=False, error="No vulnerabilities found in scan results.", code=http.HTTPStatus.NOT_FOUND) # Changed mind

        # Create scanner instance (only needed for report generation method)
        # Assuming create_scanner doesn't have heavy init costs
        scanner = create_scanner(base_dir)

        # Generate report content using the scanner's method
        zap_logger.info(f"Generating code report content for {model}/app{app_num}")
        # Pass the target file path to the generation method
        report_content = scanner.generate_affected_code_report(vulnerabilities, str(report_file_path))

        # Count vulnerabilities with code snippets found in the original data
        vulnerabilities_with_code = sum(1 for v in vulnerabilities if v.get('affected_code') and v.get('affected_code', {}).get('snippet'))

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
        # Let decorator handle conversion
        raise InternalServerError(error_msg) from e


# =============================================================================
# Analysis Routes (/analysis - Implicit prefix)
# =============================================================================
@analysis_bp.route("/backend-security/<string:model>/<int:app_num>")
@ajax_compatible # Handles response formatting / errors
def security_analysis(model: str, app_num: int):
    """
    Run backend security analysis for an app and display results.

    Args:
        model: Model name.
        app_num: App number (1-based).

    Returns:
        Rendered template with security analysis results.
    """
    security_logger.info(f"Backend security analysis requested for {model}/app{app_num}")
    full_scan = request.args.get("full", "false").lower() == "true"

    if not hasattr(current_app, 'backend_security_analyzer'):
         security_logger.error("Backend security analyzer not available.")
         flash("Backend security analyzer is not configured.", "error")
         # How to handle non-AJAX return here? Redirect or render error template?
         return render_template("security_analysis.html", model=model, app_num=app_num, error="Analyzer not configured")

    analyzer = current_app.backend_security_analyzer
    # process_security_analysis returns a rendered Response object
    return process_security_analysis(
        template="security_analysis.html",
        analyzer=analyzer,
        # Assuming the method name is consistent, adjust if needed
        analysis_method=analyzer.run_security_analysis,
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

    Args:
        model: Model name.
        app_num: App number (1-based).

    Returns:
        Rendered template with security analysis results.
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


@analysis_bp.route("/security/analyze", methods=["POST"]) # Changed route to match others, added prefix implicitly
@ajax_compatible # Handles JSON response / errors
def analyze_security_issues():
    """
    Analyze a list of security issues (provided in JSON body) using an AI service.

    Returns:
        JSON with AI analysis results.
    """
    security_logger.info("AI security analysis requested via POST")
    try:
        data = request.get_json()
        if not data or not isinstance(data.get("issues"), list):
            security_logger.warning("No 'issues' list provided in JSON for AI security analysis")
            raise BadRequest("Request body must be JSON with an 'issues' list.")

        issues = data["issues"]
        model_name = data.get("model", "default-model") # AI model to use, not app model
        app_context_info = data.get("app_context", {}) # Optional context like app model/num

        security_logger.info(f"Analyzing {len(issues)} security issues using AI model '{model_name}'. App Context: {app_context_info}")

        # --- Build structured prompt (simplified example) ---
        prompt = f"# Security Analysis Request for {app_context_info.get('model', 'App')} / {app_context_info.get('app_num', '')}\n\n"
        prompt += f"## Issues ({len(issues)} total):\n"
        # Group by severity (example)
        issues.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.get('severity', 'low').lower(), 3))
        for i, issue in enumerate(issues[:20]): # Limit prompt length
            prompt += f"\n### Issue {i+1}: {issue.get('issue_type', 'Unknown Type')} ({issue.get('severity', 'N/A')})\n"
            prompt += f"- **Tool:** {issue.get('tool', 'N/A')}\n"
            prompt += f"- **Description:** {issue.get('issue_text', 'N/A')}\n"
            if issue.get('filename'): prompt += f"- **File:** {issue.get('filename')}\n"
            if issue.get('code'): prompt += f"- **Code Snippet:** ```\n{issue['code'][:200]}\n```\n" # Limit code snippet

        if len(issues) > 20: prompt += "\n...(additional issues truncated)..."

        prompt += """
## Analysis Tasks:
1. Summarize the key security risks based on the provided issues.
2. Provide prioritized recommendations for remediation (Top 3-5).
3. Briefly explain the potential impact if these issues are not addressed.
Please format the response clearly using Markdown."""
        # --- End Prompt Building ---

        security_logger.debug(f"Sending security analysis prompt (length: {len(prompt)}) to AI service '{model_name}'")
        analysis_result = call_ai_service(model_name, prompt) # Assuming call_ai_service exists and works
        security_logger.info("Received security analysis response from AI service")

        return APIResponse(success=True, data={"response": analysis_result})

    except BadRequest as e:
        security_logger.warning(f"Bad request in AI security analysis: {e}")
        # Let decorator handle conversion
        raise e
    except Exception as e:
        security_logger.exception(f"Error during AI security analysis: {e}")
        # Let decorator handle conversion
        raise InternalServerError("Failed to perform AI security analysis") from e


@analysis_bp.route("/security/summary/<string:model>/<int:app_num>")
@ajax_compatible # Handles JSON response / errors
def get_security_summary(model: str, app_num: int):
    """
    Get a combined security analysis summary (backend & frontend) for an app.

    Args:
        model: Model name.
        app_num: App number (1-based).

    Returns:
        Dictionary with combined security summary.
    """
    security_logger.info(f"Combined security summary requested for {model}/app{app_num}")
    backend_summary = {"total_issues": 0, "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0}}
    backend_status = {}
    frontend_summary = {"total_issues": 0, "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0}}
    frontend_status = {}
    error_details = []

    try:
        # Run backend analysis (quick mode)
        if hasattr(current_app, 'backend_security_analyzer'):
             analyzer = current_app.backend_security_analyzer
             security_logger.debug(f"Running backend security analysis for summary...")
             # Assuming analyze_security was the intended method, not run_security_analysis if that's the template one
             backend_issues, backend_status, _ = analyzer.analyze_security(model, app_num, use_all_tools=False)
             backend_summary = analyzer.get_analysis_summary(backend_issues)
             security_logger.debug(f"Backend summary: {backend_summary['total_issues']} issues.")
        else:
             error_details.append("Backend analyzer unavailable.")
             security_logger.warning("Backend security analyzer unavailable for summary.")

        # Run frontend analysis (quick mode)
        if hasattr(current_app, 'frontend_security_analyzer'):
             analyzer = current_app.frontend_security_analyzer
             security_logger.debug(f"Running frontend security analysis for summary...")
             frontend_issues, frontend_status, _ = analyzer.run_security_analysis(model, app_num, use_all_tools=False)
             frontend_summary = analyzer.get_analysis_summary(frontend_issues)
             security_logger.debug(f"Frontend summary: {frontend_summary['total_issues']} issues.")
        else:
             error_details.append("Frontend analyzer unavailable.")
             security_logger.warning("Frontend security analyzer unavailable for summary.")

        # Combine results
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
            "scan_time": datetime.now().isoformat(), # Time summary was generated
            "errors": error_details if error_details else None # Include errors if any occurred
        }
        return combined_summary

    except Exception as e:
        security_logger.exception(f"Error generating combined security summary for {model}/app{app_num}: {e}")
        # Let decorator handle conversion
        raise InternalServerError("Failed to generate security summary") from e


@analysis_bp.route("/security/analyze-file", methods=["POST"])
@ajax_compatible # Handles JSON response / errors
def analyze_single_file():
    """
    Analyze a single code file using the appropriate analyzer (backend/frontend).
    Expects JSON payload: {"file_path": "...", "is_frontend": true/false}

    Returns:
        JSON with analysis results for the specified file.
    """
    security_logger.info("Single file analysis requested via POST")
    try:
        data = request.get_json()
        if not data or "file_path" not in data:
            raise BadRequest("Request body must be JSON with a 'file_path' field.")

        # Security: Validate file_path belongs to the project base? Essential!
        # This example assumes file_path is trusted or validated elsewhere.
        # Never directly use user-provided paths without strict validation/sandboxing.
        file_path = Path(data["file_path"]) # Consider validating this path
        is_frontend = data.get("is_frontend", False)
        file_type = "frontend" if is_frontend else "backend"

        security_logger.info(f"Analyzing single {file_type} file: {file_path}")

        analyzer = None
        if is_frontend:
             if hasattr(current_app, 'frontend_security_analyzer'):
                  analyzer = current_app.frontend_security_analyzer
             else: raise RuntimeError("Frontend analyzer not available.")
        else:
             if hasattr(current_app, 'backend_security_analyzer'):
                  analyzer = current_app.backend_security_analyzer
             else: raise RuntimeError("Backend analyzer not available.")

        # Assuming analyzers have a common 'analyze_single_file' method
        # Or call specific tool methods like _run_eslint/_run_bandit as before
        if hasattr(analyzer, 'analyze_single_file') and callable(analyzer.analyze_single_file):
             security_logger.debug(f"Running analyzer.analyze_single_file on {file_path}")
             # This method should return the same structure: issues, tool_status, tool_output
             issues, tool_status, tool_output = analyzer.analyze_single_file(file_path)
        else:
             # Fallback to previous logic if generic method doesn't exist
             security_logger.warning(f"Analyzer {type(analyzer).__name__} missing 'analyze_single_file' method, using tool-specific fallback.")
             if is_frontend:
                  # Assuming _run_eslint takes directory, need adaptation for single file
                  # This logic needs adjustment based on how analyzers work
                  security_logger.error("Frontend single file analysis via _run_eslint not implemented correctly.")
                  raise NotImplementedError("Frontend single file analysis needs specific implementation.")
             else:
                  # Assuming _run_bandit takes directory, need adaptation
                  security_logger.error("Backend single file analysis via _run_bandit not implemented correctly.")
                  raise NotImplementedError("Backend single file analysis needs specific implementation.")


        security_logger.info(f"Found {len(issues)} issues in {file_path.name}")

        return {
            "status": "success",
            "issues": [asdict(issue) for issue in issues], # Convert Issue objects if they are dataclasses
            "tool_status": tool_status,
            "tool_output": tool_output,
        }
    except BadRequest as e:
         security_logger.warning(f"Bad request in single file analysis: {e}")
         raise e # Let decorator handle
    except FileNotFoundError as e:
         security_logger.error(f"File not found for analysis: {e}")
         return APIResponse(success=False, error=f"File not found: {e}", code=http.HTTPStatus.NOT_FOUND)
    except (RuntimeError, NotImplementedError) as e:
         security_logger.error(f"Configuration or implementation error during file analysis: {e}")
         # Let decorator handle
         raise InternalServerError(f"Analysis error: {e}") from e
    except Exception as e:
        security_logger.exception(f"Unexpected error analyzing file: {e}")
        # Let decorator handle
        raise InternalServerError("File analysis failed due to an unexpected error.") from e


# =============================================================================
# Performance Testing Routes (/performance)
# =============================================================================
@performance_bp.route("/<string:model>/<int:port>", methods=["GET", "POST"])
@ajax_compatible # Handles response formatting / errors
def performance_test(model: str, port: int):
    """
    Display performance test page (GET) or run a test (POST).

    Args:
        model: The model identifier.
        port: The port of the application backend/frontend to test.

    Returns:
        Rendered template (GET) or JSON results (POST).
    """
    if not hasattr(current_app, 'performance_tester'):
         msg = "Performance tester service is not available."
         perf_logger.error(msg)
         if request.method == "POST":
              raise RuntimeError(msg) # Let decorator handle for API call
         else:
              flash(msg, "error")
              # Need a way to display error on GET, maybe render template with error
              return render_template("performance_test.html", model=model, port=port, error=msg)

    tester = current_app.performance_tester
    base_dir = Path(current_app.config.get("BASE_DIR", "."))
    output_dir = base_dir / "performance_reports" # Defined in tester or config? Assume here for now

    if request.method == "POST":
        perf_logger.info(f"Starting performance test POST request for {model} on port {port}")
        try:
            data = request.get_json()
            if not data: raise BadRequest("Missing JSON request body.")

            num_users = int(data.get("num_users", 10))
            duration = int(data.get("duration", 30))
            spawn_rate = int(data.get("spawn_rate", 1))
            # Expecting endpoints as list of strings or list of dicts
            endpoints_raw = data.get("endpoints", ["/"])

            # Validate parameters
            if not (num_users > 0 and duration > 0 and spawn_rate > 0):
                 raise BadRequest("Number of users, duration, and spawn rate must be positive integers.")
            if not endpoints_raw:
                 raise BadRequest("At least one endpoint path must be provided.")

            perf_logger.info(
                f"Test parameters: users={num_users}, duration={duration}s, "
                f"spawn_rate={spawn_rate}, raw_endpoints={endpoints_raw}"
            )

            # Format endpoints if needed (assuming tester expects list of dicts)
            formatted_endpoints = []
            for ep in endpoints_raw:
                if isinstance(ep, str):
                     formatted_endpoints.append({"path": ep, "method": "GET", "weight": 1})
                elif isinstance(ep, dict) and "path" in ep: # Basic check for dict format
                     formatted_endpoints.append(ep)
                else: raise BadRequest(f"Invalid endpoint format: {ep}")


            # Generate a unique test name/ID for report storage
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            test_name = f"{model}_{port}_{timestamp}"
            host_url = f"http://localhost:{port}" # TODO: Make host configurable?

            perf_logger.info(f"Running performance test '{test_name}' against {host_url}")
            # Assuming run_test_cli returns a results object or dict, or raises error
            result_data = tester.run_test_cli(
                test_name=test_name,
                host=host_url,
                endpoints=formatted_endpoints,
                user_count=num_users,
                spawn_rate=spawn_rate,
                run_time=f"{duration}s",
                html_report=True,
                # output_dir should be handled internally by tester? Pass if needed.
            )

            perf_logger.info(f"Test '{test_name}' completed.")
            # Try to find report path (logic might be internal to tester)
            # This assumes tester creates reports in output_dir/test_name/*_report.html
            report_path_rel = None
            try:
                 test_output_dir = output_dir / test_name
                 report_files = list(test_output_dir.glob("*_report.html"))
                 if report_files:
                      report_path = report_files[0]
                      # Path relative to static folder (assuming base_dir is project root)
                      report_path_rel = Path("static") / report_path.relative_to(base_dir)
                      perf_logger.info(f"Report generated: {report_path_rel}")
            except Exception as report_err:
                 perf_logger.warning(f"Could not determine report path for {test_name}: {report_err}")

            # Return success with results data and report path if found
            return {
                "status": "success",
                "message": f"Test '{test_name}' completed.",
                "data": result_data, # Raw results from tester
                "report_url": url_for('static', filename=str(report_path_rel).replace('\\', '/')) if report_path_rel else None
            }

        except BadRequest as e:
             perf_logger.warning(f"Bad request for performance test: {e}")
             raise e # Let decorator handle
        except Exception as e:
            perf_logger.exception(f"Performance test execution error for {model} on port {port}: {e}")
            # Let decorator handle
            raise InternalServerError("Test execution failed") from e
    else:
        # GET request - render the test form
        perf_logger.info(f"Rendering performance test form for {model} on port {port}")
        return render_template("performance_test.html", model=model, port=port)


@performance_bp.route("/<string:model>/<int:port>/stop", methods=["POST"])
@ajax_compatible # Handles JSON response / errors
def stop_performance_test(model: str, port: int):
    """
    Stop a running performance test (Placeholder).

    Args:
        model: Model name.
        port: Port number.

    Returns:
        JSON indicating stop request was received.
    """
    perf_logger.info(f"Request to stop performance test for {model} on port {port}")
    try:
        # TODO: Implement actual test stopping logic
        # This would involve finding the process ID of the running Locust test
        # associated with model/port and terminating it gracefully (e.g., SIGTERM).
        perf_logger.warning("Performance test stopping is not yet implemented.")
        return {
            "status": "success", # Indicate request was received, not necessarily stopped
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

    Args:
        model: Model name.
        port: Port number.

    Returns:
        JSON list of available reports.
    """
    perf_logger.info(f"Listing performance reports for {model} on port {port}")
    reports = []
    try:
        base_dir = Path(current_app.config.get("BASE_DIR", "."))
        report_base_dir = base_dir / "performance_reports"
        if not report_base_dir.is_dir():
            perf_logger.debug(f"Report directory does not exist: {report_base_dir}")
            return {"reports": []} # Return empty list if base dir doesn't exist

        test_name_prefix = f"{model}_{port}_" # Pattern for directories

        for test_dir in report_base_dir.iterdir():
            # Check if it's a directory matching the pattern
            if test_dir.is_dir() and test_dir.name.startswith(test_name_prefix):
                report_id = test_dir.name # Use directory name as ID
                timestamp_str = report_id.replace(test_name_prefix, "") # Extract timestamp part
                formatted_time = "Unknown"
                try:
                     # Try parsing timestamp from dir name
                     dt_obj = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                     formatted_time = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                     perf_logger.warning(f"Could not parse timestamp from report directory: {report_id}")

                # Find the HTML report file within this directory
                html_report_path = next(test_dir.glob("*_report.html"), None)
                report_url = None
                if html_report_path:
                     # Generate URL relative to static folder
                     relative_path = Path("performance_reports") / report_id / html_report_path.name
                     report_url = url_for('static', filename=str(relative_path).replace('\\', '/'))

                # Find associated graphs
                graphs = []
                for graph_file in test_dir.glob("*.png"):
                     graph_rel_path = Path("performance_reports") / report_id / graph_file.name
                     graphs.append({
                         "name": graph_file.stem.replace("_", " ").title(),
                         "url": url_for('static', filename=str(graph_rel_path).replace('\\', '/'))
                     })

                reports.append({
                    "id": report_id,
                    "timestamp_str": timestamp_str, # Raw timestamp from dir name
                    "created": formatted_time,
                    "report_url": report_url,
                    "graphs": graphs
                })

        # Sort reports by timestamp descending
        reports.sort(key=lambda x: x.get("timestamp_str", ""), reverse=True)
        perf_logger.info(f"Found {len(reports)} performance reports for {model} on port {port}")
        return {"reports": reports}

    except Exception as e:
        perf_logger.exception(f"Error listing performance reports for {model} on port {port}: {e}")
        raise InternalServerError("Failed to list reports.") from e


@performance_bp.route("/<string:model>/<int:port>/reports/<path:report_id>", methods=["GET"])
# @ajax_compatible - This renders HTML directly
def view_performance_report(model: str, port: int, report_id: str):
    """
    View a specific performance test report HTML page.

    Args:
        model: Model name.
        port: Port number.
        report_id: Report directory ID (e.g., "ModelX_8000_20250424_120000").

    Returns:
        Rendered template containing the report or 404/500 error page.
    """
    perf_logger.info(f"Viewing performance report {report_id} for {model} on port {port}")
    try:
        base_dir = Path(current_app.config.get("BASE_DIR", "."))
        report_dir = base_dir / "performance_reports" / report_id

        # Security Check: Ensure report_id looks valid and matches model/port prefix
        expected_prefix = f"{model}_{port}_"
        # Basic validation: check prefix and avoid path traversal attempts
        if not report_id.startswith(expected_prefix) or ".." in report_id or "/" in report_id or "\\" in report_id:
             perf_logger.warning(f"Invalid or potentially unsafe report ID requested: {report_id}")
             return render_template("404.html", message="Invalid Report ID"), http.HTTPStatus.BAD_REQUEST

        if not report_dir.is_dir():
            perf_logger.warning(f"Report directory not found: {report_dir}")
            return render_template("404.html", message="Report not found"), http.HTTPStatus.NOT_FOUND

        # Find the primary HTML report file
        html_report_path = next(report_dir.glob("*_report.html"), None)
        if not html_report_path or not html_report_path.is_file():
             perf_logger.warning(f"No HTML report file found in directory: {report_dir}")
             return render_template("404.html", message="Report file not found"), http.HTTPStatus.NOT_FOUND

        perf_logger.debug(f"Loading report content from: {html_report_path}")
        with open(html_report_path, "r", encoding='utf-8', errors='replace') as f:
            report_content = f.read()

        # Find associated graphs for display
        graphs = []
        for graph_file in report_dir.glob("*.png"):
             graph_rel_path = Path("performance_reports") / report_id / graph_file.name
             graphs.append({
                 "name": graph_file.stem.replace("_", " ").title(),
                 "url": url_for('static', filename=str(graph_rel_path).replace('\\', '/'))
             })

        perf_logger.info(f"Rendering report {report_id} with {len(graphs)} graphs.")
        return render_template(
            "performance_report_viewer.html",
            model=model,
            port=port,
            report_id=report_id,
            report_content=report_content, # Pass raw HTML (ensure template handles safely, e.g. via iframe or careful rendering)
            graphs=graphs
        )
    except Exception as e:
        perf_logger.exception(f"Error viewing performance report {report_id}: {e}")
        return render_template("500.html", error=f"Failed to load report: {e}"), http.HTTPStatus.INTERNAL_SERVER_ERROR


@performance_bp.route("/<string:model>/<int:port>/results/<path:report_id>", methods=["GET"])
@ajax_compatible # Handles JSON response / errors
def get_performance_results(model: str, port: int, report_id: str):
    """
    Get raw JSON or parsed CSV results for a specific performance test run.

    Args:
        model: Model name.
        port: Port number.
        report_id: Report directory ID.

    Returns:
        JSON containing test results data or error.
    """
    perf_logger.info(f"Getting raw performance results data for {report_id}")
    try:
        base_dir = Path(current_app.config.get("BASE_DIR", "."))
        report_dir = base_dir / "performance_reports" / report_id

        # Security Check (similar to view_performance_report)
        expected_prefix = f"{model}_{port}_"
        if not report_id.startswith(expected_prefix) or ".." in report_id or "/" in report_id or "\\" in report_id:
             perf_logger.warning(f"Invalid or potentially unsafe report ID for results: {report_id}")
             raise BadRequest("Invalid Report ID")

        if not report_dir.is_dir():
            perf_logger.warning(f"Results directory not found: {report_dir}")
            raise FileNotFoundError("Report not found")

        # Prioritize JSON results file if it exists
        json_file = next(report_dir.glob("*_results.json"), None) # Assuming a specific naming convention
        if json_file and json_file.is_file():
             perf_logger.debug(f"Loading JSON results from: {json_file}")
             with open(json_file, "r", encoding='utf-8', errors='replace') as f:
                  # Return the raw JSON data directly
                  return json.load(f)

        # If no JSON, look for stats CSV (and potentially parse it)
        stats_file = next(report_dir.glob("*_stats.csv"), None)
        if stats_file and stats_file.is_file():
             perf_logger.warning(f"No JSON results file found for {report_id}. CSV parsing not implemented.")
             # TODO: Implement CSV parsing if needed
             # For now, return message indicating CSV availability
             csv_rel_path = Path("performance_reports") / report_id / stats_file.name
             return {
                 "status": "partial",
                 "message": "Raw JSON results not found. CSV data available.",
                 "csv_url": url_for('static', filename=str(csv_rel_path).replace('\\', '/'))
             }

        perf_logger.warning(f"No suitable result data file (JSON or CSV) found in directory: {report_dir}")
        raise FileNotFoundError("No result data found for this report")

    except BadRequest as e:
         raise e # Let decorator handle
    except FileNotFoundError as e:
         return APIResponse(success=False, error=str(e), code=http.HTTPStatus.NOT_FOUND)
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

    Args:
        model: Model name.
        port: Port number.
        report_id: Report directory ID to delete.

    Returns:
        JSON indicating success or failure of deletion.
    """
    perf_logger.info(f"Request to delete performance report directory {report_id}")
    try:
        base_dir = Path(current_app.config.get("BASE_DIR", "."))
        report_dir = base_dir / "performance_reports" / report_id

        # Security Check (similar to view_performance_report)
        expected_prefix = f"{model}_{port}_"
        if not report_id.startswith(expected_prefix) or ".." in report_id or "/" in report_id or "\\" in report_id:
             perf_logger.warning(f"Invalid or potentially unsafe report ID for deletion: {report_id}")
             raise BadRequest("Invalid Report ID")

        if not report_dir.is_dir():
            perf_logger.warning(f"Report directory not found for deletion: {report_dir}")
            raise FileNotFoundError("Report not found")

        # Use shutil.rmtree for robust recursive directory deletion
        import shutil
        perf_logger.warning(f"Recursively deleting report directory: {report_dir}") # Log clearly!
        shutil.rmtree(report_dir)
        perf_logger.info(f"Successfully deleted report directory {report_id}")

        return {"status": "success", "message": f"Report {report_id} deleted successfully"}

    except BadRequest as e:
         raise e # Let decorator handle
    except FileNotFoundError as e:
         return APIResponse(success=False, error=str(e), code=http.HTTPStatus.NOT_FOUND)
    except Exception as e:
        perf_logger.exception(f"Error deleting performance report {report_id}: {e}")
        raise InternalServerError(f"Failed to delete report: {e}") from e


# =============================================================================
# GPT4All Routes (/gpt4all)
# =============================================================================
# Note: These routes were duplicated in the original provided file.
# Keeping one set here under the gpt4all_bp blueprint.

@gpt4all_bp.route("/analysis", methods=["GET", "POST"])
@ajax_compatible # Handles response formatting / errors
def gpt4all_analysis():
    """
    Main route for requirements analysis using GPT4All.
    Handles both rendering the analysis form (GET) and processing analysis requests (POST).

    Returns:
        Rendered template or JSON response (via decorator).
    """
    gpt4all_logger.info(f"Received {request.method} request for GPT4All analysis page/action")
    results = None
    requirements = []
    template_name = None
    error = None
    model = request.args.get("model") or request.form.get("model")
    app_num_str = request.args.get("app_num") or request.form.get("app_num")
    app_num = None

    # --- Parameter Validation ---
    if not model or not app_num_str:
        error = "Model and App Number are required parameters."
        gpt4all_logger.warning(error)
        if request.method == "POST": raise BadRequest(error) # Fail early for POST API calls
        # For GET, render template with error
    else:
        try:
            app_num = int(app_num_str)
            if app_num <= 0: raise ValueError("App number must be positive.")
        except ValueError as e:
            error = f"Invalid App Number: {app_num_str}. {e}"
            gpt4all_logger.warning(error)
            if request.method == "POST": raise BadRequest(error)

    if error: # If validation failed on GET
         flash(error, "error")
         return render_template(
             "requirements_check.html", model=model, app_num=None,
             requirements=[], results=None, error=error
         )

    # --- Analyzer and Server Check ---
    if not hasattr(current_app, 'gpt4all_analyzer'):
        error = "GPT4All analyzer service is not available."
        gpt4all_logger.error(error)
        if request.method == "POST": raise RuntimeError(error) # Let decorator handle as 500
        flash(error, "error")
        return render_template("requirements_check.html", model=model, app_num=app_num, error=error)

    analyzer = current_app.gpt4all_analyzer

    try:
        gpt4all_logger.debug("Checking GPT4All server availability...")
        if not analyzer.client or not analyzer.client.check_server():
            error = "GPT4All server is not available or not responding. Please ensure it is running."
            gpt4all_logger.error(error)
            if request.method == "POST": raise ConnectionError(error) # Let decorator handle as 500/503?
            flash(error, "error")
            return render_template("requirements_check.html", model=model, app_num=app_num, error=error)
        gpt4all_logger.debug("GPT4All server is available.")
    except Exception as server_error:
        error = f"Error checking GPT4All server: {server_error}"
        gpt4all_logger.exception(error)
        if request.method == "POST": raise ConnectionError(error) from server_error
        flash(error, "error")
        return render_template("requirements_check.html", model=model, app_num=app_num, error=error)

    # --- Get Default Requirements ---
    try:
        requirements, template_name = analyzer.get_requirements_for_app(app_num)
        gpt4all_logger.info(f"Loaded {len(requirements)} default requirements for {model}/app{app_num} from template '{template_name}'")
    except Exception as req_error:
        error = f"Could not load default requirements: {req_error}"
        gpt4all_logger.exception(error)
        # Proceed without default requirements, allow user input
        flash(error, "warning")
        requirements = [] # Ensure requirements is a list

    # --- Handle POST Request (Run Analysis) ---
    if request.method == "POST":
        gpt4all_logger.info(f"Processing analysis POST request for {model}/app{app_num}")
        # Allow overriding requirements from form
        if "requirements" in request.form:
             custom_requirements_text = request.form.get("requirements", "").strip()
             if custom_requirements_text:
                  custom_requirements = [r.strip() for r in custom_requirements_text.splitlines() if r.strip()]
                  if custom_requirements:
                       requirements = custom_requirements # Override default/loaded requirements
                       gpt4all_logger.info(f"Using {len(requirements)} custom requirements provided in form.")
                  else:
                       gpt4all_logger.warning("Custom requirements field was present but empty after stripping.")

        # Get selected AI model from form if provided
        selected_ai_model = request.form.get("gpt4all_model")
        if selected_ai_model:
             gpt4all_logger.info(f"Using selected AI model for analysis: {selected_ai_model}")
             analyzer.client.preferred_model = selected_ai_model # Assuming client has this attribute

        if not requirements:
            gpt4all_logger.warning("No requirements available to perform analysis.")
            flash("No requirements found or provided. Cannot run analysis.", "error")
            # Re-render form
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
            if not results:
                 flash("Analysis ran but returned no results.", "warning")
            else:
                 flash("Analysis completed successfully.", "success")
        except Exception as analysis_error:
            error = f"Analysis failed: {analysis_error}"
            gpt4all_logger.exception(error)
            flash(error, "error")
            # Fall through to render template with error

    # --- Render Template (GET or POST) ---
    return render_template(
        "requirements_check.html",
        model=model,
        app_num=app_num,
        requirements=requirements,
        template_name=template_name,
        results=results, # Will be None on GET or if POST failed before analysis
        error=error      # Will be None on GET or if POST succeeded
    )

@gpt4all_bp.route("/api/requirements-check", methods=["POST"])
@ajax_compatible # Handles JSON response / errors
def api_requirements_check():
    """
    API endpoint for checking requirements against code (JSON request/response).

    Returns:
        JSON with check results or error information.
    """
    gpt4all_logger.info("API requirements check received via POST")
    try:
        data = request.get_json()
        if not data: raise BadRequest("Request body must be JSON.")

        model = data.get("model")
        app_num_str = data.get("app_num") # Allow string or int
        requirements = data.get("requirements") # Should be list of strings
        selected_ai_model = data.get("gpt4all_model") # Optional AI model override

        # --- Validation ---
        if not model or app_num_str is None:
             raise BadRequest("Missing required fields: 'model' and 'app_num'.")
        try:
            app_num = int(app_num_str)
            if app_num <= 0: raise ValueError("App number must be positive.")
        except (ValueError, TypeError) as e:
            raise BadRequest(f"Invalid 'app_num': {app_num_str}. Must be a positive integer.") from e
        if requirements is not None and not isinstance(requirements, list):
             raise BadRequest("'requirements' field must be a list of strings.")

        # --- Analyzer and Server Check ---
        if not hasattr(current_app, 'gpt4all_analyzer'):
             raise RuntimeError("GPT4All analyzer service is not available.") # Let decorator handle as 500
        analyzer = current_app.gpt4all_analyzer
        if not analyzer.client or not analyzer.client.check_server():
             raise ConnectionError("GPT4All server is not available or not responding.") # Let decorator handle as 500/503?

        # --- Get/Use Requirements ---
        if not requirements: # If list is empty or None/missing
             gpt4all_logger.debug(f"No requirements in request for {model}/{app_num}, fetching defaults.")
             try:
                  requirements, _ = analyzer.get_requirements_for_app(app_num)
                  if not requirements: raise ValueError("No default requirements found.")
                  gpt4all_logger.info(f"Using {len(requirements)} default requirements.")
             except Exception as req_error:
                  gpt4all_logger.exception(f"Failed to get default requirements for {model}/{app_num}: {req_error}")
                  raise RuntimeError(f"Could not load requirements: {req_error}") from req_error
        else:
             # Clean provided requirements
             requirements = [r.strip() for r in requirements if isinstance(r, str) and r.strip()]
             if not requirements:
                  raise BadRequest("Provided 'requirements' list was empty after cleanup.")
             gpt4all_logger.info(f"Using {len(requirements)} requirements from request.")

        # --- Run Analysis ---
        if selected_ai_model:
             gpt4all_logger.info(f"Using selected AI model for analysis: {selected_ai_model}")
             analyzer.client.preferred_model = selected_ai_model

        gpt4all_logger.info(f"Starting API requirements analysis for {model}/app{app_num}...")
        start_timer = time.time()
        results = analyzer.check_requirements(model, app_num, requirements)
        duration = time.time() - start_timer
        gpt4all_logger.info(f"API Analysis completed in {duration:.2f} seconds with {len(results)} results.")

        # Convert results to dicts for JSON
        result_dicts = []
        for check in results:
             result_dict = {"requirement": check.requirement}
             # Handle different result formats gracefully
             if hasattr(check.result, 'to_dict') and callable(check.result.to_dict):
                  result_dict["result"] = check.result.to_dict()
             elif hasattr(check.result, "__dataclass_fields__"):
                  result_dict["result"] = asdict(check.result)
             else: # Primitive type or other object
                  result_dict["result"] = check.result # Store as is
             result_dicts.append(result_dict)

        return {"status": "success", "results": result_dicts}

    except (BadRequest, ValueError, ConnectionError, RuntimeError) as e:
         gpt4all_logger.warning(f"API requirements check failed: {e}")
         raise e # Let decorator handle conversion to appropriate HTTP error
    except Exception as e:
        gpt4all_logger.exception(f"Unexpected error in API requirements check: {e}")
        # Let decorator handle conversion to 500
        raise InternalServerError("An unexpected error occurred during analysis.") from e


@gpt4all_bp.route("/models", methods=["GET"])
@ajax_compatible # Handles JSON response / errors
def get_available_models():
    """
    Get the list of available models from the configured GPT4All server.

    Returns:
        JSON list of available model names or error information.
    """
    gpt4all_logger.info("Request for available GPT4All models")
    if not hasattr(current_app, 'gpt4all_analyzer'):
        raise RuntimeError("GPT4All analyzer service is not available.")

    analyzer = current_app.gpt4all_analyzer
    if not analyzer.client:
         raise RuntimeError("GPT4All client not configured within analyzer.")

    try:
        # check_server implicitly updates available_models if successful
        if analyzer.client.check_server():
            models = analyzer.client.available_models
            gpt4all_logger.info(f"Returning {len(models)} available models.")
            return {"status": "success", "models": models}
        else:
            raise ConnectionError("GPT4All server is not available or not responding.")

    except ConnectionError as e:
        gpt4all_logger.error(f"Failed to connect to GPT4All server for models: {e}")
        raise e # Let decorator handle
    except Exception as e:
        gpt4all_logger.exception(f"Unexpected error getting available models: {e}")
        raise InternalServerError("Failed to retrieve available models.") from e


@gpt4all_bp.route("/server-status", methods=["GET"])
@ajax_compatible # Handles JSON response / errors
def check_server_status():
    """
    Check the availability of the configured GPT4All server.

    Returns:
        JSON indicating server status and URL.
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

    # Use APIResponse for consistent structure via decorator
    return APIResponse(
        success=status_info["available"],
        error=status_info["error"],
        data={"available": status_info["available"], "server_url": status_info["server_url"]},
        code=http_code
    )


# Legacy route redirect - Keep as is
@gpt4all_bp.route("/gpt4all-analysis", methods=["GET", "POST"])
def legacy_analysis_redirect():
    """Redirects legacy URL to the new /analysis endpoint."""
    gpt4all_logger.info("Redirecting from legacy /gpt4all-analysis to /gpt4all/analysis")
    # Preserve query parameters during redirect
    return redirect(url_for('gpt4all.gpt4all_analysis', **request.args))

# Ping route - Keep as is
@gpt4all_bp.route("/ping", methods=["GET"])
@ajax_compatible
def ping():
    """Simple health check endpoint for the GPT4All blueprint."""
    gpt4all_logger.info("Ping request received for gpt4all blueprint.")
    return {"status": "success", "message": "GPT4All routes are active."}