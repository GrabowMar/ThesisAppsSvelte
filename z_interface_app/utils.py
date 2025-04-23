"""
Utility functions and helper classes for the AI Model Management System.
"""

# =============================================================================
# Standard Library Imports
# =============================================================================
import http # Added for HTTP status codes
import json
import os
# import random # Removed: Appears unused
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from functools import wraps # Kept: Used by ajax_compatible
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple # Added Callable back
# Removed unused typing imports: Generator, Union, Callable

# =============================================================================
# Third-Party Imports
# =============================================================================
# import docker # Removed: Appears unused in this file
from flask import (
    Response, current_app, jsonify, render_template, request
    # Removed unused Flask imports: flash, g, make_response, redirect, url_for
)
from werkzeug.exceptions import HTTPException # Kept: Used in ajax_compatible
# Removed unused werkzeug imports: BadRequest

# =============================================================================
# Custom Module Imports
# =============================================================================
from logging_service import create_logger_for_component
from services import DockerManager, PortManager # SystemHealthMonitor Removed: Appears unused

# =============================================================================
# Module Constants
# =============================================================================
_AJAX_REQUEST_HEADER_NAME = 'X-Requested-With'
_AJAX_REQUEST_HEADER_VALUE = 'XMLHttpRequest'
_DEFAULT_MODEL_COLOR = "#666666"

# Create the main application logger (assuming 'app' logger is desired here)
# If this should be specific to utils, consider renaming (e.g., 'utils_logger')
logger = create_logger_for_component('app')


