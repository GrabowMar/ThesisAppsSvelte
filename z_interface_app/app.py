"""
Flask application factory and entry point for the AI Model Management System.

This module provides the main application factory pattern for creating
and configuring the Flask application with all necessary components.
It handles application setup, error handling, request hooks, and
service initialization.
"""

# =============================================================================
# Standard Library Imports
# =============================================================================
import logging
import os
import random
import http  # Added for HTTPStatus enum
from pathlib import Path
from typing import Optional

# =============================================================================
# Third-Party Imports
# =============================================================================
from flask import Flask, request, render_template, jsonify
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

# =============================================================================
# Custom Module Imports
# =============================================================================
from batch_analysis import init_batch_analysis, batch_analysis_bp
from backend_security_analysis import BackendSecurityAnalyzer
from frontend_security_analysis import FrontendSecurityAnalyzer
from gpt4all_analysis import GPT4AllAnalyzer
from logging_service import initialize_logging, create_logger_for_component
from performance_analysis import LocustPerformanceTester
from zap_scanner import create_scanner

from services import DockerManager, SystemHealthMonitor
from utils import AppConfig, CustomJSONEncoder, stop_zap_scanners
from routes import (
    main_bp, api_bp, analysis_bp, performance_bp,
    gpt4all_bp, zap_bp
)

# =============================================================================
# Constants
# =============================================================================
_OCCASIONAL_CLEANUP_PROBABILITY = 0.01  # Probability for running cleanup tasks
_AJAX_REQUEST_HEADER = "XMLHttpRequest"  # Standard header value for AJAX requests

# =============================================================================
# Error Handlers
# =============================================================================
def register_error_handlers(app: Flask) -> None:
    """
    Register Flask error handlers for various HTTP status codes.

    These handlers provide appropriate responses based on request type
    (AJAX vs standard) and log error details for troubleshooting.

    Args:
        app: Flask application instance
    """
    error_logger = create_logger_for_component('errors')

    def _handle_error_response(error_code: int, error_name: str, error_message: str, original_error: Optional[Exception] = None):
        """
        Generate appropriate error response (JSON for AJAX, HTML otherwise).

        Args:
            error_code: The HTTP status code.
            error_name: A short name for the error (e.g., "Not Found").
            error_message: A descriptive message for the error.
            original_error: The original exception object, if available.

        Returns:
            A Flask Response object tuple (response, status_code).
        """
        if request.headers.get("X-Requested-With") == _AJAX_REQUEST_HEADER:
            return jsonify({
                "success": False,
                "error": error_name,
                "message": error_message
            }), error_code

        # Determine template name, default to 500.html for non-404 server errors
        template_name = f"{error_code}.html"
        if error_code != http.HTTPStatus.NOT_FOUND and error_code >= 500:
             # Check if specific template exists, otherwise use generic one
             if not app.jinja_env.get_template(template_name):
                 template_name = "500.html" # Fallback template
        elif not app.jinja_env.get_template(template_name):
            # If even 404.html is missing, use a very basic response or log critical error
            error_logger.critical(f"Error template '{template_name}' not found!")
            return f"<h1>Error {error_code}</h1><p>{error_name}: {error_message}</p>", error_code


        return render_template(template_name, error=original_error or error_message), error_code

    @app.errorhandler(http.HTTPStatus.NOT_FOUND)
    def not_found(error: HTTPException):
        """Handle 404 Not Found errors."""
        error_logger.warning(f"404 error: {request.path} - {error.description}")
        return _handle_error_response(
            http.HTTPStatus.NOT_FOUND,
            error.name, # Use Werkzeug's error name
            error.description, # Use Werkzeug's error description
            error
        )

    @app.errorhandler(http.HTTPStatus.INTERNAL_SERVER_ERROR)
    def server_error(error: HTTPException):
        """Handle 500 Internal Server errors."""
        # Log with exception info for server errors
        error_logger.error(f"500 error: {request.path} - {error}", exc_info=True)
        # Use Werkzeug's error details if available, otherwise generic
        error_name = getattr(error, 'name', 'Internal Server Error')
        error_description = getattr(error, 'description', str(error))
        return _handle_error_response(
            http.HTTPStatus.INTERNAL_SERVER_ERROR,
            error_name,
            error_description,
            error
        )

    @app.errorhandler(Exception)
    def handle_exception(error: Exception):
        """
        Handle any unhandled exceptions (catch-all).

        Logs the full stack trace and attempts to return an appropriate
        HTTP response, defaulting to 500 Internal Server Error.
        """
        error_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
        error_name = "Internal Server Error"
        error_description = str(error)

        # If it's an HTTPException, use its code and details
        if isinstance(error, HTTPException):
            error_code = error.code or http.HTTPStatus.INTERNAL_SERVER_ERROR
            error_name = error.name or "HTTP Error"
            error_description = error.description or str(error)

        error_logger.exception(
            f"Unhandled exception ({error_code} - {error_name}): {request.path} - {error}"
        )
        return _handle_error_response(
            error_code,
            error_name,
            error_description,
            error
        )


