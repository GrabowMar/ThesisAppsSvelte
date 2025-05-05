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
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, TypeVar, cast

# =============================================================================
# Third-Party Imports
# =============================================================================
try:
    import psutil
except ImportError:
    psutil = None

from flask import (
    Blueprint, Response, current_app, flash, jsonify,
    redirect, render_template, request, url_for, send_file, g
)
from werkzeug.exceptions import BadRequest, HTTPException, InternalServerError, NotFound

# =============================================================================
# Custom Module Imports
# =============================================================================
from logging_service import create_logger_for_component
from services import (
    DockerManager, ScanManager, SystemHealthMonitor, call_ai_service,
    create_scanner
)
from utils import (
    AIModel, AI_MODELS, APIResponse,
    _AJAX_REQUEST_HEADER_NAME, _AJAX_REQUEST_HEADER_VALUE,
    ajax_compatible, get_all_apps, get_app_container_statuses,
    get_app_directory, get_app_info, get_apps_for_model,
    get_container_names, get_model_index, get_scan_manager,
    handle_docker_action, process_security_analysis, stop_zap_scanners,
    verify_container_health, PortManager
)
from zap_scanner import CodeContext, ZapVulnerability

# Type variable for better type hints
T = TypeVar('T')

# =============================================================================
# Scan State Enum Definition
# =============================================================================
class ScanState(Enum):
    """Defines the possible states for a ZAP scan."""
    NOT_RUN = "Not Run"          # Scan has never been initiated for this app
    STARTING = "Starting"        # Scan thread initiated, ZAP setup in progress
    SPIDERING = "Spidering"      # Spidering phase active
    SCANNING = "Scanning"        # Active scanning phase active
    COMPLETE = "Complete"        # Scan finished successfully
    FAILED = "Failed"            # Scan finished, but reported failure (e.g., ZAP error during scan)
    ERROR = "Error"              # Scan couldn't start/run due to setup/thread error (e.g., DirNotFound)
    STOPPED = "Stopped"          # Scan was explicitly stopped by user


# =============================================================================
# Blueprint Definitions
# =============================================================================
main_bp = Blueprint("main", __name__)
api_bp = Blueprint("api", __name__, url_prefix="/api")
analysis_bp = Blueprint("analysis", __name__, url_prefix="/analysis")
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
# Utility Functions
# =============================================================================
def get_docker_manager() -> DockerManager:
    """
    Get the Docker manager from the application context.
    
    Returns:
        DockerManager: The Docker manager instance
        
    Raises:
        RuntimeError: If Docker manager is not available
    """
    docker_manager = current_app.config.get("docker_manager")
    if not docker_manager:
        raise RuntimeError("Docker manager is not available")
    return docker_manager


def get_safe_path(base_dir: Path, *path_parts: str) -> Path:
    """
    Safely join paths to prevent directory traversal attacks.
    
    Args:
        base_dir: Base directory that all paths must be under
        *path_parts: Path components to join
        
    Returns:
        Path: The safely constructed path
        
    Raises:
        ValueError: If the resulting path is outside the base directory
    """
    # Resolve the base directory to an absolute path
    base_dir = base_dir.resolve()
    
    # Join the path components
    path = base_dir.joinpath(*path_parts)
    
    # Resolve to absolute path and check that it's within the base directory
    resolved_path = path.resolve()
    if not str(resolved_path).startswith(str(base_dir)):
        raise ValueError(f"Path '{resolved_path}' is outside base directory '{base_dir}'")
        
    return resolved_path


def log_client_request(logger, action: str, model: str, app_num: Optional[int] = None) -> None:
    """
    Log a client request with standardized format.
    
    Args:
        logger: Logger instance to use
        action: Action being performed
        model: Model name
        app_num: Optional app number
    """
    if app_num is not None:
        logger.info(f"{action} requested for {model}/app{app_num}")
    else:
        logger.info(f"{action} requested for {model}")


def handle_route_error(e: Exception, logger, redirect_url: Optional[str] = None) -> Union[Response, Tuple[Any, int]]:
    """
    Handle errors in route handlers with standardized behavior.
    
    Args:
        e: The exception that was caught
        logger: Logger instance to use
        redirect_url: Optional URL to redirect to if not AJAX
        
    Returns:
        Response object or (response, status_code) tuple
    """
    is_ajax = request.headers.get(_AJAX_REQUEST_HEADER_NAME) == _AJAX_REQUEST_HEADER_VALUE
    
    if isinstance(e, BadRequest):
        logger.warning(f"Bad request: {str(e)}")
        status_code = http.HTTPStatus.BAD_REQUEST
    elif isinstance(e, NotFound):
        logger.warning(f"Resource not found: {str(e)}")
        status_code = http.HTTPStatus.NOT_FOUND
    elif isinstance(e, HTTPException):
        logger.error(f"HTTP exception: {str(e)}")
        status_code = e.code
    else:
        logger.exception(f"Unexpected error: {str(e)}")
        status_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
    
    # Return JSON response for AJAX requests
    if is_ajax:
        return APIResponse(
            success=False,
            error=str(e),
            code=status_code
        ).to_response()
    
    # Flash error and redirect for regular requests
    if redirect_url:
        flash(str(e), "error")
        return redirect(redirect_url)
    
    # Fallback: re-raise the exception
    raise e


