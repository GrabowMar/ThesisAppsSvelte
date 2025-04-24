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

# Standard Library Imports
import logging
import logging.handlers
import os
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Set, Union, Any, Tuple

# Third-Party Imports
import coloredlogs
from flask import Flask, Response, current_app, g, has_app_context, has_request_context, jsonify, request # Added Response
from werkzeug.exceptions import HTTPException

# Local Application Imports (assuming app_models is local)
try:
    # Attempt to import the standard APIResponse model
    from app_models import APIResponse
except ImportError:
    # Fallback implementation if app_models is not available
    class APIResponse:
        """Simple fallback implementation of APIResponse."""
        def __init__(self, success: bool = True, message: str = "", error: str = "", data: Optional[Dict] = None, code: int = 200):
            self.success = success
            self.message = message
            self.error = error
            self.data = data or {}
            self.code = code

        def to_response(self) -> Tuple[Any, int]:
            """Convert to Flask response with appropriate status code."""
            # Import jsonify here to avoid circular dependency if Flask is not fully loaded
            from flask import jsonify
            response_data = {
                "success": self.success,
                "message": self.message,
            }

            if self.data: # Check if data is not empty
                response_data["data"] = self.data

            if self.error: # Check if error is not empty
                response_data["error"] = self.error

            return jsonify(response_data), self.code


class LogConfig:
    """Centralized logging configuration with sensible defaults."""

    # Log levels by name
    LEVELS: Dict[str, int] = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }

    # Default formats
    CONSOLE_FORMAT: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    # Added request_id and component to the file format for better context
    FILE_FORMAT: str = "%(asctime)s [%(levelname)s] [%(request_id)s] [%(threadName)s] %(component)s.%(name)s: %(message)s"
    REQUEST_FILE_FORMAT: str = "%(asctime)s [%(levelname)s] [%(request_id)s] %(message)s"
    ERROR_FILE_FORMAT: str = "%(asctime)s [%(levelname)s] [%(request_id)s] %(component)s.%(name)s.%(funcName)s:%(lineno)d - %(message)s"
    DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    # Default log directories and files
    DEFAULT_LOG_DIR: str = "logs"
    REQUEST_LOG: str = "requests.log"
    ERROR_LOG: str = "errors.log"
    APP_LOG: str = "app.log"

    # Size-based rotation (10MB)
    MAX_BYTES: int = 10 * 1024 * 1024
    BACKUP_COUNT: int = 5

    @classmethod
    def get_level(cls, level_name: str) -> int:
        """Convert level name to level value with fallback to INFO."""
        return cls.LEVELS.get(level_name.upper(), logging.INFO)


class ContextFilter(logging.Filter):
    """
    Injects contextual information like request_id and component name
    into log records.
    """
    DEFAULT_REQUEST_ID: str = '-'
    DEFAULT_COMPONENT_NAME: str = 'app'

    def __init__(self, app_name: str = DEFAULT_COMPONENT_NAME):
        super().__init__()
        self.app_name = app_name

    def filter(self, record: logging.LogRecord) -> bool:
        """Adds request_id and component to the log record."""
        # Add request_id if in a request context
        try:
            # Check if we are in both an app and request context
            if has_app_context() and has_request_context():
                record.request_id = getattr(g, 'request_id', self.DEFAULT_REQUEST_ID)
            else:
                record.request_id = self.DEFAULT_REQUEST_ID
        except (RuntimeError):
            # Handle cases where Flask contexts might not be available (e.g., startup, background tasks)
            record.request_id = self.DEFAULT_REQUEST_ID

        # Add component information if not already present
        if not hasattr(record, 'component'):
            # Extract component from logger name if structured like 'component.submodule'
            if '.' in record.name:
                record.component = record.name.split('.', 1)[0]
            else:
                # Fallback to app name or default if logger name has no component part
                record.component = self.app_name if record.name == 'root' else record.name

        # Ensure component is always set, defaulting if necessary
        record.component = getattr(record, 'component', self.app_name)

        return True


