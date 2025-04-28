# performance_analysis.py

import json
import logging
import os
import re
import tempfile # Still needed for run_test_cli's _create_temp_locustfile
# *** ADD timedelta and dataclasses imports ***
from datetime import datetime, timedelta # <--- IMPORTED TIMEDELTA HERE
from dataclasses import dataclass, field, asdict # <--- IMPORTED DATACLASSES HERE
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Callable, Tuple, TypedDict
import socket
import io # For capturing graph data in memory if needed

# For direct Locust control
from locust import HttpUser, task, constant, events, between
from locust.env import Environment
from locust.stats import stats_printer, StatsEntry, RequestStats, sort_stats # Import RequestStats
from locust.runners import Runner, LocalRunner
import gevent
# Still used for graph generation (optional) and CSV parsing in CLI mode
import pandas as pd
import matplotlib.pyplot as plt
# import requests # Not directly used here

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EndpointStats:
    """Statistics for a single endpoint."""
    name: str
    method: str
    num_requests: int = 0
    num_failures: int = 0
    median_response_time: float = 0
    avg_response_time: float = 0
    min_response_time: float = 0
    max_response_time: float = 0
    avg_content_length: float = 0
    current_rps: float = 0
    current_fail_per_sec: float = 0
    percentiles: Dict[str, float] = field(default_factory=dict)


@dataclass
class ErrorStats:
    """Error statistics for test run."""
    error_type: str # Changed from error_type to match Locust's 'error' key
    count: int
    endpoint: str # 'name' in Locust stats
    method: str
    description: str = "" # 'error' in Locust stats


@dataclass
class GraphInfo(TypedDict):
    """Information about a generated graph."""
    name: str
    url: str

@dataclass
class PerformanceResult:
    """Comprehensive performance test results."""
    total_requests: int
    total_failures: int
    avg_response_time: float
    median_response_time: float
    requests_per_sec: float
    start_time: str
    end_time: str
    duration: int # Duration in seconds
    endpoints: List[EndpointStats] = field(default_factory=list)
    errors: List[ErrorStats] = field(default_factory=list)
    percentile_95: float = 0
    percentile_99: float = 0
    user_count: int = 0
    spawn_rate: int = 0
    test_name: str = "" # Added to store the test name
    host: str = ""      # Added to store the target host
    graph_urls: List[GraphInfo] = field(default_factory=list) # Store graph URLs if generated

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        # Ensure nested dataclasses are also converted
        result['endpoints'] = [asdict(endpoint) for endpoint in self.endpoints]
        result['errors'] = [asdict(error) for error in self.errors]
        result['graph_urls'] = list(self.graph_urls) # Ensure list type if needed
        return result

    def save_json(self, file_path: Union[str, Path]) -> None:
        """Save results as JSON."""
        # Ensure the directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Performance results saved to {file_path}")


class UserGenerator:
    """Generates Locust user classes dynamically."""

    @staticmethod
    def create_http_user(host: str, endpoints: List[Dict[str, Any]]) -> type:
        """
        Create a dynamic HttpUser class for testing specific endpoints.

        Args:
            host: Target host URL
            endpoints: List of endpoint configurations
                Example: [
                    {'path': '/api/users', 'method': 'GET', 'weight': 10},
                    {'path': '/api/products', 'method': 'POST', 'weight': 5,
                     'data': {'name': 'Product'}, 'headers': {'Content-Type': 'application/json'}}
                ]

        Returns:
            Dynamic HttpUser class
        """
        class_attrs = {
            'host': host,
            'wait_time': between(1, 3)  # Default wait time between tasks
        }

        # Create task methods for each endpoint
        for i, endpoint in enumerate(endpoints):
            path = endpoint['path']
            method = endpoint.get('method', 'GET').lower()
            weight = endpoint.get('weight', 1)
            # Use a more descriptive name if available, otherwise index
            # Sanitize path for use in function name
            ep_name_part = re.sub(r"[^a-zA-Z0-9_]", "_", path.strip('/')).lower()
            if not ep_name_part: ep_name_part = "root" # Handle root path case
            task_name = endpoint.get('name', f"task_{method}_{ep_name_part}_{i}")

            # Create the task function using a closure to capture endpoint config
            def create_task_fn(captured_path, captured_method, captured_endpoint_config):
                def task_fn(self: HttpUser): # Add type hint for self
                    # Extract request parameters from endpoint configuration
                    kwargs = {}
                    # Process potential request arguments
                    for param in ['params', 'data', 'json', 'headers', 'files']:
                        if param in captured_endpoint_config:
                            kwargs[param] = captured_endpoint_config[param]

                    # Set custom name for the request stats grouping (defaults to path)
                    request_name = captured_endpoint_config.get('request_name', captured_path)
                    kwargs['name'] = request_name

                    # Execute the request with the specified method
                    request_method_func = getattr(self.client, captured_method)
                    # Use 'with' context manager for automatic handling
                    with request_method_func(captured_path, catch_response=True, **kwargs) as response:
                        # Apply custom validators if provided
                        validators = captured_endpoint_config.get('validators')
                        if validators and callable(validators):
                            try:
                                validators(response)
                            except Exception as val_err:
                                # Report validation failure as a Locust failure
                                response.failure(f"Validator failed: {val_err}")
                        # Basic validation if no custom validator
                        elif not response.ok: # Use response.ok for simplicity (covers 4xx and 5xx)
                            # Keep failure message concise for better aggregation
                            response.failure(f"HTTP {response.status_code}")

                # Set the function name and docstring for clarity in Locust UI/logs
                task_fn.__name__ = task_name
                task_fn.__doc__ = f"Task for {captured_method.upper()} {captured_path}"
                return task_fn

            # Create and decorate the task function
            task_fn_instance = create_task_fn(path, method, endpoint)
            decorated_task = task(weight)(task_fn_instance)
            class_attrs[task_name] = decorated_task # Add decorated task to class attributes

        # Create and return the dynamic class using type()
        DynamicUserClass = type('DynamicHttpUser', (HttpUser,), class_attrs)
        logger.debug(f"Created DynamicHttpUser class with tasks: {list(class_attrs.keys())}")
        return DynamicUserClass