def get_zap_results_path(app, model: str, app_num: int) -> Path:
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

    try:
        docker_manager = get_docker_manager()
        apps = get_all_apps()

        main_route_logger.debug(f"Found {len(apps)} apps, fetching statuses...")
        start_time = time.time()
        
        for app_info in apps:
            try:
                statuses = get_app_container_statuses(
                    app_info["model"], app_info["app_num"], docker_manager
                )
                app_info["backend_status"] = statuses.get("backend", {})
                app_info["frontend_status"] = statuses.get("frontend", {})
                
                if statuses.get("error"):
                    main_route_logger.warning(
                        f"Error getting status for {app_info['model']}/{app_info['app_num']}: "
                        f"{statuses['error']}"
                    )
                    app_info["status_error"] = statuses['error']
            except Exception as e:
                main_route_logger.exception(
                    f"Unexpected error getting status for {app_info['model']}/{app_info['app_num']}: {e}"
                )
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
    except Exception as e:
        return handle_route_error(e, main_route_logger)


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
    log_client_request(main_route_logger, "Docker logs view", model, app_num)
    compose_logs = "Could not retrieve docker-compose logs."
    backend_logs = "Could not retrieve backend logs."
    frontend_logs = "Could not retrieve frontend logs."

    try:
        # Use helper to get validated app directory path
        app_dir = get_app_directory(current_app, model, app_num)

        try:
            main_route_logger.debug(f"Running 'docker-compose logs' in {app_dir}")
            result = subprocess.run(
                ["docker-compose", "logs", "--no-color", "--tail", "200"],
                cwd=str(app_dir),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=20
            )
            if result.returncode == 0:
                compose_logs = result.stdout or "No logs output from docker-compose."
            else:
                compose_logs = (
                    f"Error running docker-compose logs (Code {result.returncode}):\n"
                    f"{result.stderr or result.stdout}"
                )
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
        b_name, f_name = get_container_names(model, app_num)
        docker_manager = get_docker_manager()

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

    except Exception as e:
        return handle_route_error(e, main_route_logger, url_for("main.index"))


@main_bp.route("/status/<string:model>/<int:app_num>")
@ajax_compatible
def check_app_status(model: str, app_num: int):
    """
    Check and return container status for an app.
    """
    main_route_logger.debug(f"Checking status for {model}/app{app_num}")
    try:
        docker_manager = get_docker_manager()
        status = get_app_container_statuses(model, app_num, docker_manager)
        return status
    except Exception as e:
        return handle_route_error(e, main_route_logger)


@main_bp.route("/batch/<action>/<string:model>", methods=["POST"])
@ajax_compatible
def batch_docker_action(action: str, model: str):
    """
    Perform batch Docker operations on all apps for a specific model.
    """
    log_client_request(main_route_logger, f"Batch action '{action}'", model)

    valid_actions = ["start", "stop", "restart", "build", "rebuild", "health-check"]
    if action not in valid_actions:
        main_route_logger.warning(f"Invalid batch action requested: {action}")
        return APIResponse(
            success=False,
            error=f"Invalid action: {action}",
            code=http.HTTPStatus.BAD_REQUEST
        )

    try:
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
        docker_manager = current_app.config.get("docker_manager")

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
        main_route_logger.info(
            f"Batch action '{action}' for '{model}' completed: {status} "
            f"({success_count}/{len(results)} succeeded)"
        )

        return {
            "status": status,
            "total": len(results),
            "success_count": success_count,
            "failure_count": len(results) - success_count,
            "results": results
        }
    except Exception as e:
        return handle_route_error(e, main_route_logger)


@main_bp.route("/logs/<string:model>/<int:app_num>")
@ajax_compatible
def view_logs(model: str, app_num: int):
    """
    View container logs for an app.
    """
    log_client_request(main_route_logger, "Container logs view", model, app_num)
    logs_data = {"backend": "Error retrieving logs.", "frontend": "Error retrieving logs."}
    
    try:
        docker_manager = get_docker_manager()
        b_name, f_name = get_container_names(model, app_num)

        main_route_logger.debug(f"Fetching logs for containers: {b_name}, {f_name}")
        logs_data["backend"] = docker_manager.get_container_logs(b_name)
        logs_data["frontend"] = docker_manager.get_container_logs(f_name)

        return render_template("logs.html", logs=logs_data, model=model, app_num=app_num)
    except Exception as e:
        return handle_route_error(e, main_route_logger, url_for("main.index"))


@main_bp.route("/<action>/<string:model>/<int:app_num>", methods=["POST"])
@ajax_compatible
def handle_docker_action_route(action: str, model: str, app_num: int):
    """
    Handle Docker action (start, stop, restart, build, rebuild) for an app via POST.
    """
    log_client_request(main_route_logger, f"Docker action '{action}'", model, app_num)

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
        return handle_route_error(e, main_route_logger, url_for("main.index"))


# =============================================================================
# API Routes (/api)
# =============================================================================
@api_bp.route("/system-info")
@ajax_compatible
def system_info():
    """
    Get detailed system information for the dashboard.
    """
    api_logger.debug("System info requested")
    
    try:
        docker_manager = current_app.config.get("docker_manager")
        system_health_metrics = {}
        docker_status = {
            "healthy": False, 
            "client_available": False, 
            "containers": {"running": 0, "stopped": 0, "total": 0}
        }
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
            app_stats["models"] = {model.name: 0 for model in AI_MODELS}
            for app in apps:
                model_name = app["model"]
                if model_name in app_stats["models"]:
                    app_stats["models"][model_name] += 1

            # Get app status counts (sampling)
            sample_size = min(10, len(apps))
            api_logger.debug(f"Sampling app statuses for dashboard (sample size: {sample_size} apps)")
            sampled_apps = apps[:sample_size]
            running, partial, stopped = 0, 0, 0
            
            if docker_status["client_available"]:
                for app in sampled_apps:
                    try:
                        statuses = get_app_container_statuses(app["model"], app["app_num"], docker_manager)
                        if statuses.get("error"):
                            continue

                        backend_running = statuses.get("backend", {}).get("running", False)
                        frontend_running = statuses.get("frontend", {}).get("running", False)

                        if backend_running and frontend_running:
                            running += 1
                        elif backend_running or frontend_running:
                            partial += 1
                        else:
                            stopped += 1
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
    except Exception as e:
        return handle_route_error(e, api_logger)


@api_bp.route("/container/<string:model>/<int:app_num>/status")
@ajax_compatible
def container_status(model: str, app_num: int):
    """
    Get container status for a specific app.
    """
    api_logger.debug(f"Container status requested for {model}/app{app_num}")
    try:
        docker_manager = get_docker_manager()
        status = get_app_container_statuses(model, app_num, docker_manager)
        return status
    except Exception as e:
        return handle_route_error(e, api_logger)


