import json
import logging
import os
import re
import tempfile
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Callable, Tuple, TypedDict
import socket
import io

from locust import HttpUser, task, constant, events, between
from locust.env import Environment
from locust.stats import stats_printer, StatsEntry, RequestStats, sort_stats
from locust.runners import Runner, LocalRunner
import gevent
import pandas as pd
import matplotlib.pyplot as plt

# Import JsonResultsManager from utils.py for standardized file handling
from utils import JsonResultsManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EndpointStats:
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
    error_type: str
    count: int
    endpoint: str
    method: str
    description: str = ""


@dataclass
class GraphInfo(TypedDict):
    name: str
    url: str


@dataclass
class PerformanceResult:
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
    test_name: str = ""
    host: str = ""
    graph_urls: List[GraphInfo] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['endpoints'] = [asdict(endpoint) for endpoint in self.endpoints]
        result['errors'] = [asdict(error) for error in self.errors]
        result['graph_urls'] = list(self.graph_urls)
        return result

    def save_json(self, file_path: Union[str, Path]) -> None:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Performance results saved to {file_path}")


class UserGenerator:
    @staticmethod
    def create_http_user(host: str, endpoints: List[Dict[str, Any]]) -> type:
        class_attrs = {
            'host': host,
            'wait_time': between(1, 3)
        }

        for i, endpoint in enumerate(endpoints):
            path = endpoint['path']
            method = endpoint.get('method', 'GET').lower()
            weight = endpoint.get('weight', 1)
            ep_name_part = re.sub(r"[^a-zA-Z0-9_]", "_", path.strip('/')).lower()
            if not ep_name_part: ep_name_part = "root"
            task_name = endpoint.get('name', f"task_{method}_{ep_name_part}_{i}")

            def create_task_fn(captured_path, captured_method, captured_endpoint_config):
                def task_fn(self: HttpUser):
                    kwargs = {}
                    for param in ['params', 'data', 'json', 'headers', 'files']:
                        if param in captured_endpoint_config:
                            kwargs[param] = captured_endpoint_config[param]

                    request_name = captured_endpoint_config.get('request_name', captured_path)
                    kwargs['name'] = request_name

                    request_method_func = getattr(self.client, captured_method)
                    with request_method_func(captured_path, catch_response=True, **kwargs) as response:
                        validators = captured_endpoint_config.get('validators')
                        if validators and callable(validators):
                            try:
                                validators(response)
                            except Exception as val_err:
                                response.failure(f"Validator failed: {val_err}")
                        elif not response.ok:
                            response.failure(f"HTTP {response.status_code}")
                task_fn.__name__ = task_name
                task_fn.__doc__ = f"Task for {captured_method.upper()} {captured_path}"
                return task_fn

            task_fn_instance = create_task_fn(path, method, endpoint)
            decorated_task = task(weight)(task_fn_instance)
            class_attrs[task_name] = decorated_task

        DynamicUserClass = type('DynamicHttpUser', (HttpUser,), class_attrs)
        logger.debug(f"Created DynamicHttpUser class with tasks: {list(class_attrs.keys())}")
        return DynamicUserClass


