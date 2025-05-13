import http
import json
import logging
import os
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union, cast

from flask import (
    Response, current_app, jsonify, render_template, request
)
from werkzeug.exceptions import HTTPException

from logging_service import create_logger_for_component
from services import DockerManager, PortManager

_AJAX_REQUEST_HEADER_NAME = 'X-Requested-With'
_AJAX_REQUEST_HEADER_VALUE = 'XMLHttpRequest'
_DEFAULT_MODEL_COLOR = "#666666"

T = TypeVar('T')

logger = create_logger_for_component('app')


def safe_int_env(key: str, default: int) -> int:
    """Safely parse an integer from environment variables."""
    value = os.getenv(key)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning(f"Invalid integer value for {key}: '{value}', using default: {default}")
        return default


@dataclass
class AppConfig:
    DEBUG: bool = os.getenv("FLASK_ENV", "development") != "production"
    SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "your-secret-key-here")
    BASE_DIR: Path = Path(__file__).parent
    DOCKER_TIMEOUT: int = safe_int_env("DOCKER_TIMEOUT", 10)
    CACHE_DURATION: int = safe_int_env("CACHE_DURATION", 5)
    HOST: str = "0.0.0.0" if os.getenv("FLASK_ENV") == "production" else "127.0.0.1"
    PORT: int = safe_int_env("PORT", 5000)
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO" if os.getenv("FLASK_ENV") == "production" else "DEBUG")
    MODELS_BASE_DIR: Optional[str] = os.getenv("MODELS_BASE_DIR")
    CORS_ENABLED: bool = os.getenv("CORS_ENABLED", "false").lower() == "true"
    CORS_ORIGINS: List[str] = field(default_factory=lambda: ["http://localhost:5000"])
    AJAX_TIMEOUT: int = safe_int_env("AJAX_TIMEOUT", 30)

    def __post_init__(self):
        log_path = Path(self.LOG_DIR)
        if not log_path.is_absolute():
            log_path = self.BASE_DIR.parent / log_path
        log_path.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR = str(log_path)

        if self.SECRET_KEY == "your-secret-key-here" and not self.DEBUG:
            logger.warning("SECURITY WARNING: FLASK_SECRET_KEY is not set or is using the default value in a non-debug environment!")

        if self.MODELS_BASE_DIR is None:
            self.MODELS_BASE_DIR = str(self.BASE_DIR.parent / "models")
            logger.info(f"MODELS_BASE_DIR not set, using default: {self.MODELS_BASE_DIR}")

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls()