class RequestFilter(logging.Filter):
    """
    Filter for reducing noise from frequent, successful requests on specific paths.
    Logs these paths only if they result in errors or warnings.
    """
    DEFAULT_EXCLUDED_PATHS: Set[str] = {
        '/api/container/',
        '/api/status',
        '/api/system-info',
        '/static/'
    }

    def __init__(self, excluded_paths: Optional[Set[str]] = None):
        super().__init__()
        # Paths to exclude from regular successful logging
        self.excluded_paths = excluded_paths or self.DEFAULT_EXCLUDED_PATHS
        # Always log these paths if they result in errors (status >= 400)
        self.log_excluded_on_error = True

    def filter(self, record: logging.LogRecord) -> bool:
        """Filters log records based on request path and status code."""
        # Check if it's a standard werkzeug request log format
        # e.g., "GET /path HTTP/1.1" 200 -
        is_werkzeug_log = (
            hasattr(record, 'args') and
            isinstance(record.args, tuple) and
            len(record.args) >= 3 and
            isinstance(record.args[0], str) # method, path, proto
        )

        if not is_werkzeug_log:
            # Don't filter non-werkzeug logs (e.g., our custom request start/end logs)
            return True

        # Extract request path and status code from werkzeug log message
        # Example record.args[0]: '127.0.0.1 - - [24/Apr/2025 01:30:00] "GET /api/status HTTP/1.1" 200 -'
        log_message = record.getMessage() # Get the formatted message
        parts = log_message.split()
        if len(parts) < 7: # Basic check for expected format elements
             return True # Cannot parse, don't filter

        request_line = parts[5:8] # ["GET", "/path", "HTTP/1.1"]
        status_code_str = parts[8]  # "200"

        if not status_code_str.isdigit():
             return True # Cannot parse status code, don't filter

        path = request_line[1]
        status_code = int(status_code_str)

        # Check if this path should be filtered
        for excluded_path_pattern in self.excluded_paths:
            if excluded_path_pattern in path:
                # If status code is success (2xx or 3xx) and we don't log errors for excluded
                is_success = 200 <= status_code < 400
                if is_success:
                    return False # Filter out successful request for excluded path
                elif self.log_excluded_on_error:
                    # Allow errors (4xx, 5xx) for excluded paths through
                    return True
                else:
                     # Filter out errors too if log_excluded_on_error is False
                     return False

        # If not an excluded path, always let the log record through
        return True


