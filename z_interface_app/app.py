import http
import logging
import os
import sys
import time
import threading
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Union, List, Set, TypeVar, Type, Callable

from flask import Flask, request, render_template, jsonify, Response, current_app, g
from werkzeug.exceptions import BadRequest, HTTPException, NotFound
from werkzeug.middleware.proxy_fix import ProxyFix

# Constants
AJAX_HEADER_NAME = "X-Requested-With"
AJAX_HEADER_VALUE = "XMLHttpRequest"
DEFAULT_CLEANUP_INTERVAL = 300  # 5 minutes
IDLE_SCAN_TIMEOUT = 3600  # 1 hour
MAX_ZAP_SCANS = 10  # Maximum concurrent ZAP scans to prevent memory issues
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000

# Import modules with proper exception handling
try:
    from batch_analysis import init_batch_analysis, batch_analysis_bp
    HAS_BATCH_ANALYSIS = True
except ImportError as e:
    temp_logger = logging.getLogger('app_startup')
    temp_logger.error(f"Failed to import batch_analysis: {e}", exc_info=True)
    HAS_BATCH_ANALYSIS = False

# Import all required modules
from backend_security_analysis import BackendSecurityAnalyzer
from frontend_security_analysis import FrontendSecurityAnalyzer
from gpt4all_analysis import GPT4AllAnalyzer
from performance_analysis import LocustPerformanceTester
from logging_service import initialize_logging, create_logger_for_component
from services import (
    DockerManager, SystemHealthMonitor, ScanManager, PortManager,
    create_scanner as create_zap_scanner
)
from utils import (
    AppConfig, CustomJSONEncoder, AIModel, AI_MODELS, stop_zap_scanners,
    APIResponse
)
from routes import (
    main_bp, api_bp, analysis_bp, performance_bp,
    gpt4all_bp, zap_bp
)

# Locks for thread safety
INIT_LOCK = threading.RLock()
CLEANUP_LOCK = threading.RLock()
CONFIG_LOCK = threading.RLock()

# Generic service type for initialization
ServiceType = TypeVar('ServiceType')


def get_config_value(app: Flask, key: str, default: Any = None) -> Any:
    """Thread-safe config getter."""
    with CONFIG_LOCK:
        return app.config.get(key, default)


def set_config_value(app: Flask, key: str, value: Any) -> None:
    """Thread-safe config setter."""
    with CONFIG_LOCK:
        app.config[key] = value


def validate_host_port(host: Optional[str], port: Optional[int]) -> Tuple[str, int]:
    """Validate and return host and port configuration."""
    # Validate host
    if not host:
        host = DEFAULT_HOST
    elif not isinstance(host, str) or len(host.strip()) == 0:
        raise ValueError(f"Invalid host value: {host}")
    
    # Validate port
    if port is None:
        port = DEFAULT_PORT
    elif not isinstance(port, int) or not (1 <= port <= 65535):
        raise ValueError(f"Invalid port value: {port}. Must be between 1 and 65535.")
    
    return host, port


def generate_error_response(
    app: Flask,
    error_code: int,
    error_name: str,
    error_message: str,
    original_error: Optional[Exception] = None,
    error_logger: Optional[logging.Logger] = None
) -> Tuple[Union[Response, str], int]:
    """Generate an appropriate error response based on request type."""
    if error_logger is None:
        error_logger = create_logger_for_component('errors')

    # Check if it's an AJAX request
    if request.headers.get(AJAX_HEADER_NAME) == AJAX_HEADER_VALUE:
        return jsonify({
            "success": False,
            "error": error_name,
            "message": error_message
        }), error_code

    # For regular requests, try to render an error template
    return _render_error_template(
        app, error_code, error_name, error_message, original_error, error_logger
    )


