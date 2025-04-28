"""
Batch Security Analysis Module

Provides functionality for running batch security analysis on both frontend
and backend code across multiple applications or models, including job
management and reporting.
"""

import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set, Union

import flask
from flask import (
    Blueprint, current_app, jsonify, render_template, request, url_for,
    redirect, flash
)

from logging_service import create_logger_for_component

# Module-specific logger
logger = create_logger_for_component('batch_analysis')

# Flask Blueprint for batch analysis routes
batch_analysis_bp = Blueprint(
    "batch_analysis",
    __name__,
    template_folder="templates"
)

# =============================================================================
# Data Models & Enums
# =============================================================================

class JobStatus(str, Enum):
    """Enumeration for batch analysis job statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class ScanType(str, Enum):
    """Enumeration for the type of scan performed in a batch job."""
    FRONTEND = "frontend"
    BACKEND = "backend"
    BOTH = "both"


@dataclass
class BatchAnalysisJob:
    """Represents a batch analysis job configuration and status."""
    id: int
    name: str
    description: str
    created_at: datetime
    status: JobStatus = JobStatus.PENDING
    models: List[str] = field(default_factory=list)
    app_ranges: Dict[str, List[int]] = field(default_factory=dict) # Maps model name to list of app numbers
    scan_options: Dict[str, Any] = field(default_factory=dict) # e.g., {"full_scan": True}
    scan_type: ScanType = ScanType.FRONTEND
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_tasks: int = 0 # Total number of individual app scans
    completed_tasks: int = 0
    results: Dict[str, Any] = field(default_factory=dict) # Could store aggregated results if needed
    errors: List[str] = field(default_factory=list) # Stores errors encountered during job execution

    def to_dict(self) -> Dict[str, Any]:
        """Converts the job object to a dictionary suitable for JSON serialization."""
        result_dict = asdict(self)
        # Convert datetime objects to ISO format strings
        for key in ['created_at', 'started_at', 'completed_at']:
            if isinstance(result_dict[key], datetime):
                result_dict[key] = result_dict[key].isoformat()
        # Convert enums to their string values
        result_dict['status'] = self.status.value
        result_dict['scan_type'] = self.scan_type.value
        return result_dict


@dataclass
class BatchAnalysisResult:
    """Represents the result of a single analysis task within a batch job."""
    id: int
    job_id: int
    model: str
    app_num: int
    status: str # e.g., "completed", "failed"
    scan_type: ScanType
    issues_count: int = 0
    high_severity: int = 0
    medium_severity: int = 0
    low_severity: int = 0
    scan_time: Optional[datetime] = None
    details: Dict[str, Any] = field(default_factory=dict) # Stores raw issues, summary, tool status

    def to_dict(self) -> Dict[str, Any]:
        """Converts the result object to a dictionary suitable for JSON serialization."""
        result_dict = asdict(self)
        if isinstance(result_dict['scan_time'], datetime):
            result_dict['scan_time'] = result_dict['scan_time'].isoformat()
        result_dict['scan_type'] = self.scan_type.value
        return result_dict

# =============================================================================
# In-Memory Job Storage
# =============================================================================

class JobStorage:
    """Simple in-memory storage for batch analysis jobs and their results."""
    def __init__(self):
        self.jobs: Dict[int, BatchAnalysisJob] = {}
        self.results: Dict[int, List[BatchAnalysisResult]] = {} # Maps job_id to list of results
        self.next_job_id = 1
        self.next_result_id = 1
        self._lock = threading.RLock() # Reentrant lock for thread safety

    def _get_next_id(self, counter_attr: str) -> int:
        """Safely increments and returns the next ID."""
        with self._lock:
            current_id = getattr(self, counter_attr)
            setattr(self, counter_attr, current_id + 1)
            return current_id

    def create_job(self, job_data: Dict[str, Any]) -> BatchAnalysisJob:
        """Creates and stores a new batch analysis job."""
        with self._lock:
            job_id = self._get_next_id('next_job_id')

            # Ensure scan_type is an Enum member
            scan_type_input = job_data.get('scan_type', ScanType.FRONTEND)
            scan_type = ScanType(scan_type_input) if isinstance(scan_type_input, str) else scan_type_input

            job = BatchAnalysisJob(
                id=job_id,
                name=job_data.get('name', f'Batch Job {job_id}'),
                description=job_data.get('description', ''),
                created_at=datetime.now(),
                models=job_data.get('models', []),
                app_ranges=job_data.get('app_ranges', {}),
                scan_options=job_data.get('scan_options', {}),
                scan_type=scan_type,
            )

            # Pre-calculate an estimated total task count
            job.total_tasks = self._calculate_total_tasks(job)

            self.jobs[job_id] = job
            self.results[job_id] = []

            logger.info(f"Created Job {job_id}: '{job.name}' ({job.scan_type.value}, est. {job.total_tasks} tasks)")
            return job

    def _calculate_total_tasks(self, job: BatchAnalysisJob) -> int:
        """Calculates an estimated total number of tasks for a job based on configuration."""
        total_tasks = 0
        base_path = current_app.config.get('APP_BASE_PATH', Path('.')) # Needs app context or default

        for model in job.models:
            app_range = job.app_ranges.get(model, [])
            app_count = 0

            if not app_range and model in job.app_ranges:
                # Empty range means scan all apps for this model
                try:
                     # Attempt to get actual count dynamically if possible
                     model_path = base_path / model
                     app_count = sum(1 for item in model_path.iterdir()
                                     if item.is_dir() and item.name.startswith('app') and item.name[3:].isdigit())
                     logger.debug(f"Dynamically found {app_count} apps for model '{model}' for task calculation.")
                     if app_count == 0:
                         logger.warning(f"No app directories found for model '{model}' when calculating tasks.")
                except Exception as e:
                    logger.warning(f"Could not dynamically determine app count for model '{model}': {e}. Using placeholder count 10.")
                    app_count = 10 # Fallback placeholder if dynamic check fails
            else:
                app_count = len(app_range)

            # Factor in scan type (BOTH means double the tasks)
            multiplier = 2 if job.scan_type == ScanType.BOTH else 1
            total_tasks += app_count * multiplier

        return total_tasks

    def get_job(self, job_id: int) -> Optional[BatchAnalysisJob]:
        """Retrieves a job by its ID."""
        return self.jobs.get(job_id)

    def get_all_jobs(self) -> List[BatchAnalysisJob]:
        """Returns a list of all stored jobs."""
        with self._lock:
            return list(self.jobs.values())

    def update_job(self, job_id: int, **kwargs) -> Optional[BatchAnalysisJob]:
        """Updates attributes of an existing job."""
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                logger.warning(f"Attempted to update non-existent job: {job_id}")
                return None

            updated_fields = []
            for key, value in kwargs.items():
                if hasattr(job, key):
                    # Special handling for enums if necessary
                    if key == 'status' and isinstance(value, str):
                       try:
                           setattr(job, key, JobStatus(value))
                       except ValueError:
                            logger.error(f"Invalid status value '{value}' for job {job_id}")
                            continue # Skip invalid update
                    else:
                         setattr(job, key, value)
                    updated_fields.append(f"{key}={value}")
                else:
                    logger.warning(f"Attempted to set unknown attribute '{key}' on job {job_id}")

            if updated_fields:
                 logger.debug(f"Updated job {job_id}: {', '.join(updated_fields)}")
            return job

    def add_result(self, job_id: int, result_data: Dict[str, Any]) -> Optional[BatchAnalysisResult]:
        """Adds an analysis result for a specific job."""
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                logger.warning(f"Attempted to add result to non-existent job: {job_id}")
                return None # Indicate failure to add result

            result_id = self._get_next_id('next_result_id')

            # Ensure scan_type is an Enum member
            scan_type_input = result_data.get('scan_type', ScanType.FRONTEND)
            scan_type = ScanType(scan_type_input) if isinstance(scan_type_input, str) else scan_type_input

            result = BatchAnalysisResult(
                id=result_id,
                job_id=job_id,
                model=result_data.get('model', 'UnknownModel'),
                app_num=result_data.get('app_num', 0),
                status=result_data.get('status', 'failed'),
                scan_type=scan_type,
                issues_count=result_data.get('issues_count', 0),
                high_severity=result_data.get('high_severity', 0),
                medium_severity=result_data.get('medium_severity', 0),
                low_severity=result_data.get('low_severity', 0),
                scan_time=result_data.get('scan_time', datetime.now()),
                details=result_data.get('details', {})
            )

            self.results.setdefault(job_id, []).append(result)

            # Update job progress statistics
            job.completed_tasks += 1
            if job.status == JobStatus.RUNNING and job.completed_tasks >= job.total_tasks:
                final_status = JobStatus.COMPLETED if not job.errors else JobStatus.FAILED
                self.update_job(job_id, status=final_status, completed_at=datetime.now())
                logger.info(f"Job {job_id} finished. Status: {final_status}. Tasks: {job.completed_tasks}/{job.total_tasks}")

            return result

    def get_results(self, job_id: int) -> List[BatchAnalysisResult]:
        """Retrieves all results associated with a job ID."""
        return self.results.get(job_id, [])

    def get_result(self, result_id: int) -> Optional[BatchAnalysisResult]:
        """Retrieves a specific result by its unique ID."""
        with self._lock:
            for results_list in self.results.values():
                for result in results_list:
                    if result.id == result_id:
                        return result
        return None

    def delete_job(self, job_id: int) -> bool:
        """Deletes a job and all its associated results."""
        with self._lock:
            if job_id in self.jobs:
                del self.jobs[job_id]
                if job_id in self.results:
                    del self.results[job_id]
                logger.info(f"Deleted job {job_id} and its results.")
                return True
            logger.warning(f"Attempted to delete non-existent job: {job_id}")
            return False

# Global instance of the job storage
job_storage = JobStorage()

# =============================================================================
# Batch Analysis Execution Service
# =============================================================================

class BatchAnalysisService:
    """Manages the execution lifecycle of batch analysis jobs."""

    def __init__(self, storage: JobStorage):
        """
        Initializes the service.

        Args:
            storage: The JobStorage instance to use.
        """
        self.storage = storage
        self._running_jobs: Dict[int, threading.Thread] = {}
        self._cancel_flags: Set[int] = set() # Stores IDs of jobs marked for cancellation
        self.max_concurrent_jobs = int(os.environ.get("BATCH_MAX_JOBS", 2))
        self.max_concurrent_tasks = int(os.environ.get("BATCH_MAX_TASKS", 5))
        self.app: Optional[flask.Flask] = None # To be set later via set_app
        self.logger = create_logger_for_component('batch_service')
        self.logger.info(f"Initialized BatchAnalysisService (Max Jobs: {self.max_concurrent_jobs}, Max Tasks: {self.max_concurrent_tasks})")

    def set_app(self, app: flask.Flask):
        """Stores the Flask application instance for accessing context."""
        self.app = app
        self.logger.info("Flask app instance registered with BatchAnalysisService.")

    def start_job(self, job_id: int) -> bool:
        """
        Starts a batch analysis job execution in a background thread.

        Args:
            job_id: The ID of the job to start.

        Returns:
            True if the job was started successfully, False otherwise.
        """
        job = self.storage.get_job(job_id)
        if not job:
            self.logger.error(f"Cannot start job {job_id}: Job not found.")
            return False

        if job.status == JobStatus.RUNNING:
            self.logger.warning(f"Cannot start job {job_id}: Job is already running.")
            return False

        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELED]:
             self.logger.warning(f"Cannot start job {job_id}: Job has already finished (Status: {job.status.value}).")
             return False

        with self.storage._lock: # Ensure atomicity of check and update
            if len(self._running_jobs) >= self.max_concurrent_jobs:
                self.logger.warning(f"Cannot start job {job_id}: Maximum concurrent jobs ({self.max_concurrent_jobs}) reached.")
                # Optionally change status to QUEUED or similar here
                return False

            # Update job status and start time
            self.storage.update_job(
                job_id,
                status=JobStatus.RUNNING,
                started_at=datetime.now(),
                completed_tasks=0, # Reset progress if restarting
                errors=[] # Clear previous errors
            )

            thread = threading.Thread(
                target=self._run_job_wrapper, # Use wrapper for app context
                args=(job_id,),
                daemon=True,
                name=f"batch-job-{job_id}"
            )
            self._running_jobs[job_id] = thread
            thread.start()

        self.logger.info(f"Started job {job_id} ('{job.name}') in background thread.")
        return True

    def _run_job_wrapper(self, job_id: int) -> None:
         """Wrapper to run the job logic within the Flask app context."""
         if not self.app:
              self.logger.error(f"Cannot run job {job_id}: Flask app context is not available.")
              self.storage.update_job(job_id, status=JobStatus.FAILED, errors=["Flask app context unavailable"])
              return
         with self.app.app_context():
              self._run_job_logic(job_id)


    def _run_job_logic(self, job_id: int) -> None:
        """The core logic for executing tasks within a batch job."""
        job = self.storage.get_job(job_id)
        # Re-check job existence and status within the context
        if not job or job.status != JobStatus.RUNNING:
            self.logger.warning(f"Job {job_id} execution aborted: Job not found or status changed.")
            if job_id in self._running_jobs: del self._running_jobs[job_id] # Clean up running jobs dict
            return

        try:
            self.logger.info(f"Executing Job {job_id}: '{job.name}'")
            tasks = self._generate_task_list(job)

            # Update total tasks if the dynamic calculation differs significantly
            if abs(len(tasks) - job.total_tasks) > 0: # Update if calculation changed
                self.storage.update_job(job_id, total_tasks=len(tasks))
                self.logger.info(f"Refreshed task count for Job {job_id} to {len(tasks)}")

            if not tasks:
                 self.logger.warning(f"Job {job_id} has no tasks to execute.")
                 self.storage.update_job(job_id, status=JobStatus.COMPLETED, completed_at=datetime.now()) # Mark as complete if no tasks
                 if job_id in self._running_jobs: del self._running_jobs[job_id]
                 return

            with ThreadPoolExecutor(max_workers=self.max_concurrent_tasks, thread_name_prefix=f"batch_task_{job_id}") as executor:
                future_to_task = {
                    executor.submit(self._analyze_app_task, job_id, model, app_num, scan_type, job.scan_options):
                    (model, app_num, scan_type)
                    for model, app_num, scan_type in tasks
                }

                for future in concurrent.futures.as_completed(future_to_task):
                    if job_id in self._cancel_flags:
                        self.logger.info(f"Cancellation detected for job {job_id}. Stopping task processing.")
                        # Attempt to cancel pending futures (may not work if already running)
                        for f in future_to_task: f.cancel()
                        break # Exit task processing loop

                    try:
                        future.result() # Retrieve result (or raise exception if task failed)
                    except Exception as task_exc:
                        model, app_num, scan_type = future_to_task[future]
                        error_msg = f"Task Error ({model}/app{app_num}/{scan_type.value}): {str(task_exc)}"
                        self.logger.error(error_msg, exc_info=False) # Log exception without full trace unless debugging
                        job = self.storage.get_job(job_id) # Re-fetch job to append error
                        if job:
                            # Record the specific task error
                             self.storage.add_result(job_id, {
                                 "model": model, "app_num": app_num, "scan_type": scan_type,
                                 "status": "failed", "details": {"error": str(task_exc)}
                             })
                             # Append general error to job
                             self.storage.update_job(job_id, errors=job.errors + [error_msg])


            # Final status update after all tasks attempt completion or cancellation
            job = self.storage.get_job(job_id) # Get final state
            if job:
                if job_id in self._cancel_flags:
                    final_status = JobStatus.CANCELED
                elif job.errors:
                    final_status = JobStatus.FAILED
                elif job.completed_tasks >= job.total_tasks:
                     final_status = JobStatus.COMPLETED
                else:
                     # Should not happen if logic is correct, but handle unexpected state
                     final_status = JobStatus.FAILED
                     self.storage.update_job(job_id, errors=job.errors + ["Job ended prematurely"])

                self.storage.update_job(job_id, status=final_status, completed_at=datetime.now())
                self.logger.info(f"Job {job_id} finished processing. Final status: {final_status.value}")

        except Exception as e:
            self.logger.exception(f"Critical error during execution of job {job_id}: {e}")
            self.storage.update_job(job_id, status=JobStatus.FAILED, errors=["Critical job execution error: " + str(e)])
        finally:
            # Cleanup: Remove from running jobs dict and clear cancel flag
            if job_id in self._running_jobs:
                del self._running_jobs[job_id]
            if job_id in self._cancel_flags:
                self._cancel_flags.remove(job_id)


    def _generate_task_list(self, job: BatchAnalysisJob) -> List[Tuple[str, int, ScanType]]:
        """Generates the list of individual analysis tasks based on job config."""
        tasks = []
        base_path = current_app.config.get('APP_BASE_PATH', Path('.'))

        for model in job.models:
            app_range = job.app_ranges.get(model, [])
            apps_to_scan = []

            if not app_range and model in job.app_ranges:
                # Empty list means "all apps for this model"
                try:
                    model_path = base_path / model
                    apps_to_scan = sorted([
                        int(item.name[3:]) for item in model_path.iterdir()
                        if item.is_dir() and item.name.startswith('app') and item.name[3:].isdigit()
                    ])
                    if not apps_to_scan:
                         logger.warning(f"No app directories found for model '{model}' when generating tasks.")
                except Exception as e:
                    logger.error(f"Failed to list apps for model '{model}': {e}")
            else:
                apps_to_scan = sorted(list(set(app_range))) # Use provided list, ensure unique & sorted

            for app_num in apps_to_scan:
                if job.scan_type == ScanType.FRONTEND or job.scan_type == ScanType.BOTH:
                    tasks.append((model, app_num, ScanType.FRONTEND))
                if job.scan_type == ScanType.BACKEND or job.scan_type == ScanType.BOTH:
                    tasks.append((model, app_num, ScanType.BACKEND))

        logger.debug(f"Generated {len(tasks)} tasks for Job {job.id}")
        return tasks

    # This method is deprecated - logic moved to _generate_task_list with dynamic lookup
    # def _get_all_apps_for_model(self, model: str) -> List[int]: ...

    def _analyze_app_task(self, job_id: int, model: str, app_num: int, scan_type: ScanType, scan_options: Dict[str, Any]) -> None:
        """Performs the analysis for a single app within a Flask app context."""
        task_logger = create_logger_for_component(f'batch_task_{job_id}')

        # Check for cancellation before starting analysis
        if job_id in self._cancel_flags:
            task_logger.info(f"Skipping task {model}/app{app_num} ({scan_type.value}) due to job cancellation.")
            # Still need to update completed tasks count maybe? Or handle differently?
            # Let's assume cancellation stops adding results, job status handled elsewhere.
            return

        task_logger.info(f"Starting task: {model}/app{app_num} ({scan_type.value})")
        start_time = datetime.now()
        issues = []
        summary = {}
        tool_status = {}
        status = "failed" # Default status

        try:
            analyzer = None
            # Select the correct analyzer based on scan_type
            if scan_type == ScanType.FRONTEND:
                analyzer = current_app.frontend_security_analyzer
            elif scan_type == ScanType.BACKEND:
                analyzer = current_app.backend_security_analyzer
            else:
                 raise ValueError(f"Unsupported scan type for analysis task: {scan_type}")

            if not analyzer:
                 raise RuntimeError(f"Required analyzer for {scan_type.value} not found in app context.")

            full_scan = scan_options.get("full_scan", False)
            issues, tool_status, _ = analyzer.run_security_analysis(
                model, app_num, use_all_tools=full_scan
            )
            summary = analyzer.get_analysis_summary(issues)
            status = "completed"
            task_logger.info(f"Completed task: {model}/app{app_num} ({scan_type.value}). Issues: {len(issues)}")

        except Exception as e:
            task_logger.exception(f"Failed task: {model}/app{app_num} ({scan_type.value}): {e}")
            # Store error details
            summary = {"error": str(e)} # Put error in summary for reporting

        finally:
             # Ensure result is always added, even on failure or cancellation check *after* task start
            if not job_id in self._cancel_flags: # Only add result if not cancelled during execution
                 self.storage.add_result(
                     job_id,
                     {
                         "model": model,
                         "app_num": app_num,
                         "scan_type": scan_type,
                         "status": status,
                         "issues_count": len(issues),
                         "high_severity": summary.get("severity_counts", {}).get("HIGH", 0) if status == "completed" else 0,
                         "medium_severity": summary.get("severity_counts", {}).get("MEDIUM", 0) if status == "completed" else 0,
                         "low_severity": summary.get("severity_counts", {}).get("LOW", 0) if status == "completed" else 0,
                         "scan_time": start_time, # Log start time, duration can be calculated
                         "details": {
                             "issues": [asdict(issue) for issue in issues], # Use asdict for nested dataclasses
                             "summary": summary,
                             "tool_status": tool_status
                         }
                     }
                 )


    def cancel_job(self, job_id: int) -> bool:
        """
        Marks a running job for cancellation.

        Args:
            job_id: The ID of the job to cancel.

        Returns:
            True if the job was successfully marked for cancellation, False otherwise.
        """
        job = self.storage.get_job(job_id)
        if not job:
            self.logger.error(f"Cannot cancel job {job_id}: Job not found.")
            return False

        if job.status != JobStatus.RUNNING:
            self.logger.warning(f"Cannot cancel job {job_id}: Not currently running (Status: {job.status.value}).")
            return False

        self._cancel_flags.add(job_id)
        # The running thread will check this flag and update status accordingly
        self.logger.info(f"Job {job_id} marked for cancellation. Running tasks will attempt to stop.")
        # We don't immediately set status to CANCELED here, let the runner thread handle it.
        return True

    def get_job_status(self, job_id: int) -> Dict[str, Any]:
        """
        Retrieves detailed status information for a specific job.

        Args:
            job_id: The ID of the job.

        Returns:
            A dictionary containing the job's status and progress details.
        """
        job = self.storage.get_job(job_id)
        if not job:
            return {"error": f"Job {job_id} not found"}

        results = self.storage.get_results(job_id)
        frontend_results = [r for r in results if r.scan_type == ScanType.FRONTEND]
        backend_results = [r for r in results if r.scan_type == ScanType.BACKEND]

        # Calculate progress safely
        progress_percent = 0
        if job.total_tasks > 0:
            progress_percent = int((job.completed_tasks / job.total_tasks) * 100)

        # Aggregate issue counts safely
        def sum_results(results_list, key):
            return sum(getattr(r, key, 0) for r in results_list)

        return {
            "job": job.to_dict(), # Use the job's own serialization method
            "progress": {
                "total": job.total_tasks,
                "completed": job.completed_tasks,
                "percent": progress_percent
            },
            "results_summary": {
                "total_analyzed": len(results),
                "completed": sum(1 for r in results if r.status == "completed"),
                "failed": sum(1 for r in results if r.status == "failed"),
                "frontend": {
                    "count": len(frontend_results),
                    "issues_total": sum_results(frontend_results, 'issues_count'),
                    "high": sum_results(frontend_results, 'high_severity'),
                    "medium": sum_results(frontend_results, 'medium_severity'),
                    "low": sum_results(frontend_results, 'low_severity'),
                },
                "backend": {
                     "count": len(backend_results),
                    "issues_total": sum_results(backend_results, 'issues_count'),
                    "high": sum_results(backend_results, 'high_severity'),
                    "medium": sum_results(backend_results, 'medium_severity'),
                    "low": sum_results(backend_results, 'low_severity'),
                },
                "overall_issues": {
                    "total": sum_results(results, 'issues_count'),
                    "high": sum_results(results, 'high_severity'),
                    "medium": sum_results(results, 'medium_severity'),
                    "low": sum_results(results, 'low_severity'),
                }
            },
             "results_preview": [r.to_dict() for r in results[:20]] # Include a preview of recent results
        }

# Global instance of the service
batch_service = BatchAnalysisService(job_storage)

# =============================================================================
# Route Helper Functions & Decorators
# =============================================================================

def error_handler(f):
    """Decorator for handling exceptions in Flask routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        err_logger = create_logger_for_component('batch_routes')
        try:
            return f(*args, **kwargs)
        except Exception as e:
            err_logger.exception(f"Error in route {request.path} ({f.__name__}): {e}")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest": # Check if AJAX
                return jsonify({"success": False, "error": str(e)}), 500
            else:
                flash(f"An unexpected error occurred: {str(e)}", "error")
                # Redirect to dashboard or a generic error page
                return redirect(url_for('batch_analysis.batch_dashboard'))
    return decorated_function


