"""
Refactored Flask-based AI Model Management System

A Flask application that:
- Manages Docker-based frontend/backend apps
- Uses the Python Docker library for container operations
- Handles both synchronous and asynchronous workflows
"""

# Standard library imports
import asyncio
import dataclasses  # For advanced dataclass operations
import json
import logging
import os
import random
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Third-party imports
import docker
from docker.errors import NotFound
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from werkzeug.exceptions import BadRequest
from werkzeug.middleware.proxy_fix import ProxyFix

# Custom module imports (assumed to be available in the project)
from codacy_analysis import CodacyAnalyzer
from frontend_security_analysis import FrontendSecurityAnalyzer
from gpt4all_analysis import GPT4AllAnalyzer, get_analysis_summary
from performance_analysis import PerformanceTester
from security_analysis import SecurityAnalyzer
from zap_scanner import ZAPScanner, create_scanner

# Module-level logger for consistent logging throughout the application.
logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
@dataclass
class AppConfig:
	"""
	Application configuration parameters.
	
	These are read from environment variables with sensible defaults.
	"""
	DEBUG: bool = True
	SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "your-secret-key-here")
	BASE_DIR: Path = Path(__file__).parent
	LOG_LEVEL: str = os.getenv("LOG_LEVEL", "ERROR")
	DOCKER_TIMEOUT: int = int(os.getenv("DOCKER_TIMEOUT", "10"))
	CACHE_DURATION: int = int(os.getenv("CACHE_DURATION", "5"))
	# Use different host values for production and development environments.
	HOST: str = "0.0.0.0" if os.getenv("FLASK_ENV") == "production" else "127.0.0.1"
	PORT: int = int(os.getenv("PORT", "5000"))

	

	@classmethod
	def from_env(cls) -> "AppConfig":
		"""Create an AppConfig instance using environment variables."""
		return cls()


# -------------------------------------------------------------------
# Domain Models
# -------------------------------------------------------------------
@dataclass
class AIModel:
	"""Represents an AI model with its name and an associated color."""
	name: str
	color: str


@dataclass
class DockerStatus:
	"""
	Represents the status of a Docker container.
	
	Attributes include existence, running status, health, status text,
	and additional details.
	"""
	exists: bool = False
	running: bool = False
	health: str = "unknown"
	status: str = "unknown"
	details: str = ""

	def to_dict(self) -> Dict[str, Any]:
		"""Convert the DockerStatus instance to a dictionary."""
		return asdict(self)


# -------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------
# List of supported AI models with their colors.
AI_MODELS: List[AIModel] = [
	AIModel("ChatGPT4o", "#10a37f"),
	AIModel("ChatGPTo1", "#0ea47f"),
	AIModel("ChatGPTo3", "#0ca57f"),
	AIModel("ClaudeSonnet", "#7b2bf9"),
	AIModel("CodeLlama", "#f97316"),
	AIModel("Gemini", "#1a73e8"),
	AIModel("Grok", "#ff4d4f"),
	AIModel("Mixtral", "#9333ea"),
	AIModel("DeepSeek", "#ff5555"),
	AIModel("Qwen", "#fa541c"),
]


# -------------------------------------------------------------------
# Logging Configuration
# -------------------------------------------------------------------
class StatusEndpointFilter(logging.Filter):
	"""
	Filter to exclude log entries for routine container status checks.
	This helps reduce noise in the logs.
	"""
	def filter(self, record: logging.LogRecord) -> bool:
		if not hasattr(record, "args") or len(record.args) < 3:
			return True
		msg = record.args[2] if isinstance(record.args[2], str) else ""
		# Do not log the typical HTTP 200 messages for container status requests.
		return "GET /api/container/" not in msg or not msg.endswith(' HTTP/1.1" 200 -')


class LoggingService:
	"""
	Provides a static method to configure logging settings.
	"""
	@staticmethod
	def configure(log_level: str) -> None:
		# Basic configuration for logging (level and format).
		logging.basicConfig(
			level=getattr(logging, log_level),
			format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
		)
		# Adjust log levels for specific loggers to reduce unnecessary output.
		logging.getLogger("werkzeug").addFilter(StatusEndpointFilter())
		logging.getLogger("zap_scanner").setLevel(logging.INFO)
		logging.getLogger("owasp_zap").setLevel(logging.WARNING)  # Reduce ZAP API noise


# -------------------------------------------------------------------
# Port Management
# -------------------------------------------------------------------
class PortManager:
	"""
	Manages port allocation for backend and frontend services.
	
	Each model is allocated a range of ports based on its index.
	"""
	BASE_BACKEND_PORT = 5001
	BASE_FRONTEND_PORT = 5501
	PORTS_PER_APP = 2
	BUFFER_PORTS = 20
	APPS_PER_MODEL = 20

	@classmethod
	def get_port_range(cls, model_idx: int) -> Dict[str, Dict[str, int]]:
		"""
		Calculate and return the port ranges for backend and frontend for a given model index.
		"""
		total_needed = cls.APPS_PER_MODEL * cls.PORTS_PER_APP + cls.BUFFER_PORTS
		return {
			"backend": {
				"start": cls.BASE_BACKEND_PORT + (model_idx * total_needed),
				"end": cls.BASE_BACKEND_PORT + ((model_idx + 1) * total_needed) - cls.BUFFER_PORTS,
			},
			"frontend": {
				"start": cls.BASE_FRONTEND_PORT + (model_idx * total_needed),
				"end": cls.BASE_FRONTEND_PORT + ((model_idx + 1) * total_needed) - cls.BUFFER_PORTS,
			},
		}

	@classmethod
	def get_app_ports(cls, model_idx: int, app_num: int) -> Dict[str, int]:
		"""
		Given a model index and app number, compute the specific ports for backend and frontend.
		"""
		rng = cls.get_port_range(model_idx)
		return {
			"backend": rng["backend"]["start"] + (app_num - 1) * cls.PORTS_PER_APP,
			"frontend": rng["frontend"]["start"] + (app_num - 1) * cls.PORTS_PER_APP,
		}


