# Standard Library Imports
import logging
import logging.handlers
import os
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Set, Union, Any, Tuple
import queue
import atexit

# Third-Party Imports
import coloredlogs
from flask import Flask, Response, current_app, g, has_app_context, has_request_context, jsonify, request
from werkzeug.exceptions import HTTPException

# Local Application Imports
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
            from flask import jsonify
            response_data = {
                "success": self.success,
                "message": self.message,
            }
            if self.data: response_data["data"] = self.data
            if self.error: response_data["error"] = self.error
            return jsonify(response_data), self.code


class LogConfig:
    """Centralized logging configuration with sensible defaults."""
    LEVELS: Dict[str, int] = {
        "DEBUG": logging.DEBUG, "INFO": logging.INFO, "WARNING": logging.WARNING,
        "ERROR": logging.ERROR, "CRITICAL": logging.CRITICAL
    }
    
    # Base format with common elements
    BASE_FORMAT: str = "%(asctime)s [%(levelname)s]"
    # Format extensions
    CONSOLE_FORMAT: str = f"{BASE_FORMAT} %(name)s: %(message)s"
    FILE_FORMAT: str = f"{BASE_FORMAT} [%(request_id)s] [%(threadName)s] %(component)s.%(name)s: %(message)s"
    REQUEST_FILE_FORMAT: str = f"{BASE_FORMAT} [%(request_id)s] %(message)s"
    ERROR_FILE_FORMAT: str = f"{BASE_FORMAT} [%(request_id)s] %(component)s.%(name)s.%(funcName)s:%(lineno)d - %(message)s"
    
    DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    DEFAULT_LOG_DIR: str = "logs"
    REQUEST_LOG: str = "requests.log"
    ERROR_LOG: str = "errors.log"
    APP_LOG: str = "app.log"
    MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB
    BACKUP_COUNT: int = 5
    
    # Default queue size (100,000 messages)
    DEFAULT_QUEUE_SIZE: int = 100000

    @classmethod
    def get_level(cls, level_name: str) -> int:
        """Convert level name to level value with fallback to INFO."""
        return cls.LEVELS.get(level_name.upper(), logging.INFO)


class ContextFilter(logging.Filter):
    """Injects contextual information into log records."""
    DEFAULT_REQUEST_ID: str = '-'
    DEFAULT_COMPONENT_NAME: str = 'app'

    def __init__(self, app_name: str = DEFAULT_COMPONENT_NAME):
        super().__init__()
        self.app_name = app_name

    def filter(self, record: logging.LogRecord) -> bool:
        """Adds request_id and component to the log record."""
        try:
            if has_app_context() and has_request_context():
                record.request_id = getattr(g, 'request_id', self.DEFAULT_REQUEST_ID)
            else:
                record.request_id = self.DEFAULT_REQUEST_ID
        except RuntimeError:
            record.request_id = self.DEFAULT_REQUEST_ID

        if not hasattr(record, 'component'):
            if '.' in record.name:
                record.component = record.name.split('.', 1)[0]
            else:
                record.component = self.app_name if record.name == 'root' else record.name
        record.component = getattr(record, 'component', self.app_name)
        return True