# =============================================================================
# Configuration & Domain Models
# =============================================================================
@dataclass
class AppConfig:
    """Application configuration with environment variable fallbacks."""
    DEBUG: bool = os.getenv("FLASK_ENV", "development") != "production" # Better default DEBUG logic
    SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "your-secret-key-here") # Keep default for development
    BASE_DIR: Path = Path(__file__).parent
    DOCKER_TIMEOUT: int = int(os.getenv("DOCKER_TIMEOUT", "10"))
    CACHE_DURATION: int = int(os.getenv("CACHE_DURATION", "5"))
    HOST: str = "0.0.0.0" if os.getenv("FLASK_ENV") == "production" else "127.0.0.1"
    PORT: int = int(os.getenv("PORT", "5000"))
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO" if os.getenv("FLASK_ENV") == "production" else "DEBUG") # Better default log level

    # CORS settings for API endpoints
    CORS_ENABLED: bool = os.getenv("CORS_ENABLED", "false").lower() == "true"
    CORS_ORIGINS: List[str] = field(default_factory=lambda: ["http://localhost:5000"]) # Example default
    # jQuery Ajax specific settings (Consider if still needed)
    # JSONP_ENABLED: bool = os.getenv("JSONP_ENABLED", "false").lower() == "true"
    AJAX_TIMEOUT: int = int(os.getenv("AJAX_TIMEOUT", "30"))

    def __post_init__(self):
         # Ensure log directory exists
         log_path = Path(self.LOG_DIR)
         if not log_path.is_absolute():
              log_path = self.BASE_DIR.parent / log_path # Assume logs relative to project root (parent of utils)
         log_path.mkdir(parents=True, exist_ok=True)
         self.LOG_DIR = str(log_path) # Store as string after creation

         if self.SECRET_KEY == "your-secret-key-here" and not self.DEBUG:
              logger.warning("SECURITY WARNING: FLASK_SECRET_KEY is not set or is using the default value in a non-debug environment!")


    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create a configuration instance from environment variables."""
        # The __init__ already reads from env vars via defaults
        return cls()


@dataclass
class AIModel:
    """Represents an AI model with display properties"""
    name: str
    color: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class DockerStatus:
    """Represents the status of a Docker container."""
    exists: bool = False
    running: bool = False
    health: str = "unknown"
    status: str = "unknown"
    details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert status to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class APIResponse:
    """Standard API response format."""
    success: bool = True
    message: Optional[str] = None
    data: Any = None
    error: Optional[str] = None
    code: int = http.HTTPStatus.OK # Use standard OK code

    def to_response(self) -> Tuple[Response, int]:
        """Convert to Flask JSON response with appropriate status code."""
        response_data = {"success": self.success}

        if self.message is not None:
            response_data["message"] = self.message
        if self.data is not None:
            response_data["data"] = self.data
        if self.error is not None:
            response_data["error"] = self.error

        return jsonify(response_data), self.code


# Supported AI models with their display colors.
AI_MODELS: List[AIModel] = [
    AIModel("Llama", "#f97316"),
    AIModel("Mistral", "#9333ea"),
    AIModel("DeepSeek", "#ff5555"),
    AIModel("GPT4o", "#10a37f"),
    AIModel("Claude", "#7b2bf9"),
    AIModel("Gemini", "#1a73e8"),
    AIModel("Grok", "#ff4d4f"),
    AIModel("R1", "#fa541c"),
    AIModel("O3", "#0ca57f")
]

# =============================================================================
# Enhanced JSON Encoder
# =============================================================================
class CustomJSONEncoder(json.JSONEncoder):
    """Extended JSON encoder: handles dataclasses, __dict__, datetime, Path."""

    def default(self, obj):
        """
        Custom encoding for special types.

        Args:
            obj: Object to encode

        Returns:
            JSON serializable representation
        """
        if hasattr(obj, "__dataclass_fields__"):
            return asdict(obj)
        # Avoid using __dict__ directly if a 'to_dict' method exists
        if hasattr(obj, 'to_dict') and callable(obj.to_dict):
             return obj.to_dict()
        if hasattr(obj, "__dict__"): # Fallback
             # Be cautious with __dict__, might expose internal state
             return obj.__dict__
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
        # Let the base class default method raise the TypeError
        return super().default(obj)

# =============================================================================
# Utility Functions & Decorators
# =============================================================================
def ajax_compatible(f):
    """
    Decorator to standardize endpoint responses for AJAX and non-AJAX calls.

    - Returns JSON for AJAX requests (based on X-Requested-With header).
    - Handles exceptions, returning JSON error for AJAX or rendering 500.html.
    - Automatically converts dict, dataclass, or APIResponse results to JSON.
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        function_logger = create_logger_for_component(f'ajax.{f.__name__}') # More specific logger name
        is_ajax = request.headers.get(_AJAX_REQUEST_HEADER_NAME) == _AJAX_REQUEST_HEADER_VALUE
        try:
            result = f(*args, **kwargs)

            # --- Response Handling ---
            # If the function already returned a Flask Response tuple (e.g., jsonify, render_template)
            if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], Response):
                return result
            # If the function returned our standard APIResponse object
            if isinstance(result, APIResponse):
                return result.to_response()

            # --- AJAX Specific Formatting ---
            if is_ajax:
                 # Wrap successful non-Response results in standard JSON structure
                 api_response = APIResponse(success=True, data=result, code=http.HTTPStatus.OK)
                 return api_response.to_response()
            else:
                 # For non-AJAX, return the result directly (e.g., rendered template string)
                 # If the result wasn't already a Response, this might lead to issues if not a string/template
                 if isinstance(result, Response): # Double check if it became a Response object
                     return result
                 elif isinstance(result, str): # Allow returning rendered templates directly
                     return result
                 else:
                     # Unhandled non-AJAX return type, log warning and maybe return error
                     function_logger.warning(f"Non-AJAX request to {f.__name__} returned unexpected type: {type(result)}. Converting to string.")
                     return str(result) # Best effort conversion

        except Exception as e:
            function_logger.exception(f"Error encountered in decorated function '{f.__name__}'")

            error_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
            error_message = str(e)
            if isinstance(e, HTTPException):
                 error_code = e.code or http.HTTPStatus.INTERNAL_SERVER_ERROR
                 error_message = e.description or str(e)

            if is_ajax:
                 error_response = APIResponse(
                     success=False,
                     error=error_message,
                     message="An error occurred processing your request.", # Generic message
                     code=error_code
                 )
                 return error_response.to_response()
            else:
                 # For regular requests, render the standard error template
                 return render_template("500.html", error=error_message), error_code
    return wrapped


def get_model_index(model_name: str) -> Optional[int]:
    """
    Get the 0-based index of a model in the AI_MODELS list.

    Args:
        model_name: Name of the model (case-sensitive).

    Returns:
        Index in the AI_MODELS list or None if not found.
    """
    try:
        return next(i for i, m in enumerate(AI_MODELS) if m.name == model_name)
    except StopIteration:
         logger.warning(f"Model name '{model_name}' not found in AI_MODELS list.")
         return None