@dataclass
class AIModel:
    name: str
    color: str = _DEFAULT_MODEL_COLOR

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DockerStatus:
    exists: bool = False
    running: bool = False
    health: str = "unknown"
    status: str = "unknown"
    details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class APIResponse:
    success: bool = True
    message: Optional[str] = None
    data: Any = None
    error: Optional[str] = None
    code: int = http.HTTPStatus.OK

    def to_response(self) -> Tuple[Response, int]:
        response_data = {"success": self.success}
        if self.message is not None:
            response_data["message"] = self.message
        if self.data is not None:
            response_data["data"] = self.data
        if self.error is not None:
            response_data["error"] = self.error
        return jsonify(response_data), self.code


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


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if hasattr(obj, 'to_dict') and callable(obj.to_dict):
            return obj.to_dict()
        if hasattr(obj, "__dataclass_fields__"):
            return asdict(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return super().default(obj)


def log_and_handle_exception(func_name: str, e: Exception,
                             logger_name: str = 'error') -> Tuple[str, int]:
    error_logger = create_logger_for_component(logger_name)
    if isinstance(e, HTTPException):
        error_code = e.code or http.HTTPStatus.INTERNAL_SERVER_ERROR
        error_message = e.description or str(e)
        error_logger.warning(f"HTTP error in {func_name}: {error_code} - {error_message}")
    elif isinstance(e, ValueError):
        error_code = http.HTTPStatus.BAD_REQUEST
        error_message = str(e)
        error_logger.warning(f"Value error in {func_name}: {error_message}")
    elif isinstance(e, FileNotFoundError):
        error_code = http.HTTPStatus.NOT_FOUND
        error_message = str(e)
        error_logger.warning(f"File not found in {func_name}: {error_message}")
    elif isinstance(e, subprocess.TimeoutExpired):
        error_code = http.HTTPStatus.GATEWAY_TIMEOUT
        error_message = f"Operation timed out after {e.timeout}s"
        error_logger.error(f"Timeout in {func_name}: {error_message}")
    else:
        error_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
        error_message = f"An unexpected error occurred: {str(e)}"
        error_logger.exception(f"Exception in {func_name}: {e}")
    return error_message, error_code


def ajax_compatible(f: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(f)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        function_logger = create_logger_for_component(f'ajax.{f.__name__}')
        is_ajax = request.headers.get(_AJAX_REQUEST_HEADER_NAME) == _AJAX_REQUEST_HEADER_VALUE
        try:
            result = f(*args, **kwargs)
            return _format_ajax_response(result, is_ajax, function_logger)
        except Exception as e:
            return _handle_ajax_exception(e, is_ajax, f.__name__, function_logger)
    return wrapped


def _format_ajax_response(result: Any, is_ajax: bool,
                          logger: Optional[logging.Logger] = None) -> Any:
    if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], Response):
        return result
    if isinstance(result, APIResponse):
        return result.to_response()
    if is_ajax:
        api_response = APIResponse(success=True, data=result, code=http.HTTPStatus.OK)
        return api_response.to_response()
    if isinstance(result, Response):
        return result
    elif isinstance(result, str):
        return result
    else:
        if logger:
            logger.warning(
                f"Non-AJAX request returned unexpected type: {type(result)}. Converting to string."
            )
        return str(result)


def _handle_ajax_exception(e: Exception, is_ajax: bool, func_name: str,
                           logger: Optional[logging.Logger] = None) -> Any:
    error_message, error_code = log_and_handle_exception(func_name, e)
    if is_ajax:
        error_response = APIResponse(
            success=False,
            error=error_message,
            message="An error occurred processing your request.",
            code=error_code
        )
        return error_response.to_response()
    else:
        return render_template("500.html", error=error_message), error_code


def get_model_index(model_name: str) -> Optional[int]:
    """
    Get the index of a model in the AI_MODELS list.
    
    Args:
        model_name: Name of the model to find
        
    Returns:
        The index of the model in AI_MODELS, or None if not found
    """
    try:
        return next(i for i, m in enumerate(AI_MODELS) if m.name == model_name)
    except StopIteration:
        logger.warning(f"Model name '{model_name}' not found in AI_MODELS list.")
        return None


def get_models_base_dir(config: Optional[Dict[str, Any]] = None) -> Path:
    """
    Get the models base directory from configuration.
    
    Args:
        config: Application configuration dictionary
        
    Returns:
        Path to the models base directory
    """
    models_base_dir = None
    
    if config:
        # Try to get from config dict
        models_base_dir = config.get('MODELS_BASE_DIR')
        
        # Try to get from APP_CONFIG object
        if not models_base_dir:
            app_config_obj = config.get('APP_CONFIG')
            if app_config_obj and hasattr(app_config_obj, 'MODELS_BASE_DIR'):
                models_base_dir = app_config_obj.MODELS_BASE_DIR
    
    # Use app's base directory as fallback
    if not models_base_dir:
        base_dir = config.get('BASE_DIR') if config else None
        if not base_dir:
            logger.warning("No BASE_DIR found, using current directory")
            base_dir = Path.cwd()
        models_base_dir = Path(base_dir).parent / "models"
        logger.debug(f"Using default models base directory: {models_base_dir}")
    
    return Path(models_base_dir)


