import datetime
import enum
import json
import random
import threading # DATA_LOCK still needs threading.Lock
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from flask import (
    Blueprint,
    current_app, # Added for use in the custom filter
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

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
    tasks: List[AnalysisTask] = field(default_factory=list) # Holds task *objects* references

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "description": self.description,
            "analysis_types": [str(at) for at in self.analysis_types],
            "models": self.models, "app_ranges": self.app_ranges,
            "analysis_options": self.analysis_options, "status": str(self.status),
            "created_at": self.created_at.isoformat(),
            # "created_at_formatted" can be removed if datetimeformat filter is used in template
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_tasks": self.total_tasks, "completed_tasks": self.completed_tasks,
            "errors": self.errors,
        }

# --- In-memory Storage & Locks ---
BATCH_JOBS: Dict[str, BatchJob] = {}
ANALYSIS_TASKS: Dict[str, AnalysisTask] = {}
DATA_LOCK = threading.Lock() # For all shared data modifications

# --- Dummy Data ---
ALL_MODELS = ["Llama", "Mistral", "DeepSeek", "GPT4o", "Claude", "Gemini", "Grok", "R1", "O3"]
DEFAULT_JOB_NAME_TEMPLATE = "Batch Job - {date}"
DEFAULT_TASK_TIMEOUT = 1800

# --- Blueprint Definition (ensure this is before filter registration) ---
batch_analysis_bp = Blueprint(
    "batch_analysis", __name__, template_folder="templates", static_folder="static", url_prefix="/batch-analysis"
)

# --- Custom Jinja Filter ---
@batch_analysis_bp.app_template_filter('datetimeformat')
def format_datetime_filter(value, fmt="%Y-%m-%d %H:%M:%S"):
    """Formats a datetime object or an ISO format string into a more readable string."""
    if not value:
        return "N/A"

    dt_object = None
    if isinstance(value, str):
        try:
            # This is the logic from the user's provided solution block:
            # Handles cases with microseconds but no 'Z' (e.g., "2023-10-26T12:30:45.123456")
            # and cases with 'Z' or no microseconds.
            if '.' in value and 'Z' not in value:
                 # Python's fromisoformat before 3.11 might struggle with 'Z' and microseconds.
                 # This branch handles strings with microseconds but no 'Z'.
                 # It splits off microseconds; this might be too simple if timezone info followed microseconds.
                 # However, .isoformat() typically puts timezone at the very end or uses 'Z'.
                value_no_ms = value.split('.')[0]
                dt_object = datetime.datetime.fromisoformat(value_no_ms)
            else:
                # Handles strings with 'Z' (e.g., "2023-10-26T12:30:45Z" or "2023-10-26T12:30:45.123Z")
                # or strings without microseconds and no 'Z' (e.g., "2023-10-26T12:30:45+01:00")
                dt_object = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            # Fallback: Try parsing with common strptime formats if fromisoformat fails.
            # This is useful if the string isn't strictly ISO 8601 as expected by fromisoformat,
            # or if the .to_dict() methods sometimes produce a slightly different format.
            try:
                dt_object = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
            except ValueError:
                try:
                    dt_object = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    # Use current_app.logger if available and configured
                    if current_app:
                        current_app.logger.warning(f"Could not parse date string: {value} using fromisoformat or strptime fallbacks.")
                    else: # Fallback print if logger not available (e.g. during early init or tests)
                        print(f"Warning: Could not parse date string: {value}")
                    return value # Return original string if all parsing fails
    elif isinstance(value, datetime.datetime):
        # If it's already a datetime object, use it directly
        dt_object = value

    if dt_object:
        # Format the datetime object into the desired string representation
        return dt_object.strftime(fmt)

    # Fallback: if value is not a string or datetime, or if dt_object is None after logic
    return value


