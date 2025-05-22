import datetime
import enum
import json
import logging # Import for BatchJobService fallback logger
import random
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path # Import Path
from typing import Any, Dict, List, Optional, Tuple

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

# Assuming these might be needed for interpreting results from analyzers
# If not, they can be removed. Using string literals for severity keys for now.
# from backend_security_analysis import Severity as BackendSeverity
# from frontend_security_analysis import Severity as FrontendSeverity

from utils import get_app_info # For ZAP and Performance target URLs

# --- Enums ---
class AnalysisType(str, enum.Enum):
    FRONTEND_SECURITY = "frontend_security"
    BACKEND_SECURITY = "backend_security"
    PERFORMANCE = "performance"
    GPT4ALL = "gpt4all"
    ZAP = "zap"
    CODE_QUALITY = "code_quality"
    def __str__(self): return self.value

class JobStatus(str, enum.Enum):
    PENDING = "PENDING"; QUEUED = "QUEUED"; INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"; COMPLETED = "COMPLETED"; FAILED = "FAILED"
    ERROR = "ERROR"; CANCELLED = "CANCELLED"; CANCELLING = "CANCELLING"
    ARCHIVED = "ARCHIVED"
    def __str__(self): return self.value

class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"; RUNNING = "RUNNING"; COMPLETED = "COMPLETED"
    FAILED = "FAILED"; TIMED_OUT = "TIMED_OUT"; CANCELLED = "CANCELLED"
    SKIPPED = "SKIPPED"
    def __str__(self): return self.value

# --- Data Models ---
@dataclass
class TaskError:
    category: str; message: str; traceback: Optional[str] = None
    def to_dict(self): return asdict(self)

@dataclass
class AnalysisTask:
    id: str; job_id: str; model: str; app_num: int; analysis_type: AnalysisType
    status: TaskStatus = TaskStatus.PENDING
    scan_start_time: Optional[datetime.datetime] = None
    scan_end_time: Optional[datetime.datetime] = None
    duration_seconds: Optional[int] = None
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[TaskError] = None
    issues_count: int = 0; high_severity: int = 0
    medium_severity: int = 0; low_severity: int = 0
    task_id: Optional[str] = None
    def __post_init__(self):
        if self.task_id is None: self.task_id = self.id
    def to_dict(self):
        data = asdict(self)
        for key in ["analysis_type", "status"]: data[key] = str(getattr(self, key))
        for dt_key in ["scan_start_time", "scan_end_time"]:
            if getattr(self, dt_key): data[dt_key] = getattr(self, dt_key).isoformat()
        if self.error: data["error"] = self.error.to_dict()
        return data

@dataclass
class BatchJob:
    id: str; name: str; description: Optional[str] = None
    analysis_types: List[AnalysisType] = field(default_factory=list)
    models: List[str] = field(default_factory=list)
    app_ranges: Dict[str, str] = field(default_factory=dict)
    analysis_options: Dict[str, Any] = field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    created_at: datetime.datetime = field(default_factory=datetime.datetime.utcnow)
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None
    total_tasks: int = 0; completed_tasks: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    tasks: List[AnalysisTask] = field(default_factory=list)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "description": self.description,
            "analysis_types": [str(at) for at in self.analysis_types],
            "models": self.models, "app_ranges": self.app_ranges,
            "analysis_options": self.analysis_options, "status": str(self.status),
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_tasks": self.total_tasks, "completed_tasks": self.completed_tasks,
            "errors": self.errors,
        }

# --- In-memory Storage & Locks ---
BATCH_JOBS: Dict[str, BatchJob] = {}
ANALYSIS_TASKS: Dict[str, AnalysisTask] = {}
DATA_LOCK = threading.Lock()

# --- Constants ---
ALL_MODELS = ["Llama", "Mistral", "DeepSeek", "GPT4o", "Claude", "Gemini", "Grok", "R1", "O3"]
DEFAULT_JOB_NAME_TEMPLATE = "Batch Job - {date}"
DEFAULT_TASK_TIMEOUT = 1800

batch_analysis_bp = Blueprint(
    "batch_analysis", __name__, template_folder="templates", static_folder="static", url_prefix="/batch-analysis"
)

@batch_analysis_bp.app_template_filter('datetimeformat')
def format_datetime_filter(value, fmt="%Y-%m-%d %H:%M:%S"):
    if not value: return "N/A"
    dt_object = None
    if isinstance(value, str):
        try:
            if '.' in value and 'Z' not in value: value_no_ms = value.split('.')[0]; dt_object = datetime.datetime.fromisoformat(value_no_ms)
            else: dt_object = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            try: dt_object = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
            except ValueError:
                try: dt_object = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    if current_app: current_app.logger.warning(f"Could not parse date string: {value}")
                    else: print(f"Warning: Could not parse date string: {value}")
                    return value
    elif isinstance(value, datetime.datetime): dt_object = value
    if dt_object: return dt_object.strftime(fmt)
    return value