@api_bp.route("/debug/docker/<string:model>/<int:app_num>")
@ajax_compatible
def debug_docker_environment(model: str, app_num: int):
    """
    Debug endpoint to inspect Docker environment for an app.
    """
    log_client_request(api_logger, "Docker environment debug", model, app_num)
    debug_info = {"error": None}
    
    try:
        app_dir = get_app_directory(current_app, model, app_num)
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
                compose_content = compose_file_content[:1000] + ("..." if len(compose_file_content) > 1000 else "")
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
                compose_cmd = ["docker", "compose", "version"]  # V2 command
                docker_compose_version = subprocess.run(
                    compose_cmd, capture_output=True, text=True,
                    encoding='utf-8', errors='replace', check=True
                ).stdout.strip()
        except (FileNotFoundError, subprocess.CalledProcessError) as dcv_err:
            docker_compose_version = f"Error checking Docker Compose version: {dcv_err}"
            api_logger.error(docker_compose_version)
            
        debug_info["docker_compose_version"] = docker_compose_version

        docker_manager = get_docker_manager()
        container_statuses = get_app_container_statuses(model, app_num, docker_manager)
        debug_info["backend_container"] = container_statuses.get("backend", {"error": "Status unavailable"})
        debug_info["frontend_container"] = container_statuses.get("frontend", {"error": "Status unavailable"})
        
        if container_statuses.get("error"):
            debug_info["container_status_error"] = container_statuses["error"]

        debug_info["timestamp"] = datetime.now().isoformat()
        api_logger.debug(f"Debug data collected for {model}/app{app_num}")
        return debug_info

    except Exception as e:
        return handle_route_error(e, api_logger)


@api_bp.route("/health/<string:model>/<int:app_num>")
@ajax_compatible
def check_container_health(model: str, app_num: int):
    """
    Check if containers for a specific app are healthy after startup.
    """
    api_logger.debug(f"Health check requested for {model}/app{app_num}")
    try:
        docker_manager = get_docker_manager()
        healthy, message = verify_container_health(docker_manager, model, app_num)
        api_logger.debug(f"Health check result for {model}/app{app_num}: {healthy} - {message}")
        return {"healthy": healthy, "message": message}
    except Exception as e:
        return handle_route_error(e, api_logger)


