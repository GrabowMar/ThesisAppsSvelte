"""
Enhanced Logging Service for AI Model Management System

This module provides a comprehensive logging system with:
- Structured logs with contextual information
- Separate log files for different types of logs
- Log rotation to prevent excessive disk usage
- Noise reduction for high-frequency endpoints
- Console coloring for development environments
- Component-specific logging levels

Usage:
    from logging_service import initialize_logging, create_logger_for_component
    
    # In app initialization
    initialize_logging(app)
    
    # In any module
    logger = create_logger_for_component('docker')
    logger.info('Container started successfully')
"""

import logging
import logging.handlers
import os
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Set, Union
from flask import Flask, g, request, current_app
from werkzeug.exceptions import HTTPException
import coloredlogs

# Try to import APIResponse, fall back to a simple implementation if not available
try:
    from app_models import APIResponse
except ImportError:
    class APIResponse:
        """Simple fallback implementation of APIResponse."""
        def __init__(self, success=True, message="", error="", data=None, code=200):
            self.success = success
            self.message = message
            self.error = error
            self.data = data or {}
            self.code = code
            
        def to_response(self):
            """Convert to Flask response with appropriate status code."""
            from flask import jsonify
            response_data = {
                "success": self.success,
                "message": self.message,
            }
            
            if self.data is not None:
                response_data["data"] = self.data
                
            if self.error is not None:
                response_data["error"] = self.error
                
            return jsonify(response_data), self.code


class LogConfig:
    """Centralized logging configuration with sensible defaults."""
    
    # Log levels by name
    LEVELS = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    # Default formats
    CONSOLE_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    FILE_FORMAT = "%(asctime)s [%(levelname)s] [%(threadName)s] %(name)s: %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    # Default log directories and files
    DEFAULT_LOG_DIR = "logs"
    REQUEST_LOG = "requests.log"
    ERROR_LOG = "errors.log"
    APP_LOG = "app.log"
    
    # Size-based rotation (10MB)
    MAX_BYTES = 10 * 1024 * 1024
    BACKUP_COUNT = 5
    
    @classmethod
    def get_level(cls, level_name: str) -> int:
        """Convert level name to level value with fallback to INFO."""
        return cls.LEVELS.get(level_name.upper(), logging.INFO)


class ContextFilter(logging.Filter):
    """Add contextual information to log records."""
    
    def __init__(self, app_name: str = "app"):
        super().__init__()
        self.app_name = app_name
    
    def filter(self, record):
        # Safely handle access to Flask's g object
        try:
            from flask import g, has_request_context, has_app_context
            if has_app_context() and has_request_context():
                # Only access g when we're in a Flask request context
                record.request_id = getattr(g, 'request_id', '-')
            else:
                record.request_id = '-'
        except (RuntimeError, ImportError):
            # Not in Flask context or Flask not available
            record.request_id = '-'
                
        # Add component information if not present
        if not hasattr(record, 'component'):
            # Extract component from logger name
            if record.name.find('.') > 0:
                record.component = record.name.split('.')[0]
            else:
                record.component = self.app_name
                
        return True


class RequestFilter(logging.Filter):
    """Filter for reducing noise from frequent requests."""
    
    def __init__(self, excluded_paths: Optional[Set[str]] = None):
        super().__init__()
        # Paths to exclude from regular logging
        self.excluded_paths = excluded_paths or {
            '/api/container/', 
            '/api/status',
            '/api/system-info',
            '/static/'
        }
        # Only log these excluded paths if they result in errors
        self.log_excluded_on_error = True
        
    def filter(self, record):
        # Check if it's a request log
        if not hasattr(record, 'args') or not isinstance(record.args, tuple) or len(record.args) < 3:
            return True
            
        # Extract request info from werkzeug log format
        msg = record.args[2] if isinstance(record.args[2], str) else ""
        
        # Check if this is a common path we want to filter
        for path in self.excluded_paths:
            if path in msg:
                # For successful requests (200, 304), filter them out
                if ' 200 ' in msg or ' 304 ' in msg:
                    return False
                # For error responses, let them through if configured to do so
                elif self.log_excluded_on_error:
                    return True
                else:
                    return False
                    
        return True