class BatchJobService:
    def __init__(self, app_instance=None):
        if app_instance:
            self._app = app_instance
            self.logger = self._app.logger.getChild('batch_service')
        else:
            try:
                self.logger = current_app.logger.getChild('batch_service')
            except RuntimeError:
                self.logger = logging.getLogger('batch_service_fallback')
                self.logger.warning("BatchJobService initialized without Flask app context. Using fallback logger.")
                if not self.logger.hasHandlers(): # Add a basic handler if none configured
                    handler = logging.StreamHandler()
                    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                    handler.setFormatter(formatter)
                    self.logger.addHandler(handler)
                    self.logger.setLevel(logging.INFO)


    def _generate_id(self): return str(uuid.uuid4())

    def _parse_app_range(self, range_str: str, max_apps: int = 30) -> List[int]:
        if not range_str: return list(range(1, max_apps + 1))
        apps = set(); parts = range_str.split(',')
        for part in parts:
            part = part.strip()
            if not part: continue
            if '-' in part:
                try:
                    start, end = map(int, part.split('-'))
                    if start > end: start, end = end, start # Auto-correct order
                    apps.update(range(start, min(end, max_apps) + 1))
                except ValueError: self.logger.warning(f"Invalid range part: {part} in {range_str}")
            else:
                try:
                    app_num = int(part)
                    if 1 <= app_num <= max_apps: apps.add(app_num)
                except ValueError: self.logger.warning(f"Invalid app number: {part} in {range_str}")
        return sorted(list(apps))

    def create_job(self, data: Dict[str, Any]) -> BatchJob:
        # ... (Implementation from previous response - parsing form data, creating Job and Tasks) ...
        with DATA_LOCK:
            job_id = self._generate_id()
            job_name = data.get("name", DEFAULT_JOB_NAME_TEMPLATE.format(date=datetime.datetime.now().strftime("%Y-%m-%d")))
            raw_analysis_types = data.getlist("analysis_types"); scan_type_radio = data.get("scan_type")
            final_analysis_types_str = set(raw_analysis_types)
            if scan_type_radio == "frontend": final_analysis_types_str.add(AnalysisType.FRONTEND_SECURITY.value)
            elif scan_type_radio == "backend": final_analysis_types_str.add(AnalysisType.BACKEND_SECURITY.value)
            elif scan_type_radio == "both":
                final_analysis_types_str.add(AnalysisType.FRONTEND_SECURITY.value)
                final_analysis_types_str.add(AnalysisType.BACKEND_SECURITY.value)
            analysis_types_enums = [AnalysisType(val) for val in final_analysis_types_str if val]

            analysis_options = {}
            for key, value in data.items(): # data is request.form (MultiDict)
                if key.startswith("analysis_opt_"):
                    parts = key.replace("analysis_opt_", "").split("_", 1)
                    tool_name_key = parts[0]
                    option_name_key = parts[1] if len(parts) > 1 else "general_option_" + parts[0]

                    if tool_name_key not in analysis_options: analysis_options[tool_name_key] = {}
                    
                    # Handle multiple values for the same option key (e.g., from multiple checkboxes for 'endpoints')
                    actual_values = data.getlist(key)
                    processed_value = None
                    if len(actual_values) > 1:
                        processed_value = actual_values # Keep as list
                    elif len(actual_values) == 1:
                        single_value = actual_values[0]
                        try: processed_value = int(single_value)
                        except ValueError:
                            if single_value.lower() == 'true': processed_value = True
                            elif single_value.lower() == 'false': processed_value = False
                            else: processed_value = single_value # Keep as string
                    
                    if processed_value is not None:
                         analysis_options[tool_name_key][option_name_key] = processed_value

            job = BatchJob(id=job_id, name=job_name, description=data.get("description"),
                           analysis_types=analysis_types_enums, models=data.getlist("models"),
                           analysis_options=analysis_options)
            
            apps_per_model_config = current_app.config.get("APPS_PER_MODEL", 30) if current_app else 30

            for model_name in job.models:
                app_range_str = data.get(f"app_range_{model_name}", ""); job.app_ranges[model_name] = app_range_str
                for app_num in self._parse_app_range(app_range_str, max_apps=apps_per_model_config):
                    for at_enum in job.analysis_types:
                        task_id = self._generate_id()
                        task = AnalysisTask(id=task_id, job_id=job_id, model=model_name, app_num=app_num, analysis_type=at_enum)
                        job.tasks.append(task); ANALYSIS_TASKS[task_id] = task
            job.total_tasks = len(job.tasks)
            job.status = JobStatus.QUEUED if job.total_tasks > 0 else JobStatus.COMPLETED
            BATCH_JOBS[job_id] = job
            self.logger.info(f"Created BatchJob '{job.name}' (ID: {job.id}) with {job.total_tasks} tasks. Status: {job.status}. Options: {job.analysis_options}")

        if job.status == JobStatus.QUEUED:
            self.logger.info(f"Starting synchronous processing for Job ID: {job.id}")
            self._execute_job_synchronously(job_id)
            self.logger.info(f"Synchronous processing finished for Job ID: {job.id}. Final Status: {job.status}")
        return job

    # ... (get_job, get_all_jobs, get_job_tasks, get_task, _update_job_status, _update_task_status remain as previously defined)
    def get_job(self, job_id: str) -> Optional[BatchJob]:
        with DATA_LOCK: return BATCH_JOBS.get(job_id)
    def get_all_jobs(self) -> List[BatchJob]:
        with DATA_LOCK: return sorted(BATCH_JOBS.values(), key=lambda j: j.created_at, reverse=True)
    def get_job_tasks(self, job_id: str) -> List[AnalysisTask]:
        job = self.get_job(job_id)
        if job:
            with DATA_LOCK: return [ANALYSIS_TASKS[task.id] for task in job.tasks if task.id in ANALYSIS_TASKS]
        return []
    def get_task(self, task_id: str) -> Optional[AnalysisTask]:
        with DATA_LOCK: return ANALYSIS_TASKS.get(task_id)

    def _update_job_status(self, job_id: str, status: JobStatus, errors: Optional[List[Dict]] = None):
        job = BATCH_JOBS.get(job_id)
        if job:
            old_status = job.status; job.status = status
            if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.ERROR] and not job.completed_at:
                job.completed_at = datetime.datetime.utcnow()
            if errors: job.errors.extend(errors)
            if old_status != status: self.logger.info(f"Job {job_id} status updated from {old_status} to {status}")
        else: self.logger.warning(f"Attempt to update status for non-existent job {job_id}")

    def _update_task_status(self, task_id: str, status: TaskStatus, **kwargs):
        task = ANALYSIS_TASKS.get(task_id)
        if not task: self.logger.warning(f"Task {task_id} not found for status update."); return
        task.status = status
        for key, value in kwargs.items():
            if hasattr(task, key): setattr(task, key, value)
            elif key in ['issues_count', 'high_severity', 'medium_severity', 'low_severity']: setattr(task, key, value)
            elif key == 'details': task.details.update(value)
        if 'error' in kwargs and kwargs['error'] is not None: task.error = kwargs['error']
        elif status not in [TaskStatus.FAILED, TaskStatus.TIMED_OUT]: task.error = None; task.details.pop("error_info", None)
        self.logger.debug(f"Task {task_id} status updated to {status}.")
        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.TIMED_OUT, TaskStatus.CANCELLED, TaskStatus.SKIPPED]:
            job = BATCH_JOBS.get(task.job_id)
            if job:
                job.completed_tasks += 1
                self.logger.debug(f"Task {task.id} (Job {job.id}) finished. Job progress: {job.completed_tasks}/{job.total_tasks}")
                if job.completed_tasks >= job.total_tasks and job.status == JobStatus.RUNNING:
                    job_failed = any(ANALYSIS_TASKS[t.id].status in [TaskStatus.FAILED, TaskStatus.TIMED_OUT] for t in job.tasks if t.id in ANALYSIS_TASKS) or bool(job.errors)
                    job_was_cancelled = any(ANALYSIS_TASKS[t.id].status == TaskStatus.CANCELLED for t in job.tasks if t.id in ANALYSIS_TASKS)
                    final_status = JobStatus.COMPLETED
                    if job.status == JobStatus.CANCELLING or job_was_cancelled: final_status = JobStatus.CANCELLED
                    elif job_failed: final_status = JobStatus.FAILED
                    self._update_job_status(job.id, final_status)
                    self.logger.info(f"Job {job.id} fully processed. Final status: {final_status}")
            else: self.logger.warning(f"Job {task.job_id} for task {task.id} not found during task completion update.")


    def _execute_actual_analysis(self, task: AnalysisTask, job_options: Dict[str, Any]):
        self.logger.info(f"Executing actual analysis for {task.analysis_type} on {task.model}/app{task.app_num} (Task ID: {task.id})")
        start_time = datetime.datetime.utcnow()
        self._update_task_status(task.id, TaskStatus.RUNNING, scan_start_time=start_time)

        final_task_status = TaskStatus.FAILED # Default
        task_status_update_kwargs: Dict[str, Any] = {"details": {}} # Ensure details is always a dict
        error_obj: Optional[TaskError] = None
        
        project_root_dir = Path(current_app.config.get("PROJECT_ROOT_DIR", "."))


        try:
            if task.analysis_type == AnalysisType.BACKEND_SECURITY:
                analyzer = getattr(current_app, 'backend_security_analyzer', None)
                if analyzer:
                    opts = job_options.get(AnalysisType.BACKEND_SECURITY.value, {}) # e.g. job_options['backend_security']
                    use_all_tools = opts.get("use_all_tools", True)
                    issues, tool_status, _ = analyzer.run_security_analysis(task.model, task.app_num, use_all_tools=use_all_tools, force_rerun=opts.get("force_rerun", False))
                    summary = analyzer.get_analysis_summary(issues)
                    task_status_update_kwargs["details"]["summary"] = summary; task_status_update_kwargs["details"]["tool_status"] = tool_status
                    task_status_update_kwargs["issues_count"] = summary.get("total_issues", 0)
                    task_status_update_kwargs["high_severity"] = summary.get("severity_counts", {}).get("HIGH", 0)
                    task_status_update_kwargs["medium_severity"] = summary.get("severity_counts", {}).get("MEDIUM", 0)
                    task_status_update_kwargs["low_severity"] = summary.get("severity_counts", {}).get("LOW", 0)
                    final_task_status = TaskStatus.COMPLETED
                    if any(ts.startswith("❌") for ts in tool_status.values()) and not issues:
                        final_task_status = TaskStatus.FAILED; error_obj = TaskError(category="BackendSecurityToolFailure", message="One or more tools failed.")
                else: error_obj = TaskError(category="ConfigError", message="BackendSecurityAnalyzer not available."); final_task_status = TaskStatus.SKIPPED

            elif task.analysis_type == AnalysisType.FRONTEND_SECURITY:
                analyzer = getattr(current_app, 'frontend_security_analyzer', None)
                if analyzer:
                    opts = job_options.get(AnalysisType.FRONTEND_SECURITY.value, {})
                    use_all_tools = opts.get("use_all_tools", True)
                    issues, tool_status, _ = analyzer.run_security_analysis(task.model, task.app_num, use_all_tools=use_all_tools, force_rerun=opts.get("force_rerun", False))
                    summary = analyzer.get_analysis_summary(issues)
                    task_status_update_kwargs["details"]["summary"] = summary; task_status_update_kwargs["details"]["tool_status"] = tool_status
                    task_status_update_kwargs["issues_count"] = summary.get("total_issues", 0)
                    task_status_update_kwargs["high_severity"] = summary.get("severity_counts", {}).get("HIGH", 0)
                    task_status_update_kwargs["medium_severity"] = summary.get("severity_counts", {}).get("MEDIUM", 0)
                    task_status_update_kwargs["low_severity"] = summary.get("severity_counts", {}).get("LOW", 0)
                    final_task_status = TaskStatus.COMPLETED
                    if any(ts.startswith("❌") for ts in tool_status.values()) and not issues:
                        final_task_status = TaskStatus.FAILED; error_obj = TaskError(category="FrontendSecurityToolFailure", message="One or more tools failed.")
                else: error_obj = TaskError(category="ConfigError", message="FrontendSecurityAnalyzer not available."); final_task_status = TaskStatus.SKIPPED

            elif task.analysis_type == AnalysisType.PERFORMANCE:
                tester = getattr(current_app, 'performance_tester', None)
                app_info = get_app_info(task.model, task.app_num)
                if tester and app_info and app_info.get('frontend_url'):
                    host_url = app_info['frontend_url']
                    opts = job_options.get(AnalysisType.PERFORMANCE.value, {})
                    user_count = int(opts.get("user_count", 10))
                    spawn_rate = int(opts.get("spawn_rate", 1))
                    run_time_s = int(opts.get("run_time_seconds", 30))
                    endpoints_cfg = opts.get("endpoints", [{"path": "/", "method": "GET", "weight": 1}])
                    
                    perf_result = tester.run_test_library(
                        test_name=f"batch_{task.model}_{task.app_num}_{int(time.time())}",
                        host=host_url, endpoints=endpoints_cfg, user_count=user_count,
                        spawn_rate=spawn_rate, run_time=run_time_s, model=task.model, app_num=task.app_num,
                        force_rerun=opts.get("force_rerun", False)
                    )
                    if perf_result:
                        task_status_update_kwargs["details"] = perf_result.to_dict()
                        task_status_update_kwargs["issues_count"] = perf_result.total_failures
                        final_task_status = TaskStatus.COMPLETED
                    else: error_obj = TaskError(category="PerformanceError", message="Test run failed/returned no result.")
                else: error_obj = TaskError(category="ConfigError", message="PerformanceTester/AppInfo not available."); final_task_status = TaskStatus.SKIPPED

            elif task.analysis_type == AnalysisType.ZAP:
                zap_scanner = getattr(current_app, 'zap_scanner', None)
                if zap_scanner:
                    opts = job_options.get(AnalysisType.ZAP.value, {})
                    quick_scan_opt = opts.get("quick_scan", False)
                    
                    actual_app_src_path = project_root_dir / "models" / task.model / f"app{task.app_num}"
                    if actual_app_src_path.exists():
                        zap_scanner.set_source_code_root(str(actual_app_src_path))
                        self.logger.info(f"Set ZAP source code root for task {task.id} to: {actual_app_src_path}")
                    else:
                        self.logger.warning(f"ZAP source code path for task {task.id} not found: {actual_app_src_path}. Code context may be limited.")

                    scan_success = zap_scanner.start_scan(task.model, task.app_num, quick_scan=quick_scan_opt) # Assumes start_scan is blocking
                    
                    if scan_success:
                        zap_results_data = zap_scanner.load_scan_results(task.model, task.app_num)
                        if zap_results_data and "summary" in zap_results_data:
                            summary = zap_results_data["summary"]
                            task_status_update_kwargs["issues_count"] = summary.get("total_alerts", 0)
                            risk_counts = summary.get("risk_counts", {})
                            task_status_update_kwargs["high_severity"] = risk_counts.get("High", 0)
                            task_status_update_kwargs["medium_severity"] = risk_counts.get("Medium", 0)
                            task_status_update_kwargs["low_severity"] = risk_counts.get("Low", 0)
                            task_status_update_kwargs["details"]["summary"] = summary
                            task_status_update_kwargs["details"]["alerts_preview"] = zap_results_data.get("alerts", [])[:5]
                            final_task_status = TaskStatus.COMPLETED
                        else: error_obj = TaskError(category="ZapResultError", message="Scan completed but results unreadable.")
                    else: error_obj = TaskError(category="ZapScanError", message="ZAP scan execution failed.")
                else: error_obj = TaskError(category="ConfigError", message="ZAPScanner not available."); final_task_status = TaskStatus.SKIPPED

            elif task.analysis_type == AnalysisType.GPT4ALL:
                analyzer = getattr(current_app, 'gpt4all_analyzer', None)
                if analyzer:
                    opts = job_options.get(AnalysisType.GPT4ALL.value, {})
                    custom_reqs = opts.get("requirements")
                    req_list_to_check, _ = analyzer.get_requirements_for_app(task.app_num)
                    if custom_reqs and isinstance(custom_reqs, list): req_list_to_check = custom_reqs

                    if not req_list_to_check:
                        final_task_status = TaskStatus.SKIPPED; task_status_update_kwargs["details"]["message"] = "No requirements for GPT4All."
                    else:
                        check_results = analyzer.check_requirements(task.model, task.app_num, req_list_to_check, force_rerun=opts.get("force_rerun", False))
                        met_count = sum(1 for cr in check_results if cr.result.met)
                        total_reqs = len(check_results)
                        task_status_update_kwargs["details"]["summary"] = {"requirements_checked": total_reqs, "met_count": met_count}
                        task_status_update_kwargs["details"]["results_preview"] = [cr.to_dict() for cr in check_results[:5]]
                        task_status_update_kwargs["issues_count"] = total_reqs - met_count
                        task_status_update_kwargs["medium_severity"] = total_reqs - met_count
                        final_task_status = TaskStatus.COMPLETED
                else: error_obj = TaskError(category="ConfigError", message="GPT4AllAnalyzer not available."); final_task_status = TaskStatus.SKIPPED
            
            elif task.analysis_type == AnalysisType.CODE_QUALITY:
                analyzer = getattr(current_app, 'code_quality_analyzer', None)
                if analyzer: # Actual call to CodeQualityAnalyzer
                    opts = job_options.get(AnalysisType.CODE_QUALITY.value, {})
                    # Example: cq_results = analyzer.analyze(task.model, task.app_num, options=opts)
                    # For now, using the placeholder simulation logic:
                    self.logger.info(f"Simulating Code Quality for {task.model}/app{task.app_num} (Task ID: {task.id}) as actual analyzer call is TBD.")
                    time.sleep(random.randint(1,2)); sim_lint_errors = random.randint(0,20); sim_complexity = random.uniform(5.0,15.0); sim_duplication = random.uniform(0.0,10.0)
                    task_status_update_kwargs["details"]["summary"] = {"lint_errors": sim_lint_errors, "average_complexity": round(sim_complexity,1), "duplication_percentage": round(sim_duplication,1), "message":"Placeholder: Simulated code quality."}
                    task_status_update_kwargs["issues_count"] = sim_lint_errors
                    if sim_lint_errors > 10: task_status_update_kwargs["high_severity"] = 1
                    elif sim_lint_errors > 5: task_status_update_kwargs["medium_severity"] = 1
                    elif sim_lint_errors > 0 : task_status_update_kwargs["low_severity"] = 1
                    final_task_status = TaskStatus.COMPLETED
                else: error_obj = TaskError(category="ConfigError", message="CodeQualityAnalyzer not available."); final_task_status = TaskStatus.SKIPPED
            else:
                self.logger.warning(f"Unknown analysis type: {task.analysis_type} for task {task.id}")
                error_obj = TaskError(category="TypeError", message=f"Unknown analysis type: {task.analysis_type}")
                final_task_status = TaskStatus.SKIPPED

        except FileNotFoundError as fnf_error: # Catch specific path errors from analyzers
            self.logger.exception(f"FileNotFoundError during actual analysis for task {task.id} ({task.analysis_type}): {fnf_error}")
            error_obj = TaskError(category="FileNotFoundError", message=str(fnf_error), traceback=str(fnf_error.__traceback__))
            final_task_status = TaskStatus.FAILED
        except Exception as e:
            self.logger.exception(f"Error during actual analysis for task {task.id} ({task.analysis_type}): {e}")
            error_obj = TaskError(category="AnalysisExecutionError", message=str(e), traceback=str(e.__traceback__))
            final_task_status = TaskStatus.FAILED
        
        if error_obj:
            task_status_update_kwargs["error"] = error_obj
            if "details" not in task_status_update_kwargs: task_status_update_kwargs["details"] = {} # Ensure details dict exists
            task_status_update_kwargs["details"]["error_info"] = error_obj.to_dict()

        end_time = datetime.datetime.utcnow()
        duration = int((end_time - start_time).total_seconds())
        task_status_update_kwargs["scan_end_time"] = end_time
        task_status_update_kwargs["duration_seconds"] = duration
        
        self._update_task_status(task.id, final_task_status, **task_status_update_kwargs)
        self.logger.info(f"Finished {task.analysis_type} for {task.model}/app{task.app_num}. Status: {final_task_status}, Duration: {duration}s")

    def _execute_job_synchronously(self, job_id: str):
        # ... (Implementation from previous response - calls _execute_actual_analysis) ...
        job = self.get_job(job_id) 
        if not job: self.logger.error(f"SYNC: Job {job_id} not found for execution."); return
        self.logger.info(f"SYNC: Starting execution for Job {job_id} ({job.name}). Status: {job.status}")
        if job.status != JobStatus.QUEUED: self.logger.warning(f"SYNC: Job {job_id} not QUEUED (is {job.status}). Cannot execute."); return

        with DATA_LOCK: 
            self._update_job_status(job.id, JobStatus.INITIALIZING); job.started_at = datetime.datetime.utcnow()
            self.logger.info(f"SYNC: Job {job_id} Initializing. Total tasks: {job.total_tasks}")
        time.sleep(0.1) 
        with DATA_LOCK:
            self._update_job_status(job.id, JobStatus.RUNNING); self.logger.info(f"SYNC: Job {job.id} Running.")
            if not job.tasks: self.logger.warning(f"SYNC: Job {job_id} has no tasks.")
            else:
                for task_obj_snapshot in list(job.tasks): 
                    task_id_to_process = task_obj_snapshot.id
                    current_task_version = ANALYSIS_TASKS.get(task_id_to_process) 
                    if not current_task_version:
                        self.logger.warning(f"SYNC: Task {task_id_to_process} not found. Skipping."); job.completed_tasks +=1; continue
                    if current_task_version.status == TaskStatus.PENDING:
                        current_job_state = BATCH_JOBS.get(job_id) 
                        if current_job_state and current_job_state.status == JobStatus.CANCELLING:
                            self.logger.info(f"SYNC: Job {job_id} CANCELLING. Cancelling task {current_task_version.id}.")
                            self._update_task_status(current_task_version.id, TaskStatus.CANCELLED, details={"skip_reason": "Job was cancelled."})
                        else: self._execute_actual_analysis(current_task_version, job.analysis_options) # Pass job options
                    else: self.logger.info(f"SYNC: Skipping task {current_task_version.id} as status is {current_task_version.status}")
            if job.completed_tasks >= job.total_tasks and job.status == JobStatus.RUNNING:
                job_failed = any(ANALYSIS_TASKS[t.id].status in [TaskStatus.FAILED, TaskStatus.TIMED_OUT] for t in job.tasks if t.id in ANALYSIS_TASKS) or bool(job.errors)
                job_was_cancelled = any(ANALYSIS_TASKS[t.id].status == TaskStatus.CANCELLED for t in job.tasks if t.id in ANALYSIS_TASKS)
                final_status = JobStatus.COMPLETED
                if job.status == JobStatus.CANCELLING or job_was_cancelled : final_status = JobStatus.CANCELLED
                elif job_failed: final_status = JobStatus.FAILED
                self._update_job_status(job.id, final_status)
                self.logger.info(f"SYNC: Job {job_id} explicitly finalized to {final_status} after loop.")

    # ... (cancel_job, delete_job, archive_job, get_job_stats, get_status_data_for_job_view - keep as previously defined)
    def cancel_job(self, job_id: str) -> bool:
        with DATA_LOCK:
            job = self.get_job(job_id)
            if not job: return False
            if job.status not in [JobStatus.PENDING, JobStatus.QUEUED, JobStatus.INITIALIZING, JobStatus.RUNNING]: return False
            self._update_job_status(job_id, JobStatus.CANCELLING)
            tasks_cancelled_count = 0
            for task_obj_snapshot in list(job.tasks):
                task = ANALYSIS_TASKS.get(task_obj_snapshot.id)
                if task and task.status == TaskStatus.PENDING:
                    self._update_task_status(task.id, TaskStatus.CANCELLED, details={"skip_reason": "Job was cancelled."})
                    tasks_cancelled_count +=1
            self.logger.info(f"Job {job_id} CANCELLING: {tasks_cancelled_count} pending tasks marked CANCELLED.")
            if all( (ANALYSIS_TASKS.get(t.id) is None or ANALYSIS_TASKS[t.id].status not in [TaskStatus.PENDING, TaskStatus.RUNNING]) for t in job.tasks):
                self._update_job_status(job_id, JobStatus.CANCELLED)
            return True

    def delete_job(self, job_id: str) -> bool: 
        with DATA_LOCK:
            job = BATCH_JOBS.pop(job_id, None)
            if job:
                for task_id in [task.id for task in job.tasks]: ANALYSIS_TASKS.pop(task_id, None)
                self.logger.info(f"Deleted Job {job_id} and its tasks.")
                return True
            return False

    def archive_job(self, job_id: str) -> bool: 
        with DATA_LOCK:
            job = self.get_job(job_id)
            if not job: return False
            if job.status not in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.ERROR]: return False
            self._update_job_status(job_id, JobStatus.ARCHIVED)
            return True
    
    def get_job_stats(self) -> Dict[str, Any]: 
        stats: Dict[str, Any] = {s.value: 0 for s in JobStatus}; stats["total"] = 0
        for job_obj in self.get_all_jobs(): stats["total"] += 1; stats[job_obj.status.value] += 1
        return stats

    def get_status_data_for_job_view(self, job: BatchJob) -> Dict[str, Any]:
        # (Implementation from previous response, ensuring it uses ANALYSIS_TASKS correctly and handles detailed summaries)
        if not job: return {"progress": {"total": 0, "completed": 0, "percent": 0, "by_status": {}}, "active_tasks_count": 0, "results_summary": {}}
        with DATA_LOCK: tasks_for_job_snap = [ANALYSIS_TASKS[t.id] for t in job.tasks if t.id in ANALYSIS_TASKS]
        progress = {"total": job.total_tasks, "completed": job.completed_tasks,
                    "percent": int((job.completed_tasks / job.total_tasks * 100) if job.total_tasks > 0 else (100 if job.status == JobStatus.COMPLETED else 0)),
                    "by_status": {s.value: 0 for s in TaskStatus}}
        active_tasks_count = 0
        results_summary = {"high_total": 0, "medium_total": 0, "low_total": 0, "total_issues": 0}
        # Initialize detailed summary fields for each analysis type dynamically based on AnalysisType enum
        for at_enum in AnalysisType:
            results_summary[at_enum.value] = {"tasks_processed": 0} # Basic init
            if at_enum in [AnalysisType.FRONTEND_SECURITY, AnalysisType.BACKEND_SECURITY]:
                results_summary[at_enum.value]["issues_by_severity"] = {"HIGH":0, "MEDIUM":0, "LOW":0}
            elif at_enum == AnalysisType.PERFORMANCE:
                results_summary[at_enum.value].update({"avg_rps": "N/A", "avg_rt": "N/A", "total_failures": 0})
            elif at_enum == AnalysisType.GPT4ALL:
                 results_summary[at_enum.value].update({"reqs_checked": 0, "reqs_met": 0})
            elif at_enum == AnalysisType.ZAP:
                results_summary[at_enum.value].update({"total_alerts": 0, "alerts_by_risk": {"High":0, "Medium":0, "Low":0, "Informational":0}}) # ZAP uses "Informational"
            elif at_enum == AnalysisType.CODE_QUALITY:
                results_summary[at_enum.value].update({"lint_errors": 0, "avg_complexity": "N/A", "avg_duplication": "N/A"})
        
        perf_rps_list, perf_rt_list, cq_comp_list, cq_dupl_list = [], [], [], []

        for task in tasks_for_job_snap:
            progress["by_status"][task.status.value] += 1
            if task.status == TaskStatus.RUNNING: active_tasks_count += 1
            if task.status == TaskStatus.COMPLETED:
                results_summary["total_issues"] += task.issues_count
                results_summary["high_total"] += task.high_severity
                results_summary["medium_total"] += task.medium_severity
                results_summary["low_total"] += task.low_severity
                tool_key = task.analysis_type.value
                results_summary[tool_key]["tasks_processed"] += 1
                task_details_summary = task.details.get("summary", {})

                if task.analysis_type in [AnalysisType.FRONTEND_SECURITY, AnalysisType.BACKEND_SECURITY]:
                    results_summary[tool_key]["issues_by_severity"]["HIGH"] += task_details_summary.get("severity_counts", {}).get("HIGH",0)
                    results_summary[tool_key]["issues_by_severity"]["MEDIUM"] += task_details_summary.get("severity_counts", {}).get("MEDIUM",0)
                    results_summary[tool_key]["issues_by_severity"]["LOW"] += task_details_summary.get("severity_counts", {}).get("LOW",0)
                elif task.analysis_type == AnalysisType.PERFORMANCE: # task.details IS the perf_result dict
                    perf_rps_list.append(task.details.get("requests_per_sec", 0))
                    perf_rt_list.append(task.details.get("avg_response_time", 0))
                    results_summary[tool_key]["total_failures"] += task.details.get("total_failures", 0)
                elif task.analysis_type == AnalysisType.ZAP and task_details_summary:
                    results_summary[tool_key]["total_alerts"] += task_details_summary.get("total_alerts",0)
                    for risk, count in task_details_summary.get("risk_counts", {}).items():
                         results_summary[tool_key]["alerts_by_risk"][risk] = results_summary[tool_key]["alerts_by_risk"].get(risk,0) + count
                elif task.analysis_type == AnalysisType.GPT4ALL and task_details_summary:
                    results_summary[tool_key]["reqs_checked"] += task_details_summary.get("requirements_checked", 0)
                    results_summary[tool_key]["reqs_met"] += task_details_summary.get("met_count", 0)
                elif task.analysis_type == AnalysisType.CODE_QUALITY and task_details_summary:
                    results_summary[tool_key]["lint_errors"] += task_details_summary.get("lint_errors", 0)
                    if isinstance(task_details_summary.get("average_complexity"), (int, float)): cq_comp_list.append(float(task_details_summary["average_complexity"]))
                    if isinstance(task_details_summary.get("duplication_percentage"), (int, float)): cq_dupl_list.append(float(task_details_summary["duplication_percentage"]))
        
        if perf_rps_list: results_summary[AnalysisType.PERFORMANCE.value]["avg_rps"] = round(sum(perf_rps_list) / len(perf_rps_list), 1)
        if perf_rt_list: results_summary[AnalysisType.PERFORMANCE.value]["avg_rt"] = round(sum(perf_rt_list) / len(perf_rt_list), 0)
        if cq_comp_list: results_summary[AnalysisType.CODE_QUALITY.value]["avg_complexity"] = round(sum(cq_comp_list) / len(cq_comp_list), 1)
        if cq_dupl_list: results_summary[AnalysisType.CODE_QUALITY.value]["avg_duplication"] = round(sum(cq_dupl_list) / len(cq_dupl_list), 1)
        
        return {"progress": progress, "active_tasks_count": active_tasks_count, "results_summary": results_summary, "job_status_val": job.status.value}


