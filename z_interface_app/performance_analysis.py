"""
Simple performance testing module using Locust.
Tests basic HTTP endpoints for load testing.
"""

import json
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceResult:
    """Store performance test results"""
    total_requests: int
    total_failures: int
    avg_response_time: float
    median_response_time: float
    requests_per_sec: float
    start_time: str
    end_time: str
    duration: int

class PerformanceTester:
    """Simple performance testing using Locust"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.stats_file = None
        self.locustfile = None

    def _create_locustfile(self, host: str) -> str:
        """Create a temporary Locustfile with basic tests"""
        content = f'''
from locust import HttpUser, task, between

class TestUser(HttpUser):
    wait_time = between(1, 3)
    host = "{host}"
    
    @task
    def test_api_health(self):
        self.client.get("/api/health")
        
    @task
    def test_api_status(self):
        self.client.get("/api/status")
'''
        # Create temporary file
        fd, path = tempfile.mkstemp(suffix='.py')
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        return path

    def run_test(
        self,
        model: str,
        app_num: int,
        num_users: int = 10,
        duration: int = 30,
        spawn_rate: int = 1
    ) -> Tuple[Optional[PerformanceResult], Dict[str, str]]:
        """Run a performance test"""
        try:
            # Calculate backend port (simplified)
            base_port = 5001
            backend_port = base_port + app_num
            host = f"http://localhost:{backend_port}"

            # Create temporary files
            self.locustfile = self._create_locustfile(host)
            fd, self.stats_file = tempfile.mkstemp(suffix='.json')
            os.close(fd)

            # Build locust command
            cmd = [
                "locust",
                "-f", self.locustfile,
                "--headless",
                "--host", host,
                "--users", str(num_users),
                "--spawn-rate", str(spawn_rate),
                "--run-time", f"{duration}s",
                "--json", self.stats_file
            ]

            # Run the test
            start_time = datetime.now()
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=duration + 10
            )
            end_time = datetime.now()

            # Check if test was successful
            if process.returncode != 0:
                logger.error(f"Locust test failed: {process.stderr}")
                return None, {
                    "status": "failed",
                    "error": process.stderr
                }

            # Parse results
            with open(self.stats_file, 'r') as f:
                stats = json.load(f)

            # Create result object
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
            # Cleanup temporary files
            self._cleanup()

    def _cleanup(self):
        """Clean up temporary files"""
        try:
            if self.stats_file and os.path.exists(self.stats_file):
                os.unlink(self.stats_file)
            if self.locustfile and os.path.exists(self.locustfile):
                os.unlink(self.locustfile)
        except Exception as e:
            logger.warning(f"Cleanup failed: {str(e)}")

def main():
    """Test function"""
    base_path = Path(__file__).parent
    tester = PerformanceTester(base_path)
    
    result, info = tester.run_test(
        model="test",
        app_num=1,
        num_users=5,
        duration=10,
        spawn_rate=1
    )
    
    if result:
        print(f"Test completed successfully:")
        print(f"Total requests: {result.total_requests}")
        print(f"Average response time: {result.avg_response_time:.2f}ms")
        print(f"Requests per second: {result.requests_per_sec:.2f}")
    else:
        print(f"Test failed: {info.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()