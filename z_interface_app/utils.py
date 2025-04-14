"""
Utility functions and helper classes for the AI Model Management System.
"""

# =============================================================================
# Standard Library Imports
# =============================================================================
import json
import os
import random
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Union

# =============================================================================
# Third-Party Imports
# =============================================================================
import docker
from flask import (
    Response, current_app, flash, g, jsonify, make_response, 
    redirect, render_template, request, url_for
)
from werkzeug.exceptions import BadRequest, HTTPException

# =============================================================================
# Custom Module Imports
# =============================================================================
from logging_service import create_logger_for_component
from services import DockerManager, PortManager, SystemHealthMonitor

# Create the main application logger
logger = create_logger_for_component('app')

# =============================================================================
# Configuration & Domain Models
# =============================================================================
@dataclass
class AppConfig:
    """Application configuration with environment variable fallbacks."""
    DEBUG: bool = True
    SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "your-secret-key-here")
    BASE_DIR: Path = Path(__file__).parent
    DOCKER_TIMEOUT: int = int(os.getenv("DOCKER_TIMEOUT", "10"))
    CACHE_DURATION: int = int(os.getenv("CACHE_DURATION", "5"))
    HOST: str = "0.0.0.0" if os.getenv("FLASK_ENV") == "production" else "127.0.0.1"
    PORT: int = int(os.getenv("PORT", "5000"))
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # CORS settings for API endpoints
    CORS_ENABLED: bool = os.getenv("CORS_ENABLED", "false").lower() == "true"
    CORS_ORIGINS: List[str] = field(default_factory=lambda: ["http://localhost:5000"])
    # jQuery Ajax specific settings
    JSONP_ENABLED: bool = os.getenv("JSONP_ENABLED", "false").lower() == "true"
    AJAX_TIMEOUT: int = int(os.getenv("AJAX_TIMEOUT", "30"))

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create a configuration instance from environment variables."""
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
    """Standard API response format for jQuery AJAX compatibility."""
    success: bool = True
    message: Optional[str] = None
    data: Any = None
    error: Optional[str] = None
    code: int = 200
    
    def to_response(self) -> Tuple[Response, int]:
        """Convert to Flask response with appropriate status code."""
        response_data = {
            "success": self.success,
            "message": self.message,
        }
        
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
    """Extended JSON encoder that can handle dataclasses and objects with __dict__."""
    
    def default(self, obj):
        """
        Custom encoding for special types.
        
        Args:
            obj: Object to encode
            
        Returns:
            JSON serializable representation
        """
        # Handle dataclasses
        if hasattr(obj, "__dataclass_fields__"):
            return asdict(obj)
        # Handle objects with __dict__
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        # Handle datetime objects
        if isinstance(obj, datetime):
            return obj.isoformat()
        # Handle Path objects
        if isinstance(obj, Path):
            return str(obj)
        # Default behavior
        return super().default(obj)

# =============================================================================
# Utility Functions & Decorators
# =============================================================================
def ajax_compatible(f):
    """
    Decorator to make endpoints compatible with jQuery AJAX.
    Ensures proper error handling and response formatting.
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        function_logger = create_logger_for_component('ajax')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        try:
            result = f(*args, **kwargs)
            
            # If already a response, return it
            if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], (dict, Response)):
                return result
                
            # If result is already an APIResponse, convert it
            if isinstance(result, APIResponse):
                return result.to_response()
                
            # For AJAX calls, ensure we return JSON
            if is_ajax:
                if isinstance(result, dict):
                    return jsonify(result)
                elif not isinstance(result, str) and hasattr(result, '__dict__'):
                    return jsonify(asdict(result))
                else:
                    return jsonify({"success": True, "data": result})
                    
            # Otherwise return original result
            return result
                
        except Exception as e:
            function_logger.exception(f"Error in {f.__name__}: {e}")
            
            if is_ajax:
                error_response = APIResponse(
                    success=False,
                    error=str(e),
                    code=500 if not isinstance(e, HTTPException) else e.code
                )
                return error_response.to_response()
                
            # For regular requests, render error template
            return render_template("500.html", error=str(e)), 500
    return wrapped


def get_model_index(model_name: str) -> int:
    """
    Get the index of a model in the AI_MODELS list.
    
    Args:
        model_name: Name of the model
        
    Returns:
        Index in the AI_MODELS list or 0 if not found
    """
    return next((i for i, m in enumerate(AI_MODELS) if m.name == model_name), 0)