def _render_error_template(
    app: Flask,
    error_code: int,
    error_name: str,
    error_message: str,
    original_error: Optional[Exception],
    error_logger: logging.Logger
) -> Tuple[Union[Response, str], int]:
    """Attempt to render an appropriate error template."""
    template_name = f"{error_code}.html"
    fallback_template = "500.html"

    try:
        templates = set(app.jinja_env.list_templates())

        # First try specific error template
        if template_name in templates:
            return render_template(template_name, error=original_error or error_message), error_code

        # Then try fallback for server errors
        if error_code >= http.HTTPStatus.INTERNAL_SERVER_ERROR and fallback_template in templates:
            return render_template(fallback_template, error=original_error or error_message), error_code

        # Log if no templates found for common error codes
        if error_code in (http.HTTPStatus.NOT_FOUND, http.HTTPStatus.INTERNAL_SERVER_ERROR):
            error_logger.warning(f"Error template '{template_name}' not found, using basic response.")
    except Exception as e:
        error_logger.exception(f"Error while rendering error template: {e}")

    # Fallback to basic HTML response
    basic_response = f"<h1>Error {error_code}</h1><p>{error_name}: {error_message}</p>"
    return basic_response, error_code


def register_error_handlers(app: Flask) -> None:
    """Register error handlers for the Flask application."""
    error_logger = create_logger_for_component('errors')

    @app.errorhandler(http.HTTPStatus.NOT_FOUND)
    def not_found(error: HTTPException) -> Tuple[Union[Response, str], int]:
        error_logger.warning(f"404 error: {request.path} - {error.description}")
        return generate_error_response(
            app, http.HTTPStatus.NOT_FOUND, error.name, error.description, error, error_logger
        )

    @app.errorhandler(http.HTTPStatus.INTERNAL_SERVER_ERROR)
    def server_error(error: HTTPException) -> Tuple[Union[Response, str], int]:
        error_logger.error(f"500 error: {request.path} - {error}", exc_info=True)
        error_name = getattr(error, 'name', 'Internal Server Error')
        error_description = getattr(error, 'description', str(error))
        return generate_error_response(
            app, http.HTTPStatus.INTERNAL_SERVER_ERROR, error_name,
            error_description, error, error_logger
        )

    @app.errorhandler(BadRequest)
    def handle_bad_request(error: BadRequest) -> Tuple[Union[Response, str], int]:
        error_logger.warning(f"Bad request: {request.path} - {error.description}")
        return generate_error_response(
            app, http.HTTPStatus.BAD_REQUEST, error.name, error.description, error, error_logger
        )

    @app.errorhandler(NotFound)
    def handle_not_found(error: NotFound) -> Tuple[Union[Response, str], int]:
        error_logger.warning(f"Resource not found: {request.path} - {error.description}")
        return generate_error_response(
            app, http.HTTPStatus.NOT_FOUND, error.name, error.description, error, error_logger
        )

    @app.errorhandler(Exception)
    def handle_exception(error: Exception) -> Tuple[Union[Response, str], int]:
        error_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
        error_name = "Internal Server Error"
        error_description = str(error)

        if isinstance(error, HTTPException):
            error_code = error.code or http.HTTPStatus.INTERNAL_SERVER_ERROR
            error_name = error.name or "HTTP Error"
            error_description = error.description or str(error)

        error_logger.exception(
            f"Unhandled exception ({error_code} - {error_name}): {request.path} - {error}"
        )
        return generate_error_response(
            app, error_code, error_name, error_description, error, error_logger
        )


def cleanup_docker_containers(docker_manager: Any, logger: logging.Logger) -> None:
    """Clean up Docker containers."""
    if docker_manager and hasattr(docker_manager, 'cleanup_containers'):
        try:
            logger.debug("Cleaning up Docker containers")
            docker_manager.cleanup_containers()
        except Exception as e:
            logger.error(f"Failed to cleanup Docker containers: {e}")