@api_bp.route("/status")
@ajax_compatible
def system_status():
    """
    Get overall system status (Docker and Disk).
    """
    api_logger.debug("System status check requested")
    
    try:
        docker_manager = current_app.config.get("docker_manager")
        docker_ok = False
        disk_ok = False
        details = {}

        disk_ok = SystemHealthMonitor.check_disk_space()
        details["disk_space_ok"] = disk_ok

        if docker_manager and docker_manager.client:
            docker_ok = SystemHealthMonitor.check_docker_connection(docker_manager.client)
            details["docker_connection_ok"] = docker_ok
        else:
            details["docker_connection_ok"] = False
            details["docker_error"] = "Docker client not available"

        status = "healthy" if (disk_ok and docker_ok) else "warning" if (disk_ok or docker_ok) else "error"
        api_logger.debug(f"System status: {status} (disk: {disk_ok}, docker: {docker_ok})")

        return {
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return handle_route_error(e, api_logger)


@api_bp.route("/model-info")
@ajax_compatible
def get_model_info():
    """
    Get configuration information about all AI models.
    """
    api_logger.debug("Model information requested")
    
    try:
        model_info = []
        for idx, model in enumerate(AI_MODELS):
            model_name = model.name if hasattr(model, 'name') else str(model)
            model_color = model.color if hasattr(model, 'color') else "#FFFFFF"
            
            try:
                # Get app count without throwing error if dir missing
                apps_list = get_apps_for_model(model_name)
                app_count = len(apps_list)
                port_range = PortManager.get_port_range(idx)
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
    except Exception as e:
        return handle_route_error(e, api_logger)


# =============================================================================
# Client-side Error Logging Endpoint
# =============================================================================
@api_bp.route("/log-client-error", methods=["POST"])
@ajax_compatible
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
        
        if 'stack' in data:
            error_context['stack_preview'] = data['stack'][:500] + '...'
        if 'context' in data:
            error_context['extra_context'] = data['context']

        client_error_logger.error(
            "ClientError: %(message)s | URL: %(url)s | File: %(file_info)s | UA: %(user_agent)s",
            error_context
        )
        if 'stack' in data:
            client_error_logger.debug("Full Client Stack Trace:\n%s", data['stack'])

        return {"status": "logged"}

    except Exception as e:
        return handle_route_error(e, client_error_logger)


# =============================================================================
# ZAP Routes (/zap)
# =============================================================================
@zap_bp.route("/<string:model>/<int:app_num>")
@ajax_compatible
def zap_scan_page(model: str, app_num: int):
    """
    Display the ZAP scanner page for a specific app.
    """
    log_client_request(zap_logger, "ZAP scan page", model, app_num)
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
                    
                    zap_logger.info(
                        f"Loaded {len(alerts)} alerts: H={summary['high']}, M={summary['medium']}, "
                        f"L={summary['low']}, I={summary['info']}, with_code={summary['vulnerabilities_with_code']}"
                    )
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

        return render_template(
            "zap_scan.html",
            model=model,
            app_num=app_num,
            alerts=alerts,
            error=error_msg,
            summary=summary,
            results_exist=results_exist
        )
    except Exception as e:
        return handle_route_error(e, zap_logger)


@zap_bp.route("/scan/<string:model>/<int:app_num>", methods=["POST"])
@ajax_compatible
def start_zap_scan(model: str, app_num: int):
    """
    Start a comprehensive ZAP scan in a background thread.
    """
    log_client_request(zap_logger, "Start ZAP scan", model, app_num)
    
    try:
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
                return APIResponse(
                    success=False, 
                    error="A scan is already running for this app.", 
                    code=http.HTTPStatus.CONFLICT
                )

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
                    scanner = create_scanner(base_dir_thread)  # Use base dir for scanner logs/tmp

                    scan_thread_logger.info(f"Setting source code root directory to {app_dir_thread}")
                    scanner.set_source_code_root(str(app_dir_thread))  # Pass app dir for code mapping

                    current_scan_manager = get_scan_manager()
                    current_scan_manager.update_scan(
                        scan_id_thread,
                        scanner=scanner,  # Store scanner instance if stop is needed
                        # Use ScanState Enum value for status
                        status=ScanState.STARTING.value,
                        progress=0,
                        spider_progress=0, passive_progress=0, active_progress=0, ajax_progress=0,
                        start_time=datetime.now().isoformat(),
                        end_time=None,
                        results=None
                    )

                    scan_thread_logger.info(f"Starting comprehensive ZAP scan for {model_thread}/app{app_num_thread}")
                    success = scanner.start_scan(model_thread, app_num_thread)  # Blocks until scan finishes

                    scan_thread_logger.info(f"Scan finished for {scan_id_thread}. Success reported by scanner: {success}")
                    # Determine final status based on scanner's return and potential prior errors
                    # Scan manager state might have been updated if scan_target failed critically
                    current_state = current_scan_manager.get_scan_details(scan_id_thread)
                    if current_state and current_state.get("status") == ScanState.ERROR.value:
                        final_status = ScanState.ERROR.value  # Keep Error status if set during scan
                    else:
                        final_status = ScanState.COMPLETE.value if success else ScanState.FAILED.value

                    final_progress = 100  # Mark as 100% done

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
                        active_progress=final_progress, ajax_progress=final_progress,  # Mark all 100%
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
                    get_scan_manager().update_scan(
                        scan_id_thread, 
                        status=ScanState.ERROR.value, 
                        progress=0, 
                        error=f"Directory not found: {e}"
                    )
                except Exception as e:
                    scan_thread_logger.exception(f"Error during background scan {scan_id_thread}: {e}")
                    # Use ScanState Enum value for status
                    get_scan_manager().update_scan(
                        scan_id_thread, 
                        status=ScanState.ERROR.value, 
                        progress=0, 
                        error=str(e)
                    )
                finally:
                    # Scanner's start_scan should handle its own cleanup, but we ensure manager state is updated
                    get_scan_manager().cleanup_old_scans()  # Clean up old entries if needed
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
    except Exception as e:
        return handle_route_error(e, zap_logger)


@zap_bp.route("/scan/<string:model>/<int:app_num>/status")
@ajax_compatible
def zap_scan_status(model: str, app_num: int):
    """
    Get the status of the latest ZAP scan for an app.
    """
    zap_logger.debug(f"Scan status requested for {model}/app{app_num}")
    
    try:
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
        # Update only existing keys
        response.update({key: scan_state.get(key) for key in default_status if key in scan_state})
        response["scan_id"] = scan_id  # Ensure scan_id is correct

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
    except Exception as e:
        return handle_route_error(e, zap_logger)


@zap_bp.route("/scan/<string:model>/<int:app_num>/stop", methods=["POST"])
@ajax_compatible
def stop_zap_scan(model: str, app_num: int):
    """
    Stop a running ZAP scan for a specific app.
    """
    log_client_request(zap_logger, "Stop ZAP scan", model, app_num)
    
    try:
        scan_manager = get_scan_manager()
        latest_scan_info = scan_manager.get_latest_scan_for_app(model, app_num)

        if not latest_scan_info:
            zap_logger.warning(f"Stop request failed: No scan found for {model}/app{app_num}")
            return APIResponse(
                success=False, 
                error="No scan found for this app", 
                code=http.HTTPStatus.NOT_FOUND
            )

        scan_id, scan_state = latest_scan_info
        # Use ScanState Enum values for checking
        active_statuses = {
            ScanState.STARTING.value, 
            ScanState.SPIDERING.value, 
            ScanState.SCANNING.value
        }

        if scan_state.get("status") not in active_statuses:
            current_status = scan_state.get("status", "Unknown")
            zap_logger.warning(f"Stop request ignored: Scan {scan_id} is not running (status: {current_status})")
            return APIResponse(
                success=False, 
                error=f"Scan is not running (status: {current_status})", 
                code=http.HTTPStatus.BAD_REQUEST
            )

        zap_logger.info(f"Attempting to stop scan ID {scan_id} ({model}/app{app_num})")
        
        # Retrieve scans from current_app config to stop
        zap_scans = current_app.config.get("ZAP_SCANS", {})
        stop_zap_scanners(zap_scans)

        scan_manager.update_scan(
            scan_id,
            # Use ScanState Enum value
            status=ScanState.STOPPED.value,
            progress=0,  # Reset progress
            spider_progress=0, passive_progress=0, active_progress=0, ajax_progress=0,
            end_time=datetime.now().isoformat(),
            error="Scan stopped by user request."  # Add note
        )

        zap_logger.info(f"Scan {scan_id} for {model}/app{app_num} marked as stopped.")
        return {"status": "stopped", "message": "Scan stop request processed (cleanup attempted)."}

    except Exception as e:
        return handle_route_error(e, zap_logger)


@zap_bp.route("/code_report/<string:model>/<int:app_num>")
def download_code_report(model: str, app_num: int):
    """
    Download the generated ZAP code analysis report (Markdown).
    """
    log_client_request(zap_logger, "Code report download", model, app_num)
    
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
            mimetype="text/markdown; charset=utf-8",  # Specify charset
            as_attachment=True,
            download_name=f"security_code_report_{model}_app{app_num}.md"
        )
    except Exception as e:
        return handle_route_error(e, zap_logger, url_for('zap.zap_scan_page', model=model, app_num=app_num))


@zap_bp.route("/regenerate_code_report/<string:model>/<int:app_num>", methods=["POST"])
@ajax_compatible
def regenerate_code_report(model: str, app_num: int):
    """
    Regenerate the code analysis report from existing ZAP scan results JSON.
    """
    log_client_request(zap_logger, "Code report regeneration", model, app_num)
    
    try:
        base_dir = Path(current_app.config["BASE_DIR"])
        app_dir = get_app_directory(current_app, model, app_num)
        results_file = app_dir / ".zap_results.json"
        report_file_path = app_dir / ".zap_code_report.md"

        if not results_file.is_file() or results_file.stat().st_size < 10:
            msg = f"Valid ZAP results file not found at {results_file}. Cannot regenerate report."
            zap_logger.warning(msg)
            return APIResponse(
                success=False, 
                error="Scan results not found or empty.", 
                code=http.HTTPStatus.NOT_FOUND
            )

        zap_logger.info(f"Reading scan results from {results_file}")
        with open(results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract alerts, handling potential structure variations
        alerts_raw = data.get("alerts", [])
        if not alerts_raw and "summary" in data and "alerts" in data["summary"]:
            alerts_raw = data["summary"]["alerts"]  # Check older format maybe?

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
                    affected_code=affected_code_obj,  # Pass reconstructed object
                    **alert_dict_copy  # Pass remaining fields
                )
                vulnerabilities_obj.append(vuln_obj)
            except TypeError as te:
                zap_logger.warning(
                    f"Skipping alert due to TypeError during reconstruction: {te} | "
                    f"Alert data: {alert_dict}"
                )
            except Exception as recon_err:
                zap_logger.warning(
                    f"Skipping alert due to unexpected error during reconstruction: {recon_err} | "
                    f"Alert data: {alert_dict}"
                )

        if not vulnerabilities_obj:
            zap_logger.warning(f"No valid vulnerabilities could be reconstructed for {model}/app{app_num}")
            # Allow generating an empty report

        # Create scanner instance (only needed for report generation method)
        scanner = create_scanner(base_dir)

        zap_logger.info(f"Generating code report content for {model}/app{app_num}")
        report_content = scanner.generate_affected_code_report(vulnerabilities_obj, str(report_file_path))

        # Count vulnerabilities with code from the *reconstructed objects*
        vulnerabilities_with_code = sum(
            1 for v in vulnerabilities_obj 
            if v.affected_code and v.affected_code.snippet
        )

        zap_logger.info(
            f"Code report regenerated to '{report_file_path}' with "
            f"{vulnerabilities_with_code} code-related findings."
        )
        
        return {
            "success": True,
            "message": f"Code report regenerated successfully with {vulnerabilities_with_code} code-related findings.",
            "vulnerabilities_with_code": vulnerabilities_with_code
        }
    except Exception as e:
        return handle_route_error(e, zap_logger)


