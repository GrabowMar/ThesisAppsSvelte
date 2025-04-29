"""
Batch Analysis Module

Provides functionality for running batch analyses (security, performance, etc.)
across multiple applications or models, including job management and reporting.

Integrates with various analysis modules (FrontendSecurityAnalyzer,
BackendSecurityAnalyzer, LocustPerformanceTester, GPT4AllAnalyzer, ZAPScanner).
Relies on Flask application context for configuration and analyzer instances.
"""

import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime # Import datetime here
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set, Union

import flask
from flask import (
    Blueprint, current_app, jsonify, render_template, request, url_for,
    redirect, flash
)

# --- Import Analyzers/Testers ---
# Assume these are correctly structured and available in the project
try:
    from frontend_security_analysis import FrontendSecurityAnalyzer, SecurityIssue as FrontendSecurityIssue
except ImportError:
    FrontendSecurityAnalyzer = None
    FrontendSecurityIssue = None
    print("WARNING: FrontendSecurityAnalyzer not found.")

try:
    from backend_security_analysis import BackendSecurityAnalyzer, BackendSecurityIssue
except ImportError:
    BackendSecurityAnalyzer = None
    BackendSecurityIssue = None
    print("WARNING: BackendSecurityAnalyzer not found.")

try:
    from performance_analysis import LocustPerformanceTester, PerformanceResult
except ImportError:
    LocustPerformanceTester = None
    PerformanceResult = None # Placeholder if needed
    print("WARNING: LocustPerformanceTester not found.")

try:
    from gpt4all_analysis import GPT4AllAnalyzer, RequirementCheck
except ImportError:
    GPT4AllAnalyzer = None
    RequirementCheck = None # Placeholder if needed
    print("WARNING: GPT4AllAnalyzer not found.")

try:
    # ZAP integration is handled via ScanManager, but import for type hints if needed
    from zap_scanner import ZAPScanner, ZapVulnerability # Import ZapVulnerability if needed for result details
except ImportError:
    ZAPScanner = None
    ZapVulnerability = None
    print("WARNING: ZAPScanner not found.")

# Import ScanManager from services if available
try:
    from services import ScanManager
except ImportError:
    ScanManager = None
    print("WARNING: ScanManager not found in services.")

# Import PortManager if needed for performance tests
try:
    from services import PortManager
except ImportError:
    PortManager = None
    print("WARNING: PortManager not found in services.")

# Import utilities
try:
    from utils import get_model_index, get_apps_for_model # Import necessary utils
except ImportError:
    print("WARNING: Could not import utility functions (get_model_index, get_apps_for_model) from utils.")
    # Define dummy functions if needed for the script to load
    def get_model_index(model_name: str) -> Optional[int]: return 0
    def get_apps_for_model(model_name: str) -> List[Dict[str, Any]]: return []


from logging_service import create_logger_for_component

# Module-specific logger
logger = create_logger_for_component('batch_analysis')
route_logger = create_logger_for_component('batch_routes') # Specific logger for routes

