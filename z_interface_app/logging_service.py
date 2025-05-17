import logging
import logging.handlers
import os
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Set, Union, Any, Tuple, Type, Callable
import queue
import atexit

import coloredlogs
from flask import Flask, Response, current_app, g, has_app_context, has_request_context, jsonify, request
from werkzeug.exceptions import HTTPException

try:
    from app_models import APIResponse
except ImportError:
    # Define fallback APIResponse if not available
    class APIResponse:
        """Fallback API response class when the actual module is not available."""
        
        def __init__(self, success: bool = True, message: str = "", error: str = "", data: Optional[Dict] = None, code: int = 200):
            self.success = success
            self.message = message
            self.error = error
            self.data = data or {}
            self.code = code

        def to_response(self) -> Tuple[Any, int]:
            """Convert the response to a Flask JSON response with status code."""
            from flask import jsonify
            response_data = {
                "success": self.success,
                "message": self.message,
            }
            if self.data: response_data["data"] = self.data
            if self.error: response_data["error"] = self.error
            return jsonify(response_data), self.code


class LogConfig:
    """Configuration constants for logging."""
    
    LEVELS: Dict[str, int] = {
        "DEBUG": logging.DEBUG, "INFO": logging.INFO, "WARNING": logging.WARNING,
        "ERROR": logging.ERROR, "CRITICAL": logging.CRITICAL
    }

    BASE_FORMAT: str = "%(asctime)s [%(levelname)s]"
    CONSOLE_FORMAT: str = f"{BASE_FORMAT} %(name)s: %(message)s"
    FILE_FORMAT: str = f"{BASE_FORMAT} [%(request_id)s] [%(threadName)s] %(component)s.%(name)s: %(message)s"
    REQUEST_FILE_FORMAT: str = f"{BASE_FORMAT} [%(request_id)s] %(message)s"
    ERROR_FILE_FORMAT: str = f"{BASE_FORMAT} [%(request_id)s] %(component)s.%(name)s.%(funcName)s:%(lineno)d - %(message)s"

    DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    DEFAULT_LOG_DIR: str = "logs"
    REQUEST_LOG: str = "requests.log"
    ERROR_LOG: str = "errors.log"
    APP_LOG: str = "app.log"
    MAX_BYTES: int = 10 * 1024 * 1024
    BACKUP_COUNT: int = 5

    DEFAULT_QUEUE_SIZE: int = 100000

    @classmethod
    def get_level(cls, level_name: str) -> int:
        """Convert a level name to a logging level value."""
        return cls.LEVELS.get(level_name.upper(), logging.INFO)


class ContextFilter(logging.Filter):
    """Filter that adds request context information to log records."""
    
    DEFAULT_REQUEST_ID: str = '-'
    DEFAULT_COMPONENT_NAME: str = 'app'

    def __init__(self, app_name: str = DEFAULT_COMPONENT_NAME):
        super().__init__()
        self.app_name = app_name

    def filter(self, record: logging.LogRecord) -> bool:
        # Add request_id attribute to the record
        try:
            if has_app_context() and has_request_context():
                record.request_id = getattr(g, 'request_id', self.DEFAULT_REQUEST_ID)
            else:
                record.request_id = self.DEFAULT_REQUEST_ID
        except RuntimeError:
            record.request_id = self.DEFAULT_REQUEST_ID

        # Add component attribute to the record
        if not hasattr(record, 'component'):
            if '.' in record.name:
                record.component = record.name.split('.', 1)[0]
            else:
                record.component = self.app_name if record.name == 'root' else record.name
        record.component = getattr(record, 'component', self.app_name)
        return True


class PathMatcher:
    """Utility for path matching operations in log filtering."""
    
    @staticmethod
    def path_matches_any_pattern(path: str, patterns: Set[str]) -> bool:
        """Check if a path matches any of the provided patterns."""
        return any(pattern in path for pattern in patterns)


