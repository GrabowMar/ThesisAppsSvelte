# -*- coding: utf-8 -*-
"""
Flask application factory for AI Model Management System.
Handles app setup, error handling, request processing, and service initialization.
"""

import logging
import os
import time
import http
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Union
from threading import Lock

from flask import Flask, request, render_template, jsonify, Response, current_app
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

# Import required modules at the top level
# Try to import batch_analysis, but don't fail if unavailable
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

# Thread-safe lock for initialization and cleanup operations
INIT_LOCK = Lock()
CLEANUP_LOCK = Lock()
CLEANUP_INTERVAL = 300  # 5 minutes
AJAX_HEADER_VALUE = "XMLHttpRequest"


def generate_error_response(
    app: Flask,
    error_code: int,
    error_name: str,
    error_message: str,
    original_error: Optional[Exception] = None,
    error_logger: Optional[logging.Logger] = None
) -> Tuple[Union[Response, str], int]:
    """Generate appropriate error response (JSON for AJAX, HTML otherwise)."""
    if error_logger is None:
        error_logger = create_logger_for_component('errors')
        
    # AJAX requests get JSON response
    if request.headers.get("X-Requested-With") == AJAX_HEADER_VALUE:
        return jsonify({
            "success": False,
            "error": error_name,
            "message": error_message
        }), error_code

    # Standard requests get HTML response
    template_name = f"{error_code}.html"
    
    try:
        # Check if template exists before rendering
        if template_name in app.jinja_env.list_templates():
            return render_template(template_name, error=original_error or error_message), error_code
        elif error_code == http.HTTPStatus.NOT_FOUND:
            error_logger.warning(f"Error template '{template_name}' not found!")
        elif error_code >= http.HTTPStatus.INTERNAL_SERVER_ERROR:
            if "500.html" in app.jinja_env.list_templates():
                return render_template("500.html", error=original_error or error_message), error_code
            else:
                error_logger.warning("Fallback error template '500.html' not found!")
        else:
            error_logger.warning(f"Error template '{template_name}' not found, providing basic response.")
    except Exception as e:
        error_logger.exception(f"Error while checking for template existence: {e}")
    
    # Basic HTML fallback
    basic_response = f"<h1>Error {error_code}</h1><p>{error_name}: {error_message}</p>"
    return basic_response, error_code


def register_error_handlers(app: Flask) -> None:
    """Register Flask error handlers for HTTP status codes."""
    error_logger = create_logger_for_component('errors')

    @app.errorhandler(http.HTTPStatus.NOT_FOUND)
    def not_found(error: HTTPException):
        error_logger.warning(f"404 error: {request.path} - {error.description}")
        return generate_error_response(
            app, http.HTTPStatus.NOT_FOUND, error.name, error.description, error, error_logger
        )

    @app.errorhandler(http.HTTPStatus.INTERNAL_SERVER_ERROR)
    def server_error(error: HTTPException):
        error_logger.error(f"500 error: {request.path} - {error}", exc_info=True)
        error_name = getattr(error, 'name', 'Internal Server Error')
        error_description = getattr(error, 'description', str(error))
        return generate_error_response(
            app, http.HTTPStatus.INTERNAL_SERVER_ERROR, error_name, 
            error_description, error, error_logger
        )

    @app.errorhandler(Exception)
    def handle_exception(error: Exception):
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