# --- Routes ---
def _get_batch_service() -> BatchJobService:
    if "batch_service" not in current_app.extensions:
        current_app.extensions["batch_service"] = BatchJobService(app_instance=current_app._get_current_object())
    return current_app.extensions["batch_service"]

# ... (batch_dashboard, create_batch_job, view_job, view_result, and API routes remain as previously defined,
#      ensuring they use the updated BatchJobService correctly) ...
@batch_analysis_bp.route("/")
def batch_dashboard():
    service = _get_batch_service()
    jobs_list = service.get_all_jobs()
    jobs_dict = [job.to_dict() for job in jobs_list] 
    job_view_data = {job.id: service.get_status_data_for_job_view(job) for job in jobs_list}
    stats = service.get_job_stats()
    default_job_name = DEFAULT_JOB_NAME_TEMPLATE.format(date=datetime.datetime.now().strftime("%Y-%m-%d"))
    submitted_data_json = request.args.get('submitted_data')
    submitted_data = json.loads(submitted_data_json) if submitted_data_json else None
    return render_template("batch_dashboard.html", jobs=jobs_dict, stats=stats, all_models=ALL_MODELS,
                           default_job_name=default_job_name, batch_service={"default_task_timeout": DEFAULT_TASK_TIMEOUT},
                           AnalysisType=AnalysisType, JobStatus=JobStatus, submitted_data=submitted_data,
                           job_view_data=job_view_data)