# =============================================================================
# Analysis Routes (/analysis)
# =============================================================================
@analysis_bp.route("/backend-security/<string:model>/<int:app_num>")
@ajax_compatible
def security_analysis(model: str, app_num: int):
    """
    Run backend security analysis for an app and display results.
    """
    log_client_request(security_logger, "Backend security analysis", model, app_num)
    full_scan = request.args.get("full", "false").lower() == "true"

    try:
        if not hasattr(current_app, 'backend_security_analyzer'):
            security_logger.error("Backend security analyzer not available.")
            flash("Backend security analyzer is not configured.", "error")
            return render_template(
                "security_analysis.html", 
                model=model, 
                app_num=app_num, 
                error="Analyzer not configured"
            )

        analyzer = current_app.backend_security_analyzer
        return process_security_analysis(
            template="security_analysis.html",
            analyzer=analyzer,
            # Assuming the method name is consistent, adjust if needed
            analysis_method=analyzer.run_security_analysis,  # Check method name in analyzer
            model=model,
            app_num=app_num,
            full_scan=full_scan,
            no_issue_message="No significant backend security issues found."
        )
    except Exception as e:
        return handle_route_error(e, security_logger)


@analysis_bp.route("/frontend-security/<string:model>/<int:app_num>")
@ajax_compatible
def frontend_security_analysis(model: str, app_num: int):
    """
    Run frontend security analysis for an app and display results.
    """
    log_client_request(security_logger, "Frontend security analysis", model, app_num)
    full_scan = request.args.get("full", "false").lower() == "true"

    try:
        if not hasattr(current_app, 'frontend_security_analyzer'):
            security_logger.error("Frontend security analyzer not available.")
            flash("Frontend security analyzer is not configured.", "error")
            return render_template(
                "security_analysis.html", 
                model=model, 
                app_num=app_num, 
                error="Analyzer not configured"
            )

        analyzer = current_app.frontend_security_analyzer
        return process_security_analysis(
            template="security_analysis.html",  # Can use the same template?
            analyzer=analyzer,
            analysis_method=analyzer.run_security_analysis,  # Assuming same method name
            model=model,
            app_num=app_num,
            full_scan=full_scan,
            no_issue_message="No significant frontend security issues found."
        )
    except Exception as e:
        return handle_route_error(e, security_logger)


@analysis_bp.route("/analyze", methods=["POST"])
@ajax_compatible
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
        model_name = data.get("model", "default-model")  # AI model to use
        app_context_info = data.get("app_context", {})  # Optional context

        security_logger.info(
            f"Analyzing {len(issues)} security issues using AI model '{model_name}'. "
            f"App Context: {app_context_info}"
        )

        # --- Build structured prompt ---
        prompt = f"# Security Analysis Request for {app_context_info.get('model', 'App')} / {app_context_info.get('app_num', '')}\n\n"
        prompt += f"## Issues ({len(issues)} total):\n"
        issues.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.get('severity', 'low').lower(), 3))
        
        for i, issue in enumerate(issues[:20]):  # Limit prompt length
            prompt += f"\n### Issue {i+1}: {issue.get('issue_type', 'Unknown Type')} ({issue.get('severity', 'N/A')})\n"
            prompt += f"- **Tool:** {issue.get('tool', 'N/A')}\n"
            prompt += f"- **Description:** {issue.get('issue_text', 'N/A')}\n"
            if issue.get('filename'):
                prompt += f"- **File:** {issue.get('filename')}\n"
            if issue.get('code'):
                prompt += f"- **Code Snippet:** ```\n{issue['code'][:200]}\n```\n"

        if len(issues) > 20:
            prompt += "\n...(additional issues truncated)..."

        prompt += """
## Analysis Tasks:
1. Summarize the key security risks based on the provided issues.
2. Provide prioritized recommendations for remediation (Top 3-5).
3. Briefly explain the potential impact if these issues are not addressed.
Please format the response clearly using Markdown."""
        # --- End Prompt Building ---

        security_logger.debug(
            f"Sending security analysis prompt (length: {len(prompt)}) to AI service '{model_name}'"
        )
        analysis_result = call_ai_service(model_name, prompt)
        security_logger.info("Received security analysis response from AI service")

        return APIResponse(success=True, data={"response": analysis_result})

    except BadRequest as e:
        return handle_route_error(e, security_logger)
    except Exception as e:
        return handle_route_error(e, security_logger)