class RequestFilter(logging.Filter):
    """Filter to exclude certain requests from logs based on path patterns."""
    
    DEFAULT_EXCLUDED_PATHS: Set[str] = {
        '/api/container/', '/api/status', '/api/system-info', '/static/'
    }

    def __init__(self, excluded_paths: Optional[Set[str]] = None):
        super().__init__()
        self.excluded_paths = excluded_paths or self.DEFAULT_EXCLUDED_PATHS
        self.log_excluded_on_error = True

    def filter(self, record: logging.LogRecord) -> bool:
        # Only apply filter to werkzeug logger
        if record.name != 'werkzeug':
            return True

        # Check if the record contains a valid HTTP request
        if not (hasattr(record, 'args') and
                isinstance(record.args, tuple) and
                len(record.args) >= 3 and
                isinstance(record.args[0], str) and
                any(record.args[0].startswith(method) for method in
                    ('GET ', 'POST ', 'PUT ', 'DELETE ', 'PATCH '))):
            return True

        try:
            request_line = record.args[0]
            status_code = record.args[1]
            path = request_line.split()[1]

            if PathMatcher.path_matches_any_pattern(path, self.excluded_paths):
                is_success = 200 <= status_code < 400
                return not is_success or self.log_excluded_on_error

            return True
        except (IndexError, ValueError, TypeError):
            # In case of parsing errors, allow the record to be logged
            return True


class HandlerFactory:
    """Factory for creating different types of log handlers."""
    
    @staticmethod
    def create_rotating_file_handler(
        filename: Path,
        level: int,
        formatter: logging.Formatter,
        filters: Optional[List[logging.Filter]] = None,
        max_bytes: int = LogConfig.MAX_BYTES,
        backup_count: int = LogConfig.BACKUP_COUNT
    ) -> Union[logging.handlers.RotatingFileHandler, logging.handlers.WatchedFileHandler]:
        """Create an appropriate file handler with the specified configuration."""
        filename.parent.mkdir(parents=True, exist_ok=True)
        
        # Use WatchedFileHandler on Windows to avoid file locking issues during rotation
        if os.name == 'nt':
            # On Windows, use WatchedFileHandler instead of RotatingFileHandler
            # This handler doesn't try to rename files, avoiding the locking issues
            handler = logging.handlers.WatchedFileHandler(
                filename=str(filename),
                encoding='utf-8'
            )
            # Since we're not using rotation directly, implement a basic size check
            # and manual rotation logic if needed in the future
            logging.info(f"Using WatchedFileHandler for Windows for log file: {filename}")
        else:
            # On Unix-like systems, continue using RotatingFileHandler
            handler = logging.handlers.RotatingFileHandler(
                filename=filename,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8',
                delay=True  # Only open the file when first record is emitted
            )
        
        handler.setFormatter(formatter)
        handler.setLevel(level)
        
        if filters:
            for filter_obj in filters:
                handler.addFilter(filter_obj)
                
        return handler
    
    @staticmethod
    def create_console_handler(
        level: int,
        formatter: logging.Formatter,
        filters: Optional[List[logging.Filter]] = None
    ) -> logging.StreamHandler:
        """Create a console handler with the specified configuration."""
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(formatter)
        
        if filters:
            for filter_obj in filters:
                handler.addFilter(filter_obj)
                
        return handler
    
    @staticmethod
    def create_colored_console_handler(
        level: int,
        logger: logging.Logger,
        format_str: str,
        date_format: str
    ) -> Optional[logging.StreamHandler]:
        """Create a colored console handler using coloredlogs."""
        try:
            coloredlogs.install(
                level=level,
                logger=logger,
                fmt=format_str,
                datefmt=date_format,
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
                    'request_id': {'color': 'blue'},
                    'component': {'color': 'yellow'}
                }
            )
            
            # Return the first StreamHandler found
            for handler in logger.handlers:
                if isinstance(handler, logging.StreamHandler):
                    return handler
                    
            return None
        except Exception as e:
            # Log the error to stderr since logging might not be set up yet
            import sys
            print(f"Failed to initialize coloredlogs: {e}", file=sys.stderr)
            return None


