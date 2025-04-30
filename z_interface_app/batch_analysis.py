# -*- coding: utf-8 -*-
"""
Batch Analysis Module (Enhanced for Reliability v6 - Claude Structure + Fixes)

Provides functionality for running batch analyses (security, performance, etc.)
across multiple applications or models, including job management and reporting.

Enhanced with:
- Task-level timeouts to prevent hangs.
- More robust error handling and state management.
- Improved cancellation logic visibility.
- Detailed logging with consistent prefixes.
- Fixes for previous known issues (AttributeError, Logging).
- v4 Fix: Correctly handles ZAP scan results retrieval.
- v5 Fix: Added pre-check for performance tasks; added logging advice.
- v6: Refined structure, improved result serialization, enhanced comments.
"""

import json
import os
import re
import shutil
import socket # Added for performance task connection check
import threading
import time
import traceback
import queue # Added for task timeout mechanism
from concurrent.futures import ThreadPoolExecutor, as_completed, Future, TimeoutError as FutureTimeoutError
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set, Union, Type
from urllib.parse import urlparse # Added for performance task connection check

import flask
from flask import (
    Blueprint, current_app, jsonify, render_template, request, url_for,
    redirect, flash
)
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError

# --- Logging Setup ---
# ==============================================================================
# CRITICAL NOTE on Logging PermissionError [WinError 32] on Windows:
# This error occurs when multiple threads/processes using RotatingFileHandler
# try to rotate the same log file concurrently.
#
# *** THE RECOMMENDED SOLUTION ***
# Implement centralized logging in your main Flask application setup using:
#   - `logging.handlers.QueueHandler`: All threads/processes put log records
#     into a queue.
#   - `logging.handlers.QueueListener`: A single, separate thread/process
#     listens to the queue and handles writing to the actual file (including
#     rotation), thus avoiding concurrency issues.
#
# This module's fallback logging uses basicConfig (StreamHandler), which avoids
# the rotation error but might not meet production needs. Modifying handlers
# *within* this module is unlikely to fix the root cause if the main app's
# logging configuration is the source of the conflict.
# ==============================================================================
try:
    # Assume logging_service provides a configured logger instance
    # If not available, basicConfig will be used as fallback below.
    from logging_service import logger as root_logger # Assuming base logger is configured
    # Create specific loggers for different parts of the module if needed
    logger = root_logger.getChild('batch_analysis') # General module logs
    storage_logger = root_logger.getChild('batch_storage') # Job/Result storage ops
    service_logger = root_logger.getChild('batch_service') # Service logic, job lifecycle
    route_logger = root_logger.getChild('batch_routes')   # Flask route handling
    task_logger = root_logger.getChild('batch_task')     # Individual task execution
    logger.info("Using logging service for batch analysis module.")
except ImportError as log_imp_err:
    # Fallback basic logging if logging_service is unavailable
    import logging
    # basicConfig typically uses StreamHandler, avoiding the rotation error
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    logger = logging.getLogger('batch_analysis')
    storage_logger = logging.getLogger('batch_storage')
    service_logger = logging.getLogger('batch_service')
    route_logger = logging.getLogger('batch_routes')
    task_logger = logging.getLogger('batch_task')
    logger.error(f"Failed to import logging_service: {log_imp_err}. Using basic fallback logging (StreamHandler).")
    logger.warning("RECOMMENDATION: Implement QueueHandler/QueueListener in main app for robust file logging.")


# --- Import Analyzers/Testers ---
# Added logging for import failures and store classes/types for later checks
ANALYZER_CLASSES = {}
try:
    # Assume SecurityIssue is the common base or specific type for frontend
    from frontend_security_analysis import FrontendSecurityAnalyzer, SecurityIssue as FrontendSecurityIssue
    ANALYZER_CLASSES['frontend_security'] = FrontendSecurityAnalyzer
    logger.info("FrontendSecurityAnalyzer imported successfully.")
except ImportError as e:
    FrontendSecurityAnalyzer = None # Keep None for compatibility if used directly elsewhere
    FrontendSecurityIssue = None # Define as None if import failed
    logger.warning(f"FrontendSecurityAnalyzer not found. Frontend Security tasks will fail. Error: {e}")

try:
    # Assume BackendSecurityIssue is the specific type for backend
    from backend_security_analysis import BackendSecurityAnalyzer, BackendSecurityIssue
    ANALYZER_CLASSES['backend_security'] = BackendSecurityAnalyzer
    logger.info("BackendSecurityAnalyzer imported successfully.")
except ImportError as e:
    BackendSecurityAnalyzer = None
    BackendSecurityIssue = None # Define as None if import failed
    logger.warning(f"BackendSecurityAnalyzer not found. Backend Security tasks will fail. Error: {e}")

try:
    from performance_analysis import LocustPerformanceTester, PerformanceResult
    ANALYZER_CLASSES['performance'] = LocustPerformanceTester
    logger.info("LocustPerformanceTester imported successfully.")
except ImportError as e:
    LocustPerformanceTester = None
    PerformanceResult = None # Define as None if import failed
    logger.warning(f"LocustPerformanceTester not found. Performance tasks will fail. Error: {e}")

try:
    from gpt4all_analysis import GPT4AllAnalyzer, RequirementCheck
    ANALYZER_CLASSES['gpt4all'] = GPT4AllAnalyzer
    logger.info("GPT4AllAnalyzer imported successfully.")
except ImportError as e:
    GPT4AllAnalyzer = None
    RequirementCheck = None # Define as None if import failed
    logger.warning(f"GPT4AllAnalyzer not found. GPT4All tasks will fail. Error: {e}")

try:
    # ZAP uses ScanManager, not a direct analyzer class here
    from zap_scanner import ZAPScanner, ZapVulnerability # Import types for result processing
    logger.info("ZAPScanner types imported (used via ScanManager).")
except ImportError as e:
    ZAPScanner = None # Keep None for compatibility
    ZapVulnerability = None # Define as None if import failed
    logger.warning(f"ZAPScanner types not found. Error: {e}")

# Import ScanManager from services if available
try:
    # Assume ScanManager is responsible for ZAP interactions
    # It should have methods like create_scan, get_scan_status, get_scan_results
    from services import ScanManager
    ANALYZER_CLASSES['zap'] = ScanManager # Map ZAP type to ScanManager
    logger.info("ScanManager imported successfully (for ZAP).")
except ImportError as e:
    ScanManager = None
    logger.warning(f"ScanManager not found in services. ZAP tasks will fail. Error: {e}")

# Import PortManager if needed for performance tests
try:
    from services import PortManager
    logger.info("PortManager imported successfully.")
except ImportError as e:
    PortManager = None # Class will be checked before running performance tasks
    logger.warning(f"PortManager not found in services. Performance tasks will fail. Error: {e}")

# Import utilities
try:
    from utils import get_model_index, get_apps_for_model, get_app_directory, AI_MODELS
    logger.info("Utility functions (get_model_index, etc.) imported successfully.")
except ImportError as e:
    logger.error(f"Could not import key utility functions from utils. Error: {e}. Using dummy fallbacks.")
    # Define dummy functions if needed for the script to load, log errors on use
    def get_model_index(model_name: str) -> Optional[int]: logger.error("Dummy get_model_index called!"); return 0
    def get_apps_for_model(model_name: str) -> List[Dict[str, Any]]: logger.error("Dummy get_apps_for_model called!"); return []
    def get_app_directory(app_context: flask.Flask, model: str, app_num: int) -> Path:
        logger.error(f"Dummy get_app_directory called for {model}/app{app_num}")
        base = Path(app_context.config.get('APP_BASE_PATH', '.'))
        p = base / model / f"app{app_num}"
        if not p.is_dir(): raise FileNotFoundError(f"Dummy: Path not found: {p}")
        return p
    AI_MODELS = [] # Dummy empty list


# --- Blueprint Definition ---
batch_analysis_bp = Blueprint(
    "batch_analysis",
    __name__,
    template_folder="templates",
    url_prefix="/batch-analysis"
)
logger.debug("Batch Analysis Blueprint created.")

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
    logger.debug("JobStatus Enum defined.")

class AnalysisType(str, Enum):
    """Enumeration for the specific type of analysis to perform."""
    FRONTEND_SECURITY = "frontend_security"
    BACKEND_SECURITY = "backend_security"
    PERFORMANCE = "performance"
    GPT4ALL = "gpt4all"
    ZAP = "zap"
    logger.debug("AnalysisType Enum defined.")

@dataclass
class BatchAnalysisJob:
    """Represents a batch analysis job configuration and status."""
    id: int
    name: str
    description: str
    created_at: datetime
    status: JobStatus = JobStatus.PENDING
    models: List[str] = field(default_factory=list)
    app_ranges: Dict[str, List[int]] = field(default_factory=dict) # model -> list of app nums (empty list means all)
    analysis_types: List[AnalysisType] = field(default_factory=list)
    analysis_options: Dict[str, Any] = field(default_factory=dict) # Stores options per AnalysisType.value
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    results_summary: Dict[str, Any] = field(default_factory=dict) # Aggregated counts/stats
    errors: List[str] = field(default_factory=list) # Job-level errors (setup, critical failures)

    @property
    def created_at_formatted(self) -> str:
        """Returns created_at time formatted as YYYY-MM-DD HH:MM (local time)."""
        if not self.created_at: return 'N/A'
        local_dt = self.created_at.astimezone() if self.created_at.tzinfo else self.created_at
        return local_dt.strftime('%Y-%m-%d %H:%M')

    def _format_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        """Safely formats datetime object to ISO 8601 string (UTC 'Z' format)."""
        if isinstance(dt, datetime):
            try:
                # Ensure datetime is timezone-aware (assume UTC if not)
                utc_dt = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
                # Format to ISO 8601 with 'Z' for UTC
                return utc_dt.isoformat(timespec='seconds').replace('+00:00', 'Z')
            except Exception as e:
                logger.warning(f"[Job {self.id}] Could not format datetime {dt}: {e}")
                return str(dt) # Fallback to string representation
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Converts the job object to a dictionary suitable for JSON serialization."""
        result_dict = asdict(self)
        # Format datetime objects and enums for JSON
        result_dict['created_at'] = self._format_datetime(self.created_at)
        result_dict['started_at'] = self._format_datetime(self.started_at)
        result_dict['completed_at'] = self._format_datetime(self.completed_at)
        result_dict['status'] = self.status.value
        result_dict['analysis_types'] = [at.value for at in self.analysis_types]
        # Add formatted time for display purposes
        result_dict['created_at_formatted'] = self.created_at_formatted
        # Optionally truncate long errors list in dict representation for cleaner APIs
        # max_errors_in_dict = 10
        # if len(result_dict['errors']) > max_errors_in_dict:
        #     result_dict['errors'] = result_dict['errors'][:max_errors_in_dict] + ["... (truncated)"]
        return result_dict


@dataclass
class BatchAnalysisResult:
    """Represents the result of a single analysis task within a batch job."""
    id: int
    job_id: int
    model: str
    app_num: int
    status: str # e.g., "completed", "failed", "skipped", "timed_out"
    analysis_type: AnalysisType
    issues_count: int = 0 # Generic count (e.g., vulnerabilities, failed reqs, perf errors)
    high_severity: int = 0 # Primarily for security scans
    medium_severity: int = 0
    low_severity: int = 0
    scan_start_time: Optional[datetime] = None
    scan_end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    # Stores detailed results specific to the analysis type (e.g., list of issues, perf metrics)
    # Includes 'error' and 'traceback' keys on failure/timeout.
    details: Dict[str, Any] = field(default_factory=dict)

    def _format_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        """Safely formats datetime object to ISO 8601 string (UTC 'Z' format)."""
        if isinstance(dt, datetime):
            try:
                utc_dt = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
                return utc_dt.isoformat(timespec='seconds').replace('+00:00', 'Z')
            except Exception as e:
                # Use specific task logger if available, else module logger
                (task_logger or logger).warning(f"[Job {self.job_id}/Res {self.id}] Could not format datetime {dt}: {e}")
                return str(dt) # Fallback
        return None

    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitizes the details dictionary for JSON serialization."""
        sanitized = {}
        max_str_len = 1000
        max_list_len = 50 # Limit number of issues/items shown directly in JSON

        for key, value in details.items():
            if isinstance(value, str):
                sanitized[key] = value[:max_str_len] + ('...' if len(value) > max_str_len else '')
            elif isinstance(value, list):
                # Handle lists, potentially truncating and ensuring items are serializable
                if len(value) > max_list_len:
                    sanitized[key] = [self._sanitize_item(item) for item in value[:max_list_len]] + ["... (truncated)"]
                else:
                    sanitized[key] = [self._sanitize_item(item) for item in value]
            elif isinstance(value, dict):
                 # Recursively sanitize nested dictionaries (limit depth if needed)
                 sanitized[key] = self._sanitize_details(value) # Simple recursion for now
            else:
                 # Keep other JSON-serializable types as is
                 try:
                      json.dumps(value) # Quick check if serializable
                      sanitized[key] = value
                 except (TypeError, OverflowError):
                      sanitized[key] = f"<Unserializable type: {type(value).__name__}>"
        return sanitized

    def _sanitize_item(self, item: Any) -> Any:
        """Sanitizes a single item, often within a list."""
        if isinstance(item, dict):
            return self._sanitize_details(item) # Sanitize dicts within lists
        elif isinstance(item, str):
             max_str_len = 200 # Shorter limit for items in list
             return item[:max_str_len] + ('...' if len(item) > max_str_len else '')
        else:
            # Try to keep other simple types, represent complex ones
            try:
                json.dumps(item)
                return item
            except (TypeError, OverflowError):
                return f"<Unserializable item: {type(item).__name__}>"

    def to_dict(self) -> Dict[str, Any]:
        """Converts the result object to a dictionary suitable for JSON serialization."""
        result_dict = asdict(self)
        result_dict['scan_start_time'] = self._format_datetime(self.scan_start_time)
        result_dict['scan_end_time'] = self._format_datetime(self.scan_end_time)
        result_dict['analysis_type'] = self.analysis_type.value
        # Sanitize/Truncate potentially large details for cleaner JSON output
        result_dict['details'] = self._sanitize_details(result_dict['details'])
        return result_dict

