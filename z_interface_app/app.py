import http
import logging
import os
import sys # Added for sys.exit
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

# Import modules with proper exception handling
try:
    from batch_analysis import init_batch_analysis, batch_analysis_bp
    HAS_BATCH_ANALYSIS = True
except ImportError as e:
    # Log the import error for batch_analysis specifically for easier debugging
    # Use a temporary logger if main logging isn't set up yet
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
            # Use current_app._get_current_object() to ensure we have the correct app instance
            # in environments where app might be a proxy.
            flask_app = current_app._get_current_object() 
            last_cleanup_time = flask_app.config.get("LAST_CLEANUP_TIME", 0)

            if current_time - last_cleanup_time > cleanup_interval:
                hooks_logger.debug(
                    f"Running scheduled cleanup tasks (interval: {cleanup_interval}s)"
                )
                perform_cleanup_tasks(flask_app, hooks_logger)
                flask_app.config["LAST_CLEANUP_TIME"] = current_time

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
                               This is used for analyzers that need access to the 'models' folder.
    :param app_base_dir: The base directory of the Flask app itself (e.g., z_interface_app).
                         Used for analyzers that might need resources relative to the app.
    """
    logger = create_logger_for_component('init.analyzers')
    
    # Path to the 'models' directory, relative to the project root
    # This is what APP_BASE_PATH (used by batch_analysis) should effectively point to.
    models_dir_for_analyzers = project_root_path / "models" 

    try:
        logger.info(f"Initializing backend security analyzer with models path: {models_dir_for_analyzers}")
        app.backend_security_analyzer = BackendSecurityAnalyzer(models_dir_for_analyzers)
    except Exception as e:
        logger.exception(f"Failed to initialize backend security analyzer: {e}")
        app.backend_security_analyzer = None
        
    try:
        logger.info(f"Initializing frontend security analyzer with models path: {models_dir_for_analyzers}")
        app.frontend_security_analyzer = FrontendSecurityAnalyzer(models_dir_for_analyzers)
    except Exception as e:
        logger.exception(f"Failed to initialize frontend security analyzer: {e}")
        app.frontend_security_analyzer = None
        
    try:
        # GPT4AllAnalyzer might use app_base_dir (z_interface_app) if it loads resources relative to itself,
        # or project_root_path if it also needs access to the 'models' structure.
        # Assuming it needs project_root_path for consistency or potential access to model-specific requirements.
        logger.info(f"Initializing GPT4All analyzer with base directory: {project_root_path}")
        app.gpt4all_analyzer = GPT4AllAnalyzer(project_root_path) 
    except Exception as e:
        logger.exception(f"Failed to initialize GPT4All analyzer: {e}")
        app.gpt4all_analyzer = None
        
    try:
        # LocustPerformanceTester might store reports relative to the models it tests.
        logger.info(f"Initializing performance tester with output/models path: {models_dir_for_analyzers}")
        # It needs a base output directory, typically within z_interface_app for serving static files,
        # but might also interact with model specific paths. Let's use app_base_dir for reports.
        performance_report_dir = app_base_dir / "performance_reports" # Static files might be served from here.
        app.performance_tester = LocustPerformanceTester(output_dir=performance_report_dir)
    except Exception as e:
        logger.exception(f"Failed to initialize performance tester: {e}")
        app.performance_tester = None
        
    try:
        # ZAP Scanner might generate reports or need config within the app's structure.
        logger.info(f"Initializing ZAP scanner with base directory (for its resources/reports): {app_base_dir}")
        app.zap_scanner = create_zap_scanner(app_base_dir) 
        app.config["ZAP_SCANS"] = {} # Initialize ZAP_SCANS storage
    except Exception as e:
        logger.exception(f"Failed to initialize ZAP scanner: {e}")
        app.zap_scanner = None
        app.config["ZAP_SCANS"] = {}

    # Initialize CodeQualityAnalyzer
    try:
        # Assuming CodeQualityAnalyzer exists in a 'code_quality_analysis.py'
        # and takes the path to the models directory for analysis.
        from code_quality_analysis import CodeQualityAnalyzer 
        logger.info(f"Initializing Code Quality analyzer with models path: {models_dir_for_analyzers}")
        app.code_quality_analyzer = CodeQualityAnalyzer(models_dir_for_analyzers)
    except ImportError:
        logger.warning("CodeQualityAnalyzer not found or could not be imported. Code quality analysis will be unavailable.")
        app.code_quality_analyzer = None
    except Exception as e:
        logger.exception(f"Failed to initialize Code Quality analyzer: {e}")
        app.code_quality_analyzer = None
    
    logger.info("All analyzers initialized (or placeholders set where errors occurred).")


def initialize_service(
    app: Flask, 
    service_class: Type[ServiceType], 
    attribute_name: str, # Attribute name to set on 'app'
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
        "docker_manager", # Will be app.docker_manager
        logger,
        "Docker-based functionality (e.g., ZAP scans) may be disabled or limited."
    )
    app.config["docker_manager"] = docker_manager # Also keep in app.config for legacy access if any

    initialize_service(
        app, 
        ScanManager, 
        "scan_manager", # Will be app.scan_manager
        logger,
        "Scan manager initialization failed. ZAP-related batch tasks may fail."
        # ScanManager constructor is parameterless according to services.py
    )
    
    # Initialize PortManager and set its cache
    port_manager_instance = initialize_service(
        app,
        PortManager,
        "port_manager", # Will be app.port_manager
        logger,
        "PortManager initialization failed. Performance tests and port-dependent features might be affected."
    )
    if port_manager_instance: # Check if initialization was successful
        try:
            model_index_map = {model.name: idx for idx, model in enumerate(AI_MODELS)}
            # Assuming PortManager instance has a method to set this, or it's a class method
            # If PortManager is mostly static methods, direct instantiation might not be needed
            # but batch_analysis expects an instance on app.port_manager
            if hasattr(port_manager_instance, 'set_model_index_cache'):
                 port_manager_instance.set_model_index_cache(model_index_map)
            else: # Fallback to class method if instance method not found
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
        # init_batch_analysis will check for its required services on the app object.
        # These services (like app.scan_manager, app.port_manager etc.) 
        # should have been initialized by initialize_services and initialize_analyzers by now.
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
    docker_manager = app.config.get("docker_manager") # From app.config
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
        # system_health = False # Uncomment if Docker is absolutely critical

    if not hasattr(app, 'scan_manager') or app.scan_manager is None:
        logger.warning("ScanManager not initialized. ZAP-related batch tasks will fail.")
        # system_health = False # Uncomment if ScanManager is critical

    app.config["SYSTEM_HEALTH"] = system_health
    return system_health


def display_access_info(config: AppConfig, logger: logging.Logger) -> None:
    """Display information about how to access the application."""
    try:
        host = config.HOST or "127.0.0.1"
        host_display = "localhost" if host in ["0.0.0.0", "127.0.0.1"] else host
        port = config.PORT or 5000

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
    is_main_werkzeug_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'

    if app_config.DEBUG:
        return is_main_werkzeug_process 
    else:
        return not is_initialized 


def create_app(config: Optional[AppConfig] = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app_config = config or AppConfig.from_env()
    app.config.from_object(app_config)
    
    z_interface_app_dir = Path(app.root_path) 
    app.config["Z_INTERFACE_APP_DIR"] = str(z_interface_app_dir)

    project_root_dir = z_interface_app_dir.parent 
    app.config["PROJECT_ROOT_DIR"] = str(project_root_dir)

    models_actual_path = project_root_dir / "models"
    app.config['APP_BASE_PATH'] = str(models_actual_path) 
    
    app.config.setdefault('IS_INITIALIZED', False)
    app.config.setdefault('LAST_CLEANUP_TIME', 0)
    app.config.setdefault('CLEANUP_INTERVAL', 300) 

    initialize_logging(app) 
    app_logger = create_logger_for_component('app')

    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    process_type = "reloader (worker) process" if is_reloader_process else "main (parent) process"
    app_logger.info(f"Starting application setup ({process_type}). Flask app root: {app.root_path}")
    app_logger.info(f"Project root directory set to: {project_root_dir}")
    app_logger.info(f"APP_BASE_PATH (for model discovery & batch_analysis) set to: {models_actual_path}")


    app.json_encoder = CustomJSONEncoder # type: ignore[misc] 

    initialize_app_components(app, app_config, project_root_dir, z_interface_app_dir, app_logger)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1) # type: ignore[assignment]

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
                
                app.config['IS_INITIALIZED'] = True
                app_logger.info("Application components initialized successfully.")
            except Exception as e:
                app_logger.exception(f"Critical error during application component initialization: {e}")
                app.config['IS_INITIALIZED'] = False 
                raise RuntimeError(f"Failed to initialize critical application components: {e}") from e
        else:
            process_type = "reloader (worker) process" if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' else "main (parent) process"
            is_initialized_flag = app.config.get('IS_INITIALIZED', False)
            app_logger.info(f"Skipping component initialization for this process ({process_type}, already_initialized={is_initialized_flag}).")
            
            # Ensure essential attributes/config keys exist even if full init is skipped.
            # This helps prevent AttributeError if accessed by other parts of the app
            # that might run in the parent Werkzeug process (e.g., initial setup).
            if not is_initialized_flag: # Only set defaults if truly not initialized yet
                app.docker_manager = getattr(app, 'docker_manager', None) # Keep if set by a partial init
                app.config["docker_manager"] = app.docker_manager # Ensure config also has it
                app.scan_manager = getattr(app, 'scan_manager', None)
                app.port_manager = getattr(app, 'port_manager', None)
                app.code_quality_analyzer = getattr(app, 'code_quality_analyzer', None)
                app.frontend_security_analyzer = getattr(app, 'frontend_security_analyzer', None)
                app.backend_security_analyzer = getattr(app, 'backend_security_analyzer', None)
                app.performance_tester = getattr(app, 'performance_tester', None)
                app.gpt4all_analyzer = getattr(app, 'gpt4all_analyzer', None)
                app.zap_scanner = getattr(app, 'zap_scanner', None)
                app.config.setdefault("ZAP_SCANS", {})


if __name__ == "__main__":
    main_logger = logging.getLogger('main_startup') 
    main_logger.setLevel(logging.INFO)
    if not main_logger.hasHandlers(): 
        startup_handler = logging.StreamHandler(sys.stdout) # Ensure logs go to stdout
        startup_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
        main_logger.addHandler(startup_handler)

    is_reloader_main_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    process_info = "Reloader (Worker) Process" if is_reloader_main_process else "Main (Parent) Process"
    main_logger.info(f"Application starting via __main__ ({process_info})")

    config = AppConfig.from_env()
    config.HOST = config.HOST or "127.0.0.1"
    config.PORT = config.PORT or 5000

    try:
        main_logger.info(f"Creating Flask application with LOG_LEVEL={config.LOG_LEVEL}, DEBUG={config.DEBUG}")
        flask_app = create_app(config)

        if (is_reloader_main_process and config.DEBUG) or (not config.DEBUG):
            with flask_app.app_context(): 
                main_logger.info("Performing post-initialization health checks...")
                system_health = check_system_health(flask_app, main_logger)
                if not system_health:
                    main_logger.warning("System health check reported issues. Some features might be limited. Check logs.")
                display_access_info(config, main_logger)
        elif not is_reloader_main_process and config.DEBUG:
             main_logger.info("Skipping health checks and access info display for Werkzeug main (parent) process in debug mode.")


        main_logger.info(f"Starting Flask server on http://{config.HOST}:{config.PORT}/ (Debug mode: {config.DEBUG})")
        flask_app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG, use_reloader=config.DEBUG) # Explicitly manage reloader based on debug

    except Exception as e:
        main_logger.critical(f"FATAL: Failed to start application: {e}", exc_info=True)
        sys.exit(1)