def register_request_hooks(app: Flask) -> None:
    """Register Flask request hooks for request processing."""
    hooks_logger = create_logger_for_component('hooks')
    
    # Store last cleanup time in app config instead of global variable
    app.config.setdefault("LAST_CLEANUP_TIME", 0)
    
    @app.before_request
    def perform_request_preprocessing():
        # Use thread-safe access to cleanup state
        with CLEANUP_LOCK:
            current_time = time.time()
            last_cleanup_time = current_app.config.get("LAST_CLEANUP_TIME", 0)
            
            # Scheduled cleanup based on fixed interval
            if current_time - last_cleanup_time > CLEANUP_INTERVAL:
                hooks_logger.debug(
                    f"Running scheduled cleanup tasks (interval: {CLEANUP_INTERVAL}s)"
                )
                try:
                    # Docker container cleanup
                    docker_manager = current_app.config.get("docker_manager")
                    if docker_manager and hasattr(docker_manager, 'cleanup_containers'):
                        docker_manager.cleanup_containers()
                    
                    # Idle ZAP scan cleanup
                    if "ZAP_SCANS" in current_app.config:
                        zap_scans = current_app.config["ZAP_SCANS"]
                        if zap_scans and isinstance(zap_scans, dict):
                            idle_scans = []
                            for scan_id, scan_info in zap_scans.items():
                                if isinstance(scan_info, dict) and scan_info.get("last_activity", 0) < current_time - 3600:  # 1 hour idle
                                    idle_scans.append(scan_id)
                            
                            if idle_scans:
                                hooks_logger.info(f"Stopping {len(idle_scans)} idle ZAP scans")
                                stop_zap_scanners({k: zap_scans[k] for k in idle_scans})
                                # Remove stopped scans
                                for scan_id in idle_scans:
                                    zap_scans.pop(scan_id, None)
                    
                    current_app.config["LAST_CLEANUP_TIME"] = current_time
                except Exception as e:
                    hooks_logger.exception(f"Error during cleanup tasks: {e}")

    @app.after_request
    def process_response(response):
        # Security headers
        response.headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        })

        # AJAX request caching
        if request.headers.get("X-Requested-With") == AJAX_HEADER_VALUE:
            response.headers.update({
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0"
            })

        return response

    @app.teardown_appcontext
    def cleanup_resources(exception=None):
        teardown_logger = create_logger_for_component('teardown')
        
        if exception:
            teardown_logger.warning(f"Context teardown with exception: {exception}")

        try:
            # ZAP scan cleanup
            if "ZAP_SCANS" in current_app.config:
                zap_scans = current_app.config["ZAP_SCANS"]
                if zap_scans:
                    teardown_logger.debug("Stopping active ZAP scans during teardown")
                    stop_zap_scanners(zap_scans)
            
            # Docker resource cleanup
            docker_manager = current_app.config.get("docker_manager")
            if docker_manager and hasattr(docker_manager, 'cleanup_containers'):
                teardown_logger.debug("Cleaning up Docker resources during teardown")
                docker_manager.cleanup_containers()
        except Exception as e:
            teardown_logger.exception(f"Error during resource cleanup: {e}")


def initialize_analyzers(app: Flask, base_path: Path, base_dir: Path) -> None:
    """Initialize and attach analyzer components to the Flask application."""
    app.backend_security_analyzer = BackendSecurityAnalyzer(base_path)
    app.frontend_security_analyzer = FrontendSecurityAnalyzer(base_path)
    app.gpt4all_analyzer = GPT4AllAnalyzer(base_dir)
    app.performance_tester = LocustPerformanceTester(base_path)
    app.zap_scanner = create_scanner(base_dir)
    app.config["ZAP_SCANS"] = {}


def initialize_services(app: Flask, logger: logging.Logger) -> None:
    """Initialize and attach service components to the Flask application."""
    # DockerManager initialization
    try:
        docker_manager = DockerManager()
        app.config["docker_manager"] = docker_manager
        logger.info("Initialized DockerManager on app context.")
    except ImportError as ie:
        logger.error(f"Failed to import DockerManager: {ie}. Docker-based functionality disabled.")
        app.config["docker_manager"] = None
    except Exception as e:
        logger.exception(f"Error initializing DockerManager: {e}")
        app.config["docker_manager"] = None

    # ScanManager initialization
    try:
        app.scan_manager = ScanManager()
        logger.info("Initialized ScanManager on app context.")
    except ImportError as ie:
        logger.error(f"Failed to import ScanManager: {ie}. Batch analysis requiring it may fail.")
        app.scan_manager = None
    except Exception as e:
        logger.exception(f"Error initializing ScanManager: {e}")
        app.scan_manager = None

    # PortManager is used via class methods
    app.port_manager = PortManager


def register_blueprints(app: Flask) -> None:
    """Register application blueprints."""
    # Core blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(analysis_bp)
    app.register_blueprint(performance_bp, url_prefix="/performance")
    app.register_blueprint(gpt4all_bp, url_prefix="/gpt4all")
    app.register_blueprint(zap_bp, url_prefix="/zap")
    
    # Batch analysis (only if available and ScanManager is initialized)
    logger = create_logger_for_component('app')
    if HAS_BATCH_ANALYSIS and app.scan_manager is not None:
        try:
            init_batch_analysis(app)
            app.register_blueprint(batch_analysis_bp, url_prefix="/batch-analysis")
            logger.info("Batch analysis module initialized and registered")
        except Exception as e:
            logger.exception(f"Failed to initialize batch analysis module: {e}")
    else:
        if not HAS_BATCH_ANALYSIS:
            logger.warning("Batch analysis module not available (import failed)")
        else:
            logger.warning("Batch analysis module not initialized (missing ScanManager)")