# Flask Blueprint for batch analysis routes
# *** FIXED: Changed prefix to match common registration pattern and screenshot URL ***
batch_analysis_bp = Blueprint(
    "batch_analysis",
    __name__,
    template_folder="templates", # Assumes templates are in a 'templates' subdir relative to this file
    url_prefix="/batch-analysis" # Corrected prefix
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

# Updated: More specific analysis types
class AnalysisType(str, Enum):
    """Enumeration for the specific type of analysis to perform."""
    FRONTEND_SECURITY = "frontend_security"
    BACKEND_SECURITY = "backend_security"
    PERFORMANCE = "performance"
    GPT4ALL = "gpt4all"
    ZAP = "zap"

@dataclass
class BatchAnalysisJob:
    """Represents a batch analysis job configuration and status."""
    id: int
    name: str
    description: str
    created_at: datetime
    status: JobStatus = JobStatus.PENDING
    models: List[str] = field(default_factory=list)
    # Maps model name to list of app numbers. Empty list means "all apps for this model".
    app_ranges: Dict[str, List[int]] = field(default_factory=dict)
    # Updated: List of analysis types to run for this job
    analysis_types: List[AnalysisType] = field(default_factory=list)
    # Stores specific options for each analysis type (e.g., perf users, zap context)
    analysis_options: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_tasks: int = 0 # Total number of individual app analyses (app * analysis_type)
    completed_tasks: int = 0
    results_summary: Dict[str, Any] = field(default_factory=dict) # Stores aggregated counts
    errors: List[str] = field(default_factory=list) # Stores errors encountered during job execution

    # Add a property for formatted created_at time
    @property
    def created_at_formatted(self) -> str:
        return self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else 'N/A'

    def to_dict(self) -> Dict[str, Any]:
        """Converts the job object to a dictionary suitable for JSON serialization."""
        result_dict = asdict(self)
        # Convert datetime objects to ISO format strings
        for key in ['created_at', 'started_at', 'completed_at']:
            if isinstance(result_dict[key], datetime):
                result_dict[key] = result_dict[key].isoformat()
        # Convert enums to their string values
        result_dict['status'] = self.status.value
        result_dict['analysis_types'] = [at.value for at in self.analysis_types]
        # Add formatted date string
        result_dict['created_at_formatted'] = self.created_at_formatted
        return result_dict


@dataclass
class BatchAnalysisResult:
    """Represents the result of a single analysis task within a batch job."""
    id: int
    job_id: int
    model: str
    app_num: int
    status: str # e.g., "completed", "failed", "skipped", "triggered" (for ZAP)
    analysis_type: AnalysisType # Use the specific enum
    issues_count: int = 0 # Generic count, might represent different things
    high_severity: int = 0 # Primarily for security scans
    medium_severity: int = 0
    low_severity: int = 0
    scan_start_time: Optional[datetime] = None
    scan_end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    # Stores detailed results specific to the analysis type
    # e.g., list of SecurityIssue dicts, PerformanceResult dict, list of RequirementCheck dicts, ZAP scan ID
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the result object to a dictionary suitable for JSON serialization."""
        result_dict = asdict(self)
        if isinstance(result_dict['scan_start_time'], datetime):
            result_dict['scan_start_time'] = result_dict['scan_start_time'].isoformat()
        if isinstance(result_dict['scan_end_time'], datetime):
            result_dict['scan_end_time'] = result_dict['scan_end_time'].isoformat()
        result_dict['analysis_type'] = self.analysis_type.value # Use enum value
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

    def create_job(self, job_data: Dict[str, Any], app_context: flask.Flask) -> BatchAnalysisJob:
        """Creates and stores a new batch analysis job."""
        with self._lock:
            job_id = self._get_next_id('next_job_id')

            # Ensure analysis_types are Enum members
            analysis_types_input = job_data.get('analysis_types', [])
            valid_analysis_types = []
            if isinstance(analysis_types_input, list):
                for at_input in analysis_types_input:
                    try:
                        at_enum = AnalysisType(at_input) if isinstance(at_input, str) else at_input
                        if isinstance(at_enum, AnalysisType):
                            valid_analysis_types.append(at_enum)
                        else: raise ValueError("Invalid type")
                    except ValueError:
                        logger.warning(f"Invalid analysis_type '{at_input}' provided. Skipping.")
            else:
                logger.warning(f"Invalid 'analysis_types' format: {analysis_types_input}. Expected a list.")

            if not valid_analysis_types:
                raise ValueError("No valid analysis types selected for the job.")

            job = BatchAnalysisJob(
                id=job_id,
                name=job_data.get('name', f'Batch Job {job_id}'),
                description=job_data.get('description', ''),
                created_at=datetime.now(),
                models=job_data.get('models', []),
                app_ranges=job_data.get('app_ranges', {}),
                analysis_types=valid_analysis_types, # Use validated list
                analysis_options=job_data.get('analysis_options', {}),
            )

            # Pre-calculate an estimated total task count using app context for path
            job.total_tasks = self._calculate_total_tasks(job, app_context)

            self.jobs[job_id] = job
            self.results[job_id] = []

            analysis_names = ', '.join([at.value for at in job.analysis_types])
            logger.info(f"Created Job {job_id}: '{job.name}' (Types: {analysis_names}, est. {job.total_tasks} tasks)")
            return job

    def _calculate_total_tasks(self, job: BatchAnalysisJob, app_context: flask.Flask) -> int:
        """
        Calculates an estimated total number of tasks for a job based on configuration.
        Requires Flask app context to resolve the base path.
        """
        total_tasks = 0
        # Use the configured APP_BASE_PATH from the Flask app context
        # Ensure APP_BASE_PATH is set during app initialization
        base_path_str = app_context.config.get('APP_BASE_PATH')
        if not base_path_str:
             logger.error("APP_BASE_PATH not found in Flask config. Cannot calculate tasks.")
             return 0 # Cannot calculate without base path
        base_path = Path(base_path_str)
        logger.debug(f"Calculating tasks using base path: {base_path}")

        for model in job.models:
            app_range = job.app_ranges.get(model, [])
            app_count = 0

            # Check if the range for this model is explicitly empty, meaning "scan all"
            scan_all_apps = (model in job.app_ranges and not job.app_ranges[model])

            if scan_all_apps:
                # Attempt to get actual count dynamically
                try:
                    model_path = base_path / model
                    if not model_path.is_dir():
                        logger.warning(f"Model directory not found for task calculation: {model_path}")
                        continue # Skip this model if dir doesn't exist

                    app_count = sum(1 for item in model_path.iterdir()
                                    if item.is_dir() and item.name.startswith('app') and item.name[3:].isdigit())
                    logger.debug(f"Dynamically found {app_count} apps for model '{model}' for task calculation.")
                    if app_count == 0:
                        logger.warning(f"No app directories found for model '{model}' when calculating tasks.")
                except Exception as e:
                    logger.warning(f"Could not dynamically determine app count for model '{model}': {e}. Assuming 0 tasks for this model.")
                    app_count = 0 # Assume 0 if dynamic check fails
            else:
                # Use the length of the provided app number list
                app_count = len(app_range)

            # Factor in the number of analysis types selected
            multiplier = len(job.analysis_types)
            total_tasks += app_count * multiplier

        return total_tasks

    def get_job(self, job_id: int) -> Optional[BatchAnalysisJob]:
        """Retrieves a job by its ID."""
        with self._lock:
            return self.jobs.get(job_id)

    def get_all_jobs(self) -> List[BatchAnalysisJob]:
        """Returns a list of all stored jobs."""
        with self._lock:
            return [job for job in self.jobs.values()]

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
                    current_value = getattr(job, key)
                    # Handle status enum conversion
                    if key == 'status' and isinstance(value, str):
                        try:
                            new_status = JobStatus(value)
                            if new_status != current_value:
                                setattr(job, key, new_status)
                                updated_fields.append(f"{key}={new_status.value}")
                        except ValueError:
                            logger.error(f"Invalid status value '{value}' for job {job_id}")
                            continue # Skip invalid update
                    elif value != current_value: # Only update if value changed
                        setattr(job, key, value)
                        # Truncate long error lists for logging
                        if key == 'errors' and isinstance(value, list) and len(value) > 5:
                            updated_fields.append(f"{key}=<list len {len(value)}>")
                        else:
                            updated_fields.append(f"{key}={value}")
                else:
                    logger.warning(f"Attempted to set unknown attribute '{key}' on job {job_id}")

            if updated_fields:
                logger.debug(f"Updated job {job_id}: {', '.join(updated_fields)}")
            return job

    def add_result(self, job_id: int, result_data: Dict[str, Any]) -> Optional[BatchAnalysisResult]:
        """Adds an analysis result for a specific job and updates job progress."""
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                logger.warning(f"Attempted to add result to non-existent job: {job_id}")
                return None # Indicate failure to add result

            result_id = self._get_next_id('next_result_id')

            # Ensure analysis_type is an Enum member
            analysis_type_input = result_data.get('analysis_type', AnalysisType.FRONTEND_SECURITY) # Default? Risky.
            try:
                analysis_type = AnalysisType(analysis_type_input) if isinstance(analysis_type_input, str) else analysis_type_input
                if not isinstance(analysis_type, AnalysisType): raise ValueError("Invalid type")
            except ValueError:
                logger.error(f"Invalid analysis_type '{analysis_type_input}' in result data for job {job_id}. Skipping result.")
                return None

            # Calculate duration if start and end times are available
            duration = None
            start_time = result_data.get('scan_start_time')
            end_time = result_data.get('scan_end_time', datetime.now()) # Default end time to now if missing
            if isinstance(start_time, datetime) and isinstance(end_time, datetime):
                duration = (end_time - start_time).total_seconds()

            result = BatchAnalysisResult(
                id=result_id,
                job_id=job_id,
                model=result_data.get('model', 'UnknownModel'),
                app_num=result_data.get('app_num', 0),
                status=result_data.get('status', 'failed'),
                analysis_type=analysis_type,
                issues_count=result_data.get('issues_count', 0),
                high_severity=result_data.get('high_severity', 0),
                medium_severity=result_data.get('medium_severity', 0),
                low_severity=result_data.get('low_severity', 0),
                scan_start_time=start_time,
                scan_end_time=end_time,
                duration_seconds=duration,
                details=result_data.get('details', {})
            )

            self.results.setdefault(job_id, []).append(result)

            # --- Update Job Progress and Summary ---
            job.completed_tasks += 1
            # Aggregate results into job summary
            summary = job.results_summary # Get current summary dict
            summary['total_tasks_completed'] = summary.get('total_tasks_completed', 0) + 1
            summary[f'{analysis_type.value}_tasks_completed'] = summary.get(f'{analysis_type.value}_tasks_completed', 0) + 1

            if result.status == 'completed':
                # Aggregate generic counts
                summary['issues_total'] = summary.get('issues_total', 0) + result.issues_count
                # Aggregate severity only if applicable (security scans)
                if analysis_type in [AnalysisType.FRONTEND_SECURITY, AnalysisType.BACKEND_SECURITY, AnalysisType.ZAP]:
                    summary['high_total'] = summary.get('high_total', 0) + result.high_severity
                    summary['medium_total'] = summary.get('medium_total', 0) + result.medium_severity
                    summary['low_total'] = summary.get('low_total', 0) + result.low_severity
                # Track per-type counts
                summary[f'{analysis_type.value}_issues_total'] = summary.get(f'{analysis_type.value}_issues_total', 0) + result.issues_count
                if analysis_type in [AnalysisType.FRONTEND_SECURITY, AnalysisType.BACKEND_SECURITY, AnalysisType.ZAP]:
                    summary[f'{analysis_type.value}_high'] = summary.get(f'{analysis_type.value}_high', 0) + result.high_severity
                    summary[f'{analysis_type.value}_medium'] = summary.get(f'{analysis_type.value}_medium', 0) + result.medium_severity
                    summary[f'{analysis_type.value}_low'] = summary.get(f'{analysis_type.value}_low', 0) + result.low_severity
            elif result.status == 'failed':
                summary['tasks_failed'] = summary.get('tasks_failed', 0) + 1
                summary[f'{analysis_type.value}_tasks_failed'] = summary.get(f'{analysis_type.value}_tasks_failed', 0) + 1
            elif result.status == 'triggered': # Handle ZAP trigger
                 summary['tasks_triggered'] = summary.get('tasks_triggered', 0) + 1
                 summary[f'{analysis_type.value}_tasks_triggered'] = summary.get(f'{analysis_type.value}_tasks_triggered', 0) + 1

            # Check if job is finished
            # Use >= in case total_tasks calculation was slightly off or changed during run
            if job.status == JobStatus.RUNNING and job.completed_tasks >= job.total_tasks:
                final_status = JobStatus.COMPLETED if not job.errors and summary.get('tasks_failed', 0) == 0 else JobStatus.FAILED
                self.update_job(job_id, status=final_status, completed_at=datetime.now(), results_summary=summary)
                logger.info(f"Job {job_id} finished. Status: {final_status.value}. Tasks: {job.completed_tasks}/{job.total_tasks}")
            else:
                # Update summary even if job is still running
                self.update_job(job_id, results_summary=summary)

            return result

    def get_results(self, job_id: int) -> List[BatchAnalysisResult]:
        """Retrieves all results associated with a job ID."""
        with self._lock:
            # Return copies to prevent external modification
            return [res for res in self.results.get(job_id, [])]

    def get_result(self, result_id: int) -> Optional[BatchAnalysisResult]:
        """Retrieves a specific result by its unique ID."""
        with self._lock:
            for results_list in self.results.values():
                for result in results_list:
                    if result.id == result_id:
                        return result # Return the actual object
        return None

    def delete_job(self, job_id: int) -> bool:
        """Deletes a job and all its associated results."""
        with self._lock:
            if job_id in self.jobs:
                # Ensure job is not running before deleting
                if self.jobs[job_id].status == JobStatus.RUNNING:
                    logger.error(f"Cannot delete job {job_id}: Job is currently running.")
                    return False
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
        self.max_concurrent_jobs = int(os.environ.get("BATCH_MAX_JOBS", 2)) # Max jobs running concurrently
        self.max_concurrent_tasks = int(os.environ.get("BATCH_MAX_TASKS", 4)) # Max tasks per job
        self.app: Optional[flask.Flask] = None # To be set later via set_app
        self.logger = create_logger_for_component('batch_service')
        self.logger.info(f"Initialized BatchAnalysisService (Max Jobs: {self.max_concurrent_jobs}, Max Tasks Per Job: {self.max_concurrent_tasks})")

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

        # Prevent starting if already running or finished
        if job.status == JobStatus.RUNNING:
            self.logger.warning(f"Cannot start job {job_id}: Job is already running.")
            return False
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELED]:
            self.logger.warning(f"Cannot start job {job_id}: Job has already finished (Status: {job.status.value}).")
            return False

        with self.storage._lock: # Ensure atomicity of check and update
            if len(self._running_jobs) >= self.max_concurrent_jobs:
                self.logger.warning(f"Cannot start job {job_id}: Maximum concurrent jobs ({self.max_concurrent_jobs}) reached. Job remains {job.status.value}.")
                # Consider changing status to QUEUED if implementing a queue system
                return False

            # --- Reset job state before starting/restarting ---
            self.logger.info(f"Resetting state for job {job_id} before starting.")
            self.storage.update_job(
                job_id,
                status=JobStatus.RUNNING,
                started_at=datetime.now(),
                completed_at=None, # Clear completion time
                completed_tasks=0, # Reset progress
                errors=[], # Clear previous errors
                results_summary={} # Clear previous summary
            )
            # Recalculate total tasks in case app structure changed
            if self.app:
                # Need the actual app object, not just the type hint
                current_flask_app = self.app
                job.total_tasks = self.storage._calculate_total_tasks(job, current_flask_app)
                self.storage.update_job(job_id, total_tasks=job.total_tasks)
                self.logger.info(f"Refreshed task count for Job {job_id} to {job.total_tasks}")
            else:
                self.logger.error("Cannot recalculate task count: Flask app context not available.")
                # Proceed with potentially stale task count


            # Clear any previous results for this job if restarting
            if job_id in self.storage.results:
                self.storage.results[job_id] = []
                self.logger.info(f"Cleared previous results for job {job_id}.")


            thread = threading.Thread(
                target=self._run_job_wrapper, # Use wrapper for app context
                args=(job_id,),
                daemon=True,
                name=f"batch-job-{job_id}"
            )
            self._running_jobs[job_id] = thread
            thread.start()

        self.logger.info(f"Started job {job_id} ('{job.name}') in background thread. Total tasks: {job.total_tasks}")
        return True

    def _run_job_wrapper(self, job_id: int) -> None:
        """Wrapper to run the job logic within the Flask app context."""
        if not self.app:
            self.logger.error(f"Cannot run job {job_id}: Flask app context is not available.")
            # Update status directly if possible, otherwise it remains RUNNING until manually fixed
            try:
                self.storage.update_job(job_id, status=JobStatus.FAILED, errors=["Flask app context unavailable at runtime"])
            except Exception as e:
                self.logger.error(f"Failed to update job {job_id} status after app context error: {e}")
            # Clean up running job entry
            if job_id in self._running_jobs: del self._running_jobs[job_id]
            return

        # Get the actual Flask app object before entering the context
        current_flask_app = self.app
        with current_flask_app.app_context():
            self.logger.info(f"App context acquired for job {job_id} thread.")
            self._run_job_logic(job_id)


    def _run_job_logic(self, job_id: int) -> None:
        """The core logic for executing tasks within a batch job."""
        job = self.storage.get_job(job_id)
        # Re-check job existence and status within the context
        if not job or job.status != JobStatus.RUNNING:
            self.logger.warning(f"Job {job_id} execution aborted: Job not found or status changed before execution start.")
            if job_id in self._running_jobs: del self._running_jobs[job_id] # Clean up running jobs dict
            return

        try:
            self.logger.info(f"Executing Job {job_id}: '{job.name}'")
            tasks = self._generate_task_list(job)

            # Update total tasks if the dynamic calculation differs significantly from initial estimate
            if len(tasks) != job.total_tasks:
                self.logger.info(f"Task count for Job {job_id} changed from {job.total_tasks} to {len(tasks)}. Updating job.")
                self.storage.update_job(job_id, total_tasks=len(tasks))
                job.total_tasks = len(tasks) # Update local job object too

            if not tasks:
                self.logger.warning(f"Job {job_id} has no tasks to execute (check model/app configuration).")
                self.storage.update_job(job_id, status=JobStatus.COMPLETED, completed_at=datetime.now()) # Mark as complete if no tasks
                if job_id in self._running_jobs: del self._running_jobs[job_id]
                return

            # Use ThreadPoolExecutor to run analysis tasks concurrently
            with ThreadPoolExecutor(max_workers=self.max_concurrent_tasks, thread_name_prefix=f"batch_task_{job_id}") as executor:
                # Map futures to task details for error reporting
                future_to_task = {
                    executor.submit(self._analyze_app_task, job_id, model, app_num, analysis_type, job.analysis_options):
                    (model, app_num, analysis_type)
                    for model, app_num, analysis_type in tasks
                }

                # Process completed tasks
                for future in as_completed(future_to_task):
                    # Check for cancellation flag *before* processing result
                    if job_id in self._cancel_flags:
                        self.logger.info(f"Cancellation detected for job {job_id}. Skipping result processing.")
                        # Attempt to cancel remaining futures (best effort)
                        for f in future_to_task: f.cancel()
                        break # Exit task processing loop

                    model, app_num, analysis_type = future_to_task[future]
                    try:
                        # Retrieve result. If the task raised an exception, it will be re-raised here.
                        future.result()
                        self.logger.debug(f"Task {model}/app{app_num} ({analysis_type.value}) completed successfully.")
                    except Exception as task_exc:
                        error_msg = f"Task Error ({model}/app{app_num}/{analysis_type.value}): {type(task_exc).__name__} - {str(task_exc)}"
                        self.logger.error(error_msg, exc_info=False) # Log concise error
                        self.logger.debug("Task failure details:", exc_info=True) # Log full traceback on debug level

                        # Record the specific task error as a result
                        self.storage.add_result(job_id, {
                            "model": model, "app_num": app_num, "analysis_type": analysis_type,
                            "status": "failed",
                            "scan_start_time": datetime.now(), # Approximate time
                            "details": {"error": error_msg} # Store the error message
                        })
                        # Append general error to the main job object
                        current_job = self.storage.get_job(job_id) # Re-fetch job to append error safely
                        if current_job:
                            # Use update_job which handles locking
                            self.storage.update_job(job_id, errors=current_job.errors + [error_msg])


            # --- Final status update after all tasks attempt completion or cancellation ---
            # Re-fetch job to get its final state after all tasks are processed
            job = self.storage.get_job(job_id)
            if job:
                final_status = JobStatus.COMPLETED # Assume success initially
                # Use job.errors which should have been updated by failed tasks
                final_errors = job.errors

                if job_id in self._cancel_flags:
                    final_status = JobStatus.CANCELED
                    # Avoid adding duplicate messages if already added
                    if "Job canceled by user." not in final_errors:
                        final_errors.append("Job canceled by user.")
                elif job.errors or job.results_summary.get('tasks_failed', 0) > 0:
                    # If any errors were logged to the job or tasks failed
                    final_status = JobStatus.FAILED
                # Check if all tasks completed, even if some failed (ensure loop finished)
                elif job.completed_tasks < job.total_tasks and final_status != JobStatus.CANCELED:
                    # If not canceled, no errors, but not all tasks completed
                    final_status = JobStatus.FAILED
                    error_msg = f"Job ended prematurely. Completed {job.completed_tasks}/{job.total_tasks} tasks."
                    if error_msg not in final_errors:
                        final_errors.append(error_msg)

                self.storage.update_job(job_id, status=final_status, completed_at=datetime.now(), errors=final_errors)
                self.logger.info(f"Job {job_id} finished processing. Final status: {final_status.value}")

        except Exception as e:
            self.logger.exception(f"Critical error during execution of job {job_id}: {e}")
            # Ensure job status is updated to FAILED on critical error
            self.storage.update_job(job_id, status=JobStatus.FAILED, errors=["Critical job execution error: " + str(e)], completed_at=datetime.now())
        finally:
            # Cleanup: Remove from running jobs dict and clear cancel flag regardless of outcome
            if job_id in self._running_jobs:
                del self._running_jobs[job_id]
                self.logger.debug(f"Removed job {job_id} from running jobs.")
            if job_id in self._cancel_flags:
                self._cancel_flags.remove(job_id)
                self.logger.debug(f"Removed cancel flag for job {job_id}.")


    def _generate_task_list(self, job: BatchAnalysisJob) -> List[Tuple[str, int, AnalysisType]]:
        """Generates the list of individual analysis tasks based on job config."""
        tasks = []
        # Needs app context to get the base path
        if not self.app:
            logger.error("Cannot generate task list: Flask app context not available.")
            return []
        # Use current_app which is available within the app context established by _run_job_wrapper
        base_path_str = current_app.config.get('APP_BASE_PATH')
        if not base_path_str:
             logger.error("APP_BASE_PATH not found in Flask config. Cannot generate tasks.")
             return []
        base_path = Path(base_path_str)

        for model in job.models:
            model_path = base_path / model
            if not model_path.is_dir():
                logger.warning(f"Model directory '{model_path}' not found. Skipping model '{model}' for job {job.id}.")
                continue # Skip this model

            app_range = job.app_ranges.get(model, [])
            apps_to_scan = []

            # Check if the range for this model is explicitly empty, meaning "scan all"
            scan_all_apps = (model in job.app_ranges and not job.app_ranges[model])

            if scan_all_apps:
                # Scan the model directory for app subdirectories
                try:
                    apps_to_scan = sorted([
                        int(item.name[3:]) for item in model_path.iterdir()
                        if item.is_dir() and item.name.startswith('app') and item.name[3:].isdigit()
                    ])
                    if not apps_to_scan:
                        logger.warning(f"No app directories (app<N>) found in '{model_path}' for job {job.id}.")
                except Exception as e:
                    logger.error(f"Failed to list apps for model '{model}' in '{model_path}': {e}")
            else:
                # Use the provided list of app numbers
                apps_to_scan = sorted(list(set(app_range))) # Ensure unique & sorted

            # Create tasks, verifying app subdirectories exist
            for app_num in apps_to_scan:
                # TODO: Use a centralized function (e.g., utils.get_app_directory)
                app_dir = model_path / f"app{app_num}"
                if not app_dir.is_dir():
                    logger.warning(f"App directory '{app_dir}' not found. Skipping app {app_num} for model '{model}' in job {job.id}.")
                    continue # Skip task generation for this specific app

                # Add tasks for each selected analysis type
                for analysis_type in job.analysis_types:
                    tasks.append((model, app_num, analysis_type))

        logger.debug(f"Generated {len(tasks)} tasks for Job {job.id}")
        return tasks

    def _analyze_app_task(self, job_id: int, model: str, app_num: int, analysis_type: AnalysisType, analysis_options: Dict[str, Any]) -> None:
        """
        Performs the specific analysis for a single app/analysis type.
        This runs within the Flask app context provided by the wrapper.
        Updates the job storage with the result.
        """
        task_logger = create_logger_for_component(f'batch_task_{job_id}')
        task_desc = f"{model}/app{app_num} ({analysis_type.value})"

        # --- Cancellation Check ---
        if job_id in self._cancel_flags:
            task_logger.info(f"Skipping task {task_desc} due to job cancellation.")
            # Do not add a result for cancelled tasks, but ensure job progress is updated eventually
            # The main loop handles final job status update.
            return

        task_logger.info(f"Starting task: {task_desc}")
        start_time = datetime.now()
        issues = []
        summary = {}
        tool_status = {}
        raw_output = None # Initialize raw_output
        status = "failed" # Default status unless successful
        result_details = {} # Store specific results here
        issues_count = 0
        high_sev = 0
        med_sev = 0
        low_sev = 0

        try:
            # --- Select and Run Analyzer/Tester ---
            if analysis_type == AnalysisType.FRONTEND_SECURITY:
                analyzer = getattr(current_app, 'frontend_security_analyzer', None)
                if not analyzer or not FrontendSecurityAnalyzer: raise RuntimeError("FrontendSecurityAnalyzer not available.")
                full_scan = analysis_options.get(AnalysisType.FRONTEND_SECURITY.value, {}).get("full_scan", False) # Get options for this type
                issues, tool_status, raw_output = analyzer.run_security_analysis(model, app_num, use_all_tools=full_scan)
                summary = analyzer.get_analysis_summary(issues)
                status = "completed"
                issues_count = len(issues)
                high_sev = summary.get("severity_counts", {}).get("HIGH", 0)
                med_sev = summary.get("severity_counts", {}).get("MEDIUM", 0)
                low_sev = summary.get("severity_counts", {}).get("LOW", 0)
                result_details["issues"] = [asdict(issue) for issue in issues] # Convert issues to dicts
                result_details["summary"] = summary
                result_details["tool_status"] = tool_status

            elif analysis_type == AnalysisType.BACKEND_SECURITY:
                analyzer = getattr(current_app, 'backend_security_analyzer', None)
                if not analyzer or not BackendSecurityAnalyzer: raise RuntimeError("BackendSecurityAnalyzer not available.")
                full_scan = analysis_options.get(AnalysisType.BACKEND_SECURITY.value, {}).get("full_scan", False) # Get options for this type
                issues, tool_status, raw_output = analyzer.run_security_analysis(model, app_num, use_all_tools=full_scan)
                summary = analyzer.get_analysis_summary(issues)
                status = "completed"
                issues_count = len(issues)
                high_sev = summary.get("severity_counts", {}).get("HIGH", 0)
                med_sev = summary.get("severity_counts", {}).get("MEDIUM", 0)
                low_sev = summary.get("severity_counts", {}).get("LOW", 0)
                result_details["issues"] = [asdict(issue) for issue in issues] # Convert issues to dicts
                result_details["summary"] = summary
                result_details["tool_status"] = tool_status

            elif analysis_type == AnalysisType.PERFORMANCE:
                tester = getattr(current_app, 'performance_tester', None)
                port_manager = getattr(current_app, 'port_manager', None) # Get PortManager instance
                if not tester or not LocustPerformanceTester: raise RuntimeError("LocustPerformanceTester not available.")
                if not port_manager or not PortManager: raise RuntimeError("PortManager not available.")

                # Get parameters from analysis_options
                perf_opts = analysis_options.get(AnalysisType.PERFORMANCE.value, {}) # Get options for this type
                users = perf_opts.get('users', 10)
                duration = perf_opts.get('duration', 30) # In seconds
                spawn_rate = perf_opts.get('spawn_rate', 1)
                endpoints = perf_opts.get('endpoints', [{"path": "/", "method": "GET"}]) # Default endpoint

                # Get port using PortManager
                model_idx = get_model_index(model)
                if model_idx is None: raise ValueError(f"Model index not found for '{model}'")
                ports = port_manager.get_app_ports(model_idx, app_num)
                target_port = ports['frontend'] # Assume testing frontend port
                host_url = f"http://localhost:{target_port}" # Assuming localhost

                task_logger.info(f"Running performance test: {host_url}, Users={users}, Duration={duration}s")
                perf_result: PerformanceResult = tester.run_test_library(
                    test_name=f"batch_{job_id}_{model}_{app_num}",
                    host=host_url,
                    endpoints=endpoints,
                    user_count=users,
                    spawn_rate=spawn_rate,
                    run_time=duration,
                    generate_graphs=True, # Generate graphs for batch results
                    model=model, # Pass model/app for consolidated results saving
                    app_num=app_num
                )
                status = "completed"
                summary = perf_result.to_dict() # Store full result dict as summary/details
                issues_count = summary.get('total_failures', 0) # Use failures as 'issues' count
                # Performance doesn't have severity in the same way, maybe use RPS/Avg Time?
                # For now, set severity counts to 0
                result_details = summary # Store the whole result object
                tool_status = {"Locust": "Completed"}
                # Store JSON as raw output preview
                preview = json.dumps(summary, indent=2)[:1000]
                if len(json.dumps(summary, indent=2)) > 1000: preview += "..."
                raw_output = preview


            elif analysis_type == AnalysisType.GPT4ALL:
                analyzer = getattr(current_app, 'gpt4all_analyzer', None)
                if not analyzer or not GPT4AllAnalyzer: raise RuntimeError("GPT4AllAnalyzer not available.")

                gpt_opts = analysis_options.get(AnalysisType.GPT4ALL.value, {}) # Get options for this type
                requirements = gpt_opts.get('requirements') # Get requirements from options
                if not requirements: # Load defaults if not provided
                    requirements, _ = analyzer.get_requirements_for_app(app_num)

                task_logger.info(f"Running GPT4All analysis with {len(requirements)} requirements.")
                gpt_results: List[RequirementCheck] = analyzer.check_requirements(model, app_num, requirements)
                status = "completed"
                # Convert RequirementCheck objects to dicts for storage
                issues_list = [res.to_dict() for res in gpt_results]
                issues_count = len(issues_list)
                # Summarize GPT4All results
                met_count = sum(1 for r in issues_list if r.get('result', {}).get('met', False))
                summary = {"requirements_checked": issues_count, "met_count": met_count}
                # Store specific counts for summary aggregation
                result_details['summary'] = {
                    'gpt4all_reqs_checked_total': issues_count,
                    'gpt4all_reqs_met_total': met_count
                }
                # GPT4All doesn't have severity in the same way
                result_details["issues"] = issues_list # Store list of result dicts
                tool_status = {"GPT4All": "Completed"}
                # Store JSON as raw output preview
                preview = json.dumps(issues_list, indent=2)[:1000]
                if len(json.dumps(issues_list, indent=2)) > 1000: preview += "..."
                raw_output = preview


            elif analysis_type == AnalysisType.ZAP:
                scan_manager = getattr(current_app, 'scan_manager', None) # Use ScanManager from utils/app context
                if not scan_manager or not ScanManager: raise RuntimeError("ZAP ScanManager not available.")
                if not ZAPScanner: raise RuntimeError("ZAPScanner class not available.") # Check if ZAP module loaded

                zap_opts = analysis_options.get(AnalysisType.ZAP.value, {}) # Get options for this type
                # Trigger ZAP scan via ScanManager (assumes ZAP routes handle async start)
                task_logger.info("Triggering ZAP scan via ScanManager...")
                # Note: ZAP options might need to be passed differently depending on ScanManager implementation
                scan_id = scan_manager.create_scan(model, app_num, zap_opts)
                # TODO: The actual triggering logic needs to exist, likely calling a ZAP route or service method.
                # This task only records that the trigger was attempted.
                # We need a mechanism (e.g., polling ZAP status route) if we want to wait for completion here.
                # For now, just report 'triggered'.
                status = "triggered"
                summary = {"zap_scan_id": scan_id} # Store scan ID for reference
                tool_status = {"ZAP": "Triggered"}
                raw_output = f"ZAP scan triggered via ScanManager with ID: {scan_id}. Monitor ZAP status separately."
                issues_count = 0 # No immediate issues
                result_details["summary"] = summary # Store ZAP scan ID in details

            else:
                raise ValueError(f"Unsupported analysis type: {analysis_type}")

            task_logger.info(f"Completed task: {task_desc}. Status: {status}")

        except Exception as e:
            # Catch errors during analysis
            error_message = f"Failed task {task_desc}: {type(e).__name__} - {str(e)}"
            task_logger.error(error_message, exc_info=False)
            task_logger.debug(f"Task failure details for {task_desc}:", exc_info=True)
            status = "failed"
            summary = {"error": error_message}
            failed_tool_name = analysis_type.value # Use enum value as tool name
            tool_status[failed_tool_name] = f"❌ Error: {str(e)}"
            result_details["error"] = error_message # Add error to details


        finally:
            # --- Record Result ---
            # Check cancellation flag again before adding result
            if not job_id in self._cancel_flags:
                end_time = datetime.now()
                # Add raw output preview to details if available
                if raw_output:
                    preview = str(raw_output)[:1000] # Limit preview size
                    if len(str(raw_output)) > 1000: preview += "..."
                    result_details["raw_output_preview"] = preview

                self.storage.add_result(
                    job_id,
                    {
                        "model": model,
                        "app_num": app_num,
                        "analysis_type": analysis_type,
                        "status": status,
                        "issues_count": issues_count,
                        "high_severity": high_sev,
                        "medium_severity": med_sev,
                        "low_severity": low_sev,
                        "scan_start_time": start_time,
                        "scan_end_time": end_time,
                        "details": result_details # Store the collected details
                    }
                )
            else:
                task_logger.info(f"Skipped adding result for task {task_desc} due to job cancellation.")


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

        # Only cancel jobs that are actually running
        if job.status != JobStatus.RUNNING:
            self.logger.warning(f"Cannot cancel job {job_id}: Not currently running (Status: {job.status.value}).")
            return False

        # Set the cancel flag. The running thread will check this.
        self._cancel_flags.add(job_id)
        self.logger.info(f"Job {job_id} marked for cancellation. Running tasks will attempt to stop gracefully.")
        # Do NOT change the status here; let the runner thread update it to CANCELED when it finishes processing.
        return True

    def get_job_status(self, job_id: int) -> Dict[str, Any]:
        """
        Retrieves detailed status information for a specific job, including aggregated results.

        Args:
            job_id: The ID of the job.

        Returns:
            A dictionary containing the job's status and progress details.
            Returns {"error": ...} if the job is not found.
        """
        job = self.storage.get_job(job_id)
        if not job:
            return {"error": f"Job {job_id} not found"}

        # Calculate progress safely
        progress_percent = 0
        if job.total_tasks > 0:
            # Ensure completed_tasks doesn't exceed total_tasks for percentage calculation
            completed = min(job.completed_tasks, job.total_tasks)
            progress_percent = int((completed / job.total_tasks) * 100)

        # Use the aggregated summary stored directly on the job object
        results_summary = job.results_summary

        # Prepare the response structure
        status_response = {
            "job": job.to_dict(), # Use the job's own serialization method
            "progress": {
                "total": job.total_tasks,
                "completed": job.completed_tasks,
                "percent": progress_percent
            },
            # Include the pre-aggregated summary from the job object
            "results_summary": results_summary,
            # Optionally include a preview of recent individual results if needed by UI
            # "results_preview": [r.to_dict() for r in self.storage.get_results(job_id)[-10:]] # Last 10 results
        }
        return status_response

# Global instance of the service
batch_service = BatchAnalysisService(job_storage)

# =============================================================================
# Route Helper Functions & Decorators
# =============================================================================

def error_handler(f):
    """Decorator for handling exceptions in Flask routes and providing user feedback."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        err_logger = create_logger_for_component('batch_routes')
        try:
            return f(*args, **kwargs)
        except Exception as e:
            err_logger.exception(f"Error in route {request.path} ({f.__name__}): {e}")
            # Check if the request expects JSON (e.g., AJAX)
            is_ajax = (
                request.headers.get("X-Requested-With") == "XMLHttpRequest" or
                "application/json" in request.accept_mimetypes
            )
            if is_ajax:
                # Return JSON error response
                return jsonify({"success": False, "error": f"An unexpected error occurred: {str(e)}"}), 500
            else:
                # Flash message and redirect for regular requests
                flash(f"An unexpected error occurred: {str(e)}", "error")
                # Redirect to the batch dashboard as a safe fallback
                return redirect(url_for('batch_analysis.batch_dashboard'))
    return decorated_function


def get_available_models() -> List[str]:
    """Retrieves the list of available AI models for selection forms."""
    # Priority 1: Use AI_MODELS from utils if available (assumed structure)
    try:
        # Assumes utils.py exists and contains AI_MODELS list/dict
        from utils import AI_MODELS
        # Adapt based on AI_MODELS structure (list of objects with .name, list of strings, etc.)
        if isinstance(AI_MODELS, list) and AI_MODELS and hasattr(AI_MODELS[0], 'name'):
            model_names = sorted([m.name for m in AI_MODELS])
            logger.debug(f"Loaded {len(model_names)} models from utils.AI_MODELS.")
            return model_names
        elif isinstance(AI_MODELS, list) and AI_MODELS and isinstance(AI_MODELS[0], str):
            model_names = sorted(AI_MODELS)
            logger.debug(f"Loaded {len(model_names)} models from utils.AI_MODELS (list of strings).")
            return model_names
        else:
            logger.warning("utils.AI_MODELS found but has unexpected structure.")
    except (ImportError, AttributeError, Exception) as e:
        logger.warning(f"Could not load AI_MODELS from utils ({e}). Falling back to directory scan.")

    # Priority 2: Fallback to scanning directories in APP_BASE_PATH
    try:
        # Use current_app if available (should be during request or app context)
        flask_app = current_app._get_current_object() if current_app else None
        if not flask_app:
            logger.error("Cannot scan directories: Flask app context not available.")
            return []
        base_path_str = flask_app.config.get('APP_BASE_PATH')
        if not base_path_str:
             logger.error("APP_BASE_PATH not found in Flask config. Cannot scan for models.")
             return []
        base_path = Path(base_path_str)

        if not base_path.is_dir():
            logger.error(f"APP_BASE_PATH '{base_path}' is not a valid directory.")
            return []

        model_names = sorted([
            item.name for item in base_path.iterdir()
            if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('_')
            # Add more specific checks if needed (e.g., presence of a marker file)
        ])
        logger.debug(f"Found {len(model_names)} potential models by scanning {base_path}.")
        return model_names
    except Exception as e:
        logger.error(f"Failed to list models from directory scan: {e}")
        return []


def parse_app_range(range_str: str) -> List[int]:
    """
    Parses a comma-separated string of numbers and ranges (e.g., "1-3,5,8")
    into a sorted list of unique integers. Returns empty list for empty/invalid input.
    """
    app_nums: Set[int] = set()
    # Handle None or empty string gracefully
    if not range_str or not range_str.strip():
        return []

    for part in range_str.split(','):
        part = part.strip()
        if not part: continue
        if '-' in part:
            # Handle ranges like "1-5"
            try:
                start_str, end_str = part.split('-', 1)
                start = int(start_str.strip())
                end = int(end_str.strip())
                if start <= end:
                    # Add all numbers in the range (inclusive)
                    app_nums.update(range(start, end + 1))
                else:
                    # Log warning for invalid range order (e.g., "5-1")
                    logger.warning(f"Invalid range order in '{part}', end must be >= start. Skipping.")
            except ValueError:
                # Log warning for invalid range format (e.g., "1-abc")
                logger.warning(f"Invalid range format '{part}', expected N-M. Skipping.")
        else:
            # Handle single numbers
            try:
                app_nums.add(int(part))
            except ValueError:
                # Log warning for invalid number format (e.g., "abc")
                logger.warning(f"Invalid app number '{part}', expected integer. Skipping.")

    # Return sorted list of unique app numbers
    return sorted(list(app_nums))


# =============================================================================
# Flask Routes
# =============================================================================

@batch_analysis_bp.route("/")
@error_handler
def batch_dashboard():
    """Displays the main dashboard for batch analysis jobs."""
    # --- START DEBUG LOGGING ---
    route_logger.info("Entered batch_dashboard route.") # Use route_logger
    try:
        route_logger.debug("Attempting to get jobs from storage...")
        jobs = sorted(job_storage.get_all_jobs(), key=lambda j: j.created_at, reverse=True)
        route_logger.debug(f"Retrieved {len(jobs)} jobs.")

        route_logger.debug("Attempting to get available models...")
        all_models = get_available_models()
        route_logger.debug(f"Retrieved {len(all_models)} models.")

        # Calculate overall stats
        stats = {status.value: 0 for status in JobStatus} # Initialize all statuses to 0
        for job in jobs:
            stats[job.status.value] += 1
        route_logger.debug(f"Calculated stats: {stats}")

    except Exception as e:
        route_logger.exception("Error during data retrieval in batch_dashboard route!")
        # Re-raise the exception to be caught by the error_handler decorator
        raise e
    # --- END DEBUG LOGGING ---

    route_logger.info("Rendering batch_dashboard.html template.")
    return render_template(
        "batch_dashboard.html", # Assumes template exists in 'templates' folder
        jobs=jobs,
        all_models=all_models,
        stats=stats,
        # Pass JobStatus and AnalysisType enums for use in template logic
        JobStatus=JobStatus,
        AnalysisType=AnalysisType
    )


@batch_analysis_bp.route("/create", methods=["GET", "POST"])
@error_handler
def create_batch_job():
    """Handles the creation of a new batch analysis job via a form."""
    route_logger.info(f"Received {request.method} request for /create") # Use route_logger
    all_models = get_available_models()
    # Pass AnalysisType enum to template for checkboxes/options
    analysis_types_available = list(AnalysisType)

    if request.method == "POST":
        route_logger.info("Processing POST request to create batch job.")
        # --- Form Data Parsing ---
        selected_models = request.form.getlist("models")
        if not selected_models:
            flash("Please select at least one model to analyze.", "warning")
            route_logger.warning("Job creation failed: No models selected.")
            return render_template("create_batch_job.html", models=all_models, analysis_types=analysis_types_available), 400 # Bad Request

        # Get selected analysis types from checkboxes
        selected_analysis_types = []
        for at_enum in analysis_types_available:
            if request.form.get(f"analysis_type_{at_enum.value}") == "on":
                selected_analysis_types.append(at_enum)

        if not selected_analysis_types:
            flash("Please select at least one analysis type to run.", "warning")
            route_logger.warning("Job creation failed: No analysis types selected.")
            return render_template("create_batch_job.html", models=all_models, analysis_types=analysis_types_available), 400

        # Parse app ranges for each selected model
        app_ranges_parsed = {}
        for model in selected_models:
            range_input = request.form.get(f"app_range_{model}", "")
            # parse_app_range returns [] for empty string, correctly interpreted as "all apps"
            app_ranges_parsed[model] = parse_app_range(range_input)
            route_logger.debug(f"Parsed app range for {model}: {app_ranges_parsed[model]}")

        # --- Collect Analysis Options ---
        analysis_options = {}
        # Security Options (shared for FE/BE for now)
        sec_full_scan = request.form.get("security_full_scan") == "on"
        analysis_options[AnalysisType.FRONTEND_SECURITY.value] = {"full_scan": sec_full_scan}
        analysis_options[AnalysisType.BACKEND_SECURITY.value] = {"full_scan": sec_full_scan}
        route_logger.debug(f"Security option full_scan: {sec_full_scan}")
        # Performance Options
        analysis_options[AnalysisType.PERFORMANCE.value] = {
            "users": int(request.form.get("perf_users", 10)),
            "duration": int(request.form.get("perf_duration", 30)),
            "spawn_rate": int(request.form.get("perf_spawn_rate", 1)),
            "endpoints": [{"path": "/", "method": "GET"}] # Default for now
        }
        route_logger.debug(f"Performance options: {analysis_options[AnalysisType.PERFORMANCE.value]}")
        # GPT4All Options
        analysis_options[AnalysisType.GPT4ALL.value] = { "requirements": None } # Load defaults in service
        # ZAP Options
        zap_quick_scan = request.form.get("zap_quick_scan") == "on"
        analysis_options[AnalysisType.ZAP.value] = { "quick_scan": zap_quick_scan }
        route_logger.debug(f"ZAP option quick_scan: {zap_quick_scan}")


        job_data = {
            "name": request.form.get("name", f"Batch Scan - {datetime.now():%Y-%m-%d %H:%M}"),
            "description": request.form.get("description", ""),
            "models": selected_models,
            "app_ranges": app_ranges_parsed,
            "analysis_types": selected_analysis_types, # Pass the list of enums
            "analysis_options": analysis_options # Pass collected options
        }
        route_logger.debug(f"Prepared job data: {job_data}")

        # --- Job Creation and Start ---
        try:
            # Pass current_app for context needed in _calculate_total_tasks
            job = job_storage.create_job(job_data, current_app._get_current_object())
            route_logger.info(f"Job {job.id} created in storage.")
            success = batch_service.start_job(job.id)

            if success:
                flash(f"Batch job '{job.name}' (ID: {job.id}) created and started successfully.", "success")
                route_logger.info(f"Job {job.id} started successfully.")
            else:
                flash(f"Batch job '{job.name}' (ID: {job.id}) created but could not be started (queue full or error). Check logs.", "warning")
                route_logger.warning(f"Job {job.id} could not be started.")

            # Redirect to the newly created job's detail page
            return redirect(url_for("batch_analysis.view_job", job_id=job.id))
        except ValueError as ve: # Catch errors from create_job (e.g., no valid analysis types)
            flash(f"Error creating job: {ve}", "error")
            route_logger.error(f"ValueError during job creation: {ve}")
            return render_template("create_batch_job.html", models=all_models, analysis_types=analysis_types_available), 400
        except Exception as e: # Catch unexpected errors
             flash(f"An unexpected error occurred during job creation: {e}", "error")
             route_logger.exception("Error during batch job creation:")
             return render_template("create_batch_job.html", models=all_models, analysis_types=analysis_types_available), 500


    # --- GET Request ---
    route_logger.info("Displaying create batch job form.")
    # Generate default job name with timestamp for the form
    default_job_name = f"Batch Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    return render_template(
        "create_batch_job.html", # Assumes template exists
        models=all_models,
        analysis_types=analysis_types_available, # Pass enum list to template
        default_job_name=default_job_name # Pass default name
    )


