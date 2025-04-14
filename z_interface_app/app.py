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
    
    @app.errorhandler(404)
    def not_found(error):
        """
        Handle 404 Not Found errors.
        
        Args:
            error: The exception raised
            
        Returns:
            JSON response for AJAX requests, HTML template otherwise
        """
        error_logger.warning(f"404 error: {request.path} - {error}")
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({
                "success": False,
                "error": "Not found",
                "message": str(error)
            }), 404
        return render_template("404.html", error=error), 404

    @app.errorhandler(500)
    def server_error(error):
        """
        Handle 500 Internal Server errors.
        
        Args:
            error: The exception raised
            
        Returns:
            JSON response for AJAX requests, HTML template otherwise
        """
        error_logger.error(f"500 error: {request.path} - {error}")
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({
                "success": False,
                "error": "Internal server error",
                "message": str(error)
            }), 500
        return render_template("500.html", error=error), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        """
        Handle any unhandled exceptions.
        
        This is a catch-all handler for exceptions not covered by specific
        error handlers. It logs the full stack trace for debugging.
        
        Args:
            error: The exception raised
            
        Returns:
            JSON response for AJAX requests, HTML template otherwise
        """
        error_logger.exception(f"Unhandled exception: {request.path} - {error}")
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({
                "success": False,
                "error": str(error),
            }), 500
        return render_template("500.html", error=error), 500


# =============================================================================
# Request Hooks
# =============================================================================
def register_request_hooks(app: Flask, docker_manager: DockerManager) -> None:
    """
    Register Flask request hooks for request preprocessing and response handling.
    
    Hooks include:
    - before_request: Occasional cleanup of resources
    - after_request: Adding security headers and cache control
    - teardown_appcontext: Resource cleanup on request completion
    
    Args:
        app: Flask application instance
        docker_manager: Docker manager service for container management
    """
    hooks_logger = create_logger_for_component('hooks')
    
    @app.before_request
    def before():
        """
        Execute actions before processing each request.
        
        Performs occasional cleanup tasks (1% probability per request) such as
        removing stale Docker containers and stopping inactive ZAP scans.
        """
        # Perform occasional cleanup (1% probability)
        if random.random() < 0.01:
            hooks_logger.debug("Running occasional cleanup tasks")
            try:
                docker_manager.cleanup_containers()
                # Stop any lingering ZAP scanners
                if "ZAP_SCANS" in app.config:
                    stop_zap_scanners(app.config["ZAP_SCANS"])
            except Exception as e:
                hooks_logger.exception(f"Error during cleanup tasks: {e}")

    @app.after_request
    def after(response):
        """
        Process the response before returning it to the client.
        
        Adds security headers to all responses and configures caching
        for AJAX requests.
        
        Args:
            response: Flask response object
            
        Returns:
            Modified response with security headers
        """
        # Add security headers to all responses
        response.headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        })
        
        # Disable caching for AJAX requests
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            
        return response

    @app.teardown_appcontext
    def teardown(exception=None):
        """
        Clean up resources when the request context is torn down.
        
        Stops active ZAP scans on context teardown to prevent resource leaks.
        
        Args:
            exception: Optional exception that caused the teardown
        """
        if exception:
            hooks_logger.warning(
                f"Context teardown with exception: {exception}"
            )
            
        if "ZAP_SCANS" in app.config:
            hooks_logger.debug("Stopping active ZAP scans during teardown")
            stop_zap_scanners(app.config["ZAP_SCANS"])