# =============================================================================
# Request Hooks
# =============================================================================
def register_request_hooks(app: Flask, docker_manager: DockerManager) -> None:
    """
    Register Flask request hooks for preprocessing and response handling.

    Args:
        app: Flask application instance
        docker_manager: Docker manager service for container management
    """
    hooks_logger = create_logger_for_component('hooks')

    @app.before_request
    def before():
        """Execute actions before processing each request."""
        # Perform occasional cleanup (using defined probability)
        if random.random() < _OCCASIONAL_CLEANUP_PROBABILITY:
            hooks_logger.debug(
                "Running occasional cleanup tasks (prob: %s)",
                _OCCASIONAL_CLEANUP_PROBABILITY
            )
            try:
                if docker_manager: # Ensure manager exists
                    docker_manager.cleanup_containers()
                # Stop any lingering ZAP scanners
                if "ZAP_SCANS" in app.config:
                    stop_zap_scanners(app.config["ZAP_SCANS"])
            except Exception as e:
                hooks_logger.exception(f"Error during cleanup tasks: {e}")

    @app.after_request
    def after(response):
        """Process the response before returning it to the client."""
        # Add security headers
        response.headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        })

        # Disable caching for AJAX requests (using defined header value)
        if request.headers.get("X-Requested-With") == _AJAX_REQUEST_HEADER:
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response

    @app.teardown_appcontext
    def teardown(exception=None):
        """Clean up resources when the request context is torn down."""
        if exception:
            hooks_logger.warning(
                f"Context teardown with exception: {exception}"
            )

        # Ensure ZAP scans are stopped
        if "ZAP_SCANS" in app.config:
            hooks_logger.debug("Stopping active ZAP scans during teardown")
            stop_zap_scanners(app.config["ZAP_SCANS"])