@batch_analysis_bp.route("/job/<int:job_id>")
@error_handler
def view_job(job_id: int):
    """Displays the detailed view for a specific batch job."""
    route_logger.info(f"Viewing job details for job ID: {job_id}")
    job_status_data = batch_service.get_job_status(job_id)

    if "error" in job_status_data:
        flash(job_status_data["error"], "error")
        route_logger.warning(f"Job {job_id} not found when trying to view.")
        return redirect(url_for("batch_analysis.batch_dashboard"))

    # Fetch individual results for display in the template
    results = sorted(
        job_storage.get_results(job_id),
        # Sort by model, app_num, then analysis type value
        key=lambda r: (r.model, r.app_num, r.analysis_type.value)
    )
    route_logger.debug(f"Found {len(results)} results for job {job_id}.")

    # Add datetime helper to context for template formatting
    # from datetime import datetime as dt # No longer needed, passed from init

    return render_template(
        "view_job.html", # Assumes template exists
        job=job_status_data['job'], # The job data dict
        status_data=job_status_data, # The full status object including summaries
        results=results, # Pass individual results
        JobStatus=JobStatus, # Pass enums for template checks
        AnalysisType=AnalysisType,
        # now=dt.utcnow # No longer needed, passed from init
    )


@batch_analysis_bp.route("/job/<int:job_id>/status")
@error_handler
def get_job_status_api(job_id: int):
    """API endpoint to get the status of a batch job (for AJAX updates)."""
    route_logger.debug(f"API request for status of job ID: {job_id}")
    status_data = batch_service.get_job_status(job_id)
    if "error" in status_data:
        route_logger.warning(f"Job {job_id} not found for API status request.")
        return jsonify(status_data), 404 # Not Found
    return jsonify(status_data)