# =============================================================================
# Flask App Factory
# =============================================================================
def create_app(config: Optional[AppConfig] = None) -> Flask:
    """
    Create and configure the Flask application with all necessary components.
    
    This factory function initializes the Flask app with configuration,
    middleware, blueprints, security analyzers, and service components.
    
    Args:
        config: Optional configuration object. If not provided, will be loaded
               from environment variables.
        
    Returns:
        Configured Flask application ready to run
    """
    # Create Flask app instance
    app = Flask(__name__)
    
    # Load configuration
    app_config = config or AppConfig.from_env()
    app.config.from_object(app_config)
    app.config["BASE_DIR"] = app_config.BASE_DIR
    
    # Initialize enhanced logging system
    initialize_logging(app)
    app_logger = create_logger_for_component('app')
    app_logger.info("Starting application setup")
    
    # Configure custom JSON encoder for improved serialization
    app.json_encoder = CustomJSONEncoder
    
    # Log base path information for diagnostics
    base_path = app_config.BASE_DIR.parent
    app_logger.info(f"Application base path: {app_config.BASE_DIR}")
    app_logger.info(f"Parent base path: {base_path}")

    # Initialize analyzers and service components
    app_logger.info("Initializing security analyzers")
    app.backend_security_analyzer = BackendSecurityAnalyzer(base_path)
    app.frontend_security_analyzer = FrontendSecurityAnalyzer(base_path)
    
    app_logger.info("Initializing GPT4All analyzer")
    app.gpt4all_analyzer = GPT4AllAnalyzer(base_path)
    
    app_logger.info("Initializing performance tester")
    app.performance_tester = LocustPerformanceTester(base_path)
    
    app_logger.info("Initializing ZAP scanner")
    app.zap_scanner = create_scanner(app_config.BASE_DIR)

    # Create and attach Docker manager
    app_logger.info("Creating Docker manager")
    docker_manager = DockerManager()
    app.config["docker_manager"] = docker_manager

    # Configure proxy fix middleware to handle requests behind proxies
    app_logger.info("Configuring proxy fix middleware")
    app.wsgi_app = ProxyFix(app.wsgi_app)

    # Register route blueprints
    app_logger.info("Registering application blueprints")
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(analysis_bp)
    app.register_blueprint(performance_bp, url_prefix="/performance")
    app.register_blueprint(gpt4all_bp)
    app.register_blueprint(zap_bp, url_prefix="/zap")

    # Initialize batch analysis module
    app_logger.info("Initializing batch analysis module")
    init_batch_analysis(app)
    app.register_blueprint(batch_analysis_bp, url_prefix="/batch-analysis")

    # Register error handlers and request hooks
    app_logger.info("Registering error handlers and request hooks")
    register_error_handlers(app)
    register_request_hooks(app, docker_manager)
    
    app_logger.info("Application initialization complete")
    return app


# =============================================================================
# Main Entry Point
# =============================================================================
if __name__ == "__main__":
    # Create standalone logger for main script
    # (doesn't depend on Flask request context)
    main_logger = logging.getLogger('main')
    main_logger.setLevel(logging.INFO)
    
    # Configure console handler for main logger
    handler = logging.StreamHandler()
    log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    handler.setFormatter(logging.Formatter(log_format))
    main_logger.addHandler(handler)
    
    main_logger.info("Application starting")
    
    # Load configuration from environment variables
    config = AppConfig.from_env()
    
    try:
        main_logger.info(
            f"Creating application with LOG_LEVEL={config.LOG_LEVEL}"
        )
        app = create_app(config)
        
        # Perform system health checks within app context
        with app.app_context():
            docker_manager = DockerManager()
            system_health = True
            
            if docker_manager.client:
                system_health = SystemHealthMonitor.check_health(
                    docker_manager.client
                )
                if not system_health:
                    main_logger.warning(
                        "System health check failed - "
                        "reduced functionality expected"
                    )
            else:
                main_logger.warning(
                    "Docker client unavailable - "
                    "reduced functionality expected"
                )
        
        # Start the Flask development server
        main_logger.info(
            f"Starting Flask server on {config.HOST}:{config.PORT} "
            f"(debug={config.DEBUG})"
        )
        app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
    except Exception as e:
        main_logger.critical(f"Failed to start application: {e}", exc_info=True)
        raise e