class LocustPerformanceTester:
    """
    Enhanced framework for performance testing using Locust. Runs tests
    programmatically and returns results directly.
    """

    def __init__(self, output_dir: Union[str, Path], static_url_path: str = "/static"):
        """
        Initialize the PerformanceTester.

        Args:
            output_dir: Base directory for storing test reports and data (e.g., graphs, consolidated JSON).
                        This should correspond to the Flask static folder or a subfolder within it.
            static_url_path: The URL path configured in Flask for static files (e.g., '/static').
                             Used to construct correct URLs for graphs.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Ensure static_url_path starts with / and doesn't end with /
        self.static_url_path = "/" + static_url_path.strip('/')
        logger.info(f"PerformanceTester initialized. Output dir: {self.output_dir}, Static URL path: {self.static_url_path}")
        self.current_test_dir: Optional[Path] = None
        self.environment: Optional[Environment] = None
        self.runner: Optional[Runner] = None

    def _save_consolidated_results(self,
                                   result: PerformanceResult,
                                   model: str,
                                   app_num: int) -> str:
        """
        Save a consolidated JSON result file in the model/app directory
        within the performance_reports subdirectory.

        Args:
            result: PerformanceResult object containing test results
            model: Model name
            app_num: App number

        Returns:
            Path to the saved JSON file as a string, or empty string on failure.
        """
        try:
            # Results go into 'output_dir/performance_reports/model/appN'
            base_reports_dir = self.output_dir / "performance_reports"
            app_dir = base_reports_dir / model / f"app{app_num}"
            app_dir.mkdir(parents=True, exist_ok=True)

            # Define the result file path (hidden file)
            result_file = app_dir / ".locust_result.json"

            # Use the result object's save method
            result.save_json(result_file)

            # Add metadata (optional, could be part of PerformanceResult itself)
            # result_dict = result.to_dict() ... add metadata ... save json
            # For simplicity, save_json handles the core data.

            return str(result_file)
        except Exception as e:
            logger.exception(f"Error saving consolidated results for {model}/app{app_num}: {e}")
            return ""

    def _setup_test_directory(self, test_name: str) -> Path:
        """
        Set up a directory for the current test run artifacts (like graphs).
        Directory is created inside self.output_dir / "performance_reports".

        Args:
            test_name: Name to identify this test run (should include timestamp)

        Returns:
            Path to the test directory
        """
        # Ensure test_name is filesystem-safe (replace invalid chars)
        safe_test_name = re.sub(r'[<>:"/\\|?*\s]+', '_', test_name)
        test_dir = self.output_dir / "performance_reports" / safe_test_name
        test_dir.mkdir(parents=True, exist_ok=True)
        self.current_test_dir = test_dir
        logger.info(f"Test artifacts directory set up at: {test_dir}")
        return test_dir

    def create_user_class(self, host: str, endpoints: List[Dict[str, Any]]) -> type:
        """
        Create a custom user class for the test using UserGenerator.

        Args:
            host: Target host URL
            endpoints: List of endpoint configurations

        Returns:
            HttpUser class for testing
        """
        user_class = UserGenerator.create_http_user(host, endpoints)
        return user_class

    def run_test_cli(
        self,
        test_name: str,
        host: str,
        locustfile_path: Optional[str] = None,
        endpoints: Optional[List[Dict[str, Any]]] = None,
        user_count: int = 10,
        spawn_rate: int = 1,
        run_time: str = "30s",
        headless: bool = True,
        workers: int = 0,
        tags: Optional[List[str]] = None,
        html_report: bool = True, # Controls Locust's HTML report file
        model: Optional[str] = None,
        app_num: Optional[int] = None
    ) -> Optional[PerformanceResult]:
        """
        Run a Locust test via command line subprocess.
        NOTE: This method relies on file output (CSV, potentially HTML).
              Use run_test_library for direct frontend integration.

        Args:
            test_name: Name for the test (timestamp will be added if missing).
            host: Target host URL.
            locustfile_path: Path to a custom locustfile (optional).
            endpoints: List of endpoint configs (if no locustfile).
            user_count: Number of concurrent users.
            spawn_rate: Rate users are spawned per second.
            run_time: Duration string (e.g., "30s", "5m", "1h").
            headless: Run Locust without the web UI.
            workers: Number of worker processes for distributed mode (0 for local).
            tags: List of tags to filter tasks/User classes.
            html_report: Generate Locust's built-in HTML report file.
            model: Model name for saving consolidated results.
            app_num: App number for saving consolidated results.

        Returns:
            PerformanceResult object parsed from CSV files, or None if parsing fails or test errors.
        """
        import subprocess
        import csv # Needed for parsing results here

        # Add timestamp if not already present in test_name
        if not re.search(r'_\d{8}_\d{6}$', test_name):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            full_test_name = f"{test_name}_{timestamp}"
        else:
            full_test_name = test_name

        # Set up test directory within 'performance_reports'
        test_dir = self._setup_test_directory(full_test_name)
        csv_prefix = str(test_dir / "stats") # Save CSVs inside the test dir

        # --- Temporary locustfile generation ---
        temp_locustfile = None
        if not locustfile_path and endpoints:
            try:
                temp_locustfile = self._create_temp_locustfile(host, endpoints, test_dir)
                locustfile_path = temp_locustfile
            except Exception as temp_err:
                logger.error(f"Failed to create temporary locustfile: {temp_err}")
                return None
        elif not locustfile_path:
             logger.error("No locustfile or endpoints provided for CLI test.")
             return None

        try:
            # Build the Locust command
            cmd = ["locust", "-f", locustfile_path, "--host", host]

            if headless:
                cmd.extend(["--headless", "--users", str(user_count),
                            "--spawn-rate", str(spawn_rate), "--run-time", run_time])
            else:
                 # Add options for running with UI if needed (e.g., port)
                 # cmd.extend(["--web-host", "127.0.0.1", "--web-port", "8089"])
                 pass # Default UI runs on 8089

            # Add CSV output options (necessary for this method's parsing)
            cmd.extend(["--csv", csv_prefix, "--csv-full-history"]) # Include history

            # Add Locust's HTML report if requested
            if html_report:
                 # Ensure filename is safe and inside test_dir
                 html_file_path = test_dir / f"{test_dir.name}_locust_report.html"
                 cmd.extend(["--html", str(html_file_path)])

            # Add worker/master options if distributed
            if workers > 0:
                # Requires running worker processes separately
                cmd.extend(["--master", "--expect-workers", str(workers)])

            # Add tags if specified
            if tags:
                cmd.extend(["--tags"] + tags) # Pass tags correctly

            # Run the command
            logger.info(f"Running Locust command: {' '.join(cmd)}")
            start_time = datetime.now()

            # Execute the subprocess
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8', # Specify encoding
                check=False # Check return code manually
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"Locust process finished in {duration:.2f}s with exit code {process.returncode}")

            # Save command output regardless of exit code
            output_file = test_dir / "locust_output.txt"
            with open(output_file, "w", encoding='utf-8') as f:
                f.write("--- STDOUT ---\n")
                f.write(process.stdout if process.stdout else "[No stdout]")
                f.write("\n\n--- STDERR ---\n")
                f.write(process.stderr if process.stderr else "[No stderr]")
            logger.info(f"Locust output saved to {output_file}")


            # Check for failures after saving logs
            if process.returncode != 0:
                logger.error(f"Locust test failed with exit code {process.returncode}.")
                # Error output already saved above
                return None # Indicate failure clearly

            # --- Parse the CSV results ---
            stats_file = f"{csv_prefix}_stats.csv"
            failures_file = f"{csv_prefix}_failures.csv"
            history_file = f"{csv_prefix}_stats_history.csv" # Correct history file name

            if not Path(stats_file).exists():
                logger.error(f"Locust completed but stats CSV not found: {stats_file}")
                return None

            result = self._parse_csv_results(
                stats_file=stats_file,
                failures_file=failures_file,
                start_time=start_time,
                end_time=end_time,
                user_count=user_count,
                spawn_rate=spawn_rate
            )
            if result is None: # Check if parsing failed
                 logger.error("Failed to parse CSV results.")
                 return None

            result.test_name = full_test_name
            result.host = host

            # Generate graphs from CSV history (optional)
            graph_infos = self._generate_graphs_from_csv(history_file, test_dir)
            result.graph_urls = graph_infos # Add graph URLs if generated

            # Save consolidated results if model and app_num are provided
            if model and app_num:
                self._save_consolidated_results(result, model, app_num)

            return result

        except FileNotFoundError as e:
             logger.error(f"Locust command not found or file path error: {e}")
             return None
        except Exception as e:
             logger.exception(f"Unhandled error running Locust CLI test '{full_test_name}': {e}")
             return None
        finally:
            # Clean up the temporary locustfile if created
            if temp_locustfile and os.path.exists(temp_locustfile):
                try:
                    os.unlink(temp_locustfile)
                    logger.debug(f"Deleted temporary locustfile: {temp_locustfile}")
                except Exception as e_unlink:
                    logger.warning(f"Failed to delete temporary file {temp_locustfile}: {e_unlink}")
    # --- End run_test_cli ---

    def _extract_stats_from_environment(
        self,
        stats: RequestStats,
        start_time: datetime,
        end_time: datetime,
        user_count: int,
        spawn_rate: int
    ) -> PerformanceResult:
        """
        Extracts statistics directly from the Locust Stats object after a library run.

        Args:
            stats: The Locust RequestStats object from environment.stats.
            start_time: Test start time.
            end_time: Test end time.
            user_count: Number of users targetted.
            spawn_rate: User spawn rate targetted.

        Returns:
            PerformanceResult object populated with stats.
        """
        logger.info("Extracting stats directly from Locust environment...")
        endpoints: List[EndpointStats] = []
        errors: List[ErrorStats] = []

        # Process individual endpoint stats (entries in the stats object)
        # Use sort_stats to ensure 'Aggregated' is last if present (though we handle total separately)
        sorted_entries = sort_stats(stats.entries)
        for entry in sorted_entries:
            # Skip the Aggregated entry here, handle it separately via stats.total
            if entry.name == "Aggregated":
                continue

            # Calculate percentiles directly
            percentiles_dict = {}
            try:
                 # Use the defined percentiles to report
                 for p in RequestStats.PERCENTILES_TO_REPORT:
                      percentile_value = entry.get_response_time_percentile(p)
                      # Format key as "50", "95", etc.
                      percentiles_dict[f"{p*100:.0f}"] = percentile_value if percentile_value is not None else 0.0
            except Exception as p_err:
                 logger.warning(f"Could not calculate percentiles for {entry.name}: {p_err}")


            ep_stats = EndpointStats(
                name=entry.name,
                method=entry.method or "N/A", # Handle case where method might be None
                num_requests=entry.num_requests,
                num_failures=entry.num_failures,
                median_response_time=entry.median_response_time or 0.0,
                avg_response_time=entry.avg_response_time or 0.0,
                min_response_time=entry.min_response_time if entry.num_requests > 0 and entry.min_response_time is not None else 0.0,
                max_response_time=entry.max_response_time or 0.0,
                avg_content_length=entry.avg_content_length or 0.0,
                current_rps=entry.current_rps or 0.0,
                current_fail_per_sec=entry.current_fail_per_sec or 0.0,
                percentiles=percentiles_dict
            )
            endpoints.append(ep_stats)

        # Process errors recorded in stats.errors
        for error_key, error_entry in stats.errors.items():
            # error_key is usually the exception string or similar identifier
            # error_entry contains method, name, error details, occurrences
            err_stats = ErrorStats(
                error_type=str(error_entry.error), # The actual error/exception string
                count=error_entry.occurrences,
                endpoint=error_entry.name or "N/A", # Endpoint name where error occurred
                method=error_entry.method or "N/A", # Method used
                description=str(error_entry.error) # Can be same as error_type or more specific if needed
            )
            errors.append(err_stats)

        # Get total aggregated stats from stats.total
        total_entry = stats.total
        duration_sec = max((end_time - start_time).total_seconds(), 0.1) # Avoid division by zero

        # Calculate overall percentiles
        total_p95 = total_entry.get_response_time_percentile(0.95) or 0.0
        total_p99 = total_entry.get_response_time_percentile(0.99) or 0.0

        result = PerformanceResult(
            total_requests=total_entry.num_requests,
            total_failures=total_entry.num_failures,
            avg_response_time=total_entry.avg_response_time or 0.0,
            median_response_time=total_entry.median_response_time or 0.0,
            # Calculate total RPS based on duration for accuracy
            requests_per_sec=(total_entry.num_requests / duration_sec),
            start_time=start_time.strftime("%Y-%m-%d %H:%M:%S"),
            end_time=end_time.strftime("%Y-%m-%d %H:%M:%S"),
            duration=int(duration_sec),
            endpoints=endpoints,
            errors=errors,
            percentile_95=total_p95,
            percentile_99=total_p99,
            user_count=user_count, # Target user count
            spawn_rate=spawn_rate
        )
        logger.info(f"Stats extraction complete. Total Requests: {result.total_requests}, Failures: {result.total_failures}")
        return result

    def run_test_library(
        self,
        test_name: str,
        host: str,
        user_class: Optional[type] = None,
        endpoints: Optional[List[Dict[str, Any]]] = None,
        user_count: int = 10,
        spawn_rate: int = 1,
        run_time: int = 30, # Duration in seconds
        generate_graphs: bool = True, # Control graph generation
        on_start_callback: Optional[Callable[[Environment], None]] = None, # Type hint for callback
        on_stop_callback: Optional[Callable[[Environment], None]] = None, # Type hint for callback
        model: Optional[str] = None, # For consolidated results
        app_num: Optional[int] = None # For consolidated results

    ) -> PerformanceResult:
        """
        Run a Locust test using the library approach and return results directly.

        Args:
            test_name: Base name for the test (timestamp will be added).
            host: Target host URL.
            user_class: Custom user class (optional).
            endpoints: List of endpoint configurations (if no user_class).
            user_count: Number of concurrent users.
            spawn_rate: Rate at which users are spawned per second.
            run_time: Duration of the test in seconds.
            generate_graphs: Whether to generate and save performance graphs.
            on_start_callback: Function to call when the test starts (receives environment).
            on_stop_callback: Function to call when the test stops (receives environment).
            model: Model name for saving consolidated results.
            app_num: App number for saving consolidated results.

        Returns:
            PerformanceResult object containing the test metrics.
        Raises:
            ValueError: If neither user_class nor endpoints are provided.
            RuntimeError: If the Locust runner fails to initialize or stats are missing.
        """
        # Add timestamp to test name for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_test_name = f"{test_name}_{timestamp}"

        # Set up test directory for potential artifacts like graphs
        test_dir = self._setup_test_directory(full_test_name)

        # Create user class if needed
        if user_class is None and endpoints:
            user_class = self.create_user_class(host, endpoints)

        if user_class is None:
            raise ValueError("Either user_class or endpoints must be provided")

        # --- Setup Locust Environment ---
        # Ensure clean state if run multiple times
        self.environment = None
        self.runner = None

        # Initialize Locust environment programmatically
        # stats_history_enabled=True is default and needed for graphs from history
        self.environment = Environment(user_classes=[user_class], host=host, catch_exceptions=True)
        self.environment.create_local_runner()
        # self.environment.create_web_ui("127.0.0.1", 0) # Optional: Start web UI on a free port for monitoring

        if not self.environment.runner:
             raise RuntimeError("Failed to create Locust runner.")
        self.runner = self.environment.runner


        # --- Setup Event Handlers ---
        # Use a dictionary attached to the environment to store custom state like start time
        self.environment.custom_data = {}

        @events.test_start.add_listener
        def on_test_start(environment: Environment, **kwargs):
            # Attach start time directly to the environment object
            environment.custom_data['start_time'] = datetime.now()
            logger.info(f"Test '{full_test_name}' starting at {environment.custom_data['start_time'].isoformat()} with {user_count} users at {spawn_rate} users/s on host {environment.host}")
            if on_start_callback:
                try:
                    on_start_callback(environment)
                except Exception as cb_err:
                    logger.error(f"Error in on_start_callback: {cb_err}", exc_info=True)

        @events.test_stop.add_listener
        def on_test_stop(environment: Environment, **kwargs):
            logger.info(f"Test '{full_test_name}' stopping...")
            if on_stop_callback:
                 try:
                     on_stop_callback(environment)
                 except Exception as cb_err:
                     logger.error(f"Error in on_stop_callback: {cb_err}", exc_info=True)

        # --- Run the Test ---
        # Start the test without blocking
        self.runner.start(user_count, spawn_rate=spawn_rate)
        logger.info(f"Locust runner started. Waiting for {run_time} seconds...")

        # Schedule the test to stop after run_time seconds using gevent
        stopper_greenlet = None
        try:
            def stopper():
                gevent.sleep(run_time) # Wait for the specified duration
                logger.info(f"Run time ({run_time}s) elapsed. Stopping runner for test '{full_test_name}'...")
                if self.runner:
                    self.runner.quit() # Signal the runner to stop users and shut down
                    logger.info("Runner quit signal sent.")
                else:
                     logger.warning("Stopper executed but runner was None.")

            stopper_greenlet = gevent.spawn(stopper)

            # Optional: Print stats periodically to console during the run
            # stats_printer_greenlet = gevent.spawn(stats_printer(self.environment.stats))

            # Wait for the runner to finish (either by time via stopper or external stop)
            self.runner.greenlet.join() # Wait for the main run loop greenlet to exit
            logger.info("Runner greenlet joined (test run finished).")

        except KeyboardInterrupt:
             logger.warning("Test run interrupted by user (KeyboardInterrupt). Stopping runner...")
             if self.runner: self.runner.quit()
             # Allow finally block to handle cleanup
        except Exception as run_err:
             logger.exception(f"Error during runner execution or join for test '{full_test_name}': {run_err}")
             if self.runner: self.runner.quit() # Attempt graceful shutdown on error
             # Re-raise or handle as appropriate
             raise RuntimeError(f"Locust run failed: {run_err}") from run_err
        finally:
             # Clean up the stopper greenlet if it exists and hasn't finished
             if stopper_greenlet and not stopper_greenlet.dead:
                 stopper_greenlet.kill(block=False)
                 logger.debug("Stopper greenlet killed.")
             # if stats_printer_greenlet and not stats_printer_greenlet.dead:
             #     stats_printer_greenlet.kill(block=False)

        end_time = datetime.now()
        logger.info(f"Test '{full_test_name}' finished execution at {end_time.isoformat()}")

        # Retrieve start time from the environment's custom data
        start_time = self.environment.custom_data.get('start_time')

        if start_time is None:
             # This should ideally not happen with the new approach
             logger.warning("Start time not found on environment.custom_data! Using approximate start based on end time and duration.")
             # Fallback calculation (timedelta is imported now)
             start_time = end_time - timedelta(seconds=run_time)
        else:
             logger.info(f"Actual test start time recorded: {start_time.isoformat()}")


        # --- Process Results ---
        if not self.environment or not self.environment.stats:
            # This indicates a major issue if stats aren't available after run
            raise RuntimeError("Locust environment or stats object not available after test run.")

        # Extract results directly from the environment stats object
        result = self._extract_stats_from_environment(
            stats=self.environment.stats,
            start_time=start_time,
            end_time=end_time,
            user_count=user_count, # Use the target count
            spawn_rate=spawn_rate
        )
        result.test_name = full_test_name # Add test name and host to result object
        result.host = host

        # Generate graphs if requested and save them to the test directory
        if generate_graphs:
            try:
                # Use history if available (requires stats_history_enabled=True, default)
                graph_infos = self._generate_graphs_from_history(self.environment.stats.history, test_dir)
                result.graph_urls = graph_infos
            except Exception as graph_err:
                 logger.error(f"Failed to generate graphs for test '{full_test_name}': {graph_err}", exc_info=True)
                 result.graph_urls = [] # Ensure it's an empty list on error

        # Save consolidated results (e.g., .locust_result.json) if model/app provided
        if model is not None and app_num is not None:
            self._save_consolidated_results(result, model, app_num)

        # --- Cleanup ---
        # Remove the incorrect cleanup call
        # if self.environment and self.environment.runner:
        #      self.environment.runner.cleanup() # REMOVED - Causes AttributeError
        #      logger.debug("Locust runner cleaned up.")

        # Clear references to potentially help garbage collection
        self.environment = None
        self.runner = None
        logger.debug("Environment and runner references cleared.")


        logger.info(f"Returning results for test {full_test_name}")
        return result
    # --- End run_test_library ---


    # Helper for run_test_cli to create temp file
    def _create_temp_locustfile(self, host: str, endpoints: List[Dict[str, Any]], test_dir: Path) -> str:
        """ Creates a temporary locustfile in the test-specific directory for CLI runs. """
        # Indent code block for readability
        content = f"""# Auto-generated Locustfile for {test_dir.name}