def get_container_names(model: str, app_num: int) -> Tuple[str, str]:
    """
    Get the container names for a given model and app number.

    Args:
        model: Model name.
        app_num: Application number (1-based).

    Returns:
        Tuple of (backend_container_name, frontend_container_name).

    Raises:
        ValueError: If the model name is not found or ports cannot be assigned.
    """
    idx = get_model_index(model)
    if idx is None:
        raise ValueError(f"Model '{model}' not found in configuration.")
    try:
        ports = PortManager.get_app_ports(idx, app_num)
        base = model.lower()
        return (f"{base}_backend_{ports['backend']}", f"{base}_frontend_{ports['frontend']}")
    except ValueError as e: # Catch errors from PortManager (e.g., app_num out of range)
        logger.error(f"Failed to get ports for {model}/app{app_num}: {e}")
        raise # Re-raise the original error


def get_app_info(model_name: str, app_num: int) -> Optional[Dict[str, Any]]:
    """
    Get detailed information for a specific app instance.

    Args:
        model_name: Name of the AI model.
        app_num: Application number (1-based).

    Returns:
        Dictionary with app details, or None if model/app is invalid.
    """
    idx = get_model_index(model_name)
    if idx is None:
        return None # Model not found

    model_instance = AI_MODELS[idx] # Get the AIModel object
    try:
        ports = PortManager.get_app_ports(idx, app_num)
        host = current_app.config.get("HOST", "127.0.0.1") # Get host from config if available
        # Ensure host doesn't accidentally become 0.0.0.0 for client-side URLs
        display_host = host if host != "0.0.0.0" else "127.0.0.1"

        return {
            "name": f"{model_instance.name} App {app_num}",
            "model": model_instance.name,
            "color": model_instance.color,
            "backend_port": ports["backend"],
            "frontend_port": ports["frontend"],
            "app_num": app_num,
            "backend_url": f"http://{display_host}:{ports['backend']}",
            "frontend_url": f"http://{display_host}:{ports['frontend']}",
        }
    except ValueError as e:
        logger.warning(f"Could not get info for {model_name}/app{app_num}: {e}")
        return None


def get_apps_for_model(model_name: str) -> List[Dict[str, Any]]:
    """
    Get all valid app instances found for a specific model.

    This function checks for directories like 'app1', 'app2' inside the model's base directory.

    Args:
        model_name: Name of the model.

    Returns:
        List of app information dictionaries for valid apps found.
    """
    util_logger = create_logger_for_component('utils.apps')
    apps = []
    # Use the potentially problematic get_app_directory to find the base
    # Note: This still uses the hardcoded path logic until fixed.
    # We need the base directory containing app1, app2 etc.
    # Assuming get_app_directory points to '.../model/appN', we need the parent.
    try:
        # Get path for app1 to find the model base directory
        app1_dir = get_app_directory(current_app, model_name, 1)
        model_base_dir = app1_dir.parent
        util_logger.debug(f"Scanning for apps in model base directory: {model_base_dir}")

        if not model_base_dir.exists() or not model_base_dir.is_dir():
            util_logger.warning(f"Model base directory does not exist or is not a directory: {model_base_dir}")
            return []

        # Iterate through potential app directories
        for item in model_base_dir.iterdir():
            if item.is_dir() and item.name.startswith("app"):
                try:
                    app_num_str = item.name.replace("app", "")
                    app_num = int(app_num_str)
                    if app_num > 0:
                         app_info = get_app_info(model_name, app_num)
                         if app_info: # Check if app info could be generated (valid ports etc.)
                             apps.append(app_info)
                         else:
                             util_logger.warning(f"Skipping invalid app configuration for {item.name}")
                except ValueError:
                    util_logger.warning(f"Skipping directory with non-numeric app suffix: {item.name}")
                except Exception as e: # Catch other potential errors during get_app_info
                     util_logger.error(f"Error processing app directory {item.name}: {e}")

        # Sort apps by app_num
        apps.sort(key=lambda x: x['app_num'])

    except Exception as e:
        util_logger.exception(f"Error scanning apps for model '{model_name}': {e}")

    util_logger.debug(f"Found {len(apps)} valid apps for model '{model_name}'")
    return apps