def cleanup_idle_zap_scans(app: Flask, logger: logging.Logger) -> None:
    """Clean up idle ZAP scans and enforce maximum scan limit."""
    zap_scans = get_config_value(app, "ZAP_SCANS", {})
    if not isinstance(zap_scans, dict):
        return
    
    current_time = time.time()
    
    # Find idle scans
    idle_scans = {
        scan_id: scan_info for scan_id, scan_info in zap_scans.items()
        if isinstance(scan_info, dict) and
        scan_info.get("last_activity", 0) < current_time - IDLE_SCAN_TIMEOUT
    }
    
    # Clean up idle scans
    if idle_scans:
        logger.info(f"Stopping {len(idle_scans)} idle ZAP scans")
        try:
            stop_zap_scanners(idle_scans)
            for scan_id in idle_scans:
                zap_scans.pop(scan_id, None)
        except Exception as e:
            logger.error(f"Error stopping idle ZAP scans: {e}")
    
    # Enforce maximum scan limit
    if len(zap_scans) > MAX_ZAP_SCANS:
        logger.warning(f"ZAP scan limit exceeded ({len(zap_scans)}/{MAX_ZAP_SCANS}), removing oldest scans")
        # Sort by last_activity and remove oldest
        sorted_scans = sorted(
            zap_scans.items(),
            key=lambda x: x[1].get("last_activity", 0) if isinstance(x[1], dict) else 0
        )
        scans_to_remove = sorted_scans[:len(zap_scans) - MAX_ZAP_SCANS]
        
        for scan_id, scan_info in scans_to_remove:
            try:
                stop_zap_scanners({scan_id: scan_info})
                zap_scans.pop(scan_id, None)
            except Exception as e:
                logger.error(f"Error removing excess ZAP scan {scan_id}: {e}")


def perform_cleanup_tasks(app: Flask, logger: logging.Logger) -> None:
    """Perform cleanup tasks for the application."""
    # Clean up Docker containers
    docker_manager = get_config_value(app, "docker_manager")
    cleanup_docker_containers(docker_manager, logger)
    
    # Clean up ZAP scans
    cleanup_idle_zap_scans(app, logger)


def register_request_hooks(app: Flask) -> None:
    """Register request hooks for the Flask application."""
    hooks_logger = create_logger_for_component('hooks')
    cleanup_interval = get_config_value(app, 'CLEANUP_INTERVAL', DEFAULT_CLEANUP_INTERVAL)
    
    set_config_value(app, "LAST_CLEANUP_TIME", 0)

    @app.before_request
    def perform_request_preprocessing() -> None:
        """Perform preprocessing tasks before handling a request."""
        with CLEANUP_LOCK:
            current_time = time.time()
            flask_app = current_app._get_current_object()
            last_cleanup_time = get_config_value(flask_app, "LAST_CLEANUP_TIME", 0)

            if current_time - last_cleanup_time > cleanup_interval:
                hooks_logger.debug(
                    f"Running scheduled cleanup tasks (interval: {cleanup_interval}s)"
                )
                perform_cleanup_tasks(flask_app, hooks_logger)
                set_config_value(flask_app, "LAST_CLEANUP_TIME", current_time)

    @app.after_request
    def process_response(response: Response) -> Response:
        """Process and enhance response before returning to client."""
        # Add security headers to all responses
        response.headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        })

        # Add cache control headers for AJAX requests
        if request.headers.get(AJAX_HEADER_NAME) == AJAX_HEADER_VALUE:
            response.headers.update({
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0"
            })

        return response

    @app.teardown_appcontext
    def cleanup_resources(exception: Optional[Exception] = None) -> None:
        """Clean up resources when the application context ends."""
        teardown_logger = create_logger_for_component('teardown')

        if exception:
            teardown_logger.warning(f"Context teardown with exception: {exception}")

        flask_app = current_app._get_current_object()
        teardown_logger.debug("Performing resource cleanup during teardown")
        perform_cleanup_tasks(flask_app, teardown_logger)