# -------------------------------------------------------------------
# Docker Management
# -------------------------------------------------------------------
class DockerManager:
	"""
	Handles Docker-related operations such as fetching container statuses,
	retrieving logs, and cleaning up stopped containers.
	"""
	def __init__(self, client: Optional[docker.DockerClient] = None) -> None:
		self.logger = logging.getLogger(__name__)
		# Create a Docker client or use an existing one if provided.
		self.client = client or self._create_docker_client()
		# Cache to store container statuses along with timestamps.
		self._cache: Dict[str, Tuple[float, DockerStatus]] = {}
		self._cache_duration = AppConfig.from_env().CACHE_DURATION
		self._lock = asyncio.Lock()  # For thread-safe async operations.

	def _create_docker_client(self) -> Optional[docker.DockerClient]:
		"""
		Create and return a Docker client instance.
		"""
		try:
			docker_host = os.getenv("DOCKER_HOST", "npipe:////./pipe/docker_engine")
			return docker.DockerClient(
				base_url=docker_host,
				timeout=AppConfig.from_env().DOCKER_TIMEOUT,
			)
		except Exception as e:
			self.logger.error(f"Docker client creation failed: {e}")
			return None

	def get_container_status(self, container_name: str) -> DockerStatus:
		"""
		Get the status of a container. If the status is cached and still valid,
		return the cached version; otherwise, fetch a new status.
		"""
		now = time.time()
		if container_name in self._cache:
			timestamp, status = self._cache[container_name]
			if now - timestamp < self._cache_duration:
				return status

		status = self._fetch_container_status(container_name)
		self._cache[container_name] = (now, status)
		return status

	def _fetch_container_status(self, container_name: str) -> DockerStatus:
		"""
		Fetch container status information directly from Docker.
		"""
		if not self.client:
			return DockerStatus(
				exists=False,
				status="error",
				details="Docker client unavailable",
			)
		try:
			container = self.client.containers.get(container_name)
			is_running = container.status == "running"
			state = container.attrs.get("State", {})
			health = state.get("Health", {}).get("Status", "healthy" if is_running else "stopped")
			return DockerStatus(
				exists=True,
				running=is_running,
				health=health,
				status=container.status,
				details=state.get("Status", "unknown"),
			)
		except NotFound:
			return DockerStatus(
				exists=False,
				status="no_container",
				details="Container not found",
			)
		except Exception as e:
			self.logger.error(f"Docker error for {container_name}: {e}")
			return DockerStatus(exists=False, status="error", details=str(e))

	def get_container_logs(self, container_name: str, tail: int = 100) -> str:
		"""
		Retrieve and return the logs for a given container.
		"""
		if not self.client:
			return "Docker client unavailable"
		try:
			container = self.client.containers.get(container_name)
			return container.logs(tail=tail).decode("utf-8")
		except Exception as e:
			self.logger.error(f"Log retrieval failed for {container_name}: {e}")
			return f"Log retrieval error: {e}"

	def cleanup_containers(self) -> None:
		"""
		Clean up containers that have been stopped for over 24 hours.
		"""
		if not self.client:
			return
		try:
			self.client.containers.prune(filters={"until": "24h"})
		except Exception as e:
			self.logger.error(f"Container cleanup failed: {e}")


# -------------------------------------------------------------------
# System Health Monitoring
# -------------------------------------------------------------------
class SystemHealthMonitor:
	"""
	Provides methods to monitor system health aspects such as disk space and Docker connectivity.
	"""
	@staticmethod
	def check_disk_space() -> bool:
		"""
		Check whether disk usage is below a critical threshold.
		Returns True if disk space is sufficient.
		"""
		try:
			if os.name == "nt":
				# Windows disk space check using WMIC.
				result = subprocess.run(
					["wmic", "logicaldisk", "get", "size,freespace,caption"],
					capture_output=True,
					text=True,
					check=True,
				)
				lines = result.stdout.strip().split("\n")[1:]
				for line in lines:
					parts = line.split()
					if len(parts) >= 3:
						try:
							free = int(parts[1])
							total = int(parts[2])
							if total > 0 and (total - free) / total * 100 > 90:
								logging.warning(f"Disk usage critical: {parts[0]}")
								return False
						except ValueError:
							continue
			else:
				# Unix-based systems disk space check using the 'df' command.
				result = subprocess.run(
					["df", "-h"], capture_output=True, text=True, check=True
				)
				lines = result.stdout.split("\n")[1:]
				for line in lines:
					if line and (fields := line.split()) and len(fields) >= 5:
						if int(fields[4].rstrip("%")) > 90:
							logging.warning(f"Disk usage critical: {fields[5]}")
							return False
		except Exception as e:
			logging.error(f"Disk check failed: {e}")
			return False
		return True

	@staticmethod
	def check_health(docker_client: Optional[docker.DockerClient]) -> bool:
		"""
		Check overall system health by ensuring Docker is responsive and disk space is adequate.
		"""
		if not docker_client:
			logging.error("No Docker client")
			return False
		try:
			docker_client.ping()
			return SystemHealthMonitor.check_disk_space()
		except Exception as e:
			logging.error(f"Health check failed: {e}")
			return False