def get_all_apps() -> List[Dict[str, Any]]:
    """
    Get all valid apps for all configured models.

    Returns:
        List of app information dictionaries for all models.
    """
    all_apps = []
    util_logger = create_logger_for_component('utils.apps')
    util_logger.info("Retrieving all apps for all models...")
    for model in AI_MODELS:
        try:
            model_apps = get_apps_for_model(model.name)
            all_apps.extend(model_apps)
        except Exception as e:
             util_logger.exception(f"Failed to get apps for model '{model.name}': {e}")

    util_logger.info(f"Retrieved {len(all_apps)} apps across all models.")
    return all_apps


def run_docker_compose(
    command: List[str],
    model: str,
    app_num: int,
    timeout: int = 60, # Default timeout for most commands
    check: bool = True, # Default to raising error on failure
) -> Tuple[bool, str]:
    """
    Run a docker-compose command for a specific app.

    Args:
        command: The docker-compose command arguments (e.g., ["up", "-d"]).
        model: The model name.
        app_num: The application number (1-based).
        timeout: Command timeout in seconds.
        check: Whether to raise CalledProcessError on non-zero exit code.

    Returns:
        Tuple of (success, combined stdout/stderr output).
    """
    compose_logger = create_logger_for_component('docker_compose')
    try:
        # Uses the potentially problematic get_app_directory function
        app_dir = get_app_directory(current_app, model, app_num)

        # Check for compose file existence more robustly
        compose_file_path = None
        for filename in ["docker-compose.yml", "docker-compose.yaml"]:
             potential_path = app_dir / filename
             if potential_path.exists() and potential_path.is_file():
                  compose_file_path = potential_path
                  break

        if not compose_file_path:
             msg = f"No docker-compose.yml or docker-compose.yaml file found in {app_dir}"
             compose_logger.error(msg)
             return False, msg

        # Build the custom project name (lowercase, safe characters)
        project_name = "".join(c if c.isalnum() else '_' for c in f"{model}_app{app_num}".lower())

        # Construct the full command
        # Use -f to specify file path explicitly, avoids ambiguity if CWD!=app_dir
        cmd = ["docker-compose", "-p", project_name, "-f", str(compose_file_path)] + command
        compose_logger.info(f"Running command: {' '.join(cmd)} in CWD={app_dir} with timeout {timeout}s")

        result = subprocess.run(
            cmd,
            cwd=str(app_dir), # Run command with app_dir as working directory
            check=check,      # Raise error if check=True and command fails
            capture_output=True,
            text=True,
            encoding='utf-8',   # Explicitly set UTF-8 encoding
            errors='replace',   # Replace invalid characters
            timeout=timeout,
        )
        output = result.stdout + ("\n" + result.stderr if result.stderr else "") # Combine stdout/stderr
        success = result.returncode == 0

        if success:
            compose_logger.info(f"Command successful: {' '.join(cmd)}")
            compose_logger.debug(f"Output:\n{output}")
        else:
            # Error logged automatically if check=True causes CalledProcessError
            # Log here only if check=False
            if not check:
                 compose_logger.error(
                    f"Command failed with code {result.returncode}: {' '.join(cmd)}\n"
                    f"Output: {output[:1000]}..." # Limit log output size
                 )

        return success, output.strip()

    except FileNotFoundError:
         # Error if docker-compose command itself is not found
         compose_logger.exception("`docker-compose` command not found. Is Docker Compose installed and in PATH?")
         return False, "`docker-compose` command not found."
    except subprocess.TimeoutExpired:
        compose_logger.error(f"Command timed out after {timeout}s: {' '.join(cmd)}")
        return False, f"Command timed out after {timeout}s"
    except subprocess.CalledProcessError as e:
        # This catches errors when check=True
        output = e.stdout + ("\n" + e.stderr if e.stderr else "")
        compose_logger.error(
            f"Command failed with code {e.returncode}: {' '.join(e.cmd)}\n"
            f"Output: {output[:1000]}..."
        )
        return False, output.strip()
    except Exception as e:
        # Catch other potential errors (permissions, etc.)
        compose_logger.exception(f"Error running {' '.join(cmd)}: {e}")
        return False, f"An unexpected error occurred: {e}"