class LoggingService:
    """Enhanced logging service with multiple handlers and filters."""
    
    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        self.log_dir = Path(LogConfig.DEFAULT_LOG_DIR)
        self.handlers = {}
        
        # Create logger once the app is available
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize logging with application context."""
        self.app = app
        
        # Get configuration from app or environment
        log_level = app.config.get('LOG_LEVEL', os.environ.get('LOG_LEVEL', 'INFO'))
        self.log_dir = Path(app.config.get('LOG_DIR', os.environ.get('LOG_DIR', LogConfig.DEFAULT_LOG_DIR)))
        
        # Create log directory if it doesn't exist
        self.log_dir.mkdir(exist_ok=True, parents=True)
        
        # Configure root logger
        self._configure_root_logger(LogConfig.get_level(log_level))
        
        # Configure specialized loggers
        self._configure_request_logger()
        self._configure_error_logger()
        self._configure_component_loggers()
        
        # Add colorized logs for console if not in production
        if app.debug or os.environ.get('FLASK_ENV') != 'production':
            self._configure_colored_console_logs()
        
        # Add context filter to all loggers
        context_filter = ContextFilter(app_name=app.name)
        for logger in [logging.getLogger(), 
                      logging.getLogger('werkzeug'),
                      logging.getLogger('requests'),
                      logging.getLogger('errors')]:
            logger.addFilter(context_filter)
        
        app.logger.info(f"Logging initialized at level {log_level} to {self.log_dir}")
    
    def _configure_root_logger(self, level: int):
        """Configure the root logger with app-wide log file."""
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # Create formatter for file logging
        file_formatter = logging.Formatter(
            fmt=LogConfig.FILE_FORMAT,
            datefmt=LogConfig.DATE_FORMAT
        )
        
        # App-wide rotating log file
        app_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / LogConfig.APP_LOG,
            maxBytes=LogConfig.MAX_BYTES,
            backupCount=LogConfig.BACKUP_COUNT
        )
        app_handler.setFormatter(file_formatter)
        app_handler.setLevel(level)
        
        # Store handler for later reference
        self.handlers['app'] = app_handler
        
        # Add handler to root logger
        root_logger.addHandler(app_handler)
    
    def _configure_request_logger(self):
        """Configure logger specifically for HTTP requests."""
        request_logger = logging.getLogger('requests')
        request_logger.propagate = False  # Don't send to root logger
        
        # Create formatter for request logs
        request_formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(request_id)s] %(message)s",
            datefmt=LogConfig.DATE_FORMAT
        )
        
        # Request log file with rotation
        request_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / LogConfig.REQUEST_LOG,
            maxBytes=LogConfig.MAX_BYTES,
            backupCount=LogConfig.BACKUP_COUNT
        )
        request_handler.setFormatter(request_formatter)
        
        # Add request filter to reduce noise
        request_filter = RequestFilter()
        request_handler.addFilter(request_filter)
        
        # Store handler for later reference
        self.handlers['requests'] = request_handler
        
        # Add handler to request logger
        request_logger.addHandler(request_handler)
        
        # Also filter werkzeug logger
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.addFilter(request_filter)
    
    def _configure_error_logger(self):
        """Configure logger specifically for errors."""
        error_logger = logging.getLogger('errors')
        error_logger.setLevel(logging.ERROR)
        error_logger.propagate = False  # Don't send to root logger
        
        # Create formatter for error logs
        error_formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(request_id)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s",
            datefmt=LogConfig.DATE_FORMAT
        )
        
        # Error log file with rotation
        error_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / LogConfig.ERROR_LOG,
            maxBytes=LogConfig.MAX_BYTES,
            backupCount=LogConfig.BACKUP_COUNT
        )
        error_handler.setFormatter(error_formatter)
        error_handler.setLevel(logging.ERROR)
        
        # Store handler for later reference
        self.handlers['errors'] = error_handler
        
        # Add handler to error logger
        error_logger.addHandler(error_handler)
        
        # Also send errors from root logger to error log
        logging.getLogger().addHandler(error_handler)
    
    def _configure_component_loggers(self):
        """Configure specialized loggers for different components."""
        # Set specific log levels for various components
        component_levels = {
            "zap_scanner": logging.INFO,
            "owasp_zap": logging.WARNING,
            "docker": logging.INFO,
            "performance": logging.INFO,
            "security": logging.INFO,
            "gpt4all": logging.INFO,
            "batch_analysis": logging.INFO
        }
        
        for component, level in component_levels.items():
            component_logger = logging.getLogger(component)
            component_logger.setLevel(level)
    
    def _configure_colored_console_logs(self):
        """Add colored logging to console for development."""
        # Configure colored logs for console
        coloredlogs.install(
            level=logging.INFO,
            fmt=LogConfig.CONSOLE_FORMAT,
            datefmt=LogConfig.DATE_FORMAT,
            level_styles={
                'debug': {'color': 'blue'},
                'info': {'color': 'green'},
                'warning': {'color': 'yellow', 'bold': True},
                'error': {'color': 'red', 'bold': True},
                'critical': {'color': 'red', 'bold': True, 'background': 'white'}
            },
            field_styles={
                'asctime': {'color': 'green'},
                'levelname': {'color': 'cyan', 'bold': True},
                'name': {'color': 'magenta'}
            }
        )
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger with the given name, configured with our settings."""
        return logging.getLogger(name)