def get_container_names(model: str, app_num: int) -> Tuple[str, str]:
    """
    Get backend and frontend container names for a model/app.
    
    Args:
        model: Model name
        app_num: Application number
        
    Returns:
        Tuple of (backend_container_name, frontend_container_name)
        
    Raises:
        ValueError: If the model is not found or port configuration is invalid
    """
    idx = get_model_index(model)
    if idx is None:
        raise ValueError(f"Model '{model}' not found in configuration.")
    
    try:
        ports = PortManager.get_app_ports(idx, app_num)
        base = model.lower()
        return (f"{base}_backend_{ports['backend']}", f"{base}_frontend_{ports['frontend']}")
    except KeyError as e:
        logger.error(f"Missing expected port key for {model}/app{app_num}: {e}")
        raise ValueError(f"Invalid port configuration: {e}")
    except ValueError as e:
        logger.error(f"Failed to get ports for {model}/app{app_num}: {e}")
        raise


def get_app_info(model_name: str, app_num: int) -> Optional[Dict[str, Any]]:
    """
    Get information about a specific AI model application.
    
    Args:
        model_name: Name of the AI model
        app_num: Application number
        
    Returns:
        Dictionary with app information, or None if the model doesn't exist
    """
    idx = get_model_index(model_name)
    if idx is None:
        return None
    model_instance = AI_MODELS[idx]
    try:
        ports = PortManager.get_app_ports(idx, app_num)
        host = current_app.config.get("HOST", "127.0.0.1")
        display_host = "127.0.0.1" if host == "0.0.0.0" else host
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


def get_app_directory(app: Any, model: str, app_num: int) -> Path:
    """
    Get the directory for a specific application.
    
    Args:
        app: Flask application object
        model: Model name
        app_num: Application number
        
    Returns:
        Path to the application directory
        
    Raises:
        ValueError: If BASE_DIR is missing from configuration
        FileNotFoundError: If the application directory does not exist
    """
    config = app.config
    models_base_dir = get_models_base_dir(config)
    
    model_app_path = models_base_dir / model / f"app{app_num}"
    
    if not model_app_path.is_dir():
        logger.error(f"Required application directory does not exist: {model_app_path}")
        raise FileNotFoundError(f"Application directory not found: {model_app_path}")
    
    logger.debug(f"Using app directory: {model_app_path}")
    return model_app_path


def get_apps_for_model(model_name: str) -> List[Dict[str, Any]]:
    """
    Get all applications for a specific model.
    
    Args:
        model_name: Name of the model
        
    Returns:
        List of dictionaries with application information
    """
    util_logger = create_logger_for_component('utils.apps')
    apps = []
    try:
        app = current_app._get_current_object()
        config = app.config
        models_base_dir = get_models_base_dir(config)
        model_base_dir = models_base_dir / model_name
        
        util_logger.debug(f"Scanning for apps in model base directory: {model_base_dir}")
        if not model_base_dir.exists() or not model_base_dir.is_dir():
            util_logger.warning(f"Model base directory does not exist: {model_base_dir}")
            return []
            
        for item in model_base_dir.iterdir():
            if item.is_dir() and item.name.startswith("app"):
                try:
                    app_num_str = item.name.replace("app", "")
                    app_num = int(app_num_str)
                    if app_num > 0:
                        app_info = get_app_info(model_name, app_num)
                        if app_info:
                            apps.append(app_info)
                        else:
                            util_logger.warning(f"Skipping invalid app configuration: {item.name}")
                except ValueError:
                    util_logger.warning(f"Skipping non-numeric app suffix: {item.name}")
                except Exception as e:
                    util_logger.error(f"Error processing app directory {item.name}: {e}")
                    
        apps.sort(key=lambda x: x.get('app_num', 0))
    except Exception as e:
        util_logger.exception(f"Error scanning apps for model '{model_name}': {e}")
        
    util_logger.debug(f"Found {len(apps)} valid apps for model '{model_name}'")
    return apps