# =============================================================================
# In-Memory Job Storage (Thread-Safe)
# =============================================================================

class JobStorage:
    """Simple in-memory storage for batch analysis jobs and their results."""
    def __init__(self):
        self.jobs: Dict[int, BatchAnalysisJob] = {}
        self.results: Dict[int, List[BatchAnalysisResult]] = {} # job_id -> list of results
        self.next_job_id = 1
        self.next_result_id = 1
        self._lock = threading.RLock() # Reentrant lock for safe nested calls if needed
        storage_logger.info("JobStorage initialized.")

    def _get_next_id(self, counter_attr: str) -> int:
        """Safely increments and returns the next ID (Internal, requires lock)."""
        # Assumes lock is already held when called
        current_id = getattr(self, counter_attr)
        setattr(self, counter_attr, current_id + 1)
        return current_id

    def create_job(self, job_data: Dict[str, Any], app_context: flask.Flask) -> BatchAnalysisJob:
        """Creates and stores a new batch analysis job."""
        storage_logger.debug(f"Attempting to create job with data keys: {list(job_data.keys())}")
        with self._lock:
            job_id = self._get_next_id('next_job_id')
            job_log_prefix = f"[Job {job_id}]"
            storage_logger.info(f"{job_log_prefix} Assigning ID for new job.")

            # --- Validate and Parse Input ---
            try:
                analysis_types_input = job_data.get('analysis_types', [])
                valid_analysis_types = []
                if isinstance(analysis_types_input, list):
                    for at_input in analysis_types_input:
                        if isinstance(at_input, AnalysisType): valid_analysis_types.append(at_input)
                        elif isinstance(at_input, str): valid_analysis_types.append(AnalysisType(at_input))
                        else: raise TypeError(f"Invalid type for analysis type: {type(at_input)}")
                else: raise TypeError("'analysis_types' must be a list.")
                if not valid_analysis_types: raise ValueError("No valid analysis types selected.")

                models_input = job_data.get('models', [])
                if not isinstance(models_input, list) or not all(isinstance(m, str) for m in models_input):
                    raise ValueError("'models' must be a list of strings.")
                if not models_input: raise ValueError("At least one model must be selected.")

                app_ranges_input = job_data.get('app_ranges', {})
                if not isinstance(app_ranges_input, dict): raise ValueError("'app_ranges' must be a dictionary.")
                # Further validation of app_ranges content (list of ints) happens implicitly later

            except (ValueError, TypeError) as validation_err:
                storage_logger.error(f"Job creation validation failed: {validation_err}", exc_info=True)
                raise validation_err # Re-raise to be caught by route handler

            # --- Create Job Object ---
            job = BatchAnalysisJob(
                id=job_id,
                name=job_data.get('name', f'Batch Job {job_id}').strip(),
                description=job_data.get('description', '').strip(),
                created_at=datetime.now(timezone.utc),
                models=models_input,
                app_ranges=app_ranges_input,
                analysis_types=valid_analysis_types,
                analysis_options=job_data.get('analysis_options', {}),
            )
            storage_logger.debug(f"{job_log_prefix} BatchAnalysisJob object created in memory.")

            # --- Estimate Total Tasks ---
            try:
                # Pass the app context needed by the calculation method
                job.total_tasks = self._calculate_total_tasks(job, app_context)
                storage_logger.debug(f"{job_log_prefix} Estimated total tasks: {job.total_tasks}")
            except Exception as calc_err:
                storage_logger.warning(f"{job_log_prefix} Failed to calculate initial task count: {calc_err}. Setting to 0.", exc_info=False)
                job.total_tasks = 0

            # --- Store Job ---
            self.jobs[job_id] = job
            self.results[job_id] = []
            analysis_names = ', '.join([at.value for at in job.analysis_types])
            storage_logger.info(f"{job_log_prefix} Created Job '{job.name}' (Types: {analysis_names}, Est Tasks: {job.total_tasks})")
            storage_logger.debug(f"Current job IDs in storage: {list(self.jobs.keys())}")
            return job

    def _calculate_total_tasks(self, job: BatchAnalysisJob, app_context: flask.Flask) -> int:
        """Calculates estimated total tasks. Requires Flask app context. (Internal)"""
        job_log_prefix = f"[Job {job.id}]"
        storage_logger.debug(f"{job_log_prefix} Calculating total tasks...")
        total_tasks = 0
        base_path_str = app_context.config.get('APP_BASE_PATH')
        if not base_path_str:
            storage_logger.error(f"{job_log_prefix} APP_BASE_PATH not found in Flask config. Cannot calculate tasks.")
            return 0
        base_path = Path(base_path_str)
        storage_logger.debug(f"{job_log_prefix} Using base path: {base_path}")

        if not job.analysis_types:
            storage_logger.warning(f"{job_log_prefix} No analysis types defined, task count is 0.")
            return 0

        for model in job.models:
            storage_logger.debug(f"{job_log_prefix} Processing model '{model}' for task calculation.")
            model_path = base_path / model
            if not model_path.is_dir():
                storage_logger.warning(f"{job_log_prefix} Model directory not found: {model_path}. Skipping model.")
                continue

            # Determine target apps for this model
            target_apps_nums = []
            app_range_for_model = job.app_ranges.get(model) # Could be None or []
            # Check if key exists and value is explicitly an empty list []
            scan_all_apps = (model in job.app_ranges and isinstance(app_range_for_model, list) and not app_range_for_model)

            if scan_all_apps:
                storage_logger.debug(f"{job_log_prefix} Model '{model}' set to scan all apps.")
                try:
                    target_apps_nums = sorted([
                        int(item.name[3:]) for item in model_path.iterdir()
                        if item.is_dir() and item.name.startswith('app') and item.name[3:].isdigit()
                    ])
                    storage_logger.debug(f"{job_log_prefix} Dynamically found apps for '{model}': {target_apps_nums}")
                except Exception as e:
                    storage_logger.error(f"{job_log_prefix} Failed list apps for '{model}': {e}. Assuming 0 apps.")
                    target_apps_nums = []
            elif isinstance(app_range_for_model, list):
                # Use specified list (already parsed into ints by route handler/parse_app_range)
                target_apps_nums = sorted(list(set(app_range_for_model)))
                storage_logger.debug(f"{job_log_prefix} Using specified apps for '{model}': {target_apps_nums}")
            else:
                 # Model key might be missing from app_ranges, or value is not a list -> treat as "scan none"
                 storage_logger.debug(f"{job_log_prefix} No specific app range defined for '{model}', assuming 0 apps.")
                 target_apps_nums = []


            # Count valid apps that actually exist
            valid_app_count = 0
            for app_num in target_apps_nums:
                try:
                    # Use the utility function for consistency, requires app_context
                    app_dir = get_app_directory(app_context, model, app_num)
                    if app_dir.is_dir():
                        valid_app_count += 1
                    else:
                        storage_logger.debug(f"{job_log_prefix} App directory {app_dir} not found during count.")
                except FileNotFoundError:
                    storage_logger.debug(f"{job_log_prefix} App dir not found via util for {model}/app{app_num} during count.")
                except Exception as e:
                    storage_logger.warning(f"{job_log_prefix} Error checking app {app_num} for '{model}': {e}")

            model_tasks = valid_app_count * len(job.analysis_types)
            total_tasks += model_tasks
            storage_logger.debug(f"{job_log_prefix} Model '{model}': {valid_app_count} valid apps * {len(job.analysis_types)} types = {model_tasks} tasks. Running total: {total_tasks}")

        storage_logger.info(f"{job_log_prefix} Total estimated tasks calculated: {total_tasks}")
        return total_tasks

    def get_job(self, job_id: int) -> Optional[BatchAnalysisJob]:
        """Retrieves a job by its ID."""
        job_log_prefix = f"[Job {job_id}]"
        storage_logger.debug(f"{job_log_prefix} Request retrieve job.")
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                storage_logger.warning(f"{job_log_prefix} Job not found in storage.")
            return job

    def get_all_jobs(self) -> List[BatchAnalysisJob]:
        """Returns a list of all stored jobs."""
        storage_logger.debug("Request retrieve all jobs.")
        with self._lock:
            all_jobs = list(self.jobs.values())
            storage_logger.debug(f"Retrieved {len(all_jobs)} jobs.")
            return all_jobs

    def update_job(self, job_id: int, **kwargs) -> Optional[BatchAnalysisJob]:
        """Updates attributes of an existing job. Thread-safe."""
        job_log_prefix = f"[Job {job_id}]"
        # Log keys being updated, avoid logging large values directly
        log_kwargs_keys = list(kwargs.keys())
        storage_logger.debug(f"{job_log_prefix} Request update job with keys: {log_kwargs_keys}")

        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                storage_logger.warning(f"{job_log_prefix} Update failed: Job not found.")
                return None

            updated_fields = []
            for key, value in kwargs.items():
                if not hasattr(job, key):
                    storage_logger.warning(f"{job_log_prefix} Attempted to set unknown attribute '{key}'. Skipping.")
                    continue

                current_value = getattr(job, key)
                new_value = value

                # --- Type Conversions/Validations ---
                try:
                    if key == 'status' and isinstance(value, str): new_value = JobStatus(value)
                    elif key == 'status' and isinstance(value, JobStatus): pass # Already correct type
                    elif key in ['started_at', 'completed_at'] and isinstance(value, datetime):
                        new_value = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
                    elif key == 'errors' and isinstance(value, list): new_value = [str(e) for e in value]
                    elif key == 'results_summary' and isinstance(value, dict): pass
                    elif key in ['total_tasks', 'completed_tasks'] and value is not None: new_value = int(value)
                    # Add other type checks as needed
                except (ValueError, TypeError) as conv_err:
                    storage_logger.error(f"{job_log_prefix} Invalid value type for '{key}': {value}. Error: {conv_err}. Update skipped.")
                    continue

                # --- Update if Changed ---
                if new_value != current_value:
                    # Abbreviate log value representation for large items
                    log_value_repr = repr(new_value)
                    if isinstance(new_value, (dict, list)) and len(new_value) > 5: log_value_repr = f"<{type(new_value).__name__} len {len(new_value)}>"
                    elif isinstance(new_value, str) and len(new_value) > 100: log_value_repr = repr(new_value[:100] + '...')

                    storage_logger.info(f"{job_log_prefix} Updating '{key}': {repr(current_value)} -> {log_value_repr}")
                    setattr(job, key, new_value)
                    updated_fields.append(key)

            if not updated_fields:
                storage_logger.debug(f"{job_log_prefix} No fields needed update.")

            return job

    def add_result(self, job_id: int, result_data: Dict[str, Any]) -> Optional[BatchAnalysisResult]:
        """Adds an analysis result, updates job progress/summary. Thread-safe."""
        job_log_prefix = f"[Job {job_id}]"
        task_info = f"{result_data.get('model', '?')}/app{result_data.get('app_num', '?')}/{result_data.get('analysis_type', '?')}"
        storage_logger.debug(f"{job_log_prefix} Request add result for task: {task_info} (Status: {result_data.get('status')}).")

        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                storage_logger.warning(f"{job_log_prefix} Cannot add result: Job not found.")
                return None

            # --- Generate Result ID ---
            result_id = self._get_next_id('next_result_id')
            res_log_prefix = f"{job_log_prefix}[Result {result_id}]"
            storage_logger.info(f"{res_log_prefix} Assigning ID for new result (Task: {task_info})")

            # --- Validate and Parse Result Data ---
            try:
                analysis_type_input = result_data.get('analysis_type')
                if isinstance(analysis_type_input, AnalysisType): analysis_type = analysis_type_input
                elif isinstance(analysis_type_input, str): analysis_type = AnalysisType(analysis_type_input)
                else: raise TypeError(f"Invalid analysis_type: {analysis_type_input}")

                status = result_data.get('status', 'failed') # Default to failed
                # ZAP now uses 'completed' or 'failed' instead of 'triggered'
                valid_statuses = ["completed", "failed", "skipped", "timed_out"]
                if status not in valid_statuses:
                    storage_logger.warning(f"{res_log_prefix} Result has unrecognized status '{status}'. Storing as is.")

                start_time_in = result_data.get('scan_start_time')
                end_time_in = result_data.get('scan_end_time', datetime.now(timezone.utc))

                start_time = start_time_in if start_time_in and start_time_in.tzinfo else start_time_in.replace(tzinfo=timezone.utc) if start_time_in else None
                end_time = end_time_in if end_time_in and end_time_in.tzinfo else end_time_in.replace(tzinfo=timezone.utc)

                duration = None
                if isinstance(start_time, datetime) and isinstance(end_time, datetime):
                    duration = (end_time - start_time).total_seconds()
                    if duration < 0:
                        storage_logger.warning(f"{res_log_prefix} Calculated negative duration ({duration:.2f}s). Setting to None.")
                        duration = None
                    else:
                        storage_logger.debug(f"{res_log_prefix} Duration calculated: {duration:.2f}s")

            except (ValueError, TypeError) as validation_err:
                storage_logger.error(f"{res_log_prefix} Result data validation failed: {validation_err}", exc_info=True)
                # Add error to job itself
                job_errors = job.errors + [f"Invalid result data received for task {task_info}: {validation_err}"]
                self.update_job(job_id, errors=job_errors) # update_job handles lock
                return None

            # --- Create and Store Result Object ---
            result = BatchAnalysisResult(
                id=result_id,
                job_id=job_id,
                model=result_data.get('model', 'UnknownModel'),
                app_num=result_data.get('app_num', 0),
                status=status,
                analysis_type=analysis_type,
                issues_count=result_data.get('issues_count', 0),
                high_severity=result_data.get('high_severity', 0),
                medium_severity=result_data.get('medium_severity', 0),
                low_severity=result_data.get('low_severity', 0),
                scan_start_time=start_time,
                scan_end_time=end_time,
                duration_seconds=duration,
                details=result_data.get('details', {}) # Includes error/traceback
            )
            storage_logger.debug(f"{res_log_prefix} BatchAnalysisResult object created.")

            self.results.setdefault(job_id, []).append(result)
            storage_logger.info(f"{res_log_prefix} Result added. Job '{job.name}' now has {len(self.results[job_id])} results.")

            # --- Update Job Progress and Summary ---
            storage_logger.debug(f"{job_log_prefix} Updating progress after result {result_id}.")
            job.completed_tasks += 1 # Increment completion count atomically (under lock)
            job_completed_tasks = job.completed_tasks
            job_total_tasks = job.total_tasks
            summary = job.results_summary.copy() # Work on a copy

            # Increment overall and per-type task completion counts
            summary['total_tasks_processed'] = summary.get('total_tasks_processed', 0) + 1
            summary[f'{analysis_type.value}_tasks_processed'] = summary.get(f'{analysis_type.value}_tasks_processed', 0) + 1

            # Aggregate based on status
            summary[f'tasks_{status}'] = summary.get(f'tasks_{status}', 0) + 1
            summary[f'{analysis_type.value}_tasks_{status}'] = summary.get(f'{analysis_type.value}_tasks_{status}', 0) + 1

            # Aggregate counts only for 'completed' tasks that provide counts
            if status == 'completed':
                summary['issues_total'] = summary.get('issues_total', 0) + result.issues_count
                # ZAP now also contributes to severity counts
                if analysis_type in [AnalysisType.FRONTEND_SECURITY, AnalysisType.BACKEND_SECURITY, AnalysisType.ZAP]:
                    summary['high_total'] = summary.get('high_total', 0) + result.high_severity
                    summary['medium_total'] = summary.get('medium_total', 0) + result.medium_severity
                    summary['low_total'] = summary.get('low_total', 0) + result.low_severity
                # Track per-type issue counts
                summary[f'{analysis_type.value}_issues_total'] = summary.get(f'{analysis_type.value}_issues_total', 0) + result.issues_count
                # Add specific metric aggregation if needed (e.g., Performance/GPT4All)
                if analysis_type == AnalysisType.PERFORMANCE and 'total_failures' in result.details:
                     summary['performance_total_failures'] = summary.get('performance_total_failures', 0) + result.details['total_failures']
                if analysis_type == AnalysisType.GPT4ALL and 'summary' in result.details:
                     gpt_summary = result.details['summary']
                     summary['gpt4all_reqs_checked_total'] = summary.get('gpt4all_reqs_checked_total', 0) + gpt_summary.get('requirements_checked', 0)
                     summary['gpt4all_reqs_met_total'] = summary.get('gpt4all_reqs_met_total', 0) + gpt_summary.get('met_count', 0)

            # --- Check if Job is Finished ---
            # Use >= total_tasks in case total changes or overshoots slightly
            # Ensure total_tasks > 0 to avoid finishing jobs with 0 tasks prematurely
            is_finished = job.status == JobStatus.RUNNING and job_total_tasks > 0 and job_completed_tasks >= job_total_tasks
            final_status_update = {}
            if is_finished:
                # Determine final status based on errors and task outcomes
                has_job_errors = bool(job.errors)
                has_failed_tasks = summary.get('tasks_failed', 0) > 0
                has_timed_out_tasks = summary.get('tasks_timed_out', 0) > 0

                final_status = JobStatus.FAILED if (has_job_errors or has_failed_tasks or has_timed_out_tasks) else JobStatus.COMPLETED
                storage_logger.info(f"{job_log_prefix} Job finished processing tasks. Tasks: {job_completed_tasks}/{job_total_tasks}. JobErrors: {has_job_errors}, FailedTasks: {has_failed_tasks}, TimedOutTasks: {has_timed_out_tasks}. Final Status: {final_status.value}")
                final_status_update = {
                    "status": final_status,
                    "completed_at": datetime.now(timezone.utc)
                }

            # --- Update Job State ---
            # Always update completed tasks and summary, add final status if finished
            update_data = {
                "completed_tasks": job_completed_tasks,
                "results_summary": summary,
                **final_status_update
            }
            # Call update_job which handles the lock internally
            update_success = self.update_job(job_id, **update_data)
            if update_success:
                storage_logger.debug(f"{job_log_prefix} Updated job state in storage.")
            else:
                # Should not happen if lock is held correctly unless job deleted concurrently
                storage_logger.error(f"{job_log_prefix} CRITICAL: Failed to update job state after adding result {result_id}.")

            return result # Return the created result object

    def get_results(self, job_id: int) -> List[BatchAnalysisResult]:
        """Retrieves all results associated with a job ID."""
        job_log_prefix = f"[Job {job_id}]"
        storage_logger.debug(f"{job_log_prefix} Request retrieve results.")
        with self._lock:
            results_list = list(self.results.get(job_id, [])) # Return a copy
            storage_logger.debug(f"{job_log_prefix} Found {len(results_list)} results.")
            return results_list

    def get_result(self, result_id: int) -> Optional[BatchAnalysisResult]:
        """Retrieves a specific result by its unique ID."""
        res_log_prefix = f"[Result {result_id}]"
        storage_logger.debug(f"{res_log_prefix} Request retrieve result.")
        with self._lock:
            for job_id_key, results_list in self.results.items():
                for result in results_list:
                    if result.id == result_id:
                        storage_logger.debug(f"{res_log_prefix} Found in Job {job_id_key}.")
                        return result
        storage_logger.warning(f"{res_log_prefix} Result not found in any job.")
        return None

    def delete_job(self, job_id: int) -> bool:
        """Deletes a job and all its associated results."""
        job_log_prefix = f"[Job {job_id}]"
        storage_logger.info(f"{job_log_prefix} Request delete job.")
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                storage_logger.warning(f"{job_log_prefix} Delete failed: Job not found.")
                return False

            if job.status == JobStatus.RUNNING:
                storage_logger.error(f"{job_log_prefix} Cannot delete job: Job is currently RUNNING. Cancel it first.")
                return False # Prevent deletion of running jobs

            # Proceed with deletion
            del self.jobs[job_id]
            deleted_results_count = 0
            if job_id in self.results:
                deleted_results_count = len(self.results[job_id])
                del self.results[job_id]

            storage_logger.info(f"{job_log_prefix} Deleted job '{job.name}' and {deleted_results_count} associated results.")
            storage_logger.debug(f"Remaining job IDs: {list(self.jobs.keys())}")
            return True

