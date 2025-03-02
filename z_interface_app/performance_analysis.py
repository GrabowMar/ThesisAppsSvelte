"""
Enhanced Performance Testing Module using Locust

This module uses Locust to perform load tests on HTTP endpoints.
It supports detailed metrics collection, percentile response times, 
error analysis, and comprehensive reporting capabilities.
"""

import json
import logging
import os
import subprocess
import tempfile
import csv
import io
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

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
    response_times: Dict[str, float] = field(default_factory=dict)
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {k: v for k, v in asdict(self).items()}


class PerformanceTester:
    """
    Enhanced class to run performance tests using Locust with detailed metrics.
    
    Features:
    - Support for custom task scripts
    - Detailed endpoint statistics
    - Percentile response times
    - Error tracking and analysis
    - History statistics
    - CSV report generation
    """

    def __init__(self, base_path: Path):
        """
        Initialize the PerformanceTester.
        
        Args:
            base_path: Base directory path for storing reports and artifacts.
        """
        self.base_path = base_path
        self.locustfile: Optional[str] = None
        self.report_dir = base_path / "performance_reports"
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def _create_locustfile(self, target_host: str, endpoints: List[str] = None) -> str:
        """
        Create a temporary Locustfile with tasks to access specified endpoints.
        
        Args:
            target_host: The target host URL.
            endpoints: List of endpoints to test. Defaults to ["/"].
        
        Returns:
            The path to the temporary Locustfile.
        """
        if not endpoints:
            endpoints = ["/"]
            
        tasks = []
        for i, endpoint in enumerate(endpoints):
            weight = 10 if endpoint == "/" else 5  # Main page gets higher weight
            tasks.append(f"""
    @task({weight})
    def access_{i}(self):
        self.client.get("{endpoint}")""")
        
        locust_content = f"""from locust import HttpUser, task, between

class TestUser(HttpUser):
    wait_time = between(1, 3)
    host = "{target_host}"
    
{"".join(tasks)}

    def on_start(self):
        # Called when a user starts
        pass
        
    def on_stop(self):
        # Called when a user stops
        pass
"""
        fd, path = tempfile.mkstemp(suffix=".py", prefix="locustfile_")
        with os.fdopen(fd, "w") as f:
            f.write(locust_content)
        logger.info(f"Created temporary Locustfile at {path}")
        return path

    def _parse_locust_stats(self, stdout_str: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Parse the JSON stats from Locust stdout.
        
        Args:
            stdout_str: The stdout output from Locust containing JSON data.
            
        Returns:
            Tuple containing (endpoint stats, error stats)
        """
        try:
            # Try to parse the main JSON stats
            parsed_data = json.loads(stdout_str)
            
            # Check if it's a valid format
            if not isinstance(parsed_data, dict) and not isinstance(parsed_data, list):
                raise ValueError("Unexpected JSON format from Locust")
            
            # Handle both new and old Locust output formats
            if isinstance(parsed_data, dict):
                # New format: dictionary with 'stats' and 'errors' keys
                endpoint_stats = parsed_data.get('stats', [])
                error_stats = parsed_data.get('errors', [])
            else:
                # Old format: list of endpoint stats
                endpoint_stats = parsed_data
                error_stats = []  # No error info in old format
                
            return endpoint_stats, error_stats
            
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from Locust stdout: {e}")
            # Try to parse CSV format as fallback
            return self._try_parse_csv(stdout_str)
            
    def _try_parse_csv(self, output: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Try to parse CSV output from Locust as a fallback.
        
        Args:
            output: The output string from Locust.
            
        Returns:
            Tuple containing (endpoint stats, error stats)
        """
        endpoint_stats = []
        error_stats = []
        
        try:
            # Try to find CSV data between markers
            stats_start = output.find("Type,Name,Request Count")
            stats_end = output.find("\n\n", stats_start)
            
            if stats_start > -1 and stats_end > stats_start:
                stats_csv = output[stats_start:stats_end]
                reader = csv.DictReader(io.StringIO(stats_csv))
                for row in reader:
                    endpoint_stats.append({
                        "name": row.get("Name", "unknown"),
                        "method": row.get("Type", "GET"),
                        "num_requests": int(row.get("Request Count", 0)),
                        "num_failures": int(row.get("Failure Count", 0)),
                        "median_response_time": float(row.get("Median Response Time", 0)),
                        "avg_response_time": float(row.get("Average Response Time", 0)),
                        "min_response_time": float(row.get("Min Response Time", 0)),
                        "max_response_time": float(row.get("Max Response Time", 0)),
                        "current_rps": float(row.get("Requests/s", 0))
                    })
            
            # Try to find error data
            errors_start = output.find("Error,Occurrences")
            errors_end = output.find("\n\n", errors_start)
            
            if errors_start > -1 and errors_end > errors_start:
                errors_csv = output[errors_start:errors_end]
                reader = csv.DictReader(io.StringIO(errors_csv))
                for row in reader:
                    error_stats.append({
                        "error": row.get("Error", "unknown"),
                        "occurrences": int(row.get("Occurrences", 0))
                    })
            
        except Exception as e:
            logger.error(f"Error parsing CSV data: {e}")
            
        return endpoint_stats, error_stats

    def _create_report(self, result: PerformanceResult, model: str, port: int) -> str:
        """
        Create an HTML report for the test results.
        
        Args:
            result: The PerformanceResult object.
            model: The model identifier.
            port: The port that was tested.
            
        Returns:
            Path to the HTML report file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.report_dir / f"report_{model}_{port}_{timestamp}.html"
        
        with open(report_path, "w") as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Performance Test Report - {model}:{port}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .summary {{ margin-bottom: 30px; }}
        .error {{ color: red; }}
    </style>
</head>
<body>
    <h1>Performance Test Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Model:</strong> {model}</p>
        <p><strong>Port:</strong> {port}</p>
        <p><strong>Test Duration:</strong> {result.duration} seconds</p>
        <p><strong>Start Time:</strong> {result.start_time}</p>
        <p><strong>End Time:</strong> {result.end_time}</p>
        <p><strong>Users:</strong> {result.user_count}</p>
        <p><strong>Spawn Rate:</strong> {result.spawn_rate} users/second</p>
        <p><strong>Total Requests:</strong> {result.total_requests}</p>
        <p><strong>Total Failures:</strong> {result.total_failures}</p>
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
        </tr>""")
            
            for endpoint in result.endpoints:
                f.write(f"""
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
        </tr>""")
            
            f.write("""
    </table>""")
            
            if result.errors:
                f.write("""
    <h2>Errors</h2>
    <table>
        <tr>
            <th>Error Type</th>
            <th>Count</th>
            <th>Endpoint</th>
            <th>Method</th>
            <th>Description</th>
        </tr>""")
                
                for error in result.errors:
                    f.write(f"""
        <tr>
            <td class="error">{error.error_type}</td>
            <td>{error.count}</td>
            <td>{error.endpoint}</td>
            <td>{error.method}</td>
            <td>{error.description}</td>
        </tr>""")
                    
                f.write("""
    </table>""")
            
            f.write("""
</body>
</html>""")
        
        return str(report_path)

    def run_test(
        self,
        model: str,
        port: int,
        num_users: int = 10,
        duration: int = 30,
        spawn_rate: int = 1,
        endpoints: List[str] = None
    ) -> Tuple[Optional[PerformanceResult], Dict[str, Any]]:
        """
        Run a performance test using Locust with detailed metrics.
        
        Args:
            model: Model identifier (for logging and reporting).
            port: Port number of the target backend.
            num_users: Number of concurrent users to simulate.
            duration: Test duration in seconds.
            spawn_rate: Rate at which users are spawned per second.
            endpoints: List of endpoints to test. Defaults to ["/"].
        
        Returns:
            A tuple containing a PerformanceResult object (or None on failure) and a status dictionary.
        """
        try:
            # Build the target host URL
            host = f"http://localhost:{port}"
            logger.info(f"Target host: {host}")

            # Create a temporary Locustfile
            self.locustfile = self._create_locustfile(host, endpoints)

            # Build the Locust command with additional options
            cmd = [
                "locust",
                "-f", self.locustfile,
                "--headless",
                "--host", host,
                "--users", str(num_users),
                "--spawn-rate", str(spawn_rate),
                "--run-time", f"{duration}s",
                "--csv", str(self.report_dir / f"stats_{model}_{port}"),
                "--json",  # For JSON output
                "--only-summary"  # Reduce console output except for the summary
            ]
            logger.info(f"Running Locust command: {' '.join(cmd)}")

            start_time = datetime.now()
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=duration + 30,  # Extra time for startup and shutdown
                env=os.environ.copy()
            )
            end_time = datetime.now()

            if process.returncode != 0:
                logger.error(f"Locust test failed with exit code {process.returncode}: {process.stderr}")
                return None, {
                    "status": "failed", 
                    "error": process.stderr,
                    "command": " ".join(cmd)
                }

            # Parse the JSON stats from stdout
            stdout_str = process.stdout.strip()
            if not stdout_str:
                logger.error("Locust output (stdout) is empty.")
                return None, {"status": "error", "error": "Locust stdout is empty."}

            # Parse statistics
            endpoint_stats, error_stats = self._parse_locust_stats(stdout_str)
            
            # Process endpoint statistics
            endpoints_data = []
            total_requests = 0
            total_failures = 0
            avg_response_times = []
            median_response_times = []
            
            for stat in endpoint_stats:
                if stat.get('name') != 'Aggregated':  # Skip the aggregated stats
                    endpoint = EndpointStats(
                        name=stat.get('name', 'unknown'),
                        method=stat.get('method', 'GET'),
                        num_requests=stat.get('num_requests', 0),
                        num_failures=stat.get('num_failures', 0),
                        median_response_time=stat.get('median_response_time', 0),
                        avg_response_time=stat.get('avg_response_time', 0),
                        min_response_time=stat.get('min_response_time', 0),
                        max_response_time=stat.get('max_response_time', 0),
                        avg_content_length=stat.get('avg_content_length', 0),
                        current_rps=stat.get('current_rps', 0),
                        current_fail_per_sec=stat.get('current_fail_per_sec', 0),
                        response_times=stat.get('response_times', {}),
                        percentiles=stat.get('response_time_percentiles', {})
                    )
                    endpoints_data.append(endpoint)
                    
                    total_requests += endpoint.num_requests
                    total_failures += endpoint.num_failures
                    
                    if endpoint.num_requests > 0:
                        avg_response_times.append(endpoint.avg_response_time)
                        median_response_times.append(endpoint.median_response_time)
            
            # Process error statistics
            errors_data = []
            for error in error_stats:
                error_data = ErrorStats(
                    error_type=error.get('error', 'unknown'),
                    count=error.get('occurrences', 0),
                    endpoint=error.get('name', 'unknown'),
                    method=error.get('method', 'unknown'),
                    description=error.get('description', '')
                )
                errors_data.append(error_data)
            
            # Calculate overall statistics
            avg_response = sum(avg_response_times) / len(avg_response_times) if avg_response_times else 0
            median_response = sum(median_response_times) / len(median_response_times) if median_response_times else 0
            
            # Get percentiles from aggregated stats if available
            percentile_95 = 0
            percentile_99 = 0
            
            for stat in endpoint_stats:
                if stat.get('name') == 'Aggregated':
                    percentiles = stat.get('response_time_percentiles', {})
                    percentile_95 = percentiles.get('95', 0)
                    percentile_99 = percentiles.get('99', 0)
                    break
            
            # Approximate requests per second
            requests_per_sec = total_requests / duration if duration > 0 else 0
            
            # Create the result object
            result = PerformanceResult(
                total_requests=total_requests,
                total_failures=total_failures,
                avg_response_time=avg_response,
                median_response_time=median_response,
                requests_per_sec=requests_per_sec,
                start_time=start_time.strftime("%Y-%m-%d %H:%M:%S"),
                end_time=end_time.strftime("%Y-%m-%d %H:%M:%S"),
                duration=duration,
                endpoints=endpoints_data,
                errors=errors_data,
                percentile_95=percentile_95,
                percentile_99=percentile_99,
                user_count=num_users,
                spawn_rate=spawn_rate
            )
            
            # Generate the HTML report
            report_path = self._create_report(result, model, port)
            
            logger.info(f"Performance test completed successfully. Report saved to {report_path}")
            return result, {
                "status": "success", 
                "output": process.stdout,
                "report_path": report_path
            }

        except subprocess.TimeoutExpired:
            logger.error("Performance test timed out")
            return None, {"status": "timeout", "error": "Test timed out"}
        except Exception as e:
            logger.error(f"Performance test error: {e}")
            return None, {"status": "error", "error": str(e)}
        finally:
            self._cleanup()

    def _cleanup(self):
        """Clean up temporary files created during the test."""
        if self.locustfile and os.path.exists(self.locustfile):
            try:
                os.unlink(self.locustfile)
                logger.info(f"Deleted temporary Locustfile: {self.locustfile}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary Locustfile {self.locustfile}: {e}")