def check_system_health(app: Flask, logger: logging.Logger) -> bool:
    """Perform system health checks and return status."""
    docker_manager = app.config.get("docker_manager")
    system_health = False

    # Docker health check
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

    # ScanManager availability check
    if not hasattr(app, 'scan_manager') or app.scan_manager is None:
        logger.warning("ScanManager not initialized. ZAP-related batch tasks may fail.")
        system_health = False
    
    # Store health status
    app.config["SYSTEM_HEALTH"] = system_health
    return system_health


def display_access_info(config: AppConfig, logger: logging.Logger) -> None:
    """Display application access information in logs."""
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


def create_app(config: Optional[AppConfig] = None) -> Flask:
    """Create and configure the Flask application instance."""
    # Create Flask app and apply config
    app = Flask(__name__)
    app_config = config or AppConfig.from_env()
    app.config.from_object(app_config)
    app.config["BASE_DIR"] = app_config.BASE_DIR
    app.config.setdefault('APP_BASE_PATH', app_config.BASE_DIR)
    app.config.setdefault('IS_INITIALIZED', False)
    app.config.setdefault('LAST_CLEANUP_TIME', 0)

    # Initialize logging
    initialize_logging(app)
    app_logger = create_logger_for_component('app')
    
    # Check if we're in Flask reloader process
    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    
    # Process identification
    process_type = "reloader process" if is_reloader_process else "parent process"
    app_logger.info(f"Starting application setup ({process_type})")
    
    # Configure JSON encoder
    app.json_encoder = CustomJSONEncoder

    # Set up base paths
    base_path = app_config.BASE_DIR.parent
    app_logger.info(f"Application base directory: {app_config.BASE_DIR}")
    app_logger.info(f"Parent base path: {base_path}")

    # Use a thread-safe approach to initialization
    with INIT_LOCK:
        # Initialize components - prevent double initialization between processes
        is_initialized = app.config.get('IS_INITIALIZED', False)
        should_initialize = (
            (is_reloader_process and app_config.DEBUG) or 
            (not app_config.DEBUG and not is_initialized)
        )
        
        if should_initialize:
            app_logger.info("Initializing components and services")
            try:
                initialize_analyzers(app, base_path, app_config.BASE_DIR)
                initialize_services(app, app_logger)
                app.config['IS_INITIALIZED'] = True
            except Exception as e:
                app_logger.exception(f"Error during initialization: {e}")
                raise RuntimeError(f"Failed to initialize application: {e}") from e
        else:
            app_logger.info(f"Skipping initialization ({process_type}, initialized={is_initialized})")
            # Ensure placeholder values are set to avoid attribute errors
            if not is_initialized:
                app.config["docker_manager"] = None
                app.scan_manager = None
                app.config["ZAP_SCANS"] = {}

    # Apply proxy fix middleware
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Register blueprints, error handlers, and request hooks
    register_blueprints(app)
    register_error_handlers(app)
    register_request_hooks(app)

    app_logger.info("Application initialization complete")
    return app


if __name__ == "__main__":
    # Setup startup logger
    main_logger = logging.getLogger('main')
    main_logger.setLevel(logging.INFO)
    
    if not main_logger.hasHandlers():
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
        main_logger.addHandler(handler)

    # Process identification
    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    process_type = "reloader process" if is_reloader_process else "parent process"
    main_logger.info(f"Application starting via __main__ ({process_type})")

    # Load configuration
    config = AppConfig.from_env()

    # Validate critical configuration
    if config.HOST is None:
        config.HOST = "127.0.0.1"
        main_logger.warning(f"HOST configuration is None, using default: {config.HOST}")
    
    if config.PORT is None:
        config.PORT = 5000
        main_logger.warning(f"PORT configuration is None, using default: {config.PORT}")

    try:
        # Create and initialize the application
        main_logger.info(f"Creating application with LOG_LEVEL={config.LOG_LEVEL}")
        app = create_app(config)

        # Health checks and info display only in appropriate process
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

        # Start Flask server
        main_logger.info(f"Starting Flask server on {config.HOST}:{config.PORT} (debug={config.DEBUG})")
        app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)

    except Exception as e:
        main_logger.critical(f"FATAL: Failed to start application: {e}", exc_info=True)
        import sys
        sys.exit(1)