def handle_docker_action(action: str, model: str, app_num: int) -> Tuple[bool, str]:
    """
    Handle Docker Compose actions (start, stop, restart, build, rebuild).

    Args:
        action: The action ('start', 'stop', 'restart', 'build', 'rebuild').
        model: The model name.
        app_num: The application number (1-based).

    Returns:
        Tuple of (success, message).
    """
    docker_logger = create_logger_for_component(f'docker.action.{action}')
    # Define command sequences with appropriate arguments and timeouts
    # Format: (command_args_list, check_flag, timeout_seconds)
    commands_config = {
        "start": [ (["up", "-d", "--remove-orphans"], True, 90) ], # Add --remove-orphans, reasonable timeout
        "stop": [ (["down"], True, 60) ], # Usually faster
        "restart": [ (["restart"], True, 90) ], # Can take time
        "build": [ (["build", "--no-cache"], True, 600) ], # Long timeout for build, no cache
        "rebuild": [
            (["down"], True, 60),
            (["build", "--no-cache"], True, 600), # Rebuild implies no cache
            (["up", "-d", "--remove-orphans"], True, 90)
        ],
    }

    if action not in commands_config:
        docker_logger.error(f"Invalid docker action requested: {action}")
        return False, f"Invalid action: {action}"

    docker_logger.info(f"Initiating docker action '{action}' for {model}/app{app_num}")

    # Execute each command step defined for the action
    steps = commands_config[action]
    full_output = []
    for i, (cmd_args, check_flag, timeout) in enumerate(steps):
        step_desc = f"Step {i+1}/{len(steps)}: docker-compose {' '.join(cmd_args)}"
        docker_logger.info(f"Executing {step_desc} for {model}/app{app_num}")

        success, msg = run_docker_compose(
            cmd_args, model, app_num, timeout=timeout, check=check_flag
        )
        full_output.append(f"--- {step_desc} ---\n{msg}")

        if not success:
            error_msg = f"{action.capitalize()} failed during step: {' '.join(cmd_args)}"
            docker_logger.error(f"Docker action '{action}' failed for {model}/app{app_num}. Details:\n{msg}")
            # Return combined output up to the failure point
            return False, f"{error_msg}\n\nFull Output:\n{''.join(full_output)}"

    docker_logger.info(f"Successfully completed docker action '{action}' for {model}/app{app_num}")
    # Return combined output of all successful steps
    return True, f"Action '{action}' completed successfully.\n\nFull Output:\n{''.join(full_output)}"


def verify_container_health(
    docker_manager: DockerManager, model: str, app_num: int, max_retries: int = 15, retry_delay: int = 5 # Increased defaults
) -> Tuple[bool, str]:
    """
    Verify that an app's containers (backend & frontend) are running and healthy.

    Checks Docker container status, specifically the 'health' attribute if available.

    Args:
        docker_manager: DockerManager instance.
        model: Model name.
        app_num: App number (1-based).
        max_retries: Maximum number of checks.
        retry_delay: Delay between checks in seconds.

    Returns:
        Tuple of (is_healthy, message).
    """
    health_logger = create_logger_for_component('health')
    try:
        backend_name, frontend_name = get_container_names(model, app_num)
    except ValueError as e:
        health_logger.error(f"Cannot verify health, invalid model/app: {e}")
        return False, f"Invalid model/app: {e}"

    health_logger.info(f"Verifying container health for {model}/app{app_num} ({backend_name}, {frontend_name}). Max retries: {max_retries}, Delay: {retry_delay}s.")

    backend_healthy = False
    frontend_healthy = False
    last_backend_status = "N/A"
    last_frontend_status = "N/A"

    for attempt in range(1, max_retries + 1):
        try:
             backend = docker_manager.get_container_status(backend_name)
             frontend = docker_manager.get_container_status(frontend_name)

             # Consider 'running' state with unknown/checking health as potentially okay initially
             # but require 'healthy' eventually.
             backend_healthy = backend.running and backend.health in ("healthy",) # Require explicitly healthy
             frontend_healthy = frontend.running and frontend.health in ("healthy",)

             last_backend_status = f"{backend.status}({backend.health})" if backend.exists else "Not Found"
             last_frontend_status = f"{frontend.status}({frontend.health})" if frontend.exists else "Not Found"

             health_logger.debug(
                 f"Health check attempt {attempt}/{max_retries}: "
                 f"Backend[{backend_name}]: {last_backend_status}, "
                 f"Frontend[{frontend_name}]: {last_frontend_status}"
             )

             if backend_healthy and frontend_healthy:
                 health_logger.info(f"Containers confirmed healthy for {model}/app{app_num} on attempt {attempt}.")
                 return True, "All containers healthy"

        except Exception as e:
            health_logger.exception(f"Error during health check attempt {attempt} for {model}/app{app_num}: {e}")
            # Continue retrying even if one check fails temporarily

        # Wait before the next attempt, unless it's the last one
        if attempt < max_retries:
             time.sleep(retry_delay)

    # If loop finishes without both being healthy
    health_logger.warning(
        f"Containers failed to reach healthy state for {model}/app{app_num} "
        f"after {max_retries} attempts. "
        f"Last Status: BE={last_backend_status}, FE={last_frontend_status}"
    )
    message = (f"Containers failed to become healthy. "
               f"Last Status: Backend={last_backend_status}, Frontend={last_frontend_status}")
    return False, message