class RequestFilter(logging.Filter):
    """Filter for reducing noise from frequent, successful requests."""
    DEFAULT_EXCLUDED_PATHS: Set[str] = {
        '/api/container/', '/api/status', '/api/system-info', '/static/'
    }

    def __init__(self, excluded_paths: Optional[Set[str]] = None):
        super().__init__()
        self.excluded_paths = excluded_paths or self.DEFAULT_EXCLUDED_PATHS
        self.log_excluded_on_error = True

    def filter(self, record: logging.LogRecord) -> bool:
        """Filters log records based on request path and status code."""
        # Only filter werkzeug access logs
        if record.name != 'werkzeug':
            return True
            
        # Check if it's an access log by looking at the arguments pattern
        if not (hasattr(record, 'args') and 
                isinstance(record.args, tuple) and 
                len(record.args) >= 3 and
                isinstance(record.args[0], str) and
                any(record.args[0].startswith(method) for method in 
                    ('GET ', 'POST ', 'PUT ', 'DELETE ', 'PATCH '))):
            return True
            
        try:
            # Extract path and status code from werkzeug log format
            request_line = record.args[0]
            status_code = record.args[1]
            path = request_line.split()[1]  # Get path from "GET /path HTTP/1.1"

            # Check if path matches any excluded pattern
            for excluded_path_pattern in self.excluded_paths:
                if excluded_path_pattern in path:
                    # Filter successful requests for excluded paths
                    is_success = 200 <= status_code < 400
                    return not is_success or self.log_excluded_on_error
                    
            return True  # Not an excluded path
        except (IndexError, ValueError, TypeError):
            return True  # Cannot parse reliably, let it pass