from locust import HttpUser, task, between
import json # Make json available for data payloads if needed

class DynamicHttpUser(HttpUser):
    host = "{host}"
    wait_time = between(1, 3) # Wait 1-3 seconds between tasks
    print(f"DynamicHttpUser targeting host: {{host}}") # Log host on startup

"""
        # Add tasks for each endpoint definition
        for i, endpoint in enumerate(endpoints):
            path = endpoint['path']
            method = endpoint.get('method', 'GET').lower()
            weight = endpoint.get('weight', 1)
            # Sanitize path for function name
            ep_name_part = re.sub(r"[^a-zA-Z0-9_]", "_", path.strip('/')).lower()
            if not ep_name_part: ep_name_part = "root"
            func_name = f"task_{method}_{ep_name_part}_{i}"
            # Use path for request grouping unless a specific name is given
            request_name = endpoint.get('request_name', path)

            # Build list of keyword arguments for the client call
            params_list = []
            params_list.append(f'name="{request_name}"') # Group stats by this name
            params_list.append('catch_response=True') # Allow checking response status

            # Handle different payload types correctly
            if 'params' in endpoint: params_list.append(f"params={endpoint['params']!r}") # Use repr for safety
            if 'data' in endpoint: params_list.append(f"data={endpoint['data']!r}")
            # Ensure JSON is properly formatted string within the f-string for dynamic execution
            if 'json' in endpoint: params_list.append(f"json={endpoint['json']!r}") # Pass as repr, Locust client handles dicts
            if 'headers' in endpoint: params_list.append(f"headers={endpoint['headers']!r}")
            # Add files support if needed:
            # if 'files' in endpoint: params_list.append(f"files={endpoint['files']!r}")

            param_str = ", ".join(params_list)

            # Generate the task method code string
            task_code = f"""
    @task({weight})
    def {func_name}(self):
        # print(f"Executing task: {method.upper()} {path}") # Optional: log task execution
        # Using 'with' ensures the response context is managed
        with self.client.{method}("{path}", {param_str}) as response:
            # Basic check for success (status code < 400)
            if not response.ok:
                # Mark request as failure for stats, provide concise reason
                response.failure(f"HTTP {{response.status_code}}")
            # else:
            #     response.success() # Explicitly mark success (optional)