def process_security_analysis(
    template: str,
    analyzer, # Expects an analyzer instance (e.g., BackendSecurityAnalyzer)
    analysis_method: Callable, # Expects the method to call (e.g., analyzer.analyze_directory)
    model: str,
    app_num: int,
    full_scan: bool,
    no_issue_message: str = "No significant issues found.", # Default message
) -> Response:
    """
    Common logic for running security analysis and rendering the result template.

    Args:
        template: Template name to render (e.g., "backend_analysis.html").
        analyzer: Security analyzer instance.
        analysis_method: The method on the analyzer to call for analysis.
        model: Model name.
        app_num: App number (1-based).
        full_scan: Whether to use all tools/rules in the analysis.
        no_issue_message: Message to display when no issues are found.

    Returns:
        Rendered Flask Response object.
    """
    sec_logger = create_logger_for_component(f'security.{analyzer.__class__.__name__}')
    issues = None
    summary = {}
    error = None
    message = None
    tool_status = {}
    tool_output_details = {}

    try:
        sec_logger.info(f"Running analysis via {analysis_method.__name__} for {model}/app{app_num} (full_scan={full_scan})")

        # Call the provided analysis method
        analysis_result = analysis_method(
            model, app_num, use_all_tools=full_scan
        )

        # Unpack results (assuming format: issues, tool_status, tool_output_details)
        if isinstance(analysis_result, tuple) and len(analysis_result) == 3:
            issues, tool_status, tool_output_details = analysis_result
            issue_count = len(issues) if issues else 0
            sec_logger.info(f"Analysis complete for {model}/app{app_num}: Found {issue_count} issues.")
            if not issues:
                 message = no_issue_message
        else:
             # Handle unexpected return format from analysis method
             error = "Analysis method returned unexpected result format."
             sec_logger.error(f"{error} Result: {analysis_result}")
             issues = [] # Ensure issues is iterable for summary

        # Get summary regardless of errors during analysis, pass empty list if issues is None
        summary = analyzer.get_analysis_summary(issues or [])

    except ValueError as e:
        # Specific error likely indicating no relevant files found
        error = str(e)
        sec_logger.warning(f"Analysis value error for {model}/app{app_num}: {error}")
        summary = analyzer.get_analysis_summary([]) # Still provide empty summary structure
    except Exception as e:
        error = f"Security analysis failed: {e}"
        sec_logger.exception(f"Analysis failed for {model}/app{app_num}: {e}")
        summary = analyzer.get_analysis_summary([]) # Still provide empty summary structure

    # Render the template with all collected context
    return render_template(
        template,
        model=model,
        app_num=app_num,
        issues=issues or [], # Ensure issues is always a list for template
        summary=summary,
        error=error,
        message=message,
        full_scan=full_scan,
        tool_status=tool_status,
        tool_output_details=tool_output_details,
    )


