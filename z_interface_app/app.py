"""
Flask application factory and entry point for the AI Model Management System.

This module provides the main application factory pattern for creating
and configuring the Flask application with all necessary components.
It handles application setup, error handling, request hooks, and
service initialization.
"""

import logging
import os
import random
import http  # Using HTTPStatus enum
from pathlib import Path
from typing import Optional

from flask import Flask, request, render_template, jsonify
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

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

    Provides appropriate responses based on request type (AJAX vs standard)
    and logs error details.

    Args:
        app: Flask application instance
    """
    error_logger = create_logger_for_component('errors')

    def _handle_error_response(
        error_code: int,
        error_name: str,
        error_message: str,
        original_error: Optional[Exception] = None
    ):
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

        template_name = f"{error_code}.html"
        template_exists = False
        try:
            app.jinja_env.get_template(template_name)
            template_exists = True
        except Exception: # Catches TemplateNotFound, etc.
             template_exists = False

        # Use specific template if it exists, otherwise fallback logic
        if not template_exists:
             if error_code == http.HTTPStatus.NOT_FOUND:
                 # Log critical if even 404.html is missing
                 error_logger.critical(f"Error template '{template_name}' not found!")
                 basic_response = f"<h1>Error {error_code}</h1><p>{error_name}: {error_message}</p>"
                 return basic_response, error_code
             elif error_code >= http.HTTPStatus.INTERNAL_SERVER_ERROR:
                 # For server errors, try 500.html as a generic fallback
                 template_name = "500.html"
                 try:
                     app.jinja_env.get_template(template_name)
                     template_exists = True
                 except Exception:
                     error_logger.critical(f"Fallback error template '{template_name}' not found!")
                     basic_response = f"<h1>Error {error_code}</h1><p>{error_name}: {error_message}</p>"
                     return basic_response, error_code
             else:
                 # For other client errors without specific templates
                 error_logger.warning(f"Error template '{template_name}' not found, providing basic response.")
                 basic_response = f"<h1>Error {error_code}</h1><p>{error_name}: {error_message}</p>"
                 return basic_response, error_code

        return render_template(template_name, error=original_error or error_message), error_code

    @app.errorhandler(http.HTTPStatus.NOT_FOUND)
    def not_found(error: HTTPException):
        """Handle 404 Not Found errors."""
        error_logger.warning(f"404 error: {request.path} - {error.description}")
        return _handle_error_response(
            http.HTTPStatus.NOT_FOUND,
            error.name,
            error.description,
            error
        )

    @app.errorhandler(http.HTTPStatus.INTERNAL_SERVER_ERROR)
    def server_error(error: HTTPException):
        """Handle 500 Internal Server errors."""
        error_logger.error(f"500 error: {request.path} - {error}", exc_info=True)
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

        Logs the full stack trace and returns an appropriate HTTP response,
        defaulting to 500 Internal Server Error.
        """
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
        # Perform occasional cleanup based on probability
        if random.random() < _OCCASIONAL_CLEANUP_PROBABILITY:
            hooks_logger.debug(
                "Running occasional cleanup tasks (prob: %s)",
                _OCCASIONAL_CLEANUP_PROBABILITY
            )
            try:
                if docker_manager:
                    docker_manager.cleanup_containers()
                if "ZAP_SCANS" in app.config:
                    stop_zap_scanners(app.config["ZAP_SCANS"])
            except Exception as e:
                hooks_logger.exception(f"Error during cleanup tasks: {e}")

    @app.after_request
    def after(response):
        """Process the response before returning it to the client."""
        # Add common security headers
        response.headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        })

        # Disable caching for AJAX requests
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

        # Ensure ZAP scans associated with the context are stopped
        if "ZAP_SCANS" in app.config:
            hooks_logger.debug("Stopping active ZAP scans during teardown")
            stop_zap_scanners(app.config["ZAP_SCANS"])