"""
            content += task_code

        # Write the generated content to a file inside the test run directory
        locustfile_path = test_dir / f"locustfile_{test_dir.name}.py"
        try:
             with open(locustfile_path, "w", encoding='utf-8') as f:
                 f.write(content)
             logger.info(f"Created temporary Locustfile for CLI run at {locustfile_path}")
             return str(locustfile_path)
        except Exception as e:
             logger.error(f"Failed to write temporary locustfile {locustfile_path}: {e}", exc_info=True)
             raise # Re-raise the exception to prevent proceeding


    # Kept for run_test_cli or manual CSV analysis
    def _parse_csv_results(
        self,
        stats_file: str,
        failures_file: str,
        start_time: datetime,
        end_time: datetime,
        user_count: int,
        spawn_rate: int
    ) -> Optional[PerformanceResult]:
        """
        Parse Locust CSV results into a PerformanceResult object.
        NOTE: Less accurate than direct environment stats, especially for percentiles.
              Returns None if essential files are missing or parsing fails.
        """
        total_requests, total_failures = 0, 0
        avg_response_time, median_response_time, requests_per_sec = 0.0, 0.0, 0.0
        percentile_95, percentile_99 = 0.0, 0.0
        endpoints: List[EndpointStats] = []
        errors: List[ErrorStats] = []

        try:
            # --- Parse Stats CSV ---
            stats_path = Path(stats_file)
            if stats_path.exists() and stats_path.stat().st_size > 0:
                df_stats = pd.read_csv(stats_file)

                # Define columns expected to be numeric
                num_cols = ['Request Count', 'Failure Count', 'Median Response Time',
                            'Average Response Time', 'Min Response Time', 'Max Response Time',
                            'Average Content Size', 'Requests/s', 'Failures/s']
                # Dynamically add percentile columns (e.g., '50%', '95%')
                percentile_cols = [col for col in df_stats.columns if '%' in col]
                num_cols.extend(percentile_cols)

                # Convert relevant columns to numeric, coercing errors to NaN, then fill NaN with 0
                for col in num_cols:
                     if col in df_stats.columns:
                         df_stats[col] = pd.to_numeric(df_stats[col], errors='coerce').fillna(0)
                     else:
                         logger.warning(f"Expected numeric column '{col}' not found in {stats_file}")


                # Iterate through rows to extract stats
                for _, row in df_stats.iterrows():
                    is_aggregated = row['Name'] == 'Aggregated'

                    # Extract percentiles found in the row
                    percentiles_dict = {}
                    p95_val, p99_val = 0.0, 0.0
                    for p_col in percentile_cols:
                         if p_col in row:
                             p_key = p_col.replace('%', '').strip()
                             p_val = row.get(p_col, 0.0)
                             percentiles_dict[p_key] = p_val
                             # Specifically capture 95th and 99th for the summary result
                             if '95' in p_key: p95_val = p_val
                             if '99' in p_key: p99_val = p_val

                    # Populate aggregated results or endpoint stats
                    if is_aggregated:
                        total_requests = int(row.get('Request Count', 0))
                        total_failures = int(row.get('Failure Count', 0))
                        avg_response_time = row.get('Average Response Time', 0.0)
                        median_response_time = row.get('Median Response Time', 0.0)
                        requests_per_sec = row.get('Requests/s', 0.0)
                        percentile_95 = p95_val
                        percentile_99 = p99_val
                    else:
                        endpoint_stats = EndpointStats(
                            name=row.get('Name', 'Unknown Endpoint'),
                            method=row.get('Type', 'Unknown Method'), # 'Type' column holds method in CSV
                            num_requests=int(row.get('Request Count', 0)),
                            num_failures=int(row.get('Failure Count', 0)),
                            median_response_time=row.get('Median Response Time', 0.0),
                            avg_response_time=row.get('Average Response Time', 0.0),
                            min_response_time=row.get('Min Response Time', 0.0),
                            max_response_time=row.get('Max Response Time', 0.0),
                            avg_content_length=row.get('Average Content Size', 0.0),
                            current_rps=row.get('Requests/s', 0.0),
                            current_fail_per_sec=row.get('Failures/s', 0.0),
                            percentiles=percentiles_dict
                        )
                        endpoints.append(endpoint_stats)
            else:
                logger.error(f"Stats CSV file not found or is empty: {stats_file}. Cannot parse results.")
                return None # Cannot proceed without stats

            # --- Parse Failures CSV ---
            failures_path = Path(failures_file)
            if failures_path.exists() and failures_path.stat().st_size > 0:
                df_failures = pd.read_csv(failures_file)
                # Ensure 'Occurrences' is numeric
                df_failures['Occurrences'] = pd.to_numeric(df_failures['Occurrences'], errors='coerce').fillna(0).astype(int)

                # Group by error details to consolidate similar errors if needed, or process row by row
                # For simplicity, processing row by row as Locust CSV usually aggregates already
                for _, row in df_failures.iterrows():
                    error_stats = ErrorStats(
                        # Headers in failures.csv: Method,Name,Error,Occurrences
                        method=row.get('Method', 'N/A'),
                        endpoint=row.get('Name', 'N/A'), # Endpoint name
                        error_type=row.get('Error', 'Unknown Error'), # The error string
                        count=int(row.get('Occurrences', 0)),
                        description=row.get('Error', '') # Use error string as description too
                    )
                    errors.append(error_stats)
            else:
                 logger.warning(f"Failures CSV file not found or is empty: {failures_file}")
                 # Continue without error details, but log it

            # --- Construct Final Result ---
            duration = max((end_time - start_time).total_seconds(), 0.1) # Avoid zero duration

            result = PerformanceResult(
                total_requests=total_requests,
                total_failures=total_failures,
                avg_response_time=avg_response_time,
                median_response_time=median_response_time,
                requests_per_sec=requests_per_sec, # Use value from Aggregated row
                start_time=start_time.strftime("%Y-%m-%d %H:%M:%S"),
                end_time=end_time.strftime("%Y-%m-%d %H:%M:%S"),
                duration=int(duration),
                endpoints=endpoints,
                errors=errors,
                percentile_95=percentile_95,
                percentile_99=percentile_99,
                user_count=user_count,
                spawn_rate=spawn_rate,
            )
            logger.info(f"Successfully parsed CSV results for test ending {result.end_time}")
            return result

        except pd.errors.EmptyDataError as e:
             logger.warning(f"CSV parsing failed: File was empty ({e})")
             return None # Indicate parsing failure
        except Exception as e:
            logger.exception(f"Unexpected error parsing CSV results: {e}")
            return None # Indicate parsing failure


    def _generate_graphs_from_history(self, history: List[StatsEntry], test_dir: Path) -> List[GraphInfo]:
        """
        Generates performance graphs from Locust stats history list (from library run).

        Args:
            history: List of StatsEntry objects from environment.stats.history.
            test_dir: Directory to save the generated graph PNG files.

        Returns:
            List of dictionaries containing graph names and their URLs relative to static path.
        """
        graph_infos: List[GraphInfo] = []
        if not history:
            logger.warning("No history data provided for graph generation.")
            return graph_infos

        try:
            # Convert history list (list of StatsEntry objects) to DataFrame
            history_data = [h.to_dict() for h in history] # Convert each entry to dict
            df = pd.DataFrame(history_data)

            if df.empty or 'time' not in df.columns:
                 logger.warning("History DataFrame is empty or missing 'time' column after conversion.")
                 return graph_infos

            # Convert 'time' string (e.g., "YYYY-MM-DD HH:MM:SS") to datetime objects
            try:
                df['time_dt'] = pd.to_datetime(df['time'])
            except Exception as time_err:
                logger.error(f"Could not parse history time column: {time_err}. Using index.", exc_info=True)
                # Fallback: Use row index if time parsing fails
                df['time_dt'] = pd.to_datetime(df.index, unit='s', origin=pd.Timestamp(history[0].time) if history else 'unix')


            plt.style.use('seaborn-v0_8-whitegrid') # Use a visually appealing style

            # --- Graph 1: Requests & Failures Per Second ---
            if 'current_rps' in df.columns and 'current_fail_per_sec' in df.columns:
                plt.figure(figsize=(12, 6))
                plt.plot(df['time_dt'], df['current_rps'], label='Requests/s', color='tab:blue', linewidth=1.5)
                plt.plot(df['time_dt'], df['current_fail_per_sec'], label='Failures/s', color='tab:red', linestyle='--', linewidth=1)
                plt.title('Requests and Failures Per Second Over Time')
                plt.xlabel('Time')
                plt.ylabel('Rate (per second)')
                plt.legend()
                plt.grid(True, which='both', linestyle='--', linewidth=0.5)
                plt.tight_layout() # Adjust layout to prevent labels overlapping
                rps_path = test_dir / 'requests_failures_per_second.png'
                plt.savefig(rps_path)
                plt.close() # Close the figure to free memory
                # Construct URL relative to the static root (self.output_dir)
                graph_url = f"{self.static_url_path}/{rps_path.relative_to(self.output_dir).as_posix()}"
                graph_infos.append({"name": "RPS & Failures/s", "url": graph_url})
            else:
                 logger.warning("Skipping RPS graph: 'current_rps' or 'current_fail_per_sec' column missing.")


            # --- Graph 2: Response Times (Average, Median, 95th Percentile) ---
            required_rt_cols = ['median_response_time', 'avg_response_time']
            if all(col in df.columns for col in required_rt_cols):
                 plt.figure(figsize=(12, 6))
                 plt.plot(df['time_dt'], df['avg_response_time'], label='Average RT', color='tab:green', linewidth=1.5)
                 plt.plot(df['time_dt'], df['median_response_time'], label='Median RT (P50)', color='tab:orange', linestyle='-', linewidth=1.5)

                 # Add 95th percentile if available (column name might vary slightly based on Locust version)
                 # Look for column names like '95.0' or similar
                 p95_col_name = next((col for col in df.columns if '95' in col and isinstance(df[col].iloc[0], (int, float))), None)
                 if p95_col_name:
                      plt.plot(df['time_dt'], df[p95_col_name], label='95th Percentile RT', color='tab:purple', linestyle=':', linewidth=1.5)
                 else:
                      logger.warning("95th percentile column not found or not numeric in history data.")


                 plt.title('Response Times Over Time')
                 plt.xlabel('Time')
                 plt.ylabel('Response Time (ms)')
                 plt.legend()
                 plt.grid(True, which='both', linestyle='--', linewidth=0.5)
                 plt.tight_layout()
                 rt_path = test_dir / 'response_times.png'
                 plt.savefig(rt_path)
                 plt.close()
                 graph_url = f"{self.static_url_path}/{rt_path.relative_to(self.output_dir).as_posix()}"
                 graph_infos.append({"name": "Response Times", "url": graph_url})
            else:
                 logger.warning("Skipping Response Time graph: Required columns missing.")

            # --- Graph 3: Active User Count ---
            if 'user_count' in df.columns:
                plt.figure(figsize=(12, 6))
                plt.plot(df['time_dt'], df['user_count'], label='Active Users', color='tab:cyan', linewidth=1.5)
                plt.title('Number of Active Users Over Time')
                plt.xlabel('Time')
                plt.ylabel('Users')
                plt.legend()
                plt.grid(True, which='both', linestyle='--', linewidth=0.5)
                plt.tight_layout()
                users_path = test_dir / 'active_users.png'
                plt.savefig(users_path)
                plt.close()
                graph_url = f"{self.static_url_path}/{users_path.relative_to(self.output_dir).as_posix()}"
                graph_infos.append({"name": "Active Users", "url": graph_url})
            else:
                 logger.warning("Skipping Active Users graph: 'user_count' column missing.")

            logger.info(f"Generated {len(graph_infos)} performance graphs in {test_dir}")
            return graph_infos

        except ImportError:
            logger.warning("Matplotlib or Pandas not installed. Skipping graph generation from history.")
            return []
        except Exception as e:
            logger.error(f"Error generating graphs from history: {e}", exc_info=True)
            return [] # Return empty list on error


    def _generate_graphs_from_csv(self, history_csv_path: str, test_dir: Path) -> List[GraphInfo]:
        """
        Generates graphs from the _stats_history.csv file (used by run_test_cli).
        """
        graph_infos: List[GraphInfo] = []
        history_file = Path(history_csv_path)
        if not history_file.exists() or history_file.stat().st_size == 0:
            logger.warning(f"History CSV file not found or empty: {history_csv_path}. Cannot generate graphs.")
            return graph_infos

        try:
            df = pd.read_csv(history_file)
            if df.empty or 'Timestamp' not in df.columns:
                logger.warning(f"History CSV {history_csv_path} is empty or missing 'Timestamp' column.")
                return graph_infos

            # Convert Unix timestamp to datetime
            try:
                # Use errors='coerce' to handle potential bad timestamps
                df['time_dt'] = pd.to_datetime(df['Timestamp'], unit='s', errors='coerce')
                # Drop rows where timestamp conversion failed
                df.dropna(subset=['time_dt'], inplace=True)
                if df.empty:
                     logger.warning("No valid timestamps found in history CSV after conversion.")
                     return graph_infos
            except Exception as time_err:
                logger.error(f"Could not parse history timestamp column: {time_err}. Using index.", exc_info=True)
                df['time_dt'] = df.index # Fallback

            plt.style.use('seaborn-v0_8-whitegrid')

            # --- Requests Per Second (from CSV) ---
            if 'Requests/s' in df.columns and 'Failures/s' in df.columns:
                plt.figure(figsize=(12, 6))
                plt.plot(df['time_dt'], df['Requests/s'], label='RPS', color='tab:blue', linewidth=1.5)
                plt.plot(df['time_dt'], df['Failures/s'], label='Failures/s', color='tab:red', linestyle='--', linewidth=1)
                plt.title('Requests and Failures Per Second Over Time (from CSV)')
                plt.xlabel('Time')
                plt.ylabel('Rate (per second)')
                plt.legend()
                plt.grid(True, which='both', linestyle='--', linewidth=0.5)
                plt.tight_layout()
                rps_path = test_dir / 'requests_failures_per_second_csv.png'
                plt.savefig(rps_path)
                plt.close()
                graph_url = f"{self.static_url_path}/{rps_path.relative_to(self.output_dir).as_posix()}"
                graph_infos.append({"name": "RPS & Failures/s (CSV)", "url": graph_url})

            # --- Response Times (from CSV) ---
            rt_cols = ['Average Response Time', 'Median Response Time']
            if all(col in df.columns for col in rt_cols):
                 plt.figure(figsize=(12, 6))
                 plt.plot(df['time_dt'], df['Average Response Time'], label='Average RT', color='tab:green', linewidth=1.5)
                 plt.plot(df['time_dt'], df['Median Response Time'], label='Median RT (P50)', color='tab:orange', linewidth=1.5)

                 # Find 95th percentile column (e.g., '95%')
                 p95_col = next((col for col in df.columns if '95%' in col), None)
                 if p95_col:
                      # Ensure the column is numeric before plotting
                      df[p95_col] = pd.to_numeric(df[p95_col], errors='coerce')
                      # Use fillna(method='ffill') to handle potential NaNs from coercion
                      plt.plot(df['time_dt'], df[p95_col].fillna(method='ffill'), label='95th Percentile RT', color='tab:purple', linestyle=':', linewidth=1.5)

                 plt.title('Response Times Over Time (from CSV)')
                 plt.xlabel('Time')
                 plt.ylabel('Response Time (ms)')
                 plt.legend()
                 plt.grid(True, which='both', linestyle='--', linewidth=0.5)
                 plt.tight_layout()
                 rt_path = test_dir / 'response_times_csv.png'
                 plt.savefig(rt_path)
                 plt.close()
                 graph_url = f"{self.static_url_path}/{rt_path.relative_to(self.output_dir).as_posix()}"
                 graph_infos.append({"name": "Response Times (CSV)", "url": graph_url})


            # --- User Count (from CSV) ---
            if 'User Count' in df.columns:
                plt.figure(figsize=(12, 6))
                plt.plot(df['time_dt'], df['User Count'], label='Active Users', color='tab:cyan', linewidth=1.5)
                plt.title('Number of Active Users Over Time (from CSV)')
                plt.xlabel('Time')
                plt.ylabel('Users')
                plt.legend()
                plt.grid(True, which='both', linestyle='--', linewidth=0.5)
                plt.tight_layout()
                users_path = test_dir / 'active_users_csv.png'
                plt.savefig(users_path)
                plt.close()
                graph_url = f"{self.static_url_path}/{users_path.relative_to(self.output_dir).as_posix()}"
                graph_infos.append({"name": "Active Users (CSV)", "url": graph_url})

            logger.info(f"Generated {len(graph_infos)} performance graphs from CSV in {test_dir}")
            return graph_infos

        except ImportError:
            logger.warning("Matplotlib or Pandas not installed. Skipping graph generation from CSV.")
            return []
        except pd.errors.EmptyDataError:
            logger.warning(f"History CSV file was empty: {history_csv_path}")
            return []
        except Exception as e:
            logger.error(f"Error generating graphs from CSV '{history_csv_path}': {e}", exc_info=True)
            return [] # Return empty list on error