@batch_analysis_bp.route("/job/<int:job_id>/cancel", methods=["POST"])
@error_handler
def cancel_job_api(job_id: int):
    """API endpoint or form target to cancel a running job."""
    route_logger.info(f"Received request to cancel job ID: {job_id}")
    success = batch_service.cancel_job(job_id)
    is_ajax = (
        request.headers.get("X-Requested-With") == "XMLHttpRequest" or
        "application/json" in request.accept_mimetypes
    )

    if is_ajax:
        if success:
            route_logger.info(f"Job {job_id} marked for cancellation (API).")
            return jsonify({"message": "Job marked for cancellation.", "status": JobStatus.CANCELED.value})
        else:
            job = job_storage.get_job(job_id)
            reason = "Job not found."
            if job:
                reason = f"Job is not running (status: {job.status.value})." if job.status != JobStatus.RUNNING else "Cancellation request failed."
            route_logger.warning(f"Failed to cancel job {job_id} (API): {reason}")
            return jsonify({"success": False, "error": reason}), 400 # Bad Request
    else:
        # Handle standard form submission
        if success:
            flash(f"Job {job_id} marked for cancellation.", "info")
            route_logger.info(f"Job {job_id} marked for cancellation (Form).")
        else:
            flash(f"Failed to cancel job {job_id}. It might have already finished or encountered an error.", "error")
            route_logger.warning(f"Failed to cancel job {job_id} (Form).")
        # Redirect back to the job view page
        return redirect(url_for("batch_analysis.view_job", job_id=job_id))