@batch_analysis_bp.route("/job", methods=["POST"])
def create_batch_job():
    service = _get_batch_service()
    form_data = request.form 
    errors = []
    if not form_data.get("name"): errors.append("Job name is required.")
    if not form_data.getlist("analysis_types") and not form_data.get("scan_type"): errors.append("At least one analysis type or default scan type must be selected.")
    if not form_data.getlist("models"): errors.append("At least one model must be selected.")
    if errors:
        for error in errors: flash(error, "error")
        return redirect(url_for("batch_analysis.batch_dashboard", submitted_data=json.dumps(dict(form_data))))
    try:
        job = service.create_job(form_data) 
        flash_map = {JobStatus.COMPLETED: "success", JobStatus.FAILED: "error", JobStatus.CANCELLED: "warning"}
        flash(f"Batch job '{job.name}' processed. Status: {job.status}.", flash_map.get(job.status, "info"))
        return redirect(url_for("batch_analysis.view_job", job_id=job.id))
    except Exception as e:
        current_app.logger.error(f"Error creating batch job: {e}", exc_info=True)
        flash(f"Error creating batch job: {str(e)}", "error")
        return redirect(url_for("batch_analysis.batch_dashboard", submitted_data=json.dumps(dict(form_data))))

@batch_analysis_bp.route("/job/<job_id>")
def view_job(job_id: str):
    service = _get_batch_service(); job = service.get_job(job_id)
    if not job: flash(f"Job {job_id} not found.", "error"); return redirect(url_for("batch_analysis.batch_dashboard"))
    tasks_current = [ANALYSIS_TASKS.get(t.id, t) for t in job.tasks] # Get current state from global
    status_data = service.get_status_data_for_job_view(job)
    return render_template("view_job.html", job=job.to_dict(), results=[task.to_dict() for task in tasks_current],
                           status_data=status_data, AnalysisType=AnalysisType, JobStatus=JobStatus, TaskStatus=TaskStatus)