def get_available_models() -> List[str]:
    """Retrieves the list of available AI models for selection forms."""
    try:
        # Assumes AI_MODELS is defined in utils and accessible
        from utils import AI_MODELS
        return sorted([m.name for m in AI_MODELS])
    except (ImportError, AttributeError):
        logger.warning("Could not load AI_MODELS from utils. Falling back to directory scan.")
        # Fallback: Scan directories in the base path
        try:
             base_path = current_app.config.get('APP_BASE_PATH', Path('.'))
             return sorted([item.name for item in base_path.iterdir() if item.is_dir() and not item.name.startswith('.')])
        except Exception as e:
             logger.error(f"Failed to list models from directory scan: {e}")
             return []


def parse_app_range(range_str: str) -> List[int]:
     """Parses a comma-separated string of numbers and ranges (e.g., "1-3,5,8")."""
     app_nums = set()
     if not range_str or not range_str.strip():
          return [] # Return empty list for empty input

     for part in range_str.split(','):
         part = part.strip()
         if not part: continue
         if '-' in part:
             try:
                 start, end = map(int, part.split('-', 1))
                 if start <= end:
                      app_nums.update(range(start, end + 1))
                 else:
                      logger.warning(f"Invalid range order in '{part}', skipping.")
             except ValueError:
                 logger.warning(f"Invalid range format '{part}', skipping.")
         else:
             try:
                 app_nums.add(int(part))
             except ValueError:
                 logger.warning(f"Invalid app number '{part}', skipping.")
     return sorted(list(app_nums))


