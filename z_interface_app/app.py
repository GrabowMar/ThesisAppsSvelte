import logging
import os
import time
import http
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Union, List, Set, TypeVar, Type, Callable
from threading import Lock

from flask import Flask, request, render_template, jsonify, Response, current_app, g
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix


# Constants - consider moving to AppConfig
AJAX_HEADER_NAME = "X-Requested-With"
AJAX_HEADER_VALUE = "XMLHttpRequest"

# Import modules with proper exception handling
try:
    from batch_analysis import init_batch_analysis, batch_analysis_bp
    HAS_BATCH_ANALYSIS = True
except ImportError:
    HAS_BATCH_ANALYSIS = False

from backend_security_analysis import BackendSecurityAnalyzer
from frontend_security_analysis import FrontendSecurityAnalyzer
from gpt4all_analysis import GPT4AllAnalyzer
from performance_analysis import LocustPerformanceTester
from zap_scanner import create_scanner
from logging_service import initialize_logging, create_logger_for_component
from services import DockerManager, SystemHealthMonitor, ScanManager, PortManager
from utils import AppConfig, CustomJSONEncoder, stop_zap_scanners
from routes import (
    main_bp, api_bp, analysis_bp, performance_bp,
    gpt4all_bp, zap_bp
)

# Locks for thread safety
INIT_LOCK = Lock()
CLEANUP_LOCK = Lock()

# Generic service type for initialization
ServiceType = TypeVar('ServiceType')


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


def perform_cleanup_tasks(app: Flask, logger: logging.Logger) -> None:
    """Perform cleanup tasks for the application."""
    try:
        # Clean up Docker containers if available
        docker_manager = app.config.get("docker_manager")
        if docker_manager and hasattr(docker_manager, 'cleanup_containers'):
            logger.debug("Cleaning up Docker containers")
            docker_manager.cleanup_containers()

        # Clean up idle ZAP scans
        if "ZAP_SCANS" in app.config:
            zap_scans = app.config["ZAP_SCANS"]
            if zap_scans and isinstance(zap_scans, dict):
                current_time = time.time()
                # Find scans that have been idle for more than 1 hour
                idle_scans = {
                    scan_id: scan_info for scan_id, scan_info in zap_scans.items()
                    if isinstance(scan_info, dict) and
                    scan_info.get("last_activity", 0) < current_time - 3600
                }

                if idle_scans:
                    logger.info(f"Stopping {len(idle_scans)} idle ZAP scans")
                    stop_zap_scanners(idle_scans)
                    for scan_id in idle_scans:
                        zap_scans.pop(scan_id, None)
    except Exception as e:
        logger.exception(f"Error during cleanup tasks: {e}")


def register_request_hooks(app: Flask) -> None:
    """Register request hooks for the Flask application."""
    hooks_logger = create_logger_for_component('hooks')
    cleanup_interval = app.config.get('CLEANUP_INTERVAL', 300)  # Default to 5 minutes
    
    app.config.setdefault("LAST_CLEANUP_TIME", 0)

    @app.before_request
    def perform_request_preprocessing() -> None:
        """Perform preprocessing tasks before handling a request."""
        with CLEANUP_LOCK:
            current_time = time.time()
            app = current_app._get_current_object()
            last_cleanup_time = app.config.get("LAST_CLEANUP_TIME", 0)

            if current_time - last_cleanup_time > cleanup_interval:
                hooks_logger.debug(
                    f"Running scheduled cleanup tasks (interval: {cleanup_interval}s)"
                )
                perform_cleanup_tasks(app, hooks_logger)
                app.config["LAST_CLEANUP_TIME"] = current_time

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

        app = current_app._get_current_object()
        teardown_logger.debug("Performing resource cleanup during teardown")
        perform_cleanup_tasks(app, teardown_logger)


def initialize_analyzers(app: Flask, base_path: Path, base_dir: Path) -> None:
    """Initialize all analyzers used by the application."""
    app.backend_security_analyzer = BackendSecurityAnalyzer(base_path)
    app.frontend_security_analyzer = FrontendSecurityAnalyzer(base_path)
    app.gpt4all_analyzer = GPT4AllAnalyzer(base_dir)
    app.performance_tester = LocustPerformanceTester(base_path)
    app.zap_scanner = create_scanner(base_dir)
    app.config["ZAP_SCANS"] = {}


