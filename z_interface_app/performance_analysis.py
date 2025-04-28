"""
Enhanced Performance Testing Framework using Locust

A flexible and robust framework for running load tests using Locust, 
providing detailed metrics, customizable test scenarios, and comprehensive reporting.
"""

import json
import logging
import os
import re
import tempfile
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Callable, Tuple
import socket
# For direct Locust control
from locust import HttpUser, task, constant, events, between
from locust.env import Environment
from locust.stats import stats_printer, StatsEntry
from locust.runners import Runner, LocalRunner
import gevent
import pandas as pd
import matplotlib.pyplot as plt
import requests

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
    endpoints: List[EndpointStats] = field(default_factory=list)
    errors: List[ErrorStats] = field(default_factory=list)
    percentile_95: float = 0
    percentile_99: float = 0
    user_count: int = 0
    spawn_rate: int = 0
    raw_stats: Optional[Dict[str, Any]] = None
    csv_stats_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {k: v for k, v in asdict(self).items() if k != 'raw_stats'}
        result['endpoints'] = [asdict(endpoint) for endpoint in self.endpoints]
        result['errors'] = [asdict(error) for error in self.errors]
        return result

    def save_json(self, file_path: Union[str, Path]) -> None:
        """Save results as JSON."""
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


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
            'wait_time': between(1, 3)  # Default wait time
        }
        
        # Create task methods for each endpoint
        for i, endpoint in enumerate(endpoints):
            path = endpoint['path']
            method = endpoint.get('method', 'GET').lower()
            weight = endpoint.get('weight', 1)
            name = endpoint.get('name', f"endpoint_{i}")
            
            # Create the task function
            def create_task_fn(path, method, endpoint_config):
                def task_fn(self):
                    # Extract request parameters from endpoint configuration
                    kwargs = {}
                    for param in ['params', 'data', 'json', 'headers']:
                        if param in endpoint_config:
                            kwargs[param] = endpoint_config[param]
                    
                    # Set custom name for the request if specified
                    if 'request_name' in endpoint_config:
                        kwargs['name'] = endpoint_config['request_name']
                    
                    # Execute the request with the specified method
                    request_method = getattr(self.client, method)
                    with request_method(path, catch_response=True, **kwargs) as response:
                        # Apply custom validators if provided
                        if 'validators' in endpoint_config and callable(endpoint_config['validators']):
                            endpoint_config['validators'](response)
                        # Basic validation
                        elif response.status_code >= 400:
                            response.failure(f"HTTP {response.status_code}: {response.text}")
                
                # Set the function name and docstring
                task_fn.__name__ = f"task_{name}"
                task_fn.__doc__ = f"Task for {method.upper()} {path}"
                return task_fn
            
            # Create and decorate the task function
            task_fn = create_task_fn(path, method, endpoint)
            task_fn = task(weight)(task_fn)
            class_attrs[f"task_{name}"] = task_fn
        
        # Create and return the dynamic class
        return type('DynamicHttpUser', (HttpUser,), class_attrs)


