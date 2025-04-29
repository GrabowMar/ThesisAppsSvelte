# Standard Library Imports
import logging
import logging.handlers
import os
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Set, Union, Any, Tuple
import queue # Import the queue module
import atexit # For graceful listener shutdown

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
            from flask import jsonify # Local import
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
    CONSOLE_FORMAT: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    # Add request_id and component to file format
    FILE_FORMAT: str = "%(asctime)s [%(levelname)s] [%(request_id)s] [%(threadName)s] %(component)s.%(name)s: %(message)s"
    REQUEST_FILE_FORMAT: str = "%(asctime)s [%(levelname)s] [%(request_id)s] %(message)s"
    ERROR_FILE_FORMAT: str = "%(asctime)s [%(levelname)s] [%(request_id)s] %(component)s.%(name)s.%(funcName)s:%(lineno)d - %(message)s"
    DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    DEFAULT_LOG_DIR: str = "logs"
    REQUEST_LOG: str = "requests.log"
    ERROR_LOG: str = "errors.log"
    APP_LOG: str = "app.log"
    MAX_BYTES: int = 10 * 1024 * 1024
    BACKUP_COUNT: int = 5

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
        # Try filtering based on werkzeug log format
        is_werkzeug_log = (
            record.name == 'werkzeug' and
            hasattr(record, 'args') and
            isinstance(record.args, tuple) and
            len(record.args) >= 3 and
            isinstance(record.args[0], str) and
            record.args[0].startswith(('GET ', 'POST ', 'PUT ', 'DELETE ', 'PATCH ')) # Check for method
        )

        if is_werkzeug_log:
            try:
                # Simpler parsing assuming standard werkzeug format in args
                # args = ("GET /api/status HTTP/1.1", 200, ...)
                request_line = record.args[0]
                status_code = record.args[1]
                path = request_line.split()[1] # Get path from "GET /path HTTP/1.1"

                for excluded_path_pattern in self.excluded_paths:
                    if excluded_path_pattern in path:
                        is_success = 200 <= status_code < 400
                        if is_success:
                            return False # Filter success for excluded paths
                        elif self.log_excluded_on_error:
                            return True # Log errors for excluded paths
                        else:
                            return False # Filter errors too if configured

                return True # Not an excluded path
            except (IndexError, ValueError, TypeError):
                # Cannot parse reliably, let it pass
                return True

        # Don't filter non-werkzeug logs or logs not matching the expected format
        return True