# =============================================================================
# Flask Routes
# =============================================================================

@batch_analysis_bp.route("/")
@error_handler
def batch_dashboard():
    """Displays the main dashboard for batch analysis jobs."""
    jobs = sorted(job_storage.get_all_jobs(), key=lambda j: j.created_at, reverse=True)
    all_models = get_available_models()

    stats = {
        "running": sum(1 for j in jobs if j.status == JobStatus.RUNNING),
        "completed": sum(1 for j in jobs if j.status == JobStatus.COMPLETED),
        "failed": sum(1 for j in jobs if j.status in (JobStatus.FAILED, JobStatus.CANCELED)),
        "pending": sum(1 for j in jobs if j.status == JobStatus.PENDING),
    }

    return render_template(
        "batch_dashboard.html",
        jobs=jobs,
        all_models=all_models,
        stats=stats,
        # Pass through potential query args for form pre-population
        model=request.args.get('model'),
        app_num=request.args.get('app_num'),
        selected_model=request.args.get('selected_model')
    )


@batch_analysis_bp.route("/create", methods=["GET", "POST"])
@error_handler
def create_batch_job():
    """Handles the creation of a new batch analysis job via a form."""
    all_models = get_available_models()

    if request.method == "POST":
        selected_models = request.form.getlist("models")
        if not selected_models:
            flash("Please select at least one model to analyze.", "warning")
            return render_template("create_batch_job.html", models=all_models), 400

        try:
            scan_type = ScanType(request.form.get("scan_type", "frontend"))
        except ValueError:
            flash("Invalid scan type selected.", "error")
            return render_template("create_batch_job.html", models=all_models), 400

        job_data = {
            "name": request.form.get("name", f"Batch Scan - {datetime.now():%Y-%m-%d %H:%M}"),
            "description": request.form.get("description", ""),
            "models": selected_models,
            "app_ranges": {
                model: parse_app_range(request.form.get(f"app_range_{model}", ""))
                for model in selected_models
            },
            "scan_type": scan_type,
            "scan_options": {"full_scan": request.form.get("full_scan") == "on"}
        }

        job = job_storage.create_job(job_data)
        success = batch_service.start_job(job.id)

        if success:
            flash(f"Batch job '{job.name}' created and started successfully.", "success")
        else:
            flash(f"Batch job '{job.name}' created but could not be started (queue full or error). Check logs.", "warning")

        return redirect(url_for("batch_analysis.view_job", job_id=job.id))

    # GET request: Display the creation form
    return render_template(
        "create_batch_job.html",
        models=all_models,
        model=request.args.get('model'),
        app_num=request.args.get('app_num'),
        selected_model=request.args.get('selected_model')
    )