# Global instance of the job storage
job_storage = JobStorage()
logger.debug("Global job_storage instance created.")


# =============================================================================
# Batch Analysis Execution Service (Handles Job Lifecycle)
# =============================================================================
class BatchAnalysisService:
    """Manages the execution lifecycle of batch analysis jobs."""

    def __init__(self, storage: JobStorage):
        self.storage = storage
        self._running_jobs: Dict[int, threading.Thread] = {} # job_id -> Thread object
        self._cancel_flags: Set[int] = set() # Stores IDs of jobs marked for cancellation
        # Read config from environment or defaults
        self.max_concurrent_jobs = max(1, int(os.environ.get("BATCH_MAX_JOBS", 2)))
        self.max_concurrent_tasks = max(1, int(os.environ.get("BATCH_MAX_TASKS", 4)))
        # Increased default timeout to accommodate potentially longer ZAP scans
        self.default_task_timeout = int(os.environ.get("BATCH_TASK_TIMEOUT_SECONDS", 1800)) # Default 30 mins
        self.app: Optional[flask.Flask] = None # Set via set_app
        service_logger.info(f"Initialized BatchAnalysisService (MaxJobs:{self.max_concurrent_jobs}, MaxTasks:{self.max_concurrent_tasks}, TaskTimeout:{self.default_task_timeout}s)")

    def set_app(self, app: flask.Flask):
        """Stores the Flask application instance for accessing context."""
        self.app = app
        # Update config from Flask app if set there
        self.max_concurrent_jobs = max(1, app.config.get("BATCH_MAX_JOBS", self.max_concurrent_jobs))
        self.max_concurrent_tasks = max(1, app.config.get("BATCH_MAX_TASKS", self.max_concurrent_tasks))
        self.default_task_timeout = app.config.get("BATCH_TASK_TIMEOUT_SECONDS", self.default_task_timeout)
        service_logger.info(f"Flask app '{app.name}' registered. Effective config: MaxJobs:{self.max_concurrent_jobs}, MaxTasks:{self.max_concurrent_tasks}, TaskTimeout:{self.default_task_timeout}s")

    def start_job(self, job_id: int) -> bool:
        """Starts a job execution in a background thread after checks and cleanup."""
        job_log_prefix = f"[Job {job_id}]"
        service_logger.info(f"{job_log_prefix} Request to start job.")
        job = self.storage.get_job(job_id)

        # --- Initial Checks ---
        if not job: service_logger.error(f"{job_log_prefix} Start failed: Job not found."); return False
        service_logger.debug(f"{job_log_prefix} Found job '{job.name}', Status: {job.status.value}")
        if job.status == JobStatus.RUNNING: service_logger.warning(f"{job_log_prefix} Start failed: Job already running."); return False
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELED]: service_logger.info(f"{job_log_prefix} Job finished ({job.status.value}). Attempting restart.")
        if not self.app:
            service_logger.error(f"{job_log_prefix} Start failed: Service missing Flask app context.")
            self.storage.update_job(job_id, status=JobStatus.FAILED, errors=["Service missing Flask app context"])
            return False

        # --- Pre-start Checks & Cleanup (within request context) ---
        new_total_tasks = 0
        try:
            current_flask_app = current_app._get_current_object() # Get context from triggering request
            with current_flask_app.app_context():
                service_logger.info(f"{job_log_prefix} Starting pre-run checks and cleanup...")

                # 1. Pre-run Cleanup (Clear results, temp files, etc.)
                service_logger.debug(f"{job_log_prefix} Performing cleanup...")
                try:
                    with self.storage._lock: # Lock needed for modifying storage state
                        if job_id in self.storage.results and self.storage.results[job_id]:
                            count = len(self.storage.results[job_id])
                            self.storage.results[job_id] = []
                            service_logger.info(f"{job_log_prefix} Cleared {count} previous results.")
                    # Add other cleanup logic (temp files, external services) here if needed
                    # Example: temp_dir = Path(current_flask_app.config.get("TEMP_DIR", "/tmp")) / f"batch_{job_id}" ... shutil.rmtree(...)
                    service_logger.info(f"{job_log_prefix} Pre-run cleanup finished.")
                except Exception as cleanup_err:
                    service_logger.exception(f"{job_log_prefix} Error during pre-run cleanup: {cleanup_err}. Proceeding cautiously.")
                    # Optionally fail the job here if cleanup is critical

                # 2. Recalculate tasks and check if runnable
                service_logger.debug(f"{job_log_prefix} Recalculating total tasks...")
                new_total_tasks = self.storage._calculate_total_tasks(job, current_flask_app)
                if new_total_tasks == 0:
                    fail_msg = "Job configuration resulted in 0 tasks (check model/app paths and ranges)."
                    if not job.analysis_types: fail_msg = "No analysis types selected."
                    service_logger.error(f"{job_log_prefix} Start failed: {fail_msg}")
                    self.storage.update_job(job_id, status=JobStatus.FAILED, errors=[fail_msg])
                    return False

        except Exception as pre_start_err:
            service_logger.exception(f"{job_log_prefix} Error during pre-start checks: {pre_start_err}.")
            self.storage.update_job(job_id, status=JobStatus.FAILED, errors=[f"Error during pre-start: {pre_start_err}"])
            return False

        # --- Acquire Lock and Start Thread ---
        with self.storage._lock:
            service_logger.debug(f"{job_log_prefix} Acquired storage lock. Checking concurrent job limit ({len(self._running_jobs)}/{self.max_concurrent_jobs}).")
            if len(self._running_jobs) >= self.max_concurrent_jobs:
                service_logger.warning(f"{job_log_prefix} Start failed: Max concurrent jobs ({self.max_concurrent_jobs}) reached.")
                # TODO: Implement queuing mechanism here if desired (set status to QUEUED)
                flash(f"Job {job_id} cannot start: maximum concurrent jobs reached.", "warning")
                return False # Cannot start now

            # --- Reset Job State for Run ---
            service_logger.info(f"{job_log_prefix} Resetting job state for start (Tasks: {new_total_tasks}).")
            start_time_utc = datetime.now(timezone.utc)
            update_success = self.storage.update_job(
                job_id,
                status=JobStatus.RUNNING,
                started_at=start_time_utc,
                completed_at=None,
                completed_tasks=0,
                errors=[],
                results_summary={},
                total_tasks=new_total_tasks # Use recalculated count
            )
            if not update_success: # Should not happen if job existed before lock
                service_logger.error(f"{job_log_prefix} Failed to update job state during reset. Aborting start.")
                return False

            job = self.storage.get_job(job_id) # Fetch updated job object
            if not job: # Paranoid check
                service_logger.error(f"{job_log_prefix} Job disappeared after state reset. Aborting start.")
                return False

            # --- Start Background Thread ---
            thread_name = f"batch-job-{job_id}"
            service_logger.debug(f"{job_log_prefix} Creating background thread '{thread_name}'.")
            thread = threading.Thread(
                target=self._run_job_wrapper,
                args=(job_id,),
                daemon=True, # Allows app to exit even if thread is running
                name=thread_name
            )
            self._running_jobs[job_id] = thread # Add before starting thread
            thread.start()
            service_logger.info(f"{job_log_prefix} Successfully started job '{job.name}' in background thread '{thread_name}'. Tasks: {job.total_tasks}")

        return True

    def _run_job_wrapper(self, job_id: int) -> None:
        """Wrapper to run the job logic within the Flask app context."""
        thread_name = threading.current_thread().name
        job_log_prefix = f"[{thread_name}]" # Use thread name as prefix
        service_logger.info(f"{job_log_prefix} Job wrapper thread started for Job {job_id}.")

        if not self.app:
            service_logger.error(f"{job_log_prefix} CRITICAL: Cannot run job {job_id}: Flask app context unavailable.")
            self._handle_thread_exit_error(job_id, "Flask app context unavailable at runtime")
            return # Cleanup handled in finally

        current_flask_app = self.app
        service_logger.debug(f"{job_log_prefix} Entering app context for job {job_id} using app '{current_flask_app.name}'.")
        try:
            with current_flask_app.app_context():
                service_logger.info(f"{job_log_prefix} App context acquired for job {job_id}.")
                self._run_job_logic(job_id) # Execute main logic
            service_logger.info(f"{job_log_prefix} App context released for job {job_id}.")
        except Exception as wrapper_exc:
            service_logger.exception(f"{job_log_prefix} Unhandled exception in job wrapper for job {job_id}: {wrapper_exc}")
            self._handle_thread_exit_error(job_id, f"Unhandled wrapper error: {wrapper_exc}")
        finally:
            # --- CRITICAL: Ensure cleanup runs regardless of exceptions ---
            self._cleanup_after_job_thread(job_id)
            service_logger.info(f"{job_log_prefix} Job wrapper thread finished for Job {job_id}.")


    def _run_job_logic(self, job_id: int) -> None:
        """Core logic for executing tasks. Runs within app context."""
        job_log_prefix = f"[{threading.current_thread().name}][Job {job_id}]"
        service_logger.info(f"{job_log_prefix} Starting core execution logic.")

        # --- Re-fetch Job and Validate Status ---
        job = self.storage.get_job(job_id)
        if not job: service_logger.error(f"{job_log_prefix} Aborting: Job not found."); return
        if job.status != JobStatus.RUNNING: service_logger.warning(f"{job_log_prefix} Aborting: Expected RUNNING, found '{job.status.value}'."); return

        # --- Fetch Required Services (within context) ---
        service_logger.debug(f"{job_log_prefix} Fetching required analyzers/services...")
        analyzers_services = {}
        fetch_errors = []
        # Map AnalysisType enum to expected attribute name on current_app or imported class
        required_map = {
            AnalysisType.FRONTEND_SECURITY: ('frontend_security_analyzer', ANALYZER_CLASSES.get('frontend_security')),
            AnalysisType.BACKEND_SECURITY: ('backend_security_analyzer', ANALYZER_CLASSES.get('backend_security')),
            AnalysisType.PERFORMANCE: ('performance_tester', ANALYZER_CLASSES.get('performance')),
            AnalysisType.GPT4ALL: ('gpt4all_analyzer', ANALYZER_CLASSES.get('gpt4all')),
            AnalysisType.ZAP: ('scan_manager', ANALYZER_CLASSES.get('zap')), # Use ScanManager
        }
        port_manager_available = PortManager is not None # Check if class was imported

        for analysis_type in job.analysis_types:
            if analysis_type in required_map:
                attr_name, expected_class = required_map[analysis_type]
                service_instance = getattr(current_app, attr_name, None)

                if service_instance is None:
                    error_msg = f"Required service '{attr_name}' for '{analysis_type.value}' not found on Flask app."
                    fetch_errors.append(error_msg); service_logger.error(f"{job_log_prefix} {error_msg}")
                elif expected_class and not isinstance(service_instance, expected_class):
                    # Check type if expected class is known
                    error_msg = f"Service '{attr_name}' for '{analysis_type.value}' has wrong type: Found {type(service_instance).__name__}, expected {expected_class.__name__}."
                    fetch_errors.append(error_msg); service_logger.error(f"{job_log_prefix} {error_msg}")
                else:
                    analyzers_services[analysis_type] = service_instance
                    service_logger.debug(f"{job_log_prefix} Fetched service '{attr_name}': {type(service_instance).__name__}")
            # Special check for performance task dependency
            if analysis_type == AnalysisType.PERFORMANCE and not port_manager_available:
                 error_msg = f"PortManager class unavailable, required for '{analysis_type.value}' tasks."
                 if error_msg not in fetch_errors: # Avoid duplicates if already added by main check
                     fetch_errors.append(error_msg); service_logger.error(f"{job_log_prefix} {error_msg}")


        if fetch_errors:
            service_logger.error(f"{job_log_prefix} Aborting execution due to missing/invalid services.")
            self.storage.update_job(job_id, status=JobStatus.FAILED, errors=fetch_errors, completed_at=datetime.now(timezone.utc))
            return # Cleanup handled by wrapper's finally

        # --- Task Generation (within context) ---
        try:
            service_logger.info(f"{job_log_prefix} Generating task list for '{job.name}'.")
            tasks = self._generate_task_list(job) # Requires app context
            service_logger.info(f"{job_log_prefix} Generated {len(tasks)} tasks.")

            # Update total tasks if different from estimate/reset value
            if len(tasks) != job.total_tasks:
                service_logger.info(f"{job_log_prefix} Task count changed {job.total_tasks}->{len(tasks)}. Updating job.")
                self.storage.update_job(job_id, total_tasks=len(tasks))
                job.total_tasks = len(tasks) # Update local copy

            if not tasks:
                service_logger.warning(f"{job_log_prefix} Job has no tasks to execute. Marking as COMPLETED.")
                self.storage.update_job(job_id, status=JobStatus.COMPLETED, completed_at=datetime.now(timezone.utc))
                return

        except Exception as task_gen_err:
            service_logger.exception(f"{job_log_prefix} Error generating task list: {task_gen_err}")
            self.storage.update_job(job_id, status=JobStatus.FAILED, errors=[f"Error generating tasks: {task_gen_err}"], completed_at=datetime.now(timezone.utc))
            return


        # --- Task Execution using ThreadPoolExecutor ---
        active_futures: Dict[Future, Tuple[str, int, AnalysisType]] = {} # future -> (model, app_num, analysis_type)
        cancelled_by_flag = False
        try:
            service_logger.info(f"{job_log_prefix} Starting ThreadPoolExecutor (workers={self.max_concurrent_tasks}).")
            with ThreadPoolExecutor(max_workers=self.max_concurrent_tasks, thread_name_prefix=f"batch_task_{job_id}") as executor:
                service_logger.debug(f"{job_log_prefix} Submitting {len(tasks)} tasks.")
                for model, app_num, analysis_type in tasks:
                    task_desc = f"{model}/app{app_num}/{analysis_type.value}"
                    required_service = analyzers_services.get(analysis_type) # Fetch instance

                    # Check dependencies again before submitting (service instance, PortManager class)
                    skip_task = False; error_detail = None
                    if required_service is None and analysis_type in required_map: # Check if service instance exists
                        error_detail = f"Required service instance for {analysis_type.value} not available."
                        skip_task = True
                    elif analysis_type == AnalysisType.PERFORMANCE and not port_manager_available:
                        error_detail = "PortManager class is not available for Performance task."
                        skip_task = True

                    if skip_task:
                        service_logger.error(f"{job_log_prefix} Cannot submit task {task_desc}: {error_detail}")
                        # Record a failed result directly immediately
                        self.storage.add_result(job_id, {
                            "model": model, "app_num": app_num, "analysis_type": analysis_type,
                            "status": "failed", "scan_start_time": datetime.now(timezone.utc),
                            "details": {"error": error_detail}
                        })
                        continue # Skip submitting this task

                    # Submit the task
                    service_logger.debug(f"{job_log_prefix} Submitting task: {task_desc}")
                    future = executor.submit(
                        self._analyze_app_task, # Target function
                        job_id, model, app_num, analysis_type, # Task details
                        job.analysis_options, # Job-level options
                        required_service,     # Specific service instance
                        PortManager           # Pass PortManager class (or None)
                    )
                    active_futures[future] = (model, app_num, analysis_type)

                service_logger.info(f"{job_log_prefix} All {len(active_futures)} valid tasks submitted. Waiting for completion...")
                # --- Process Completed Tasks ---
                completed_count = 0
                for future in as_completed(active_futures):
                    completed_count += 1
                    model, app_num, analysis_type = active_futures[future]
                    task_desc = f"{model}/app{app_num}/{analysis_type.value}"
                    service_logger.debug(f"{job_log_prefix} Future completed for task: {task_desc} ({completed_count}/{len(active_futures)})")

                    # --- Check for Cancellation Flag ---
                    with self.storage._lock: cancelled = job_id in self._cancel_flags
                    if cancelled:
                        service_logger.info(f"{job_log_prefix} Cancellation detected processing task {task_desc}. Breaking loop.")
                        cancelled_by_flag = True; break # Break loop, handle cleanup below

                    # --- Process Task Result/Exception ---
                    try:
                        # Check for exceptions raised by the task function itself.
                        # The task function (_analyze_app_task) should handle its internal errors
                        # and report them via storage.add_result. This catches unexpected errors
                        # in the task wrapper or future execution.
                        future.result(timeout=0.1) # Small timeout just to check for immediate exceptions
                        service_logger.debug(f"{job_log_prefix} Task {task_desc} future completed without immediate exception.")
                    except FutureTimeoutError:
                         # Expected if task is still running, result processed via storage.add_result
                         pass
                    except Exception as task_exc:
                        # This catches unexpected errors *outside* the _analyze_app_task's main try/except
                        error_msg = f"Task Error ({task_desc}): Unhandled exception during future processing: {type(task_exc).__name__} - {str(task_exc)}"
                        detailed_traceback = traceback.format_exc()
                        service_logger.error(f"{job_log_prefix} {error_msg}", exc_info=False)
                        service_logger.debug(f"{job_log_prefix} Unhandled task exception details for {task_desc}:\n{detailed_traceback}")

                        # Record a specific "failed" result for this unhandled exception
                        self.storage.add_result(job_id, {
                            "model": model, "app_num": app_num, "analysis_type": analysis_type,
                            "status": "failed", "scan_start_time": datetime.now(timezone.utc), # Approx time
                            "details": {"error": error_msg, "traceback": detailed_traceback}
                        })
                        # Add error to the main job object
                        with self.storage._lock:
                            current_job = self.storage.get_job(job_id)
                            current_job_errors = current_job.errors if current_job else []
                        self.storage.update_job(job_id, errors=current_job_errors + [error_msg])

            # --- End of ThreadPoolExecutor Context Manager ---
            service_logger.info(f"{job_log_prefix} ThreadPoolExecutor finished processing submitted tasks.")

            # --- Handle Cancellation Cleanup (After Loop) ---
            if cancelled_by_flag:
                remaining_futures_count = len(active_futures) - completed_count
                service_logger.info(f"{job_log_prefix} Attempting to cancel {remaining_futures_count} remaining futures due to cancellation flag.")
                cancelled_count = 0
                for f, t_info in active_futures.items():
                    if not f.done():
                        if f.cancel(): # Attempt to cancel
                            cancelled_count += 1
                            service_logger.debug(f"{job_log_prefix} Submitted cancellation for future task: {t_info[0]}/app{t_info[1]}/{t_info[2].value}")
                if cancelled_count > 0: service_logger.info(f"{job_log_prefix} Submitted cancellation request for {cancelled_count} futures.")
                # Set final status to CANCELED
                service_logger.info(f"{job_log_prefix} Updating final status to CANCELED.")
                cancel_msg = "Job canceled by user."
                with self.storage._lock: # Add error message safely
                     current_job = self.storage.get_job(job_id)
                     current_errors = current_job.errors if current_job else []
                     if cancel_msg not in current_errors: current_errors.append(cancel_msg)
                self.storage.update_job(job_id, status=JobStatus.CANCELED, errors=current_errors, completed_at=datetime.now(timezone.utc))


            # --- Final Status Update (if not cancelled) ---
            # Re-fetch job state after all tasks processed or loop broken
            job = self.storage.get_job(job_id)
            if not job: service_logger.error(f"{job_log_prefix} Job object missing after task execution!"); return

            # If the job finished normally (all tasks processed) and wasn't cancelled,
            # its status should have been updated by the last call to add_result.
            # If it's still RUNNING here, it means something went wrong or tasks didn't complete.
            if job.status == JobStatus.RUNNING and not cancelled_by_flag:
                 final_status = JobStatus.FAILED # Assume failure if still running after loop
                 final_errors = list(job.errors)
                 error_msg = f"Job ended unexpectedly while still in RUNNING state. Completed {job.completed_tasks}/{job.total_tasks} tasks."
                 service_logger.error(f"{job_log_prefix} {error_msg}")
                 if error_msg not in final_errors: final_errors.append(error_msg)
                 self.storage.update_job(job_id, status=final_status, errors=final_errors, completed_at=datetime.now(timezone.utc))
                 service_logger.info(f"{job_log_prefix} Core logic finished. Final status forced to: {final_status.value}")
            elif not cancelled_by_flag:
                 # Job status is already COMPLETED or FAILED (set by add_result)
                 service_logger.info(f"{job_log_prefix} Core logic execution finished. Final status already set: {job.status.value}")


        except Exception as e:
            # Catch critical errors during the execution logic itself
            service_logger.exception(f"{job_log_prefix} CRITICAL error during job execution logic: {e}")
            self._handle_thread_exit_error(job_id, f"Critical job logic error: {e}")
            # Cleanup handled by wrapper's finally


    def _generate_task_list(self, job: BatchAnalysisJob) -> List[Tuple[str, int, AnalysisType]]:
        """Generates list of (model, app_num, analysis_type) tasks. Runs within app context."""
        job_log_prefix = f"[{threading.current_thread().name}][Job {job.id}]"
        service_logger.info(f"{job_log_prefix} Generating task list...")
        tasks = []
        if not self.app: service_logger.error(f"{job_log_prefix} Cannot generate task list: Flask app context unavailable."); return []
        base_path_str = current_app.config.get('APP_BASE_PATH')
        if not base_path_str: service_logger.error(f"{job_log_prefix} APP_BASE_PATH not found."); return []
        base_path = Path(base_path_str); service_logger.debug(f"{job_log_prefix} Using base path '{base_path}'.")

        for model in job.models:
            service_logger.debug(f"{job_log_prefix} Processing model '{model}'.")
            model_path = base_path / model
            if not model_path.is_dir(): service_logger.warning(f"{job_log_prefix} Model directory '{model_path}' not found. Skipping."); continue

            # Determine target app numbers (logic duplicated from _calculate_total_tasks, could refactor)
            apps_to_scan_nums = []
            app_range_for_model = job.app_ranges.get(model)
            scan_all_apps = (model in job.app_ranges and isinstance(app_range_for_model, list) and not app_range_for_model)

            if scan_all_apps:
                service_logger.debug(f"{job_log_prefix} Scanning '{model_path}' for all apps.")
                try: apps_to_scan_nums = sorted([int(item.name[3:]) for item in model_path.iterdir() if item.is_dir() and item.name.startswith('app') and item.name[3:].isdigit()])
                except Exception as e: service_logger.error(f"{job_log_prefix} Failed list apps for '{model}': {e}")
                if not apps_to_scan_nums: service_logger.warning(f"{job_log_prefix} No app directories found in '{model_path}'.")
                else: service_logger.debug(f"{job_log_prefix} Found apps: {apps_to_scan_nums}")
            elif isinstance(app_range_for_model, list):
                 apps_to_scan_nums = sorted(list(set(app_range_for_model)))
                 service_logger.debug(f"{job_log_prefix} Using specified apps: {apps_to_scan_nums}")
            else:
                 service_logger.debug(f"{job_log_prefix} No specific app range for '{model}', skipping.")
                 apps_to_scan_nums = []


            # Create tasks, verifying app subdirectories exist
            for app_num in apps_to_scan_nums:
                try:
                    app_dir = get_app_directory(current_app, model, app_num); # Use utility
                    if not app_dir.is_dir(): service_logger.warning(f"{job_log_prefix} App dir missing: {app_dir}. Skipping tasks for this app."); continue
                    # Add tasks for each selected analysis type
                    for analysis_type in job.analysis_types:
                        task_tuple = (model, app_num, analysis_type); tasks.append(task_tuple)
                        service_logger.debug(f"{job_log_prefix} Added task: {(model, app_num, analysis_type.value)}")
                except FileNotFoundError: service_logger.warning(f"{job_log_prefix} App dir not found via util for {model}/app{app_num}. Skipping.")
                except Exception as e: service_logger.error(f"{job_log_prefix} Error processing {model}/app{app_num}: {e}")

        service_logger.info(f"{job_log_prefix} Generated {len(tasks)} tasks.")
        return tasks


    def _analyze_app_task(
        self, job_id: int, model: str, app_num: int, analysis_type: AnalysisType,
        analysis_options: Dict[str, Any], analyzer_service: Any, port_manager_class: Optional[Type[PortManager]]
    ) -> None:
        """
        Performs analysis for a single app/type. Runs in Executor thread.
        Handles internal errors, timeouts, and updates storage.
        **v5:** Added pre-connection check for performance tasks.
        """
        # --- Setup ---
        task_thread_name = threading.current_thread().name
        log_prefix = f"[{task_thread_name}][Job {job_id}][Task {model}/app{app_num}/{analysis_type.value}]"
        task_logger.info(f"{log_prefix} Starting task execution.")

        # --- Cancellation Check ---
        if job_id in self._cancel_flags:
            task_logger.info(f"{log_prefix} Task cancelled before execution started.")
            # Do not add result for cancelled tasks. Job status updated by main loop.
            return

        start_time = datetime.now(timezone.utc)
        status = "failed" # Default status
        result_details = {"error": None, "traceback": None}
        issues_count, high_sev, med_sev, low_sev = 0, 0, 0, 0
        raw_output_preview = None
        task_timed_out = False

        # --- Get Task-Specific Timeout ---
        # Allow overriding default timeout via analysis_options
        type_options = analysis_options.get(analysis_type.value, {})
        task_timeout_seconds = type_options.get("timeout_seconds", self.default_task_timeout)
        task_logger.debug(f"{log_prefix} Using task timeout: {task_timeout_seconds} seconds.")

        # --- Main Execution Block with Timeout ---
        analysis_q = queue.Queue() # Queue to get results back from thread

        def _wait_for_port(host: str, port: int, timeout: int = 30) -> bool:
            """Checks if a port is open and listening."""
            start_wait = time.monotonic()
            while time.monotonic() - start_wait < timeout:
                try:
                    with socket.create_connection((host, port), timeout=1):
                        task_logger.info(f"{log_prefix} Successfully connected to {host}:{port}.")
                        return True
                except (socket.timeout, ConnectionRefusedError, OSError):
                    task_logger.debug(f"{log_prefix} Waiting for {host}:{port} to become available...")
                    time.sleep(2) # Wait before retrying
            task_logger.error(f"{log_prefix} Timeout waiting for {host}:{port} after {timeout} seconds.")
            return False

        def analysis_thread_target():
            """Wrapper function to run the actual analysis logic."""
            try:
                # --- Select and Run Analyzer/Tester ---
                task_logger.debug(f"{log_prefix} Analysis Type: {analysis_type.value}")
                task_logger.debug(f"{log_prefix} Using options: {type_options}")

                # Check service instance (already checked before submit, but double-check)
                if analyzer_service is None and analysis_type not in [AnalysisType.PERFORMANCE]:
                     raise RuntimeError(f"Required analyzer/service instance missing.")
                if analysis_type == AnalysisType.PERFORMANCE and port_manager_class is None:
                     raise RuntimeError(f"PortManager class missing for Performance task.")

                # --- Frontend Security ---
                if analysis_type == AnalysisType.FRONTEND_SECURITY:
                    if not isinstance(analyzer_service, ANALYZER_CLASSES.get('frontend_security')): raise TypeError("Incorrect analyzer: FE Security")
                    full_scan = type_options.get("full_scan", False)
                    task_logger.info(f"{log_prefix} Running frontend security (full_scan={full_scan}).")
                    issues, tool_status, raw_out = analyzer_service.run_security_analysis(model, app_num, use_all_tools=full_scan)
                    analysis_q.put(("success", (issues, tool_status, raw_out)))

                # --- Backend Security ---
                elif analysis_type == AnalysisType.BACKEND_SECURITY:
                    if not isinstance(analyzer_service, ANALYZER_CLASSES.get('backend_security')): raise TypeError("Incorrect analyzer: BE Security")
                    full_scan = type_options.get("full_scan", False)
                    task_logger.info(f"{log_prefix} Running backend security (full_scan={full_scan}).")
                    issues, tool_status, raw_out = analyzer_service.run_security_analysis(model, app_num, use_all_tools=full_scan)
                    analysis_q.put(("success", (issues, tool_status, raw_out)))

                # --- Performance ---
                elif analysis_type == AnalysisType.PERFORMANCE:
                    if not isinstance(analyzer_service, ANALYZER_CLASSES.get('performance')): raise TypeError("Incorrect tester: Performance")
                    users=int(type_options.get('users',10)); duration=int(type_options.get('duration',30)); spawn_rate=int(type_options.get('spawn_rate',1)); endpoints=type_options.get('endpoints', [{"path":"/","method":"GET"}])
                    if not (users > 0 and duration > 0 and spawn_rate > 0): raise ValueError("Performance params must be positive.")
                    task_logger.info(f"{log_prefix} Running performance test: U={users}, D={duration}s, R={spawn_rate}.")
                    # Get Port
                    try:
                        model_idx = get_model_index(model) # Requires utils import
                        if model_idx is None: raise ValueError(f"Model index not found for {model}")
                        ports = port_manager_class.get_app_ports(model_idx, app_num) # Static call
                        if not ports or 'frontend' not in ports: raise ValueError(f"FE port not found for {model}/app{app_num}")
                        # Assuming target is localhost based on previous errors
                        target_host = "localhost"
                        target_port = ports['frontend']
                        host_url = f"http://{target_host}:{target_port}"
                        task_logger.info(f"{log_prefix} Target host URL: {host_url}")
                    except Exception as port_err: raise RuntimeError(f"Port determination failed: {port_err}") from port_err

                    # --- Wait for target app to be available ---
                    task_logger.info(f"{log_prefix} Checking if target app is available at {target_host}:{target_port}...")
                    if not _wait_for_port(target_host, target_port, timeout=30):
                         raise RuntimeError(f"Target application {model}/app{app_num} did not respond on {target_host}:{target_port} within 30s.")
                    task_logger.info(f"{log_prefix} Target app responded. Starting Locust test...")

                    # Run Test
                    perf_result = analyzer_service.run_test_library(
                        test_name=f"batch_{job_id}_{model}_{app_num}", host=host_url, endpoints=endpoints,
                        user_count=users, spawn_rate=spawn_rate, run_time=duration, generate_graphs=True,
                        model=model, app_num=app_num
                    )
                    if perf_result is None: raise RuntimeError("Performance test run_test_library returned None.")
                    analysis_q.put(("success", perf_result)) # Pass result object

                # --- GPT4All ---
                elif analysis_type == AnalysisType.GPT4ALL:
                    if not isinstance(analyzer_service, ANALYZER_CLASSES.get('gpt4all')): raise TypeError("Incorrect analyzer: GPT4All")
                    requirements = type_options.get('requirements')
                    if not requirements: # Load defaults if none provided
                        try:
                            # Assuming get_requirements_for_app works without direct context if paths are resolvable
                            requirements, template_name = analyzer_service.get_requirements_for_app(app_num)
                            task_logger.info(f"{log_prefix} Loaded {len(requirements)} default requirements from '{template_name}'.")
                        except Exception as req_err: raise RuntimeError(f"Could not load requirements: {req_err}") from req_err
                    if not requirements:
                         task_logger.warning(f"{log_prefix} No requirements found, skipping analysis.")
                         analysis_q.put(("skipped", "No requirements provided or found."))
                    else:
                        task_logger.info(f"{log_prefix} Running GPT4All analysis with {len(requirements)} requirements.")
                        gpt_results = analyzer_service.check_requirements(model, app_num, requirements)
                        analysis_q.put(("success", gpt_results)) # Pass list of RequirementCheck objects

                # --- ZAP ---
                elif analysis_type == AnalysisType.ZAP:
                    if not isinstance(analyzer_service, ANALYZER_CLASSES.get('zap')): raise TypeError("ScanManager instance expected for ZAP")
                    task_logger.info(f"{log_prefix} Triggering ZAP scan via ScanManager.")
                    # Trigger scan
                    scan_id = analyzer_service.create_scan(model, app_num, type_options)
                    if not scan_id: raise RuntimeError("ScanManager failed to return a scan ID.")
                    task_logger.info(f"{log_prefix} ZAP scan triggered. Scan ID: {scan_id}. Waiting for completion...")

                    # Poll for completion
                    poll_interval = 15 # seconds
                    max_polls = int(task_timeout_seconds / poll_interval) # Calculate max polls based on overall task timeout
                    zap_status = None
                    for poll_num in range(max_polls):
                         # Check cancellation flag during polling
                         if job_id in self._cancel_flags:
                              task_logger.info(f"{log_prefix} ZAP task cancelled during polling.")
                              raise InterruptedError("ZAP task cancelled") # Raise specific error

                         time.sleep(poll_interval)
                         try:
                              zap_status = analyzer_service.get_scan_status(scan_id)
                              task_logger.debug(f"{log_prefix} ZAP poll {poll_num+1}/{max_polls}: Status={zap_status.get('status', 'unknown')}, Progress={zap_status.get('progress', '?')}%")
                              if zap_status.get('status') == 'completed':
                                   task_logger.info(f"{log_prefix} ZAP scan {scan_id} completed.")
                                   break
                              elif zap_status.get('status') == 'failed':
                                   error_msg = zap_status.get('error', 'Unknown ZAP failure')
                                   task_logger.error(f"{log_prefix} ZAP scan {scan_id} failed: {error_msg}")
                                   raise RuntimeError(f"ZAP scan failed: {error_msg}")
                         except Exception as poll_err:
                              task_logger.warning(f"{log_prefix} Error polling ZAP status for scan {scan_id}: {poll_err}. Continuing poll.")
                    else: # Loop finished without break (i.e., timeout)
                         task_logger.error(f"{log_prefix} ZAP scan {scan_id} did not complete within task timeout ({task_timeout_seconds}s).")
                         raise TimeoutError(f"ZAP scan timed out after {task_timeout_seconds}s")

                    # Retrieve results
                    task_logger.info(f"{log_prefix} Retrieving ZAP results for scan {scan_id}...")
                    zap_results = analyzer_service.get_scan_results(scan_id) # Assume this returns List[ZapVulnerability] or similar
                    if zap_results is None: # Handle case where results retrieval fails
                         raise RuntimeError("Failed to retrieve ZAP results after scan completion.")

                    task_logger.info(f"{log_prefix} Retrieved {len(zap_results)} ZAP alerts.")
                    # Pass results to the main thread via queue
                    # Include scan_id and status in payload for context
                    analysis_q.put(("success", (zap_results, zap_status)))

                # --- Unknown Type ---
                else:
                    raise ValueError(f"Unsupported analysis type: {analysis_type.value}")

            except InterruptedError as cancel_err:
                 # Catch cancellation specifically
                 analysis_q.put(("cancelled", str(cancel_err)))
            except Exception as thread_err:
                # Catch errors from within the analysis logic
                analysis_q.put(("error", thread_err, traceback.format_exc()))

        # Start the analysis in a separate thread
        analysis_thread = threading.Thread(target=analysis_thread_target, daemon=True)
        analysis_thread.start()

        # Wait for the result or timeout
        try:
            q_status, q_payload, *q_tb = analysis_q.get(timeout=task_timeout_seconds)
            task_logger.debug(f"{log_prefix} Analysis thread completed with status: {q_status}")

            if q_status == "success":
                status = "completed" # Mark as completed now
                # Process successful result based on analysis type
                if analysis_type in [AnalysisType.FRONTEND_SECURITY, AnalysisType.BACKEND_SECURITY]:
                    issues, tool_status, raw_output = q_payload
                    analyzer_instance = analyzer_service # Use passed instance
                    summary = analyzer_instance.get_analysis_summary(issues)
                    issues_count = len(issues); high_sev=summary.get("severity_counts",{}).get("HIGH",0); med_sev=summary.get("severity_counts",{}).get("MEDIUM",0); low_sev=summary.get("severity_counts",{}).get("LOW",0)
                    # FIX: Properly serialize issues using correct method for each analyzer type
                    serializable_issues = []
                    for issue in issues:
                         if hasattr(issue, 'to_dict') and callable(issue.to_dict):
                             # Use to_dict method if available (better than asdict for custom serialization)
                             serializable_issues.append(issue.to_dict())
                         elif hasattr(issue, '__dataclass_fields__'):
                             # Fallback to asdict for standard dataclasses
                             serializable_issues.append(asdict(issue))
                         else:
                             # Last resort: try to convert to dict directly, logging a warning
                             task_logger.warning(f"{log_prefix} Issue of type {type(issue)} has no to_dict method or is not a dataclass")
                             try:
                                 serializable_issues.append(dict(issue))
                             except Exception as err:
                                 task_logger.error(f"{log_prefix} Could not serialize issue: {err}")
                                 # Include a minimal representation to avoid losing the issue
                                 serializable_issues.append({"issue_text": str(issue), "severity": "UNKNOWN"})

                    result_details.update({
                        "issues": serializable_issues,
                        "summary": summary,
                        "tool_status": tool_status
                    })
                    raw_output_preview = str(raw_output) if raw_output else None

                elif analysis_type == AnalysisType.PERFORMANCE:
                    perf_result = q_payload # PerformanceResult object
                    perf_dict = perf_result.to_dict()
                    issues_count = perf_dict.get('total_failures', 0)
                    result_details.update(perf_dict)
                    try: raw_output_preview = json.dumps(perf_dict, indent=2)
                    except Exception: raw_output_preview = str(perf_dict)

                elif analysis_type == AnalysisType.GPT4ALL:
                    gpt_results = q_payload # List of RequirementCheck objects
                    # FIX: Properly serialize GPT4All results
                    issues_list = []
                    for res in gpt_results:
                        if hasattr(res, 'to_dict') and callable(res.to_dict):
                            issues_list.append(res.to_dict())
                        else:
                            # Fallback
                            if hasattr(res, '__dataclass_fields__'):
                                issues_list.append(asdict(res))
                            else:
                                issues_list.append({"requirement": str(res)})

                    met_count = sum(1 for r in issues_list if r.get('result', {}).get('met', False))
                    summary = {"requirements_checked": len(issues_list), "met_count": met_count}
                    task_logger.debug(f"{log_prefix} GPT4All Summary: {summary}")
                    result_details.update({"issues": issues_list, "summary": summary})
                    issues_count = len(issues_list)
                    try: raw_output_preview = json.dumps(issues_list, indent=2)
                    except Exception: raw_output_preview = str(issues_list)

                elif analysis_type == AnalysisType.ZAP:
                    zap_alerts, zap_status_info = q_payload # Get alerts and final status
                    # Convert ZapVulnerability objects (or dicts) to serializable dicts
                    serializable_alerts = []
                    if ZapVulnerability: # Check if class was imported
                         severity_map = {"High": 0, "Medium": 1, "Low": 2, "Informational": 3}
                         for alert in zap_alerts:
                              if isinstance(alert, ZapVulnerability):
                                   alert_dict = asdict(alert)
                                   # Convert CodeContext if present
                                   if alert.affected_code and hasattr(alert.affected_code, '__dataclass_fields__'):
                                        alert_dict['affected_code'] = asdict(alert.affected_code)
                                   serializable_alerts.append(alert_dict)
                                   # Count severity
                                   risk = alert.risk
                                   if risk == "High": high_sev += 1
                                   elif risk == "Medium": med_sev += 1
                                   elif risk == "Low": low_sev += 1
                              elif isinstance(alert, dict): # Handle if results are already dicts
                                   serializable_alerts.append(alert)
                                   risk = alert.get("risk")
                                   if risk == "High": high_sev += 1
                                   elif risk == "Medium": med_sev += 1
                                   elif risk == "Low": low_sev += 1

                    issues_count = len(serializable_alerts)
                    result_details.update({"issues": serializable_alerts, "zap_status": zap_status_info})
                    raw_output_preview = f"ZAP scan completed. Found {issues_count} alerts. High: {high_sev}, Medium: {med_sev}, Low: {low_sev}."
                    task_logger.info(f"{log_prefix} ZAP results processed.")


            elif q_status == "skipped":
                status = "skipped"
                result_details["error"] = str(q_payload)
                task_logger.info(f"{log_prefix} Task skipped: {q_payload}")
            elif q_status == "cancelled":
                 # Handle cancellation detected within the thread
                 status = "failed" # Treat cancellation as failure for reporting
                 error_message = f"Task cancelled during execution: {q_payload}"
                 task_logger.info(f"{log_prefix} {error_message}")
                 result_details["error"] = error_message
                 result_details["traceback"] = "Task cancelled by user request."
            elif q_status == "error":
                # Error occurred within the analysis thread
                task_err = q_payload
                detailed_traceback = q_tb[0] if q_tb else ""
                error_message = f"Task failed internally: {type(task_err).__name__} - {str(task_err)}"
                task_logger.error(f"{log_prefix} {error_message}", exc_info=False)
                task_logger.debug(f"{log_prefix} Internal task traceback:\n{detailed_traceback}")
                status = "failed"
                result_details["error"] = error_message
                result_details["traceback"] = detailed_traceback

        except queue.Empty:
            # Timeout occurred waiting for queue result
            task_timed_out = True
            status = "timed_out"
            error_message = f"Task timed out after {task_timeout_seconds} seconds."
            task_logger.error(f"{log_prefix} {error_message}")
            result_details["error"] = error_message
            # Optionally try to interrupt the thread (may not work for all blocking calls)
            # Note: Interrupting threads forcefully is generally unsafe in Python.
            # Rely on the timeout mechanism and reporting.

        except Exception as e:
            # Catch unexpected errors in the result processing logic itself
            error_message = f"Result processing failed: {type(e).__name__} - {str(e)}"
            detailed_traceback = traceback.format_exc()
            task_logger.exception(f"{log_prefix} Error processing task result: {e}")
            status = "failed" # Ensure status is failed
            result_details["error"] = error_message
            result_details["traceback"] = detailed_traceback

        # --- Record Result (Finally Block) ---
        finally:
            task_logger.debug(f"{log_prefix} Entering finally block for task result recording.")
            # Check cancellation flag *again* right before adding result
            if job_id in self._cancel_flags:
                task_logger.info(f"{log_prefix} Skipped adding result to storage due to cancellation flag.")
            else:
                end_time = datetime.now(timezone.utc)
                # Add raw output preview if available
                if raw_output_preview:
                    preview = raw_output_preview[:1500] # Truncate
                    if len(raw_output_preview) > 1500: preview += "\n...(truncated)"
                    result_details["raw_output_preview"] = preview
                else:
                    result_details["raw_output_preview"] = None

                # Prepare final result payload
                result_payload = {
                    "model": model, "app_num": app_num, "analysis_type": analysis_type,
                    "status": status, # Final determined status
                    "issues_count": issues_count, "high_severity": high_sev,
                    "medium_severity": med_sev, "low_severity": low_sev,
                    "scan_start_time": start_time, "scan_end_time": end_time,
                    "details": result_details # Includes error/traceback/preview
                }
                task_logger.info(f"{log_prefix} Adding result to storage (Status: {status}).")
                try:
                    # Call storage to add result and update job progress/summary
                    add_success = self.storage.add_result(job_id, result_payload)
                    if add_success: task_logger.debug(f"{log_prefix} Result storage successful.")
                    else: task_logger.error(f"{log_prefix} Failed to add result to storage (storage.add_result returned None/False).")
                except Exception as storage_err:
                    task_logger.exception(f"{log_prefix} CRITICAL: Exception occurred while adding result to storage: {storage_err}")

            # Log task finish regardless of result storage outcome
            task_logger.info(f"{log_prefix} Task execution thread finished.")


    def cancel_job(self, job_id: int) -> bool:
        """Marks a running job for cancellation. Thread-safe."""
        job_log_prefix = f"[Job {job_id}]"
        service_logger.info(f"{job_log_prefix} Received request to cancel job.")
        with self.storage._lock:
            job = self.storage.get_job(job_id)
            if not job: service_logger.error(f"{job_log_prefix} Cannot cancel: Job not found."); return False
            if job.status != JobStatus.RUNNING: service_logger.warning(f"{job_log_prefix} Cannot cancel: Not running (Status: {job.status.value})."); return False
            if job_id in self._cancel_flags: service_logger.info(f"{job_log_prefix} Job already marked for cancellation."); return True

            service_logger.debug(f"{job_log_prefix} Adding job to cancel flags set: {self._cancel_flags}")
            self._cancel_flags.add(job_id)
            service_logger.info(f"{job_log_prefix} Job successfully marked for cancellation. Runner thread will handle status update.")
            # The runner thread (_run_job_logic) is responsible for detecting the flag,
            # attempting to stop tasks (via future.cancel), and setting the final CANCELED status.
        return True

    def get_job_status(self, job_id: int) -> Dict[str, Any]:
        """Retrieves detailed status information for a specific job."""
        job_log_prefix = f"[Job {job_id}]"
        service_logger.debug(f"{job_log_prefix} Request get job status.")
        job = self.storage.get_job(job_id)
        if not job:
            service_logger.warning(f"{job_log_prefix} Get status failed: Job not found.")
            return {"error": f"Job {job_id} not found"}

        # Calculate progress
        progress_percent = 0
        if job.total_tasks > 0:
            completed = min(job.completed_tasks, job.total_tasks) # Cap completed at total
            progress_percent = int((completed / job.total_tasks) * 100)
        elif job.status in [JobStatus.COMPLETED, JobStatus.CANCELED]: # Show 100 if finished/cancelled
             progress_percent = 100
        elif job.status == JobStatus.FAILED and job.total_tasks == 0: # Show 0 if failed due to 0 tasks
             progress_percent = 0

        service_logger.debug(f"{job_log_prefix} Progress: {job.completed_tasks}/{job.total_tasks} ({progress_percent}%)")
        results_summary = job.results_summary
        service_logger.debug(f"{job_log_prefix} Results summary keys: {list(results_summary.keys())}")

        # Prepare response using job's serializer
        job_dict = job.to_dict()
        status_response = {
            "job": job_dict,
            "progress": {
                "total": job.total_tasks,
                "completed": job.completed_tasks, # Use actual completed count here
                "percent": progress_percent
            },
            "results_summary": results_summary,
        }
        service_logger.debug(f"{job_log_prefix} Returning status response.")
        return status_response

    # --- Private Helper Methods for Thread Management ---
    def _handle_thread_exit_error(self, job_id: int, error_message: str):
        """Handles job failure when the execution thread exits unexpectedly."""
        job_log_prefix = f"[Job {job_id}]"
        service_logger.error(f"{job_log_prefix} Thread exited with error: {error_message}")
        try:
            with self.storage._lock:
                job = self.storage.get_job(job_id)
                current_errors = job.errors if job else []
                full_error_msg = f"Job thread error: {error_message}"
                if full_error_msg not in current_errors: current_errors.append(full_error_msg)
                # Update job status regardless of whether job object was retrieved
                self.storage.update_job(job_id,
                                        status=JobStatus.FAILED,
                                        errors=current_errors,
                                        completed_at=datetime.now(timezone.utc))
                service_logger.info(f"{job_log_prefix} Updated job status to FAILED due to thread error.")
        except Exception as update_err:
            service_logger.exception(f"{job_log_prefix} CRITICAL: Failed to update job status after thread error: {update_err}")

    def _cleanup_after_job_thread(self, job_id: int):
        """Removes job ID from running jobs dict and cancel flags. Thread-safe."""
        job_log_prefix = f"[Job {job_id}]"
        service_logger.debug(f"{job_log_prefix} Performing post-thread cleanup.")
        with self.storage._lock:
            if job_id in self._running_jobs:
                del self._running_jobs[job_id]
                service_logger.debug(f"{job_log_prefix} Removed job from running jobs list. Remaining: {list(self._running_jobs.keys())}")
            if job_id in self._cancel_flags:
                self._cancel_flags.remove(job_id)
                service_logger.debug(f"{job_log_prefix} Removed cancel flag for job. Current flags: {self._cancel_flags}")
        service_logger.debug(f"{job_log_prefix} Post-thread cleanup finished.")