def initialize_analyzers(app: Flask, project_root_path: Path, app_base_dir: Path) -> None:
    """
    Initialize all analyzers used by the application.
    :param app: The Flask application instance.
    :param project_root_path: The root directory of the project (e.g., THESISAPPSSVELTE).
    :param app_base_dir: The base directory of the Flask app itself (e.g., z_interface_app).
    """
    logger = create_logger_for_component('init.analyzers')
    
    # Validate paths
    try:
        models_dir_for_analyzers = project_root_path / "models"
        if not models_dir_for_analyzers.exists():
            logger.warning(f"Models directory does not exist: {models_dir_for_analyzers}")
    except Exception as e:
        logger.error(f"Error validating models directory path: {e}")
        models_dir_for_analyzers = project_root_path / "models"  # Continue with path anyway

    # Initialize each analyzer with proper error handling
    _initialize_backend_analyzer(app, models_dir_for_analyzers, logger)
    _initialize_frontend_analyzer(app, models_dir_for_analyzers, logger)
    _initialize_gpt4all_analyzer(app, project_root_path, logger)
    _initialize_performance_tester(app, app_base_dir, logger)
    _initialize_zap_scanner(app, app_base_dir, logger)
    _initialize_code_quality_analyzer(app, models_dir_for_analyzers, logger)
    
    logger.info("All analyzers initialized (or placeholders set where errors occurred).")


def _initialize_backend_analyzer(app: Flask, models_dir: Path, logger: logging.Logger) -> None:
    """Initialize backend security analyzer."""
    try:
        logger.info(f"Initializing backend security analyzer with models path: {models_dir}")
        app.backend_security_analyzer = BackendSecurityAnalyzer(models_dir)
    except Exception as e:
        logger.exception(f"Failed to initialize backend security analyzer: {e}")
        app.backend_security_analyzer = None


def _initialize_frontend_analyzer(app: Flask, models_dir: Path, logger: logging.Logger) -> None:
    """Initialize frontend security analyzer."""
    try:
        logger.info(f"Initializing frontend security analyzer with models path: {models_dir}")
        app.frontend_security_analyzer = FrontendSecurityAnalyzer(models_dir)
    except Exception as e:
        logger.exception(f"Failed to initialize frontend security analyzer: {e}")
        app.frontend_security_analyzer = None


def _initialize_gpt4all_analyzer(app: Flask, project_root: Path, logger: logging.Logger) -> None:
    """Initialize GPT4All analyzer."""
    try:
        logger.info(f"Initializing GPT4All analyzer with base directory: {project_root}")
        app.gpt4all_analyzer = GPT4AllAnalyzer(project_root)
    except Exception as e:
        logger.exception(f"Failed to initialize GPT4All analyzer: {e}")
        app.gpt4all_analyzer = None


def _initialize_performance_tester(app: Flask, app_base_dir: Path, logger: logging.Logger) -> None:
    """Initialize performance tester."""
    try:
        performance_report_dir = app_base_dir / "performance_reports"
        # Ensure directory exists
        performance_report_dir.mkdir(exist_ok=True)
        logger.info(f"Initializing performance tester with output path: {performance_report_dir}")
        app.performance_tester = LocustPerformanceTester(output_dir=performance_report_dir)
    except Exception as e:
        logger.exception(f"Failed to initialize performance tester: {e}")
        app.performance_tester = None


def _initialize_zap_scanner(app: Flask, app_base_dir: Path, logger: logging.Logger) -> None:
    """Initialize ZAP scanner."""
    try:
        logger.info(f"Initializing ZAP scanner with base directory: {app_base_dir}")
        app.zap_scanner = create_zap_scanner(app_base_dir)
        set_config_value(app, "ZAP_SCANS", {})
    except Exception as e:
        logger.exception(f"Failed to initialize ZAP scanner: {e}")
        app.zap_scanner = None
        set_config_value(app, "ZAP_SCANS", {})


def _initialize_code_quality_analyzer(app: Flask, models_dir: Path, logger: logging.Logger) -> None:
    """Initialize code quality analyzer."""
    try:
        from code_quality_analysis import CodeQualityAnalyzer
        logger.info(f"Initializing Code Quality analyzer with models path: {models_dir}")
        app.code_quality_analyzer = CodeQualityAnalyzer(models_dir)
    except ImportError:
        logger.warning("CodeQualityAnalyzer not found. Code quality analysis will be unavailable.")
        app.code_quality_analyzer = None
    except Exception as e:
        logger.exception(f"Failed to initialize Code Quality analyzer: {e}")
        app.code_quality_analyzer = None