class LocustPerformanceTester:
    """
    Enhanced framework for performance testing using Locust.
    
    Features:
    - Run tests either as a library or via command line
    - Support for custom user behaviors and scenarios
    - Detailed metrics collection
    - Comprehensive reporting options
    - CSV and graphical output
    """

    def __init__(self, output_dir: Union[str, Path]):
        """
        Initialize the PerformanceTester.
        
        Args:
            output_dir: Directory for storing test reports and data
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.current_test_dir = None
        self.environment = None
        self.runner = None
        self.user_classes = []

    # Add this method to the LocustPerformanceTester class in performance_analysis.py

    def _save_consolidated_results(self, 
                                result: PerformanceResult, 
                                model: str, 
                                app_num: int) -> str:
        """
        Save a consolidated JSON result file in the model/app directory.
        
        Args:
            result: PerformanceResult object containing test results
            model: Model name
            app_num: App number
            
        Returns:
            Path to the saved JSON file
        """
        try:
            # Construct path to the model/app directory
            app_dir = self.output_dir.parent / model / f"app{app_num}"
            app_dir.mkdir(parents=True, exist_ok=True)
            
            # Define the result file path
            result_file = app_dir / ".locust_result.json"
            
            # Convert result to dictionary for JSON serialization
            result_dict = result.to_dict()
            
            # Add some additional metadata
            result_dict["metadata"] = {
                "model": model,
                "app_num": app_num,
                "timestamp": datetime.now().isoformat(),
                "test_name": result_dict.get("test_name", f"{model}_app{app_num}"),
                "server_info": {
                    "hostname": socket.gethostname() if hasattr(socket, "gethostname") else "unknown"
                }
            }
            
            # Write to JSON file
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result_dict, f, indent=2)
                
            logger.info(f"Consolidated performance results saved to {result_file}")
            return str(result_file)
        except Exception as e:
            logger.exception(f"Error saving consolidated results: {e}")
            return ""

    def _setup_test_directory(self, test_name: str) -> Path:
        """
        Set up a directory for the current test run.
        
        Args:
            test_name: Name to identify this test run
            
        Returns:
            Path to the test directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Remove any existing timestamp from test_name to avoid duplication
        if re.search(r'_\d{8}_\d{6}$', test_name):
            # Test name already has a timestamp, don't add another one
            test_dir = self.output_dir / test_name
        else:
            # Add timestamp to test name
            test_dir = self.output_dir / f"{test_name}_{timestamp}"
        
        test_dir.mkdir(parents=True, exist_ok=True)
        self.current_test_dir = test_dir
        return test_dir

    def create_user_class(self, host: str, endpoints: List[Dict[str, Any]]) -> type:
        """
        Create a custom user class for the test.
        
        Args:
            host: Target host URL
            endpoints: List of endpoint configurations
            
        Returns:
            HttpUser class for testing
        """
        user_class = UserGenerator.create_http_user(host, endpoints)
        self.user_classes.append(user_class)
        return user_class

    # Update the run_test_cli method in LocustPerformanceTester to save consolidated results