@batch_analysis_bp.route("/job/<int:job_id>")
@error_handler
def view_job(job_id: int):
    """Displays the detailed view for a specific batch job."""
    job_status_data = batch_service.get_job_status(job_id)

    if "error" in job_status_data:
        flash(job_status_data["error"], "error")
        return redirect(url_for("batch_analysis.batch_dashboard"))

    # Results are included in job_status_data['results_preview']
    # If full results needed, query separately:
    # results = sorted(job_storage.get_results(job_id), key=lambda r: (r.model, r.app_num, r.scan_type.value))

    return render_template(
        "view_job.html",
        job=job_status_data['job'], # The job data dict
        status_data=job_status_data # The full status object including summaries
        # results=results # Pass full results if needed
    )


@batch_analysis_bp.route("/job/<int:job_id>/status")
@error_handler
def get_job_status_api(job_id: int):
    """API endpoint to get the status of a batch job (for AJAX updates)."""
    status_data = batch_service.get_job_status(job_id)
    if "error" in status_data:
        return jsonify(status_data), 404
    return jsonify(status_data)


@batch_analysis_bp.route("/job/<int:job_id>/cancel", methods=["POST"])
@error_handler
def cancel_job_api(job_id: int):
    """API endpoint or form target to cancel a running job."""
    success = batch_service.cancel_job(job_id)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if is_ajax:
        if success:
            return jsonify({"message": "Job marked for cancellation.", "status": "canceling"})
        else:
            # Provide more context if possible
            job = job_storage.get_job(job_id)
            reason = "Job not found or not running." if not job or job.status != JobStatus.RUNNING else "Cancellation failed."
            return jsonify({"error": reason}), 400
    else:
        if success:
            flash(f"Job {job_id} marked for cancellation.", "info")
        else:
            flash(f"Failed to cancel job {job_id}. It might have already finished or encountered an error.", "error")
        return redirect(url_for("batch_analysis.view_job", job_id=job_id))