def initialize_service(
    app: Flask, 
    service_class: Type[ServiceType], 
    attribute_name: str,
    logger: logging.Logger,
    error_message: str,
    *service_args: Any, 
    **service_kwargs: Any 
) -> Optional[ServiceType]:
    """Generic service initializer to reduce code duplication."""
    try:
        service = service_class(*service_args, **service_kwargs)
        setattr(app, attribute_name, service)
        logger.info(f"Initialized {service_class.__name__} successfully as app.{attribute_name}.")
        return service
    except ImportError as ie:
        logger.error(f"Failed to import {service_class.__name__}: {ie}. {error_message}")
        setattr(app, attribute_name, None)
        return None
    except Exception as e:
        logger.exception(f"Error initializing {service_class.__name__}: {e}")
        setattr(app, attribute_name, None)
        return None


def initialize_services(app: Flask, logger: logging.Logger) -> None:
    """Initialize all services used by the application."""
    
    docker_manager = initialize_service(
        app, 
        DockerManager, 
        "docker_manager",
        logger,
        "Docker-based functionality (e.g., ZAP scans) may be disabled or limited."
    )
    set_config_value(app, "docker_manager", docker_manager)

    initialize_service(
        app, 
        ScanManager, 
        "scan_manager",
        logger,
        "Scan manager initialization failed. ZAP-related batch tasks may fail."
    )
    
    # Initialize PortManager and set its cache
    port_manager_instance = initialize_service(
        app,
        PortManager,
        "port_manager",
        logger,
        "PortManager initialization failed. Performance tests and port-dependent features might be affected."
    )
    
    if port_manager_instance:
        _configure_port_manager_cache(port_manager_instance, logger)


def _configure_port_manager_cache(port_manager: Any, logger: logging.Logger) -> None:
    """Configure the PortManager model index cache."""
    try:
        model_index_map = {model.name: idx for idx, model in enumerate(AI_MODELS)}
        
        # Try instance method first, then class method
        if hasattr(port_manager, 'set_model_index_cache'):
            port_manager.set_model_index_cache(model_index_map)
        else:
            PortManager.set_model_index_cache(model_index_map)
        
        logger.info(f"Initialized PortManager model index cache with {len(model_index_map)} model indices")
    except Exception as e:
        logger.error(f"Failed to initialize PortManager model index cache: {e}")


def register_blueprints(app: Flask) -> None:
    """Register all blueprints for the application."""
    logger = create_logger_for_component('app.blueprints')

    # Register main blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(performance_bp)
    app.register_blueprint(gpt4all_bp)
    app.register_blueprint(zap_bp)
    logger.info("Core blueprints registered successfully")

    # Conditionally register batch analysis blueprint
    register_batch_analysis_blueprint(app, logger)


def register_batch_analysis_blueprint(app: Flask, logger: logging.Logger) -> None:
    """Register the batch analysis blueprint if available."""
    if HAS_BATCH_ANALYSIS:
        try:
            init_batch_analysis(app)
            app.register_blueprint(batch_analysis_bp)
            logger.info("Batch analysis module initialized and blueprint registered.")
        except Exception as e:
            logger.exception(f"Failed to initialize or register batch analysis module: {e}")
    else:
        logger.warning("Batch analysis module not available (import failed). Batch features disabled.")


def check_system_health(app: Flask, logger: logging.Logger) -> bool:
    """Check the health of the system and its components."""
    docker_manager = get_config_value(app, "docker_manager")
    system_health = True

    if docker_manager and hasattr(docker_manager, 'client') and docker_manager.client:
        logger.info("Checking system health via Docker manager...")
        try:
            if not SystemHealthMonitor.check_health(docker_manager.client):
                logger.warning("System health check via Docker failed - reduced functionality expected.")
                system_health = False
            else:
                logger.info("System health check via Docker passed.")
        except Exception as e:
            logger.error(f"Error during Docker system health check: {e}", exc_info=True)
            system_health = False
    else:
        logger.warning("Docker client unavailable - Docker-dependent functionality (like ZAP) may be limited.")

    if not hasattr(app, 'scan_manager') or app.scan_manager is None:
        logger.warning("ScanManager not initialized. ZAP-related batch tasks will fail.")

    set_config_value(app, "SYSTEM_HEALTH", system_health)
    return system_health