class LoggingService:
    """Enhanced logging service integrating handlers, filters, and formatters."""

    def __init__(self, app: Optional[Flask] = None):
        self.app: Optional[Flask] = app
        self.log_dir: Path = Path(LogConfig.DEFAULT_LOG_DIR)
        # Store the actual handlers (targets for the listener)
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

        # --- Step 1: Create the target handlers (but don't add them to loggers yet) ---
        self.context_filter = ContextFilter(app_name=app.name or LogConfig.DEFAULT_COMPONENT_NAME)
        app_handler = self._create_target_rotating_handler(
            filename=self.log_dir / LogConfig.APP_LOG,
            level=log_level, # Will log records at this level or higher
            formatter=logging.Formatter(LogConfig.FILE_FORMAT, LogConfig.DATE_FORMAT),
            filters=[self.context_filter] # Add context filter
        )
        self.target_handlers['app'] = app_handler

        error_handler = self._create_target_rotating_handler(
            filename=self.log_dir / LogConfig.ERROR_LOG,
            level=logging.ERROR, # *Only* logs ERROR and CRITICAL
            formatter=logging.Formatter(LogConfig.ERROR_FILE_FORMAT, LogConfig.DATE_FORMAT),
            filters=[self.context_filter] # Add context filter
        )
        self.target_handlers['errors'] = error_handler

        request_handler = self._create_target_rotating_handler(
            filename=self.log_dir / LogConfig.REQUEST_LOG,
            level=log_level, # Logs werkzeug messages at this level or higher
            formatter=logging.Formatter(LogConfig.REQUEST_FILE_FORMAT, LogConfig.DATE_FORMAT),
            # Add RequestFilter *and* ContextFilter to this specific handler
            filters=[self.context_filter, RequestFilter()]
        )
        self.target_handlers['requests'] = request_handler

        # --- Step 2: Create the Log Queue and QueueHandler ---
        log_queue = queue.Queue(-1)
        queue_handler = logging.handlers.QueueHandler(log_queue)

        # --- Step 3: Configure Loggers to use QueueHandler ---
        # Configure root logger
        root_logger = logging.getLogger()
        # Remove default handlers Flask might add
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        root_logger.setLevel(log_level) # Set base level for root
        root_logger.addHandler(queue_handler) # Send all root logs to the queue

        # Configure werkzeug logger
        werkzeug_logger = logging.getLogger('werkzeug')
        for handler in werkzeug_logger.handlers[:]:
            werkzeug_logger.removeHandler(handler)
        werkzeug_logger.setLevel(log_level)
        werkzeug_logger.addHandler(queue_handler) # Send werkzeug logs to the queue
        werkzeug_logger.propagate = False # IMPORTANT: Prevent duplication to root

        # --- Step 4: Configure Console Handler (Does NOT use the queue) ---
        console_handlers = []
        if app.debug or os.environ.get('FLASK_ENV') != 'production':
             # Setup coloredlogs; it attaches its own handler to the root logger
             console_handler = self._configure_colored_console_logs(log_level)
             if console_handler:
                 console_handlers.append(console_handler)
        else:
             # Add standard console handler directly to the root logger
             console_handler = self._configure_standard_console_handler(log_level)
             if console_handler:
                 root_logger.addHandler(console_handler) # Add directly
                 console_handlers.append(console_handler)

        # Apply ContextFilter and RequestFilter to console handlers
        request_filter_console = RequestFilter() # Separate instance for console
        for ch in console_handlers:
             if self.context_filter and self.context_filter not in ch.filters:
                 ch.addFilter(self.context_filter)
             if request_filter_console not in ch.filters:
                 ch.addFilter(request_filter_console)

        # --- Step 5: Create and Start the QueueListener ---
        # The listener pulls from the queue and sends to the *correct* target file handlers
        self.queue_listener = logging.handlers.QueueListener(
            log_queue,
            # Handlers that the listener will dispatch to:
            self.target_handlers['app'],
            self.target_handlers['errors'],
            self.target_handlers['requests'],
            respect_handler_level=True # IMPORTANT: Ensures handler levels/filters are checked
        )
        self.queue_listener.start()

        # Register listener stop for graceful shutdown
        atexit.register(self.stop_listener)

        # Configure component levels (this just sets level, propagation sends to root -> queue)
        self._configure_component_loggers()

        root_logger.info(f"Queue-based logging initialized. Level: {log_level_name}. Log directory: {self.log_dir}")

    def stop_listener(self):
        """Stops the queue listener thread."""
        if self.queue_listener:
            logging.info("Stopping queue listener...")
            self.queue_listener.stop()
            self.queue_listener = None # Indicate stopped
            logging.info("Queue listener stopped.")

    def _create_target_rotating_handler(self, filename: Path, level: int, formatter: logging.Formatter, filters: Optional[List[logging.Filter]] = None) -> logging.handlers.RotatingFileHandler:
        """Creates a RotatingFileHandler intended to be used by the QueueListener."""
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
            # Ensure propagation is True (default) so logs reach the root logger -> QueueHandler

    def _configure_colored_console_logs(self, level: int) -> Optional[logging.StreamHandler]:
        """Configures colored console logs and returns the handler created."""
        try:
            # Clear existing root handlers before applying coloredlogs if needed
            root_logger = logging.getLogger()
            console_handler_found = None
            for handler in root_logger.handlers[:]:
                if isinstance(handler, logging.StreamHandler):
                    # Assume this might be a default handler or one from a previous init
                    # Keep track of it to add filters later
                    console_handler_found = handler
                    # Don't remove if we want coloredlogs to potentially replace/style it
                # Keep the QueueHandler
                if not isinstance(handler, logging.handlers.QueueHandler) and not isinstance(handler, logging.StreamHandler):
                     root_logger.removeHandler(handler)

            coloredlogs.install(
                level=level,
                logger=root_logger, # Apply to root
                fmt=LogConfig.CONSOLE_FORMAT,
                datefmt=LogConfig.DATE_FORMAT,
                level_styles={
                    'debug': {'color': 'blue'}, 'info': {'color': 'green'},
                    'warning': {'color': 'yellow', 'bold': True},
                    'error': {'color': 'red', 'bold': True},
                    'critical': {'color': 'red', 'bold': True, 'background': 'white'}
                },
                field_styles={
                    'asctime': {'color': 'green'}, 'levelname': {'color': 'cyan', 'bold': True},
                    'name': {'color': 'magenta'}, 'request_id': {'color': 'blue'},
                    'component': {'color': 'yellow'}
                }
            )
             # Find the handler created or modified by coloredlogs
            final_console_handler = None
            for handler in root_logger.handlers:
                 if isinstance(handler, logging.StreamHandler):
                     final_console_handler = handler
                     break
            return final_console_handler
        except Exception as e:
            logging.error(f"Failed to initialize coloredlogs: {e}", exc_info=True)
            return None # Fallback to standard console handler if coloredlogs fails

    def _configure_standard_console_handler(self, level: int) -> Optional[logging.StreamHandler]:
        """Adds a standard, non-colored console handler directly to root logger."""
        console_formatter = logging.Formatter(LogConfig.CONSOLE_FORMAT, LogConfig.DATE_FORMAT)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        # Filters (ContextFilter, RequestFilter) will be added in init_app
        return console_handler

    def get_logger(self, name: str) -> logging.Logger:
        """Gets a logger instance."""
        return logging.getLogger(name)


# --- Middleware and Helper Functions (Largely Unchanged) ---