class LoggingService:
    """Enhanced logging service integrating handlers, filters, and formatters."""

    def __init__(self, app: Optional[Flask] = None):
        self.app: Optional[Flask] = app
        self.log_dir: Path = Path(LogConfig.DEFAULT_LOG_DIR)
        self.handlers: Dict[str, logging.Handler] = {}
        self.context_filter: Optional[ContextFilter] = None

        # Initialize immediately if app is provided
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize logging configuration using Flask app context."""
        self.app = app

        # Get configuration from app config or environment variables
        log_level_name = app.config.get('LOG_LEVEL', os.environ.get('LOG_LEVEL', 'INFO'))
        log_level = LogConfig.get_level(log_level_name)
        self.log_dir = Path(app.config.get('LOG_DIR', os.environ.get('LOG_DIR', LogConfig.DEFAULT_LOG_DIR)))

        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create shared context filter
        self.context_filter = ContextFilter(app_name=app.name or LogConfig.DEFAULT_COMPONENT_NAME)

        # Configure specialized loggers first (so root doesn't capture everything unfiltered)
        self._configure_request_logger(log_level)
        self._configure_error_logger()

        # Configure the root logger (handles general app logs)
        self._configure_root_logger(log_level)

        # Apply component-specific levels
        self._configure_component_loggers()

        # Add colorized console logs for development environments
        if app.debug or os.environ.get('FLASK_ENV') != 'production':
            self._configure_colored_console_logs(log_level)
        else:
            # Add a standard console handler for production if needed
            self._configure_standard_console_handler(log_level)

        # Add context filter to relevant handlers (already added during handler creation)

        # Log initialization message
        root_logger = logging.getLogger()
        root_logger.info(f"Logging initialized. Level: {log_level_name}. Log directory: {self.log_dir}")


    def _create_rotating_handler(self, filename: Path, level: int, formatter: logging.Formatter) -> logging.handlers.RotatingFileHandler:
        """Creates and configures a RotatingFileHandler."""
        handler = logging.handlers.RotatingFileHandler(
            filename=filename,
            maxBytes=LogConfig.MAX_BYTES,
            backupCount=LogConfig.BACKUP_COUNT,
            encoding='utf-8' # Explicitly set encoding
        )
        handler.setFormatter(formatter)
        handler.setLevel(level)
        if self.context_filter:
            handler.addFilter(self.context_filter) # Add context here
        return handler

    def _configure_root_logger(self, level: int) -> None:
        """Configures the root logger for general application logs."""
        root_logger = logging.getLogger()
        root_logger.setLevel(level) # Set base level for the root logger

        # Remove default handlers Flask might add
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        file_formatter = logging.Formatter(fmt=LogConfig.FILE_FORMAT, datefmt=LogConfig.DATE_FORMAT)

        app_handler = self._create_rotating_handler(
            filename=self.log_dir / LogConfig.APP_LOG,
            level=level, # Root handler logs at the global level
            formatter=file_formatter
        )
        self.handlers['app'] = app_handler
        root_logger.addHandler(app_handler)

        # Also send root logger errors to the error log file
        if 'errors' in self.handlers:
            error_handler = self.handlers['errors']
            # Ensure the error handler filters correctly at the root level too
            error_handler.setLevel(logging.ERROR)
            if self.context_filter:
                 # Make sure error handler also has context
                error_handler.addFilter(self.context_filter)
            root_logger.addHandler(error_handler)


    def _configure_request_logger(self, level: int) -> None:
        """Configures the logger specifically for HTTP requests (werkzeug)."""
        # Configure the 'werkzeug' logger used by Flask for request logging
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(level) # Use the global level for requests initially

        # Remove default handlers werkzeug might add to avoid duplication
        for handler in werkzeug_logger.handlers[:]:
            werkzeug_logger.removeHandler(handler)

        request_formatter = logging.Formatter(fmt=LogConfig.REQUEST_FILE_FORMAT, datefmt=LogConfig.DATE_FORMAT)

        request_handler = self._create_rotating_handler(
            filename=self.log_dir / LogConfig.REQUEST_LOG,
            level=level, # Request handler logs at the global level
            formatter=request_formatter
        )

        # Add request filter to reduce noise from frequent successful requests
        request_filter = RequestFilter()
        request_handler.addFilter(request_filter) # Filter specific file handler

        self.handlers['requests'] = request_handler
        werkzeug_logger.addHandler(request_handler)

        # Prevent werkzeug logs from propagating to the root logger's app.log file
        werkzeug_logger.propagate = False


    def _configure_error_logger(self) -> None:
        """Configures the logger specifically for error-level logs."""
        # Error logs are handled by adding a dedicated handler to the root logger,
        # filtering for ERROR level. No separate logger needed.
        error_formatter = logging.Formatter(fmt=LogConfig.ERROR_FILE_FORMAT, datefmt=LogConfig.DATE_FORMAT)

        error_handler = self._create_rotating_handler(
            filename=self.log_dir / LogConfig.ERROR_LOG,
            level=logging.ERROR, # This handler *only* captures ERROR+
            formatter=error_formatter
        )
        self.handlers['errors'] = error_handler
        # This handler will be added to the root logger in _configure_root_logger


    def _configure_component_loggers(self) -> None:
        """Sets specific logging levels for different application components."""
        component_levels = {
            # Example: Set more verbose logging for 'docker' component if needed
             # "docker": logging.DEBUG,
             "zap_scanner": logging.INFO,
             "owasp_zap": logging.WARNING, # Reduce noise from ZAP library itself
             "docker": logging.INFO,
             "performance": logging.INFO,
             "security": logging.INFO,
             "gpt4all": logging.INFO,
             "batch_analysis": logging.INFO,
             # Add other components as needed
        }

        for component, level in component_levels.items():
            component_logger = logging.getLogger(component)
            component_logger.setLevel(level)
            # Ensure component logs propagate to root handlers (app.log, error.log)
            component_logger.propagate = True
            # Add context filter directly? No, it's handled by the root handlers.

    def _configure_colored_console_logs(self, level: int) -> None:
        """Adds colored logging to the console for development environments."""
        # coloredlogs modifies the root logger's handlers, so configure it carefully
        coloredlogs.install(
            level=level,
            # Use root logger instance to avoid conflicts if already configured
            logger=logging.getLogger(),
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
                'name': {'color': 'magenta'},
                'request_id': {'color': 'blue'}, # Example: Add style for custom fields
                'component': {'color': 'yellow'}
            }
        )
        # Add context filter to the console handler created by coloredlogs
        # Note: coloredlogs might replace existing handlers. Check its behavior.
        # Generally safer to add filter to root logger and let handlers inherit.
        # Let's ensure the root logger has the filter.
        if self.context_filter:
             logging.getLogger().addFilter(self.context_filter)

        # Add request filter to the console handler as well to reduce noise there
        # Find the console handler added by coloredlogs (usually StreamHandler)
        console_handler = None
        for handler in logging.getLogger().handlers:
             if isinstance(handler, logging.StreamHandler):
                  console_handler = handler
                  break
        if console_handler:
             request_filter = RequestFilter()
             console_handler.addFilter(request_filter) # Filter console output too
             # Ensure console handler also has context filter if not inherited
             if self.context_filter and self.context_filter not in console_handler.filters:
                 console_handler.addFilter(self.context_filter)

        self.handlers['console_colored'] = console_handler

    def _configure_standard_console_handler(self, level: int) -> None:
        """Adds a standard, non-colored console handler (e.g., for production)."""
        console_formatter = logging.Formatter(fmt=LogConfig.CONSOLE_FORMAT, datefmt=LogConfig.DATE_FORMAT)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)

        # Add filters for context and request noise reduction
        if self.context_filter:
            console_handler.addFilter(self.context_filter)
        request_filter = RequestFilter()
        console_handler.addFilter(request_filter)

        self.handlers['console_standard'] = console_handler
        logging.getLogger().addHandler(console_handler)


    def get_logger(self, name: str) -> logging.Logger:
        """Gets a logger instance configured within our logging system."""
        # Loggers automatically inherit level/handlers from parents unless overridden
        logger = logging.getLogger(name)
        # No need to add handlers/filters here; they are managed at the root
        # or specific component levels set in _configure_component_loggers
        return logger


class EnhancedRequestLoggerMiddleware:
    """
    Flask middleware hooks to log request start, end, and errors
    with enhanced context like duration and request ID.
    """
    # Constants for magic values
    SLOW_REQUEST_THRESHOLD_SECONDS: float = 1.0
    REQUEST_ID_HEADER: str = 'X-Request-ID'
    AJAX_HEADER_CHECK: Tuple[str, str] = ('X-Requested-With', 'XMLHttpRequest')
    REQUEST_ID_LENGTH: int = 8

    # Endpoints for which successful requests shouldn't clutter logs excessively
    # Note: The RequestFilter applied to handlers actually performs the filtering
    # This set might be redundant if RequestFilter covers all cases, but can be
    # used for specific middleware logic if needed (like skipping before_request log).
    QUIET_ENDPOINTS_PATTERNS: Set[str] = {
        '/static/',
        '/api/status',
        '/api/health', # Added common health check endpoint
        '/api/container/'
    }

    def __init__(self, app: Flask):
        """Initialize middleware and attach handlers to the Flask app."""
        self.app = app
        # Get specific loggers if needed, but often logging is done via root or werkzeug
        # self.request_logger = logging.getLogger('requests') # Not used directly here
        self.error_logger = logging.getLogger('errors') # Used for explicit exception logging

        # Register request lifecycle handlers using decorators within the class scope
        self._register_handlers()


    def _is_quiet_endpoint(self) -> bool:
        """Checks if the current request path matches any quiet endpoint patterns."""
        # Ensure we are in a request context
        if not has_request_context():
            return False
        path = request.path
        for pattern in self.QUIET_ENDPOINTS_PATTERNS:
            if pattern in path:
                return True
        return False

    def _register_handlers(self) -> None:
        """Registers the before_request, after_request, and errorhandler methods."""

        @self.app.before_request
        def before_request_logging() -> None:
            """Log the start of a request and set up context."""
            # Generate a unique ID for this request
            request_id = str(uuid.uuid4())[:self.REQUEST_ID_LENGTH]
            g.request_id = request_id
            g.start_time = time.time()
            g.is_quiet = self._is_quiet_endpoint() # Check if endpoint is quiet

            # Skip detailed "Request started" log for quiet endpoints
            if g.is_quiet:
                return

            # Log the beginning of the request (will be handled by werkzeug logger)
            # No, werkzeug handles the *completion*, we might want a start marker
            # Let's log it via the root logger.
            referrer = request.referrer or 'No referrer'
            user_agent = request.user_agent.string if request.user_agent else 'No user agent'
            truncated_referrer = f"{referrer[:50]}{'...' if len(referrer) > 50 else ''}" # Slightly longer truncate

            # Use root logger, context filter will add request_id
            logging.info(
                f"Request started: {request.method} {request.path} - "
                f"IP: {request.remote_addr} - Ref: {truncated_referrer} - Agent: {user_agent[:50]}..."
            )


        @self.app.after_request
        def after_request_logging(response: Any) -> Any:
            """Log the completion of a request, duration, and add headers."""
            start_time = g.get('start_time', time.time()) # Default to now if start_time missing
            duration = time.time() - start_time
            request_id = g.get('request_id', ContextFilter.DEFAULT_REQUEST_ID)

            # Add request ID to response headers for client-side debugging
            if isinstance(response, Response): # Check if it's a Flask Response object
                 response.headers[self.REQUEST_ID_HEADER] = request_id

            # Determine if logging is needed (not quiet, or error, or slow)
            is_quiet = g.get('is_quiet', False)
            status_code = response.status_code if isinstance(response, Response) else getattr(response, 'code', 0) # Handle non-Response returns (e.g., tuple)

            is_error = status_code >= 400
            is_slow = duration > self.SLOW_REQUEST_THRESHOLD_SECONDS

            # Note: Werkzeug logger usually logs the completion line (e.g., "GET /path 200").
            # We might want to *avoid* duplicating that log line here unless adding info.
            # Let's only log explicitly here if it's SLOW or an ERROR that werkzeug might miss context on.

            if is_slow or (is_error and not is_quiet): # Log slow requests, or errors on non-quiet paths
                log_level = logging.WARNING if is_error else logging.INFO
                status_msg = f"{status_code}"
                if is_slow:
                    status_msg += " [SLOW]"

                # Use root logger, context filter adds request_id
                logging.log( # Use logging.log to specify level dynamically
                    log_level,
                    f"Request finished: {request.method} {request.path} - "
                    f"Status: {status_msg} - Duration: {duration:.3f}s"
                )

            # Add CORS headers if enabled in app config
            if current_app.config.get('CORS_ENABLED', False) and isinstance(response, Response):
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With' # Added Authorization

            return response


        @self.app.errorhandler(Exception)
        def handle_exception_logging(e: Exception) -> Any:
            """Log unhandled exceptions and return appropriate response."""
            start_time = g.get('start_time', time.time())
            duration = time.time() - start_time
            request_id = g.get('request_id', ContextFilter.DEFAULT_REQUEST_ID) # Use constant

            # Log the exception with traceback using the dedicated error logger setup
            # The context filter will add the request ID automatically.
            self.error_logger.exception(
                f"Unhandled exception during request: {request.method} {request.path} - "
                f"Error: {e!s} - Duration: {duration:.3f}s"
            )

            # Special handling for AJAX requests to return structured JSON error
            header_name, header_value = self.AJAX_HEADER_CHECK
            if request.headers.get(header_name) == header_value:
                status_code = 500
                if isinstance(e, HTTPException):
                    status_code = e.code or 500 # Use HTTPException code if available

                # Use the imported or fallback APIResponse
                api_response = APIResponse(
                    success=False,
                    error=str(e), # Simple string representation for client
                    message="An internal server error occurred.", # Generic message
                    code=status_code
                )
                return api_response.to_response()

            # For non-AJAX requests, re-raise the exception to let Flask's default
            # error handling (e.g., showing a 500 error page) take over.
            # If Flask is in debug mode, this will show the interactive debugger.
            # If not in debug mode, it shows the standard server error page.
            # Note: Returning a response here would bypass Flask's standard error page rendering.
            raise e


def create_logger_for_component(component_name: str) -> logging.Logger:
    """
    Gets a logger instance for a specific application component.

    Log level and handlers are determined by the logging configuration
    (see _configure_component_loggers and root logger setup).

    Args:
        component_name: Name of the component (e.g., 'docker', 'security').
                        Should match keys used in _configure_component_loggers
                        for specific level overrides.

    Returns:
        Configured logger instance.
    """
    # Loggers are typically named using dot notation, e.g., 'component.submodule'
    # This ensures correct propagation and potential level setting.
    return logging.getLogger(component_name)


def initialize_logging(app: Flask) -> LoggingService:
    """
    Initializes the enhanced logging system for the Flask application.

    Sets up handlers, formatters, filters, and integrates request lifecycle logging.

    Args:
        app: The Flask application instance.

    Returns:
        The configured LoggingService instance.
    """
    # Disable Flask's default logging handlers if they exist, as we manage our own.
    # Note: Flask >= 1.0 doesn't add handlers by default if LOGGING_CONFIG is not set.
    # However, explicitly setting level prevents default handler creation if logger is accessed early.
    app.logger.setLevel(logging.DEBUG) # Set level early, handlers will control output
    # Remove default handlers if any were added previously
    for handler in app.logger.handlers[:]:
         app.logger.removeHandler(handler)
    app.logger.propagate = True # Let Flask app logs go to our root logger

    # Create and initialize the logging service
    logging_service = LoggingService()
    logging_service.init_app(app)

    # Apply the enhanced request logger middleware
    EnhancedRequestLoggerMiddleware(app)

    # Optionally store the service instance on the app context if needed elsewhere
    app.extensions['logging_service'] = logging_service

    app.logger.info("Enhanced logging service and request middleware initialized.")
    return logging_service