def display_access_info(config: AppConfig, logger: logging.Logger) -> None:
    """Display information about how to access the application."""
    try:
        host = config.HOST or DEFAULT_HOST
        host_display = "localhost" if host in ["0.0.0.0", "127.0.0.1"] else host
        port = config.PORT or DEFAULT_PORT

        logger.info("=" * 50)
        logger.info("AI Model Management System is ready!")
        logger.info(f"Access the application at: http://{host_display}:{port}/")
        logger.info("=" * 50 + "\n")
    except Exception as e:
        logger.error(f"Error displaying access information: {e}")
        logger.info("AI Model Management System is ready, but access info unavailable.")


def should_initialize_components(app: Flask, app_config: AppConfig) -> bool:
    """Determine if components should be initialized based on app state."""
    is_initialized = get_config_value(app, 'IS_INITIALIZED', False)
    is_main_werkzeug_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'

    if app_config.DEBUG:
        return is_main_werkzeug_process
    else:
        return not is_initialized


def setup_flask_json_encoder(app: Flask) -> None:
    """Set up custom JSON encoder for Flask, handling version differences."""
    try:
        # Check if we have Flask 2.2+ with the new json provider system
        if hasattr(app, 'json') and hasattr(app.json, 'encoder'):
            # Flask 2.2+ - set the encoder on the json provider
            app.json.encoder = CustomJSONEncoder
        else:
            # Flask < 2.2 - use the old json_encoder attribute
            app.json_encoder = CustomJSONEncoder  # type: ignore[misc]
    except AttributeError as e:
        # Fallback to old method if something goes wrong
        app.json_encoder = CustomJSONEncoder  # type: ignore[misc]
        logger = create_logger_for_component('app')
        logger.debug(f"Using legacy json_encoder setup: {e}")


def configure_app_paths(app: Flask) -> Tuple[Path, Path]:
    """Configure and validate application paths."""
    z_interface_app_dir = Path(app.root_path)
    set_config_value(app, "Z_INTERFACE_APP_DIR", str(z_interface_app_dir))

    project_root_dir = z_interface_app_dir.parent
    set_config_value(app, "PROJECT_ROOT_DIR", str(project_root_dir))

    models_actual_path = project_root_dir / "models"
    set_config_value(app, 'APP_BASE_PATH', str(models_actual_path))
    
    return project_root_dir, z_interface_app_dir