# -------------------------------------------------------------------
# Utility Functions & Decorators
# -------------------------------------------------------------------
def error_handler(f):
	"""
	Decorator for route handlers to catch exceptions.
	For AJAX requests, returns a JSON error; otherwise, renders an error page.
	"""
	@wraps(f)
	def wrapped(*args, **kwargs):
		try:
			return f(*args, **kwargs)
		except Exception as e:
			logger.error(f"Error in {f.__name__}: {e}")
			if request.headers.get("X-Requested-With") == "XMLHttpRequest":
				return jsonify({"error": str(e)}), 500
			return render_template("500.html"), 500

	return wrapped


def get_model_index(model_name: str) -> int:
	"""
	Retrieve the index of the given model from the AI_MODELS list.
	"""
	return next((i for i, m in enumerate(AI_MODELS) if m.name == model_name), 0)


def get_container_names(model: str, app_num: int) -> Tuple[str, str]:
	"""
	Generate the Docker container names for the backend and frontend
	based on the model name and application number.
	"""
	idx = get_model_index(model)
	ports = PortManager.get_app_ports(idx, app_num)
	base = model.lower()
	return (
		f"{base}_backend_{ports['backend']}",
		f"{base}_frontend_{ports['frontend']}",
	)


def get_app_info(model_name: str, app_num: int) -> Dict[str, Any]:
	"""
	Construct and return information about a specific application instance,
	including its URLs and port numbers.
	"""
	idx = get_model_index(model_name)
	model_color = next((m.color for m in AI_MODELS if m.name == model_name), "#666666")
	ports = PortManager.get_app_ports(idx, app_num)
	return {
		"name": f"{model_name} App {app_num}",
		"model": model_name,
		"color": model_color,
		"backend_port": ports["backend"],
		"frontend_port": ports["frontend"],
		"app_num": app_num,
		"backend_url": f"http://localhost:{ports['backend']}",
		"frontend_url": f"http://localhost:{ports['frontend']}",
	}


def get_apps_for_model(model_name: str) -> List[Dict[str, Any]]:
	"""
	Retrieve all application instances for a given model by scanning the model directory.
	"""
	base_path = Path(f"{model_name}")
	if not base_path.exists():
		return []
	apps = []
	# Filter directories starting with "app" and sort them numerically.
	app_dirs = sorted(
		(d for d in base_path.iterdir() if d.is_dir() and d.name.startswith("app")),
		key=lambda x: int(x.name.replace("app", "")),
	)
	for app_dir in app_dirs:
		try:
			app_num = int(app_dir.name.replace("app", ""))
			apps.append(get_app_info(model_name, app_num))
		except ValueError as e:
			logger.error(f"Error processing {app_dir}: {e}")
	return apps


def get_all_apps() -> List[Dict[str, Any]]:
	"""
	Retrieve information for all application instances across all defined AI models.
	"""
	return [app_info for model in AI_MODELS for app_info in get_apps_for_model(model.name)]


def run_docker_compose(
	command: List[str],
	model: str,
	app_num: int,
	timeout: int = 60,
	check: bool = True,
) -> Tuple[bool, str]:
	"""
	Run a docker-compose command for a specific application's directory.
	
	Returns a tuple of (success: bool, output: str).
	"""
	app_dir = Path(f"{model}/app{app_num}")
	if not app_dir.exists():
		return False, f"Directory not found: {app_dir}"

	try:
		result = subprocess.run(
			["docker-compose"] + command,
			cwd=app_dir,
			check=check,
			capture_output=True,
			text=True,
			timeout=timeout,
		)
		success = result.returncode == 0
		output = result.stdout or result.stderr
		return success, output
	except subprocess.TimeoutExpired:
		return False, f"Timeout after {timeout}s"
	except Exception as e:
		return False, str(e)


def handle_docker_action(action: str, model: str, app_num: int) -> Tuple[bool, str]:
	"""
	Handle Docker actions (start, stop, reload, rebuild, build) for a given application.
	"""
	commands = {
		"start": [("up", "-d", 120)],
		"stop": [("down", None, 30)],
		"reload": [("restart", None, 90)],
		"rebuild": [
			("down", None, 30),
			("build", None, 300),
			("up", "-d", 120),
		],
		"build": [("build", None, 300)],
	}
	if action not in commands:
		return False, f"Invalid action: {action}"

	# Execute each command in the sequence for the specified action.
	for base_cmd, extra_arg, timeout in commands[action]:
		cmd = [base_cmd] + ([extra_arg] if extra_arg else [])
		success, msg = run_docker_compose(cmd, model, app_num, timeout=timeout)
		if not success:
			logger.error(f"Docker {action} failed on {cmd}: {msg}")
			return False, msg
	return True, f"Successfully completed {action}"