def get_container_names(model: str, app_num: int) -> Tuple[str, str]:
    """
    Get the container names for a given model and app number.
    
    Args:
        model: Model name
        app_num: Application number
        
    Returns:
        Tuple of (backend_container_name, frontend_container_name)
    """
    idx = get_model_index(model)
    ports = PortManager.get_app_ports(idx, app_num)
    base = model.lower()
    return (f"{base}_backend_{ports['backend']}", f"{base}_frontend_{ports['frontend']}")


def get_app_info(model_name: str, app_num: int) -> Dict[str, Any]:
    """
    Get detailed information for a specific app.
    
    Args:
        model_name: Name of the AI model
        app_num: Application number
        
    Returns:
        Dictionary with app details
    """
    idx = get_model_index(model_name)
    model_color = next((m.color for m in AI_MODELS if m.name == model_name), "#666666")
    ports = PortManager.get_app_ports(idx, app_num)
    return {
        "name": f"{model_name} App {app_num}",
        "model": model_name,
        "color": model_color,
        "backend_port": ports["backend"],
        "frontend_port": ports["frontend"],
        "app_num": app_num,
        "backend_url": f"http://localhost:{ports['backend']}",
        "frontend_url": f"http://localhost:{ports['frontend']}",
    }


def get_apps_for_model(model_name: str) -> List[Dict[str, Any]]:
    """
    Get all apps for a specific model.
    
    Args:
        model_name: Name of the model
        
    Returns:
        List of app information dictionaries
    """
    base_path = Path(model_name)
    util_logger = create_logger_for_component('utils')
    
    if not base_path.exists():
        util_logger.debug(f"Model directory does not exist: {base_path}")
        return []
    
    apps = []
    try:
        app_dirs = sorted(
            (d for d in base_path.iterdir() if d.is_dir() and d.name.startswith("app")),
            key=lambda x: int(x.name.replace("app", ""))
        )
        
        for app_dir in app_dirs:
            try:
                app_num = int(app_dir.name.replace("app", ""))
                apps.append(get_app_info(model_name, app_num))
            except ValueError as e:
                util_logger.error(f"Error processing {app_dir}: {e}")
    except Exception as e:
        util_logger.exception(f"Error scanning apps for model {model_name}: {e}")
    
    util_logger.debug(f"Found {len(apps)} apps for model {model_name}")
    return apps


def get_all_apps() -> List[Dict[str, Any]]:
    """
    Get all apps for all models.
    
    Returns:
        List of app information dictionaries for all models
    """
    all_apps = []
    for model in AI_MODELS:
        model_apps = get_apps_for_model(model.name)
        all_apps.extend(model_apps)
    
    logger.debug(f"Retrieved {len(all_apps)} apps across all models")
    return all_apps


def run_docker_compose(
    command: List[str],
    model: str,
    app_num: int,
    timeout: int = 60,
    check: bool = True,
) -> Tuple[bool, str]:
    """
    Run a docker-compose command for a specific app.
    
    Args:
        command: The docker-compose command to run
        model: The model name
        app_num: The application number
        timeout: Command timeout in seconds
        check: Whether to check the command's return code
        
    Returns:
        Tuple of (success, output)
    """
    compose_logger = create_logger_for_component('docker_compose')
    app_dir = Path(f"{model}/app{app_num}")
    
    if not app_dir.exists():
        compose_logger.error(f"Directory not found: {app_dir}")
        return False, f"Directory not found: {app_dir}"
    
    # Check for compose file existence
    compose_file = app_dir / "docker-compose.yml"
    compose_yaml = app_dir / "docker-compose.yaml"
    if not compose_file.exists() and not compose_yaml.exists():
        compose_logger.error(f"No docker-compose.yml/yaml file found in {app_dir}")
        return False, f"No docker-compose file found in {app_dir}"
    
    # Build the custom project name
    project_name = f"{model}_app{app_num}".lower()

    
    # Include the -p option to rename the compose stack
    cmd = ["docker-compose", "-p", project_name] + command
    compose_logger.info(f"Running command: {' '.join(cmd)} in {app_dir} with timeout {timeout}s")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(app_dir),  # Ensure string path for compatibility
            check=check,
            capture_output=True,
            text=True,
            encoding='utf-8',  # Explicitly set UTF-8 encoding
            errors='replace',   # Replace invalid characters instead of failing
            timeout=timeout,
        )
        output = result.stdout or result.stderr
        success = result.returncode == 0
        
        if success:
            compose_logger.info(f"Command succeeded: {' '.join(cmd)}")
        else:
            compose_logger.error(
                f"Command failed with code {result.returncode}: {' '.join(cmd)}\n"
                f"Error output: {output[:500]}"
            )
        
        return success, output
    except subprocess.TimeoutExpired:
        compose_logger.error(f"Command timed out after {timeout}s: {' '.join(cmd)}")
        return False, f"Command timed out after {timeout}s"
    except Exception as e:
        compose_logger.exception(f"Error running {' '.join(cmd)}: {str(e)}")
        return False, str(e)