def create_app(config: Optional[AppConfig] = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app_config = config or AppConfig.from_env()
    app.config.from_object(app_config)
    
    # Configure paths
    project_root_dir, z_interface_app_dir = configure_app_paths(app)
    
    # Set default config values
    set_config_value(app, 'IS_INITIALIZED', False)
    set_config_value(app, 'LAST_CLEANUP_TIME', 0)
    set_config_value(app, 'CLEANUP_INTERVAL', DEFAULT_CLEANUP_INTERVAL)

    # Initialize logging
    initialize_logging(app)
    app_logger = create_logger_for_component('app')

    # Log startup information
    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    process_type = "reloader (worker) process" if is_reloader_process else "main (parent) process"
    app_logger.info(f"Starting application setup ({process_type}). Flask app root: {app.root_path}")
    app_logger.info(f"Project root directory set to: {project_root_dir}")
    app_logger.info(f"APP_BASE_PATH (for model discovery & batch_analysis) set to: {project_root_dir / 'models'}")

    # Set up JSON encoder
    setup_flask_json_encoder(app)

    # Initialize components
    initialize_app_components(app, app_config, project_root_dir, z_interface_app_dir, app_logger)

    # Configure proxy fix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)  # type: ignore[assignment]

    # Register blueprints and handlers
    register_blueprints(app)
    register_error_handlers(app)
    register_request_hooks(app)

    app_logger.info("Application initialization sequence complete.")
    return app


def initialize_app_components(
    app: Flask,
    app_config: AppConfig,
    project_root_path: Path,
    app_base_dir: Path,
    app_logger: logging.Logger
) -> None:
    """Initialize application components based on configuration."""
    with INIT_LOCK:
        if should_initialize_components(app, app_config):
            app_logger.info("Initializing core components and services...")
            try:
                initialize_services(app, app_logger)
                initialize_analyzers(app, project_root_path, app_base_dir)
                
                set_config_value(app, 'IS_INITIALIZED', True)
                app_logger.info("Application components initialized successfully.")
            except Exception as e:
                app_logger.exception(f"Critical error during application component initialization: {e}")
                set_config_value(app, 'IS_INITIALIZED', False)
                raise RuntimeError(f"Failed to initialize critical application components: {e}") from e
        else:
            process_type = "reloader (worker) process" if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' else "main (parent) process"
            is_initialized_flag = get_config_value(app, 'IS_INITIALIZED', False)
            app_logger.info(f"Skipping component initialization for this process ({process_type}, already_initialized={is_initialized_flag}).")
            
            # Ensure essential attributes exist
            _ensure_component_defaults(app)


def _ensure_component_defaults(app: Flask) -> None:
    """Ensure essential component attributes exist with defaults."""
    # Only set defaults if truly not initialized yet
    if not get_config_value(app, 'IS_INITIALIZED', False):
        # Preserve existing values or set to None
        app.docker_manager = getattr(app, 'docker_manager', None)
        set_config_value(app, "docker_manager", app.docker_manager)
        app.scan_manager = getattr(app, 'scan_manager', None)
        app.port_manager = getattr(app, 'port_manager', None)
        app.code_quality_analyzer = getattr(app, 'code_quality_analyzer', None)
        app.frontend_security_analyzer = getattr(app, 'frontend_security_analyzer', None)
        app.backend_security_analyzer = getattr(app, 'backend_security_analyzer', None)
        app.performance_tester = getattr(app, 'performance_tester', None)
        app.gpt4all_analyzer = getattr(app, 'gpt4all_analyzer', None)
        app.zap_scanner = getattr(app, 'zap_scanner', None)
        set_config_value(app, "ZAP_SCANS", {})


if __name__ == "__main__":
    # Set up main logger
    main_logger = logging.getLogger('main_startup')
    main_logger.setLevel(logging.INFO)
    if not main_logger.hasHandlers():
        startup_handler = logging.StreamHandler(sys.stdout)
        startup_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
        main_logger.addHandler(startup_handler)

    is_reloader_main_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    process_info = "Reloader (Worker) Process" if is_reloader_main_process else "Main (Parent) Process"
    main_logger.info(f"Application starting via __main__ ({process_info})")

    # Load configuration
    config = AppConfig.from_env()
    
    try:
        # Validate host and port
        config.HOST, config.PORT = validate_host_port(config.HOST, config.PORT)
        
        main_logger.info(f"Creating Flask application with LOG_LEVEL={config.LOG_LEVEL}, DEBUG={config.DEBUG}")
        flask_app = create_app(config)

        # Perform health checks and display info only in appropriate process
        if (is_reloader_main_process and config.DEBUG) or (not config.DEBUG):
            with flask_app.app_context():
                main_logger.info("Performing post-initialization health checks...")
                system_health = check_system_health(flask_app, main_logger)
                if not system_health:
                    main_logger.warning("System health check reported issues. Some features might be limited.")
                display_access_info(config, main_logger)
        elif not is_reloader_main_process and config.DEBUG:
            main_logger.info("Skipping health checks and access info display for Werkzeug main (parent) process in debug mode.")

        main_logger.info(f"Starting Flask server on http://{config.HOST}:{config.PORT}/ (Debug mode: {config.DEBUG})")
        flask_app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG, use_reloader=config.DEBUG)

    except ValueError as ve:
        main_logger.critical(f"Configuration error: {ve}")
        sys.exit(1)
    except Exception as e:
        main_logger.critical(f"FATAL: Failed to start application: {e}", exc_info=True)
        sys.exit(1)