@analysis_bp.route("/summary/<string:model>/<int:app_num>")
@ajax_compatible
def get_security_summary(model: str, app_num: int):
    """
    Get a combined security analysis summary (backend & frontend) for an app.
    """
    log_client_request(security_logger, "Combined security summary", model, app_num)
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
            backend_issues, backend_status, _ = analyzer.run_security_analysis(
                model, app_num, use_all_tools=False
            )
            backend_summary = analyzer.get_analysis_summary(backend_issues)
            security_logger.debug(f"Backend summary: {backend_summary['total_issues']} issues.")
        else:
            error_details.append("Backend analyzer unavailable.")
            security_logger.warning("Backend security analyzer unavailable for summary.")

        if hasattr(current_app, 'frontend_security_analyzer'):
            analyzer = current_app.frontend_security_analyzer
            security_logger.debug(f"Running frontend security analysis for summary...")
            frontend_issues, frontend_status, _ = analyzer.run_security_analysis(
                model, app_num, use_all_tools=False
            )
            frontend_summary = analyzer.get_analysis_summary(frontend_issues)
            security_logger.debug(f"Frontend summary: {frontend_summary['total_issues']} issues.")
        else:
            error_details.append("Frontend analyzer unavailable.")
            security_logger.warning("Frontend security analyzer unavailable for summary.")

        total_issues = backend_summary["total_issues"] + frontend_summary["total_issues"]
        security_logger.info(
            f"Combined security summary for {model}/app{app_num}: {total_issues} total issues found."
        )

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
        return handle_route_error(e, security_logger)


@analysis_bp.route("/analyze-file", methods=["POST"])
@ajax_compatible
def analyze_single_file():
    """
    Analyze a single code file using the appropriate analyzer (backend/frontend).
    """
    security_logger.info("Single file analysis requested via POST")
    
    try:
        data = request.get_json()
        if not data or "file_path" not in data:
            raise BadRequest("Request body must be JSON with a 'file_path' field.")

        file_path = Path(data["file_path"])
        is_frontend = data.get("is_frontend", False)
        file_type = "frontend" if is_frontend else "backend"
        security_logger.info(f"Analyzing single {file_type} file: {file_path}")

        # Validate path to prevent directory traversal
        base_dir = Path(current_app.config["BASE_DIR"])
        safe_file_path = get_safe_path(base_dir, str(file_path))
        
        analyzer = None
        if is_frontend:
            if hasattr(current_app, 'frontend_security_analyzer'):
                analyzer = current_app.frontend_security_analyzer
            else:
                raise RuntimeError("Frontend analyzer not available.")
        else:
            if hasattr(current_app, 'backend_security_analyzer'):
                analyzer = current_app.backend_security_analyzer
            else:
                raise RuntimeError("Backend analyzer not available.")

        # Use a more specific method if available
        if hasattr(analyzer, 'analyze_single_file') and callable(analyzer.analyze_single_file):
            security_logger.debug(f"Running analyzer.analyze_single_file on {safe_file_path}")
            issues, tool_status, tool_output = analyzer.analyze_single_file(safe_file_path)
        else:
            # Fallback logic requires specific implementation based on analyzer tools
            security_logger.error(
                f"Analyzer {type(analyzer).__name__} missing 'analyze_single_file' method "
                "and fallback not implemented."
            )
            raise NotImplementedError("Single file analysis fallback not implemented.")

        security_logger.info(f"Found {len(issues)} issues in {safe_file_path.name}")

        # Assuming 'issues' contains objects with asdict or are directly serializable
        return {
            "status": "success",
            "issues": [asdict(issue) if hasattr(issue, '__dataclass_fields__') else issue for issue in issues],
            "tool_status": tool_status,
            "tool_output": tool_output,
        }
    except Exception as e:
        return handle_route_error(e, security_logger)


# =============================================================================
# Performance Testing Routes (/performance)
# =============================================================================
def get_tester():
    """Get the performance tester instance."""
    if not hasattr(current_app, 'performance_tester'):
        raise RuntimeError("Performance tester service is not available.")
    return current_app.performance_tester


def get_base_dir():
    """Get the base directory from configuration."""
    return Path(current_app.config.get("BASE_DIR", "."))