class LoggerManager:
    """Manages the configuration of different loggers."""
    
    @staticmethod
    def clear_handlers(logger: logging.Logger) -> None:
        """Remove all handlers from a logger."""
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
    
    @staticmethod
    def configure_component_loggers(component_levels: Dict[str, int]) -> None:
        """Configure log levels for different application components."""
        for component, level in component_levels.items():
            logging.getLogger(component).setLevel(level)


class LoggingService:
    """Main service for configuring and managing application logging."""
    
    def __init__(self, app: Optional[Flask] = None):
        self.app: Optional[Flask] = app
        self.log_dir: Path = Path(LogConfig.DEFAULT_LOG_DIR)
        self.target_handlers: Dict[str, logging.Handler] = {}
        self.context_filter: Optional[ContextFilter] = None
        self.queue_listener: Optional[logging.handlers.QueueListener] = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize logging for a Flask application."""
        self.app = app
        log_level_name = app.config.get('LOG_LEVEL', os.environ.get('LOG_LEVEL', 'INFO'))
        log_level = LogConfig.get_level(log_level_name)
        self.log_dir = Path(app.config.get('LOG_DIR', os.environ.get('LOG_DIR', LogConfig.DEFAULT_LOG_DIR)))
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.context_filter = ContextFilter(app_name=app.name or LogConfig.DEFAULT_COMPONENT_NAME)

        self._create_target_handlers(log_level)
        self._setup_queue_logging(log_level)
        self._setup_console_logging(log_level, app.debug)
        self._configure_component_loggers()

        # Register cleanup function
        atexit.register(self.stop_listener)

        logging.getLogger().info(
            f"Queue-based logging initialized. Level: {log_level_name}. "
            f"Log directory: {self.log_dir}"
        )

    def _create_target_handlers(self, log_level: int) -> None:
        """Create file handlers for different log types."""
        # App log handler
        self.target_handlers['app'] = HandlerFactory.create_rotating_file_handler(
            filename=self.log_dir / LogConfig.APP_LOG,
            level=log_level,
            formatter=logging.Formatter(LogConfig.FILE_FORMAT, LogConfig.DATE_FORMAT),
            filters=[self.context_filter]
        )

        # Error log handler
        self.target_handlers['errors'] = HandlerFactory.create_rotating_file_handler(
            filename=self.log_dir / LogConfig.ERROR_LOG,
            level=logging.ERROR,
            formatter=logging.Formatter(LogConfig.ERROR_FILE_FORMAT, LogConfig.DATE_FORMAT),
            filters=[self.context_filter]
        )

        # Request log handler
        self.target_handlers['requests'] = HandlerFactory.create_rotating_file_handler(
            filename=self.log_dir / LogConfig.REQUEST_LOG,
            level=log_level,
            formatter=logging.Formatter(LogConfig.REQUEST_FILE_FORMAT, LogConfig.DATE_FORMAT),
            filters=[self.context_filter, RequestFilter()]
        )

    def _setup_queue_logging(self, log_level: int) -> None:
        """Set up queue-based logging to avoid blocking I/O during request processing."""
        if not self.app:
            return
            
        queue_size = self.app.config.get('LOG_QUEUE_SIZE', LogConfig.DEFAULT_QUEUE_SIZE)
        log_queue = queue.Queue(queue_size)
        queue_handler = logging.handlers.QueueHandler(log_queue)

        # Configure the root logger
        root_logger = logging.getLogger()
        LoggerManager.clear_handlers(root_logger)
        root_logger.setLevel(log_level)
        root_logger.addHandler(queue_handler)

        # Configure the werkzeug logger
        werkzeug_logger = logging.getLogger('werkzeug')
        LoggerManager.clear_handlers(werkzeug_logger)
        werkzeug_logger.setLevel(log_level)
        werkzeug_logger.addHandler(queue_handler)
        werkzeug_logger.propagate = False

        # Start the queue listener
        self.queue_listener = logging.handlers.QueueListener(
            log_queue,
            self.target_handlers['app'],
            self.target_handlers['errors'],
            self.target_handlers['requests'],
            respect_handler_level=True
        )
        self.queue_listener.start()

    def _setup_console_logging(self, log_level: int, is_debug_mode: bool) -> None:
        """Set up console logging with appropriate formatting."""
        console_handler = None

        # Determine if we should use colored logs
        if is_debug_mode or os.environ.get('FLASK_ENV') != 'production':
            console_handler = self._setup_colored_console_handler(log_level)
            
        # Fall back to standard console handler if colored logs aren't set up
        if console_handler is None:
            console_handler = self._setup_standard_console_handler(log_level)

        # Add filters to the console handler
        if console_handler:
            console_handler.addFilter(self.context_filter)
            console_handler.addFilter(RequestFilter())

    def _setup_colored_console_handler(self, log_level: int) -> Optional[logging.StreamHandler]:
        """Set up colored console logging."""
        root_logger = logging.getLogger()
        return HandlerFactory.create_colored_console_handler(
            level=log_level, 
            logger=root_logger,
            format_str=LogConfig.CONSOLE_FORMAT,
            date_format=LogConfig.DATE_FORMAT
        )

    def _setup_standard_console_handler(self, log_level: int) -> logging.StreamHandler:
        """Set up standard (non-colored) console logging."""
        console_formatter = logging.Formatter(LogConfig.CONSOLE_FORMAT, LogConfig.DATE_FORMAT)
        console_handler = HandlerFactory.create_console_handler(
            level=log_level,
            formatter=console_formatter
        )
        logging.getLogger().addHandler(console_handler)
        return console_handler

    def _configure_component_loggers(self) -> None:
        """Configure log levels for specific application components."""
        component_levels = {
            "zap_scanner": logging.INFO,
            "owasp_zap": logging.WARNING,
            "docker": logging.INFO,
            "performance": logging.INFO,
            "security": logging.INFO,
            "gpt4all": logging.INFO,
            "batch_analysis": logging.INFO,
        }
        LoggerManager.configure_component_loggers(component_levels)

    def stop_listener(self) -> None:
        """Stop the queue listener when the application shuts down."""
        if self.queue_listener:
            try:
                logging.info("Stopping queue listener...")
                self.queue_listener.stop()
                self.queue_listener = None
                logging.info("Queue listener stopped.")
            except Exception as e:
                # Log to stderr as the logging system might be down
                import sys
                print(f"Error stopping queue listener: {e}", file=sys.stderr)

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger with the specified name."""
        return logging.getLogger(name)