@batch_analysis_bp.route("/job/<int:job_id>/delete", methods=["POST"])
@error_handler
def delete_job_api(job_id: int):
    """API endpoint or form target to delete a job."""
    route_logger.info(f"Received request to delete job ID: {job_id}")
    job = job_storage.get_job(job_id)
    if not job:
        flash(f"Job {job_id} not found.", "error")
        route_logger.warning(f"Attempted to delete non-existent job {job_id}.")
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": False, "error": "Job not found"}), 404
        else:
            return redirect(url_for("batch_analysis.batch_dashboard"))

    # Prevent deleting jobs that are currently running
    if job.status == JobStatus.RUNNING:
        error_msg = f"Cannot delete running job {job_id}. Please cancel it first."
        flash(error_msg, "warning")
        route_logger.warning(f"Attempted to delete running job {job_id}.")
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": False, "error": error_msg}), 400 # Bad Request
        else:
            return redirect(url_for("batch_analysis.view_job", job_id=job_id))

    # Attempt deletion
    success = job_storage.delete_job(job_id)
    is_ajax = (
        request.headers.get("X-Requested-With") == "XMLHttpRequest" or
        "application/json" in request.accept_mimetypes
    )

    if is_ajax:
        if success:
            route_logger.info(f"Deleted job {job_id} (API).")
            return jsonify({"success": True, "message": f"Job {job_id} deleted."})
        else:
            route_logger.error(f"Failed to delete job {job_id} (API).")
            return jsonify({"success": False, "error": f"Failed to delete job {job_id}."}), 500 # Internal Server Error
    else:
        # Handle standard form submission
        if success:
            flash(f"Job {job_id} and its results deleted successfully.", "success")
            route_logger.info(f"Deleted job {job_id} (Form).")
        else:
            flash(f"Failed to delete job {job_id}.", "error")
            route_logger.error(f"Failed to delete job {job_id} (Form).")
        # Redirect to the dashboard after deletion
        return redirect(url_for("batch_analysis.batch_dashboard"))


