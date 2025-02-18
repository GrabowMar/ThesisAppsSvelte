"""
Performance Testing Module using Locust

This module uses Locust to perform a load test on the main HTTP endpoint ("/").
It generates a temporary Locustfile, runs a headless performance test, and returns
test results. Stats are parsed from Locust's JSON output in stdout.
"""

import json
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceResult:
    """Data class to store performance test results."""
    total_requests: int
    total_failures: int
    avg_response_time: float
    median_response_time: float
    requests_per_sec: float
    start_time: str
    end_time: str
    duration: int


class PerformanceTester:
    """
    Class to run performance tests using Locust, parsing JSON stats from stdout.

    Requirements:
    - Locust must be installed.
    - The Locust plugin/feature that prints JSON to stdout must be available.
    """

    def __init__(self, base_path: Path):
        """
        Initialize the PerformanceTester.
        
        Args:
            base_path: Base directory path (reserved for future use).
        """
        self.base_path = base_path
        self.locustfile: Optional[str] = None

    def _create_locustfile(self, target_host: str) -> str:
        """
        Create a temporary Locustfile that defines a simple task to access the main page.
        
        Args:
            target_host: The target host URL.
        
        Returns:
            The path to the temporary Locustfile.
        """
        locust_content = f"""\
from locust import HttpUser, task, between

class TestUser(HttpUser):
    wait_time = between(1, 3)
    host = "{target_host}"
    
    @task
    def access_main_page(self):
        # Access the main page ("/")
        self.client.get("/")
"""
        fd, path = tempfile.mkstemp(suffix=".py", prefix="locustfile_")
        with os.fdopen(fd, "w") as f:
            f.write(locust_content)
        logger.info(f"Created temporary Locustfile at {path}")
        return path

    def run_test(
        self,
        model: str,
        port: int,
        num_users: int = 10,
        duration: int = 30,
        spawn_rate: int = 1
    ) -> Tuple[Optional[PerformanceResult], Dict[str, str]]:
        """
        Run a performance test using Locust, capturing JSON stats from stdout.
        
        Args:
            model: A model identifier (for logging or future use).
            port: Port number of the target backend.
            num_users: Number of concurrent users.
            duration: Test duration in seconds.
            spawn_rate: Rate at which users are spawned.
        
        Returns:
            A tuple containing a PerformanceResult (or None on failure) and a status dictionary.
        """
        try:
            # Build the target host URL.
            host = f"http://localhost:{port}"
            logger.info(f"Target host: {host}")

            # Create a temporary Locustfile.
            self.locustfile = self._create_locustfile(host)

            # Build the Locust command.
            # NOTE: We rely on the plugin/feature that prints JSON to stdout.
            # If this doesn't work, check that your Locust version supports JSON output.
            cmd = [
                "locust",
                "-f", self.locustfile,
                "--headless",
                "--host", host,
                "--users", str(num_users),
                "--spawn-rate", str(spawn_rate),
                "--run-time", f"{duration}s",
                "--json"
            ]
            logger.info(f"Running Locust command: {' '.join(cmd)}")

            start_time = datetime.now()
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=duration + 10,
                env=os.environ.copy()
            )
            end_time = datetime.now()

            if process.returncode != 0:
                logger.error(f"Locust test failed: {process.stderr}")
                return None, {"status": "failed", "error": process.stderr}

            # Parse the JSON stats from stdout.
            stdout_str = process.stdout.strip()
            if not stdout_str:
                logger.error("Locust output (stdout) is empty.")
                return None, {"status": "error", "error": "Locust stdout is empty."}

            try:
                # Locust might print an array of stats objects, e.g.:
                # [
                #   {
                #     "name": "/",
                #     "method": "GET",
                #     "num_requests": 128,
                #     "num_failures": 0,
                #     "total_response_time": 4096.56,
                #     "max_response_time": 132.15,
                #     "min_response_time": 9.26,
                #     ...
                #   }
                # ]
                parsed_stats = json.loads(stdout_str)
                if not isinstance(parsed_stats, list) or len(parsed_stats) == 0:
                    raise ValueError("Parsed JSON does not contain a list of stats objects.")

                # For simplicity, assume a single endpoint. If multiple, sum or aggregate as needed.
                endpoint_stats = parsed_stats[0]
                num_requests = endpoint_stats.get("num_requests", 0)
                total_response_time = endpoint_stats.get("total_response_time", 0)
                # Compute average response time if num_requests > 0
                avg_response = (total_response_time / num_requests) if num_requests > 0 else 0.0

                # For median, we don't have it directly in the JSON. You can compute it
                # if you wish by analyzing "response_times" distribution. For now, we'll keep it simple.
                median_response = avg_response  # Placeholder

                # We'll approximate requests_per_sec by dividing total requests by duration.
                requests_per_sec = (num_requests / duration) if duration > 0 else 0.0

            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from Locust stdout: {e}")
                return None, {"status": "error", "error": "Could not parse JSON from Locust output."}
            except Exception as parse_err:
                logger.error(f"Error interpreting Locust JSON stats: {parse_err}")
                return None, {"status": "error", "error": str(parse_err)}

            # Build the result.
            result = PerformanceResult(
                total_requests=num_requests,
                total_failures=endpoint_stats.get("num_failures", 0),
                avg_response_time=avg_response,
                median_response_time=median_response,
                requests_per_sec=requests_per_sec,
                start_time=start_time.strftime("%Y-%m-%d %H:%M:%S"),
                end_time=end_time.strftime("%Y-%m-%d %H:%M:%S"),
                duration=duration
            )

            logger.info("Performance test completed successfully.")
            return result, {"status": "success", "output": process.stdout}

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