def verify_container_health(
	docker_manager: DockerManager,
	model: str,
	app_num: int,
	max_retries: int = 10,
	retry_delay: int = 3,
) -> Tuple[bool, str]:
	"""
	Verify that both the backend and frontend Docker containers for an app are healthy.
	Retries the check a specified number of times before failing.
	"""
	backend_name, frontend_name = get_container_names(model, app_num)
	for _ in range(max_retries):
		backend = docker_manager.get_container_status(backend_name)
		frontend = docker_manager.get_container_status(frontend_name)
		if backend.health == "healthy" and frontend.health == "healthy":
			return True, "All containers healthy"
		time.sleep(retry_delay)
	return False, "Containers failed to reach healthy state"


def process_security_analysis(
	template: str,
	analyzer,
	analysis_method,
	model: str,
	app_num: int,
	full_scan: bool,
	no_issue_message: str,
):
	"""
	Helper to process security analysis and render the given template.
	
	Calls the provided analysis_method and unpacks its results.
	"""
	try:
		# Run the analysis method to obtain issues and tool outputs.
		issues, tool_status, tool_output_details = analysis_method(
			model, app_num, use_all_tools=full_scan
		)
		if not issues:
			# Render the template with a message if no issues are found.
			return render_template(
				template,
				model=model,
				app_num=app_num,
				issues=[],
				summary=analyzer.get_analysis_summary([]),
				error=None,
				message=no_issue_message,
				full_scan=full_scan,
				tool_status=tool_status,
				tool_output_details=tool_output_details,
			)
		summary = analyzer.get_analysis_summary(issues)
		return render_template(
			template,
			model=model,
			app_num=app_num,
			issues=issues,
			summary=summary,
			error=None,
			full_scan=full_scan,
			tool_status=tool_status,
			tool_output_details=tool_output_details,
		)
	except ValueError as e:
		logger.warning(f"No files to analyze: {e}")
		return render_template(
			template,
			model=model,
			app_num=app_num,
			issues=None,
			error=str(e),
			full_scan=full_scan,
			tool_status={},
			tool_output_details={},
		)
	except Exception as e:
		logger.error(f"Security analysis failed: {e}")
		return render_template(
			template,
			model=model,
			app_num=app_num,
			issues=None,
			error=f"Security analysis failed: {str(e)}",
			full_scan=full_scan,
			tool_status={},
			tool_output_details={},
		)


# -------------------------------------------------------------------
# Flask App Factory & Route Registration
# -------------------------------------------------------------------
def create_app(config: Optional[AppConfig] = None) -> Flask:
	"""
	Application factory function.
	
	Creates and configures the Flask application, initializes analyzers,
	the Docker manager, and registers all routes and error handlers.
	"""
	app = Flask(__name__)
	app.config.from_object(config or AppConfig.from_env())
	LoggingService.configure(app.config["LOG_LEVEL"])

	base_path = AppConfig.from_env().BASE_DIR.parent
	logger.info(f"Initializing analyzers with base path: {base_path}")

	# Initialize various analysis tools and attach them to the app instance.
	app.security_analyzer = SecurityAnalyzer(base_path)
	app.frontend_security_analyzer = FrontendSecurityAnalyzer(base_path)
	app.codacy_analyzer = CodacyAnalyzer(base_path)
	zap_scanner = create_scanner(app)
	app.zap_scanner = zap_scanner  # Make scanner available on app
	app.json_encoder = CustomJSONEncoder
	

	docker_manager = DockerManager()
	# Use ProxyFix to handle proxy headers correctly.
	app.wsgi_app = ProxyFix(app.wsgi_app)

	# Register application routes, error handlers, and request hooks.
	register_routes(app, docker_manager)
	register_error_handlers(app)
	register_request_hooks(app, docker_manager)

	return app


class CustomJSONEncoder(json.JSONEncoder):
	"""
	Custom JSON encoder to handle objects that have a __dict__ attribute.
	"""
	def default(self, obj):
		if hasattr(obj, "__dict__"):
			return obj.__dict__
		return super().default(obj)