class LocustPerformanceTester:
    def __init__(self, output_dir: Union[str, Path], static_url_path: str = "/static"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.static_url_path = "/" + static_url_path.strip('/')
        logger.info(f"PerformanceTester initialized. Output dir: {self.output_dir}, Static URL path: {self.static_url_path}")
        self.current_test_dir: Optional[Path] = None
        self.environment: Optional[Environment] = None
        self.runner: Optional[Runner] = None
        
        # Initialize JsonResultsManager for standardized results handling
        self.results_manager = JsonResultsManager(base_path=self.output_dir, module_name="performance")

    def _save_consolidated_results(self,
                                   result: PerformanceResult,
                                   model: str,
                                   app_num: int) -> str:
        """
        Save performance results using JsonResultsManager.
        
        Args:
            result: The performance result to save
            model: Model name
            app_num: Application number
            
        Returns:
            Path to the saved results file
        """
        try:
            # Use JsonResultsManager to save results
            file_name = ".locust_result.json"
            results_path = self.results_manager.save_results(
                model=model,
                app_num=app_num,
                results=result,
                file_name=file_name,
                maintain_legacy=False
            )
            logger.info(f"Saved consolidated performance results for {model}/app{app_num} using JsonResultsManager")
            return str(results_path)
        except Exception as e:
            logger.exception(f"Error saving consolidated results for {model}/app{app_num}: {e}")
            return ""

    def load_performance_results(self, model: str, app_num: int) -> Optional[PerformanceResult]:
        """
        Load performance test results for a specific model and app number.
        
        Args:
            model: Model name
            app_num: Application number
            
        Returns:
            PerformanceResult object or None if results not found
        """
        try:
            file_name = ".locust_result.json"
            data = self.results_manager.load_results(
                model=model,
                app_num=app_num,
                file_name=file_name
            )
            
            if not data:
                logger.warning(f"No performance results found for {model}/app{app_num}")
                return None
                
            # Convert dictionary back to PerformanceResult object
            result = PerformanceResult(
                total_requests=data.get('total_requests', 0),
                total_failures=data.get('total_failures', 0),
                avg_response_time=data.get('avg_response_time', 0.0),
                median_response_time=data.get('median_response_time', 0.0),
                requests_per_sec=data.get('requests_per_sec', 0.0),
                start_time=data.get('start_time', ''),
                end_time=data.get('end_time', ''),
                duration=data.get('duration', 0),
                user_count=data.get('user_count', 0),
                spawn_rate=data.get('spawn_rate', 0),
                test_name=data.get('test_name', ''),
                host=data.get('host', '')
            )
            
            # Load endpoints
            if 'endpoints' in data:
                result.endpoints = [
                    EndpointStats(**endpoint) for endpoint in data['endpoints']
                ]
            
            # Load errors
            if 'errors' in data:
                result.errors = [
                    ErrorStats(**error) for error in data['errors']
                ]
            
            # Load other fields
            result.percentile_95 = data.get('percentile_95', 0.0)
            result.percentile_99 = data.get('percentile_99', 0.0)
            result.graph_urls = data.get('graph_urls', [])
            
            logger.info(f"Successfully loaded performance results for {model}/app{app_num}")
            return result
        except Exception as e:
            logger.error(f"Error loading performance results for {model}/app{app_num}: {e}")
            return None
            
    def get_latest_test_result(self, model: str, port: int) -> Optional[PerformanceResult]:
        """
        Get the latest test result for a specific model and port.
        
        Args:
            model: Model name
            port: Application port
            
        Returns:
            PerformanceResult object or None if not found
        """
        try:
            # Determine app_num from port
            from utils import get_app_info
            app_info = get_app_info(port)
            if not app_info or 'app_num' not in app_info:
                logger.warning(f"Could not determine app_num from port {port}")
                return None
                
            app_num = app_info['app_num']
            return self.load_performance_results(model, app_num)
        except Exception as e:
            logger.error(f"Error getting latest test result for {model}/port{port}: {e}")
            return None

    def _setup_test_directory(self, test_name: str) -> Path:
        safe_test_name = re.sub(r'[<>:"/\\|?*\s]+', '_', test_name)
        test_dir = self.output_dir / "performance_reports" / safe_test_name
        test_dir.mkdir(parents=True, exist_ok=True)
        self.current_test_dir = test_dir
        logger.info(f"Test artifacts directory set up at: {test_dir}")
        return test_dir

    def create_user_class(self, host: str, endpoints: List[Dict[str, Any]]) -> type:
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
        html_report: bool = True,
        model: Optional[str] = None,
        app_num: Optional[int] = None,
        force_rerun: bool = False
    ) -> Optional[PerformanceResult]:
        """
        Run a Locust performance test using the CLI.
        
        Args:
            test_name: Name for the test
            host: Target host URL
            locustfile_path: Path to Locust file (optional)
            endpoints: List of endpoint configurations (used if no locustfile_path)
            user_count: Number of users to simulate
            spawn_rate: Rate at which to spawn users
            run_time: Test duration as string (e.g. "30s", "5m")
            headless: Whether to run in headless mode
            workers: Number of worker processes
            tags: Tags to filter tasks
            html_report: Whether to generate HTML report
            model: Optional model name for result organization
            app_num: Optional app number for result organization
            force_rerun: Whether to force rerun the test
            
        Returns:
            PerformanceResult object with test results or None if test fails
        """
        import subprocess
        import csv
        
        # Check for cached results if model and app_num are provided and not forcing rerun
        if model and app_num and not force_rerun:
            cached_result = self.load_performance_results(model, app_num)
            if cached_result:
                logger.info(f"Using cached performance results for {model}/app{app_num}")
                return cached_result

        # Generate full test name with timestamp if needed
        if not re.search(r'_\d{8}_\d{6}$', test_name):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            full_test_name = f"{test_name}_{timestamp}"
        else:
            full_test_name = test_name

        test_dir = self._setup_test_directory(full_test_name)
        csv_prefix = str(test_dir / "stats")

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
            cmd = ["locust", "-f", locustfile_path, "--host", host]
            if headless:
                cmd.extend(["--headless", "--users", str(user_count),
                            "--spawn_rate", str(spawn_rate), "--run-time", run_time])
            else:
                pass

            cmd.extend(["--csv", csv_prefix, "--csv-full-history"])

            if html_report:
                html_file_path = test_dir / f"{test_dir.name}_locust_report.html"
                cmd.extend(["--html", str(html_file_path)])

            if workers > 0:
                cmd.extend(["--master", "--expect-workers", str(workers)])

            if tags:
                cmd.extend(["--tags"] + tags)

            logger.info(f"Running Locust command: {' '.join(cmd)}")
            start_time = datetime.now()

            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                check=False
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"Locust process finished in {duration:.2f}s with exit code {process.returncode}")

            output_file = test_dir / "locust_output.txt"
            with open(output_file, "w", encoding='utf-8') as f:
                f.write("--- STDOUT ---\n")
                f.write(process.stdout if process.stdout else "[No stdout]")
                f.write("\n\n--- STDERR ---\n")
                f.write(process.stderr if process.stderr else "[No stderr]")
            logger.info(f"Locust output saved to {output_file}")

            if process.returncode != 0:
                logger.error(f"Locust test failed with exit code {process.returncode}.")
                return None

            stats_file = f"{csv_prefix}_stats.csv"
            failures_file = f"{csv_prefix}_failures.csv"
            history_file = f"{csv_prefix}_stats_history.csv"

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
            if result is None:
                logger.error("Failed to parse CSV results.")
                return None

            result.test_name = full_test_name
            result.host = host

            graph_infos = self._generate_graphs_from_csv(history_file, test_dir)
            result.graph_urls = graph_infos

            # Save results using JsonResultsManager if model and app_num are provided
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
            if temp_locustfile and os.path.exists(temp_locustfile):
                try:
                    os.unlink(temp_locustfile)
                    logger.debug(f"Deleted temporary locustfile: {temp_locustfile}")
                except Exception as e_unlink:
                    logger.warning(f"Failed to delete temporary file {temp_locustfile}: {e_unlink}")

    def _extract_stats_from_environment(
        self,
        stats: RequestStats,
        start_time: datetime,
        end_time: datetime,
        user_count: int,
        spawn_rate: int
    ) -> PerformanceResult:
        logger.info("Extracting stats directly from Locust environment...")
        endpoints: List[EndpointStats] = []
        errors: List[ErrorStats] = []

        sorted_entries = sort_stats(stats.entries)
        for entry in sorted_entries:
            if entry.name == "Aggregated":
                continue

            percentiles_dict = {}
            try:
                for p in RequestStats.PERCENTILES_TO_REPORT:
                    percentile_value = entry.get_response_time_percentile(p)
                    percentiles_dict[f"{p*100:.0f}"] = percentile_value if percentile_value is not None else 0.0
            except Exception as p_err:
                logger.warning(f"Could not calculate percentiles for {entry.name}: {p_err}")

            ep_stats = EndpointStats(
                name=entry.name,
                method=entry.method or "N/A",
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

        for error_key, error_entry in stats.errors.items():
            err_stats = ErrorStats(
                error_type=str(error_entry.error),
                count=error_entry.occurrences,
                endpoint=error_entry.name or "N/A",
                method=error_entry.method or "N/A",
                description=str(error_entry.error)
            )
            errors.append(err_stats)

        total_entry = stats.total
        duration_sec = max((end_time - start_time).total_seconds(), 0.1)

        total_p95 = total_entry.get_response_time_percentile(0.95) or 0.0
        total_p99 = total_entry.get_response_time_percentile(0.99) or 0.0

        result = PerformanceResult(
            total_requests=total_entry.num_requests,
            total_failures=total_entry.num_failures,
            avg_response_time=total_entry.avg_response_time or 0.0,
            median_response_time=total_entry.median_response_time or 0.0,
            requests_per_sec=(total_entry.num_requests / duration_sec),
            start_time=start_time.strftime("%Y-%m-%d %H:%M:%S"),
            end_time=end_time.strftime("%Y-%m-%d %H:%M:%S"),
            duration=int(duration_sec),
            endpoints=endpoints,
            errors=errors,
            percentile_95=total_p95,
            percentile_99=total_p99,
            user_count=user_count,
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
        run_time: int = 30,
        generate_graphs: bool = True,
        on_start_callback: Optional[Callable[[Environment], None]] = None,
        on_stop_callback: Optional[Callable[[Environment], None]] = None,
        model: Optional[str] = None,
        app_num: Optional[int] = None,
        force_rerun: bool = False
    ) -> PerformanceResult:
        """
        Run a Locust performance test using the library API.
        
        Args:
            test_name: Name for the test
            host: Target host URL
            user_class: Optional user class for the test
            endpoints: List of endpoint configurations (required if user_class not provided)
            user_count: Number of users to simulate
            spawn_rate: Rate at which to spawn users
            run_time: Test duration in seconds
            generate_graphs: Whether to generate performance graphs
            on_start_callback: Optional callback when test starts
            on_stop_callback: Optional callback when test ends
            model: Optional model name for result organization
            app_num: Optional app number for result organization
            force_rerun: Whether to force rerun the test instead of using cached results
            
        Returns:
            PerformanceResult object with test results
        """
        # Check for cached results if model and app_num are provided and not forcing rerun
        if model and app_num and not force_rerun:
            cached_result = self.load_performance_results(model, app_num)
            if cached_result:
                logger.info(f"Using cached performance results for {model}/app{app_num}")
                return cached_result
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_test_name = f"{test_name}_{timestamp}"
        test_dir = self._setup_test_directory(full_test_name)

        if user_class is None and endpoints:
            user_class = self.create_user_class(host, endpoints)
        if user_class is None:
            raise ValueError("Either user_class or endpoints must be provided")

        self.environment = None
        self.runner = None
        self.environment = Environment(user_classes=[user_class], host=host, catch_exceptions=True)
        self.environment.create_local_runner()
        if not self.environment.runner:
            raise RuntimeError("Failed to create Locust runner.")
        self.runner = self.environment.runner
        self.environment.custom_data = {}

        @events.test_start.add_listener
        def on_test_start(environment: Environment, **kwargs):
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

        self.runner.start(user_count, spawn_rate=spawn_rate)
        logger.info(f"Locust runner started. Waiting for {run_time} seconds...")

        stopper_greenlet = None
        try:
            def stopper():
                gevent.sleep(run_time)
                logger.info(f"Run time ({run_time}s) elapsed. Stopping runner for test '{full_test_name}'...")
                if self.runner:
                    self.runner.quit()
                    logger.info("Runner quit signal sent.")
                else:
                    logger.warning("Stopper executed but runner was None.")
            stopper_greenlet = gevent.spawn(stopper)
            self.runner.greenlet.join()
            logger.info("Runner greenlet joined (test run finished).")
        except KeyboardInterrupt:
            logger.warning("Test run interrupted by user (KeyboardInterrupt). Stopping runner...")
            if self.runner: self.runner.quit()
        except Exception as run_err:
            logger.exception(f"Error during runner execution or join for test '{full_test_name}': {run_err}")
            if self.runner: self.runner.quit()
            raise RuntimeError(f"Locust run failed: {run_err}") from run_err
        finally:
            if stopper_greenlet and not stopper_greenlet.dead:
                stopper_greenlet.kill(block=False)
                logger.debug("Stopper greenlet killed.")

        end_time = datetime.now()
        logger.info(f"Test '{full_test_name}' finished execution at {end_time.isoformat()}")
        start_time = self.environment.custom_data.get('start_time')
        if start_time is None:
            logger.warning("Start time not found on environment.custom_data! Using approximate start based on end time and duration.")
            start_time = end_time - timedelta(seconds=run_time)
        else:
            logger.info(f"Actual test start time recorded: {start_time.isoformat()}")

        if not self.environment or not self.environment.stats:
            raise RuntimeError("Locust environment or stats object not available after test run.")

        result = self._extract_stats_from_environment(
            stats=self.environment.stats,
            start_time=start_time,
            end_time=end_time,
            user_count=user_count,
            spawn_rate=spawn_rate
        )
        result.test_name = full_test_name
        result.host = host

        if generate_graphs:
            try:
                graph_infos = self._generate_graphs_from_history(self.environment.stats.history, test_dir)
                result.graph_urls = graph_infos
            except Exception as graph_err:
                logger.error(f"Failed to generate graphs for test '{full_test_name}': {graph_err}", exc_info=True)
                result.graph_urls = []

        # Save results using JsonResultsManager if model and app_num are provided
        if model is not None and app_num is not None:
            self._save_consolidated_results(result, model, app_num)

        self.environment = None
        self.runner = None
        logger.debug("Environment and runner references cleared.")
        logger.info(f"Returning results for test {full_test_name}")
        return result

    def _create_temp_locustfile(self, host: str, endpoints: List[Dict[str, Any]], test_dir: Path) -> str:
        content = f"""# Auto-generated Locustfile for {test_dir.name}
from locust import HttpUser, task, between
import json

class DynamicHttpUser(HttpUser):
    host = "{host}"
    wait_time = between(1, 3)
    print(f"DynamicHttpUser targeting host: {{host}}")
"""
        for i, endpoint in enumerate(endpoints):
            path = endpoint['path']
            method = endpoint.get('method', 'GET').lower()
            weight = endpoint.get('weight', 1)
            ep_name_part = re.sub(r"[^a-zA-Z0-9_]", "_", path.strip('/')).lower()
            if not ep_name_part: ep_name_part = "root"
            func_name = f"task_{method}_{ep_name_part}_{i}"
            request_name = endpoint.get('request_name', path)
            params_list = []
            params_list.append(f'name="{request_name}"')
            params_list.append('catch_response=True')
            if 'params' in endpoint: params_list.append(f"params={endpoint['params']!r}")
            if 'data' in endpoint: params_list.append(f"data={endpoint['data']!r}")
            if 'json' in endpoint: params_list.append(f"json={endpoint['json']!r}")
            if 'headers' in endpoint: params_list.append(f"headers={endpoint['headers']!r}")
            param_str = ", ".join(params_list)
            task_code = f"""
    @task({weight})
    def {func_name}(self):
        with self.client.{method}("{path}", {param_str}) as response:
            if not response.ok:
                response.failure(f"HTTP {{response.status_code}}")
"""
            content += task_code
        locustfile_path = test_dir / f"locustfile_{test_dir.name}.py"
        try:
            with open(locustfile_path, "w", encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Created temporary Locustfile for CLI run at {locustfile_path}")
            return str(locustfile_path)
        except Exception as e:
            logger.error(f"Failed to write temporary locustfile {locustfile_path}: {e}", exc_info=True)
            raise

    def _parse_csv_results(
        self,
        stats_file: str,
        failures_file: str,
        start_time: datetime,
        end_time: datetime,
        user_count: int,
        spawn_rate: int
    ) -> Optional[PerformanceResult]:
        total_requests, total_failures = 0, 0
        avg_response_time, median_response_time, requests_per_sec = 0.0, 0.0, 0.0
        percentile_95, percentile_99 = 0.0, 0.0
        endpoints: List[EndpointStats] = []
        errors: List[ErrorStats] = []

        try:
            stats_path = Path(stats_file)
            if stats_path.exists() and stats_path.stat().st_size > 0:
                df_stats = pd.read_csv(stats_file)
                num_cols = ['Request Count', 'Failure Count', 'Median Response Time', 'Average Response Time', 'Min Response Time', 'Max Response Time', 'Average Content Size', 'Requests/s', 'Failures/s']
                percentile_cols = [col for col in df_stats.columns if '%' in col]
                num_cols.extend(percentile_cols)
                for col in num_cols:
                    if col in df_stats.columns:
                        df_stats[col] = pd.to_numeric(df_stats[col], errors='coerce').fillna(0)
                    else:
                        logger.warning(f"Expected numeric column '{col}' not found in {stats_file}")

                for _, row in df_stats.iterrows():
                    is_aggregated = row['Name'] == 'Aggregated'
                    percentiles_dict = {}
                    p95_val, p99_val = 0.0, 0.0
                    for p_col in percentile_cols:
                        if p_col in row:
                            p_key = p_col.replace('%', '').strip()
                            p_val = row.get(p_col, 0.0)
                            percentiles_dict[p_key] = p_val
                            if '95' in p_key: p95_val = p_val
                            if '99' in p_key: p99_val = p_val
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
                            method=row.get('Type', 'Unknown Method'),
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
                return None

            failures_path = Path(failures_file)
            if failures_path.exists() and failures_path.stat().st_size > 0:
                df_failures = pd.read_csv(failures_file)
                df_failures['Occurrences'] = pd.to_numeric(df_failures['Occurrences'], errors='coerce').fillna(0).astype(int)
                for _, row in df_failures.iterrows():
                    error_stats = ErrorStats(
                        method=row.get('Method', 'N/A'),
                        endpoint=row.get('Name', 'N/A'),
                        error_type=row.get('Error', 'Unknown Error'),
                        count=int(row.get('Occurrences', 0)),
                        description=row.get('Error', '')
                    )
                    errors.append(error_stats)
            else:
                logger.warning(f"Failures CSV file not found or is empty: {failures_file}")

            duration = max((end_time - start_time).total_seconds(), 0.1)
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
                spawn_rate=spawn_rate
            )
            logger.info(f"Successfully parsed CSV results for test ending {result.end_time}")
            return result
        except pd.errors.EmptyDataError as e:
            logger.warning(f"CSV parsing failed: File was empty ({e})")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error parsing CSV results: {e}")
            return None

    def _generate_graphs_from_history(self, history: List[StatsEntry], test_dir: Path) -> List[GraphInfo]:
        graph_infos: List[GraphInfo] = []
        if not history:
            logger.warning("No history data provided for graph generation.")
            return graph_infos
        try:
            history_data = [h.to_dict() for h in history]
            df = pd.DataFrame(history_data)
            if df.empty or 'time' not in df.columns:
                logger.warning("History DataFrame is empty or missing 'time' column after conversion.")
                return graph_infos
            try:
                df['time_dt'] = pd.to_datetime(df['time'])
            except Exception as time_err:
                logger.error(f"Could not parse history time column: {time_err}. Using index.", exc_info=True)
                df['time_dt'] = pd.to_datetime(df.index, unit='s', origin=pd.Timestamp(history[0].time) if history else 'unix')

            plt.style.use('seaborn-v0_8-whitegrid')
            if 'current_rps' in df.columns and 'current_fail_per_sec' in df.columns:
                plt.figure(figsize=(12, 6))
                plt.plot(df['time_dt'], df['current_rps'], label='Requests/s', color='tab:blue', linewidth=1.5)
                plt.plot(df['time_dt'], df['current_fail_per_sec'], label='Failures/s', color='tab:red', linestyle='--', linewidth=1)
                plt.title('Requests and Failures Per Second Over Time')
                plt.xlabel('Time')
                plt.ylabel('Rate (per second)')
                plt.legend()
                plt.grid(True, which='both', linestyle='--', linewidth=0.5)
                plt.tight_layout()
                rps_path = test_dir / 'requests_failures_per_second.png'
                plt.savefig(rps_path)
                plt.close()
                graph_url = f"{self.static_url_path}/{rps_path.relative_to(self.output_dir).as_posix()}"
                graph_infos.append({"name": "RPS & Failures/s", "url": graph_url})
            else:
                logger.warning("Skipping RPS graph: 'current_rps' or 'current_fail_per_sec' column missing.")

            required_rt_cols = ['median_response_time', 'avg_response_time']
            if all(col in df.columns for col in required_rt_cols):
                plt.figure(figsize=(12, 6))
                plt.plot(df['time_dt'], df['avg_response_time'], label='Average RT', color='tab:green', linewidth=1.5)
                plt.plot(df['time_dt'], df['median_response_time'], label='Median RT (P50)', color='tab:orange', linestyle='-', linewidth=1.5)
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
            return []

    def _generate_graphs_from_csv(self, history_csv_path: str, test_dir: Path) -> List[GraphInfo]:
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
            try:
                df['time_dt'] = pd.to_datetime(df['Timestamp'], unit='s', errors='coerce')
                df.dropna(subset=['time_dt'], inplace=True)
                if df.empty:
                    logger.warning("No valid timestamps found in history CSV after conversion.")
                    return graph_infos
            except Exception as time_err:
                logger.error(f"Could not parse history timestamp column: {time_err}. Using index.", exc_info=True)
                df['time_dt'] = df.index
            plt.style.use('seaborn-v0_8-whitegrid')
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
            rt_cols = ['Average Response Time', 'Median Response Time']
            if all(col in df.columns for col in rt_cols):
                plt.figure(figsize=(12, 6))
                plt.plot(df['time_dt'], df['Average Response Time'], label='Average RT', color='tab:green', linewidth=1.5)
                plt.plot(df['time_dt'], df['Median Response Time'], label='Median RT (P50)', color='tab:orange', linewidth=1.5)
                p95_col = next((col for col in df.columns if '95%' in col), None)
                if p95_col:
                    df[p95_col] = pd.to_numeric(df[p95_col], errors='coerce')
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
            return []

    def get_performance_summary(self, result: PerformanceResult) -> Dict[str, Any]:
        """
        Generate a summary of performance test results.
        
        Args:
            result: PerformanceResult object
            
        Returns:
            Dictionary with summary information
        """
        # Define base results directory
        results_dir = self.base_path / "results"
        
        summary = {
            "total_requests": result.total_requests,
            "total_failures": result.total_failures,
            "failure_rate": round((result.total_failures / result.total_requests * 100) if result.total_requests else 0, 2),
            "avg_response_time": round(result.avg_response_time, 2),
            "median_response_time": round(result.median_response_time, 2),
            "percentile_95": round(result.percentile_95, 2),
            "percentile_99": round(result.percentile_99, 2),
            "requests_per_sec": round(result.requests_per_sec, 2),
            "user_count": result.user_count,
            "duration": result.duration,
            "test_name": result.test_name,
            "start_time": result.start_time,
            "end_time": result.end_time,
            "results_path": str(results_dir),  # Add results directory path
            "top_endpoints": [],
            "error_count": len(result.errors),
            "scan_time": datetime.now().isoformat()
        }
        
        # Add top 5 endpoints by request count
        sorted_endpoints = sorted(result.endpoints, key=lambda e: e.num_requests, reverse=True)
        summary["top_endpoints"] = [
            {
                "name": endpoint.name,
                "method": endpoint.method,
                "requests": endpoint.num_requests,
                "failures": endpoint.num_failures,
                "avg_response_time": round(endpoint.avg_response_time, 2)
            }
            for endpoint in sorted_endpoints[:5]
        ]
        
        # Add performance rating based on response time and failure rate
        if result.avg_response_time < 100 and summary["failure_rate"] < 1:
            summary["performance_rating"] = "Excellent"
        elif result.avg_response_time < 300 and summary["failure_rate"] < 5:
            summary["performance_rating"] = "Good"
        elif result.avg_response_time < 1000 and summary["failure_rate"] < 10:
            summary["performance_rating"] = "Fair"
        else:
            summary["performance_rating"] = "Poor"
            
        return summary