@batch_analysis_bp.route("/result/<result_id>")
def view_result(result_id: str):
    service = _get_batch_service(); task = service.get_task(result_id)
    if not task: flash(f"Result {result_id} not found.", "error"); return redirect(url_for("batch_analysis.batch_dashboard"))
    job = service.get_job(task.job_id)
    if not job: flash(f"Job {task.job_id} for result {result_id} not found.", "error"); return redirect(url_for("batch_analysis.batch_dashboard"))
    details_json = json.dumps(task.details, indent=2, sort_keys=True, default=str)
    return render_template("view_result.html", result=task.to_dict(), job=job.to_dict(),
                           AnalysisType=AnalysisType, TaskStatus=TaskStatus, full_details_json=details_json)

@batch_analysis_bp.route("/job/<job_id>/status", methods=["GET"])
def get_job_status_api(job_id: str): 
    service = _get_batch_service(); job = service.get_job(job_id)
    if not job: return jsonify({"error": "Job not found"}), 404
    status_data = service.get_status_data_for_job_view(job)
    return jsonify({"job": job.to_dict(), **status_data})

@batch_analysis_bp.route("/job/<job_id>/results", methods=["GET"])
def get_job_tasks_api(job_id: str): 
    service = _get_batch_service(); job = service.get_job(job_id)
    if not job: return jsonify({"error": "Job not found"}), 404
    tasks = [ANALYSIS_TASKS.get(t.id, t) for t in job.tasks] # Get current state from global
    return jsonify({"results": [task.to_dict() for task in tasks]})