class EnhancedRequestLoggerMiddleware:
    """Flask middleware hooks to log request start, end, and errors."""
    SLOW_REQUEST_THRESHOLD_SECONDS: float = 1.0
    REQUEST_ID_HEADER: str = 'X-Request-ID'
    AJAX_HEADER_CHECK: Tuple[str, str] = ('X-Requested-With', 'XMLHttpRequest')
    REQUEST_ID_LENGTH: int = 8
    QUIET_ENDPOINTS_PATTERNS: Set[str] = {
        '/static/', '/api/status', '/api/health', '/api/container/'
    }

    def __init__(self, app: Flask):
        self.app = app
        # Get logger via standard method, context is added by filter
        self.logger = logging.getLogger(__name__) # Use module name for middleware logs
        self._register_handlers()

    def _is_quiet_endpoint(self) -> bool:
        if not has_request_context(): return False
        path = request.path
        return any(pattern in path for pattern in self.QUIET_ENDPOINTS_PATTERNS)

    def _register_handlers(self) -> None:
        """Registers the before_request, after_request, and errorhandler methods."""

        @self.app.before_request
        def before_request_logging() -> None:
            """Log the start of a request and set up context."""
            request_id = str(uuid.uuid4())[:self.REQUEST_ID_LENGTH]
            g.request_id = request_id
            g.start_time = time.time()
            g.is_quiet = self._is_quiet_endpoint()

            if g.is_quiet: return

            referrer = request.referrer or '-'
            user_agent = request.user_agent.string if request.user_agent else '-'
            # Use root logger - context filter adds request_id, listener sends to app.log
            logging.info(
                f"Request started: {request.method} {request.path} - "
                f"IP: {request.remote_addr} - Ref: {referrer[:50]}.. - Agent: {user_agent[:50]}.."
            )

        @self.app.after_request
        def after_request_logging(response: Any) -> Any:
            """Log the completion of a request, duration, and add headers."""
            start_time = g.get('start_time', time.time())
            duration = time.time() - start_time
            request_id = g.get('request_id', ContextFilter.DEFAULT_REQUEST_ID)

            status_code = 0
            is_response_object = isinstance(response, Response)

            if is_response_object:
                response.headers[self.REQUEST_ID_HEADER] = request_id
                status_code = response.status_code
            elif isinstance(response, tuple) and len(response) > 1 and isinstance(response[1], int):
                # Handle cases where view returns (data, status_code)
                status_code = response[1]
            else:
                 # Try to infer from Werkzeug response object if possible, fallback to 0
                 try:
                     status_code = getattr(response,'status_code',0)
                 except Exception:
                     pass # Keep status_code 0


            is_quiet = g.get('is_quiet', False)
            is_error = status_code >= 400
            is_slow = duration > self.SLOW_REQUEST_THRESHOLD_SECONDS

            # Enhanced logging condition: Log if error, slow, or not quiet endpoint
            if is_error or is_slow or not is_quiet:
                log_level = logging.WARNING if is_error else logging.INFO
                status_msg = f"{status_code}"
                if is_slow: status_msg += " [SLOW]"

                # Check if werkzeug is likely to log this already
                # Werkzeug logs usually have level INFO for success, WARNING for errors
                werkzeug_will_log = not is_quiet or is_error

                # Log via root logger if not quiet, or if slow/error (provides more context)
                # Avoid double-logging simple successful requests handled by werkzeug filter
                if (is_error or is_slow) or not is_quiet:
                     # Log extra details not typically in werkzeug log
                     logging.log( # Use logging.log for dynamic level
                          log_level,
                          f"Request finished: {request.method} {request.path} - "
                          f"Status: {status_msg} - Duration: {duration:.3f}s"
                     )

            # Add CORS headers if enabled
            if current_app.config.get('CORS_ENABLED', False) and is_response_object:
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'

            return response

        @self.app.errorhandler(Exception)
        def handle_exception_logging(e: Exception) -> Any:
            """Log unhandled exceptions."""
            start_time = g.get('start_time', time.time())
            duration = time.time() - start_time
            request_id = g.get('request_id', ContextFilter.DEFAULT_REQUEST_ID)

            # Log exception via root logger - context filter adds request_id, listener sends to error.log
            logging.exception( # Use logging.exception to include traceback
                f"Unhandled exception during request: {request.method} {request.path} - "
                f"Error: {e!s} - Duration: {duration:.3f}s"
            )

            header_name, header_value = self.AJAX_HEADER_CHECK
            if request.headers.get(header_name) == header_value:
                status_code = e.code if isinstance(e, HTTPException) else 500
                api_response = APIResponse(
                    success=False, error=str(e),
                    message="An internal server error occurred.", code=status_code
                )
                return api_response.to_response()
            raise e # Re-raise for non-AJAX to get default Flask error page

def create_logger_for_component(component_name: str) -> logging.Logger:
    """Gets a logger instance for a specific application component."""
    return logging.getLogger(component_name)

def initialize_logging(app: Flask) -> LoggingService:
    """Initializes the enhanced, queue-based logging system."""
    # Disable default handlers early
    app.logger.handlers.clear()
    app.logger.propagate = True # Let Flask app logs go to our root logger

    logging_service = LoggingService()
    logging_service.init_app(app)

    EnhancedRequestLoggerMiddleware(app)

    app.extensions['logging_service'] = logging_service
    app.logger.info("Enhanced queue-based logging service initialized.") # Use app logger
    return logging_service