def register_routes(app: Flask, docker_manager: DockerManager) -> None:
	"""
	Register all HTTP routes (endpoints) for the Flask application.
	"""
	@app.route("/")
	@error_handler
	def index():
		"""
		Render the main index page with a list of all applications and their container statuses.
		"""
		apps = get_all_apps()
		for app_info in apps:
			b_name, f_name = get_container_names(app_info["model"], app_info["app_num"])
			app_info["backend_status"] = docker_manager.get_container_status(b_name)
			app_info["frontend_status"] = docker_manager.get_container_status(f_name)
		return render_template("index.html", apps=apps, models=AI_MODELS)

	@app.route("/status/<string:model>/<int:app_num>")
	@error_handler
	def check_app_status(model: str, app_num: int):
		"""
		Check the status of a specific application and either return JSON for AJAX
		requests or flash a message and redirect.
		"""
		b_name, f_name = get_container_names(model, app_num)
		status = {
			"backend": docker_manager.get_container_status(b_name).to_dict(),
			"frontend": docker_manager.get_container_status(f_name).to_dict(),
		}
		if request.headers.get("X-Requested-With") == "XMLHttpRequest":
			return jsonify(status)
		flash(f"Status checked for {model} App {app_num}", "info")
		return redirect(url_for("index"))

	@app.route("/api/container/<string:model>/<int:app_num>/status")
	@error_handler
	def container_status(model: str, app_num: int):
		"""
		API endpoint to return container status as JSON.
		"""
		b_name, f_name = get_container_names(model, app_num)
		status = {
			"backend": docker_manager.get_container_status(b_name).to_dict(),
			"frontend": docker_manager.get_container_status(f_name).to_dict(),
		}
		return jsonify(status)

	@app.route("/zap/<string:model>/<int:app_num>")
	@error_handler
	def zap_scan(model: str, app_num: int):
		"""
		Display the ZAP scan page with previously saved results if available.
		"""
		try:
			# Initialize the ZAP scanner with the base directory.
			scanner = ZAPScanner(app.config["BASE_DIR"])
			# Define the results file path.
			results_file = app.config["BASE_DIR"] / f"{model}/app{app_num}/.zap_results.json"
			alerts = []
			error_msg = None
			if results_file.exists():
				try:
					with open(results_file) as f:
						data = json.load(f)
						alerts = data.get("alerts", [])
				except Exception as e:
					error_msg = f"Failed to load previous results: {e}"
			return render_template(
				"zap_scan.html",
				model=model,
				app_num=app_num,
				alerts=alerts,
				error=error_msg,
			)
		except Exception as e:
			logger.error(f"Error in ZAP scan page: {e}")
			return render_template(
				"zap_scan.html",
				model=model,
				app_num=app_num,
				alerts=[],
				error=str(e),
			)

	@app.route("/api/zap/scan/<string:model>/<int:app_num>", methods=["POST"])
	@error_handler
	def start_zap_scan(model: str, app_num: int):
		"""
		Start a ZAP scan asynchronously and return the scan ID.
		"""
		try:
			data = request.get_json()
			# Initialize the ZAP scanner.
			scanner = ZAPScanner(app.config["BASE_DIR"])
			# Calculate the target URL based on the app's frontend port.
			frontend_port = 5501 + ((app_num - 1) * 2)
			target_url = f"http://localhost:{frontend_port}"
			# Create a unique scan ID.
			scan_id = f"{model}-{app_num}-{int(time.time())}"
			app.config["ZAP_SCANS"] = app.config.get("ZAP_SCANS", {})
			app.config["ZAP_SCANS"][scan_id] = {
				"status": "Starting",
				"progress": 0,
				"scanner": scanner,
				"start_time": datetime.now().isoformat(),
				"options": data,
			}

			# Define a function to run the scan in a background thread.
			def run_scan():
				try:
					vulnerabilities, summary = scanner.scan_target(
						target_url,
						scan_policy=data.get("scanPolicy")
					)
					# Save the scan results to a JSON file.
					results_file = app.config["BASE_DIR"] / f"{model}/app{app_num}/.zap_results.json"
					with open(results_file, "w") as f:
						json.dump(
							{
								"alerts": [asdict(v) for v in vulnerabilities],
								"summary": summary,
								"scan_time": datetime.now().isoformat(),
							},
							f,
							indent=2,
						)
					# Update the scan status.
					app.config["ZAP_SCANS"][scan_id]["status"] = "Complete"
					app.config["ZAP_SCANS"][scan_id]["progress"] = 100
				except Exception as e:
					logger.error(f"Scan error: {e}")
					app.config["ZAP_SCANS"][scan_id]["status"] = f"Failed: {e}"

			# Start the scan in a new thread.
			import threading
			thread = threading.Thread(target=run_scan)
			thread.start()
			return jsonify({"status": "started", "scan_id": scan_id})
		except Exception as e:
			logger.error(f"Failed to start ZAP scan: {e}")
			return jsonify({"error": str(e)}), 500

	@app.route("/api/zap/scan/<string:model>/<int:app_num>/status")
	@error_handler
	def zap_scan_status(model: str, app_num: int):
		"""
		Return the status and progress of a ZAP scan.
		"""
		try:
			# Locate the scan corresponding to the model and app number.
			scan_id = None
			for sid, scan in app.config.get("ZAP_SCANS", {}).items():
				if sid.startswith(f"{model}-{app_num}-"):
					scan_id = sid
					break
			if not scan_id:
				return jsonify({"status": "Not Started", "progress": 0})
			scan = app.config["ZAP_SCANS"][scan_id]
			# Read the results file to count alerts.
			results_file = app.config["BASE_DIR"] / f"{model}/app{app_num}/.zap_results.json"
			counts = {"high": 0, "medium": 0, "low": 0, "info": 0}
			if results_file.exists():
				with open(results_file) as f:
					data = json.load(f)
					for alert in data.get("alerts", []):
						risk = alert.get("risk", "").lower()
						if risk in counts:
							counts[risk] += 1
			return jsonify({
				"status": scan["status"],
				"progress": scan["progress"],
				"high_count": counts["high"],
				"medium_count": counts["medium"],
				"low_count": counts["low"],
				"info_count": counts["info"],
			})
		except Exception as e:
			logger.error(f"Failed to get ZAP status: {e}")
			return jsonify({"error": str(e)}), 500

	@app.route("/api/zap/scan/<string:model>/<int:app_num>/stop", methods=["POST"])
	@error_handler
	def stop_zap_scan(model: str, app_num: int):
		"""
		Stop a running ZAP scan.
		"""
		try:
			# Find the scan based on the model and app number.
			scan_id = None
			for sid, scan in app.config.get("ZAP_SCANS", {}).items():
				if sid.startswith(f"{model}-{app_num}-"):
					scan_id = sid
					break
			if not scan_id:
				return jsonify({"error": "No running scan found"}), 404
			scan = app.config["ZAP_SCANS"][scan_id]
			scanner = scan["scanner"]
			# Stop the scan using the scanner's internal stop method.
			scanner._stop_zap_daemon()
			# Update the scan status.
			scan["status"] = "Stopped"
			scan["progress"] = 0
			return jsonify({"status": "stopped"})
		except Exception as e:
			logger.error(f"Failed to stop ZAP scan: {e}")
			return jsonify({"error": str(e)}), 500

	@app.route("/logs/<string:model>/<int:app_num>")
	@error_handler
	def view_logs(model: str, app_num: int):
		"""
		Render a page showing logs for both the backend and frontend containers.
		"""
		b_name, f_name = get_container_names(model, app_num)
		logs_data = {
			"backend": docker_manager.get_container_logs(b_name),
			"frontend": docker_manager.get_container_logs(f_name),
		}
		return render_template("logs.html", logs=logs_data, model=model, app_num=app_num)

	@app.route("/security/<string:model>/<int:app_num>")
	@error_handler
	def security_analysis(model: str, app_num: int):
		"""
		Run security analysis on the codebase and render the results.
		"""
		full_scan = request.args.get("full", "").lower() == "true"
		return process_security_analysis(
			template="security_analysis.html",
			analyzer=app.security_analyzer,
			analysis_method=app.security_analyzer.run_bandit_analysis,
			model=model,
			app_num=app_num,
			full_scan=full_scan,
			no_issue_message="No security issues found in the codebase.",
		)

	@app.route("/performance/<string:model>/<int:app_num>", methods=["GET", "POST"])
	def performance_test(model: str, app_num: int):
		"""
		Endpoint to run performance tests on a specific application.
		
		Supports GET requests (to display the test form) and POST requests (to run the test).
		"""
		tester = PerformanceTester(AppConfig.from_env().BASE_DIR)
		if request.method == "POST":
			data = request.get_json()
			num_users = int(data.get("num_users", 10))
			duration = int(data.get("duration", 30))
			spawn_rate = int(data.get("spawn_rate", 1))
			result, info = tester.run_test(
				model=model,
				app_num=app_num,
				num_users=num_users,
				duration=duration,
				spawn_rate=spawn_rate,
			)
			if result:
				return jsonify({
					"status": "success",
					"data": {
						"total_requests": result.total_requests,
						"avg_response_time": result.avg_response_time,
						"requests_per_sec": result.requests_per_sec,
						"duration": result.duration,
						"start_time": result.start_time,
						"end_time": result.end_time,
					},
				})
			else:
				return jsonify({
					"status": "error",
					"error": info.get("error", "Unknown error"),
				}), 500
		return render_template("performance_test.html", model=model, app_num=app_num)

	@app.route("/codacy/<string:model>/<int:app_num>")
	@error_handler
	def codacy_analysis(model: str, app_num: int):
		"""
		Run Codacy analysis on the application code and display the results.
		"""
		try:
			app_path = app.config["BASE_DIR"] / f"{model}/app{app_num}"
			issues, raw_output = app.codacy_analyzer.analyze_app(model, app_num)
			config_path = app_path / ".codacy.json"
			if config_path.exists():
				with open(config_path) as f:
					config = json.load(f)
			else:
				config = {
					"tools": {
						"python": True,
						"javascript": True,
						"typescript": True,
					},
					"exclude_paths": [
						"tests/**",
						"**/__pycache__/**",
						"node_modules/**",
					],
				}
			categories = sorted(set(issue.issue_type for issue in issues))
			summary = {
				"total_issues": len(issues),
				"severity_counts": {
					"HIGH": sum(1 for i in issues if i.severity == "HIGH"),
					"MEDIUM": sum(1 for i in issues if i.severity == "MEDIUM"),
					"LOW": sum(1 for i in issues if i.severity == "LOW"),
				},
				"scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
			}
			return render_template(
				"codacy_analysis.html",
				model=model,
				app_num=app_num,
				issues=issues,
				summary=summary,
				categories=categories,
				config=config,
				raw_output=raw_output,
				error=None,
			)
		except Exception as e:
			app.logger.error(f"Codacy analysis failed: {e}")
			return render_template(
				"codacy_analysis.html",
				model=model,
				app_num=app_num,
				issues=[],
				summary=None,
				categories=[],
				config={},
				raw_output="",
				error=str(e),
			)

	@app.route("/api/codacy/config", methods=["POST"])
	@error_handler
	def update_codacy_config():
		"""
		Update the Codacy configuration for a specified application.
		"""
		try:
			data = request.get_json()
			if not data:
				raise BadRequest("No JSON data provided")
			model = data.get("model")
			app_num = data.get("app_num")
			if not model or not app_num:
				raise BadRequest("Model and app number required")
			tools = data.get("tools", [])
			excludes = data.get("excludes", [])
			config = {
				"tools": {tool: {"enabled": True} for tool in tools},
				"exclude_paths": excludes,
			}
			app_path = app.config["BASE_DIR"] / f"{model}/app{app_num}"
			config_path = app_path / ".codacy.json"
			with open(config_path, "w") as f:
				json.dump(config, f, indent=2)
			flash("Codacy configuration updated successfully", "success")
			return jsonify({"status": "success"})
		except BadRequest as e:
			app.logger.warning(f"Bad request in Codacy config update: {e}")
			return jsonify({"error": str(e)}), 400
		except Exception as e:
			app.logger.error(f"Failed to update Codacy config: {e}")
			return jsonify({"error": str(e)}), 500

	@app.route("/api/codacy/<string:model>/<int:app_num>/status")
	@error_handler
	def codacy_status(model: str, app_num: int):
		"""
		Return the current Codacy analysis status for the application.
		"""
		try:
			app_path = app.config["BASE_DIR"] / f"{model}/app{app_num}"
			status_file = app_path / ".codacy_status"
			if status_file.exists():
				with open(status_file) as f:
					status = json.load(f)
			else:
				status = {
					"last_run": None,
					"status": "not_run",
					"issues_count": 0,
				}
			return jsonify(status)
		except Exception as e:
			app.logger.error(f"Failed to get Codacy status: {e}")
			return jsonify({"error": str(e)}), 500

	@app.route("/api/codacy/<string:model>/<int:app_num>/analyze", methods=["POST"])
	@error_handler
	def trigger_codacy_analysis(model: str, app_num: int):
		"""
		Trigger a new Codacy analysis asynchronously.
		"""
		try:
			app_path = app.config["BASE_DIR"] / f"{model}/app{app_num}"
			status_file = app_path / ".codacy_status"
			with open(status_file, "w") as f:
				json.dump(
					{
						"status": "running",
						"start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
					},
					f,
				)

			def run_analysis():
				try:
					issues, _ = app.codacy_analyzer.analyze_app(model, app_num)
					with open(status_file, "w") as f:
						json.dump(
							{
								"status": "completed",
								"last_run": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
								"issues_count": len(issues),
							},
							f,
						)
				except Exception as e:
					app.logger.error(f"Async Codacy analysis failed: {e}")
					with open(status_file, "w") as f:
						json.dump(
							{
								"status": "failed",
								"error": str(e),
								"last_run": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
							},
							f,
						)

			import threading
			thread = threading.Thread(target=run_analysis)
			thread.start()
			return jsonify({"status": "started", "message": "Analysis started successfully"})
		except Exception as e:
			app.logger.error(f"Failed to trigger Codacy analysis: {e}")
			return jsonify({"error": str(e)}), 500

	@app.route("/frontend-security/<string:model>/<int:app_num>")
	def frontend_security_analysis(model, app_num):
		"""
		Render a page displaying the results of a frontend security analysis.
		"""
		try:
			issues, tool_status, tool_output_details = app.frontend_security_analyzer.run_security_analysis(
				model, app_num, use_all_tools=True
			)
			summary = app.frontend_security_analyzer.get_analysis_summary(issues)
			return render_template(
				"frontend_security_analysis.html",
				model=model,
				app_num=app_num,
				full_scan=True,
				issues=issues,
				summary=summary,
				tool_status=tool_status,
				tool_output_details=tool_output_details,
				message="Security scan completed successfully.",
			)
		except Exception as e:
			logger.error(f"Error in frontend_security_analysis: {e}")
			return render_template("500.html", error=str(e)), 500

	@app.route("/api/status")
	@error_handler
	def system_status():
		"""
		API endpoint to return overall system health, including disk space and Docker health.
		"""
		disk_ok = SystemHealthMonitor.check_disk_space()
		docker_ok = SystemHealthMonitor.check_health(docker_manager.client)
		return jsonify({
			"status": "healthy" if (disk_ok and docker_ok) else "warning",
			"details": {"disk_space": disk_ok, "docker_health": docker_ok},
		})

	@app.route("/api/model-info")
	@error_handler
	def get_model_info():
		"""
		Return information about all defined AI models, including port ranges and app counts.
		"""
		return jsonify([
			{
				"name": model.name,
				"color": model.color,
				"ports": PortManager.get_port_range(idx),
				"total_apps": len(get_apps_for_model(model.name)),
			}
			for idx, model in enumerate(AI_MODELS)
		])

	@app.route("/<action>/<string:model>/<int:app_num>")
	@error_handler
	def handle_docker_action_route(action: str, model: str, app_num: int):
		"""
		A generic route to perform a Docker action (start, stop, etc.) on an app.
		"""
		success, message = handle_docker_action(action, model, app_num)
		if request.headers.get("X-Requested-With") == "XMLHttpRequest":
			status_code = 200 if success else 500
			return jsonify({
				"status": "success" if success else "error",
				"message": message,
			}), status_code
		flash(f"{'Success' if success else 'Error'}: {message}",
			  "success" if success else "error")
		return redirect(url_for("index"))

	@app.route("/api/health/<string:model>/<int:app_num>")
	@error_handler
	def check_container_health(model: str, app_num: int):
		"""
		Return the health status of the containers for a given app as JSON.
		"""
		healthy, message = verify_container_health(docker_manager, model, app_num)
		return jsonify({"healthy": healthy, "message": message})

	@app.route("/api/analyze-gpt4all/<string:analysis_type>", methods=["POST"])
	@error_handler
	def analyze_gpt4all(analysis_type: str):
		"""
		API endpoint for GPT4All analysis using a specified analysis type.
		"""
		try:
			data = request.get_json()
			directory = Path(data.get("directory", app.config["BASE_DIR"]))
			file_patterns = data.get("file_patterns", ["*.py", "*.js", "*.ts", "*.svelte"])
			analyzer = GPT4AllAnalyzer(directory)
			issues, summary = asyncio.run(analyzer.analyze_directory(
				directory=directory,
				file_patterns=file_patterns,
				analysis_type=analysis_type,
			))
			if not isinstance(summary, dict):
				summary = get_analysis_summary(issues)
			return jsonify({
				"issues": [asdict(issue) for issue in issues],
				"summary": summary,
			})
		except Exception as e:
			logger.error(f"GPT4All analysis failed: {e}")
			return jsonify({"error": str(e)}), 500

	@app.route("/gpt4all-analysis")
	@error_handler
	def gpt4all_analysis():
		"""
		Render a page displaying GPT4All analysis results.
		"""
		try:
			model = request.args.get("model")
			app_num = request.args.get("app_num")
			analysis_type = request.args.get("type", "security")
			if not model or not app_num:
				raise ValueError("Model and app number are required")
			directory = app.config["BASE_DIR"] / f"{model}/app{app_num}"
			if not directory.exists():
				raise ValueError(f"Directory not found: {directory}")
			analyzer = GPT4AllAnalyzer(directory)
			issues, summary = asyncio.run(analyzer.analyze_directory(
				directory=directory,
				analysis_type=analysis_type,
			))
			return render_template(
				"gpt4all_analysis.html",
				model=model,
				app_num=app_num,
				directory=str(directory),
				analysis_type=analysis_type,
				issues=issues,
				summary=summary,
				model_info={
					"name": "Phi-3 Mini Instruct",
					"ram_required": "4 GB",
					"parameters": "3 billion",
					"type": "phi",
				},
				error=None,
			)
		except Exception as e:
			logger.error(f"GPT4All analysis failed: {e}")
			return render_template(
				"gpt4all_analysis.html",
				model=model if "model" in locals() else None,
				app_num=app_num if "app_num" in locals() else None,
				directory=str(directory) if "directory" in locals() else "",
				analysis_type=analysis_type if "analysis_type" in locals() else "security",
				issues=[],
				summary={
					"total_issues": 0,
					"severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
					"files_affected": 0,
					"issue_types": {},
					"scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
				},
				model_info={
					"name": "Phi-3 Mini Instruct",
					"ram_required": "4 GB",
					"parameters": "3 billion",
					"type": "phi",
				},
				error=str(e),
			)