class LoggingService:
    """Enhanced logging service integrating handlers, filters, and formatters."""

    def __init__(self, app: Optional[Flask] = None):
        self.app: Optional[Flask] = app
        self.log_dir: Path = Path(LogConfig.DEFAULT_LOG_DIR)
        self.target_handlers: Dict[str, logging.Handler] = {}
        self.context_filter: Optional[ContextFilter] = None
        self.queue_listener: Optional[logging.handlers.QueueListener] = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize queue-based logging configuration."""
        self.app = app
        log_level_name = app.config.get('LOG_LEVEL', os.environ.get('LOG_LEVEL', 'INFO'))
        log_level = LogConfig.get_level(log_level_name)
        self.log_dir = Path(app.config.get('LOG_DIR', os.environ.get('LOG_DIR', LogConfig.DEFAULT_LOG_DIR)))
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create context filter for all handlers
        self.context_filter = ContextFilter(app_name=app.name or LogConfig.DEFAULT_COMPONENT_NAME)
        
        # Create target handlers
        self._create_target_handlers(log_level)
        
        # Set up queue-based logging
        self._setup_queue_logging(log_level)
        
        # Configure console logging
        self._setup_console_logging(log_level, app.debug)
        
        # Configure component levels
        self._configure_component_loggers()
        
        # Register shutdown hook
        atexit.register(self.stop_listener)
        
        logging.getLogger().info(
            f"Queue-based logging initialized. Level: {log_level_name}. "
            f"Log directory: {self.log_dir}"
        )

    def _create_target_handlers(self, log_level: int) -> None:
        """Create the target handlers for different log files."""
        # App log handler
        self.target_handlers['app'] = self._create_target_rotating_handler(
            filename=self.log_dir / LogConfig.APP_LOG,
            level=log_level,
            formatter=logging.Formatter(LogConfig.FILE_FORMAT, LogConfig.DATE_FORMAT),
            filters=[self.context_filter]
        )

        # Error log handler
        self.target_handlers['errors'] = self._create_target_rotating_handler(
            filename=self.log_dir / LogConfig.ERROR_LOG,
            level=logging.ERROR,
            formatter=logging.Formatter(LogConfig.ERROR_FILE_FORMAT, LogConfig.DATE_FORMAT),
            filters=[self.context_filter]
        )

        # Request log handler
        self.target_handlers['requests'] = self._create_target_rotating_handler(
            filename=self.log_dir / LogConfig.REQUEST_LOG,
            level=log_level,
            formatter=logging.Formatter(LogConfig.REQUEST_FILE_FORMAT, LogConfig.DATE_FORMAT),
            filters=[self.context_filter, RequestFilter()]
        )

    def _setup_queue_logging(self, log_level: int) -> None:
        """Set up queue-based logging system."""
        # Create a bounded queue to prevent memory issues
        queue_size = self.app.config.get('LOG_QUEUE_SIZE', LogConfig.DEFAULT_QUEUE_SIZE)
        log_queue = queue.Queue(queue_size)
        queue_handler = logging.handlers.QueueHandler(log_queue)

        # Configure root logger
        root_logger = logging.getLogger()
        self._clear_existing_handlers(root_logger)
        root_logger.setLevel(log_level)
        root_logger.addHandler(queue_handler)

        # Configure werkzeug logger
        werkzeug_logger = logging.getLogger('werkzeug')
        self._clear_existing_handlers(werkzeug_logger)
        werkzeug_logger.setLevel(log_level)
        werkzeug_logger.addHandler(queue_handler)
        werkzeug_logger.propagate = False

        # Create and start the queue listener
        self.queue_listener = logging.handlers.QueueListener(
            log_queue,
            self.target_handlers['app'],
            self.target_handlers['errors'],
            self.target_handlers['requests'],
            respect_handler_level=True
        )
        self.queue_listener.start()

    def _setup_console_logging(self, log_level: int, is_debug_mode: bool) -> None:
        """Set up console logging based on environment."""
        console_handler = None
        
        if is_debug_mode or os.environ.get('FLASK_ENV') != 'production':
            # Use colored logs in development
            console_handler = self._configure_colored_console_logs(log_level)
        else:
            # Use standard console handler in production
            console_handler = self._configure_standard_console_handler(log_level)
            
        # Add context and request filters to console handler if available
        if console_handler:
            console_handler.addFilter(self.context_filter)
            console_handler.addFilter(RequestFilter())

    def _clear_existing_handlers(self, logger: logging.Logger) -> None:
        """Remove all handlers from a logger."""
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    def stop_listener(self) -> None:
        """Stops the queue listener thread."""
        if self.queue_listener:
            logging.info("Stopping queue listener...")
            self.queue_listener.stop()
            self.queue_listener = None
            logging.info("Queue listener stopped.")

    def _create_target_rotating_handler(
        self, 
        filename: Path, 
        level: int, 
        formatter: logging.Formatter, 
        filters: Optional[List[logging.Filter]] = None
    ) -> logging.handlers.RotatingFileHandler:
        """Creates a RotatingFileHandler for the queue listener."""
        handler = logging.handlers.RotatingFileHandler(
            filename=filename,
            maxBytes=LogConfig.MAX_BYTES,
            backupCount=LogConfig.BACKUP_COUNT,
            encoding='utf-8'
        )
        handler.setFormatter(formatter)
        handler.setLevel(level)
        if filters:
            for f in filters:
                handler.addFilter(f)
        return handler

    def _configure_component_loggers(self) -> None:
        """Sets specific logging levels for different application components."""
        component_levels = {
            "zap_scanner": logging.INFO,
            "owasp_zap": logging.WARNING,
            "docker": logging.INFO,
            "performance": logging.INFO,
            "security": logging.INFO,
            "gpt4all": logging.INFO,
            "batch_analysis": logging.INFO,
        }
        for component, level in component_levels.items():
            logging.getLogger(component).setLevel(level)

    def _configure_colored_console_logs(self, level: int) -> Optional[logging.StreamHandler]:
        """Configures colored console logs and returns the handler."""
        try:
            # Clear existing handlers before adding colored logs
            root_logger = logging.getLogger()
            self._clear_existing_handlers(root_logger)
            
            # Install coloredlogs
            coloredlogs.install(
                level=level,
                logger=root_logger,
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
                    'request_id': {'color': 'blue'},
                    'component': {'color': 'yellow'}
                }
            )
            
            # Find and return the StreamHandler created by coloredlogs
            for handler in root_logger.handlers:
                if isinstance(handler, logging.StreamHandler):
                    return handler
                    
            return None
            
        except Exception as e:
            logging.error(f"Failed to initialize coloredlogs: {e}", exc_info=True)
            return self._configure_standard_console_handler(level)

    def _configure_standard_console_handler(self, level: int) -> logging.StreamHandler:
        """Creates a standard console handler."""
        console_formatter = logging.Formatter(LogConfig.CONSOLE_FORMAT, LogConfig.DATE_FORMAT)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        logging.getLogger().addHandler(console_handler)
        return console_handler

    def get_logger(self, name: str) -> logging.Logger:
        """Gets a logger instance."""
        return logging.getLogger(name)


# Middleware and Helper Functions

class CorsMiddleware:
    """Flask middleware for handling CORS headers."""
    
    def __init__(self, app: Flask):
        self.app = app
        self._register_handlers()
        
    def _register_handlers(self) -> None:
        """Register the after_request handler for CORS headers."""
        
        @self.app.after_request
        def add_cors_headers(response: Response) -> Response:
            """Add CORS headers to responses if enabled."""
            if not current_app.config.get('CORS_ENABLED', False):
                return response
                
            if isinstance(response, Response):
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
                
            return response


class RequestLoggerMiddleware:
    """Flask middleware for logging request details."""
    
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
        """Check if the current request path matches quiet endpoint patterns."""
        if not has_request_context():
            return False
        path = request.path
        return any(pattern in path for pattern in self.QUIET_ENDPOINTS_PATTERNS)

    def _register_handlers(self) -> None:
        """Register request processing handlers."""
        
        @self.app.before_request
        def before_request_logging() -> None:
            """Log request start and set up request context."""
            request_id = str(uuid.uuid4())[:self.REQUEST_ID_LENGTH]
            g.request_id = request_id
            g.start_time = time.time()
            g.is_quiet = self._is_quiet_endpoint()

            if g.is_quiet:
                return

            referrer = request.referrer or '-'
            user_agent = request.user_agent.string if request.user_agent else '-'
            
            logging.info(
                f"Request started: {request.method} {request.path} - "
                f"IP: {request.remote_addr} - Ref: {referrer[:50]}.. - Agent: {user_agent[:50]}.."
            )

        @self.app.after_request
        def after_request_logging(response: Response) -> Response:
            """Log request completion and add request ID header."""
            start_time = g.get('start_time', time.time())
            duration = time.time() - start_time
            request_id = g.get('request_id', ContextFilter.DEFAULT_REQUEST_ID)

            # Safely extract status code
            status_code = 0
            try:
                if isinstance(response, Response):
                    status_code = response.status_code
                    # Add request ID header
                    response.headers[self.REQUEST_ID_HEADER] = request_id
                elif isinstance(response, tuple) and len(response) > 1 and isinstance(response[1], int):
                    status_code = response[1]
                else:
                    status_code = getattr(response, 'status_code', 0)
            except Exception:
                pass

            is_quiet = g.get('is_quiet', False)
            is_error = status_code >= 400
            is_slow = duration > self.SLOW_REQUEST_THRESHOLD_SECONDS

            # Log based on conditions
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
            """Log unhandled exceptions and provide JSON response for AJAX requests."""
            start_time = g.get('start_time', time.time())
            duration = time.time() - start_time

            logging.exception(
                f"Unhandled exception during request: {request.method} {request.path} - "
                f"Error: {e!s} - Duration: {duration:.3f}s"
            )

            # Provide JSON response for AJAX requests
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
                
            raise e  # Re-raise for non-AJAX to get default Flask error page


def create_logger_for_component(component_name: str) -> logging.Logger:
    """Gets a logger instance for a specific application component."""
    return logging.getLogger(component_name)


def initialize_logging(app: Flask) -> LoggingService:
    """Initialize the enhanced logging system and request middleware."""
    # Disable default handlers
    app.logger.handlers.clear()
    app.logger.propagate = True
    
    # Initialize logging service
    logging_service = LoggingService()
    logging_service.init_app(app)
    
    # Initialize middleware
    RequestLoggerMiddleware(app)
    CorsMiddleware(app)
    
    app.extensions['logging_service'] = logging_service
    app.logger.info("Enhanced queue-based logging service initialized.")
    return logging_service