"""
Refactored Flask-based AI Model Management System

A Flask application that:
- Manages Docker-based frontend/backend apps
- Uses the Python Docker library for container operations
- Handles both synchronous and asynchronous workflows
"""

import asyncio
import logging
import os
import random
import subprocess
import time
from dataclasses import asdict, dataclass
from functools import wraps
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import docker
from docker.errors import NotFound
from flask import (
	Flask,
	flash,
	jsonify,
	redirect,
	render_template,
	request,
	url_for,
)
from werkzeug.middleware.proxy_fix import ProxyFix

from frontend_security_analysis import FrontendSecurityAnalyzer
from security_analysis import SecurityAnalyzer

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------


@dataclass
class AppConfig:
	DEBUG: bool = True
	SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "your-secret-key-here")
	BASE_DIR: Path = Path(__file__).parent
	LOG_LEVEL: str = os.getenv("LOG_LEVEL", "ERROR")
	DOCKER_TIMEOUT: int = int(os.getenv("DOCKER_TIMEOUT", "10"))
	CACHE_DURATION: int = int(os.getenv("CACHE_DURATION", "5"))
	HOST: str = "0.0.0.0" if os.getenv("FLASK_ENV") == "production" else "127.0.0.1"
	PORT: int = int(os.getenv("PORT", "5000"))

	@classmethod
	def from_env(cls) -> "AppConfig":
		return cls()


# -------------------------------------------------------------------
# Domain Models
# -------------------------------------------------------------------


@dataclass
class AIModel:
	name: str
	color: str


@dataclass
class DockerStatus:
	exists: bool = False
	running: bool = False
	health: str = "unknown"
	status: str = "unknown"
	details: str = ""

	def to_dict(self) -> Dict[str, Any]:
		return asdict(self)


# -------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------
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
	def filter(self, record: logging.LogRecord) -> bool:
		if not hasattr(record, "args") or len(record.args) < 3:
			return True
		msg = record.args[2] if isinstance(record.args[2], str) else ""
		return "GET /api/container/" not in msg or not msg.endswith(' HTTP/1.1" 200 -')


class LoggingService:
	@staticmethod
	def configure(log_level: str) -> None:
		logging.basicConfig(
			level=getattr(logging, log_level),
			format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
		)
		logging.getLogger("werkzeug").addFilter(StatusEndpointFilter())


# -------------------------------------------------------------------
# Port Management
# -------------------------------------------------------------------


class PortManager:
	BASE_BACKEND_PORT = 5001
	BASE_FRONTEND_PORT = 5501
	PORTS_PER_APP = 2
	BUFFER_PORTS = 20
	APPS_PER_MODEL = 20

	@classmethod
	def get_port_range(cls, model_idx: int) -> Dict[str, Dict[str, int]]:
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
		rng = cls.get_port_range(model_idx)
		return {
			"backend": rng["backend"]["start"] + (app_num - 1) * cls.PORTS_PER_APP,
			"frontend": rng["frontend"]["start"] + (app_num - 1) * cls.PORTS_PER_APP,
		}


# -------------------------------------------------------------------
# Docker Management
# -------------------------------------------------------------------


class DockerManager:
	def __init__(self, client: Optional[docker.DockerClient] = None) -> None:
		self.logger = logging.getLogger(__name__)
		self.client = client or self._create_docker_client()
		self._cache: Dict[str, Tuple[float, DockerStatus]] = {}
		self._cache_duration = AppConfig.from_env().CACHE_DURATION
		self._lock = asyncio.Lock()

	def _create_docker_client(self) -> Optional[docker.DockerClient]:
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
		now = time.time()
		if container_name in self._cache:
			timestamp, status = self._cache[container_name]
			if now - timestamp < self._cache_duration:
				return status

		status = self._fetch_container_status(container_name)
		self._cache[container_name] = (now, status)
		return status

	def _fetch_container_status(self, container_name: str) -> DockerStatus:
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
		if not self.client:
			return "Docker client unavailable"
		try:
			container = self.client.containers.get(container_name)
			return container.logs(tail=tail).decode("utf-8")
		except Exception as e:
			self.logger.error(f"Log retrieval failed for {container_name}: {e}")
			return f"Log retrieval error: {e}"

	def cleanup_containers(self) -> None:
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
	@staticmethod
	def check_disk_space() -> bool:
		try:
			if os.name == "nt":
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
	@wraps(f)
	def wrapped(*args, **kwargs):
		try:
			return f(*args, **kwargs)
		except Exception as e:
			logging.error(f"Error in {f.__name__}: {e}")
			if request.headers.get("X-Requested-With") == "XMLHttpRequest":
				return jsonify({"error": str(e)}), 500
			return render_template("500.html"), 500

	return wrapped


def get_model_index(model_name: str) -> int:
	return next((i for i, m in enumerate(AI_MODELS) if m.name == model_name), 0)


