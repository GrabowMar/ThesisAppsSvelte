"""
Enhanced Performance Testing Framework using Locust

A flexible framework for running load tests using Locust, providing detailed metrics,
customizable test scenarios, and comprehensive reporting.
"""

import json
import logging
import os
import subprocess
import tempfile
import time  # Used for periodic tasks
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Callable

# Locust imports
from locust import HttpUser, task, between, events
from locust.env import Environment
from locust.stats import stats_printer, write_csv_files
import gevent

# Reporting imports
import pandas as pd
import matplotlib.pyplot as plt

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
    avg_content_length: float = 0  # Note: Locust CSV doesn't typically include this directly
    current_rps: float = 0
    current_fail_per_sec: float = 0
    percentiles: Dict[str, float] = field(default_factory=dict)


@dataclass
class ErrorStats:
    """Error statistics for a test run."""
    error_type: str
    count: int
    endpoint: str
    method: str
    description: str = ""


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
    duration: int
    user_count: int
    spawn_rate: int
    endpoints: List[EndpointStats] = field(default_factory=list)
    errors: List[ErrorStats] = field(default_factory=list)
    percentile_95: float = 0
    percentile_99: float = 0
    csv_stats_path: Optional[str] = None
    # raw_stats field removed as it was unused

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['endpoints'] = [asdict(endpoint) for endpoint in self.endpoints]
        result['errors'] = [asdict(error) for error in self.errors]
        return result

    def save_json(self, file_path: Union[str, Path]) -> None:
        """Save results as JSON."""
        try:
            with open(file_path, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            logger.info(f"Performance results saved to {file_path}")
        except IOError as e:
            logger.error(f"Failed to save results to {file_path}: {e}")


class UserGenerator:
    """Generates Locust user classes dynamically."""

    @staticmethod
    def create_http_user(host: str, endpoints: List[Dict[str, Any]]) -> type:
        """
        Create a dynamic HttpUser class for testing specific endpoints.

        Args:
            host: Target host URL.
            endpoints: List of endpoint configurations. Example:
                [
                    {'path': '/api/users', 'method': 'GET', 'weight': 10},
                    {'path': '/api/products', 'method': 'POST', 'weight': 5,
                     'data': {'name': 'Product'}, 'headers': {'Content-Type': 'application/json'},
                     'request_name': 'create_product', 'validators': my_validator_func}
                ]

        Returns:
            Dynamically created HttpUser class inheriting from locust.HttpUser.
        """
        class_attrs = {
            'host': host,
            'wait_time': between(1, 3)  # Default wait time, can be overridden
        }

        # Create task methods for each endpoint
        for i, endpoint_config in enumerate(endpoints):
            path = endpoint_config['path']
            method = endpoint_config.get('method', 'GET').lower()
            weight = endpoint_config.get('weight', 1)
            # Use provided name or generate one
            task_name = endpoint_config.get('name', f"endpoint_{i}")

            # Use closure to capture loop variables correctly for the task function
            def create_task_fn(current_path, current_method, config):
                def task_fn(self):
                    # Extract request parameters (params, data, json, headers)
                    kwargs = {
                        param: config[param]
                        for param in ['params', 'data', 'json', 'headers']
                        if param in config
                    }
                    # Set custom name for Locust stats if specified
                    if 'request_name' in config:
                        kwargs['name'] = config['request_name']
                    else:
                        # Default name combines method and path for clarity in stats
                        kwargs['name'] = f"{current_method.upper()} {current_path}"

                    request_method = getattr(self.client, current_method)
                    with request_method(current_path, catch_response=True, **kwargs) as response:
                        # Apply custom validators if provided
                        validators = config.get('validators')
                        if validators and callable(validators):
                            try:
                                validators(response)
                            except Exception as e:
                                response.failure(f"Validator failed: {e}")
                        # Basic validation if no custom validator or validator didn't fail
                        elif response.status_code >= 400:
                            failure_msg = f"HTTP {response.status_code}"
                            # Avoid logging potentially large response bodies by default
                            # failure_msg += f": {response.text[:200]}" # Uncomment if needed
                            response.failure(failure_msg)
                        else:
                            response.success() # Explicitly mark as success

                # Set metadata for the task function
                task_fn.__name__ = f"task_{task_name}"
                task_fn.__doc__ = f"Task for {method.upper()} {path}"
                return task_fn

            # Create and decorate the task function
            task_function = create_task_fn(path, method, endpoint_config)
            # Apply the @task decorator with the specified weight
            decorated_task = task(weight)(task_function)
            class_attrs[f"task_{task_name}"] = decorated_task

        # Create and return the dynamic class
        return type('DynamicHttpUser', (HttpUser,), class_attrs)


class LocustPerformanceTester:
    """
    Runs performance tests using Locust, supporting CLI and library modes.

    Collects detailed metrics and generates reports (CSV, HTML, Graphs).
    """

    def __init__(self, output_dir: Union[str, Path]):
        """
        Initialize the PerformanceTester.

        Args:
            output_dir: Directory for storing test reports and data.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.current_test_dir: Optional[Path] = None
        self.environment: Optional[Environment] = None

    def _setup_test_directory(self, test_name: str) -> Path:
        """
        Create a unique directory for the current test run based on name and timestamp.

        Args:
            test_name: Name to identify this test run.

        Returns:
            Path to the created test directory.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_dir = self.output_dir / f"{test_name}_{timestamp}"
        test_dir.mkdir(parents=True, exist_ok=True)
        self.current_test_dir = test_dir
        logger.info(f"Test output directory set to: {test_dir}")
        return test_dir

    def _create_temp_locustfile(self, host: str, endpoints: List[Dict[str, Any]]) -> str:
        """
        Generate a temporary Python script (locustfile) based on endpoint definitions.

        Args:
            host: Target host URL.
            endpoints: List of endpoint configurations.

        Returns:
            Path to the temporary locustfile.
        """
        # Generate the content for the locustfile
        endpoint_tasks = []
        for i, endpoint in enumerate(endpoints):
            path = endpoint['path']
            method = endpoint.get('method', 'GET').lower()
            weight = endpoint.get('weight', 1)
            task_name = endpoint.get('name', f"endpoint_{i}")
            request_name = endpoint.get('request_name', f"{method.upper()} {path}")

            # Build the request parameters string safely
            kwargs_list = []
            for param in ['params', 'data', 'json', 'headers']:
                if param in endpoint:
                    # Use repr() for safe string representation of parameters
                    kwargs_list.append(f"{param}={repr(endpoint[param])}")
            kwargs_str = ", ".join(kwargs_list)

            task_code = f"""
    @task({weight})
    def {task_name}(self):
        with self.client.{method}("{path}", name="{request_name}", catch_response=True{f', {kwargs_str}' if kwargs_str else ''}) as response:
            if response.status_code >= 400:
                response.failure(f"HTTP {{response.status_code}}") # Keep failure message concise
            else:
                response.success()
"""
            endpoint_tasks.append(task_code)

        content = f"""
from locust import HttpUser, task, between

class AutoGeneratedUser(HttpUser):
    host = "{host}"
    wait_time = between(1, 3)  # Default wait time
    {''.join(endpoint_tasks)}
"""
        # Write the content to a temporary file
        try:
            fd, file_path = tempfile.mkstemp(suffix=".py", prefix="locustfile_", text=True)
            with os.fdopen(fd, "w") as f:
                f.write(content)
            logger.info(f"Created temporary Locustfile at {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Failed to create temporary locustfile: {e}")
            raise  # Re-raise the exception

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
        workers: int = 0, # Set > 0 for distributed mode (master/worker)
        tags: Optional[List[str]] = None,
        html_report: bool = True,
        extra_options: Optional[List[str]] = None
    ) -> Optional[PerformanceResult]:
        """
        Run a Locust test using the command-line interface.

        Args:
            test_name: Name for this test run (used for directory naming).
            host: Target host URL (e.g., "http://localhost:8080").
            locustfile_path: Path to a custom locustfile. If None, endpoints must be provided.
            endpoints: List of endpoint configurations to generate a temporary locustfile.
            user_count: Number of concurrent users.
            spawn_rate: Rate at which users are spawned per second.
            run_time: Duration of the test (e.g., "30s", "5m", "1h").
            headless: Run Locust without the web UI. Required for automated runs.
            workers: Number of worker processes for distributed testing (0 for local run).
            tags: List of tags to filter user classes or tasks.
            html_report: Generate a basic HTML summary report.
            extra_options: List of additional command-line options for Locust.

        Returns:
            PerformanceResult object containing test metrics, or None if the test failed critically.
        """
        if not locustfile_path and not endpoints:
            logger.error("Either locustfile_path or endpoints must be provided for CLI run.")
            return None
        if headless and not run_time:
            logger.error("run_time must be specified for headless mode.")
            return None

        test_dir = self._setup_test_directory(test_name)
        csv_prefix = str(test_dir / "stats") # Base name for CSV files

        temp_locustfile = None
        try:
            # Create a temporary locustfile if endpoints are given instead of a path
            if not locustfile_path and endpoints:
                temp_locustfile = self._create_temp_locustfile(host, endpoints)
                locustfile_path = temp_locustfile
            elif not locustfile_path:
                 # This case should be caught by the initial check, but added for safety
                 logger.error("Locustfile path is missing.")
                 return None


            # Build the Locust command
            cmd = ["locust", "-f", locustfile_path, "--host", host]
            cmd.extend(["--csv", csv_prefix]) # Enable CSV output

            if headless:
                cmd.extend([
                    "--headless",
                    "--users", str(user_count),
                    "--spawn-rate", str(spawn_rate),
                    "--run-time", run_time
                ])

            if workers > 0:
                # TODO: Implement logic to start workers separately if needed
                cmd.extend(["--master", "--expect-workers", str(workers)])
                logger.warning("Distributed mode (--workers > 0) assumes workers are started externally.")

            if tags:
                cmd.extend(["--tags"] + tags) # Use '+' for list concatenation

            if html_report and headless:
                 # Locust can generate its own HTML report in headless mode
                 cmd.extend(["--html", str(test_dir / f"{test_name}_locust_report.html")])

            if extra_options:
                cmd.extend(extra_options)

            logger.info(f"Running Locust command: {' '.join(cmd)}")
            start_time = datetime.now()

            # Execute the Locust command
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False # Don't raise exception on non-zero exit code
            )

            end_time = datetime.now()

            # Save command output logs
            stdout_path = test_dir / "locust_stdout.log"
            stderr_path = test_dir / "locust_stderr.log"
            with open(stdout_path, "w") as f_out, open(stderr_path, "w") as f_err:
                f_out.write(process.stdout)
                f_err.write(process.stderr)

            if process.returncode != 0:
                logger.error(f"Locust test failed with exit code {process.returncode}.")
                logger.error(f"Stderr saved to: {stderr_path}")
                # Attempt to parse any partial results that might exist
            else:
                 logger.info("Locust test completed successfully.")

            # Parse the generated CSV results regardless of exit code
            result = self._parse_csv_results(
                stats_file=f"{csv_prefix}_stats.csv",
                failures_file=f"{csv_prefix}_failures.csv",
                history_file=f"{csv_prefix}_stats_history.csv", # Correct history file name
                start_time=start_time,
                end_time=end_time,
                user_count=user_count,
                spawn_rate=spawn_rate
            )

            # Generate custom HTML report (optional, complements Locust's own report)
            # if html_report:
            #     report_path = test_dir / f"{test_name}_summary_report.html"
            #     self._generate_html_summary_report(result, report_path)

            # Generate graphs from history data
            self._generate_graphs(test_dir, result)

            # Save results summary to JSON
            json_path = test_dir / f"{test_name}_results.json"
            result.save_json(json_path)

            return result

        except Exception as e:
            logger.error(f"An error occurred during the CLI test run: {e}", exc_info=True)
            return None # Indicate failure
        finally:
            # Clean up the temporary locustfile if created
            if temp_locustfile and os.path.exists(temp_locustfile):
                try:
                    os.unlink(temp_locustfile)
                    logger.info(f"Removed temporary locustfile: {temp_locustfile}")
                except OSError as e:
                    logger.warning(f"Failed to delete temporary file {temp_locustfile}: {e}")

    def run_test_library(
        self,
        test_name: str,
        host: str,
        user_class: Optional[type] = None,
        endpoints: Optional[List[Dict[str, Any]]] = None,
        user_count: int = 10,
        spawn_rate: int = 1,
        run_time: int = 30, # Duration in seconds for library mode
        csv_interval: int = 5, # How often to write CSV stats
        on_start_callback: Optional[Callable[[Environment], None]] = None,
        on_stop_callback: Optional[Callable[[Environment], None]] = None
    ) -> Optional[PerformanceResult]:
        """
        Run a Locust test using the library approach (embedding Locust).

        Args:
            test_name: Name for this test run.
            host: Target host URL.
            user_class: Custom HttpUser class. If None, endpoints must be provided.
            endpoints: List of endpoint configurations to generate a user class.
            user_count: Number of concurrent users.
            spawn_rate: Rate at which users are spawned per second.
            run_time: Duration of the test in seconds.
            csv_interval: Interval (in seconds) for writing stats to CSV.
            on_start_callback: Optional function called when the test starts.
            on_stop_callback: Optional function called when the test stops.

        Returns:
            PerformanceResult object containing test metrics, or None on failure.
        """
        if not user_class and not endpoints:
            logger.error("Either user_class or endpoints must be provided for library run.")
            return None

        test_dir = self._setup_test_directory(test_name)
        csv_prefix = str(test_dir / "stats")

        # Create user class dynamically if endpoints are provided
        if not user_class and endpoints:
            try:
                user_class = UserGenerator.create_http_user(host, endpoints)
            except Exception as e:
                logger.error(f"Failed to create dynamic user class: {e}")
                return None

        if not user_class: # Should not happen if logic above is correct, but check again
             logger.error("User class is not available.")
             return None

        # --- Locust Environment Setup ---
        self.environment = Environment(user_classes=[user_class])
        self.environment.create_local_runner() # Use LocalRunner for library mode
        runner = self.environment.runner
        if not runner:
             logger.error("Failed to create Locust runner.")
             return None

        # --- Event Listeners ---
        start_time = None
        end_time = None

        @events.test_start.add_listener
        def on_test_start(environment, **_kwargs):
            nonlocal start_time
            start_time = datetime.now()
            logger.info(f"Test '{test_name}' starting at {start_time.strftime('%Y-%m-%d %H:%M:%S')}...")
            logger.info(f"Users: {user_count}, Spawn Rate: {spawn_rate}, Duration: {run_time}s")
            if on_start_callback:
                try:
                    on_start_callback(environment)
                except Exception as e:
                    logger.error(f"Error in on_start_callback: {e}")

        @events.test_stop.add_listener
        def on_test_stop(environment, **_kwargs):
            nonlocal end_time
            end_time = datetime.now()
            logger.info(f"Test '{test_name}' stopped at {end_time.strftime('%Y-%m-%d %H:%M:%S')}.")
            # Ensure final stats are written
            write_csv_files(environment.stats, csv_prefix, full_history=True)
            if on_stop_callback:
                try:
                    on_stop_callback(environment)
                except Exception as e:
                    logger.error(f"Error in on_stop_callback: {e}")

        # --- Periodic Tasks (Stats Printing and CSV Writing) ---
        # Use gevent loop for periodic CSV writing
        csv_writer_greenlet = None
        def periodic_csv_writer():
            while True:
                 # Check if runner is still active before writing
                 if runner and runner.state in (runner.STATE_RUNNING, runner.STATE_SPAWNING):
                    try:
                        write_csv_files(self.environment.stats, csv_prefix, full_history=True)
                    except Exception as e:
                        logger.error(f"Error writing CSV stats: {e}")
                 gevent.sleep(csv_interval)


        # --- Test Execution ---
        main_greenlet = None
        try:
            # Start the periodic tasks
            stats_printer_greenlet = gevent.spawn(stats_printer(self.environment.stats))
            csv_writer_greenlet = gevent.spawn(periodic_csv_writer)

            # Start the test run
            runner.start(user_count, spawn_rate=spawn_rate)

            # Schedule the test to stop after run_time
            gevent.spawn_later(run_time, lambda: runner.quit())

            # Wait for the main runner greenlet to finish
            main_greenlet = runner.greenlet
            main_greenlet.join()

            # Ensure start/end times are captured even if events didn't fire perfectly
            if start_time is None: start_time = datetime.now() # Fallback
            if end_time is None: end_time = datetime.now() # Fallback

            # --- Post-Test Processing ---
            logger.info("Test run finished. Processing results...")

            # Parse results from CSV files
            result = self._parse_csv_results(
                stats_file=f"{csv_prefix}_stats.csv",
                failures_file=f"{csv_prefix}_failures.csv",
                history_file=f"{csv_prefix}_stats_history.csv",
                start_time=start_time,
                end_time=end_time,
                user_count=user_count,
                spawn_rate=spawn_rate
            )

            # Generate reports and graphs
            # report_path = test_dir / f"{test_name}_summary_report.html"
            # self._generate_html_summary_report(result, report_path)
            self._generate_graphs(test_dir, result)

            # Save results summary to JSON
            json_path = test_dir / f"{test_name}_results.json"
            result.save_json(json_path)

            return result

        except Exception as e:
            logger.error(f"An error occurred during the library test run: {e}", exc_info=True)
            # Attempt to stop the runner if it's still running
            if runner and runner.state != runner.STATE_STOPPED:
                 runner.quit()
            return None # Indicate failure
        finally:
            # Clean up greenlets
            if 'stats_printer_greenlet' in locals() and stats_printer_greenlet:
                stats_printer_greenlet.kill(block=False)
            if csv_writer_greenlet:
                csv_writer_greenlet.kill(block=False)
            # Ensure environment is shut down
            if self.environment:
                self.environment.runner.quit() # Ensure runner is stopped
                self.environment.shutdown()
            logger.info("Locust environment shut down.")


    def _parse_csv_results(
        self,
        stats_file: str,
        failures_file: str,
        history_file: str, # Added for potential future use or detailed analysis
        start_time: datetime,
        end_time: datetime,
        user_count: int,
        spawn_rate: int
    ) -> PerformanceResult:
        """
        Parse Locust CSV results (*_stats.csv, *_failures.csv) into a PerformanceResult.

        Args:
            stats_file: Path to the main statistics CSV file (_stats.csv).
            failures_file: Path to the failures CSV file (_failures.csv).
            history_file: Path to the history CSV file (_stats_history.csv).
            start_time: Test start time.
            end_time: Test end time.
            user_count: Number of configured users.
            spawn_rate: Configured user spawn rate.

        Returns:
            PerformanceResult object populated with data from the CSV files.
        """
        # Initialize default values
        summary = {
            "total_requests": 0, "total_failures": 0, "avg_response_time": 0.0,
            "median_response_time": 0.0, "requests_per_sec": 0.0,
            "percentile_95": 0.0, "percentile_99": 0.0
        }
        endpoints_data = []
        errors_data = []

        try:
            # --- Parse Stats File ---
            if os.path.exists(stats_file):
                df_stats = pd.read_csv(stats_file)
                # Find the 'Aggregated' row for summary statistics
                agg_row = df_stats[df_stats['Name'] == 'Aggregated'].iloc[0] if not df_stats[df_stats['Name'] == 'Aggregated'].empty else None

                if agg_row is not None:
                    summary["total_requests"] = int(agg_row.get('Request Count', 0))
                    summary["total_failures"] = int(agg_row.get('Failure Count', 0))
                    summary["avg_response_time"] = float(agg_row.get('Average Response Time', 0.0))
                    summary["median_response_time"] = float(agg_row.get('Median Response Time', 0.0)) # Often labeled '50%'
                    summary["requests_per_sec"] = float(agg_row.get('Requests/s', 0.0))

                    # Extract percentiles (Locust CSV column names can vary slightly)
                    # Common percentile columns: '95%', '99%' or similar
                    for col in df_stats.columns:
                        if '95%' in col:
                           summary["percentile_95"] = float(agg_row.get(col, 0.0))
                        elif '99%' in col:
                           summary["percentile_99"] = float(agg_row.get(col, 0.0))
                    # Fallback if exact names aren't found (less reliable)
                    if summary["percentile_95"] == 0.0 and '95.0' in agg_row: summary["percentile_95"] = float(agg_row['95.0'])
                    if summary["percentile_99"] == 0.0 and '99.0' in agg_row: summary["percentile_99"] = float(agg_row['99.0'])


                # Process individual endpoint statistics
                for _, row in df_stats[df_stats['Name'] != 'Aggregated'].iterrows():
                    percentiles = {
                        col.strip('%').strip(): float(row[col])
                        for col in df_stats.columns if '%' in col and pd.notna(row[col])
                    }
                    # Ensure common percentiles exist if columns were missing/different
                    percentiles.setdefault('50', float(row.get('Median Response Time', 0.0)))


                    endpoint = EndpointStats(
                        name=row.get('Name', 'Unknown'),
                        method=row.get('Type', 'Unknown'), # 'Type' column usually holds the method
                        num_requests=int(row.get('Request Count', 0)),
                        num_failures=int(row.get('Failure Count', 0)),
                        median_response_time=float(row.get('Median Response Time', percentiles.get('50', 0.0))),
                        avg_response_time=float(row.get('Average Response Time', 0.0)),
                        min_response_time=float(row.get('Min Response Time', 0.0)),
                        max_response_time=float(row.get('Max Response Time', 0.0)),
                        current_rps=float(row.get('Requests/s', 0.0)),
                        current_fail_per_sec=float(row.get('Failures/s', 0.0)),
                        percentiles=percentiles
                        # avg_content_length is not typically in standard Locust CSVs
                    )
                    endpoints_data.append(endpoint)
            else:
                logger.warning(f"Stats file not found: {stats_file}")

            # --- Parse Failures File ---
            if os.path.exists(failures_file):
                df_failures = pd.read_csv(failures_file)
                # Group by error type, request name, and method to consolidate
                grouped_failures = df_failures.groupby(['Error', 'Name', 'Method']).size().reset_index(name='Occurrences')

                for _, row in grouped_failures.iterrows():
                    error = ErrorStats(
                        error_type=row['Error'],
                        count=row['Occurrences'],
                        endpoint=row['Name'], # 'Name' column links to the request name
                        method=row['Method'],
                        description="" # Description not usually in failures CSV
                    )
                    errors_data.append(error)
            else:
                logger.warning(f"Failures file not found: {failures_file}")

        except pd.errors.EmptyDataError:
             logger.warning(f"CSV file is empty: {stats_file} or {failures_file}")
        except KeyError as e:
             logger.error(f"Missing expected column in CSV file: {e}. Check Locust version/output format.")
        except Exception as e:
            logger.error(f"Error parsing CSV results: {e}", exc_info=True)
            # Return a partially filled or default result object in case of parsing errors

        # Calculate duration
        duration = int((end_time - start_time).total_seconds()) if start_time and end_time else 0

        # Create the final result object
        result = PerformanceResult(
            total_requests=summary["total_requests"],
            total_failures=summary["total_failures"],
            avg_response_time=summary["avg_response_time"],
            median_response_time=summary.get("median_response_time", summary.get("percentile_50", 0.0)), # Use 50% if median specific column missing
            requests_per_sec=summary["requests_per_sec"],
            start_time=start_time.strftime("%Y-%m-%d %H:%M:%S") if start_time else "N/A",
            end_time=end_time.strftime("%Y-%m-%d %H:%M:%S") if end_time else "N/A",
            duration=duration,
            endpoints=endpoints_data,
            errors=errors_data,
            percentile_95=summary["percentile_95"],
            percentile_99=summary["percentile_99"],
            user_count=user_count,
            spawn_rate=spawn_rate,
            csv_stats_path=stats_file # Store path for reference
        )
        return result

    def _generate_html_summary_report(self, result: PerformanceResult, output_path: Union[str, Path]) -> None:
        """
        Generate a simple HTML summary report from test results.

        Args:
            result: PerformanceResult object.
            output_path: Path to save the HTML report.
        """
        # Basic HTML structure using f-strings for simplicity
        failure_rate = (result.total_failures / result.total_requests * 100) if result.total_requests > 0 else 0

        # --- Endpoint Table Rows ---
        endpoint_rows = ""
        for endpoint in sorted(result.endpoints, key=lambda x: x.name): # Sort by name
            p95 = endpoint.percentiles.get('95', 'N/A')
            p95_str = f"{p95:.2f}" if isinstance(p95, (int, float)) else p95
            endpoint_rows += f"""
            <tr>
                <td>{endpoint.name}</td>
                <td>{endpoint.method}</td>
                <td>{endpoint.num_requests}</td>
                <td>{endpoint.num_failures}</td>
                <td>{endpoint.median_response_time:.2f}</td>
                <td>{endpoint.avg_response_time:.2f}</td>
                <td>{endpoint.min_response_time:.2f}</td>
                <td>{endpoint.max_response_time:.2f}</td>
                <td>{endpoint.current_rps:.2f}</td>
                <td>{p95_str}</td>
            </tr>"""

        # --- Error Table Rows ---
        error_rows = ""
        if result.errors:
            for error in sorted(result.errors, key=lambda x: x.count, reverse=True): # Sort by count desc
                error_rows += f"""
            <tr>
                <td class="error">{error.error_type}</td>
                <td>{error.count}</td>
                <td>{error.endpoint}</td>
                <td>{error.method}</td>
                <td>{error.description}</td>
            </tr>"""
        else:
            error_rows = "<tr><td colspan='5'>No errors reported.</td></tr>"

        # --- HTML Template ---
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Performance Test Summary Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f4f7f6; color: #333; }}
        h1, h2 {{ color: #005f73; border-bottom: 2px solid #0a9396; padding-bottom: 5px; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 25px; box-shadow: 0 2px 3px rgba(0,0,0,0.1); background-color: #fff; }}
        th, td {{ border: 1px solid #dee2e6; padding: 10px 12px; text-align: left; }}
        th {{ background-color: #e9ecef; color: #495057; font-weight: 600; }}
        tr:nth-child(even) {{ background-color: #f8f9fa; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 25px; padding: 15px; background-color: #fff; border-radius: 5px; box-shadow: 0 2px 3px rgba(0,0,0,0.1); }}
        .summary-item {{ background-color: #e0fbfc; padding: 10px; border-radius: 4px; border-left: 5px solid #0a9396; }}
        .summary-item strong {{ display: block; margin-bottom: 5px; color: #005f73; }}
        .error {{ color: #d90429; font-weight: bold; }}
        .footer {{ margin-top: 30px; text-align: center; font-size: 0.9em; color: #6c757d; }}
    </style>
</head>
<body>
    <h1>Performance Test Summary Report</h1>

    <div class="summary-grid">
        <div class="summary-item"><strong>Start Time:</strong> {result.start_time}</div>
        <div class="summary-item"><strong>End Time:</strong> {result.end_time}</div>
        <div class="summary-item"><strong>Duration:</strong> {result.duration} seconds</div>
        <div class="summary-item"><strong>Users:</strong> {result.user_count}</div>
        <div class="summary-item"><strong>Spawn Rate:</strong> {result.spawn_rate}/sec</div>
        <div class="summary-item"><strong>Total Requests:</strong> {result.total_requests:,}</div>
        <div class="summary-item"><strong>Total Failures:</strong> <span{ ' class="error"' if result.total_failures > 0 else ''}>{result.total_failures:,} ({failure_rate:.2f}%)</span></div>
        <div class="summary-item"><strong>Requests/Sec:</strong> {result.requests_per_sec:.2f}</div>
        <div class="summary-item"><strong>Avg Response Time:</strong> {result.avg_response_time:.2f} ms</div>
        <div class="summary-item"><strong>Median Response Time:</strong> {result.median_response_time:.2f} ms</div>
        <div class="summary-item"><strong>95th Percentile:</strong> {result.percentile_95:.2f} ms</div>
        <div class="summary-item"><strong>99th Percentile:</strong> {result.percentile_99:.2f} ms</div>
    </div>

    <h2>Endpoint Details</h2>
    <table>
        <thead>
            <tr>
                <th>Endpoint Name</th>
                <th>Method</th>
                <th>Requests</th>
                <th>Failures</th>
                <th>Median (ms)</th>
                <th>Average (ms)</th>
                <th>Min (ms)</th>
                <th>Max (ms)</th>
                <th>RPS</th>
                <th>P95 (ms)</th>
            </tr>
        </thead>
        <tbody>
            {endpoint_rows}
        </tbody>
    </table>

    <h2>Errors Summary</h2>
    <table>
        <thead>
            <tr>
                <th>Error Type</th>
                <th>Count</th>
                <th>Endpoint Name</th>
                <th>Method</th>
                <th>Description</th>
            </tr>
        </thead>
        <tbody>
            {error_rows}
        </tbody>
    </table>

    <div class="footer">
        Generated by LocustPerformanceTester on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
</body>
</html>
"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"HTML summary report generated at {output_path}")
        except IOError as e:
            logger.error(f"Failed to write HTML report to {output_path}: {e}")

    def _generate_graphs(self, test_dir: Path, result: PerformanceResult) -> None:
        """
        Generate performance graphs (PNG) from the history CSV file.

        Args:
            test_dir: Directory to save the graphs.
            result: PerformanceResult object (used to find the history file path).
        """
        if not result.csv_stats_path:
            logger.warning("Cannot generate graphs: CSV stats path is missing in results.")
            return

        # Construct history file path from stats path
        history_file = result.csv_stats_path.replace('_stats.csv', '_stats_history.csv')

        if not os.path.exists(history_file):
            logger.warning(f"History file not found: {history_file}. Skipping graph generation.")
            return

        try:
            df_history = pd.read_csv(history_file)

            # Convert Timestamp to datetime objects if needed (assuming it's epoch or string)
            if not pd.api.types.is_datetime64_any_dtype(df_history['Timestamp']):
                 try:
                     # Attempt conversion from Unix timestamp first
                     df_history['Timestamp'] = pd.to_datetime(df_history['Timestamp'], unit='s')
                 except (ValueError, TypeError):
                     try:
                         # Attempt conversion from standard datetime string formats
                         df_history['Timestamp'] = pd.to_datetime(df_history['Timestamp'])
                     except (ValueError, TypeError):
                         logger.warning("Could not parse Timestamp column for graphs. Using index instead.")
                         # Use index if timestamp parsing fails
                         df_history['TimeIndex'] = df_history.index


            time_col = 'Timestamp' if 'Timestamp' in df_history.columns and pd.api.types.is_datetime64_any_dtype(df_history['Timestamp']) else 'TimeIndex'
            x_label = 'Time' if time_col == 'Timestamp' else 'Time Index (seconds)'


            plt.style.use('seaborn-v0_8-whitegrid') # Use a clean style

            # --- Requests Per Second Graph ---
            plt.figure(figsize=(12, 6))
            if 'Requests/s' in df_history.columns:
                plt.plot(df_history[time_col], df_history['Requests/s'], label='Total RPS', color='#0a9396')
            if 'Failures/s' in df_history.columns:
                 plt.plot(df_history[time_col], df_history['Failures/s'], label='Failures/s', color='#d90429', linestyle='--')
            plt.title('Requests and Failures Per Second Over Time')
            plt.xlabel(x_label)
            plt.ylabel('Rate (per second)')
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(test_dir / 'requests_failures_per_second.png')
            plt.close() # Close the plot to free memory

            # --- Response Times Graph ---
            plt.figure(figsize=(12, 6))
            percentile_cols = [col for col in df_history.columns if '%' in col]
            response_time_cols = ['Average Response Time'] + sorted(percentile_cols) # Sort percentiles

            for col in response_time_cols:
                if col in df_history.columns:
                    label = col.replace(' Response Time', '') # Cleaner label
                    plt.plot(df_history[time_col], df_history[col], label=label)

            plt.title('Response Time Percentiles Over Time')
            plt.xlabel(x_label)
            plt.ylabel('Response Time (ms)')
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(test_dir / 'response_times_percentiles.png')
            plt.close()

            # --- User Count Graph ---
            if 'User Count' in df_history.columns:
                plt.figure(figsize=(12, 6))
                plt.plot(df_history[time_col], df_history['User Count'], label='Active Users', color='#ee9b00')
                plt.title('Number of Concurrent Users Over Time')
                plt.xlabel(x_label)
                plt.ylabel('User Count')
                plt.legend()
                plt.grid(True)
                plt.tight_layout()
                plt.savefig(test_dir / 'user_count.png')
                plt.close()

            logger.info(f"Performance graphs generated in {test_dir}")

        except pd.errors.EmptyDataError:
            logger.warning(f"History file is empty: {history_file}. Skipping graph generation.")
        except KeyError as e:
            logger.error(f"Missing expected column in history file for graphs: {e}. Skipping graph generation.")
        except Exception as e:
            logger.error(f"Error generating graphs: {e}", exc_info=True)

# Example Usage (Optional - can be removed or placed in a separate script)
if __name__ == "__main__":
    OUTPUT_DIRECTORY = Path("./locust_test_results")
    TARGET_HOST = "http://httpbin.org" # Example target

    # Define endpoints for the test
    test_endpoints = [
        {'path': '/get', 'method': 'GET', 'weight': 5, 'request_name': 'get_request'},
        {'path': '/post', 'method': 'POST', 'weight': 2, 'json': {'key': 'value'}, 'request_name': 'post_request'},
        {'path': '/delay/1', 'method': 'GET', 'weight': 1, 'request_name': 'delay_1s'},
    ]

    tester = LocustPerformanceTester(output_dir=OUTPUT_DIRECTORY)

    # --- Example 1: Run via CLI ---
    print("\n--- Running Test via CLI ---")
    cli_results = tester.run_test_cli(
        test_name="httpbin_cli_test",
        host=TARGET_HOST,
        endpoints=test_endpoints, # Use endpoints to generate locustfile
        user_count=5,
        spawn_rate=1,
        run_time="15s", # Short duration for example
        headless=True,
        html_report=True # Ask Locust to generate its report
    )

    if cli_results:
        print("\nCLI Test Summary:")
        print(f"  Total Requests: {cli_results.total_requests}")
        print(f"  Total Failures: {cli_results.total_failures}")
        print(f"  Avg Response Time: {cli_results.avg_response_time:.2f} ms")
        print(f"  RPS: {cli_results.requests_per_sec:.2f}")
        # cli_results.save_json(OUTPUT_DIRECTORY / "cli_test_summary.json") # Already saved by run_test_cli

    # --- Example 2: Run via Library ---
    # print("\n--- Running Test via Library ---")
    # # You could create a user class manually or use the generator
    # # dynamic_user = UserGenerator.create_http_user(TARGET_HOST, test_endpoints)

    # library_results = tester.run_test_library(
    #     test_name="httpbin_library_test",
    #     host=TARGET_HOST,
    #     # user_class=dynamic_user, # Pass the generated class
    #     endpoints=test_endpoints, # Or let it generate internally
    #     user_count=8,
    #     spawn_rate=2,
    #     run_time=20, # Duration in seconds
    #     csv_interval=5
    # )

    # if library_results:
    #     print("\nLibrary Test Summary:")
    #     print(f"  Total Requests: {library_results.total_requests}")
    #     print(f"  Total Failures: {library_results.total_failures}")
    #     print(f"  Avg Response Time: {library_results.avg_response_time:.2f} ms")
    #     print(f"  RPS: {library_results.requests_per_sec:.2f}")
    #     # library_results.save_json(OUTPUT_DIRECTORY / "library_test_summary.json") # Already saved by run_test_library

    print(f"\nTest artifacts saved in: {OUTPUT_DIRECTORY}")