# In performance_analysis.py

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
        html_report: bool = True,
        model: Optional[str] = None,  # Add model parameter
        app_num: Optional[int] = None  # Add app_num parameter
    ) -> PerformanceResult:
        """
        Run a Locust test via command line.
        
        Args:
            test_name: Name to identify this test
            host: Target host URL
            locustfile_path: Path to a custom locustfile (optional)
            endpoints: List of endpoint configurations (if no locustfile)
            user_count: Number of concurrent users
            spawn_rate: Rate at which users are spawned per second
            run_time: Duration of the test (e.g., "30s", "5m")
            headless: Whether to run in headless mode
            workers: Number of worker processes (0 for no distributed testing)
            tags: List of tags to filter user classes or tasks
            html_report: Whether to generate an HTML report
            model: Model name (optional, for saving consolidated results)
            app_num: App number (optional, for saving consolidated results)
            
        Returns:
            PerformanceResult object
        """
        import subprocess
        import csv
        
        # Set up test directory
        test_dir = self._setup_test_directory(test_name)
        csv_prefix = str(test_dir / "stats")
        
        # Create a temporary locustfile if needed
        temp_locustfile = None
        if not locustfile_path and endpoints:
            temp_locustfile = self._create_temp_locustfile(host, endpoints)
            locustfile_path = temp_locustfile
        
        try:
            # Build the Locust command
            cmd = ["locust", "-f", locustfile_path, "--host", host]
            
            if headless:
                cmd.extend(["--headless", "--users", str(user_count), 
                            "--spawn-rate", str(spawn_rate), "--run-time", run_time])
            
            # Add CSV output options
            cmd.extend(["--csv", csv_prefix])
            
            # Add worker/master options if distributed
            if workers > 0:
                cmd.extend(["--master", "--expect-workers", str(workers)])
            
            # Add tags if specified
            if tags:
                cmd.extend(["--tags", ",".join(tags)])
            
            # Run the command
            logger.info(f"Running Locust command: {' '.join(cmd)}")
            start_time = datetime.now()
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Check for failures
            if process.returncode != 0:
                logger.error(f"Locust test failed with exit code {process.returncode}: {process.stderr}")
                error_file = test_dir / "error_output.txt"
                with open(error_file, "w") as f:
                    f.write(process.stderr)
                
                # Return a basic result with error info
                result = PerformanceResult(
                    total_requests=0,
                    total_failures=0,
                    avg_response_time=0,
                    median_response_time=0,
                    requests_per_sec=0,
                    start_time=start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    end_time=end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    duration=int(duration),
                    user_count=user_count,
                    spawn_rate=spawn_rate,
                    csv_stats_path=f"{csv_prefix}_stats.csv"
                )
                
                # Save consolidated results if model and app_num are provided
                if model and app_num:
                    self._save_consolidated_results(result, model, app_num)
                    
                return result
            
            # Save command output
            output_file = test_dir / "locust_output.txt"
            with open(output_file, "w") as f:
                f.write(process.stdout)
            
            # Parse the CSV results
            stats_file = f"{csv_prefix}_stats.csv"
            result = self._parse_csv_results(
                stats_file=stats_file,
                failures_file=f"{csv_prefix}_failures.csv",
                history_file=f"{csv_prefix}_history.csv",
                start_time=start_time,
                end_time=end_time,
                user_count=user_count,
                spawn_rate=spawn_rate
            )
            
            # Generate HTML report if requested
            if html_report:
                report_path = test_dir / f"{test_name}_report.html"
                self._generate_html_report(result, report_path)
            
            # Save consolidated results if model and app_num are provided
            if model and app_num:
                self._save_consolidated_results(result, model, app_num)
            
            return result
        
        finally:
            # Clean up the temporary file if we created one
            if temp_locustfile and os.path.exists(temp_locustfile):
                try:
                    os.unlink(temp_locustfile)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_locustfile}: {e}")

    def run_test_library(
        self,
        test_name: str,
        host: str,
        user_class: Optional[type] = None,
        endpoints: Optional[List[Dict[str, Any]]] = None,
        user_count: int = 10,
        spawn_rate: int = 1,
        run_time: int = 30,
        on_start_callback: Optional[Callable] = None,
        on_stop_callback: Optional[Callable] = None
    ) -> PerformanceResult:
        """
        Run a Locust test using the library approach.
        
        Args:
            test_name: Name to identify this test
            host: Target host URL
            user_class: Custom user class (optional)
            endpoints: List of endpoint configurations (if no user_class)
            user_count: Number of concurrent users
            spawn_rate: Rate at which users are spawned per second
            run_time: Duration of the test in seconds
            on_start_callback: Function to call when the test starts
            on_stop_callback: Function to call when the test stops
            
        Returns:
            PerformanceResult object
        """
        # Set up test directory
        test_dir = self._setup_test_directory(test_name)
        csv_prefix = str(test_dir / "stats")
        
        # Create user class if needed
        if user_class is None and endpoints:
            user_class = self.create_user_class(host, endpoints)
        
        if user_class is None:
            raise ValueError("Either user_class or endpoints must be provided")
        
        # Initialize the environment
        self.environment = Environment(user_classes=[user_class])
        self.environment.create_local_runner()
        self.runner = self.environment.runner
        
        # Set up CSV stats writer
        from locust.stats import write_csv_files, PERCENTILES_TO_REPORT
        
        def write_stats_to_csv():
            """Write current stats to CSV files."""
            write_csv_files(self.environment.stats, csv_prefix)
        
        # Set up event handlers
        @events.test_start.add_listener
        def on_test_start(environment, **kwargs):
            logger.info(f"Test '{test_name}' starting with {user_count} users at {spawn_rate} users/s")
            if on_start_callback:
                on_start_callback(environment)
        
        @events.test_stop.add_listener
        def on_test_stop(environment, **kwargs):
            logger.info(f"Test '{test_name}' completed")
            # Final stats write
            write_stats_to_csv()
            if on_stop_callback:
                on_stop_callback(environment)
        
        # Start a periodic stats writer
        interval = 10  # Write stats every 10 seconds
        greenlet = gevent.spawn(stats_printer(self.environment.stats))
        stats_writer = gevent.spawn(
            lambda: [
                gevent.sleep(interval), 
                write_stats_to_csv(), 
                gevent.sleep(interval)
            ] * (run_time // interval + 1)
        )
        
        # Start the test
        start_time = datetime.now()
        self.runner.start(user_count, spawn_rate=spawn_rate)
        
        # Run for the specified time
        gevent.spawn_later(run_time, lambda: self.runner.quit())
        
        # Wait for the test to finish
        self.runner.greenlet.join()
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Clean up greenlets
        greenlet.kill(block=False)
        stats_writer.kill(block=False)
        
        # Parse results
        result = self._parse_csv_results(
            stats_file=f"{csv_prefix}_stats.csv",
            failures_file=f"{csv_prefix}_failures.csv",
            history_file=f"{csv_prefix}_history.csv",
            start_time=start_time,
            end_time=end_time,
            user_count=user_count,
            spawn_rate=spawn_rate
        )
        
        # Generate HTML report
        report_path = test_dir / f"{test_name}_report.html"
        self._generate_html_report(result, report_path)
        
        # Generate graphs
        self._generate_graphs(test_dir, result)
        
        return result

    def _create_temp_locustfile(self, host: str, endpoints: List[Dict[str, Any]]) -> str:
        """
        Create a temporary Locustfile with tasks based on endpoint definitions.
        
        Args:
            host: Target host URL
            endpoints: List of endpoint configurations
            
        Returns:
            Path to the temporary file
        """
        # Create locustfile content
        content = f"""from locust import HttpUser, task, between

class DynamicHttpUser(HttpUser):
    host = "{host}"
    wait_time = between(1, 3)
    
"""
        
        # Add a task for each endpoint
        for i, endpoint in enumerate(endpoints):
            path = endpoint['path']
            method = endpoint.get('method', 'GET').lower()
            weight = endpoint.get('weight', 1)
            
            # Build the request parameters
            params = []
            if 'params' in endpoint:
                params.append(f"params={endpoint['params']}")
            if 'data' in endpoint:
                params.append(f"data={endpoint['data']}")
            if 'json' in endpoint:
                params.append(f"json={endpoint['json']}")
            if 'headers' in endpoint:
                params.append(f"headers={endpoint['headers']}")
            
            param_str = ", ".join(params)
            task_code = f"""    @task({weight})
    def endpoint_{i}(self):
        with self.client.{method}("{path}"{f", {param_str}" if param_str else ""}, catch_response=True) as response:
            if response.status_code >= 400:
                response.failure(f"HTTP {{response.status_code}}: {{response.text}}")
                
"""
            content += task_code
        
        # Write the file
        fd, path = tempfile.mkstemp(suffix=".py", prefix="locustfile_")
        with os.fdopen(fd, "w") as f:
            f.write(content)
        
        logger.info(f"Created temporary Locustfile at {path}")
        return path

    def _parse_csv_results(
        self,
        stats_file: str,
        failures_file: str,
        history_file: str,
        start_time: datetime,
        end_time: datetime,
        user_count: int,
        spawn_rate: int
    ) -> PerformanceResult:
        """
        Parse Locust CSV results into a PerformanceResult object.
        
        Args:
            stats_file: Path to the stats CSV file
            failures_file: Path to the failures CSV file
            history_file: Path to the history CSV file
            start_time: Test start time
            end_time: Test end time
            user_count: Number of users
            spawn_rate: User spawn rate
            
        Returns:
            PerformanceResult object
        """
        # Default values
        total_requests = 0
        total_failures = 0
        avg_response_time = 0
        median_response_time = 0
        requests_per_sec = 0
        endpoints = []
        errors = []
        percentile_95 = 0
        percentile_99 = 0
        
        try:
            # Read stats file
            if os.path.exists(stats_file):
                df_stats = pd.read_csv(stats_file)
                
                # Process each endpoint
                for _, row in df_stats.iterrows():
                    # Skip aggregated stats for endpoints
                    if row['Name'] == 'Aggregated':
                        total_requests = row['Request Count']
                        total_failures = row['Failure Count']
                        avg_response_time = row['Average Response Time']
                        median_response_time = row['Median Response Time']
                        requests_per_sec = row['Requests/s']
                        
                        # Get percentiles if available
                        for col in df_stats.columns:
                            if '95%' in col:
                                percentile_95 = row[col]
                            if '99%' in col:
                                percentile_99 = row[col]
                    else:
                        # Create endpoint stats object
                        endpoint_stats = EndpointStats(
                            name=row['Name'],
                            method=row['Type'],
                            num_requests=row['Request Count'],
                            num_failures=row['Failure Count'],
                            median_response_time=row['Median Response Time'],
                            avg_response_time=row['Average Response Time'],
                            min_response_time=row['Min Response Time'],
                            max_response_time=row['Max Response Time'],
                            current_rps=row['Requests/s'],
                            current_fail_per_sec=row['Failures/s']
                        )
                        
                        # Add percentiles if available
                        percentiles = {}
                        for col in df_stats.columns:
                            if '%' in col:
                                percentile = col.strip('%').strip()
                                try:
                                    percentiles[percentile] = row[col]
                                except Exception:
                                    pass
                        
                        endpoint_stats.percentiles = percentiles
                        endpoints.append(endpoint_stats)
            
            # Read failures file
            if os.path.exists(failures_file):
                df_failures = pd.read_csv(failures_file)
                
                # Process each error
                for _, row in df_failures.iterrows():
                    error_stats = ErrorStats(
                        error_type=row['Error'],
                        count=row['Occurrences'],
                        endpoint=row.get('Name', 'unknown'),
                        method=row.get('Method', 'unknown'),
                        description=''
                    )
                    errors.append(error_stats)
            
            # Calculate duration
            duration = (end_time - start_time).total_seconds()
            
            # Create the result object
            result = PerformanceResult(
                total_requests=total_requests,
                total_failures=total_failures,
                avg_response_time=avg_response_time,
                median_response_time=median_response_time,
                requests_per_sec=requests_per_sec,
                start_time=start_time.strftime("%Y-%m-%d %H:%M:%S"),
                end_time=end_time.strftime("%Y-%m-%d %H:%M:%S"),
                duration=int(duration),
                endpoints=endpoints,
                errors=errors,
                percentile_95=percentile_95,
                percentile_99=percentile_99,
                user_count=user_count,
                spawn_rate=spawn_rate,
                csv_stats_path=stats_file
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Error parsing CSV results: {e}")
            # Return a basic result
            return PerformanceResult(
                total_requests=0,
                total_failures=0,
                avg_response_time=0,
                median_response_time=0,
                requests_per_sec=0,
                start_time=start_time.strftime("%Y-%m-%d %H:%M:%S"),
                end_time=end_time.strftime("%Y-%m-%d %H:%M:%S"),
                duration=int((end_time - start_time).total_seconds()),
                user_count=user_count,
                spawn_rate=spawn_rate,
                csv_stats_path=stats_file
            )

    def _generate_html_report(self, result: PerformanceResult, output_path: Union[str, Path]) -> None:
        """
        Generate an HTML report from test results.
        
        Args:
            result: PerformanceResult object
            output_path: Path to save the HTML report
        """
        # HTML template
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Locust Performance Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .summary {{ margin-bottom: 30px; }}
        .error {{ color: red; }}
        .chart-container {{ margin: 20px 0; height: 400px; }}
    </style>
</head>
<body>
    <h1>Locust Performance Test Report</h1>
    
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Start Time:</strong> {result.start_time}</p>
        <p><strong>End Time:</strong> {result.end_time}</p>
        <p><strong>Duration:</strong> {result.duration} seconds</p>
        <p><strong>Users:</strong> {result.user_count}</p>
        <p><strong>Spawn Rate:</strong> {result.spawn_rate} users/second</p>
        <p><strong>Total Requests:</strong> {result.total_requests}</p>
        <p><strong>Total Failures:</strong> {result.total_failures} ({(result.total_failures / result.total_requests * 100) if result.total_requests > 0 else 0:.2f}%)</p>
        <p><strong>Requests Per Second:</strong> {result.requests_per_sec:.2f}</p>
        <p><strong>Average Response Time:</strong> {result.avg_response_time:.2f} ms</p>
        <p><strong>Median Response Time:</strong> {result.median_response_time:.2f} ms</p>
        <p><strong>95th Percentile:</strong> {result.percentile_95:.2f} ms</p>
        <p><strong>99th Percentile:</strong> {result.percentile_99:.2f} ms</p>
    </div>
    
    <h2>Endpoint Details</h2>
    <table>
        <tr>
            <th>Endpoint</th>
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
"""
        
        # Add endpoint rows
        for endpoint in result.endpoints:
            p95 = endpoint.percentiles.get('95', '')
            html += f"""
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
            <td>{p95 if p95 == '' else f"{p95:.2f}"}</td>
        </tr>"""
        
        html += """
    </table>
"""
        
        # Add errors section if there are any
        if result.errors:
            html += """
    <h2>Errors</h2>
    <table>
        <tr>
            <th>Error Type</th>
            <th>Count</th>
            <th>Endpoint</th>
            <th>Method</th>
            <th>Description</th>
        </tr>
"""
            
            for error in result.errors:
                html += f"""
        <tr>
            <td class="error">{error.error_type}</td>
            <td>{error.count}</td>
            <td>{error.endpoint}</td>
            <td>{error.method}</td>
            <td>{error.description}</td>
        </tr>"""
            
            html += """
    </table>
"""
        
        # Close the HTML
        html += """
    <div class="footer">
        <p><em>Generated by LocustPerformanceTester</em></p>
    </div>
</body>
</html>
"""
        
        # Write the HTML file
        with open(output_path, 'w') as f:
            f.write(html)
        
        logger.info(f"HTML report generated at {output_path}")

    def _generate_graphs(self, test_dir: Path, result: PerformanceResult) -> None:
        """
        Generate performance graphs from test results.
        
        Args:
            test_dir: Directory to save the graphs
            result: PerformanceResult object
        """
        try:
            # Only generate graphs if we have history data
            history_file = f"{result.csv_stats_path.replace('_stats.csv', '_history.csv')}"
            if not os.path.exists(history_file):
                return
            
            # Read history data
            df = pd.read_csv(history_file)
            
            # Create time series for requests per second
            plt.figure(figsize=(10, 6))
            plt.plot(df['Timestamp'], df['Requests/s'], label='Requests/s')
            plt.title('Requests Per Second')
            plt.xlabel('Time')
            plt.ylabel('Requests/s')
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(test_dir / 'requests_per_second.png')
            
            # Create time series for response times
            plt.figure(figsize=(10, 6))
            plt.plot(df['Timestamp'], df['Average Response Time'], label='Average')
            plt.plot(df['Timestamp'], df['Median Response Time'], label='Median')
            
            # Add 95th percentile if available
            for col in df.columns:
                if '95%' in col:
                    plt.plot(df['Timestamp'], df[col], label='95th Percentile')
                    break
            
            plt.title('Response Times')
            plt.xlabel('Time')
            plt.ylabel('Response Time (ms)')
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(test_dir / 'response_times.png')
            
            # Create time series for users
            if 'User Count' in df.columns:
                plt.figure(figsize=(10, 6))
                plt.plot(df['Timestamp'], df['User Count'], label='Users')
                plt.title('Number of Users')
                plt.xlabel('Time')
                plt.ylabel('Users')
                plt.grid(True)
                plt.tight_layout()
                plt.savefig(test_dir / 'users.png')
            
            logger.info(f"Performance graphs generated in {test_dir}")
        
        except Exception as e:
            logger.error(f"Error generating graphs: {e}")