# =============================================================================
# Flask App Factory
# =============================================================================
def create_app(config: Optional[AppConfig] = None) -> Flask:
    """
    Create and configure the Flask application.

    Initializes the Flask app with configuration, logging, middleware,
    services, blueprints, error handlers, and request hooks.

    Args:
        config: Optional configuration object. Loaded from env vars if None.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)

    # Load configuration
    app_config = config or AppConfig.from_env()
    app.config.from_object(app_config)
    app.config["BASE_DIR"] = app_config.BASE_DIR # Ensure BASE_DIR is in config

    # Initialize logging first
    initialize_logging(app)
    app_logger = create_logger_for_component('app')
    app_logger.info("Starting application setup")

    # Configure custom JSON encoder
    app.json_encoder = CustomJSONEncoder

    # Log base path information
    base_path = app_config.BASE_DIR.parent
    app_logger.info(f"Application base path: {app_config.BASE_DIR}")
    app_logger.info(f"Parent base path: {base_path}")

    # Initialize analyzers and service components
    app_logger.info("Initializing security analyzers")
    app.backend_security_analyzer = BackendSecurityAnalyzer(base_path)
    app.frontend_security_analyzer = FrontendSecurityAnalyzer(base_path)

    app_logger.info("Initializing GPT4All analyzer")
    app.gpt4all_analyzer = GPT4AllAnalyzer(app_config.BASE_DIR)

    app_logger.info("Initializing performance tester")
    app.performance_tester = LocustPerformanceTester(base_path)

    app_logger.info("Initializing ZAP scanner")
    app.zap_scanner = create_scanner(app_config.BASE_DIR)
    app.config["ZAP_SCANS"] = {} # Initialize ZAP scans dictionary

    # Create and attach Docker manager
    app_logger.info("Creating Docker manager")
    docker_manager = DockerManager()
    app.config["docker_manager"] = docker_manager # Store instance in app config

    # Configure proxy fix middleware (if behind a proxy)
    app_logger.info("Configuring proxy fix middleware")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Register route blueprints
    app_logger.info("Registering application blueprints")
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(analysis_bp) # Assuming root prefix or defined inside
    app.register_blueprint(performance_bp, url_prefix="/performance")
    app.register_blueprint(gpt4all_bp, url_prefix="/gpt4all")
    app.register_blueprint(zap_bp, url_prefix="/zap")

    # Initialize batch analysis module
    app_logger.info("Initializing batch analysis module")
    init_batch_analysis(app)
    app.register_blueprint(batch_analysis_bp, url_prefix="/batch-analysis")

    # Register error handlers and request hooks
    app_logger.info("Registering error handlers and request hooks")
    register_error_handlers(app)
    # Pass the docker_manager instance created above
    register_request_hooks(app, docker_manager)

    app_logger.info("Application initialization complete")
    return app


# =============================================================================
# Main Entry Point
# =============================================================================
if __name__ == "__main__":
    # Create standalone logger for startup messages
    main_logger = logging.getLogger('main')
    main_logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    handler.setFormatter(logging.Formatter(log_format))
    # Prevent duplicate logging if root logger is configured
    if not main_logger.hasHandlers():
        main_logger.addHandler(handler)

    main_logger.info("Application starting via __main__")

    # Load configuration from environment variables
    config = AppConfig.from_env()

    try:
        main_logger.info(
            f"Creating application with LOG_LEVEL={config.LOG_LEVEL}"
        )
        app = create_app(config)

        # Perform system health checks within app context after app creation
        with app.app_context():
            main_logger.info("Performing post-initialization health checks...")
            # Access the manager created and stored by create_app
            docker_manager = app.config.get("docker_manager")
            system_health = False # Default to false

            if docker_manager and docker_manager.client:
                main_logger.info("Checking system health via Docker manager...")
                try:
                     system_health = SystemHealthMonitor.check_health(
                         docker_manager.client
                     )
                     if system_health:
                         main_logger.info("System health check passed.")
                     else:
                         main_logger.warning(
                             "System health check failed - "
                             "reduced functionality expected."
                         )
                except Exception as health_check_exc:
                    main_logger.error(
                        f"Error during system health check: {health_check_exc}",
                        exc_info=True
                    )
            else:
                main_logger.warning(
                    "Docker client unavailable or manager not initialized - "
                    "cannot perform health check; reduced functionality expected."
                )

        # Start the Flask development server
        main_logger.info(
            f"Starting Flask server on {config.HOST}:{config.PORT} "
            f"(debug={config.DEBUG})"
        )
        # Note: app.run() is suitable for development.
        # For production, use a WSGI server like Gunicorn or uWSGI.
        app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)

    except Exception as e:
        # Log critical failure during startup
        main_logger.critical(f"Failed to start application: {e}", exc_info=True)
        # Optionally exit for critical startup failures
        import sys
        sys.exit(1) # Exit with a non-zero code to indicate failure