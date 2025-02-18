"""
Simple performance testing module using Locust.
Tests the main HTTP endpoint ("/") for load testing.
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
    """Store performance test results."""
    total_requests: int
    total_failures: int
    avg_response_time: float
    median_response_time: float
    requests_per_sec: float
    start_time: str
    end_time: str
    duration: int


class PerformanceTester:
    """Simple performance testing using Locust."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        # Temporary file paths for the Locustfile and stats.
        self.stats_file: Optional[str] = None
        self.locustfile: Optional[str] = None

    def _create_locustfile(self, target_host: str) -> str:
        """
        Create a temporary Locustfile with a single task that accesses the main page.
        
        Args:
            target_host: The target host URL.
        
        Returns:
            The path to the temporary Locustfile.
        """
        locust_content = f'''
from locust import HttpUser, task, between

class TestUser(HttpUser):
    wait_time = between(1, 3)
    host = "{target_host}"
    
    @task
    def access_main_page(self):
        # Simply access the main page
        self.client.get("/")
'''
        fd, path = tempfile.mkstemp(suffix='.py')
        with os.fdopen(fd, 'w') as f:
            f.write(locust_content)
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
        Run a performance test using Locust.
        
        Args:
            model: Model identifier (for logging or future use).
            port: The port number of the target backend.
            num_users: Number of concurrent users.
            duration: Test duration in seconds.
            spawn_rate: User spawn rate per second.
        
        Returns:
            A tuple containing a PerformanceResult (or None on failure)
            and a dictionary with status information.
        """
        try:
            # Build the target host using the passed port.
            host = f"http://localhost:{port}"

            # Create temporary files for the Locustfile and JSON stats.
            self.locustfile = self._create_locustfile(host)
            fd, self.stats_file = tempfile.mkstemp(suffix='.json')
            os.close(fd)

            # Prepare environment so that Locust writes stats to our file.
            env = os.environ.copy()
            env["LOCUST_STATS_OUTPUT"] = self.stats_file

            # Build the Locust command.
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

            start_time = datetime.now()
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=duration + 10,
                env=env
            )
            end_time = datetime.now()

            if process.returncode != 0:
                logger.error(f"Locust test failed: {process.stderr}")
                return None, {
                    "status": "failed",
                    "error": process.stderr
                }

            # Read the JSON stats written by Locust.
            with open(self.stats_file, 'r') as f:
                stats = json.load(f)

            result = PerformanceResult(
                total_requests=stats.get("total_requests", 0),
                total_failures=stats.get("total_failures", 0),
                avg_response_time=stats.get("avg_response_time", 0),
                median_response_time=stats.get("median_response_time", 0),
                requests_per_sec=stats.get("current_rps", 0),
                start_time=start_time.strftime("%Y-%m-%d %H:%M:%S"),
                end_time=end_time.strftime("%Y-%m-%d %H:%M:%S"),
                duration=duration
            )

            return result, {
                "status": "success",
                "output": process.stdout
            }

        except subprocess.TimeoutExpired:
            logger.error("Performance test timed out")
            return None, {
                "status": "timeout",
                "error": "Test timed out"
            }
        except Exception as e:
            logger.error(f"Performance test error: {str(e)}")
            return None, {
                "status": "error",
                "error": str(e)
            }
        finally:
            self._cleanup()

    def _cleanup(self):
        """Clean up temporary files created during the test."""
        try:
            if self.stats_file and os.path.exists(self.stats_file):
                os.unlink(self.stats_file)
            if self.locustfile and os.path.exists(self.locustfile):
                os.unlink(self.locustfile)
        except Exception as e:
            logger.warning(f"Cleanup failed: {str(e)}")