def get_app_container_statuses(model: str, app_num: int, docker_manager: DockerManager) -> Dict[str, Any]:
    """
    Get container statuses dictionary for an app's backend and frontend.

    Args:
        model: Model name.
        app_num: App number (1-based).
        docker_manager: DockerManager instance.

    Returns:
        Dictionary with 'backend' and 'frontend' status dicts, or error info.
    """
    statuses = {"backend": None, "frontend": None, "error": None}
    try:
        b_name, f_name = get_container_names(model, app_num)
        statuses["backend"] = docker_manager.get_container_status(b_name).to_dict()
        statuses["frontend"] = docker_manager.get_container_status(f_name).to_dict()
    except ValueError as e: # Catch error from get_container_names
         statuses["error"] = str(e)
         logger.error(f"Could not get container names for status check: {e}")
    except Exception as e:
         statuses["error"] = f"Failed to get container statuses: {e}"
         logger.exception(f"Failed to get container statuses for {model}/app{app_num}: {e}")

    return statuses


# Add these functions to utils.py ? (These seem like they belong here)

def get_app_directory(app, model: str, app_num: int) -> Path:
    """
    Get the directory for a specific app.

    Args:
        app: Flask app instance (used for config potentially).
        model: Model name.
        app_num: App number (1-based).

    Returns:
        Path object to the app directory.

    Raises:
        FileNotFoundError: If the derived directory does not exist.
    """
    # FIXME: MAJOR WARNING - Using a hardcoded absolute path.
    # This breaks portability and is highly discouraged.
    # Consider using a path relative to app.config['BASE_DIR']
    # or another configurable base path from AppConfig.
    # Example using config (if BASE_DIR is project root):
    # project_root = Path(app.config.get('BASE_DIR', '.')).parent
    # direct_path = project_root / model / f"app{app_num}"
    direct_path = Path(r"c:\Users\grabowmar\Desktop\ThesisAppsSvelte") / f"{model}/app{app_num}"

    logger.warning(f"Using hardcoded absolute path (Not Recommended): {direct_path}") # Changed log level

    # Check if directory exists and raise error if not, as functions depend on it
    if not direct_path.is_dir():
        logger.error(f"Required application directory does not exist: {direct_path}")
        raise FileNotFoundError(f"Application directory not found: {direct_path}")

    logger.debug(f"Confirmed app directory exists: {direct_path}")
    return direct_path


def stop_zap_scanners(scans: Dict[str, Any]) -> None:
    """
    Stop all active ZAP scanners stored in the provided dictionary.

    Args:
        scans: Dictionary mapping scan keys to scanner instances.
    """
    zap_logger = create_logger_for_component('zap_scanner.stop')
    stopped_count = 0
    scan_keys = list(scans.keys()) # Avoid modifying dict while iterating

    for scan_key in scan_keys:
        scanner = scans.get(scan_key) # Get scanner safely
        if scanner and hasattr(scanner, "stop_scan") and callable(scanner.stop_scan):
            try:
                # Attempt to parse model/app from key for logging
                try:
                     model, app_num_str = scan_key.split("-")[:2]
                     app_num = int(app_num_str)
                     log_prefix = f"{model}/app{app_num} (Key: {scan_key})"
                except ValueError:
                     log_prefix = f"(Key: {scan_key})" # Fallback if key format unexpected

                zap_logger.info(f"Attempting to stop ZAP scan for {log_prefix}")
                # Call the stop method - assumes stop_scan handles its own state
                scanner.stop_scan(model=model, app_num=app_num) # Pass identifying info if needed by stop_scan
                stopped_count += 1
                # Optionally remove stopped scans from the dict if managed here
                # del scans[scan_key]
            except Exception as e:
                zap_logger.exception(f"Error stopping scan for {log_prefix}: {e}")
        elif scanner:
             # Log if the item is not a valid scanner instance
             zap_logger.warning(
                 f"Item for key {scan_key} is not a valid scanner instance "
                 f"(Type: {type(scanner)}). Cannot stop."
             )
        # else: scan_key might have been removed if stop was successful and cleanup done here

    if stopped_count > 0:
        zap_logger.info(f"Attempted to stop {stopped_count} ZAP scans.")
    else:
         zap_logger.info("No active ZAP scans found to stop.")


def get_scan_manager():
    """
    Retrieve or initialize the ScanManager instance on the Flask app context.

    Returns:
        ScanManager instance.
    """
    # Imported locally to avoid circular dependency with services/routes
    from services import ScanManager

    if not hasattr(current_app, 'scan_manager'):
        logger.info("Initializing ScanManager on app context.")
        current_app.scan_manager = ScanManager()
    return current_app.scan_manager