def register_error_handlers(app: Flask) -> None:
	"""
	Register custom error handlers for HTTP errors and exceptions.
	"""
	@app.errorhandler(404)
	def not_found(error):
		if request.headers.get("X-Requested-With") == "XMLHttpRequest":
			return jsonify({"error": "Not found"}), 404
		return render_template("404.html", error=error), 404

	@app.errorhandler(500)
	def server_error(error):
		logger.error(f"Server error: {error}")
		if request.headers.get("X-Requested-With") == "XMLHttpRequest":
			return jsonify({"error": "Internal server error"}), 500
		return render_template("500.html", error=error), 500

	@app.errorhandler(Exception)
	def handle_exception(error):
		logger.error(f"Unhandled exception: {error}")
		if request.headers.get("X-Requested-With") == "XMLHttpRequest":
			return jsonify({"error": str(error)}), 500
		return render_template("500.html", error=error), 500


def register_request_hooks(app: Flask, docker_manager: DockerManager) -> None:
	"""
	Register hooks to execute code before and after each request.
	For example, to occasionally clean up Docker containers and enforce security headers.
	"""
	@app.before_request
	def before():
		# Occasionally clean up containers and ZAP processes to free up resources.
		if random.random() < 0.01:
			docker_manager.cleanup_containers()
			if hasattr(app, "zap_scanner"):
				for scan_id, scan in app.config.get("ZAP_SCANS", {}).items():
					if scan["status"] not in ["Running", "Starting"]:
						scanner = scan.get("scanner")
						if scanner:
							scanner._stop_zap_daemon()

	@app.after_request
	def after(response):
		# Add security-related HTTP headers to the response.
		response.headers.update({
			"X-Content-Type-Options": "nosniff",
			"X-Frame-Options": "SAMEORIGIN",
			"X-XSS-Protection": "1; mode=block",
			"Strict-Transport-Security": "max-age=31536000; includeSubDomains",
		})
		return response

	@app.teardown_appcontext
	def teardown(exception=None):
		# Ensure any lingering ZAP processes are terminated when the app context is torn down.
		if hasattr(app, "zap_scanner"):
			for scan_id, scan in app.config.get("ZAP_SCANS", {}).items():
				scanner = scan.get("scanner")
				if scanner:
					scanner._stop_zap_daemon()


# -------------------------------------------------------------------
# Main Entry Point
# -------------------------------------------------------------------
if __name__ == "__main__":
	# Load configuration from environment variables.
	config = AppConfig.from_env()
	LoggingService.configure(config.LOG_LEVEL)
	try:
		# Create the Flask application instance.
		app = create_app(config)
		docker_manager = DockerManager()
		# Check system health and log warnings if necessary.
		if docker_manager.client and not SystemHealthMonitor.check_health(docker_manager.client):
			logger.warning("System health check failed - reduced functionality expected.")
		elif not docker_manager.client:
			logger.warning("Docker client unavailable - reduced functionality expected.")
		# Run the Flask application.
		app.run(
			host=config.HOST,
			port=config.PORT,
			debug=config.DEBUG,
		)
	except Exception as e:
		logger.critical(f"Failed to start: {e}")
		raise
