"""
Batch Security Analysis Module - Core Logic

This module provides the core data models, storage, and service logic
for running batch security analysis on both frontend and backend code
across multiple applications or models. It offers a robust job management
system. Routing and Flask integration are handled elsewhere.
"""

# Standard Library Imports
import json
import os
import threading
import time
import traceback # Added for detailed exception logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set, Union

# Create logger
# Assume logging_service is available in the project structure
try:
    from logging_service import create_logger_for_component
    logger = create_logger_for_component('batch_analysis_core') # Renamed logger component
except ImportError:
    import logging
    logger = logging.getLogger('batch_analysis_core')
    # Add basic handler if logger has none
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    logger.warning("Could not import logging_service, using basic logging.")


# =============================================================================
# Data Models
# =============================================================================

class JobStatus(str, Enum):
    """Job status enum for batch analysis jobs"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class ScanType(str, Enum):
    """Scan type enum for batch analysis jobs"""
    FRONTEND = "frontend"
    BACKEND = "backend"
    BOTH = "both"


@dataclass
class BatchAnalysisJob:
    """Represents a batch analysis job"""
    id: int
    name: str
    description: str
    created_at: datetime
    status: JobStatus = JobStatus.PENDING
    models: List[str] = field(default_factory=list)
    app_ranges: Dict[str, List[int]] = field(default_factory=dict)
    scan_options: Dict[str, Any] = field(default_factory=dict)
    scan_type: ScanType = ScanType.FRONTEND
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    results: List[Dict[str, Any]] = field(default_factory=list) # Changed to List for better structure
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        # Convert datetime objects to ISO format strings
        for key in ['created_at', 'started_at', 'completed_at']:
            if result[key] is not None:
                result[key] = result[key].isoformat()
        # Ensure enums are strings
        result['status'] = str(self.status.value)
        result['scan_type'] = str(self.scan_type.value)
        return result


@dataclass
class BatchAnalysisResult:
    """Represents a single analysis result within a batch job"""
    id: int
    job_id: int
    model: str
    app_num: int
    status: str # 'completed' or 'failed'
    scan_type: ScanType
    issues_count: int = 0
    high_severity: int = 0
    medium_severity: int = 0
    low_severity: int = 0
    scan_time: Optional[datetime] = None
    details: Dict[str, Any] = field(default_factory=dict) # Includes 'issues', 'summary', 'tool_status', 'error'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        if result['scan_time'] is not None:
            result['scan_time'] = result['scan_time'].isoformat()
        result['scan_type'] = str(self.scan_type.value)
        return result


# =============================================================================
# In-memory Storage (Consider replacing with a persistent store for production)
# =============================================================================
class JobStorage:
    """Storage for batch analysis jobs and results"""
    def __init__(self):
        self.jobs: Dict[int, BatchAnalysisJob] = {}
        # Store results separately, linking by job_id
        self.results: Dict[int, List[BatchAnalysisResult]] = {}
        self.next_job_id = 1
        self.next_result_id = 1
        self._lock = threading.RLock() # Use RLock for reentrant access

    def create_job(self, job_data: Dict[str, Any]) -> BatchAnalysisJob:
        """Create a new batch analysis job"""
        with self._lock:
            job_id = self.next_job_id
            self.next_job_id += 1

            # Create job with provided data, ensuring ScanType is correctly instantiated
            scan_type_input = job_data.get('scan_type', ScanType.FRONTEND)
            if isinstance(scan_type_input, str):
                try:
                    scan_type = ScanType(scan_type_input)
                except ValueError:
                    logger.warning(f"Invalid scan_type string '{scan_type_input}', defaulting to FRONTEND.")
                    scan_type = ScanType.FRONTEND
            elif isinstance(scan_type_input, ScanType):
                scan_type = scan_type_input
            else:
                logger.warning(f"Invalid scan_type type '{type(scan_type_input)}', defaulting to FRONTEND.")
                scan_type = ScanType.FRONTEND

            job = BatchAnalysisJob(
                id=job_id,
                name=job_data.get('name', f'Batch Job {job_id}'),
                description=job_data.get('description', ''),
                created_at=datetime.now(),
                models=job_data.get('models', []),
                app_ranges=job_data.get('app_ranges', {}),
                scan_options=job_data.get('scan_options', {}),
                scan_type=scan_type, # Use validated enum
            )

            # Calculate total tasks based on scan type
            # Note: This is an initial estimate, might be updated when job runs if ranges are dynamic
            total_tasks = self._calculate_total_tasks(job)
            job.total_tasks = total_tasks

            # Store job and initialize results list
            self.jobs[job_id] = job
            self.results[job_id] = [] # Initialize results list for this job

            logger.info(f"Created new job {job_id}: {job.name} with estimated {total_tasks} tasks")
            return job

    def _calculate_total_tasks(self, job: BatchAnalysisJob) -> int:
        """Calculate the *estimated* total number of tasks for a job"""
        total_tasks = 0

        for model in job.models:
            app_range = job.app_ranges.get(model, [])
            app_count = len(app_range)

            # If empty range means 'all apps', we can't know the count yet
            if not app_range and model in job.app_ranges:
                # Placeholder - actual count determined when job runs
                # Return -1 to indicate dynamic task count? Or estimate?
                # For now, let's estimate 10, but log a warning.
                app_count = 10 # Placeholder estimate
                logger.warning(f"Job {job.id} uses dynamic app range for model '{model}'. Task count is an estimate.")

            # For BOTH scan type, we count each app twice (frontend + backend)
            if job.scan_type == ScanType.BOTH:
                app_count *= 2

            total_tasks += app_count

        return total_tasks

    def get_job(self, job_id: int) -> Optional[BatchAnalysisJob]:
        """Get a job by ID"""
        with self._lock:
            return self.jobs.get(job_id)

    def get_all_jobs(self) -> List[BatchAnalysisJob]:
        """Get all jobs"""
        with self._lock:
            return list(self.jobs.values())

    def update_job(self, job_id: int, **kwargs) -> Optional[BatchAnalysisJob]:
        """Update a job with the provided attributes"""
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                logger.warning(f"Attempted to update non-existent job: {job_id}")
                return None

            updated = False
            for key, value in kwargs.items():
                if hasattr(job, key):
                    # Special handling for enums
                    if key == 'status' and isinstance(value, str):
                        try:
                            setattr(job, key, JobStatus(value))
                            updated = True
                        except ValueError:
                            logger.warning(f"Attempted to set invalid status '{value}' on job {job_id}")
                    elif key == 'scan_type' and isinstance(value, str):
                        try:
                            setattr(job, key, ScanType(value))
                            updated = True
                        except ValueError:
                             logger.warning(f"Attempted to set invalid scan_type '{value}' on job {job_id}")
                    # Handle appending to errors list
                    elif key == 'errors' and isinstance(value, list):
                        job.errors.extend(value) # Append new errors
                        updated = True
                    elif getattr(job, key) != value:
                        setattr(job, key, value)
                        updated = True
                else:
                    logger.warning(f"Attempted to set unknown attribute '{key}' on job {job_id}")

            if updated:
                logger.debug(f"Updated job {job_id} with: {kwargs}")

            return job

    def add_result(self, job_id: int, result_data: Dict[str, Any]) -> Optional[BatchAnalysisResult]:
        """Add a result to a job"""
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                logger.error(f"Attempted to add result to non-existent job: {job_id}")
                return None # Changed from raising ValueError

            result_id = self.next_result_id
            self.next_result_id += 1

            # Create result with provided data
            result = BatchAnalysisResult(
                id=result_id,
                job_id=job_id,
                model=result_data.get('model', ''),
                app_num=result_data.get('app_num', 0),
                status=result_data.get('status', 'completed'),
                # Ensure ScanType is correctly instantiated
                scan_type=ScanType(result_data.get('scan_type', ScanType.FRONTEND)),
                issues_count=result_data.get('issues_count', 0),
                high_severity=result_data.get('high_severity', 0),
                medium_severity=result_data.get('medium_severity', 0),
                low_severity=result_data.get('low_severity', 0),
                scan_time=result_data.get('scan_time', datetime.now()),
                details=result_data.get('details', {})
            )

            # Add to results list for the specific job
            if job_id not in self.results:
                self.results[job_id] = []
            self.results[job_id].append(result)
            logger.debug(f"Added result {result_id} to job {job_id}")

            # --- Update job completion stats ---
            # Increment completed tasks atomically within the lock
            job.completed_tasks += 1
            logger.debug(f"Job {job_id} task progress: {job.completed_tasks}/{job.total_tasks}")

            # Check if job is now complete
            # Only mark complete if currently RUNNING to avoid race conditions with cancellation
            if job.status == JobStatus.RUNNING and job.total_tasks > 0 and job.completed_tasks >= job.total_tasks:
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now()
                logger.info(f"Job {job_id} ({job.name}) completed with {job.completed_tasks} tasks at {job.completed_at}")
            # --- End job completion update ---

            return result

    def get_results(self, job_id: int) -> List[BatchAnalysisResult]:
        """Get all results for a job"""
        with self._lock:
            # Return a copy to prevent modification outside the lock
            return list(self.results.get(job_id, []))

    def get_result(self, result_id: int) -> Optional[BatchAnalysisResult]:
        """Get a specific result by ID"""
        with self._lock:
            for results_list in self.results.values():
                for result in results_list:
                    if result.id == result_id:
                        return result # No need to copy single immutable dataclass
            return None

    def delete_job(self, job_id: int) -> bool:
        """Delete a job and all its results"""
        with self._lock:
            if job_id in self.jobs:
                del self.jobs[job_id]
                if job_id in self.results:
                    del self.results[job_id]
                logger.info(f"Deleted job {job_id}")
                return True
            logger.warning(f"Attempted to delete non-existent job: {job_id}")
            return False


# Create global storage instance
job_storage = JobStorage()


# =============================================================================
# Batch Analysis Service
# =============================================================================
class BatchAnalysisService:
    """Service for executing batch analysis jobs"""

    def __init__(self, storage: JobStorage):
        """
        Initialize the batch analysis service

        Args:
            storage: Job storage instance for managing jobs and results
        """
        self.storage = storage
        self._running_jobs: Dict[int, threading.Thread] = {}
        # Use a dictionary for cancel flags to potentially store reason/time
        self._cancel_requests: Dict[int, bool] = {}
        # Use ThreadPoolExecutor for managing task execution within a job
        # Initialize with a default, will be reconfigured by set_app
        self.thread_pool = ThreadPoolExecutor(max_workers=5, thread_name_prefix='batch_task_worker')
        self.max_concurrent_jobs = 2 # Limit concurrent *jobs*
        self.max_concurrent_tasks = 5 # Default tasks per job
        self.app = None # Flask app instance, set via set_app
        self.logger = create_logger_for_component('batch_service')

    def set_app(self, app):
        """
        Set the Flask app instance and configure concurrency settings.
        Required for accessing app context and config.

        Args:
            app: Flask application instance
        """
        self.app = app
        if self.app:
            # Get config settings safely with defaults
            self.max_concurrent_tasks = self.app.config.get('MAX_CONCURRENT_BATCH_TASKS', 5)
            self.max_concurrent_jobs = self.app.config.get('MAX_CONCURRENT_BATCH_JOBS', 2)

            # Recreate thread pool with configured size
            # Ensure graceful shutdown of old pool if already running?
            # For simplicity, we assume set_app is called only once at startup.
            if hasattr(self, 'thread_pool') and self.thread_pool:
                self.thread_pool.shutdown(wait=False) # Don't wait for current tasks

            self.thread_pool = ThreadPoolExecutor(
                max_workers=self.max_concurrent_tasks,
                thread_name_prefix='batch_task_worker'
            )
            self.logger.info(
                f"Flask app set. Max concurrent jobs: {self.max_concurrent_jobs}, "
                f"Max concurrent tasks per job: {self.max_concurrent_tasks}"
            )
        else:
             self.logger.warning("Flask app instance is not set. Analysis tasks requiring app context will fail.")

    def start_job(self, job_id: int) -> bool:
        """
        Start a batch analysis job in a background thread if concurrency limits allow.

        Args:
            job_id: ID of the job to start

        Returns:
            bool: True if job was started successfully, False otherwise
        """
        job = self.storage.get_job(job_id)
        if not job:
            self.logger.error(f"Job {job_id} not found, cannot start.")
            return False

        if job.status not in [JobStatus.PENDING, JobStatus.CANCELED, JobStatus.FAILED]: # Allow restarting failed/canceled
            self.logger.warning(f"Job {job_id} is not in a startable state (current status: {job.status})")
            return False

        with self.storage._lock: # Use storage lock to check running job count atomically
            if len(self._running_jobs) >= self.max_concurrent_jobs:
                self.logger.warning(f"Maximum concurrent jobs ({self.max_concurrent_jobs}) reached. Job {job_id} will remain pending.")
                # Optionally, add to a queue here instead of returning False
                return False

            # Update job status immediately within the lock
            self.storage.update_job(
                job_id,
                status=JobStatus.RUNNING,
                started_at=datetime.now(),
                completed_tasks=0, # Reset progress if restarting
                errors=[], # Clear previous errors
                completed_at=None # Clear completion time
            )

            # Start job processing in a background thread
            thread = threading.Thread(
                target=self._run_job,
                args=(job_id,),
                daemon=True,
                name=f"batch-job-{job_id}"
            )
            self._running_jobs[job_id] = thread # Register before starting
            thread.start()

        self.logger.info(f"Started job {job_id} ({job.name}) in background thread {thread.name}")
        return True

    def _run_job(self, job_id: int) -> None:
        """
        Execute the tasks for a specific batch analysis job using a ThreadPoolExecutor.
        This function runs in its own background thread.

        Args:
            job_id: ID of the job to run
        """
        job = self.storage.get_job(job_id)
        if not job:
            self.logger.error(f"Job runner: Job {job_id} not found.")
            return # Should not happen if start_job is used correctly

        if not self.app:
            self.logger.error(f"Job runner: Flask app context not available for job {job_id}. Aborting.")
            self.storage.update_job(job_id, status=JobStatus.FAILED, errors=["Flask app not configured for service."])
            if job_id in self._running_jobs: del self._running_jobs[job_id] # Clean up running job entry
            return

        tasks_submitted = 0
        try:
            self.logger.info(f"Job runner starting execution for job {job_id}: {job.name}")

            # Generate task list *before* starting execution
            # Need app context if _get_all_apps_for_model (via _generate_task_list) needs it
            with self.app.app_context():
                tasks = self._generate_task_list(job)

            if not tasks:
                 self.logger.warning(f"Job {job_id} has no tasks to execute.")
                 self.storage.update_job(job_id, status=JobStatus.COMPLETED, completed_at=datetime.now(), total_tasks=0)
                 if job_id in self._running_jobs: del self._running_jobs[job_id] # Clean up running job entry
                 return

            # Update total tasks count if it was estimated or needs correction
            if len(tasks) != job.total_tasks:
                self.logger.info(f"Updating job {job_id} task count from {job.total_tasks} to {len(tasks)}")
                self.storage.update_job(job_id, total_tasks=len(tasks))
                job.total_tasks = len(tasks) # Update local copy too

            # --- Execute tasks using ThreadPoolExecutor ---
            futures = []
            task_errors = []


            # Submit tasks to the pool
            for task_args in tasks:
                # Check for cancellation before submitting each task
                if job_id in self._cancel_requests:
                    self.logger.info(f"Job {job_id} cancellation detected before submitting all tasks.")
                    break # Stop submitting new tasks

                model, app_num, scan_type_enum = task_args
                future = self.thread_pool.submit(
                    self._analyze_app, # Target function
                    job_id, model, app_num, scan_type_enum, job.scan_options # Args for _analyze_app
                )
                futures.append(future)
                tasks_submitted += 1

            self.logger.info(f"Job {job_id}: Submitted {tasks_submitted} tasks to the thread pool.")

            # --- Process completed futures ---
            for future in as_completed(futures):
                 # Check for cancellation after each task completes
                 if job_id in self._cancel_requests:
                      self.logger.info(f"Job {job_id} cancellation detected while processing results.")
                      # Attempt to cancel remaining futures (best effort)
                      for f in futures:
                          if not f.done():
                              f.cancel()
                      break # Stop processing results

                 try:
                      # Check if the task raised an exception
                      future.result() # Call result() to raise exceptions from the task
                 except Exception as e:
                      # This exception originates *from within _analyze_app*
                      error_msg = f"Task failed in job {job_id}: {str(e)}"
                      self.logger.error(error_msg, exc_info=True) # Log with stack trace
                      task_errors.append(error_msg)
                      # No need to update job.errors here, _analyze_app should have recorded its failure

            # --- Final Job Status Update ---
            # Acquire lock to safely update final job state
            with self.storage._lock:
                # Refresh job object to get the latest state (completed_tasks count)
                job = self.storage.get_job(job_id)
                if not job: return # Job might have been deleted externally

                final_status = job.status # Keep current status unless changed below

                if job_id in self._cancel_requests:
                    final_status = JobStatus.CANCELED
                    self.logger.info(f"Job {job_id} finished with status: CANCELED")
                elif task_errors:
                     final_status = JobStatus.FAILED # Mark as failed if any task had errors
                     # Append task-level errors to job errors
                     self.storage.update_job(job_id, errors=task_errors)
                     self.logger.warning(f"Job {job_id} finished with status: FAILED due to {len(task_errors)} task errors.")
                elif job.status == JobStatus.RUNNING: # If still running and no errors/cancellation
                     # This case handles jobs where total_tasks might be 0 or completion logic failed
                     # If all submitted tasks completed without error, mark as COMPLETED.
                     # Check if completed_tasks matches tasks_submitted (as total_tasks might be inaccurate)
                     # Ensure total_tasks > 0 before checking completion based on it
                     if job.total_tasks > 0 and job.completed_tasks >= job.total_tasks:
                         final_status = JobStatus.COMPLETED
                         # job.completed_at = datetime.now() # Already set by add_result
                         self.logger.info(f"Job {job_id} marked complete based on task count.")
                     elif job.total_tasks == 0 and tasks_submitted == 0: # No tasks were generated/submitted
                          final_status = JobStatus.COMPLETED
                          job.completed_at = datetime.now()
                          self.logger.info(f"Job {job_id} marked complete as no tasks were generated.")
                     elif tasks_submitted > 0 and job.completed_tasks >= tasks_submitted:
                          # Fallback check if total_tasks was dynamic/inaccurate
                          final_status = JobStatus.COMPLETED
                          job.completed_at = datetime.now()
                          self.logger.info(f"Job {job_id} marked complete based on submitted tasks ({tasks_submitted}).")

                     else:
                         # Should not normally happen if task completion logic is correct
                         final_status = JobStatus.FAILED
                         self.logger.error(f"Job {job_id} ended unexpectedly. Status: {job.status}, Tasks completed: {job.completed_tasks}, Submitted: {tasks_submitted}, Total Est: {job.total_tasks}. Marking as FAILED.")
                         self.storage.update_job(job_id, errors=["Job ended unexpectedly before all tasks completed."])


                # Apply final status update
                job.status = final_status
                if job.completed_at is None and final_status != JobStatus.RUNNING:
                     job.completed_at = datetime.now() # Set completion time if not already set

        except Exception as e:
            # Catch errors during task generation or submission phase
            self.logger.exception(f"Critical error running job {job_id}: {e}")
            self.storage.update_job(job_id, status=JobStatus.FAILED, errors=[f"Job execution error: {str(e)}"])
        finally:
            # --- Cleanup ---
            # Remove from running jobs list
            if job_id in self._running_jobs:
                del self._running_jobs[job_id]
            # Remove from cancel requests
            if job_id in self._cancel_requests:
                del self._cancel_requests[job_id]
            self.logger.info(f"Job runner finished for job {job_id}. Final status: {job.status if job else 'Unknown'}")
            # Check if other jobs are pending and start one if possible
            self._check_and_start_pending_jobs()


    def _generate_task_list(self, job: BatchAnalysisJob) -> List[Tuple[str, int, ScanType]]:
        """
        Generate the list of analysis tasks based on job configuration.
        Handles dynamic app ranges ('all apps'). Requires app context.

        Args:
            job: Batch analysis job

        Returns:
            List of tasks to execute, each as (model, app_num, scan_type_enum)

        Raises:
            RuntimeError: If app context is required but not available.
        """
        if not self.app:
             raise RuntimeError("Flask app context needed for _generate_task_list but not available.")

        tasks = []
        utils_available = False
        try:
            from utils import get_apps_for_model # Try importing needed utility
            utils_available = True
        except ImportError:
             self.logger.warning("Cannot import 'get_apps_for_model' from utils. Dynamic app ranges will be skipped.")

        for model in job.models:
            app_range_config = job.app_ranges.get(model) # Could be list or None

            apps_to_scan = []
            # If app_range_config is explicitly an empty list, it means "all apps"
            if isinstance(app_range_config, list) and not app_range_config:
                if utils_available:
                    try:
                        # Use the utility function to get all app numbers
                        # Ensure we are in an app context as get_apps_for_model might need it
                        # The caller (_run_job) ensures this context.
                        apps_data = get_apps_for_model(model)
                        apps_to_scan = [app_data["app_num"] for app_data in apps_data]
                        self.logger.info(f"Dynamically found {len(apps_to_scan)} apps for model '{model}'")
                    except Exception as e:
                        self.logger.error(f"Failed to get dynamic app list for model '{model}': {e}. Skipping model.")
                        job.errors.append(f"Failed to get apps for model '{model}': {e}")
                        continue # Skip this model if dynamic lookup fails
                else:
                    self.logger.error(f"Cannot process 'all apps' for model '{model}' because 'get_apps_for_model' utility is unavailable.")
                    job.errors.append(f"Cannot get app list for model '{model}'.")
                    continue # Skip this model
            elif isinstance(app_range_config, list):
                # Specific list of apps provided
                apps_to_scan = app_range_config
            else:
                # app_ranges[model] was not set or was None/invalid
                self.logger.warning(f"No valid app range specified for model '{model}' in job {job.id}. Skipping.")
                continue # Skip this model

            # Generate tasks for each app based on scan type
            for app_num in apps_to_scan:
                if not isinstance(app_num, int) or app_num <= 0:
                    self.logger.warning(f"Skipping invalid app number '{app_num}' for model '{model}'.")
                    continue

                if job.scan_type == ScanType.FRONTEND or job.scan_type == ScanType.BOTH:
                    tasks.append((model, app_num, ScanType.FRONTEND))
                if job.scan_type == ScanType.BACKEND or job.scan_type == ScanType.BOTH:
                    tasks.append((model, app_num, ScanType.BACKEND))

        return tasks


    def _analyze_app(self, job_id: int, model: str, app_num: int, scan_type_enum: ScanType, scan_options: Dict[str, Any]) -> None:
        """
        Run security analysis for a single app within the job's ThreadPoolExecutor.
        Handles app context and records results or errors.

        Args:
            job_id: ID of the parent job
            model: Model name
            app_num: App number
            scan_type_enum: Type of scan to perform (ScanType.FRONTEND or ScanType.BACKEND)
            scan_options: Scan options from the job
        """
        # Need access to current_app from Flask
        from flask import current_app

        task_logger = create_logger_for_component(f'batch_task.{model}-{app_num}.{scan_type_enum.value}')
        task_start_time = datetime.now()
        task_logger.info(f"Starting analysis task (Job: {job_id})")

        result_data = {
            "model": model,
            "app_num": app_num,
            "scan_type": scan_type_enum, # Store the enum member
            "status": "failed", # Default to failed
            "scan_time": task_start_time,
            "details": {}
        }

        # Check for cancellation before starting analysis
        if job_id in self._cancel_requests:
            task_logger.info(f"Task skipped - job {job_id} was canceled.")
            # No result is recorded for canceled tasks
            return # Exit the task function

        if not self.app:
            task_logger.error("Task cannot run: Flask app context is not available.")
            result_data["details"]["error"] = "Flask app context unavailable"
            self.storage.add_result(job_id, result_data)
            return

        try:
            # --- Execute Analysis within App Context ---
            with self.app.app_context():
                task_logger.debug("App context acquired.")
                full_scan = scan_options.get("full_scan", False)
                analyzer = None
                issues = []
                tool_status = {}
                summary = {}

                if scan_type_enum == ScanType.FRONTEND:
                    # Access analyzer from current_app within the context
                    analyzer = current_app.frontend_security_analyzer
                    task_logger.info(f"Running frontend analysis (full_scan={full_scan})")
                elif scan_type_enum == ScanType.BACKEND:
                     # Access analyzer from current_app within the context
                    analyzer = current_app.backend_security_analyzer
                    task_logger.info(f"Running backend analysis (full_scan={full_scan})")
                else:
                    # Should not happen if _generate_task_list is correct
                    raise ValueError(f"Unsupported scan type enum: {scan_type_enum}")

                if not analyzer:
                     raise RuntimeError(f"{scan_type_enum.value.capitalize()} security analyzer not available in app context.")

                # Execute the analysis
                # Ensure the method exists before calling
                if not hasattr(analyzer, 'run_security_analysis'):
                    raise NotImplementedError(f"Analyzer {type(analyzer).__name__} does not have 'run_security_analysis' method.")

                # Make the actual call to the analyzer
                task_logger.debug(f"Calling {type(analyzer).__name__}.run_security_analysis...")
                issues, tool_status, _ = analyzer.run_security_analysis(
                    model, app_num, use_all_tools=full_scan
                )
                task_logger.debug(f"Analysis method completed. Found {len(issues)} issues.")

                # Get summary from the analyzer
                if hasattr(analyzer, 'get_analysis_summary'):
                    summary = analyzer.get_analysis_summary(issues)
                    task_logger.debug("Generated analysis summary.")
                else:
                    task_logger.warning(f"Analyzer {type(analyzer).__name__} does not have 'get_analysis_summary' method.")
                    # Basic summary fallback
                    summary = {
                        "total_issues": len(issues),
                        "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0} # Placeholder counts
                    }

                # --- Prepare Successful Result ---
                result_data["status"] = "completed"
                result_data["issues_count"] = len(issues)
                result_data["high_severity"] = summary.get("severity_counts", {}).get("HIGH", 0)
                result_data["medium_severity"] = summary.get("severity_counts", {}).get("MEDIUM", 0)
                result_data["low_severity"] = summary.get("severity_counts", {}).get("LOW", 0)
                result_data["details"] = {
                    # Serialize issues carefully
                    "issues": [asdict(issue) if hasattr(issue, '__dataclass_fields__') else issue for issue in issues],
                    "summary": summary,
                    "tool_status": tool_status
                }
                task_logger.info(f"Analysis task completed successfully in {(datetime.now() - task_start_time).total_seconds():.2f}s")

        except Exception as e:
            task_logger.exception(f"Error during analysis task: {e}")
            # Prepare Failed Result
            result_data["status"] = "failed"
            result_data["details"]["error"] = str(e)
            result_data["details"]["traceback"] = traceback.format_exc() # Include traceback in details

        finally:
            # --- Record Result (Success or Failure) ---
            # Pass the original enum member back
            result_data['scan_type'] = scan_type_enum
            self.storage.add_result(job_id, result_data)
            task_logger.debug("Result recorded in storage.")


    def cancel_job(self, job_id: int) -> bool:
        """
        Request cancellation of a running job.

        Args:
            job_id: ID of the job to cancel

        Returns:
            bool: True if job was running and marked for cancellation, False otherwise
        """
        with self.storage._lock: # Ensure atomic check and update
            job = self.storage.get_job(job_id)
            if not job:
                self.logger.error(f"Cannot cancel job {job_id}: Not found.")
                return False

            if job.status != JobStatus.RUNNING:
                self.logger.warning(f"Cannot cancel job {job_id}: Not currently running (status: {job.status}).")
                return False

            # Mark for cancellation
            self._cancel_requests[job_id] = True

            # Update job status immediately to CANCELED
            # The running thread will see the flag and stop processing/clean up.
            self.storage.update_job(job_id, status=JobStatus.CANCELED)

            self.logger.info(f"Job {job_id} marked for cancellation.")
            # Note: Actual task cancellation in the thread pool is best-effort.
            # Running tasks will complete, but new ones won't be scheduled by _run_job.
            return True

    def get_job_status(self, job_id: int) -> Dict[str, Any]:
        """
        Get detailed status information for a job, including progress and results summary.

        Args:
            job_id: ID of the job

        Returns:
            Dict containing detailed job status information, or error dict.
        """
        job = self.storage.get_job(job_id)
        if not job:
            return {"error": "Job not found", "status_code": 404} # Use status_code for API

        results = self.storage.get_results(job_id) # Get results associated with the job

        # Calculate summary stats from results
        summary_stats = {
            "total_results": len(results),
            "completed_ok": sum(1 for r in results if r.status == "completed"),
            "failed": sum(1 for r in results if r.status == "failed"),
            "total_issues": sum(r.issues_count for r in results),
            "high_issues": sum(r.high_severity for r in results),
            "medium_issues": sum(r.medium_severity for r in results),
            "low_issues": sum(r.low_severity for r in results),
            "frontend": {"count": 0, "issues": 0, "high": 0, "medium": 0, "low": 0},
            "backend": {"count": 0, "issues": 0, "high": 0, "medium": 0, "low": 0},
        }

        for r in results:
            target_key = r.scan_type.value # Use enum value ('frontend' or 'backend')
            if target_key in summary_stats:
                target = summary_stats[target_key]
                target["count"] += 1
                target["issues"] += r.issues_count
                target["high"] += r.high_severity
                target["medium"] += r.medium_severity
                target["low"] += r.low_severity

        # Calculate progress percentage safely
        percent_complete = 0
        if job.total_tasks > 0:
            percent_complete = int((job.completed_tasks / job.total_tasks) * 100)
        elif job.status == JobStatus.COMPLETED: # Handle case where total_tasks might be 0 but job finished
             percent_complete = 100
        elif job.status in [JobStatus.FAILED, JobStatus.CANCELED]:
              # If failed/canceled, show progress based on completed tasks before stopping
              if job.total_tasks > 0:
                  percent_complete = int((job.completed_tasks / job.total_tasks) * 100)
              else: # If total tasks was 0 or unknown, can't show percentage
                   percent_complete = 0

        # Build comprehensive status object using job.to_dict for base structure
        status_data = job.to_dict()
        status_data["progress"] = {
            "total": job.total_tasks,
            "completed": job.completed_tasks,
            "percent": percent_complete
        }
        status_data["results_summary"] = summary_stats

        return status_data

    def _check_and_start_pending_jobs(self):
        """Checks for pending jobs and starts one if concurrency limit allows."""
        with self.storage._lock:
            if len(self._running_jobs) < self.max_concurrent_jobs:
                pending_jobs = sorted(
                    [j for j in self.storage.get_all_jobs() if j.status == JobStatus.PENDING],
                    key=lambda j: j.created_at # Start oldest pending job first
                )
                if pending_jobs:
                    job_to_start = pending_jobs[0]
                    self.logger.info(f"Auto-starting pending job {job_to_start.id} due to available capacity.")
                    # Use Thread to avoid blocking current operation
                    threading.Thread(target=self.start_job, args=(job_to_start.id,), daemon=True).start()


# Create a service instance - this should be accessible globally or via app context
batch_service = BatchAnalysisService(job_storage)


# =============================================================================
# Initialization Function (for use by app factory)
# =============================================================================
def init_batch_analysis_logic(app):
    """
    Initialize batch analysis module logic (e.g., set app context for service).
    Does NOT register the blueprint.

    Args:
        app: Flask application instance
    """
    logger.info("Initializing batch analysis core logic...")

    # Pass the Flask app to the service instance
    # Assumes batch_service is a global or module-level instance
    global batch_service
    batch_service.set_app(app)

    # Any other logic needed at app startup for this module can go here
    # For example, loading persistent job data if storage was file-based.

    logger.info("Batch analysis core logic initialized.")