def get_container_names(model: str, app_num: int) -> Tuple[str, str]:
	idx = get_model_index(model)
	ports = PortManager.get_app_ports(idx, app_num)
	base = model.lower()
	return (
		f"{base}_backend_{ports['backend']}",
		f"{base}_frontend_{ports['frontend']}",
	)


def get_app_info(model_name: str, app_num: int) -> Dict[str, Any]:
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
	base_path = Path(f"{model_name}")
	if not base_path.exists():
		return []
	apps = []
	app_dirs = sorted(
		(d for d in base_path.iterdir() if d.is_dir() and d.name.startswith("app")),
		key=lambda x: int(x.name.replace("app", "")),
	)
	for app_dir in app_dirs:
		try:
			app_num = int(app_dir.name.replace("app", ""))
			apps.append(get_app_info(model_name, app_num))
		except ValueError as e:
			logging.error(f"Error processing {app_dir}: {e}")
	return apps


def get_all_apps() -> List[Dict[str, Any]]:
	return [app_info for model in AI_MODELS for app_info in get_apps_for_model(model.name)]


def run_docker_compose(
	command: List[str],
	model: str,
	app_num: int,
	timeout: int = 60,
	check: bool = True,
) -> Tuple[bool, str]:
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

	for base_cmd, extra_arg, timeout in commands[action]:
		cmd = [base_cmd] + ([extra_arg] if extra_arg else [])
		success, msg = run_docker_compose(cmd, model, app_num, timeout=timeout)
		if not success:
			logging.error(f"Docker {action} failed on {cmd}: {msg}")
			return False, msg
	return True, f"Successfully completed {action}"


