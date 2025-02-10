"""
performance_analysis.py - Performance and Usability Analysis Module

Integrates multiple testing tools:
- Locust for load testing
- Lighthouse for frontend performance
- Custom response time monitoring
- User interaction tracking
"""

import json
import os
import subprocess
import logging
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import requests
from locust import HttpUser, task, between

@dataclass
class PerformanceMetric:
    name: str
    value: float
    unit: str
    threshold: float
    status: str  # 'good', 'warning', 'critical'
    timestamp: str
    context: Dict[str, any]

@dataclass
class PerformanceReport:
    total_requests: int
    avg_response_time: float
    peak_response_time: float
    requests_per_second: float
    failure_rate: float
    metrics: List[PerformanceMetric]
    timestamp: str

class PerformanceAnalyzer:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.logger = logging.getLogger(__name__)
        self.thresholds = {
            'response_time': 200,  # ms
            'load_time': 3000,    # ms
            'cpu_usage': 80,      # percent
            'memory_usage': 80,   # percent
        }

    def run_locust_test(self, target_url: str, users: int = 10, spawn_rate: int = 1, 
                       duration: int = 60) -> Tuple[PerformanceReport, str]:
        """Run a Locust load test against the target URL."""
        try:
            # Define Locust user behavior
            class WebsiteUser(HttpUser):
                wait_time = between(1, 2)
                host = target_url

                @task
                def index_page(self):
                    self.client.get("/")

            # Run Locust programmatically
            command = [
                "locust",
                "-f", "locustfile.py",  # Create this file dynamically
                "--headless",
                f"--users={users}",
                f"--spawn-rate={spawn_rate}",
                f"--run-time={duration}s",
                "--host", target_url,
                "--json"
            ]

            result = subprocess.run(command, capture_output=True, text=True)
            stats = json.loads(result.stdout)

            # Process results
            metrics = []
            for endpoint in stats['stats']:
                metrics.append(
                    PerformanceMetric(
                        name=f"Response Time ({endpoint['name']})",
                        value=endpoint['avg_response_time'],
                        unit='ms',
                        threshold=self.thresholds['response_time'],
                        status=self._get_status(endpoint['avg_response_time'], 
                                              self.thresholds['response_time']),
                        timestamp=datetime.now().isoformat(),
                        context={'endpoint': endpoint['name']}
                    )
                )

            report = PerformanceReport(
                total_requests=sum(e['num_requests'] for e in stats['stats']),
                avg_response_time=statistics.mean(e['avg_response_time'] 
                                               for e in stats['stats']),
                peak_response_time=max(e['max_response_time'] for e in stats['stats']),
                requests_per_second=sum(e['current_rps'] for e in stats['stats']),
                failure_rate=sum(e['failure_count'] for e in stats['stats']) / 
                            sum(e['num_requests'] for e in stats['stats']) * 100,
                metrics=metrics,
                timestamp=datetime.now().isoformat()
            )

            return report, result.stdout

        except Exception as e:
            self.logger.error(f"Locust test failed: {e}")
            return None, str(e)

    def run_lighthouse_audit(self, url: str) -> Tuple[Dict[str, any], str]:
        """Run Lighthouse audit for frontend performance."""
        try:
            command = [
                "lighthouse",
                url,
                "--output=json",
                "--chrome-flags=--headless"
            ]
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Lighthouse failed: {result.stderr}")

            audit_data = json.loads(result.stdout)
            metrics = {
                'performance': audit_data['categories']['performance']['score'] * 100,
                'accessibility': audit_data['categories']['accessibility']['score'] * 100,
                'best-practices': audit_data['categories']['best-practices']['score'] * 100,
                'seo': audit_data['categories']['seo']['score'] * 100,
            }

            return metrics, result.stdout

        except Exception as e:
            self.logger.error(f"Lighthouse audit failed: {e}")
            return None, str(e)

    def monitor_system_resources(self, duration: int = 60) -> Dict[str, float]:
        """Monitor system resource usage."""
        try:
            import psutil
            cpu_usage = []
            memory_usage = []

            for _ in range(duration):
                cpu_usage.append(psutil.cpu_percent())
                memory_usage.append(psutil.virtual_memory().percent)

            return {
                'avg_cpu': statistics.mean(cpu_usage),
                'max_cpu': max(cpu_usage),
                'avg_memory': statistics.mean(memory_usage),
                'max_memory': max(memory_usage)
            }

        except Exception as e:
            self.logger.error(f"Resource monitoring failed: {e}")
            return None

    def analyze_response_times(self, url: str, requests: int = 100) -> Dict[str, float]:
        """Analyze response times for a given URL."""
        times = []
        errors = 0

        for _ in range(requests):
            try:
                start = datetime.now()
                response = requests.get(url)
                duration = (datetime.now() - start).total_seconds() * 1000
                times.append(duration)
                if response.status_code >= 400:
                    errors += 1
            except Exception:
                errors += 1

        if not times:
            return None

        return {
            'avg_response_time': statistics.mean(times),
            'median_response_time': statistics.median(times),
            'p95_response_time': statistics.quantiles(times, n=20)[18],
            'min_response_time': min(times),
            'max_response_time': max(times),
            'error_rate': (errors / requests) * 100
        }

    def _get_status(self, value: float, threshold: float) -> str:
        """Determine status based on value and threshold."""
        if value <= threshold * 0.7:
            return 'good'
        elif value <= threshold * 0.9:
            return 'warning'
        return 'critical'

    def get_analysis_summary(self, report: PerformanceReport) -> dict:
        """Generate a summary of performance analysis results."""
        return {
            'total_requests': report.total_requests,
            'avg_response_time': round(report.avg_response_time, 2),
            'peak_response_time': round(report.peak_response_time, 2),
            'requests_per_second': round(report.requests_per_second, 2),
            'failure_rate': round(report.failure_rate, 2),
            'metrics_summary': {
                'good': len([m for m in report.metrics if m.status == 'good']),
                'warning': len([m for m in report.metrics if m.status == 'warning']),
                'critical': len([m for m in report.metrics if m.status == 'critical'])
            },
            'timestamp': report.timestamp
        }