def get_all_apps() -> List[Dict[str, Any]]:
    """
    Get all applications for all models.
    
    Returns:
        List of dictionaries with application information
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
            
    util_logger.info(f"Retrieved {len(all_apps)} apps across all models")
    return all_apps


def run_docker_compose(
    command: List[str],
    model: str,
    app_num: int,
    timeout: int = 60,
    check: bool = True,
) -> Tuple[bool, str]:
    """
    Run a docker-compose command for a specific application.
    
    Args:
        command: Docker-compose command arguments
        model: Model name
        app_num: Application number
        timeout: Command timeout in seconds
        check: Whether to check the return code
        
    Returns:
        Tuple of (success, output)
    """
    compose_logger = create_logger_for_component('docker_compose')
    try:
        app = current_app._get_current_object()
        app_dir = get_app_directory(app, model, app_num)
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
            
        project_name = f"{model.lower()}_app{app_num}"
        project_name = "".join(c if c.isalnum() or c == '_' else '_' for c in project_name)
        cmd = ["docker-compose", "-p", project_name, "-f", str(compose_file_path)] + command
        
        compose_logger.info(f"Running command: {' '.join(cmd)} in {app_dir} (timeout: {timeout}s)")
        result = subprocess.run(
            cmd,
            cwd=str(app_dir),
            check=check,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout,
        )
        
        output = result.stdout
        if result.stderr:
            output += "\n" + result.stderr
            
        success = result.returncode == 0
        
        if success:
            compose_logger.info(f"Command successful: {' '.join(cmd)}")
            compose_logger.debug(f"Output:\n{output}")
        elif not check:
            compose_logger.error(
                f"Command failed with code {result.returncode}: {' '.join(cmd)}\n"
                f"Output: {output[:1000]}..." if len(output) > 1000 else output
            )
            
        return success, output.strip()
        
    except FileNotFoundError:
        compose_logger.exception("`docker-compose` command not found. Is Docker Compose installed?")
        return False, "`docker-compose` command not found."
    except subprocess.TimeoutExpired:
        compose_logger.error(f"Command timed out after {timeout}s")
        return False, f"Command timed out after {timeout}s"
    except subprocess.CalledProcessError as e:
        output = e.stdout + ("\n" + e.stderr if e.stderr else "")
        compose_logger.error(
            f"Command failed with code {e.returncode}: {' '.join(e.cmd)}\n"
            f"Output: {output[:1000]}..." if len(output) > 1000 else output
        )
        return False, output.strip()
    except Exception as e:
        compose_logger.exception(f"Error running docker-compose: {e}")
        return False, f"An unexpected error occurred: {e}"


def handle_docker_action(action: str, model: str, app_num: int) -> Tuple[bool, str]:
    """
    Handle Docker actions (start, stop, restart, build, rebuild).
    
    Args:
        action: Action to perform (start, stop, restart, build, rebuild)
        model: Model name
        app_num: Application number
        
    Returns:
        Tuple of (success, message)
    """
    docker_logger = create_logger_for_component(f'docker.action.{action}')
    commands_config = {
        "start": [ (["up", "-d", "--remove-orphans"], True, 90) ],
        "stop": [ (["down"], True, 60) ],
        "restart": [ (["restart"], True, 90) ],
        "build": [ (["build", "--no-cache"], True, 600) ],
        "rebuild": [
            (["down"], True, 60),
            (["build", "--no-cache"], True, 600),
            (["up", "-d", "--remove-orphans"], True, 90)
        ],
    }
    
    if action not in commands_config:
        docker_logger.error(f"Invalid docker action requested: {action}")
        return False, f"Invalid action: {action}"
        
    docker_logger.info(f"Initiating docker action '{action}' for {model}/app{app_num}")
    steps = commands_config[action]
    full_output = []
    
    for i, (cmd_args, check_flag, timeout) in enumerate(steps):
        step_desc = f"Step {i+1}/{len(steps)}: docker-compose {' '.join(cmd_args)}"
        docker_logger.info(f"Executing {step_desc} for {model}/app{app_num}")
        
        success, msg = run_docker_compose(cmd_args, model, app_num, timeout=timeout, check=check_flag)
        full_output.append(f"--- {step_desc} ---\n{msg}")
        
        if not success:
            error_msg = f"{action.capitalize()} failed during step: {' '.join(cmd_args)}"
            docker_logger.error(f"Docker action '{action}' failed for {model}/app{app_num}")
            return False, f"{error_msg}\n\nFull Output:\n{''.join(full_output)}"
            
    docker_logger.info(f"Successfully completed docker action '{action}' for {model}/app{app_num}")
    return True, f"Action '{action}' completed successfully.\n\nFull Output:\n{''.join(full_output)}"


def verify_container_health(
    docker_manager: DockerManager,
    model: str,
    app_num: int,
    max_retries: int = 15,
    retry_delay: int = 5
) -> Tuple[bool, str]:
    """
    Verify the health of containers for a specific application.
    
    Args:
        docker_manager: Docker manager instance
        model: Model name
        app_num: Application number
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        
    Returns:
        Tuple of (healthy, message)
    """
    health_logger = create_logger_for_component('health')
    try:
        backend_name, frontend_name = get_container_names(model, app_num)
    except ValueError as e:
        health_logger.error(f"Cannot verify health, invalid model/app: {e}")
        return False, f"Invalid model/app: {e}"
        
    health_logger.info(
        f"Verifying container health for {model}/app{app_num} "
        f"({backend_name}, {frontend_name}). "
        f"Max retries: {max_retries}, Delay: {retry_delay}s."
    )
    
    backend_healthy = False
    frontend_healthy = False
    last_backend_status = "N/A"
    last_frontend_status = "N/A"
    
    for attempt in range(1, max_retries + 1):
        try:
            backend = docker_manager.get_container_status(backend_name)
            frontend = docker_manager.get_container_status(frontend_name)
            
            backend_healthy = backend.running and backend.health == "healthy"
            frontend_healthy = frontend.running and frontend.health == "healthy"
            
            last_backend_status = f"{backend.status}({backend.health})" if backend.exists else "Not Found"
            last_frontend_status = f"{frontend.status}({frontend.health})" if frontend.exists else "Not Found"
            
            health_logger.debug(
                f"Health check attempt {attempt}/{max_retries}: "
                f"Backend[{backend_name}]: {last_backend_status}, "
                f"Frontend[{frontend_name}]: {last_frontend_status}"
            )
            
            if backend_healthy and frontend_healthy:
                health_logger.info(f"Containers confirmed healthy for {model}/app{app_num}")
                return True, "All containers healthy"
                
        except Exception as e:
            health_logger.exception(f"Error during health check attempt {attempt}: {e}")
            
        if attempt < max_retries:
            time.sleep(retry_delay)
            
    health_logger.warning(
        f"Containers failed to reach healthy state for {model}/app{app_num} "
        f"after {max_retries} attempts. "
        f"Last Status: BE={last_backend_status}, FE={last_frontend_status}"
    )
    
    message = (
        f"Containers failed to become healthy. "
        f"Last Status: Backend={last_backend_status}, Frontend={last_frontend_status}"
    )
    return False, message


def process_security_analysis(
    template: str,
    analyzer: Any,
    analysis_method: Callable,
    model: str,
    app_num: int,
    full_scan: bool,
    no_issue_message: str = "No significant issues found.",
) -> Response:
    """
    Process security analysis for an application.
    
    Args:
        template: Template name to render
        analyzer: Security analyzer instance
        analysis_method: Analysis method to call
        model: Model name
        app_num: Application number
        full_scan: Whether to perform a full scan
        no_issue_message: Message to display when no issues are found
        
    Returns:
        Rendered template response
    """
    sec_logger = create_logger_for_component(f'security.{analyzer.__class__.__name__}')
    issues = []
    summary = {}
    error = None
    message = None
    tool_status = {}
    tool_output_details = {}
    
    try:
        sec_logger.info(
            f"Running analysis via {analysis_method.__name__} for {model}/app{app_num} "
            f"(full_scan={full_scan})"
        )
        
        analysis_result = analysis_method(model, app_num, use_all_tools=full_scan)
        
        if isinstance(analysis_result, tuple) and len(analysis_result) == 3:
            issues, tool_status, tool_output_details = analysis_result
            issue_count = len(issues) if issues else 0
            sec_logger.info(f"Analysis complete: Found {issue_count} issues")
            if not issues:
                message = no_issue_message
        else:
            error = "Analysis method returned unexpected result format"
            sec_logger.error(f"{error} Result: {analysis_result}")
            issues = []
            
        summary = analyzer.get_analysis_summary(issues)
        
    except ValueError as e:
        error = str(e)
        sec_logger.warning(f"Analysis value error: {error}")
        summary = analyzer.get_analysis_summary([])
    except Exception as e:
        error = f"Security analysis failed: {e}"
        sec_logger.exception(f"Analysis failed: {e}")
        summary = analyzer.get_analysis_summary([])
        
    return render_template(
        template,
        model=model,
        app_num=app_num,
        issues=issues,
        summary=summary,
        error=error,
        message=message,
        full_scan=full_scan,
        tool_status=tool_status,
        tool_output_details=tool_output_details,
    )


def get_app_container_statuses(
    model: str, app_num: int, docker_manager: DockerManager
) -> Dict[str, Any]:
    """
    Get container statuses for a specific application.
    
    Args:
        model: Model name
        app_num: Application number
        docker_manager: Docker manager instance
        
    Returns:
        Dictionary with container statuses
    """
    statuses = {"backend": None, "frontend": None, "error": None}
    
    try:
        b_name, f_name = get_container_names(model, app_num)
        statuses["backend"] = docker_manager.get_container_status(b_name).to_dict()
        statuses["frontend"] = docker_manager.get_container_status(f_name).to_dict()
    except ValueError as e:
        statuses["error"] = str(e)
        logger.error(f"Could not get container names: {e}")
    except Exception as e:
        statuses["error"] = f"Failed to get container statuses: {e}"
        logger.exception(f"Failed to get container statuses: {e}")
        
    return statuses


def stop_zap_scanners(scans: Dict[str, Any]) -> None:
    """
    Stop active ZAP scanners.
    
    Args:
        scans: Dictionary of active scanners
    """
    zap_logger = create_logger_for_component('zap_scanner.stop')
    stopped_count = 0
    scan_keys = list(scans.keys())
    
    for scan_key in scan_keys:
        scanner = scans.get(scan_key)
        if not scanner:
            continue
            
        if hasattr(scanner, "stop_scan") and callable(scanner.stop_scan):
            try:
                model = "unknown"
                app_num = 0
                
                try:
                    parts = scan_key.split("-")
                    if len(parts) >= 2:
                        model = parts[0]
                        app_num = int(parts[1])
                except (ValueError, IndexError):
                    pass
                    
                log_prefix = f"{model}/app{app_num}" if model != "unknown" else scan_key
                zap_logger.info(f"Stopping ZAP scan for {log_prefix}")
                scanner.stop_scan(model=model, app_num=app_num)
                stopped_count += 1
            except Exception as e:
                zap_logger.exception(f"Error stopping scan: {e}")
        else:
            zap_logger.warning(
                f"Item for key {scan_key} is not a valid scanner instance "
                f"(Type: {type(scanner).__name__})"
            )
            
    if stopped_count > 0:
        zap_logger.info(f"Stopped {stopped_count} ZAP scans")
    else:
        zap_logger.info("No active ZAP scans found to stop")


def get_scan_manager():
    """
    Get or initialize the scan manager on the current application.
    
    Returns:
        ScanManager instance
    """
    from services import ScanManager
    if not hasattr(current_app, 'scan_manager'):
        logger.info("Initializing ScanManager on app context")
        current_app.scan_manager = ScanManager()
    return current_app.scan_manager