def handle_docker_action(action: str, model: str, app_num: int) -> Tuple[bool, str]:
    """
    Handle Docker actions (start, stop, reload, rebuild, build).
    
    Args:
        action: The action to perform
        model: The model name
        app_num: The application number
        
    Returns:
        Tuple of (success, message)
    """
    docker_logger = create_logger_for_component('docker')
    commands = {
        "start": [("up", "-d", 9000)],
        "stop": [("down", None, 300)],
        "reload": [("restart", None, 900)],
        "rebuild": [("down", None, 300), ("build", None, 6000), ("up", "-d", 1200)],  # Increased build timeout
        "build": [("build", None, 6000)],  # Increased build timeout
    }
    
    if action not in commands:
        docker_logger.error(f"Invalid action: {action}")
        return False, f"Invalid action: {action}"
    
    docker_logger.info(f"Starting {action} for {model}/app{app_num}")
    
    # Execute each command step
    for i, (base_cmd, extra_arg, timeout) in enumerate(commands[action]):
        cmd = [base_cmd] + ([extra_arg] if extra_arg else [])
        step_desc = f"Step {i+1}/{len(commands[action])}: {' '.join(cmd)}"
        docker_logger.info(f"{step_desc} for {model}/app{app_num}")
        
        success, msg = run_docker_compose(cmd, model, app_num, timeout=timeout)
        
        if not success:
            error_msg = f"{action.capitalize()} failed during {base_cmd}: {msg}"
            docker_logger.error(f"Docker {action} failed: {error_msg}")
            return False, error_msg
    
    docker_logger.info(f"Successfully completed {action} for {model}/app{app_num}")
    return True, f"Successfully completed {action}"


def verify_container_health(
    docker_manager: DockerManager, model: str, app_num: int, max_retries: int = 10, retry_delay: int = 3
) -> Tuple[bool, str]:
    """
    Verify that containers for an app are healthy.
    
    Args:
        docker_manager: Docker manager instance
        model: Model name
        app_num: App number
        max_retries: Maximum number of retries
        retry_delay: Delay between retries in seconds
        
    Returns:
        Tuple of (is_healthy, message)
    """
    health_logger = create_logger_for_component('health')
    backend_name, frontend_name = get_container_names(model, app_num)
    
    health_logger.info(f"Verifying health for {model}/app{app_num} ({backend_name}, {frontend_name})")
    
    for attempt in range(1, max_retries + 1):
        backend = docker_manager.get_container_status(backend_name)
        frontend = docker_manager.get_container_status(frontend_name)
        
        backend_status = f"{backend.status} ({backend.health})"
        frontend_status = f"{frontend.status} ({frontend.health})"
        health_logger.debug(
            f"Health check attempt {attempt}/{max_retries}: "
            f"Backend: {backend_status}, Frontend: {frontend_status}"
        )
        
        if backend.health == "healthy" and frontend.health == "healthy":
            health_logger.info(f"All containers healthy for {model}/app{app_num}")
            return True, "All containers healthy"
        
        time.sleep(retry_delay)
    
    health_logger.warning(
        f"Containers failed to reach healthy state for {model}/app{app_num} "
        f"after {max_retries} attempts"
    )
    return False, "Containers failed to reach healthy state"