@batch_analysis_bp.route("/job/<int:job_id>/delete", methods=["POST"])
@error_handler
def delete_job_api(job_id: int):
    """API endpoint or form target to delete a job."""
    job = job_storage.get_job(job_id)
    if not job:
         flash(f"Job {job_id} not found.", "error")
         return redirect(url_for("batch_analysis.batch_dashboard"))

    if job.status == JobStatus.RUNNING:
         flash(f"Cannot delete running job {job_id}. Please cancel it first.", "warning")
         return redirect(url_for("batch_analysis.view_job", job_id=job_id))

    success = job_storage.delete_job(job_id)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if is_ajax:
         if success:
              return jsonify({"message": f"Job {job_id} deleted."})
         else:
              return jsonify({"error": f"Failed to delete job {job_id}."}), 500
    else:
         if success:
              flash(f"Job {job_id} and its results deleted successfully.", "success")
         else:
              flash(f"Failed to delete job {job_id}.", "error")
         return redirect(url_for("batch_analysis.batch_dashboard"))


@batch_analysis_bp.route("/job/<int:job_id>/results")
@error_handler
def get_job_results_api(job_id: int):
    """API endpoint to retrieve all results for a specific job."""
    results = job_storage.get_results(job_id)
    return jsonify({
        "job_id": job_id,
        "results": [r.to_dict() for r in results]
    })