# --- Batch Analysis Service ---
class BatchJobService:
    def __init__(self):
        self.logger = current_app.logger.getChild('batch_service')

    def _generate_id(self): return str(uuid.uuid4())

    def _parse_app_range(self, range_str: str, max_apps: int = 3) -> List[int]: # Reduced max_apps for faster sync test
        if not range_str: return list(range(1, max_apps + 1))
        apps = set(); parts = range_str.split(',')
        for part in parts:
            part = part.strip()
            if not part: continue
            if '-' in part:
                try:
                    start, end = map(int, part.split('-'))
                    if start > end: start, end = end, start
                    apps.update(range(start, min(end, max_apps) + 1))
                except ValueError: self.logger.warning(f"Invalid range part: {part} in {range_str}")
            else:
                try:
                    app_num = int(part)
                    if 1 <= app_num <= max_apps: apps.add(app_num)
                except ValueError: self.logger.warning(f"Invalid app number: {part} in {range_str}")
        return sorted(list(apps))

    def create_job(self, data: Dict[str, Any]) -> BatchJob:
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

            job = BatchJob(id=job_id, name=job_name, description=data.get("description"),
                           analysis_types=analysis_types_enums, models=data.getlist("models"),
                           analysis_options={ # Simplified options
                               "task_timeout_override": data.get("task_timeout_override")})
            for model_name in job.models:
                app_range_str = data.get(f"app_range_{model_name}", ""); job.app_ranges[model_name] = app_range_str
                for app_num in self._parse_app_range(app_range_str):
                    for at_enum in job.analysis_types:
                        task_id = self._generate_id()
                        task = AnalysisTask(id=task_id, job_id=job_id, model=model_name, app_num=app_num, analysis_type=at_enum)
                        job.tasks.append(task); ANALYSIS_TASKS[task_id] = task
            job.total_tasks = len(job.tasks)
            job.status = JobStatus.QUEUED if job.total_tasks > 0 else JobStatus.COMPLETED
            BATCH_JOBS[job_id] = job
            self.logger.info(f"Created BatchJob '{job.name}' (ID: {job.id}) with {job.total_tasks} tasks. Status: {job.status}")

        if job.status == JobStatus.QUEUED:
            self.logger.info(f"Starting synchronous processing for Job ID: {job_id}")
            self._execute_job_synchronously(job_id) # Process synchronously
            self.logger.info(f"Synchronous processing finished for Job ID: {job_id}. Final Status: {job.status}")
        return job

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
            old_status = job.status
            job.status = status
            if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.ERROR] and not job.completed_at:
                job.completed_at = datetime.datetime.utcnow()
            if errors: job.errors.extend(errors)
            if old_status != status: 
                self.logger.info(f"Job {job_id} status updated from {old_status} to {status}")
        else:
            self.logger.warning(f"Attempt to update status for non-existent job {job_id}")


    def _update_task_status(self, task_id: str, status: TaskStatus, **kwargs):
        task = ANALYSIS_TASKS.get(task_id)
        if not task:
            self.logger.warning(f"Task {task_id} not found for status update.")
            return

        task.status = status
        if 'scan_start_time' in kwargs: task.scan_start_time = kwargs['scan_start_time']
        if 'scan_end_time' in kwargs: task.scan_end_time = kwargs['scan_end_time']
        if 'duration_seconds' in kwargs: task.duration_seconds = kwargs['duration_seconds']
        if 'details' in kwargs: task.details.update(kwargs['details'])
        
        if 'error' in kwargs and kwargs['error'] is not None:
            task.error = kwargs['error']
            if "error_info" not in task.details and isinstance(kwargs['error'], TaskError):
                 task.details["error_info"] = kwargs['error'].to_dict()
        elif status not in [TaskStatus.FAILED, TaskStatus.TIMED_OUT]:
            task.error = None; task.details.pop("error_info", None)

        for key in ['issues_count', 'high_severity', 'medium_severity', 'low_severity']:
            if key in kwargs: setattr(task, key, kwargs[key])
        
        self.logger.debug(f"Task {task_id} status updated to {status}. Details: {list(kwargs.keys())}")

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
            else:
                self.logger.warning(f"Job {task.job_id} for task {task.id} not found during task completion update.")
        # Removed else: self.logger.warning(f"Task {task_id} not found in ANALYSIS_TASKS during status update.") as it's redundant with the check at the beginning of the function.


    def _simulate_analysis(self, task: AnalysisTask):
        self.logger.info(f"SYNC Simulating {task.analysis_type} for {task.model}/app{task.app_num} (Task ID: {task.id})")
        start_time = datetime.datetime.utcnow()
        self._update_task_status(task.id, TaskStatus.RUNNING, scan_start_time=start_time)

        simulated_duration = random.randint(1, 2) 
        time.sleep(simulated_duration)
        end_time = datetime.datetime.utcnow()
        duration = int((end_time - start_time).total_seconds())
        outcome = random.choices([TaskStatus.COMPLETED, TaskStatus.FAILED], weights=[0.9, 0.1])[0]
        details = {"raw_output_preview": f"SYNC: Simulated output for {task.analysis_type} on {task.model}/app{task.app_num}...", "message": "SYNC Simulation complete."}
        error_obj, issues_count, high, med, low = None, 0, 0, 0, 0

        if outcome == TaskStatus.FAILED:
            error_obj = TaskError(category="SyncSimError", message="Task failed (sync sim).", traceback="Sync traceback.")
            details["error_info"] = error_obj.to_dict()
        elif outcome == TaskStatus.COMPLETED: 
            if task.analysis_type in [AnalysisType.FRONTEND_SECURITY, AnalysisType.BACKEND_SECURITY, AnalysisType.ZAP]:
                issues_count = random.randint(0, 5); high = random.randint(0, issues_count // 2 if issues_count else 0)
                med = random.randint(0, (issues_count - high) // 2 if (issues_count - high) > 0 else 0); low = issues_count - high - med
                details["summary"] = {"total_issues": issues_count, "high": high, "medium": med, "low": low}
                if high > 0: details["issues"] = [{"severity": "HIGH", "issue_type": "SimVuln", "issue_text": "Critical sim vuln."}]
        self._update_task_status(task.id, outcome, scan_end_time=end_time, duration_seconds=duration,
                                 details=details, error=error_obj, issues_count=issues_count,
                                 high_severity=high, medium_severity=med, low_severity=low)
        self.logger.info(f"SYNC Finished {task.analysis_type} for {task.model}/app{task.app_num}. Status: {outcome}, Duration: {duration}s")

    def _execute_job_synchronously(self, job_id: str):
        job = self.get_job(job_id) 
        if not job:
            self.logger.error(f"SYNC: Job {job_id} not found for synchronous execution.")
            return
        
        self.logger.info(f"SYNC: Starting execution for Job {job_id} ({job.name}). Status: {job.status}")
        if job.status != JobStatus.QUEUED:
            self.logger.warning(f"SYNC: Job {job_id} is not QUEUED (is {job.status}). Cannot execute.")
            return

        with DATA_LOCK: 
            self._update_job_status(job.id, JobStatus.INITIALIZING)
            job.started_at = datetime.datetime.utcnow()
            self.logger.info(f"SYNC: Job {job_id} Initializing. Total tasks: {job.total_tasks}")
        
        time.sleep(0.1) 

        with DATA_LOCK:
            self._update_job_status(job.id, JobStatus.RUNNING)
            self.logger.info(f"SYNC: Job {job_id} Running.")

            if not job.tasks:
                self.logger.warning(f"SYNC: Job {job_id} has no tasks.")
            else:
                for task_obj_snapshot in list(job.tasks): 
                    task_id_to_process = task_obj_snapshot.id
                    current_task_version = ANALYSIS_TASKS.get(task_id_to_process) 

                    if not current_task_version:
                        self.logger.warning(f"SYNC: Task {task_id_to_process} not found in global registry for job {job_id}. Skipping.")
                        job.completed_tasks +=1 
                        continue
                    
                    if current_task_version.status == TaskStatus.PENDING:
                        current_job_state = BATCH_JOBS.get(job_id) 
                        if current_job_state and current_job_state.status == JobStatus.CANCELLING:
                            self.logger.info(f"SYNC: Job {job_id} CANCELLING. Cancelling task {current_task_version.id}.")
                            self._update_task_status(current_task_version.id, TaskStatus.CANCELLED, details={"skip_reason": "Job was cancelled."})
                            continue
                        self._simulate_analysis(current_task_version)
                    else:
                        self.logger.info(f"SYNC: Skipping task {current_task_version.id} as status is {current_task_version.status}")
            
            if job.completed_tasks >= job.total_tasks and job.status == JobStatus.RUNNING:
                job_failed = any(ANALYSIS_TASKS[t.id].status in [TaskStatus.FAILED, TaskStatus.TIMED_OUT] for t in job.tasks if t.id in ANALYSIS_TASKS) or bool(job.errors)
                job_was_cancelled = any(ANALYSIS_TASKS[t.id].status == TaskStatus.CANCELLED for t in job.tasks if t.id in ANALYSIS_TASKS)
                final_status = JobStatus.COMPLETED
                if job.status == JobStatus.CANCELLING or job_was_cancelled : final_status = JobStatus.CANCELLED
                elif job_failed: final_status = JobStatus.FAILED
                self._update_job_status(job.id, final_status)
                self.logger.info(f"SYNC: Job {job_id} explicitly finalized to {final_status} after loop.")

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
            # Check if all tasks are now in a terminal state (not PENDING or RUNNING)
            # This logic might need adjustment if tasks can be retried or have other non-terminal states.
            if all( (ANALYSIS_TASKS.get(t.id) is None or # Task might have been deleted (unlikely in this flow)
                     ANALYSIS_TASKS[t.id].status not in [TaskStatus.PENDING, TaskStatus.RUNNING])
                    for t in job.tasks):
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
        for job in self.get_all_jobs(): stats["total"] += 1; stats[job.status.value] += 1
        return stats

    def get_status_data_for_job_view(self, job: BatchJob) -> Dict[str, Any]: 
        if not job: return {"progress": {"total": 0, "completed": 0, "percent": 0, "by_status": {}}, "active_tasks_count": 0, "results_summary": {}}
        with DATA_LOCK: tasks_for_job = [ANALYSIS_TASKS[t.id] for t in job.tasks if t.id in ANALYSIS_TASKS]
        progress = {"total": job.total_tasks, "completed": job.completed_tasks,
                    "percent": int((job.completed_tasks / job.total_tasks * 100) if job.total_tasks > 0 else (100 if job.status == JobStatus.COMPLETED else 0)),
                    "by_status": {s.value: 0 for s in TaskStatus}}
        active_tasks_count = 0
        results_summary = {
            "high_total": 0, "medium_total": 0, "low_total": 0, "total_issues": 0,
            "frontend_security_tasks_processed": 0, "backend_security_tasks_processed": 0,
            "performance_avg_rps": "N/A", "performance_avg_rt": "N/A", "performance_total_failures": 0, "performance_tasks_processed": 0,
            "gpt4all_reqs_checked_total": 0, "gpt4all_reqs_met_total": 0, "gpt4all_tasks_processed": 0,
            "zap_issues_total": 0, "zap_tasks_completed": 0, "zap_tasks_processed": 0,
            "code_quality_lint_errors_total": 0, "code_quality_avg_complexity": "N/A", "code_quality_avg_duplication_percentage": "N/A", "code_quality_tasks_processed": 0,
        }
        perf_rps, perf_rt, cq_comp, cq_dupl = [], [], [], []

        for task in tasks_for_job:
            progress["by_status"][task.status.value] += 1
            if task.status == TaskStatus.RUNNING: active_tasks_count += 1
            if task.status == TaskStatus.COMPLETED:
                if task.analysis_type in [AnalysisType.FRONTEND_SECURITY, AnalysisType.BACKEND_SECURITY, AnalysisType.ZAP]:
                    results_summary["high_total"] += task.high_severity; results_summary["medium_total"] += task.medium_severity
                    results_summary["low_total"] += task.low_severity; results_summary["total_issues"] += task.issues_count
                    if task.analysis_type == AnalysisType.FRONTEND_SECURITY: results_summary["frontend_security_tasks_processed"] += 1
                    if task.analysis_type == AnalysisType.BACKEND_SECURITY: results_summary["backend_security_tasks_processed"] += 1
                    if task.analysis_type == AnalysisType.ZAP:
                        results_summary["zap_tasks_completed"] +=1; results_summary["zap_issues_total"] += task.issues_count
                        results_summary["zap_tasks_processed"] +=1
                elif task.analysis_type == AnalysisType.PERFORMANCE:
                    results_summary["performance_tasks_processed"] += 1
                    perf_rps.append(task.details.get("requests_per_sec", 0)); perf_rt.append(task.details.get("avg_response_time", 0))
                    results_summary["performance_total_failures"] += task.details.get("total_failures", 0)
                elif task.analysis_type == AnalysisType.GPT4ALL:
                    results_summary["gpt4all_tasks_processed"] += 1
                    results_summary["gpt4all_reqs_checked_total"] += task.details.get("summary", {}).get("requirements_checked", 0)
                    results_summary["gpt4all_reqs_met_total"] += task.details.get("summary", {}).get("met_count", 0)
                elif task.analysis_type == AnalysisType.CODE_QUALITY:
                    results_summary["code_quality_tasks_processed"] += 1
                    results_summary["code_quality_lint_errors_total"] += task.details.get("summary", {}).get("lint_errors", 0)
                    comp = task.details.get("summary", {}).get("complexity_score", "N/A")
                    if comp not in ["N/A", None] and isinstance(comp, (int,float)): cq_comp.append(float(comp))
                    dupl = task.details.get("summary", {}).get("duplication_percentage", "N/A")
                    if dupl not in ["N/A", None] and isinstance(dupl, (int,float)): cq_dupl.append(float(dupl))
        if perf_rps: results_summary["performance_avg_rps"] = round(sum(perf_rps) / len(perf_rps), 1)
        if perf_rt: results_summary["performance_avg_rt"] = round(sum(perf_rt) / len(perf_rt), 0)
        if cq_comp: results_summary["code_quality_avg_complexity"] = round(sum(cq_comp) / len(cq_comp), 1)
        if cq_dupl: results_summary["code_quality_avg_duplication_percentage"] = round(sum(cq_dupl) / len(cq_dupl), 1)
        return {"progress": progress, "active_tasks_count": active_tasks_count,
                "results_summary": results_summary, "job_status_val": job.status.value}

# --- Routes ---
def _get_batch_service() -> BatchJobService:
    if "batch_service" not in current_app.extensions:
        current_app.extensions["batch_service"] = BatchJobService()
    return current_app.extensions["batch_service"]

@batch_analysis_bp.route("/")
def batch_dashboard():
    service = _get_batch_service()
    jobs = [job.to_dict() for job in service.get_all_jobs()]
    stats = service.get_job_stats()
    default_job_name = DEFAULT_JOB_NAME_TEMPLATE.format(date=datetime.datetime.now().strftime("%Y-%m-%d"))
    submitted_data_json = request.args.get('submitted_data')
    submitted_data = json.loads(submitted_data_json) if submitted_data_json else None
    return render_template("batch_dashboard.html", jobs=jobs, stats=stats, all_models=ALL_MODELS,
                           default_job_name=default_job_name, batch_service={"default_task_timeout": DEFAULT_TASK_TIMEOUT},
                           AnalysisType=AnalysisType, JobStatus=JobStatus, submitted_data=submitted_data)

@batch_analysis_bp.route("/job", methods=["POST"])
def create_batch_job():
    service = _get_batch_service()
    form_data = request.form; errors = []
    if not form_data.get("name"): errors.append("Job name is required.")
    if not form_data.getlist("analysis_types") and not form_data.get("scan_type"): errors.append("At least one analysis type must be selected.")
    if not form_data.getlist("models"): errors.append("At least one model must be selected.")
    if errors:
        for error in errors: flash(error, "error")
        return redirect(url_for("batch_analysis.batch_dashboard", submitted_data=json.dumps(dict(form_data))))
    try:
        job = service.create_job(form_data) 
        flash(f"Batch job '{job.name}' processed synchronously. Final status: {job.status}.", "success" if job.status == JobStatus.COMPLETED else "warning")
        return redirect(url_for("batch_analysis.view_job", job_id=job.id))
    except Exception as e:
        current_app.logger.error(f"Error creating/processing batch job: {e}", exc_info=True)
        flash(f"Error creating/processing batch job: {str(e)}", "error")
        return redirect(url_for("batch_analysis.batch_dashboard", submitted_data=json.dumps(dict(form_data))))

@batch_analysis_bp.route("/job/<job_id>")
def view_job(job_id: str):
    service = _get_batch_service(); job = service.get_job(job_id)
    if not job:
        flash(f"Job with ID {job_id} not found.", "error"); return redirect(url_for("batch_analysis.batch_dashboard"))
    tasks = service.get_job_tasks(job_id)
    status_data = service.get_status_data_for_job_view(job)
    return render_template("view_job.html", job=job.to_dict(), results=[task.to_dict() for task in tasks],
                           status_data=status_data, AnalysisType=AnalysisType, JobStatus=JobStatus, TaskStatus=TaskStatus)

@batch_analysis_bp.route("/result/<result_id>")
def view_result(result_id: str):
    service = _get_batch_service(); task = service.get_task(result_id)
    if not task:
        flash(f"Result {result_id} not found.", "error"); return redirect(url_for("batch_analysis.batch_dashboard"))
    job = service.get_job(task.job_id)
    if not job:
        flash(f"Job {task.job_id} for result {result_id} not found.", "error"); return redirect(url_for("batch_analysis.batch_dashboard"))
    full_details_json_str = json.dumps(task.details, indent=2, sort_keys=True, default=str)
    return render_template("view_result.html", result=task.to_dict(), job=job.to_dict(),
                           AnalysisType=AnalysisType, TaskStatus=TaskStatus, full_details_json=full_details_json_str)

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
    tasks = service.get_job_tasks(job_id)
    return jsonify({"results": [task.to_dict() for task in tasks]})

@batch_analysis_bp.route("/job/<job_id>/cancel", methods=["POST"])
def cancel_job_api(job_id: str): 
    service = _get_batch_service(); success = service.cancel_job(job_id)
    if success: return jsonify({"success": True, "message": "Job cancellation initiated."})
    job = service.get_job(job_id); status_val = job.status.value if job and job.status else "Not Found"
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
    job = service.get_job(job_id); status_val = job.status.value if job and job.status else "Not Found"
    return jsonify({"success": False, "error": f"Failed to archive (status: {status_val})."}), 400

def init_batch_analysis(app):
    app.register_blueprint(batch_analysis_bp)
    # Ensure the service is initialized if not already present
    if "batch_service" not in app.extensions:
        # Create the service instance, it will use current_app.logger when methods are called
        app.extensions["batch_service"] = BatchJobService()
    app.logger.info("Batch Analysis module (SYNC MODE) initialized, blueprint registered, and custom filter added.")