def verify_container_health(
	docker_manager: DockerManager, model: str, app_num: int, max_retries: int = 10, retry_delay: int = 3
) -> Tuple[bool, str]:
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
    Unpacks (issues, tool_status, tool_output_details) from the analysis method.
    """
    try:
        # Unpack three values now:
        issues, tool_status, tool_output_details = analysis_method(model, app_num, use_all_tools=full_scan)
        if not issues:
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
        logging.warning(f"No files to analyze: {e}")
        return render_template(
            template,
            model=model,
            app_num=app_num,
            issues=None,
            error=str(e),
            full_scan=full_scan,
            tool_status={},
            tool_output_details={}
        )
    except Exception as e:
        logging.error(f"Security analysis failed: {e}")
        return render_template(
            template,
            model=model,
            app_num=app_num,
            issues=None,
            error=f"Security analysis failed: {str(e)}",
            full_scan=full_scan,
            tool_status={},
            tool_output_details={}
        )



# -------------------------------------------------------------------
# Flask App Factory & Route Registration
# -------------------------------------------------------------------


def create_app(config: Optional[AppConfig] = None) -> Flask:
	app = Flask(__name__)
	app.config.from_object(config or AppConfig.from_env())
	LoggingService.configure(app.config["LOG_LEVEL"])

	base_path = AppConfig.from_env().BASE_DIR.parent
	logging.info(f"Initializing SecurityAnalyzer with base path: {base_path}")
	app.security_analyzer = SecurityAnalyzer(base_path)
	app.frontend_security_analyzer = FrontendSecurityAnalyzer(base_path)

	docker_manager = DockerManager()
	app.wsgi_app = ProxyFix(app.wsgi_app)

	register_routes(app, docker_manager)
	register_error_handlers(app)
	register_request_hooks(app, docker_manager)
	return app


def register_routes(app: Flask, docker_manager: DockerManager) -> None:
	@app.route("/")
	@error_handler
	def index():
		apps = get_all_apps()
		for app_info in apps:
			b_name, f_name = get_container_names(app_info["model"], app_info["app_num"])
			app_info["backend_status"] = docker_manager.get_container_status(b_name)
			app_info["frontend_status"] = docker_manager.get_container_status(f_name)
		return render_template("index.html", apps=apps, models=AI_MODELS)

	@app.route("/status/<string:model>/<int:app_num>")
	@error_handler
	def check_app_status(model: str, app_num: int):
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
		b_name, f_name = get_container_names(model, app_num)
		status = {
			"backend": docker_manager.get_container_status(b_name).to_dict(),
			"frontend": docker_manager.get_container_status(f_name).to_dict(),
		}
		return jsonify(status)

	@app.route("/logs/<string:model>/<int:app_num>")
	@error_handler
	def view_logs(model: str, app_num: int):
		b_name, f_name = get_container_names(model, app_num)
		logs = {
			"backend": docker_manager.get_container_logs(b_name),
			"frontend": docker_manager.get_container_logs(f_name),
		}
		return render_template("logs.html", logs=logs, model=model, app_num=app_num)

	@app.route("/security/<string:model>/<int:app_num>")
	@error_handler
	def security_analysis(model: str, app_num: int):
		full_scan = request.args.get("full", "").lower() == "true"
		return process_security_analysis(
			template="security_analysis.html",
			analyzer=app.security_analyzer,
			analysis_method=app.security_analyzer.run_bandit_analysis,
			model=model,
			app_num=app_num,
			full_scan=full_scan,
			no_issue_message="No security issues found in the codebase."
		)



	@app.route("/frontend-security/<string:model>/<int:app_num>")
	def frontend_security_analysis(model, app_num):
		try:		
			issues, tool_status, tool_output_details = app.frontend_security_analyzer.run_security_analysis(model, app_num, use_all_tools=True)
			summary = app.frontend_security_analyzer.get_analysis_summary(issues)
			return render_template(
				"frontend_security_analysis.html",
				model=model,
				app_num=app_num,
				full_scan=True,  # or False as needed
				issues=issues,
				summary=summary,
				tool_status=tool_status,
				tool_output_details=tool_output_details,
				message="Security scan completed successfully."
			)

		except Exception as e:
			# Log error and render error template or flash message
			logger.error(f"Error in frontend_security_analysis: {e}")
			return render_template("500.html", error=str(e)), 500


	@app.route("/api/status")
	@error_handler
	def system_status():
		disk_ok = SystemHealthMonitor.check_disk_space()
		docker_ok = SystemHealthMonitor.check_health(docker_manager.client)
		return jsonify(
			{
				"status": "healthy" if (disk_ok and docker_ok) else "warning",
				"details": {"disk_space": disk_ok, "docker_health": docker_ok},
			}
		)

	@app.route("/api/model-info")
	@error_handler
	def get_model_info():
		return jsonify(
			[
				{
					"name": model.name,
					"color": model.color,
					"ports": PortManager.get_port_range(idx),
					"total_apps": len(get_apps_for_model(model.name)),
				}
				for idx, model in enumerate(AI_MODELS)
			]
		)

	@app.route("/<action>/<string:model>/<int:app_num>")
	@error_handler
	def handle_docker_action_route(action: str, model: str, app_num: int):
		success, message = handle_docker_action(action, model, app_num)
		if request.headers.get("X-Requested-With") == "XMLHttpRequest":
			status_code = 200 if success else 500
			return jsonify(
				{
					"status": "success" if success else "error",
					"message": message,
				}
			), status_code
		flash(f"{'Success' if success else 'Error'}: {message}", "success" if success else "error")
		return redirect(url_for("index"))

	@app.route("/api/health/<string:model>/<int:app_num>")
	@error_handler
	def check_container_health(model: str, app_num: int):
		healthy, message = verify_container_health(docker_manager, model, app_num)
		return jsonify({"healthy": healthy, "message": message})


def register_error_handlers(app: Flask) -> None:
	@app.errorhandler(404)
	def not_found(error):
		if request.headers.get("X-Requested-With") == "XMLHttpRequest":
			return jsonify({"error": "Not found"}), 404
		return render_template("404.html", error=error), 404

	@app.errorhandler(500)
	def server_error(error):
		logging.error(f"Server error: {error}")
		if request.headers.get("X-Requested-With") == "XMLHttpRequest":
			return jsonify({"error": "Internal server error"}), 500
		return render_template("500.html", error=error), 500

	@app.errorhandler(Exception)
	def handle_exception(error):
		logging.error(f"Unhandled exception: {error}")
		if request.headers.get("X-Requested-With") == "XMLHttpRequest":
			return jsonify({"error": str(error)}), 500
		return render_template("500.html", error=error), 500


def register_request_hooks(app: Flask, docker_manager: DockerManager) -> None:
	@app.before_request
	def before():
		# Occasionally clean up containers.
		if random.random() < 0.01:
			docker_manager.cleanup_containers()

	@app.after_request
	def after(response):
		response.headers.update(
			{
				"X-Content-Type-Options": "nosniff",
				"X-Frame-Options": "SAMEORIGIN",
				"X-XSS-Protection": "1; mode=block",
				"Strict-Transport-Security": "max-age=31536000; includeSubDomains",
			}
		)
		return response


# -------------------------------------------------------------------
# Main Entry Point
# -------------------------------------------------------------------
if __name__ == "__main__":
	config = AppConfig.from_env()
	LoggingService.configure(config.LOG_LEVEL)
	logger = logging.getLogger(__name__)

	try:
		app = create_app(config)
		docker_manager = DockerManager()
		if docker_manager.client and not SystemHealthMonitor.check_health(docker_manager.client):
			logger.warning("System health check failed - reduced functionality expected.")
		elif not docker_manager.client:
			logger.warning("Docker client unavailable - reduced functionality expected.")
		app.run(
			host=config.HOST,
			port=config.PORT,
			debug=config.DEBUG,
		)
	except Exception as e:
		logger.critical(f"Failed to start: {e}")
		raise