def initialize_service(
    app: Flask, 
    service_class: Type[ServiceType], 
    config_key: str, 
    logger: logging.Logger,
    error_message: str
) -> Optional[ServiceType]:
    """Generic service initializer to reduce code duplication."""
    try:
        service = service_class()
        if config_key:
            app.config[config_key] = service
        else:
            setattr(app, service_class.__name__.lower(), service)
        logger.info(f"Initialized {service_class.__name__} successfully.")
        return service
    except ImportError as ie:
        logger.error(f"Failed to import {service_class.__name__}: {ie}. {error_message}")
        if config_key:
            app.config[config_key] = None
        return None
    except Exception as e:
        logger.exception(f"Error initializing {service_class.__name__}: {e}")
        if config_key:
            app.config[config_key] = None
        return None


def initialize_services(app: Flask, logger: logging.Logger) -> None:
    """Initialize all services used by the application."""
    # Initialize Docker manager
    initialize_service(
        app, 
        DockerManager, 
        "docker_manager", 
        logger,
        "Docker-based functionality disabled."
    )
    
    # Initialize Scan manager
    app.scan_manager = initialize_service(
        app, 
        ScanManager, 
        "", 
        logger,
        "Batch analysis requiring it may fail."
    )
    
    # Set the PortManager class
    app.port_manager = PortManager


def register_blueprints(app: Flask) -> None:
    """Register all blueprints for the application."""
    logger = create_logger_for_component('app')

    # Register main blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(analysis_bp)
    app.register_blueprint(performance_bp, url_prefix="/performance")
    app.register_blueprint(gpt4all_bp, url_prefix="/gpt4all")
    app.register_blueprint(zap_bp, url_prefix="/zap")

    # Conditionally register batch analysis blueprint
    register_batch_analysis_blueprint(app, logger)


def register_batch_analysis_blueprint(app: Flask, logger: logging.Logger) -> None:
    """Register the batch analysis blueprint if available."""
    # Check if batch analysis is available and scan manager is initialized
    if HAS_BATCH_ANALYSIS and getattr(app, 'scan_manager', None) is not None:
        try:
            init_batch_analysis(app)
            app.register_blueprint(batch_analysis_bp, url_prefix="/batch-analysis")
            logger.info("Batch analysis module initialized and registered")
        except Exception as e:
            logger.exception(f"Failed to initialize batch analysis module: {e}")
    else:
        if not HAS_BATCH_ANALYSIS:
            logger.warning("Batch analysis module not available (import failed)")
        elif getattr(app, 'scan_manager', None) is None:
            logger.warning("Batch analysis module not initialized (missing ScanManager)")


def check_system_health(app: Flask, logger: logging.Logger) -> bool:
    """Check the health of the system and its components."""
    docker_manager = app.config.get("docker_manager")
    system_health = False

    # Check Docker health if available
    if docker_manager and hasattr(docker_manager, 'client') and docker_manager.client:
        logger.info("Checking system health via Docker manager...")
        try:
            system_health = SystemHealthMonitor.check_health(docker_manager.client)
            if system_health:
                logger.info("System health check passed.")
            else:
                logger.warning("System health check failed - reduced functionality expected.")
        except Exception as e:
            logger.error(f"Error during system health check: {e}", exc_info=True)
            system_health = False
    else:
        logger.warning("Docker client unavailable - reduced functionality expected.")

    # Check if scan manager is available
    if not hasattr(app, 'scan_manager') or app.scan_manager is None:
        logger.warning("ScanManager not initialized. ZAP-related batch tasks may fail.")
        system_health = False

    # Store health state in config
    app.config["SYSTEM_HEALTH"] = system_health
    return system_health


def display_access_info(config: AppConfig, logger: logging.Logger) -> None:
    """Display information about how to access the application."""
    try:
        # Get host and port information with defaults
        host = config.HOST or "127.0.0.1"
        host_display = "localhost" if host in ["0.0.0.0", "127.0.0.1"] else host
        port = config.PORT or 5000

        # Display access information
        logger.info(f"{'='*50}")
        logger.info("AI Model Management System is ready!")
        logger.info(f"Access the application at: http://{host_display}:{port}/")
        logger.info(f"{'='*50}\n")
    except Exception as e:
        logger.error(f"Error displaying access information: {e}")
        logger.info("AI Model Management System is ready, but access info unavailable.")