class CorsMiddleware:
    """Middleware to add CORS headers to responses."""
    
    def __init__(self, app: Flask):
        self.app = app
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register the CORS handler."""
        @self.app.after_request
        def add_cors_headers(response: Response) -> Response:
            if not current_app.config.get('CORS_ENABLED', False):
                return response

            if isinstance(response, Response):
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'

            return response


class RequestLoggerMiddleware:
    """Middleware for logging request information."""
    
    SLOW_REQUEST_THRESHOLD_SECONDS: float = 1.0
    REQUEST_ID_HEADER: str = 'X-Request-ID'
    AJAX_HEADER_CHECK: Tuple[str, str] = ('X-Requested-With', 'XMLHttpRequest')
    REQUEST_ID_LENGTH: int = 8
    QUIET_ENDPOINTS_PATTERNS: Set[str] = {
        '/static/', '/api/status', '/api/health', '/api/container/'
    }

    def __init__(self, app: Flask):
        self.app = app
        self.logger = logging.getLogger(__name__)
        self._register_handlers()

    def _is_quiet_endpoint(self) -> bool:
        """Check if the current request path matches a quiet endpoint pattern."""
        if not has_request_context():
            return False
        return PathMatcher.path_matches_any_pattern(request.path, self.QUIET_ENDPOINTS_PATTERNS)

    def _register_handlers(self) -> None:
        """Register request logging handlers."""
        @self.app.before_request
        def before_request_logging() -> None:
            # Generate a request ID and record start time
            request_id = str(uuid.uuid4())[:self.REQUEST_ID_LENGTH]
            g.request_id = request_id
            g.start_time = time.time()
            g.is_quiet = self._is_quiet_endpoint()

            if g.is_quiet:
                return

            # Log request details
            referrer = request.referrer or '-'
            user_agent = request.user_agent.string if request.user_agent else '-'

            logging.info(
                f"Request started: {request.method} {request.path} - "
                f"IP: {request.remote_addr} - Ref: {referrer[:50]}.. - Agent: {user_agent[:50]}.."
            )

        @self.app.after_request
        def after_request_logging(response: Response) -> Response:
            # Calculate request duration
            start_time = getattr(g, 'start_time', time.time())
            duration = time.time() - start_time
            request_id = getattr(g, 'request_id', ContextFilter.DEFAULT_REQUEST_ID)

            # Get status code from the response
            status_code = 0
            try:
                if isinstance(response, Response):
                    status_code = response.status_code
                    response.headers[self.REQUEST_ID_HEADER] = request_id
                elif isinstance(response, tuple) and len(response) > 1 and isinstance(response[1], int):
                    status_code = response[1]
                else:
                    status_code = getattr(response, 'status_code', 0)
            except Exception:
                # If we can't get the status code, continue anyway
                pass

            # Determine if we should log this request
            is_quiet = getattr(g, 'is_quiet', False)
            is_error = status_code >= 400
            is_slow = duration > self.SLOW_REQUEST_THRESHOLD_SECONDS

            if is_error or is_slow or not is_quiet:
                log_level = logging.WARNING if is_error else logging.INFO
                status_msg = f"{status_code}"
                if is_slow:
                    status_msg += " [SLOW]"

                logging.log(
                    log_level,
                    f"Request finished: {request.method} {request.path} - "
                    f"Status: {status_msg} - Duration: {duration:.3f}s"
                )

            return response

        @self.app.errorhandler(Exception)
        def handle_exception_logging(e: Exception) -> Any:
            # Log unhandled exceptions
            start_time = getattr(g, 'start_time', time.time())
            duration = time.time() - start_time

            logging.exception(
                f"Unhandled exception during request: {request.method} {request.path} - "
                f"Error: {e!s} - Duration: {duration:.3f}s"
            )

            # Return a JSON response for AJAX requests
            header_name, header_value = self.AJAX_HEADER_CHECK
            if request.headers.get(header_name) == header_value:
                status_code = e.code if isinstance(e, HTTPException) else 500
                api_response = APIResponse(
                    success=False,
                    error=str(e),
                    message="An internal server error occurred.",
                    code=status_code
                )
                return api_response.to_response()

            # Re-raise the exception for regular requests
            raise e


def create_logger_for_component(component_name: str) -> logging.Logger:
    """Create a logger for a specific component."""
    return logging.getLogger(component_name)


def initialize_logging(app: Flask) -> LoggingService:
    """Initialize the logging service for a Flask application."""
    # Clear existing handlers and enable propagation
    if app.logger.handlers:
        app.logger.handlers.clear()
    app.logger.propagate = True

    # Initialize and configure the logging service
    logging_service = LoggingService()
    logging_service.init_app(app)

    # Set up middleware
    RequestLoggerMiddleware(app)
    CorsMiddleware(app)

    # Store the logging service in the app extensions
    app.extensions['logging_service'] = logging_service
    app.logger.info("Enhanced queue-based logging service initialized.")
    return logging_service