@batch_analysis_bp.route("/job/<int:job_id>/results")
@error_handler
def get_job_results_api(job_id: int):
    """API endpoint to retrieve all results for a specific job."""
    route_logger.debug(f"API request for results of job ID: {job_id}")
    # Check if job exists first
    job = job_storage.get_job(job_id)
    if not job:
        route_logger.warning(f"Job {job_id} not found for API results request.")
        return jsonify({"error": f"Job {job_id} not found"}), 404

    results = job_storage.get_results(job_id)
    # Serialize results using their to_dict method
    return jsonify({
        "job_id": job_id,
        "results": [r.to_dict() for r in results]
    })


@batch_analysis_bp.route("/result/<int:result_id>")
@error_handler
def view_result(result_id: int):
    """Displays the detailed view for a single analysis result."""
    route_logger.info(f"Viewing result details for result ID: {result_id}")
    result = job_storage.get_result(result_id)
    if not result:
        flash(f"Result {result_id} not found.", "error")
        route_logger.warning(f"Result {result_id} not found when trying to view.")
        return redirect(url_for("batch_analysis.batch_dashboard"))

    job = job_storage.get_job(result.job_id) # Get parent job info for context
    if not job:
         # Handle case where job might have been deleted but result lingers?
         flash(f"Parent job (ID: {result.job_id}) for result {result_id} not found.", "error")
         route_logger.error(f"Parent job {result.job_id} not found for result {result_id}.")
         return redirect(url_for("batch_analysis.batch_dashboard"))


    # Prepare details for the template
    result_details = result.details

    # Add datetime helper to context - No longer needed, added globally in init
    # from datetime import datetime as dt

    # Pass AnalysisType enum for conditional rendering
    return render_template(
        "view_result.html", # Assumes template exists
        result=result,
        job=job,
        details=result_details, # Pass the details dict
        AnalysisType=AnalysisType, # Pass the enum itself
        humanize_duration=humanize_duration, # Pass helper function
        # now=dt.utcnow # No longer needed
    )