# =============================================================================
# Flask App Factory
# =============================================================================
def create_app(config: Optional[AppConfig] = None) -> Flask:
    """
    Create and configure the Flask application instance.

    Initializes configuration, logging, middleware, services, blueprints,
    error handlers, and request hooks.

    Args:
        config: Optional configuration object. Loaded from env vars if None.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)

    app_config = config or AppConfig.from_env()
    app.config.from_object(app_config)
    # Ensure BASE_DIR is explicitly available in Flask config if needed elsewhere
    app.config["BASE_DIR"] = app_config.BASE_DIR

    initialize_logging(app)
    app_logger = create_logger_for_component('app')
    app_logger.info("Starting application setup")

    app.json_encoder = CustomJSONEncoder

    base_path = app_config.BASE_DIR.parent
    app_logger.info(f"Application base directory: {app_config.BASE_DIR}")
    app_logger.info(f"Parent base path: {base_path}")

    app_logger.info("Initializing service components and analyzers")
    app.backend_security_analyzer = BackendSecurityAnalyzer(base_path)
    app.frontend_security_analyzer = FrontendSecurityAnalyzer(base_path)
    app.gpt4all_analyzer = GPT4AllAnalyzer(app_config.BASE_DIR)
    app.performance_tester = LocustPerformanceTester(base_path)
    app.zap_scanner = create_scanner(app_config.BASE_DIR)
    app.config["ZAP_SCANS"] = {} # Store active ZAP scan processes

    docker_manager = DockerManager()
    app.config["docker_manager"] = docker_manager

    # Apply proxy fix middleware if running behind a reverse proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    app_logger.info("Registering application blueprints")
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(analysis_bp) # Assumes prefix defined within blueprint or root
    app.register_blueprint(performance_bp, url_prefix="/performance")
    app.register_blueprint(gpt4all_bp, url_prefix="/gpt4all")
    app.register_blueprint(zap_bp, url_prefix="/zap")

    app_logger.info("Initializing batch analysis module")
    init_batch_analysis(app)
    app.register_blueprint(batch_analysis_bp, url_prefix="/batch-analysis")

    app_logger.info("Registering error handlers and request hooks")
    register_error_handlers(app)
    register_request_hooks(app, docker_manager)

    app_logger.info("Application initialization complete")
    return app


# =============================================================================
# Main Entry Point
# =============================================================================
if __name__ == "__main__":
    # Standalone logger for startup messages before app context is available
    main_logger = logging.getLogger('main')
    main_logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    handler.setFormatter(logging.Formatter(log_format))
    if not main_logger.hasHandlers(): # Avoid duplicate handlers if root is configured
        main_logger.addHandler(handler)

    main_logger.info("Application starting via __main__ execution")

    config = AppConfig.from_env()

    try:
        main_logger.info(
            f"Creating application with LOG_LEVEL={config.LOG_LEVEL}"
        )
        app = create_app(config)

        # Perform post-initialization checks within app context
        with app.app_context():
            main_logger.info("Performing post-initialization health checks...")
            docker_manager = app.config.get("docker_manager")
            system_health = False

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

        # Display access information
        host_display = "localhost" if config.HOST in ["0.0.0.0", "127.0.0.1"] else config.HOST
        main_logger.info(f"\n{'='*50}")
        main_logger.info(f"AI Model Management System is ready!")
        main_logger.info(f"Access the application at: http://{host_display}:{config.PORT}/")
        main_logger.info(f"Available endpoints:")
        main_logger.info(f" • Dashboard:         http://{host_display}:{config.PORT}/")
        main_logger.info(f" • API:               http://{host_display}:{config.PORT}/api")
        main_logger.info(f" • Security Analysis: http://{host_display}:{config.PORT}/analysis")
        main_logger.info(f" • Performance Test:  http://{host_display}:{config.PORT}/performance")
        main_logger.info(f" • GPT4All Analysis:  http://{host_display}:{config.PORT}/gpt4all")
        main_logger.info(f" • Security Scanner:  http://{host_display}:{config.PORT}/zap")
        main_logger.info(f" • Batch Analysis:    http://{host_display}:{config.PORT}/batch-analysis")
        main_logger.info(f"{'='*50}\n")

        main_logger.info(
            f"Starting Flask server on {config.HOST}:{config.PORT} "
            f"(debug={config.DEBUG})"
        )
        # Note: app.run() is suitable for development.
        # For production, use a WSGI server like Gunicorn or uWSGI.
        app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)

    except Exception as e:
        main_logger.critical(f"FATAL: Failed to start application: {e}", exc_info=True)
        import sys
        sys.exit(1) # Indicate failure