def should_initialize_components(app: Flask, app_config: AppConfig) -> bool:
    """Determine if components should be initialized based on app state."""
    is_initialized = app.config.get('IS_INITIALIZED', False)
    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'

    # Initialize if:
    # 1. It's the reloader process in debug mode, or
    # 2. It's not debug mode and not already initialized
    return (is_reloader_process and app_config.DEBUG) or (not app_config.DEBUG and not is_initialized)


def create_app(config: Optional[AppConfig] = None) -> Flask:
    """Create and configure the Flask application."""
    # Create Flask app and configure it
    app = Flask(__name__)
    app_config = config or AppConfig.from_env()
    app.config.from_object(app_config)
    
    # Set up additional config defaults
    app.config["BASE_DIR"] = app_config.BASE_DIR
    app.config.setdefault('APP_BASE_PATH', app_config.BASE_DIR)
    app.config.setdefault('IS_INITIALIZED', False)
    app.config.setdefault('LAST_CLEANUP_TIME', 0)
    app.config.setdefault('CLEANUP_INTERVAL', 300)  # 5 minutes default

    # Set up logging
    initialize_logging(app)
    app_logger = create_logger_for_component('app')

    # Log startup info
    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    process_type = "reloader process" if is_reloader_process else "parent process"
    app_logger.info(f"Starting application setup ({process_type})")

    # Set custom JSON encoder
    app.json_encoder = CustomJSONEncoder

    # Determine paths
    base_path = app_config.BASE_DIR.parent
    app_logger.info(f"Application base directory: {app_config.BASE_DIR}")
    app_logger.info(f"Parent base path: {base_path}")

    # Initialize components
    initialize_app_components(app, app_config, base_path, app_logger)

    # Set up WSGI app with proxy fix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Register blueprints and hooks
    register_blueprints(app)
    register_error_handlers(app)
    register_request_hooks(app)

    app_logger.info("Application initialization complete")
    return app


def initialize_app_components(
    app: Flask,
    app_config: AppConfig,
    base_path: Path,
    app_logger: logging.Logger
) -> None:
    """Initialize application components based on configuration."""
    with INIT_LOCK:
        if should_initialize_components(app, app_config):
            app_logger.info("Initializing components and services")
            try:
                initialize_analyzers(app, base_path, app_config.BASE_DIR)
                initialize_services(app, app_logger)
                app.config['IS_INITIALIZED'] = True
            except Exception as e:
                app_logger.exception(f"Error during initialization: {e}")
                raise RuntimeError(f"Failed to initialize application: {e}") from e
        else:
            # Log skipping initialization
            process_type = "reloader process" if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' else "parent process"
            is_initialized = app.config.get('IS_INITIALIZED', False)
            app_logger.info(f"Skipping initialization ({process_type}, initialized={is_initialized})")
            
            # Set up minimal initialization for services if not initialized
            if not is_initialized:
                app.config["docker_manager"] = None
                app.scan_manager = None
                app.config["ZAP_SCANS"] = {}


if __name__ == "__main__":
    # Set up main logger
    main_logger = logging.getLogger('main')
    main_logger.setLevel(logging.INFO)

    if not main_logger.hasHandlers():
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
        main_logger.addHandler(handler)

    # Log startup information
    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    process_type = "reloader process" if is_reloader_process else "parent process"
    main_logger.info(f"Application starting via __main__ ({process_type})")

    # Load configuration
    config = AppConfig.from_env()

    # Set defaults for critical configuration
    if config.HOST is None:
        config.HOST = "127.0.0.1"
        main_logger.warning(f"HOST configuration is None, using default: {config.HOST}")

    if config.PORT is None:
        config.PORT = 5000
        main_logger.warning(f"PORT configuration is None, using default: {config.PORT}")

    try:
        # Create and initialize application
        main_logger.info(f"Creating application with LOG_LEVEL={config.LOG_LEVEL}")
        app = create_app(config)

        # Perform post-initialization health checks (only in main process or reloader with debug)
        if (is_reloader_process and config.DEBUG) or (not config.DEBUG):
            with app.app_context():
                main_logger.info("Performing post-initialization health checks...")
                system_health = check_system_health(app, main_logger)

                if not system_health:
                    main_logger.warning(
                        "System health check failed - reduced functionality expected. "
                        "Check logs for details."
                    )

                display_access_info(config, main_logger)

        # Start the Flask server
        main_logger.info(f"Starting Flask server on {config.HOST}:{config.PORT} (debug={config.DEBUG})")
        app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)

    except Exception as e:
        main_logger.critical(f"FATAL: Failed to start application: {e}", exc_info=True)
        import sys
        sys.exit(1)