# Global instance of the service
batch_service = BatchAnalysisService(job_storage)
logger.debug("Global batch_service instance created.")


# =============================================================================
# Route Helper Functions & Decorators
# =============================================================================
def error_handler(f):
    """Decorator for handling common exceptions in Flask routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        err_logger = route_logger
        route_name = f.__name__; path = request.path
        err_logger.debug(f"Route '{route_name}' ({path}): Entering error handler.")
        try:
            err_logger.debug(f"Route '{route_name}': Executing function.")
            result = f(*args, **kwargs)
            err_logger.debug(f"Route '{route_name}': Function executed successfully.")
            return result
        except (BadRequest, NotFound) as client_err:
            err_logger.warning(f"Route '{route_name}': Client Error {client_err.code} - {client_err.description}")
            # For API routes (JSON response), handle explicitly or let Flask handle for HTML
            if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
                 return jsonify(error=client_err.description, code=client_err.code), client_err.code
            else:
                 flash(f"{client_err.code}: {client_err.description}", "error")
                 # Redirect to a safe page or re-raise for Flask's default handler
                 if client_err.code == 404: return redirect(url_for("batch_analysis.batch_dashboard"))
                 raise client_err # Let Flask handle other client errors for HTML
        except InternalServerError as server_err:
            err_logger.error(f"Route '{route_name}': Internal Server Error {server_err.code} - {server_err.description}", exc_info=True)
            if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
                 return jsonify(error="An internal server error occurred.", code=500), 500
            else:
                 flash("An internal server error occurred. Please check logs.", "error")
                 return redirect(url_for("batch_analysis.batch_dashboard")) # Redirect to dashboard
        except Exception as e:
            err_logger.exception(f"Route '{route_name}': Unhandled exception caught: {type(e).__name__} - {e}")
            if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
                 return jsonify(error=f"An unexpected error occurred: {type(e).__name__}", code=500), 500
            else:
                 flash(f"An unexpected error occurred: {type(e).__name__}. Please check logs.", "error")
                 return redirect(url_for("batch_analysis.batch_dashboard"))
    return decorated_function

def get_available_models() -> List[str]:
    """Retrieves the list of available AI models."""
    logger.debug("Attempting to get available models list.")
    try:
        # Try loading from utils.AI_MODELS first (assumed to be list of strings or objects with .name)
        if isinstance(AI_MODELS, list) and AI_MODELS:
            if isinstance(AI_MODELS[0], str): model_names = sorted(AI_MODELS)
            elif hasattr(AI_MODELS[0], 'name'): model_names = sorted([m.name for m in AI_MODELS])
            else: raise TypeError("Unsupported AI_MODELS structure in utils.py")
            logger.info(f"Loaded {len(model_names)} models from utils.AI_MODELS.")
            return model_names
        else:
            logger.warning("utils.AI_MODELS found but is empty or invalid. Falling back to dir scan.")
    except (NameError, AttributeError, TypeError, Exception) as e:
        logger.warning(f"Could not load AI_MODELS from utils ({type(e).__name__}: {e}). Falling back.")

    # Fallback: Scan APP_BASE_PATH directory
    try:
        flask_app = current_app._get_current_object()
        if not flask_app: raise RuntimeError("Flask app context unavailable for dir scan.")
        base_path_str = flask_app.config.get('APP_BASE_PATH')
        if not base_path_str: raise ValueError("APP_BASE_PATH not in config.")
        base_path = Path(base_path_str)
        if not base_path.is_dir(): raise FileNotFoundError(f"APP_BASE_PATH '{base_path}' invalid.")

        model_names = sorted([item.name for item in base_path.iterdir() if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('_')])
        logger.info(f"Found {len(model_names)} models by scanning {base_path}.")
        return model_names
    except (RuntimeError, ValueError, FileNotFoundError, Exception) as e:
        logger.error(f"Failed to list models from directory scan: {e}", exc_info=True)
        return []

def parse_app_range(range_str: str) -> List[int]:
    """Parses comma-separated numbers/ranges (e.g., "1-3,5,8") into list[int]."""
    logger.debug(f"Parsing app range string: '{range_str}'")
    app_nums: Set[int] = set()
    if not range_str or not range_str.strip(): return [] # Return empty list for empty input

    parts = range_str.split(',')
    for part in parts:
        part = part.strip()
        if not part: continue
        if '-' in part: # Handle ranges "1-5"
            try:
                start_str, end_str = part.split('-', 1)
                start = int(start_str.strip()); end = int(end_str.strip())
                if start <= end and start > 0: # Ensure positive range
                    app_nums.update(range(start, end + 1))
                else: logger.warning(f"Invalid range '{part}', start/end must be positive, start <= end. Skipping.")
            except ValueError: logger.warning(f"Invalid range format '{part}'. Skipping.")
            except Exception as e: logger.warning(f"Error parsing range part '{part}': {e}")
        else: # Handle single numbers
            try:
                num = int(part)
                if num > 0: app_nums.add(num) # Ensure positive app number
                else: logger.warning(f"Invalid app number '{part}', must be positive. Skipping.")
            except ValueError: logger.warning(f"Invalid app number '{part}'. Skipping.")
            except Exception as e: logger.warning(f"Error parsing single number part '{part}': {e}")

    sorted_list = sorted(list(app_nums))
    logger.debug(f"Final parsed app numbers for '{range_str}': {sorted_list}")
    return sorted_list

# =============================================================================
# Flask Routes
# =============================================================================
@batch_analysis_bp.route("/")
@error_handler
def batch_dashboard():
    """Displays the main dashboard for batch analysis jobs."""
    route_logger.info(f"Request received for Batch Dashboard ({request.path})")
    jobs_list = sorted(job_storage.get_all_jobs(), key=lambda j: j.created_at, reverse=True)
    jobs_dict_list = [job.to_dict() for job in jobs_list] # Convert for template
    all_models = get_available_models()
    stats = {status.value: 0 for status in JobStatus}
    for job in jobs_list: stats[job.status.value] = stats.get(job.status.value, 0) + 1
    route_logger.info("Rendering batch_dashboard.html template.")
    return render_template("batch_dashboard.html", jobs=jobs_dict_list, all_models=all_models,
                           stats=stats, JobStatus=JobStatus, AnalysisType=AnalysisType)

@batch_analysis_bp.route("/create", methods=["GET", "POST"])
@error_handler
def create_batch_job():
    """Handles creation of a new batch analysis job."""
    route_logger.info(f"Request: Create Batch Job ({request.path}, Method: {request.method})")
    all_models = get_available_models()
    analysis_types_available = list(AnalysisType)

    if request.method == "POST":
        route_logger.info("Processing POST request to create batch job.")
        route_logger.debug(f"Form data: {request.form.to_dict(flat=False)}")

        try:
            selected_models = request.form.getlist("models")
            if not selected_models: raise BadRequest("Please select at least one model.")

            selected_analysis_types_str = request.form.getlist("analysis_types")
            selected_analysis_types = [AnalysisType(s) for s in selected_analysis_types_str]
            if not selected_analysis_types: raise BadRequest("Please select at least one analysis type.")

            # Parse app ranges for selected models only
            app_ranges_parsed = {}
            for m in selected_models:
                 range_str = request.form.get(f"app_range_{m}", "").strip()
                 # Empty string means scan all apps for this model -> store empty list
                 app_ranges_parsed[m] = parse_app_range(range_str) if range_str else []


            # Collect all possible options, validate types/values
            all_options = {}
            try:
                sec_scan = request.form.get("security_full_scan") == "on"
                all_options[AnalysisType.FRONTEND_SECURITY.value] = {"full_scan": sec_scan}
                all_options[AnalysisType.BACKEND_SECURITY.value] = {"full_scan": sec_scan}

                perf_u=int(request.form.get("perf_users",10)); perf_d=int(request.form.get("perf_duration",30)); perf_sr=int(request.form.get("perf_spawn_rate",1))
                if not (perf_u > 0 and perf_d > 0 and perf_sr > 0): raise ValueError("Perf params must be > 0.")
                all_options[AnalysisType.PERFORMANCE.value]={"users":perf_u,"duration":perf_d,"spawn_rate":perf_sr,"endpoints":[{"path":"/","method":"GET"}]} # Add more endpoint config later if needed

                # GPT4All options (e.g., requirements file path or content) could be added here
                all_options[AnalysisType.GPT4ALL.value] = {"requirements": None} # Placeholder

                zap_qs = request.form.get("zap_quick_scan") == "on"
                all_options[AnalysisType.ZAP.value] = {"quick_scan": zap_qs}

                # Add timeout override option
                timeout_override = request.form.get("task_timeout_override", "").strip()
                if timeout_override:
                    timeout_sec = int(timeout_override)
                    if timeout_sec <= 0: raise ValueError("Timeout override must be > 0.")
                    # Add timeout to options for *all* selected types if provided
                    for atype_enum in selected_analysis_types:
                         if atype_enum.value in all_options:
                              all_options[atype_enum.value]["timeout_seconds"] = timeout_sec
                         else: # Handle case where type might not have other options (like GPT4All)
                              all_options[atype_enum.value] = {"timeout_seconds": timeout_sec}
                    route_logger.info(f"Applying task timeout override: {timeout_sec}s")

            except ValueError as opt_val_err: raise BadRequest(f"Invalid analysis option value: {opt_val_err}")

            # Filter options based on *selected* analysis types (FIXED from v2)
            final_analysis_options = {
                atype.value: all_options[atype.value]
                for atype in selected_analysis_types if atype.value in all_options
            }
            route_logger.debug(f"Final analysis options for job: {final_analysis_options}")

            job_data = {
                "name": request.form.get("name", "").strip() or f"Batch Scan - {datetime.now():%F %T}",
                "description": request.form.get("description", "").strip(),
                "models": selected_models,
                "app_ranges": app_ranges_parsed, # Pass dict: model -> list[int] (empty list means all)
                "analysis_types": selected_analysis_types, # Pass list of Enums
                "analysis_options": final_analysis_options # Pass correctly filtered options
            }
            route_logger.info(f"Job data prepared for creation.")

        except (BadRequest, ValueError, TypeError) as form_err:
            route_logger.warning(f"Form validation failed: {form_err}")
            flash(str(form_err), "error")
            return render_template("create_batch_job.html", models=all_models, analysis_types=analysis_types_available, submitted_data=request.form), 400

        # --- Job Creation and Start ---
        try:
            route_logger.debug("Calling job_storage.create_job...")
            # Pass current_app context needed for task calculation inside create_job
            job = job_storage.create_job(job_data, current_app._get_current_object())
            job_log_prefix = f"[Job {job.id}]"
            route_logger.info(f"{job_log_prefix} Created successfully in storage.")

            success = batch_service.start_job(job.id) # Handles its own logging

            if success:
                flash(f"Job '{job.name}' (ID:{job.id}) submitted & started.", "success")
            else:
                # If start_job returns false, retrieve job to get error reason (already flashed by start_job usually)
                job = job_storage.get_job(job.id) # Re-fetch job
                reason = job.errors[-1] if job and job.errors else "Check logs."
                flash(f"Job '{job.name}' (ID:{job.id}) submitted but start failed: {reason}", "warning") # Flash again for certainty
                route_logger.warning(f"{job_log_prefix} Job submitted but failed start: {reason}")

            redir_url = url_for("batch_analysis.batch_dashboard")
            route_logger.info(f"{job_log_prefix} Redirecting to dashboard: {redir_url}")
            return redirect(redir_url)

        except (ValueError, TypeError) as create_err: # Catch specific errors from create_job validation
            route_logger.error(f"Create/Start error: {create_err}", exc_info=True)
            flash(f"Create error: {create_err}", "error")
            return render_template("create_batch_job.html", models=all_models, analysis_types=analysis_types_available, submitted_data=request.form), 400
        # Let main error_handler catch other unexpected exceptions

    # --- GET Request ---
    route_logger.info("Displaying create batch job form (GET request).")
    default_job_name = f"Batch Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    return render_template("create_batch_job.html", models=all_models, analysis_types=analysis_types_available, default_job_name=default_job_name)


@batch_analysis_bp.route("/job/<int:job_id>")
@error_handler
def view_job(job_id: int):
    """Displays the detailed view for a specific batch job."""
    job_log_prefix=f"[Job {job_id}]"; route_logger.info(f"{job_log_prefix} Req View Job")
    status_data = batch_service.get_job_status(job_id) # Gets job dict, progress, summary
    if "error" in status_data: raise NotFound(status_data["error"]) # Let error_handler manage response

    results_list = sorted(job_storage.get_results(job_id), key=lambda r: (r.model, r.app_num, r.analysis_type.value))
    results_dict_list = [r.to_dict() for r in results_list] # Convert results for template
    route_logger.info(f"{job_log_prefix} Found {len(results_dict_list)} results.")

    job_info_dict = status_data.get('job')
    if not job_info_dict: route_logger.error(f"{job_log_prefix} Missing 'job' dict in status!"); raise InternalServerError("Job info missing.")

    return render_template("view_job.html", job=job_info_dict, status_data=status_data,
                           results=results_dict_list, JobStatus=JobStatus, AnalysisType=AnalysisType)

@batch_analysis_bp.route("/job/<int:job_id>/status")
@error_handler
def get_job_status_api(job_id: int):
    """API endpoint to get the status of a specific job (JSON)."""
    job_log_prefix=f"[Job {job_id}]"; route_logger.info(f"{job_log_prefix} API req status.")
    status_data = batch_service.get_job_status(job_id)
    if "error" in status_data: raise NotFound(status_data["error"]) # Raise 404 for API
    return jsonify(status_data)

@batch_analysis_bp.route("/job/<int:job_id>/cancel", methods=["POST"])
@error_handler
def cancel_job_api(job_id: int):
    """API endpoint to cancel a running job."""
    job_log_prefix=f"[Job {job_id}]"; route_logger.info(f"{job_log_prefix} API req cancel.")
    success = batch_service.cancel_job(job_id)
    if success: return jsonify({"success": True, "status": "canceling", "message": "Job marked for cancellation."})
    else:
        # Provide specific reason for failure
        job = job_storage.get_job(job_id)
        if not job: raise NotFound(f"Job {job_id} not found.")
        elif job.status != JobStatus.RUNNING: raise BadRequest(f"Job not running (status: {job.status.value}).")
        else: raise InternalServerError("Cancel request failed unexpectedly.") # Should be rare

@batch_analysis_bp.route("/job/<int:job_id>/delete", methods=["POST"])
@error_handler
def delete_job_api(job_id: int):
    """API endpoint to delete a completed/failed/canceled job."""
    job_log_prefix=f"[Job {job_id}]"; route_logger.info(f"{job_log_prefix} API req delete.")
    # Check status before attempting delete
    job = job_storage.get_job(job_id) # Check existence first
    if not job: raise NotFound(f"Delete fail: Job {job_id} not found.")
    if job.status == JobStatus.RUNNING: raise BadRequest("Cannot delete a running job. Cancel it first.")

    success = job_storage.delete_job(job_id) # Attempt deletion

    if success:
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        if not is_ajax: flash(f"Job {job_id} deleted.", "success"); return redirect(url_for("batch_analysis.batch_dashboard"))
        else: return jsonify({"success": True, "message": f"Job {job_id} deleted."})
    else:
        # If delete failed, check *why* (e.g., job disappeared between check and delete?)
        if not job_storage.get_job(job_id): raise NotFound(f"Delete fail: Job {job_id} not found (disappeared?).")
        else: raise InternalServerError("Delete failed unexpectedly.")


@batch_analysis_bp.route("/result/<int:result_id>")
@error_handler
def view_result(result_id: int):
    """Displays the detailed view for a specific task result."""
    res_log_prefix = f"[Result {result_id}]"; route_logger.info(f"{res_log_prefix} Req View Result");
    result = job_storage.get_result(result_id)
    if not result: raise NotFound(f"Result {result_id} not found.")

    job = job_storage.get_job(result.job_id)
    if not job: route_logger.error(f"{res_log_prefix} Parent Job {result.job_id} missing!"); raise InternalServerError("Parent job missing.")

    try: job_dict = job.to_dict(); result_dict = result.to_dict()
    except Exception as ser_err: route_logger.exception(f"{res_log_prefix} Serialize err: {ser_err}"); raise InternalServerError("Data prep error.")

    return render_template("view_result.html", result=result_dict, job=job_dict,
                           AnalysisType=AnalysisType, JobStatus=JobStatus)

# =============================================================================
# Module Initialization & Helpers
# =============================================================================
def init_batch_analysis(app: flask.Flask):
    """Initializes the batch analysis module."""
    logger.info("Initializing Batch Analysis Module...")
    base_path_key = 'APP_BASE_PATH'
    # Ensure APP_BASE_PATH is configured
    if base_path_key not in app.config or not app.config[base_path_key]:
        default_path = Path(app.config.get('BASE_DIR', Path(app.root_path).parent))
        app.config[base_path_key] = default_path
        logger.warning(f"{base_path_key} not configured. Using default: {app.config[base_path_key]}")
    else:
        app.config[base_path_key] = Path(app.config[base_path_key]) # Ensure Path object
    logger.info(f"Effective {base_path_key}: {app.config[base_path_key]}")

    # Register App with Service (critical for background context)
    try: batch_service.set_app(app)
    except Exception as service_reg_err: logger.exception(f"CRITICAL: Failed to register Flask app with BatchAnalysisService: {service_reg_err}")

    # Add Jinja Helpers
    logger.debug("Adding helpers/globals to Jinja environment.")
    try:
        # *** FIX: Register as filter, not global ***
        app.jinja_env.filters['humanize_duration'] = humanize_duration
        # Register globals
        app.jinja_env.globals.update(AnalysisType=AnalysisType)
        app.jinja_env.globals.update(JobStatus=JobStatus)
        app.jinja_env.globals.update(now_utc=lambda: datetime.now(timezone.utc)) # UTC now
        logger.debug("Jinja helpers/filters added successfully.")
    except Exception as jinja_err: logger.error(f"Failed to add Jinja helpers/filters: {jinja_err}")

    # --- Log Checks for Required Services ---
    logger.debug("Checking for required service instances on app context...")
    service_attr_map = {
        AnalysisType.FRONTEND_SECURITY: 'frontend_security_analyzer',
        AnalysisType.BACKEND_SECURITY: 'backend_security_analyzer',
        AnalysisType.PERFORMANCE: 'performance_tester',
        AnalysisType.GPT4ALL: 'gpt4all_analyzer',
        AnalysisType.ZAP: 'scan_manager'
    }
    required_attrs = { atype.value: service_attr_map[atype] for atype in AnalysisType if atype in service_attr_map }
    missing = [f"{attr} (for {atype})" for atype, attr in required_attrs.items() if not hasattr(app, attr) or getattr(app, attr) is None]
    if missing: logger.error(f"Flask app context MISSING services for Batch Analysis: {', '.join(missing)}. Related tasks WILL fail.")
    else: logger.info("All required service attributes found on app context.")
    if PortManager is None: logger.error("PortManager class unavailable. Performance tasks WILL fail.")
    else: logger.info("PortManager class is available.")

    logger.info("Batch Analysis Module initialized.")


def humanize_duration(seconds: Optional[Union[int, float]]) -> str:
    """Converts seconds into a human-readable string (Xs, Xm Ys, Xh Ym)."""
    if seconds is None or not isinstance(seconds, (int, float)) or seconds < 0: return "N/A"
    try:
        delta = timedelta(seconds=int(seconds))
        if delta < timedelta(minutes=1): return f"{delta.seconds}s"
        elif delta < timedelta(hours=1):
             m, s = divmod(delta.seconds, 60)
             return f"{m}m {s}s"
        else:
             h, remainder = divmod(delta.seconds, 3600)
             m, s = divmod(remainder, 60)
             # Add days if needed: d = delta.days ... f"{d}d {h}h {m}m"
             return f"{h}h {m}m" # Simplified H:M format
    except (ValueError, TypeError):
        logger.warning(f"Could not humanize duration for value: {seconds}", exc_info=False)
        return "Invalid"


logger.info("Batch Analysis module loaded (enhanced v6 - Claude Structure + Fixes).")