def derive_app_num(port: int) -> Optional[int]:
    """
    Derive app number from port.
    
    Args:
        port: The port number
        
    Returns:
        Optional[int]: The derived app number or None if it cannot be determined
    """
    try:
        BASE_FRONTEND_PORT = current_app.config.get("BASE_FRONTEND_PORT", 5501)
        PORTS_PER_APP = current_app.config.get("PORTS_PER_APP", 2)
        port_offset = port - BASE_FRONTEND_PORT
        if port_offset >= 0:
            app_num = (port_offset // PORTS_PER_APP) + 1
            perf_logger.debug(f"Derived app_num={app_num} from port={port}")
            return app_num
        else:
            perf_logger.warning(
                f"Port {port} is below BASE_FRONTEND_PORT {BASE_FRONTEND_PORT}, cannot derive app_num."
            )
            return None
    except Exception as e:
        perf_logger.warning(f"Could not derive app_num from port {port}: {e}")
        return None


@performance_bp.route("/<string:model>/<int:port>", methods=["GET", "POST"])
@ajax_compatible
def performance_test(model: str, port: int):
    """
    Display performance test page (GET) or run a test using the library (POST).
    """
    if request.method == "POST":
        log_client_request(perf_logger, "Performance test", model)
        perf_logger.info(f"Starting performance test POST request for {model} on port {port} using library method.")
        
        try:
            tester = get_tester()
            base_dir = get_base_dir()
            app_num = derive_app_num(port)
            
            data = request.get_json()
            if not data:
                raise BadRequest("Missing JSON request body.")

            num_users = int(data.get("num_users", 10))
            duration = int(data.get("duration", 30))  # Duration in seconds for library call
            spawn_rate = int(data.get("spawn_rate", 1))
            endpoints_raw = data.get("endpoints", [{"path": "/", "method": "GET", "weight": 1}])

            if not (num_users > 0 and duration > 0 and spawn_rate > 0):
                raise BadRequest("Number of users, duration, and spawn rate must be positive integers.")
            if not endpoints_raw:
                raise BadRequest("At least one endpoint configuration must be provided.")

            perf_logger.info(
                f"Test parameters: users={num_users}, duration={duration}s, "
                f"spawn_rate={spawn_rate}, endpoints={endpoints_raw}"
            )

            formatted_endpoints = []
            for ep in endpoints_raw:
                if isinstance(ep, dict) and "path" in ep:
                    # Basic validation
                    ep['method'] = ep.get('method', 'GET').upper()
                    ep['weight'] = int(ep.get('weight', 1))
                    if ep['weight'] < 1:
                        ep['weight'] = 1
                    formatted_endpoints.append(ep)
                else:
                    raise BadRequest(f"Invalid endpoint format: {ep}. Expecting list of dicts with 'path'.")

            test_base_name = f"{model}_{port}"  # Timestamp added by run_test_library
            host_url = f"http://localhost:{port}"  # Assuming localhost for now

            perf_logger.info(f"Running library performance test '{test_base_name}' against {host_url}")

            # Run the test
            result_data = tester.run_test_library(
                test_name=test_base_name,  # Base name, timestamp added internally
                host=host_url,
                endpoints=formatted_endpoints,
                user_count=num_users,
                spawn_rate=spawn_rate,
                run_time=duration,  # Pass duration in seconds
                generate_graphs=True,  # Generate graphs and include URLs
                model=model,
                app_num=app_num
            )

            perf_logger.info(f"Test '{result_data.test_name}' completed.")

            # Return the result data directly
            return {
                "status": "success",
                "message": f"Test '{result_data.test_name}' completed.",
                "data": result_data.to_dict()  # Send the full result object as dict
            }
        except Exception as e:
            return handle_route_error(e, perf_logger)
    else:
        # GET request
        try:
            log_client_request(perf_logger, "Performance test form", model)
            
            tester = get_tester()
            base_dir = get_base_dir()
            app_num = derive_app_num(port)
            
            # You might want to load last saved result here if available
            last_result_data = None
            if app_num:
                try:
                    # Check for consolidated results file
                    app_dir = base_dir / "performance_reports" / model / f"app{app_num}"
                    result_file = app_dir / ".locust_result.json"
                    if result_file.exists():
                        with open(result_file, "r") as f:
                            last_result_data = json.load(f)
                        perf_logger.info(f"Loaded last result from {result_file}")
                except Exception as load_err:
                    perf_logger.warning(f"Could not load last result for {model}/app{app_num}: {load_err}")

            return render_template(
                "performance_test.html", 
                model=model, 
                port=port, 
                last_result=last_result_data
            )
        except Exception as e:
            return handle_route_error(e, perf_logger)


@performance_bp.route("/<string:model>/<int:port>/stop", methods=["POST"])
@ajax_compatible
def stop_performance_test(model: str, port: int):
    """Stop a running performance test (implementation needed)."""
    log_client_request(perf_logger, "Stop performance test", model)
    perf_logger.warning("Performance test stopping is not yet implemented.")
    return {"status": "warning", "message": "Test stopping not implemented."}


@performance_bp.route("/<string:model>/<int:port>/reports", methods=["GET"])
@ajax_compatible
def list_performance_reports(model: str, port: int):
    """
    List available performance test artifacts (directories containing graphs/results).
    """
    log_client_request(perf_logger, "List performance reports", model)
    
    try:
        reports = []
        base_dir = get_base_dir()
        report_base_dir = base_dir / "performance_reports"
        if not report_base_dir.is_dir():
            perf_logger.debug(f"Report directory does not exist: {report_base_dir}")
            return {"reports": []}

        test_name_prefix = f"{model}_{port}_"
        tester = get_tester()  # Need static_url_path from tester

        for test_dir in report_base_dir.iterdir():
            if test_dir.is_dir() and test_dir.name.startswith(test_name_prefix):
                report_id = test_dir.name  # e.g., model_port_YYYYMMDD_HHMMSS
                timestamp_str = report_id.replace(test_name_prefix, "")
                formatted_time = "Unknown Time"
                try:
                    dt_obj = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    formatted_time = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass  # Ignore if parsing fails

                graphs = []
                for graph_file in test_dir.glob("*.png"):
                    # Construct URL relative to static path
                    relative_path = graph_file.relative_to(base_dir)  # Relative to Flask's static root
                    graph_url = url_for('static', filename=relative_path.as_posix())

                    graphs.append({
                        "name": graph_file.stem.replace("_", " ").title(),
                        "url": graph_url
                    })

                # Check for the consolidated JSON result file
                consolidated_json_path = None
                app_num = derive_app_num(port)
                if app_num:
                    app_specific_dir = report_base_dir / model / f"app{app_num}"
                    json_file = app_specific_dir / ".locust_result.json"
                    if json_file.exists():
                        consolidated_json_path = str(json_file)  # Store path for potential loading

                reports.append({
                    "id": report_id,
                    "timestamp_str": timestamp_str,
                    "created": formatted_time,
                    "graphs": graphs,
                    "has_consolidated_json": consolidated_json_path is not None,
                    # Add URL to view consolidated data if needed
                    "results_url": url_for(
                        '.get_performance_results', 
                        model=model, 
                        port=port, 
                        report_id=report_id
                    ) if consolidated_json_path else None
                })

        reports.sort(key=lambda x: x.get("timestamp_str", ""), reverse=True)
        perf_logger.info(f"Found {len(reports)} performance report directories for {model} on port {port}")
        return {"reports": reports}  # Return list directly for ajax_compatible
    except Exception as e:
        return handle_route_error(e, perf_logger)


@performance_bp.route("/<string:model>/<int:port>/reports/<path:report_id>", methods=["GET"])
def view_performance_report_from_json(model: str, port: int, report_id: str):
    """
    Loads saved JSON results and renders them in a view template.
    """
    log_client_request(perf_logger, "View saved performance report", model)
    
    try:
        base_dir = get_base_dir()
        
        # Security Check
        expected_prefix = f"{model}_{port}_"
        if not report_id.startswith(expected_prefix) or ".." in report_id or report_id.startswith('/'):
            perf_logger.warning(f"Invalid or potentially unsafe report ID requested for viewing: {report_id}")
            return render_template("404.html", message="Invalid Report ID"), http.HTTPStatus.BAD_REQUEST

        # Find the corresponding consolidated JSON file
        result_data = None
        app_num = derive_app_num(port)
        if app_num:
            app_specific_dir = base_dir / "performance_reports" / model / f"app{app_num}"
            json_file = app_specific_dir / ".locust_result.json"
            # Check if this JSON corresponds to the requested report_id (e.g., by timestamp)
            if json_file.exists():
                try:
                    with open(json_file, "r") as f:
                        loaded_data = json.load(f)
                    # Match based on test_name stored in the JSON
                    if loaded_data.get("test_name") == report_id:
                        result_data = loaded_data
                        perf_logger.info(f"Found matching consolidated JSON: {json_file}")
                    else:
                        perf_logger.warning(
                            f"Consolidated JSON {json_file} does not match test_name {report_id}"
                        )
                except Exception as e:
                    perf_logger.error(f"Error loading or checking consolidated JSON {json_file}: {e}")

        if not result_data:
            perf_logger.warning(f"No matching consolidated result JSON found for report ID {report_id}")
            return render_template(
                "404.html", 
                message=f"Result data for report {report_id} not found."
            ), http.HTTPStatus.NOT_FOUND

        # If data found, render it using a template similar to the main one
        return render_template(
            "performance_test.html",  # Reuse the main template
            model=model,
            port=port,
            report_id=report_id,  # Pass report_id for context
            last_result=result_data,  # Pass loaded data
            is_viewing_report=True  # Flag for template logic
        )
    except Exception as e:
        return handle_route_error(e, perf_logger)


@performance_bp.route("/<string:model>/<int:port>/results/<path:report_id>", methods=["GET"])
@ajax_compatible
def get_performance_results(model: str, port: int, report_id: str):
    """
    Get raw JSON results from the saved .locust_result.json file.
    """
    log_client_request(perf_logger, "Get raw performance results", model)
    
    try:
        base_dir = get_base_dir()

        # Security Check
        expected_prefix = f"{model}_{port}_"
        if not report_id.startswith(expected_prefix) or ".." in report_id or report_id.startswith('/'):
            perf_logger.warning(f"Invalid or potentially unsafe report ID for results: {report_id}")
            raise BadRequest("Invalid Report ID")

        json_file_path = None
        app_num = derive_app_num(port)
        if app_num:
            app_specific_dir = base_dir / "performance_reports" / model / f"app{app_num}"
            json_file = app_specific_dir / ".locust_result.json"
            # Check if this file matches the report_id based on its content
            if json_file.exists():
                try:
                    with open(json_file, "r") as f:
                        data = json.load(f)
                    if data.get("test_name") == report_id:
                        json_file_path = json_file
                        perf_logger.debug(f"Found matching consolidated JSON for {report_id}: {json_file_path}")
                        return data  # Return the loaded data directly
                    else:
                        perf_logger.warning(
                            f"Consolidated JSON {json_file} test_name does not match {report_id}"
                        )
                except Exception as e:
                    perf_logger.error(f"Error reading or checking consolidated JSON {json_file}: {e}")

        # If not found in consolidated location or mismatch, raise NotFound
        perf_logger.warning(f"No matching consolidated JSON result file found for report ID: {report_id}")
        raise NotFound("Result data not found for this report ID")
    except Exception as e:
        return handle_route_error(e, perf_logger)


@performance_bp.route("/<string:model>/<int:port>/reports/<path:report_id>/delete", methods=["POST"])
@ajax_compatible
def delete_performance_report(model: str, port: int, report_id: str):
    """Delete a specific performance test report directory and its contents."""
    log_client_request(perf_logger, "Delete performance report", model)
    
    try:
        base_dir = get_base_dir()
        report_dir = base_dir / "performance_reports" / report_id

        # Security Check
        expected_prefix = f"{model}_{port}_"
        if not report_id.startswith(expected_prefix) or ".." in report_id or report_id.startswith('/'):
            perf_logger.warning(f"Invalid or potentially unsafe report ID for deletion: {report_id}")
            raise BadRequest("Invalid Report ID")

        if not report_dir.is_dir():
            perf_logger.warning(f"Report directory not found for deletion: {report_dir}")
            raise NotFound("Report directory not found")

        perf_logger.warning(f"Recursively deleting report directory: {report_dir}")
        import shutil
        shutil.rmtree(report_dir)
        perf_logger.info(f"Successfully deleted report directory {report_id}")

        return {"status": "success", "message": f"Report directory {report_id} deleted successfully"}
    except Exception as e:
        return handle_route_error(e, perf_logger)


# =============================================================================
# GPT4All Routes (/gpt4all)
# =============================================================================
@gpt4all_bp.route("/analysis", methods=["GET", "POST"])
@ajax_compatible
def gpt4all_analysis():
    """
    Main route for requirements analysis using GPT4All.
    """
    log_client_request(gpt4all_logger, "GPT4All analysis page/action", None)
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
        if request.method == "POST":
            raise BadRequest(error)
    else:
        try:
            app_num = int(app_num_str)
            if app_num <= 0:
                raise ValueError("App number must be positive.")
        except ValueError as e:
            error = f"Invalid App Number: {app_num_str}. {e}"
            gpt4all_logger.warning(error)
            if request.method == "POST":
                raise BadRequest(error)

    if error and request.method == "GET":
        flash(error, "error")
        return render_template(
            "requirements_check.html", model=model, app_num=None,
            requirements=[], results=None, error=error
        )

    try:
        if not hasattr(current_app, 'gpt4all_analyzer'):
            error = "GPT4All analyzer service is not available."
            gpt4all_logger.error(error)
            if request.method == "POST":
                raise RuntimeError(error)
            flash(error, "error")
            return render_template("requirements_check.html", model=model, app_num=app_num, error=error)

        analyzer = current_app.gpt4all_analyzer

        gpt4all_logger.debug("Checking GPT4All server availability...")
        if not analyzer.client or not analyzer.client.check_server():
            error = "GPT4All server is not available or not responding. Please ensure it is running."
            gpt4all_logger.error(error)
            if request.method == "POST":
                raise ConnectionError(error)
            flash(error, "error")
            return render_template("requirements_check.html", model=model, app_num=app_num, error=error)
        gpt4all_logger.debug("GPT4All server is available.")

        requirements, template_name = analyzer.get_requirements_for_app(app_num)
        gpt4all_logger.info(
            f"Loaded {len(requirements)} default requirements for {model}/app{app_num} "
            f"from template '{template_name}'"
        )
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
                else:
                    gpt4all_logger.warning("Custom requirements field was present but empty after stripping.")

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
            if not results:
                flash("Analysis ran but returned no results.", "warning")
            else:
                flash("Analysis completed successfully.", "success")
        except Exception as analysis_error:
            error = f"Analysis failed: {analysis_error}"
            gpt4all_logger.exception(error)
            flash(error, "error")

    return render_template(
        "requirements_check.html",
        model=model, app_num=app_num, requirements=requirements,
        template_name=template_name, results=results, error=error
    )