@batch_analysis_bp.route("/job/<job_id>/cancel", methods=["POST"])
def cancel_job_api(job_id: str): 
    service = _get_batch_service(); success = service.cancel_job(job_id)
    if success: 
        job_status = service.get_job(job_id).status.value if service.get_job(job_id) else "UNKNOWN"
        return jsonify({"success": True, "message": "Job cancellation initiated.", "job_status": job_status })
    job = service.get_job(job_id); status_val = job.status.value if job else "Not Found"
    return jsonify({"success": False, "error": f"Failed to cancel job (status: {status_val})."}), 400

@batch_analysis_bp.route("/job/<job_id>/delete", methods=["POST"])
def delete_job_api(job_id: str): 
    service = _get_batch_service(); success = service.delete_job(job_id)
    if success: return jsonify({"success": True, "message": "Job deleted."})
    return jsonify({"success": False, "error": "Failed to delete job."}), 404

@batch_analysis_bp.route("/job/<job_id>/archive", methods=["POST"])
def archive_job_api(job_id: str): 
    service = _get_batch_service(); success = service.archive_job(job_id)
    if success: return jsonify({"success": True, "message": "Job archived."})
    job = service.get_job(job_id); status_val = job.status.value if job else "Not Found"
    return jsonify({"success": False, "error": f"Failed to archive (status: {status_val})."}), 400


def init_batch_analysis(app): # app is the Flask app instance
    # app.register_blueprint(batch_analysis_bp) # <--- REMOVE THIS LINE

    # Ensure the service is initialized if not already present
    if "batch_service" not in app.extensions:
        # Pass the Flask app instance to the BatchJobService constructor
        app.extensions["batch_service"] = BatchJobService(app_instance=app)
    
    required_analyzers = [
        'backend_security_analyzer', 'frontend_security_analyzer',
        'performance_tester', 'gpt4all_analyzer', 'zap_scanner', 
        'code_quality_analyzer'
    ]
    for analyzer_name in required_analyzers:
        if not hasattr(app, analyzer_name) or getattr(app, analyzer_name) is None:
            # Use app.logger here as it's available
            app.logger.warning(
                f"Batch Analysis Init: Analyzer '{analyzer_name}' not found or not initialized on Flask app. "
                f"Tasks requiring it may default to SKIPPED or FAILED."
            )
    app.logger.info("Batch Analysis module (SYNC MODE - Actual Analyzers) initialized.")