class EnhancedRequestLoggerMiddleware:
    """
    Enhanced middleware to track and log request information.
    Separates logs by endpoint type and adds structured information.
    """
    
    # Endpoints that shouldn't be logged extensively
    QUIET_ENDPOINTS = {
        'static_file': ['/static/'],
        'health_check': ['/api/status', '/api/health'],
        'container_status': ['/api/container/']
    }
    
    def __init__(self, app):
        """Initialize middleware and attach handlers to the Flask app."""
        self.app = app
        self.request_logger = logging.getLogger('requests')
        self.error_logger = logging.getLogger('errors')
        self._setup_request_handlers()
        
        
        # Apply the middleware
        @app.before_request
        def before_request():
            # Generate a unique ID for this request
            request_id = str(uuid.uuid4())[:8]
            g.request_id = request_id
            g.start_time = time.time()
            
            # Skip detailed logging for quiet endpoints
            if self._is_quiet_endpoint():
                g.is_quiet = True
                return
            
            # Log the beginning of the request with context
            referrer = request.referrer or 'No referrer'
            user_agent = request.user_agent.string if request.user_agent else 'No user agent'
            
            log_data = {
                "method": request.method,
                "path": request.path,
                "referrer": referrer,
                "user_agent": user_agent,
                "ip": request.remote_addr
            }
            
            self.request_logger.info(
                f"Request started: {request.method} {request.path} - "
                f"Ref: {referrer[:30]}{'...' if len(referrer) > 30 else ''} - "
                f"IP: {request.remote_addr}"
            )
                
        @app.after_request
        def after_request(response):
            # Calculate the request duration
            duration = time.time() - g.get('start_time', time.time())
            
            # Get the request_id or generate a fallback
            request_id = g.get('request_id', 'unknown')
            
            # Skip detailed logging for quiet endpoints, but log slow responses
            is_quiet = g.get('is_quiet', False)
            is_error = response.status_code >= 400
            is_slow = duration > 1.0  # Log slow responses even for quiet endpoints
            
            if not is_quiet or is_error or is_slow:
                # Log at appropriate level based on status code
                log_func = self.request_logger.info
                if response.status_code >= 500:
                    log_func = self.request_logger.error
                elif response.status_code >= 400:
                    log_func = self.request_logger.warning
                
                status_msg = f"{response.status_code}" 
                if is_slow:
                    status_msg += " [SLOW]"
                
                log_func(
                    f"Request completed: {request.method} {request.path} - "
                    f"Status: {status_msg} - "
                    f"Duration: {duration:.3f}s"
                )
            
            # Add the request ID to the response headers for debugging
            response.headers['X-Request-ID'] = request_id
            
            # Add CORS headers if enabled
            if current_app.config.get('CORS_ENABLED', False):
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Requested-With'
            
            return response
        
        # Handle exceptions in requests
        @app.errorhandler(Exception)
        def handle_exception(e):
            request_id = g.get('request_id', 'unknown')
            duration = time.time() - g.get('start_time', time.time())
            
            # Log exceptions with traceback
            self.error_logger.exception(
                f"Request failed: {request.method} {request.path} - "
                f"Error: {str(e)} - "
                f"Duration: {duration:.3f}s"
            )
            
            # Special handling for AJAX requests to provide consistent error format
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                response = APIResponse(
                    success=False,
                    error=str(e),
                    code=500 if not isinstance(e, HTTPException) else e.code
                )
                return response.to_response()
                
            # Let the regular error handlers take care of the response for non-AJAX
            raise e
    def _setup_request_handlers(self):
        """Set up request handling hooks with context safety."""
        @self.app.before_request
        def before_request():
            # Generate a unique ID for this request
            request_id = str(uuid.uuid4())[:8]
            g.request_id = request_id
            g.start_time = time.time()
            
            # Skip detailed logging for quiet endpoints
            if self._is_quiet_endpoint():
                g.is_quiet = True
                return
            
            # Log the beginning of the request with context
            referrer = request.referrer or 'No referrer'
            user_agent = request.user_agent.string if request.user_agent else 'No user agent'
            
            self.request_logger.info(
                f"Request started: {request.method} {request.path} - "
                f"Ref: {referrer[:30]}{'...' if len(referrer) > 30 else ''} - "
                f"IP: {request.remote_addr}"
            )

    def _is_quiet_endpoint(self) -> bool:
        """Check if current request is to an endpoint that should have minimal logging."""
        path = request.path
        for category, patterns in self.QUIET_ENDPOINTS.items():
            for pattern in patterns:
                if pattern in path:
                    return True
        return False


def create_logger_for_component(component_name: str) -> logging.Logger:
    """
    Create a logger for a specific component with appropriate formatting.
    
    Args:
        component_name: Name of the component (e.g., 'docker', 'security')
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(component_name)


def initialize_logging(app: Flask) -> LoggingService:
    """
    Initialize the enhanced logging system for the Flask app.
    
    Args:
        app: Flask application instance
        
    Returns:
        Configured LoggingService instance
    """
    # Create logging service and initialize it with the app
    logging_service = LoggingService(app)
    
    # Apply the enhanced request logger middleware with context safety
    EnhancedRequestLoggerMiddleware(app)
    
    # Store logging service in app config for reference
    app.config['logging_service'] = logging_service
    
    return logging_service