def process_security_analysis(
    template: str,
    analyzer,
    analysis_method,
    model: str,
    app_num: int,
    full_scan: bool,
    no_issue_message: str,
):
    """
    Common logic for running security analysis and returning template.
    
    Args:
        template: Template name to render
        analyzer: Security analyzer instance
        analysis_method: Method to call for analysis
        model: Model name
        app_num: App number
        full_scan: Whether to run a full scan
        no_issue_message: Message to show when no issues found
        
    Returns:
        Rendered template with analysis results
    """
    sec_logger = create_logger_for_component('security')
    try:
        sec_logger.info(f"Running {template.split('.')[0]} analysis for {model}/app{app_num} (full_scan={full_scan})")
        
        issues, tool_status, tool_output_details = analysis_method(
            model, app_num, use_all_tools=full_scan
        )
        
        summary = analyzer.get_analysis_summary(issues) if issues else analyzer.get_analysis_summary([])
        sec_logger.info(
            f"Security analysis complete for {model}/app{app_num}: "
            f"Found {len(issues) if issues else 0} issues"
        )
        
        return render_template(
            template,
            model=model,
            app_num=app_num,
            issues=issues or [],
            summary=summary,
            error=None,
            message=no_issue_message if not issues else None,
            full_scan=full_scan,
            tool_status=tool_status,
            tool_output_details=tool_output_details,
        )
    except ValueError as e:
        sec_logger.warning(f"No files to analyze for {model}/app{app_num}: {e}")
        return render_template(
            template,
            model=model,
            app_num=app_num,
            issues=None,
            error=str(e),
            full_scan=full_scan,
            tool_status={},
            tool_output_details={},
        )
    except Exception as e:
        sec_logger.exception(f"Security analysis failed for {model}/app{app_num}: {e}")
        return render_template(
            template,
            model=model,
            app_num=app_num,
            issues=None,
            error=f"Security analysis failed: {e}",
            full_scan=full_scan,
            tool_status={},
            tool_output_details={},
        )


def get_app_container_statuses(model: str, app_num: int, docker_manager: DockerManager) -> Dict[str, Any]:
    """
    Get container statuses for an app's backend and frontend.
    
    Args:
        model: Model name
        app_num: App number
        docker_manager: Docker manager instance
        
    Returns:
        Dictionary with backend and frontend status
    """
    b_name, f_name = get_container_names(model, app_num)
    return {
        "backend": docker_manager.get_container_status(b_name).to_dict(),
        "frontend": docker_manager.get_container_status(f_name).to_dict(),
    }


# Add these functions to utils.py

def get_app_directory(app, model: str, app_num: int) -> Path:
    """
    Get the directory for a specific app, using the absolute direct path.
    
    Args:
        app: Flask app instance
        model: Model name
        app_num: App number
        
    Returns:
        Path to the app directory
    """
    # Hardcode the absolute path without z_interface_app
    direct_path = Path(r"c:\Users\grabowmar\Desktop\ThesisAppsSvelte") / f"{model}/app{app_num}"
    
    logger.debug(f"Using hardcoded direct path: {direct_path}")
    
    # Check if directory exists (only for logging purposes)
    if direct_path.exists() and direct_path.is_dir():
        logger.debug(f"Direct path exists: {direct_path}")
    else:
        logger.warning(f"Direct path does not exist: {direct_path}")
    
    # Always return direct path even if it doesn't exist
    return direct_path


def stop_zap_scanners(scans: Dict[str, Any]) -> None:
    """
    Stop all active ZAP scanners.
    
    Args:
        scans: Dictionary of scan_key -> scanner mappings
    """
    zap_logger = create_logger_for_component('zap_scanner')
    stopped_count = 0
    
    for scan_key, scanner in scans.items():
        if hasattr(scanner, "stop_scan") and callable(scanner.stop_scan):
            try:
                model, app_num = scan_key.split("-")[:2]
                zap_logger.info(f"Stopping ZAP scan for {model}/app{app_num}")
                scanner.stop_scan(model=model, app_num=int(app_num))
                stopped_count += 1
            except Exception as e:
                zap_logger.exception(f"Error stopping scan for {scan_key}: {e}")
        else:
            zap_logger.warning(
                f"Invalid scanner for key {scan_key}: expected a ZAPScanner instance but got {type(scanner)}"
            )
    
    if stopped_count > 0:
        zap_logger.info(f"Stopped {stopped_count} ZAP scans")


def get_scan_manager():
    """
    Retrieve or initialize the scan manager.
    
    Returns:
        ScanManager instance from current app or a new one if not present
    """
    from services import ScanManager  # Import here to avoid circular imports
    
    if not hasattr(current_app, 'scan_manager'):
        logger.debug("Creating new ScanManager instance")
        current_app.scan_manager = ScanManager()
    return current_app.scan_manager