@batch_analysis_bp.route("/result/<int:result_id>")
@error_handler
def view_result(result_id: int):
    """Displays the detailed view for a single analysis result."""
    result = job_storage.get_result(result_id)
    if not result:
        flash(f"Result {result_id} not found.", "error")
        return redirect(url_for("batch_analysis.batch_dashboard"))

    job = job_storage.get_job(result.job_id) # Get parent job info

    return render_template(
        "view_result.html",
        result=result,
        job=job,
        # Pass details directly if they exist
        issues=result.details.get("issues", []),
        summary=result.details.get("summary", {}),
        tool_status=result.details.get("tool_status", {})
    )


@batch_analysis_bp.route("/result/<int:result_id>/data")
@error_handler
def get_result_data_api(result_id: int):
    """API endpoint to get the raw data for a specific result."""
    result = job_storage.get_result(result_id)
    if not result:
        return jsonify({"error": "Result not found"}), 404
    return jsonify(result.to_dict())


# =============================================================================
# Module Initialization
# =============================================================================

def init_batch_analysis(app: flask.Flask):
    """
    Initializes the batch analysis module and registers components with the Flask app.

    Args:
        app: The Flask application instance.
    """
    logger.info("Initializing Batch Analysis Module...")

    # Provide the Flask app instance to the service for context access
    batch_service.set_app(app)

    # Ensure a base path is available in the app config for file operations
    if 'APP_BASE_PATH' not in app.config:
         # Default to parent directory of the app's root path if BASE_DIR isn't set
        app.config['APP_BASE_PATH'] = app.config.get('BASE_DIR', Path(app.root_path).parent)
        logger.info(f"APP_BASE_PATH configured to: {app.config['APP_BASE_PATH']}")


    # Optional: Check for required template files during initialization
    templates_dir = Path(app.root_path) / batch_analysis_bp.template_folder
    required_templates = [
        "batch_dashboard.html", "create_batch_job.html",
        "view_job.html", "view_result.html"
    ]
    for template_name in required_templates:
        if not (templates_dir / template_name).is_file():
            logger.warning(f"Batch analysis template not found: {template_name}")

    logger.info("Batch Analysis Module initialized successfully.")