@batch_analysis_bp.route("/result/<int:result_id>/data")
@error_handler
def get_result_data_api(result_id: int):
    """API endpoint to get the raw data for a specific result."""
    route_logger.debug(f"API request for data of result ID: {result_id}")
    result = job_storage.get_result(result_id)
    if not result:
        route_logger.warning(f"Result {result_id} not found for API data request.")
        return jsonify({"error": "Result not found"}), 404
    # Return the full result object serialized using its method
    return jsonify(result.to_dict())


# =============================================================================
# Module Initialization Function (Called from App Factory)
# =============================================================================

def init_batch_analysis(app: flask.Flask):
    """
    Initializes the batch analysis module: sets up configuration and registers
    the service with the Flask app. Does NOT register the blueprint here.

    Args:
        app: The Flask application instance.
    """
    logger.info("Initializing Batch Analysis Module...")

    # --- Configuration Setup ---
    # Ensure APP_BASE_PATH is set in the main app config, used by analyzers/service
    if 'APP_BASE_PATH' not in app.config:
        # Attempt to derive from app.root_path or BASE_DIR if available
        default_path = Path(app.config.get('BASE_DIR', Path(app.root_path).parent))
        app.config['APP_BASE_PATH'] = default_path
        logger.warning(f"APP_BASE_PATH not explicitly configured. Using default: {app.config['APP_BASE_PATH']}")
    else:
        # Ensure it's a Path object
        app.config['APP_BASE_PATH'] = Path(app.config['APP_BASE_PATH'])
        logger.info(f"APP_BASE_PATH configured to: {app.config['APP_BASE_PATH']}")

    # --- Service Initialization ---
    batch_service.set_app(app)

    # --- Jinja Helper ---
    # Add humanize_duration filter to Jinja environment
    app.jinja_env.globals.update(humanize_duration=humanize_duration)
    # *** REMOVED datetime and now from globals ***
    # app.jinja_env.globals.update(datetime=datetime)
    # app.jinja_env.globals.update(now=datetime.utcnow)
    app.jinja_env.globals.update(AnalysisType=AnalysisType) # Pass Enum to templates
    app.jinja_env.globals.update(JobStatus=JobStatus) # Pass Enum to templates


    # --- Analyzer/Tester Check (Log warnings if dependencies are missing) ---
    required_services = {
        'frontend_security_analyzer': FrontendSecurityAnalyzer,
        'backend_security_analyzer': BackendSecurityAnalyzer,
        'performance_tester': LocustPerformanceTester,
        'gpt4all_analyzer': GPT4AllAnalyzer,
        'scan_manager': ScanManager, # For ZAP triggering
        'port_manager': PortManager # For performance tests
        # ZAPScanner instance itself might not need to be directly on app context
        # if triggering happens via ScanManager/routes.
    }
    for attr_name, class_ref in required_services.items():
        if class_ref is None: # Check if the class failed to import
             logger.error(f"Class for '{attr_name}' could not be imported. Batch analysis for this type will fail.")
        elif not hasattr(app, attr_name):
             logger.error(f"Flask app context is missing '{attr_name}'. Batch analysis for related types will fail.")


    # --- Template Check (Optional) ---
    templates_dir = Path(__file__).parent / batch_analysis_bp.template_folder # Path relative to this file
    required_templates = [
        "batch_dashboard.html", "create_batch_job.html",
        "view_job.html", "view_result.html"
    ]
    for template_name in required_templates:
        if not (templates_dir / template_name).is_file():
            logger.warning(f"Batch analysis template not found: {templates_dir / template_name}")

    # --- IMPORTANT: Blueprint Registration REMOVED ---
    # The blueprint (batch_analysis_bp) should be registered in the main app factory (create_app)

    logger.info("Batch Analysis Module initialized (Blueprint registration expected in app factory).")

# --- Helper Functions ---
def humanize_duration(seconds: Optional[Union[int, float]]) -> str:
    """Converts seconds into a human-readable string (Xs, Xm Ys, Xh Ym)."""
    if seconds is None or seconds < 0:
        return "N/A"
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    if minutes < 60:
        return f"{minutes}m {remaining_seconds}s"
    hours = minutes // 60
    remaining_minutes = minutes % 60
    return f"{hours}h {remaining_minutes}m"


# --- Potential Future Enhancements ---
# TODO: Implement persistent storage for jobs/results (e.g., database, files) instead of in-memory.
# TODO: Add a job queue mechanism for handling more jobs than max_concurrent_jobs.
# TODO: Centralize path generation logic (e.g., using path_utils.py or a shared function).
# TODO: Enhance UI feedback during job creation/execution (e.g., websockets for real-time progress).
# TODO: Refine ZAP integration to monitor scan status after triggering.
# TODO: Add configuration options for each analysis type in the UI form.

