"""
Batch Analysis Module (Completely Rewritten for Reliability)

Provides a comprehensive framework for running batch analyses (security, performance, etc.)
across multiple applications or models with improved reliability and error handling.

Features:
- Explicit thread lifecycle management with guaranteed cleanup
- Robust error handling with proper categorization
- Consistent job and task status tracking
- Enhanced dependency verification before execution
- Thread-safe execution with proper locking
- Task-level timeouts with configurable limits
- Graceful cancellation that reliably stops tasks
- Structured logging with consistent context
- Memory-efficient operation for long-running services
- Automatic health checks and dependency validation
"""

# Standard Library Imports
import json
import os
import re
import shutil
import socket
import sys
import threading
import time
import traceback
import queue  # For task timeout mechanism
import concurrent.futures
import contextlib
import tempfile
import urllib.parse
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union

# Third-Party Imports
try:
    import flask
    from flask import (
        Blueprint, current_app, flash, jsonify, redirect,
        render_template, request, url_for
    )
    from werkzeug.exceptions import BadRequest, InternalServerError, NotFound
except ImportError:
    # Allow module to be imported even if Flask is not available
    # Will raise errors when Flask-dependent functions are called
    class Blueprint:
        def __init__(self, *args, **kwargs):
            pass
    class FlaskNotInstalledError(Exception):
        pass

# =============================================================================
# Logging Setup
# =============================================================================
import logging

# Central logger factory to support various logging configurations
class LoggerFactory:
    """Factory for creating consistently configured loggers."""
    
    @staticmethod
    def create_logger(name, propagate=True):
        """Create a logger with consistent configuration."""
        logger = logging.getLogger(name)
        
        # Only set level and add handler if not already configured
        if not logger.handlers and logger.level == logging.NOTSET:
            logger.setLevel(logging.INFO)
            
            # Create console handler
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            
            # Create formatter with contextual info
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s - %(threadName)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console.setFormatter(formatter)
            logger.addHandler(console)
        
        logger.propagate = propagate
        return logger

# Create loggers for different components
module_logger = LoggerFactory.create_logger('batch_analysis')
job_logger = LoggerFactory.create_logger('batch_analysis.job')
task_logger = LoggerFactory.create_logger('batch_analysis.task')
storage_logger = LoggerFactory.create_logger('batch_analysis.storage')
api_logger = LoggerFactory.create_logger('batch_analysis.api')
service_logger = LoggerFactory.create_logger('batch_analysis.service')

# Log configuration at the module level
module_logger.info("Batch Analysis module (rewritten version) initializing.")

# =============================================================================
# Data Models
# =============================================================================

class JobStatus(str, Enum):
    """Enumeration of possible job statuses with clear lifecycle progression."""
    PENDING = "pending"      # Job created but not started
    QUEUED = "queued"        # Job waiting to run (when max concurrent reached)
    INITIALIZING = "initializing"  # Job starting up, dependencies being checked
    RUNNING = "running"      # Job actively executing tasks
    CANCELLING = "cancelling"  # Job is in the process of being cancelled
    CANCELLED = "cancelled"  # Job was cancelled by user request
    COMPLETED = "completed"  # Job finished successfully
    FAILED = "failed"        # Job encountered error during execution
    ERROR = "error"          # Job couldn't start due to configuration/setup error

class TaskStatus(str, Enum):
    """Enumeration of possible task statuses."""
    PENDING = "pending"      # Task ready to be executed 
    RUNNING = "running"      # Task currently executing
    COMPLETED = "completed"  # Task finished successfully
    FAILED = "failed"        # Task execution failed
    TIMED_OUT = "timed_out"  # Task exceeded time limit
    CANCELLED = "cancelled"  # Task cancelled before or during execution
    SKIPPED = "skipped"      # Task skipped due to dependency issues

class AnalysisType(str, Enum):
    """Types of analysis that can be performed."""
    FRONTEND_SECURITY = "frontend_security"
    BACKEND_SECURITY = "backend_security"
    PERFORMANCE = "performance"
    GPT4ALL = "gpt4all"
    ZAP = "zap"

class ErrorCategory(str, Enum):
    """Categorization of errors for better handling and reporting."""
    CONFIGURATION = "configuration"  # Missing/invalid configuration 
    DEPENDENCY = "dependency"        # Missing/incompatible dependency
    NETWORK = "network"              # Network connectivity issues
    TIMEOUT = "timeout"              # Operation exceeded time limit
    VALIDATION = "validation"        # Input validation failed
    EXECUTION = "execution"          # Error during task execution
    INTERNAL = "internal"            # Unexpected internal error
    CANCELLED = "cancelled"          # Operation was cancelled
    UNKNOWN = "unknown"              # Unclassified error

@dataclass
class JobError:
    """Structured representation of an error with context."""
    message: str
    category: ErrorCategory
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    traceback: Optional[str] = None
    task_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "message": self.message,
            "category": self.category.value,
            "timestamp": self.timestamp.isoformat()
        }
        if self.traceback:
            result["traceback"] = self.traceback
        if self.task_id:
            result["task_id"] = self.task_id
        if self.details:
            result["details"] = self.details
        return result

@dataclass
class BatchAnalysisJob:
    """Job configuration, status, and results tracking."""
    id: int
    name: str
    description: str
    created_at: datetime
    status: JobStatus = JobStatus.PENDING
    models: List[str] = field(default_factory=list)
    app_ranges: Dict[str, List[int]] = field(default_factory=dict)
    analysis_types: List[AnalysisType] = field(default_factory=list)
    analysis_options: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    results_summary: Dict[str, Any] = field(default_factory=dict)
    errors: List[JobError] = field(default_factory=list)
    task_count_by_status: Dict[str, int] = field(default_factory=dict)
    cancellation_requested: bool = False

    @property
    def created_at_formatted(self) -> str:
        """Returns created_at time formatted as YYYY-MM-DD HH:MM (local time)."""
        if not self.created_at:
            return 'N/A'
        local_dt = self.created_at.astimezone() if self.created_at.tzinfo else self.created_at
        return local_dt.strftime('%Y-%m-%d %H:%M')

    @property
    def duration_seconds(self) -> Optional[int]:
        """Calculate job duration in seconds."""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.now(timezone.utc)
        if not self.started_at.tzinfo:
            # Ensure timezone-aware comparison
            self.started_at = self.started_at.replace(tzinfo=timezone.utc)
            
        return int((end_time - self.started_at).total_seconds())

    def add_error(self, message: str, category: ErrorCategory, traceback: Optional[str] = None,
                 task_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        """Add a structured error to the job with proper categorization."""
        error = JobError(
            message=message,
            category=category,
            traceback=traceback,
            task_id=task_id,
            details=details or {}
        )
        self.errors.append(error)
        job_logger.error(f"[Job {self.id}] Error added: {message} (Category: {category.value})")

    def update_task_status_count(self, status: TaskStatus, increment: int = 1) -> None:
        """Update the task count for a specific status."""
        current_count = self.task_count_by_status.get(status.value, 0)
        self.task_count_by_status[status.value] = current_count + increment
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for JSON serialization."""
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "models": self.models,
            "app_ranges": self.app_ranges,
            "analysis_types": [at.value for at in self.analysis_types],
            "analysis_options": self.analysis_options,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "results_summary": self.results_summary,
            "task_count_by_status": self.task_count_by_status,
            "created_at_formatted": self.created_at_formatted,
            "cancellation_requested": self.cancellation_requested
        }
        
        # Handle datetime fields
        for dt_field in ["created_at", "started_at", "completed_at"]:
            dt_value = getattr(self, dt_field)
            if dt_value:
                if not dt_value.tzinfo:
                    dt_value = dt_value.replace(tzinfo=timezone.utc)
                result[dt_field] = dt_value.isoformat()
            else:
                result[dt_field] = None
        
        # Convert errors to dictionaries
        result["errors"] = [error.to_dict() for error in self.errors]
        
        # Calculate duration
        result["duration_seconds"] = self.duration_seconds
        
        return result

@dataclass
class BatchAnalysisTask:
    """Individual analysis task with tracking and result storage."""
    id: int
    job_id: int
    model: str
    app_num: int
    analysis_type: AnalysisType
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout_seconds: int = 1800  # Default 30-minute timeout
    error: Optional[JobError] = None
    progress: int = 0  # 0-100 percentage
    result_details: Dict[str, Any] = field(default_factory=dict)
    
    def get_task_key(self) -> str:
        """Get a unique string key for this task."""
        return f"{self.model}/{self.app_num}/{self.analysis_type.value}"
    
    def start(self) -> None:
        """Mark task as started."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
    
    def complete(self, result_details: Dict[str, Any]) -> None:
        """Mark task as completed with results."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.progress = 100
        self.result_details = result_details
    
    def fail(self, message: str, category: ErrorCategory, traceback: Optional[str] = None,
             details: Optional[Dict[str, Any]] = None) -> None:
        """Mark task as failed with error information."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        self.error = JobError(
            message=message,
            category=category,
            traceback=traceback,
            task_id=self.get_task_key(),
            details=details or {}
        )
    
    def cancel(self) -> None:
        """Mark task as cancelled."""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now(timezone.utc)
    
    def timeout(self) -> None:
        """Mark task as timed out."""
        self.status = TaskStatus.TIMED_OUT
        self.completed_at = datetime.now(timezone.utc)
        self.error = JobError(
            message=f"Task exceeded timeout of {self.timeout_seconds} seconds",
            category=ErrorCategory.TIMEOUT,
            task_id=self.get_task_key()
        )
    
    @property
    def duration_seconds(self) -> Optional[int]:
        """Calculate task duration in seconds."""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.now(timezone.utc)
        return int((end_time - self.started_at).total_seconds())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for JSON serialization."""
        result = {
            "id": self.id,
            "job_id": self.job_id,
            "model": self.model,
            "app_num": self.app_num,
            "analysis_type": self.analysis_type.value,
            "status": self.status.value,
            "timeout_seconds": self.timeout_seconds,
            "progress": self.progress
        }
        
        # Handle datetime fields
        for dt_field in ["created_at", "started_at", "completed_at"]:
            dt_value = getattr(self, dt_field)
            if dt_value:
                if not dt_value.tzinfo:
                    dt_value = dt_value.replace(tzinfo=timezone.utc)
                result[dt_field] = dt_value.isoformat()
            else:
                result[dt_field] = None
        
        # Include error if present
        if self.error:
            result["error"] = self.error.to_dict()
        
        # Include result details
        result["result_details"] = self._sanitize_details(self.result_details)
        
        # Calculate duration
        result["duration_seconds"] = self.duration_seconds
        
        return result
    
    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize details for JSON serialization."""
        max_str_len = 1000
        max_list_len = 50
        
        def sanitize_value(value):
            if isinstance(value, str):
                return value[:max_str_len] + ('...' if len(value) > max_str_len else '')
            elif isinstance(value, list):
                if len(value) > max_list_len:
                    return [sanitize_value(item) for item in value[:max_list_len]] + ["... (truncated)"]
                return [sanitize_value(item) for item in value]
            elif isinstance(value, dict):
                return {k: sanitize_value(v) for k, v in value.items()}
            elif isinstance(value, (int, float, bool, type(None))):
                return value
            else:
                try:
                    json.dumps(value)  # Check if serializable
                    return value
                except (TypeError, OverflowError):
                    return f"<Unserializable type: {type(value).__name__}>"
        
        return sanitize_value(details)

@dataclass
class BatchAnalysisResult:
    """Result of a completed analysis task."""
    id: int
    job_id: int
    task_id: int
    model: str
    app_num: int
    analysis_type: AnalysisType
    status: str  # Final status: "completed", "failed", "timed_out", "cancelled", "skipped"
    issues_count: int = 0
    high_severity: int = 0
    medium_severity: int = 0
    low_severity: int = 0
    scan_start_time: Optional[datetime] = None
    scan_end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_task(cls, task: BatchAnalysisTask, result_id: int) -> 'BatchAnalysisResult':
        """Create a result from a completed task."""
        details = task.result_details.copy()
        result = cls(
            id=result_id,
            job_id=task.job_id,
            task_id=task.id,
            model=task.model,
            app_num=task.app_num,
            analysis_type=task.analysis_type,
            status=task.status.value,
            scan_start_time=task.started_at,
            scan_end_time=task.completed_at,
            duration_seconds=task.duration_seconds,
            details=details
        )
        
        # Extract metrics from result details based on analysis type
        if task.status == TaskStatus.COMPLETED:
            if task.analysis_type in [AnalysisType.FRONTEND_SECURITY, AnalysisType.BACKEND_SECURITY]:
                result.issues_count = len(details.get("issues", []))
                result.high_severity = details.get("summary", {}).get("severity_counts", {}).get("HIGH", 0)
                result.medium_severity = details.get("summary", {}).get("severity_counts", {}).get("MEDIUM", 0)
                result.low_severity = details.get("summary", {}).get("severity_counts", {}).get("LOW", 0)
            elif task.analysis_type == AnalysisType.PERFORMANCE:
                result.issues_count = details.get("total_failures", 0)
            elif task.analysis_type == AnalysisType.GPT4ALL:
                result.issues_count = details.get("summary", {}).get("requirements_checked", 0) - details.get("summary", {}).get("met_count", 0)
            elif task.analysis_type == AnalysisType.ZAP:
                issues = details.get("issues", [])
                result.issues_count = len(issues)
                result.high_severity = sum(1 for issue in issues if issue.get("risk") == "High")
                result.medium_severity = sum(1 for issue in issues if issue.get("risk") == "Medium")
                result.low_severity = sum(1 for issue in issues if issue.get("risk") == "Low")
        
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        result = {
            "id": self.id,
            "job_id": self.job_id,
            "task_id": self.task_id,
            "model": self.model,
            "app_num": self.app_num,
            "analysis_type": self.analysis_type.value,
            "status": self.status,
            "issues_count": self.issues_count,
            "high_severity": self.high_severity,
            "medium_severity": self.medium_severity,
            "low_severity": self.low_severity,
            "duration_seconds": self.duration_seconds
        }
        
        # Handle datetime fields
        for dt_field, dt_value in [("scan_start_time", self.scan_start_time), 
                                  ("scan_end_time", self.scan_end_time)]:
            if dt_value:
                if not dt_value.tzinfo:
                    dt_value = dt_value.replace(tzinfo=timezone.utc)
                result[dt_field] = dt_value.isoformat()
            else:
                result[dt_field] = None
        
        # Sanitize and include details
        sanitized_details = {}
        for key, value in self.details.items():
            if isinstance(value, (str, int, float, bool, type(None))):
                sanitized_details[key] = value
            elif isinstance(value, list) and key == "issues":
                # Include only first 50 issues to avoid excessive data
                sanitized_details[key] = value[:50]
                if len(value) > 50:
                    sanitized_details["issues_truncated"] = True
                    sanitized_details["total_issues_count"] = len(value)
            elif isinstance(value, dict):
                sanitized_details[key] = value
            else:
                sanitized_details[key] = str(value)
        
        result["details"] = sanitized_details
        
        return result

# =============================================================================
# Storage Interface & Implementation
# =============================================================================

class JobStorage:
    """Thread-safe storage for batch analysis jobs, tasks, and results."""
    
    def __init__(self):
        """Initialize storage with empty collections and locks."""
        self.jobs: Dict[int, BatchAnalysisJob] = {}
        self.tasks: Dict[int, BatchAnalysisTask] = {}  # task_id -> task
        self.job_tasks: Dict[int, List[int]] = {}  # job_id -> list of task_ids
        self.results: Dict[int, BatchAnalysisResult] = {}  # result_id -> result
        self.job_results: Dict[int, List[int]] = {}  # job_id -> list of result_ids
        
        self.next_job_id = 1
        self.next_task_id = 1
        self.next_result_id = 1
        
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        storage_logger.info("JobStorage initialized")
    
    def _get_next_id(self, counter_attr: str) -> int:
        """Get next sequential ID from a counter (thread-safe)."""
        # Assumes lock is already held when called
        current_id = getattr(self, counter_attr)
        setattr(self, counter_attr, current_id + 1)
        return current_id
    
    def create_job(self, job_data: Dict[str, Any], app_context: Any) -> BatchAnalysisJob:
        """Create a new job from provided data."""
        with self._lock:
            job_id = self._get_next_id('next_job_id')
            job_log_prefix = f"[Job {job_id}]"
            storage_logger.info(f"{job_log_prefix} Creating new job")
            
            # Validate input data
            try:
                # Parse analysis types
                analysis_types_input = job_data.get('analysis_types', [])
                analysis_types = []
                
                if isinstance(analysis_types_input, list):
                    for at_input in analysis_types_input:
                        if isinstance(at_input, AnalysisType):
                            analysis_types.append(at_input)
                        elif isinstance(at_input, str):
                            analysis_types.append(AnalysisType(at_input))
                        else:
                            raise ValueError(f"Invalid analysis type: {at_input}")
                else:
                    raise ValueError("analysis_types must be a list")
                
                if not analysis_types:
                    raise ValueError("At least one analysis type must be selected")
                
                # Validate models
                models = job_data.get('models', [])
                if not isinstance(models, list) or not models:
                    raise ValueError("At least one model must be selected")
                
                # Validate app ranges
                app_ranges = job_data.get('app_ranges', {})
                if not isinstance(app_ranges, dict):
                    raise ValueError("app_ranges must be a dictionary")
                
            except (ValueError, TypeError) as e:
                storage_logger.error(f"{job_log_prefix} Validation error: {e}")
                raise
            
            # Create job object
            job = BatchAnalysisJob(
                id=job_id,
                name=job_data.get('name', f'Batch Job {job_id}').strip(),
                description=job_data.get('description', '').strip(),
                created_at=datetime.now(timezone.utc),
                models=models,
                app_ranges=app_ranges,
                analysis_types=analysis_types,
                analysis_options=job_data.get('analysis_options', {})
            )
            
            # Calculate total tasks
            try:
                job.total_tasks = self._calculate_total_tasks(job, app_context)
                storage_logger.debug(f"{job_log_prefix} Estimated total tasks: {job.total_tasks}")
            except Exception as e:
                job.add_error(
                    message=f"Failed to calculate task count: {str(e)}",
                    category=ErrorCategory.CONFIGURATION
                )
                job.total_tasks = 0
                storage_logger.warning(f"{job_log_prefix} Failed to calculate tasks: {e}")
            
            # Store job
            self.jobs[job_id] = job
            self.job_tasks[job_id] = []
            self.job_results[job_id] = []
            
            storage_logger.info(f"{job_log_prefix} Created job '{job.name}' with {len(job.analysis_types)} analysis types")
            return job
    
    def _calculate_total_tasks(self, job: BatchAnalysisJob, app_context: Any) -> int:
        """Calculate the total number of tasks for a job."""
        job_log_prefix = f"[Job {job.id}]"
        total_tasks = 0
        
        if not hasattr(app_context, 'config'):
            storage_logger.error(f"{job_log_prefix} App context missing config attribute")
            return 0
        
        base_path_str = app_context.config.get('APP_BASE_PATH')
        if not base_path_str:
            storage_logger.error(f"{job_log_prefix} APP_BASE_PATH not found in config")
            return 0
            
        base_path = Path(base_path_str)
        
        for model in job.models:
            model_path = base_path / model
            if not model_path.is_dir():
                storage_logger.warning(f"{job_log_prefix} Model directory not found: {model_path}")
                continue
            
            # Determine target apps for this model
            target_app_nums = []
            app_range = job.app_ranges.get(model, [])
            scan_all_apps = model in job.app_ranges and isinstance(app_range, list) and not app_range
            
            if scan_all_apps:
                # Find all app directories for this model
                try:
                    target_app_nums = sorted([
                        int(item.name[3:]) for item in model_path.iterdir()
                        if item.is_dir() and item.name.startswith('app') and item.name[3:].isdigit()
                    ])
                except Exception as e:
                    storage_logger.error(f"{job_log_prefix} Error listing apps for {model}: {e}")
                    continue
            elif isinstance(app_range, list):
                target_app_nums = sorted(list(set(app_range)))
            
            # Count valid app directories
            valid_app_count = 0
            for app_num in target_app_nums:
                app_dir = model_path / f"app{app_num}"
                if app_dir.is_dir():
                    valid_app_count += 1
            
            # Total tasks for model = valid apps × analysis types
            model_tasks = valid_app_count * len(job.analysis_types)
            total_tasks += model_tasks
            
        return total_tasks
    
    def get_job(self, job_id: int) -> Optional[BatchAnalysisJob]:
        """Get a job by ID."""
        with self._lock:
            return self.jobs.get(job_id)
    
    def get_all_jobs(self) -> List[BatchAnalysisJob]:
        """Get all jobs."""
        with self._lock:
            return list(self.jobs.values())
    
    def update_job(self, job_id: int, **kwargs) -> Optional[BatchAnalysisJob]:
        """Update job attributes."""
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                storage_logger.warning(f"[Job {job_id}] Update failed: Job not found")
                return None
            
            for key, value in kwargs.items():
                if not hasattr(job, key):
                    storage_logger.warning(f"[Job {job_id}] Unknown attribute: {key}")
                    continue
                
                # Type conversions/validations
                try:
                    if key == 'status' and isinstance(value, str):
                        value = JobStatus(value)
                    elif key in ['started_at', 'completed_at'] and isinstance(value, datetime):
                        if not value.tzinfo:
                            value = value.replace(tzinfo=timezone.utc)
                    elif key in ['total_tasks', 'completed_tasks'] and value is not None:
                        value = int(value)
                except (ValueError, TypeError) as e:
                    storage_logger.error(f"[Job {job_id}] Invalid value for {key}: {e}")
                    continue
                
                # Set the attribute
                old_value = getattr(job, key)
                if value != old_value:
                    storage_logger.debug(f"[Job {job_id}] Updating {key}: {old_value} -> {value}")
                    setattr(job, key, value)
            
            return job
    
    def create_task(self, job_id: int, model: str, app_num: int, 
                   analysis_type: AnalysisType, timeout_seconds: int = 1800) -> Optional[BatchAnalysisTask]:
        """Create a new task for a job."""
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                storage_logger.warning(f"[Job {job_id}] Cannot create task: Job not found")
                return None
            
            task_id = self._get_next_id('next_task_id')
            task = BatchAnalysisTask(
                id=task_id,
                job_id=job_id,
                model=model,
                app_num=app_num,
                analysis_type=analysis_type,
                timeout_seconds=timeout_seconds
            )
            
            self.tasks[task_id] = task
            self.job_tasks[job_id].append(task_id)
            
            # Update job task count by status
            job.update_task_status_count(TaskStatus.PENDING)
            
            task_key = task.get_task_key()
            storage_logger.info(f"[Job {job_id}] Created task {task_id}: {task_key}")
            return task
    
    def get_task(self, task_id: int) -> Optional[BatchAnalysisTask]:
        """Get a task by ID."""
        with self._lock:
            return self.tasks.get(task_id)
    
    def get_job_tasks(self, job_id: int) -> List[BatchAnalysisTask]:
        """Get all tasks for a job."""
        with self._lock:
            task_ids = self.job_tasks.get(job_id, [])
            return [self.tasks.get(task_id) for task_id in task_ids if task_id in self.tasks]
    
    def update_task(self, task_id: int, **kwargs) -> Optional[BatchAnalysisTask]:
        """Update task attributes."""
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                storage_logger.warning(f"[Task {task_id}] Update failed: Task not found")
                return None
            
            old_status = task.status
            
            for key, value in kwargs.items():
                if not hasattr(task, key):
                    storage_logger.warning(f"[Task {task_id}] Unknown attribute: {key}")
                    continue
                
                # Type conversions/validations
                try:
                    if key == 'status' and isinstance(value, str):
                        value = TaskStatus(value)
                    elif key in ['created_at', 'started_at', 'completed_at'] and isinstance(value, datetime):
                        if not value.tzinfo:
                            value = value.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError) as e:
                    storage_logger.error(f"[Task {task_id}] Invalid value for {key}: {e}")
                    continue
                
                # Set the attribute
                old_value = getattr(task, key)
                if value != old_value:
                    setattr(task, key, value)
            
            # Update job task count by status if status changed
            new_status = task.status
            if new_status != old_status:
                job = self.jobs.get(task.job_id)
                if job:
                    # Decrement old status count
                    old_count = job.task_count_by_status.get(old_status.value, 0)
                    if old_count > 0:
                        job.task_count_by_status[old_status.value] = old_count - 1
                    
                    # Increment new status count
                    job.task_count_by_status[new_status.value] = job.task_count_by_status.get(new_status.value, 0) + 1
                    
                    # Update completed_tasks for terminal statuses
                    if new_status in [TaskStatus.COMPLETED, TaskStatus.FAILED, 
                                     TaskStatus.CANCELLED, TaskStatus.TIMED_OUT, 
                                     TaskStatus.SKIPPED]:
                        job.completed_tasks += 1
                        
                        # Check if job is complete
                        if job.completed_tasks >= job.total_tasks and job.status == JobStatus.RUNNING:
                            # Determine final status based on task results
                            has_failed = job.task_count_by_status.get(TaskStatus.FAILED.value, 0) > 0
                            has_timed_out = job.task_count_by_status.get(TaskStatus.TIMED_OUT.value, 0) > 0
                            has_cancelled = job.task_count_by_status.get(TaskStatus.CANCELLED.value, 0) > 0
                            has_skipped = job.task_count_by_status.get(TaskStatus.SKIPPED.value, 0) > 0
                            
                            if has_failed or has_timed_out or has_cancelled or has_skipped:
                                job.status = JobStatus.FAILED
                            else:
                                job.status = JobStatus.COMPLETED
                            
                            job.completed_at = datetime.now(timezone.utc)
                
                task_key = task.get_task_key()
                storage_logger.info(f"[Job {task.job_id}] Task {task_id} ({task_key}) status changed: {old_status.value} -> {new_status.value}")
            
            return task
    
    def add_result(self, task: BatchAnalysisTask) -> Optional[BatchAnalysisResult]:
        """Create result from a completed task."""
        with self._lock:
            job = self.jobs.get(task.job_id)
            if not job:
                storage_logger.warning(f"[Task {task.id}] Cannot add result: Job {task.job_id} not found")
                return None
            
            result_id = self._get_next_id('next_result_id')
            result = BatchAnalysisResult.from_task(task, result_id)
            
            self.results[result_id] = result
            self.job_results[task.job_id].append(result_id)
            
            # Update job summary with result data
            self._update_job_summary(job, result)
            
            storage_logger.info(f"[Job {task.job_id}] Added result {result_id} for task {task.id}: {result.status}")
            return result
    
    def _update_job_summary(self, job: BatchAnalysisJob, result: BatchAnalysisResult) -> None:
        """Update job results summary with a new result."""
        summary = job.results_summary.copy()
        
        # Track total counters
        summary['total_tasks_processed'] = summary.get('total_tasks_processed', 0) + 1
        
        # Track by analysis type
        type_key = f"{result.analysis_type.value}_tasks_processed" 
        summary[type_key] = summary.get(type_key, 0) + 1
        
        # Track by status
        status_key = f"tasks_{result.status}"
        summary[status_key] = summary.get(status_key, 0) + 1
        
        # Track by analysis type and status
        type_status_key = f"{result.analysis_type.value}_tasks_{result.status}"
        summary[type_status_key] = summary.get(type_status_key, 0) + 1
        
        # Track issue counts for completed tasks
        if result.status == "completed":
            summary['issues_total'] = summary.get('issues_total', 0) + result.issues_count
            
            # Security-related metrics
            if result.analysis_type in [AnalysisType.FRONTEND_SECURITY, AnalysisType.BACKEND_SECURITY, AnalysisType.ZAP]:
                summary['high_total'] = summary.get('high_total', 0) + result.high_severity
                summary['medium_total'] = summary.get('medium_total', 0) + result.medium_severity
                summary['low_total'] = summary.get('low_total', 0) + result.low_severity
            
            # Analysis type specific metrics
            type_issues_key = f"{result.analysis_type.value}_issues_total"
            summary[type_issues_key] = summary.get(type_issues_key, 0) + result.issues_count
            
            # Performance-specific metrics
            if result.analysis_type == AnalysisType.PERFORMANCE and 'total_failures' in result.details:
                summary['performance_total_failures'] = summary.get('performance_total_failures', 0) + result.details['total_failures']
            
            # GPT4All-specific metrics
            if result.analysis_type == AnalysisType.GPT4ALL and 'summary' in result.details:
                gpt_summary = result.details['summary']
                summary['gpt4all_reqs_checked_total'] = summary.get('gpt4all_reqs_checked_total', 0) + gpt_summary.get('requirements_checked', 0)
                summary['gpt4all_reqs_met_total'] = summary.get('gpt4all_reqs_met_total', 0) + gpt_summary.get('met_count', 0)
        
        job.results_summary = summary
    
    def get_result(self, result_id: int) -> Optional[BatchAnalysisResult]:
        """Get a result by ID."""
        with self._lock:
            return self.results.get(result_id)
    
    def get_results(self, job_id: int) -> List[BatchAnalysisResult]:
        """Get all results for a job."""
        with self._lock:
            result_ids = self.job_results.get(job_id, [])
            return [self.results.get(result_id) for result_id in result_ids if result_id in self.results]
    
    def delete_job(self, job_id: int) -> bool:
        """Delete a job and all associated tasks and results."""
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                storage_logger.warning(f"[Job {job_id}] Delete failed: Job not found")
                return False
            
            if job.status in [JobStatus.RUNNING, JobStatus.INITIALIZING, JobStatus.CANCELLING]:
                storage_logger.error(f"[Job {job_id}] Cannot delete job: Job is currently {job.status.value}")
                return False
            
            # Delete tasks
            task_ids = self.job_tasks.get(job_id, [])
            for task_id in task_ids:
                if task_id in self.tasks:
                    del self.tasks[task_id]
            
            # Delete results
            result_ids = self.job_results.get(job_id, [])
            for result_id in result_ids:
                if result_id in self.results:
                    del self.results[result_id]
            
            # Delete job and references
            del self.jobs[job_id]
            if job_id in self.job_tasks:
                del self.job_tasks[job_id]
            if job_id in self.job_results:
                del self.job_results[job_id]
            
            storage_logger.info(f"[Job {job_id}] Deleted job '{job.name}' with {len(task_ids)} tasks and {len(result_ids)} results")
            return True

# Global instance of job storage
job_storage = JobStorage()

# =============================================================================
# Task Executor Service
# =============================================================================

class TaskExecutionError(Exception):
    """Error during task execution with category and context."""
    def __init__(self, message: str, category: ErrorCategory, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.category = category
        self.details = details or {}
        super().__init__(message)

class TaskExecutor:
    """
    Handles the execution of individual analysis tasks with robust error handling,
    timeouts, and resource cleanup.
    """
    
    def __init__(self, storage: JobStorage):
        """Initialize the executor."""
        self.storage = storage
        task_logger.info("TaskExecutor initialized")
    
    @contextlib.contextmanager
    def _task_execution_context(self, task_id: int):
        """Context manager for task execution with proper lifecycle management."""
        task = self.storage.get_task(task_id)
        if not task:
            task_logger.error(f"[Task {task_id}] Task not found")
            raise TaskExecutionError(
                message=f"Task {task_id} not found",
                category=ErrorCategory.INTERNAL
            )
        
        task_key = task.get_task_key()
        job = self.storage.get_job(task.job_id)
        if not job:
            task_logger.error(f"[Task {task_id}] Parent job {task.job_id} not found")
            raise TaskExecutionError(
                message=f"Parent job {task.job_id} not found",
                category=ErrorCategory.INTERNAL
            )
        
        # Check for cancellation before starting
        if job.cancellation_requested:
            task_logger.info(f"[Task {task_id}] {task_key} - Cancelled before execution started")
            task.cancel()
            self.storage.update_task(task.id, status=TaskStatus.CANCELLED)
            raise TaskExecutionError(
                message="Task cancelled before execution started",
                category=ErrorCategory.CANCELLED
            )
        
        # Mark task as running
        task.start()
        self.storage.update_task(task.id, status=TaskStatus.RUNNING, started_at=task.started_at)
        
        task_logger.info(f"[Task {task_id}] {task_key} - Execution started")
        
        try:
            # Set up timeout mechanism using queue
            result_queue = queue.Queue()
            timeout_seconds = task.timeout_seconds
            
            # Create task context to be passed to execution function
            context = {
                "task": task,
                "job": job,
                "result_queue": result_queue,
                "app_context": None,  # Will be set by service layer
                "services": {},       # Will be filled with required services
                "progress_callback": lambda p: self._update_progress(task.id, p)
            }
            
            # Yield context to the caller
            yield context
            
            # After execution, wait for result or timeout
            try:
                task_logger.info(f"[Task {task_id}] {task_key} - Waiting for result (timeout: {timeout_seconds}s)")
                result = result_queue.get(timeout=timeout_seconds)
                
                if result.get("status") == "cancelled":
                    task_logger.info(f"[Task {task_id}] {task_key} - Cancelled during execution")
                    task.cancel()
                    self.storage.update_task(task.id, status=TaskStatus.CANCELLED, completed_at=task.completed_at)
                    
                elif result.get("status") == "completed":
                    task_logger.info(f"[Task {task_id}] {task_key} - Completed successfully")
                    task.complete(result.get("details", {}))
                    self.storage.update_task(
                        task.id, 
                        status=TaskStatus.COMPLETED, 
                        completed_at=task.completed_at,
                        result_details=task.result_details,
                        progress=100
                    )
                    
                    # Create result record
                    self.storage.add_result(task)
                    
                elif result.get("status") == "failed":
                    error_msg = result.get("error", "Unknown error")
                    error_category = result.get("category", ErrorCategory.EXECUTION)
                    error_details = result.get("details", {})
                    error_traceback = result.get("traceback")
                    
                    task_logger.error(f"[Task {task_id}] {task_key} - Failed: {error_msg}")
                    task.fail(error_msg, error_category, error_traceback, error_details)
                    self.storage.update_task(
                        task.id, 
                        status=TaskStatus.FAILED, 
                        completed_at=task.completed_at,
                        error=task.error
                    )
                    
                    # Create result record for failed task
                    self.storage.add_result(task)
                    
                elif result.get("status") == "skipped":
                    skip_reason = result.get("reason", "Unknown reason")
                    task_logger.warning(f"[Task {task_id}] {task_key} - Skipped: {skip_reason}")
                    task.status = TaskStatus.SKIPPED
                    task.completed_at = datetime.now(timezone.utc)
                    task.result_details = {"skip_reason": skip_reason}
                    self.storage.update_task(
                        task.id, 
                        status=TaskStatus.SKIPPED, 
                        completed_at=task.completed_at,
                        result_details=task.result_details
                    )
                    
                    # Create result record for skipped task
                    self.storage.add_result(task)
                
            except queue.Empty:
                # Task timed out
                task_logger.error(f"[Task {task_id}] {task_key} - Timed out after {timeout_seconds} seconds")
                task.timeout()
                self.storage.update_task(
                    task.id, 
                    status=TaskStatus.TIMED_OUT, 
                    completed_at=task.completed_at,
                    error=task.error
                )
                
                # Create result record for timed-out task
                self.storage.add_result(task)
        
        except TaskExecutionError as e:
            # Pass through TaskExecutionError
            raise
        except Exception as e:
            # Handle unexpected errors
            error_msg = f"Unexpected error in task execution context: {str(e)}"
            task_logger.exception(f"[Task {task_id}] {task_key} - {error_msg}")
            
            task.fail(
                message=error_msg,
                category=ErrorCategory.INTERNAL,
                traceback=traceback.format_exc()
            )
            self.storage.update_task(
                task.id, 
                status=TaskStatus.FAILED, 
                completed_at=task.completed_at,
                error=task.error
            )
            
            # Create result record for failed task
            self.storage.add_result(task)
            
            raise TaskExecutionError(
                message=error_msg,
                category=ErrorCategory.INTERNAL,
                details={"original_error": str(e), "traceback": traceback.format_exc()}
            )
        finally:
            task_logger.info(f"[Task {task_id}] {task_key} - Execution context completed")
    
    def _update_progress(self, task_id: int, progress: int) -> None:
        """Update task progress."""
        progress = max(0, min(100, progress))  # Ensure 0-100 range
        self.storage.update_task(task_id, progress=progress)
    
    def execute_frontend_security_task(self, context: Dict[str, Any]) -> None:
        """Execute frontend security analysis."""
        task = context["task"]
        job = context["job"]
        result_queue = context["result_queue"]
        analyzer = context["services"].get("frontend_security_analyzer")
        
        if not analyzer:
            result_queue.put({
                "status": "skipped",
                "reason": "Frontend security analyzer not available"
            })
            return
        
        try:
            task_logger.info(f"[Task {task.id}] Running frontend security analysis for {task.model}/app{task.app_num}")
            
            # Get analysis options
            options = job.analysis_options.get(AnalysisType.FRONTEND_SECURITY.value, {})
            full_scan = options.get("full_scan", False)
            
            # Execute analysis
            issues, tool_status, raw_output = analyzer.run_security_analysis(
                task.model, task.app_num, use_all_tools=full_scan
            )
            
            # Get summary
            summary = analyzer.get_analysis_summary(issues)
            
            # Prepare result
            result_details = {
                "issues": issues,
                "summary": summary,
                "tool_status": tool_status,
                "raw_output_preview": raw_output[:5000] if raw_output else None
            }
            
            result_queue.put({
                "status": "completed",
                "details": result_details
            })
            
        except Exception as e:
            task_logger.exception(f"[Task {task.id}] Frontend security analysis failed: {e}")
            result_queue.put({
                "status": "failed",
                "error": f"Frontend security analysis failed: {str(e)}",
                "category": ErrorCategory.EXECUTION,
                "traceback": traceback.format_exc(),
                "details": {"error_type": type(e).__name__}
            })
    
    def execute_backend_security_task(self, context: Dict[str, Any]) -> None:
        """Execute backend security analysis."""
        task = context["task"]
        job = context["job"]
        result_queue = context["result_queue"]
        analyzer = context["services"].get("backend_security_analyzer")
        
        if not analyzer:
            result_queue.put({
                "status": "skipped",
                "reason": "Backend security analyzer not available"
            })
            return
        
        try:
            task_logger.info(f"[Task {task.id}] Running backend security analysis for {task.model}/app{task.app_num}")
            
            # Get analysis options
            options = job.analysis_options.get(AnalysisType.BACKEND_SECURITY.value, {})
            full_scan = options.get("full_scan", False)
            
            # Execute analysis
            issues, tool_status, raw_output = analyzer.run_security_analysis(
                task.model, task.app_num, use_all_tools=full_scan
            )
            
            # Get summary
            summary = analyzer.get_analysis_summary(issues)
            
            # Prepare result
            result_details = {
                "issues": issues,
                "summary": summary,
                "tool_status": tool_status,
                "raw_output_preview": raw_output[:5000] if raw_output else None
            }
            
            result_queue.put({
                "status": "completed",
                "details": result_details
            })
            
        except Exception as e:
            task_logger.exception(f"[Task {task.id}] Backend security analysis failed: {e}")
            result_queue.put({
                "status": "failed",
                "error": f"Backend security analysis failed: {str(e)}",
                "category": ErrorCategory.EXECUTION,
                "traceback": traceback.format_exc(),
                "details": {"error_type": type(e).__name__}
            })
    
    def execute_performance_task(self, context: Dict[str, Any]) -> None:
        """Execute performance testing."""
        task = context["task"]
        job = context["job"]
        result_queue = context["result_queue"]
        tester = context["services"].get("performance_tester")
        port_manager = context["services"].get("port_manager")
        
        if not tester:
            result_queue.put({
                "status": "skipped",
                "reason": "Performance tester not available"
            })
            return
        
        if not port_manager:
            result_queue.put({
                "status": "skipped",
                "reason": "Port manager not available"
            })
            return
        
        try:
            task_logger.info(f"[Task {task.id}] Running performance test for {task.model}/app{task.app_num}")
            
            # Get analysis options
            options = job.analysis_options.get(AnalysisType.PERFORMANCE.value, {})
            users = int(options.get("users", 10))
            duration = int(options.get("duration", 30))
            spawn_rate = int(options.get("spawn_rate", 1))
            endpoints = options.get("endpoints", [{"path": "/", "method": "GET"}])
            
            # Validate parameters
            if not (users > 0 and duration > 0 and spawn_rate > 0):
                raise ValueError("Performance parameters must be positive")
            
            # Get port information
            # Function to get model index
            try:
                if hasattr(context["app_context"], "get_model_index"):
                    model_idx = context["app_context"].get_model_index(task.model)
                else:
                    # Try to import from utils
                    get_model_index = context["services"].get("get_model_index")
                    if get_model_index:
                        model_idx = get_model_index(task.model)
                    else:
                        raise ValueError(f"Cannot determine model index for {task.model}")
                
                ports = port_manager.get_app_ports(model_idx, task.app_num)
                
                if not ports or 'frontend' not in ports:
                    raise ValueError(f"Frontend port not found for {task.model}/app{task.app_num}")
                
                target_host = "localhost"
                target_port = ports['frontend']
                host_url = f"http://{target_host}:{target_port}"
                
                # Check if target app is available
                task_logger.info(f"[Task {task.id}] Checking if target app is available at {host_url}")
                
                # Function to check if port is open
                def is_port_open(host, port, timeout=5):
                    try:
                        with socket.create_connection((host, port), timeout=timeout):
                            return True
                    except (socket.timeout, ConnectionRefusedError, OSError):
                        return False
                
                # Wait for port to be available with timeout and progress updates
                port_check_timeout = 60  # seconds
                port_check_interval = 2   # seconds
                port_check_start = time.time()
                
                while time.time() - port_check_start < port_check_timeout:
                    # Check for cancellation
                    if job.cancellation_requested:
                        result_queue.put({
                            "status": "cancelled",
                            "reason": "Job cancellation requested during port check"
                        })
                        return
                    
                    if is_port_open(target_host, target_port):
                        break
                    
                    # Update progress
                    elapsed = time.time() - port_check_start
                    progress = min(30, int((elapsed / port_check_timeout) * 30))  # Max 30% progress during port check
                    context["progress_callback"](progress)
                    
                    time.sleep(port_check_interval)
                else:
                    # Port check timed out
                    raise TimeoutError(f"Target application did not respond on {target_host}:{target_port} within {port_check_timeout}s")
                
                # Execute performance test
                task_logger.info(f"[Task {task.id}] Starting performance test with {users} users for {duration}s")
                
                # Update progress to indicate test is starting
                context["progress_callback"](40)
                
                perf_result = tester.run_test_library(
                    test_name=f"batch_{job.id}_{task.model}_{task.app_num}",
                    host=host_url,
                    endpoints=endpoints,
                    user_count=users,
                    spawn_rate=spawn_rate,
                    run_time=duration,
                    generate_graphs=True,
                    model=task.model,
                    app_num=task.app_num
                )
                
                if not perf_result:
                    raise RuntimeError("Performance test returned no result")
                
                # Convert to dictionary
                if hasattr(perf_result, 'to_dict') and callable(perf_result.to_dict):
                    result_details = perf_result.to_dict()
                elif hasattr(perf_result, '__dataclass_fields__'):
                    result_details = asdict(perf_result)
                else:
                    # Manual conversion as fallback
                    result_details = {
                        "total_requests": getattr(perf_result, "total_requests", 0),
                        "total_failures": getattr(perf_result, "total_failures", 0),
                        "requests_per_sec": getattr(perf_result, "requests_per_sec", 0),
                        "avg_response_time": getattr(perf_result, "avg_response_time", 0),
                        "median_response_time": getattr(perf_result, "median_response_time", 0),
                        "percentile_95": getattr(perf_result, "percentile_95", 0),
                        "percentile_99": getattr(perf_result, "percentile_99", 0),
                    }
                
                # Update progress to indicate completion
                context["progress_callback"](100)
                
                result_queue.put({
                    "status": "completed",
                    "details": result_details
                })
                
            except (ValueError, AttributeError) as e:
                task_logger.error(f"[Task {task.id}] Configuration error: {e}")
                result_queue.put({
                    "status": "failed",
                    "error": str(e),
                    "category": ErrorCategory.CONFIGURATION,
                    "traceback": traceback.format_exc(),
                    "details": {"error_type": type(e).__name__}
                })
            except TimeoutError as e:
                task_logger.error(f"[Task {task.id}] Timeout error: {e}")
                result_queue.put({
                    "status": "failed",
                    "error": str(e),
                    "category": ErrorCategory.TIMEOUT,
                    "traceback": traceback.format_exc(),
                    "details": {"error_type": "TimeoutError"}
                })
            
        except Exception as e:
            task_logger.exception(f"[Task {task.id}] Performance test failed: {e}")
            result_queue.put({
                "status": "failed",
                "error": f"Performance test failed: {str(e)}",
                "category": ErrorCategory.EXECUTION,
                "traceback": traceback.format_exc(),
                "details": {"error_type": type(e).__name__}
            })
    
    def execute_gpt4all_task(self, context: Dict[str, Any]) -> None:
        """Execute GPT4All analysis."""
        task = context["task"]
        job = context["job"]
        result_queue = context["result_queue"]
        analyzer = context["services"].get("gpt4all_analyzer")
        
        if not analyzer:
            result_queue.put({
                "status": "skipped",
                "reason": "GPT4All analyzer not available"
            })
            return
        
        try:
            task_logger.info(f"[Task {task.id}] Running GPT4All analysis for {task.model}/app{task.app_num}")
            
            # Get analysis options
            options = job.analysis_options.get(AnalysisType.GPT4ALL.value, {})
            requirements = options.get("requirements")
            
            # Get requirements if not provided
            if not requirements:
                try:
                    requirements, template_name = analyzer.get_requirements_for_app(task.app_num)
                    task_logger.info(f"[Task {task.id}] Loaded {len(requirements)} requirements from '{template_name}'")
                except Exception as e:
                    task_logger.error(f"[Task {task.id}] Failed to load requirements: {e}")
                    result_queue.put({
                        "status": "failed",
                        "error": f"Failed to load requirements: {str(e)}",
                        "category": ErrorCategory.CONFIGURATION,
                        "traceback": traceback.format_exc(),
                        "details": {"error_type": type(e).__name__}
                    })
                    return
            
            if not requirements:
                result_queue.put({
                    "status": "skipped",
                    "reason": "No requirements found or provided"
                })
                return
            
            # Execute analysis
            context["progress_callback"](10)
            
            gpt_results = analyzer.check_requirements(task.model, task.app_num, requirements)
            
            context["progress_callback"](90)
            
            # Process results
            result_details = {
                "requirements": requirements,
                "results": []
            }
            
            met_count = 0
            for check in gpt_results:
                if hasattr(check, 'to_dict') and callable(check.to_dict):
                    check_dict = check.to_dict()
                elif hasattr(check, '__dataclass_fields__'):
                    check_dict = asdict(check)
                else:
                    check_dict = {"requirement": str(check)}
                
                result_details["results"].append(check_dict)
                
                # Count met requirements
                if check_dict.get("result", {}).get("met", False):
                    met_count += 1
            
            # Add summary
            result_details["summary"] = {
                "requirements_checked": len(requirements),
                "met_count": met_count
            }
            
            context["progress_callback"](100)
            
            result_queue.put({
                "status": "completed",
                "details": result_details
            })
            
        except Exception as e:
            task_logger.exception(f"[Task {task.id}] GPT4All analysis failed: {e}")
            result_queue.put({
                "status": "failed",
                "error": f"GPT4All analysis failed: {str(e)}",
                "category": ErrorCategory.EXECUTION,
                "traceback": traceback.format_exc(),
                "details": {"error_type": type(e).__name__}
            })
    
    def execute_zap_task(self, context: Dict[str, Any]) -> None:
        """Execute ZAP security scanning."""
        task = context["task"]
        job = context["job"]
        result_queue = context["result_queue"]
        scan_manager = context["services"].get("scan_manager")
        
        if not scan_manager:
            result_queue.put({
                "status": "skipped",
                "reason": "ZAP scan manager not available"
            })
            return
        
        try:
            task_logger.info(f"[Task {task.id}] Running ZAP scan for {task.model}/app{task.app_num}")
            
            # Get analysis options
            options = job.analysis_options.get(AnalysisType.ZAP.value, {})
            
            # Trigger scan
            scan_id = scan_manager.create_scan(task.model, task.app_num, options)
            
            if not scan_id:
                raise RuntimeError("Failed to create ZAP scan (no scan ID returned)")
            
            task_logger.info(f"[Task {task.id}] ZAP scan created with ID: {scan_id}")
            
            # Poll for completion with progress updates
            poll_interval = 15  # seconds
            max_polls = max(task.timeout_seconds // poll_interval, 1)
            
            for poll_num in range(max_polls):
                # Check for cancellation
                if job.cancellation_requested:
                    # Try to stop the ZAP scan
                    try:
                        scan_manager.stop_scan(task.model, task.app_num)
                        task_logger.info(f"[Task {task.id}] ZAP scan {scan_id} cancelled")
                    except Exception as stop_err:
                        task_logger.error(f"[Task {task.id}] Error stopping ZAP scan: {stop_err}")
                    
                    result_queue.put({
                        "status": "cancelled",
                        "reason": "Job cancellation requested during ZAP scan"
                    })
                    return
                
                # Get scan status
                try:
                    zap_status = scan_manager.get_scan_status(scan_id)
                    status = zap_status.get('status')
                    progress = zap_status.get('progress', 0)
                    
                    # Update task progress
                    context["progress_callback"](progress)
                    
                    if status == 'completed':
                        task_logger.info(f"[Task {task.id}] ZAP scan {scan_id} completed")
                        break
                    elif status == 'failed':
                        error_msg = zap_status.get('error', 'Unknown ZAP failure')
                        task_logger.error(f"[Task {task.id}] ZAP scan {scan_id} failed: {error_msg}")
                        result_queue.put({
                            "status": "failed",
                            "error": f"ZAP scan failed: {error_msg}",
                            "category": ErrorCategory.EXECUTION,
                            "details": {"scan_id": scan_id, "zap_status": zap_status}
                        })
                        return
                    
                    task_logger.info(f"[Task {task.id}] ZAP scan {scan_id} in progress: {progress}% ({poll_num+1}/{max_polls})")
                    
                except Exception as poll_err:
                    task_logger.error(f"[Task {task.id}] Error polling ZAP status: {poll_err}")
                    # Continue polling despite errors
                
                # Sleep before next poll
                time.sleep(poll_interval)
            else:
                # Loop completed without break (max polls reached)
                task_logger.error(f"[Task {task.id}] ZAP scan {scan_id} timed out after {max_polls} polls")
                result_queue.put({
                    "status": "failed",
                    "error": f"ZAP scan timed out after {max_polls * poll_interval} seconds",
                    "category": ErrorCategory.TIMEOUT,
                    "details": {"scan_id": scan_id}
                })
                return
            
            # Retrieve results
            try:
                zap_results = scan_manager.get_scan_results(scan_id)
                
                if zap_results is None:
                    raise RuntimeError("Failed to retrieve ZAP results after scan completion")
                
                task_logger.info(f"[Task {task.id}] Retrieved {len(zap_results)} ZAP alerts")
                
                # Process results
                result_details = {
                    "scan_id": scan_id,
                    "issues": [],
                    "zap_status": zap_status
                }
                
                # Convert ZAP vulnerabilities to dictionaries
                for alert in zap_results:
                    if hasattr(alert, 'to_dict') and callable(alert.to_dict):
                        alert_dict = alert.to_dict()
                    elif hasattr(alert, '__dataclass_fields__'):
                        alert_dict = asdict(alert)
                    elif isinstance(alert, dict):
                        alert_dict = alert
                    else:
                        alert_dict = {"description": str(alert)}
                    
                    result_details["issues"].append(alert_dict)
                
                result_queue.put({
                    "status": "completed",
                    "details": result_details
                })
                
            except Exception as result_err:
                task_logger.exception(f"[Task {task.id}] Error retrieving ZAP results: {result_err}")
                result_queue.put({
                    "status": "failed",
                    "error": f"Failed to retrieve ZAP results: {str(result_err)}",
                    "category": ErrorCategory.EXECUTION,
                    "traceback": traceback.format_exc(),
                    "details": {"scan_id": scan_id, "error_type": type(result_err).__name__}
                })
            
        except Exception as e:
            task_logger.exception(f"[Task {task.id}] ZAP scan failed: {e}")
            result_queue.put({
                "status": "failed",
                "error": f"ZAP scan failed: {str(e)}",
                "category": ErrorCategory.EXECUTION,
                "traceback": traceback.format_exc(),
                "details": {"error_type": type(e).__name__}
            })

# =============================================================================
# Batch Analysis Service
# =============================================================================

class BatchAnalysisService:
    """
    Service for managing batch analysis jobs with robust task execution,
    error handling, and resource management.
    """
    
    def __init__(self, storage: JobStorage):
        """Initialize the service."""
        self.storage = storage
        self.executor = TaskExecutor(storage)
        self._running_jobs: Dict[int, threading.Thread] = {}
        self._app: Optional[Any] = None
        
        # Configuration with defaults
        self.max_concurrent_jobs = int(os.environ.get("BATCH_MAX_JOBS", 2))
        self.max_concurrent_tasks = int(os.environ.get("BATCH_MAX_TASKS", 2))
        self.default_task_timeout = int(os.environ.get("BATCH_TASK_TIMEOUT_SECONDS", 1800))
        
        service_logger.info(f"BatchAnalysisService initialized (MaxJobs:{self.max_concurrent_jobs}, MaxTasks:{self.max_concurrent_tasks}, DefaultTimeout:{self.default_task_timeout}s)")
    
    def set_app(self, app: Any) -> None:
        """Set the Flask application instance."""
        self.app = app
        
        # Update configuration from app config if available
        if hasattr(app, 'config'):
            self.max_concurrent_jobs = max(1, app.config.get("BATCH_MAX_JOBS", self.max_concurrent_jobs))
            self.max_concurrent_tasks = max(1, app.config.get("BATCH_MAX_TASKS", self.max_concurrent_tasks))
            self.default_task_timeout = app.config.get("BATCH_TASK_TIMEOUT_SECONDS", self.default_task_timeout)
        
        service_logger.info(f"App registered with BatchAnalysisService. Config: MaxJobs:{self.max_concurrent_jobs}, MaxTasks:{self.max_concurrent_tasks}, DefaultTimeout:{self.default_task_timeout}s")
    
    def start_job(self, job_id: int) -> bool:
        """Start a job execution in a background thread."""
        job_log_prefix = f"[Job {job_id}]"
        service_logger.info(f"{job_log_prefix} Request to start job")
        
        job = self.storage.get_job(job_id)
        
        # Initial checks
        if not job:
            service_logger.error(f"{job_log_prefix} Start failed: Job not found")
            return False
        
        if job.status == JobStatus.RUNNING:
            service_logger.warning(f"{job_log_prefix} Start failed: Job already running")
            return False
        
        if not self.app:
            error_msg = "Flask app not registered with service"
            service_logger.error(f"{job_log_prefix} Start failed: {error_msg}")
            job.add_error(error_msg, ErrorCategory.CONFIGURATION)
            self.storage.update_job(job_id, status=JobStatus.ERROR, errors=job.errors)
            return False
        
        # Check concurrent job limit
        with threading.Lock():
            if len(self._running_jobs) >= self.max_concurrent_jobs:
                service_logger.warning(f"{job_log_prefix} Cannot start: Maximum concurrent jobs ({self.max_concurrent_jobs}) reached")
                self.storage.update_job(job_id, status=JobStatus.QUEUED)
                return False
            
            # Reset job state for new run
            self.storage.update_job(
                job_id,
                status=JobStatus.INITIALIZING,
                started_at=datetime.now(timezone.utc),
                completed_at=None,
                completed_tasks=0,
                errors=[],
                results_summary={},
                task_count_by_status={},
                cancellation_requested=False
            )
            
            # Create background thread
            thread_name = f"batch-job-{job_id}"
            thread = threading.Thread(
                target=self._run_job,
                args=(job_id,),
                daemon=True,
                name=thread_name
            )
            
            # Register thread and start
            self._running_jobs[job_id] = thread
            thread.start()
            
            service_logger.info(f"{job_log_prefix} Started in background thread '{thread_name}'")
            return True
    
    def _run_job(self, job_id: int) -> None:
        """Job execution logic in a background thread."""
        job_log_prefix = f"[Job {job_id}]"
        thread_name = threading.current_thread().name
        service_logger.info(f"{job_log_prefix} Job thread '{thread_name}' started")
        
        try:
            with self.app.app_context():
                service_logger.info(f"{job_log_prefix} Flask app context acquired")
                self._execute_job_workflow(job_id)
                service_logger.info(f"{job_log_prefix} Job workflow completed")
        except Exception as e:
            service_logger.exception(f"{job_log_prefix} Unhandled exception in job thread: {e}")
            
            # Update job status to failed
            job = self.storage.get_job(job_id)
            if job:
                job.add_error(
                    message=f"Unhandled exception in job thread: {str(e)}",
                    category=ErrorCategory.INTERNAL,
                    traceback=traceback.format_exc()
                )
                self.storage.update_job(job_id, status=JobStatus.FAILED, errors=job.errors, completed_at=datetime.now(timezone.utc))
        finally:
            self._cleanup_job_thread(job_id)
            service_logger.info(f"{job_log_prefix} Job thread '{thread_name}' finished")
    
    def _cleanup_job_thread(self, job_id: int) -> None:
        """Clean up after job thread completion."""
        with threading.Lock():
            if job_id in self._running_jobs:
                del self._running_jobs[job_id]
                service_logger.debug(f"[Job {job_id}] Removed from running jobs. Remaining: {list(self._running_jobs.keys())}")
            
            # Check if there are queued jobs that can be started
            queued_jobs = [j for j in self.storage.get_all_jobs() if j.status == JobStatus.QUEUED]
            if queued_jobs and len(self._running_jobs) < self.max_concurrent_jobs:
                next_job = queued_jobs[0]
                service_logger.info(f"[Job {next_job.id}] Starting queued job from cleanup")
                # Start on a new thread to avoid recursion/locking issues
                start_thread = threading.Thread(
                    target=self.start_job,
                    args=(next_job.id,),
                    daemon=True,
                    name=f"start-queued-job-{next_job.id}"
                )
                start_thread.start()
    
    def _execute_job_workflow(self, job_id: int) -> None:
        """Main job execution workflow with proper error handling."""
        job_log_prefix = f"[Job {job_id}]"
        
        # Fetch job and verify status
        job = self.storage.get_job(job_id)
        if not job:
            service_logger.error(f"{job_log_prefix} Job disappeared during execution")
            return
        
        if job.status != JobStatus.INITIALIZING:
            service_logger.warning(f"{job_log_prefix} Unexpected job status: {job.status.value}")
            return
        
        # Check and fetch required services
        service_logger.info(f"{job_log_prefix} Verifying required services")
        services, dependency_errors = self._check_required_services(job)
        
        if dependency_errors:
            for error in dependency_errors:
                job.add_error(
                    message=error,
                    category=ErrorCategory.DEPENDENCY
                )
            
            service_logger.error(f"{job_log_prefix} Job failed due to missing dependencies: {dependency_errors}")
            self.storage.update_job(job_id, status=JobStatus.FAILED, errors=job.errors, completed_at=datetime.now(timezone.utc))
            return
        
        # Set job to RUNNING state
        self.storage.update_job(job_id, status=JobStatus.RUNNING)
        
        # Generate task list
        service_logger.info(f"{job_log_prefix} Generating task list")
        tasks = self._generate_task_list(job)
        
        if not tasks:
            service_logger.warning(f"{job_log_prefix} No tasks generated")
            self.storage.update_job(job_id, status=JobStatus.COMPLETED, completed_at=datetime.now(timezone.utc))
            return
        
        # Update total task count if different from estimate
        if len(tasks) != job.total_tasks:
            self.storage.update_job(job_id, total_tasks=len(tasks))
        
        service_logger.info(f"{job_log_prefix} Generated {len(tasks)} tasks")
        
        # Create tasks in storage
        stored_tasks = []
        for model, app_num, analysis_type in tasks:
            # Get timeout for task from options or default
            options = job.analysis_options.get(analysis_type.value, {})
            timeout = options.get("timeout_seconds", self.default_task_timeout)
            
            task = self.storage.create_task(
                job_id=job_id,
                model=model,
                app_num=app_num,
                analysis_type=analysis_type,
                timeout_seconds=timeout
            )
            
            if task:
                stored_tasks.append(task)
        
        # Execute tasks with thread pool (limiting concurrent tasks)
        service_logger.info(f"{job_log_prefix} Starting execution of {len(stored_tasks)} tasks using ThreadPoolExecutor (max_workers={self.max_concurrent_tasks})")
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent_tasks, thread_name_prefix=f"task-{job_id}") as executor:
                # Submit initial batch of tasks (up to max_concurrent_tasks)
                task_queue = list(stored_tasks)
                futures = {}
                
                # Process tasks until all are done or job is cancelled
                while task_queue or futures:
                    # Check for cancellation
                    job = self.storage.get_job(job_id)
                    if job and job.cancellation_requested:
                        service_logger.info(f"{job_log_prefix} Cancellation detected during task submission")
                        self.storage.update_job(job_id, status=JobStatus.CANCELLING)
                        
                        # Mark unprocessed tasks as cancelled
                        for waiting_task in task_queue:
                            waiting_task.cancel()
                            self.storage.update_task(waiting_task.id, status=TaskStatus.CANCELLED, completed_at=datetime.now(timezone.utc))
                        
                        # Cancel futures if possible
                        for future in list(futures.keys()):
                            future.cancel()
                        
                        break
                    
                    # Submit new tasks as space becomes available
                    while task_queue and len(futures) < self.max_concurrent_tasks:
                        next_task = task_queue.pop(0)
                        
                        # Skip already cancelled tasks
                        if next_task.status == TaskStatus.CANCELLED:
                            continue
                        
                        # Create service context for the execution
                        analysis_type = next_task.analysis_type
                        
                        # Submit appropriate task based on analysis type
                        if analysis_type == AnalysisType.FRONTEND_SECURITY:
                            future = executor.submit(
                                self._execute_task_with_context,
                                next_task.id,
                                self.executor.execute_frontend_security_task,
                                services
                            )
                        elif analysis_type == AnalysisType.BACKEND_SECURITY:
                            future = executor.submit(
                                self._execute_task_with_context,
                                next_task.id,
                                self.executor.execute_backend_security_task,
                                services
                            )
                        elif analysis_type == AnalysisType.PERFORMANCE:
                            future = executor.submit(
                                self._execute_task_with_context,
                                next_task.id,
                                self.executor.execute_performance_task,
                                services
                            )
                        elif analysis_type == AnalysisType.GPT4ALL:
                            future = executor.submit(
                                self._execute_task_with_context,
                                next_task.id,
                                self.executor.execute_gpt4all_task,
                                services
                            )
                        elif analysis_type == AnalysisType.ZAP:
                            future = executor.submit(
                                self._execute_task_with_context,
                                next_task.id,
                                self.executor.execute_zap_task,
                                services
                            )
                        else:
                            service_logger.error(f"{job_log_prefix} Unknown analysis type: {analysis_type}")
                            continue
                        
                        futures[future] = next_task
                    
                    # Wait for at least one future to complete
                    if futures:
                        wait_time = 2.0  # seconds
                        done, not_done = concurrent.futures.wait(
                            futures.keys(),
                            timeout=wait_time,
                            return_when=concurrent.futures.FIRST_COMPLETED
                        )
                        
                        # Process completed futures
                        for future in done:
                            task = futures.pop(future)
                            try:
                                # Retrieve result to get exceptions
                                future.result()
                                service_logger.debug(f"{job_log_prefix} Task {task.id} completed via future")
                            except Exception as e:
                                # Most exceptions should be handled inside the task execution
                                # This is for uncaught exceptions that escaped the task context
                                service_logger.exception(f"{job_log_prefix} Unhandled exception in task {task.id}: {e}")
                    else:
                        # No futures to wait on but tasks in queue - should not happen
                        if task_queue:
                            service_logger.warning(f"{job_log_prefix} No active futures but {len(task_queue)} tasks in queue. This is unusual.")
                        time.sleep(0.1)  # Brief pause to avoid CPU spinning
                
                # Wait for remaining futures
                if futures:
                    service_logger.info(f"{job_log_prefix} Waiting for {len(futures)} remaining tasks to complete")
                    # Wait with a timeout
                    _, not_done = concurrent.futures.wait(
                        futures.keys(),
                        timeout=60,  # 1 minute max wait
                        return_when=concurrent.futures.ALL_COMPLETED
                    )
                    
                    if not_done:
                        service_logger.warning(f"{job_log_prefix} {len(not_done)} tasks did not complete within final wait period")
        
        except Exception as e:
            service_logger.exception(f"{job_log_prefix} Error during task execution: {e}")
            job = self.storage.get_job(job_id)
            if job:
                job.add_error(
                    message=f"Error during task execution: {str(e)}",
                    category=ErrorCategory.EXECUTION,
                    traceback=traceback.format_exc()
                )
                if job.status not in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                    self.storage.update_job(job_id, status=JobStatus.FAILED, errors=job.errors, completed_at=datetime.now(timezone.utc))
        
        # Ensure final status is set correctly
        job = self.storage.get_job(job_id)
        if job:
            if job.cancellation_requested and job.status != JobStatus.CANCELLED:
                self.storage.update_job(job_id, status=JobStatus.CANCELLED, completed_at=datetime.now(timezone.utc))
            elif job.status == JobStatus.RUNNING:
                # Determine final status based on tasks
                has_failed = job.task_count_by_status.get(TaskStatus.FAILED.value, 0) > 0
                has_timed_out = job.task_count_by_status.get(TaskStatus.TIMED_OUT.value, 0) > 0
                has_skipped = job.task_count_by_status.get(TaskStatus.SKIPPED.value, 0) > 0
                
                if has_failed or has_timed_out or has_skipped:
                    final_status = JobStatus.FAILED
                else:
                    final_status = JobStatus.COMPLETED
                
                self.storage.update_job(job_id, status=final_status, completed_at=datetime.now(timezone.utc))
        
        service_logger.info(f"{job_log_prefix} Job execution workflow completed")
    
    def _execute_task_with_context(self, task_id: int, executor_func: Callable, services: Dict[str, Any]) -> None:
        """Execute a task with the appropriate context and execution function."""
        with self.executor._task_execution_context(task_id) as context:
            # Add services and app context to the task context
            context["services"] = services
            context["app_context"] = self.app
            
            # Execute the task
            executor_func(context)
    
    def _check_required_services(self, job: BatchAnalysisJob) -> Tuple[Dict[str, Any], List[str]]:
        """Check and gather required services for job execution."""
        services = {}
        errors = []
        
        # Define the required services for each analysis type
        required_services = {
            AnalysisType.FRONTEND_SECURITY: [
                ("frontend_security_analyzer", "FrontendSecurityAnalyzer", "frontend_security_analyzer")
            ],
            AnalysisType.BACKEND_SECURITY: [
                ("backend_security_analyzer", "BackendSecurityAnalyzer", "backend_security_analyzer")
            ],
            AnalysisType.PERFORMANCE: [
                ("performance_tester", "LocustPerformanceTester", "performance_tester"),
                ("port_manager", "PortManager", "port_manager")
            ],
            AnalysisType.GPT4ALL: [
                ("gpt4all_analyzer", "GPT4AllAnalyzer", "gpt4all_analyzer")
            ],
            AnalysisType.ZAP: [
                ("scan_manager", "ScanManager", "scan_manager")
            ]
        }
        
        # Check for each required service based on job's analysis types
        for analysis_type in job.analysis_types:
            if analysis_type not in required_services:
                errors.append(f"Unknown analysis type: {analysis_type.value}")
                continue
            
            for attr_name, expected_class_name, service_key in required_services[analysis_type]:
                # Try to get service from Flask app
                service = getattr(self.app, attr_name, None)
                
                if not service:
                    errors.append(f"Required service '{attr_name}' for {analysis_type.value} not found on Flask app")
                    continue
                
                # Optional class name check
                if expected_class_name:
                    service_class_name = service.__class__.__name__
                    if service_class_name != expected_class_name:
                        service_logger.warning(f"[Job {job.id}] Service '{attr_name}' has unexpected class: {service_class_name} (expected {expected_class_name})")
                        # Don't mark as error, just warn
                
                # Store service for task execution
                services[service_key] = service
                service_logger.debug(f"[Job {job.id}] Found required service '{service_key}'")
            
        # Add utility functions if needed
        for util_func_name in ["get_model_index", "get_apps_for_model", "get_app_directory"]:
            # Try to get from Flask app
            if hasattr(self.app, util_func_name):
                services[util_func_name] = getattr(self.app, util_func_name)
            # Try to get from utils module
            else:
                try:
                    module_name = "utils"
                    if module_name in sys.modules:
                        util_func = getattr(sys.modules[module_name], util_func_name, None)
                        if util_func:
                            services[util_func_name] = util_func
                except Exception as e:
                    service_logger.debug(f"[Job {job.id}] Error finding utility function {util_func_name}: {e}")
        
        return services, errors
    
    def _generate_task_list(self, job: BatchAnalysisJob) -> List[Tuple[str, int, AnalysisType]]:
        """Generate list of tasks to be executed."""
        job_log_prefix = f"[Job {job.id}]"
        service_logger.info(f"{job_log_prefix} Generating tasks list")
        
        tasks = []
        
        base_path_str = self.app.config.get('APP_BASE_PATH')
        if not base_path_str:
            service_logger.error(f"{job_log_prefix} APP_BASE_PATH not found in Flask config")
            job.add_error(
                message="APP_BASE_PATH not found in Flask config",
                category=ErrorCategory.CONFIGURATION
            )
            return []
        
        base_path = Path(base_path_str)
        
        for model in job.models:
            service_logger.debug(f"{job_log_prefix} Processing model '{model}'")
            model_path = base_path / model
            
            if not model_path.is_dir():
                service_logger.warning(f"{job_log_prefix} Model directory not found: {model_path}")
                job.add_error(
                    message=f"Model directory not found: {model_path}",
                    category=ErrorCategory.CONFIGURATION
                )
                continue
            
            # Determine target apps for this model
            app_nums = []
            app_range = job.app_ranges.get(model, [])
            scan_all_apps = model in job.app_ranges and isinstance(app_range, list) and not app_range
            
            if scan_all_apps:
                # Find all app directories
                try:
                    app_nums = sorted([
                        int(item.name[3:]) for item in model_path.iterdir()
                        if item.is_dir() and item.name.startswith('app') and item.name[3:].isdigit()
                    ])
                    service_logger.debug(f"{job_log_prefix} Found apps for '{model}': {app_nums}")
                except Exception as e:
                    service_logger.error(f"{job_log_prefix} Error listing apps for '{model}': {e}")
                    job.add_error(
                        message=f"Error listing apps for '{model}': {str(e)}",
                        category=ErrorCategory.CONFIGURATION
                    )
            elif isinstance(app_range, list):
                app_nums = sorted(list(set(app_range)))
                service_logger.debug(f"{job_log_prefix} Using specified apps for '{model}': {app_nums}")
            
            # Create tasks for each app and analysis type
            for app_num in app_nums:
                app_dir = model_path / f"app{app_num}"
                if not app_dir.is_dir():
                    service_logger.warning(f"{job_log_prefix} App directory not found: {app_dir}")
                    continue
                
                for analysis_type in job.analysis_types:
                    task = (model, app_num, analysis_type)
                    tasks.append(task)
                    service_logger.debug(f"{job_log_prefix} Added task: {model}/app{app_num}/{analysis_type.value}")
        
        service_logger.info(f"{job_log_prefix} Generated {len(tasks)} tasks")
        return tasks
    
    def cancel_job(self, job_id: int) -> bool:
        """Mark a job for cancellation."""
        job_log_prefix = f"[Job {job_id}]"
        service_logger.info(f"{job_log_prefix} Request to cancel job")
        
        job = self.storage.get_job(job_id)
        if not job:
            service_logger.error(f"{job_log_prefix} Cancel failed: Job not found")
            return False
        
        if job.status not in [JobStatus.INITIALIZING, JobStatus.RUNNING, JobStatus.QUEUED]:
            service_logger.warning(f"{job_log_prefix} Cannot cancel job with status: {job.status.value}")
            return False
        
        # Mark job for cancellation
        self.storage.update_job(
            job_id, 
            cancellation_requested=True,
            status=JobStatus.CANCELLING if job.status == JobStatus.RUNNING else job.status
        )
        
        service_logger.info(f"{job_log_prefix} Job marked for cancellation")
        return True
    
    def get_job_status(self, job_id: int) -> Dict[str, Any]:
        """Get detailed job status information."""
        job_log_prefix = f"[Job {job_id}]"
        service_logger.debug(f"{job_log_prefix} Request for job status")
        
        job = self.storage.get_job(job_id)
        if not job:
            service_logger.warning(f"{job_log_prefix} Get status failed: Job not found")
            return {"error": f"Job {job_id} not found"}
        
        # Calculate progress
        progress_percent = 0
        if job.total_tasks > 0:
            progress_percent = min(100, int((job.completed_tasks / job.total_tasks) * 100))
        elif job.status in [JobStatus.COMPLETED, JobStatus.CANCELLED, JobStatus.FAILED]:
            progress_percent = 100
        
        # Prepare response
        job_dict = job.to_dict()
        
        status_response = {
            "job": job_dict,
            "progress": {
                "total": job.total_tasks,
                "completed": job.completed_tasks,
                "percent": progress_percent,
                "by_status": job.task_count_by_status
            },
            "results_summary": job.results_summary,
            "active_tasks_count": len([t for t in self.storage.get_job_tasks(job_id) if t.status == TaskStatus.RUNNING])
        }
        
        return status_response

# Global instance of the service
batch_service = BatchAnalysisService(job_storage)

# =============================================================================
# Flask Blueprint Routes
# =============================================================================

batch_analysis_bp = Blueprint(
    "batch_analysis",
    __name__,
    template_folder="templates",
    url_prefix="/batch-analysis"
)
api_logger.debug("Batch Analysis Blueprint created")

# =============================================================================
# Route Helper Functions & Decorators
# =============================================================================

def error_handler(f):
    """Decorator for handling common exceptions in Flask routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        route_name = f.__name__
        path = request.path if request else "unknown"
        api_logger.debug(f"Route '{route_name}' ({path}): Entering error handler")
        
        try:
            api_logger.debug(f"Route '{route_name}': Executing function")
            result = f(*args, **kwargs)
            api_logger.debug(f"Route '{route_name}': Function executed successfully")
            return result
        except (BadRequest, NotFound) as client_err:
            api_logger.warning(f"Route '{route_name}': Client Error {client_err.code} - {client_err.description}")
            
            # For API routes (JSON response)
            if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
                return jsonify(error=client_err.description, code=client_err.code), client_err.code
            
            # For HTML routes
            flash(f"{client_err.code}: {client_err.description}", "error")
            if client_err.code == 404:
                return redirect(url_for("batch_analysis.batch_dashboard"))
            raise client_err  # Let Flask handle other client errors
            
        except InternalServerError as server_err:
            api_logger.error(f"Route '{route_name}': Internal Server Error {server_err.code} - {server_err.description}", exc_info=True)
            
            # For API routes
            if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
                return jsonify(error="An internal server error occurred", code=500), 500
            
            # For HTML routes
            flash("An internal server error occurred. Please check logs.", "error")
            return redirect(url_for("batch_analysis.batch_dashboard"))
            
        except Exception as e:
            api_logger.exception(f"Route '{route_name}': Unhandled exception: {e}")
            
            # For API routes
            if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
                return jsonify(error=f"An unexpected error occurred: {type(e).__name__}", code=500), 500
            
            # For HTML routes
            flash(f"An unexpected error occurred: {type(e).__name__}. Please check logs.", "error")
            return redirect(url_for("batch_analysis.batch_dashboard"))
            
    return decorated_function

def get_available_models() -> List[str]:
    """Get list of available AI models."""
    api_logger.debug("Getting available models")
    
    try:
        # Try to get from AI_MODELS global
        if 'AI_MODELS' in globals():
            models = globals()['AI_MODELS']
            if isinstance(models, list):
                if models and isinstance(models[0], str):
                    return sorted(models)
                elif models and hasattr(models[0], 'name'):
                    return sorted([m.name for m in models])
        
        # Try to import from utils
        try:
            from utils import AI_MODELS
            if isinstance(AI_MODELS, list):
                if AI_MODELS and isinstance(AI_MODELS[0], str):
                    return sorted(AI_MODELS)
                elif AI_MODELS and hasattr(AI_MODELS[0], 'name'):
                    return sorted([m.name for m in AI_MODELS])
        except ImportError:
            pass
        
        # Fall back to directory scanning
        app = current_app._get_current_object()
        base_path_str = app.config.get('APP_BASE_PATH')
        if not base_path_str:
            raise ValueError("APP_BASE_PATH not found in config")
            
        base_path = Path(base_path_str)
        if not base_path.is_dir():
            raise FileNotFoundError(f"APP_BASE_PATH directory not found: {base_path}")
            
        model_names = sorted([
            item.name for item in base_path.iterdir()
            if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('_')
        ])
        
        return model_names
        
    except Exception as e:
        api_logger.error(f"Error getting available models: {e}", exc_info=True)
        return []

def parse_app_range(range_str: str) -> List[int]:
    """Parse app range string (e.g., "1-3,5,8") into list of integers."""
    if not range_str or not range_str.strip():
        return []
        
    app_nums = set()
    parts = range_str.split(',')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        if '-' in part:
            # Handle ranges like "1-5"
            try:
                start_str, end_str = part.split('-', 1)
                start = int(start_str.strip())
                end = int(end_str.strip())
                
                if start <= end and start > 0:
                    app_nums.update(range(start, end + 1))
                else:
                    api_logger.warning(f"Invalid range '{part}': start/end must be positive, start <= end")
            except ValueError:
                api_logger.warning(f"Invalid range format: '{part}'")
                
        else:
            # Handle single numbers
            try:
                num = int(part)
                if num > 0:
                    app_nums.add(num)
                else:
                    api_logger.warning(f"Invalid app number '{part}': must be positive")
            except ValueError:
                api_logger.warning(f"Invalid app number: '{part}'")
    
    return sorted(list(app_nums))

def humanize_duration(seconds: Optional[Union[int, float]]) -> str:
    """Convert seconds to human-readable duration string."""
    if seconds is None or not isinstance(seconds, (int, float)) or seconds < 0:
        return "N/A"
        
    try:
        delta = timedelta(seconds=int(seconds))
        
        if delta < timedelta(minutes=1):
            return f"{delta.seconds}s"
        elif delta < timedelta(hours=1):
            m, s = divmod(delta.seconds, 60)
            return f"{m}m {s}s"
        else:
            h, remainder = divmod(delta.seconds, 3600)
            m, s = divmod(remainder, 60)
            return f"{h}h {m}m"
            
    except (ValueError, TypeError):
        api_logger.warning(f"Could not humanize duration: {seconds}")
        return "Invalid"

# =============================================================================
# Route Handlers
# =============================================================================

@batch_analysis_bp.route("/")
@error_handler
def batch_dashboard():
    """Display the batch analysis dashboard."""
    api_logger.info(f"Request for Batch Dashboard ({request.path})")
    
    jobs_list = sorted(job_storage.get_all_jobs(), key=lambda j: j.created_at, reverse=True)
    jobs_dict_list = [job.to_dict() for job in jobs_list]
    
    all_models = get_available_models()
    
    # Calculate status statistics
    stats = {status.value: 0 for status in JobStatus}
    for job in jobs_list:
        stats[job.status.value] = stats.get(job.status.value, 0) + 1
    
    api_logger.info("Rendering batch_dashboard.html template")
    return render_template(
        "batch_dashboard.html",
        jobs=jobs_dict_list,
        all_models=all_models,
        stats=stats,
        JobStatus=JobStatus,
        AnalysisType=AnalysisType
    )

@batch_analysis_bp.route("/create", methods=["GET", "POST"])
@error_handler
def create_batch_job():
    """Handle creation of a new batch analysis job."""
    api_logger.info(f"Request: Create Batch Job ({request.path}, Method: {request.method})")
    all_models = get_available_models()
    analysis_types_available = list(AnalysisType)
    
    if request.method == "POST":
        api_logger.info("Processing POST request to create batch job")
        api_logger.debug(f"Form data: {request.form.to_dict(flat=False)}")
        
        try:
            # Validate models
            selected_models = request.form.getlist("models")
            if not selected_models:
                raise BadRequest("Please select at least one model")
                
            # Validate analysis types
            selected_analysis_types_str = request.form.getlist("analysis_types")
            selected_analysis_types = [AnalysisType(s) for s in selected_analysis_types_str]
            if not selected_analysis_types:
                raise BadRequest("Please select at least one analysis type")
                
            # Parse app ranges
            app_ranges_parsed = {}
            for m in selected_models:
                range_str = request.form.get(f"app_range_{m}", "").strip()
                app_ranges_parsed[m] = parse_app_range(range_str) if range_str else []
                
            # Parse analysis options
            all_options = {}
            
            # Frontend security options
            frontend_full_scan = request.form.get("frontend_full_scan") == "on"
            all_options[AnalysisType.FRONTEND_SECURITY.value] = {"full_scan": frontend_full_scan}
            
            # Backend security options
            backend_full_scan = request.form.get("backend_full_scan") == "on"
            all_options[AnalysisType.BACKEND_SECURITY.value] = {"full_scan": backend_full_scan}
            
            # Performance options
            try:
                perf_u = int(request.form.get("perf_users", 10))
                perf_d = int(request.form.get("perf_duration", 30))
                perf_sr = int(request.form.get("perf_spawn_rate", 1))
                
                if not (perf_u > 0 and perf_d > 0 and perf_sr > 0):
                    raise ValueError("Performance parameters must be positive")
                    
                all_options[AnalysisType.PERFORMANCE.value] = {
                    "users": perf_u,
                    "duration": perf_d,
                    "spawn_rate": perf_sr,
                    "endpoints": [{"path": "/", "method": "GET"}]
                }
            except ValueError as e:
                raise BadRequest(f"Invalid performance option: {e}")
                
            # GPT4All options
            all_options[AnalysisType.GPT4ALL.value] = {"requirements": None}
            
            # ZAP options
            zap_qs = request.form.get("zap_quick_scan") == "on"
            all_options[AnalysisType.ZAP.value] = {"quick_scan": zap_qs}
            
            # Process timeout override
            timeout_override = request.form.get("task_timeout_override", "").strip()
            if timeout_override:
                try:
                    timeout_sec = int(timeout_override)
                    if timeout_sec <= 0:
                        raise ValueError("Timeout override must be positive")
                        
                    # Add timeout to all selected analysis types
                    for atype in selected_analysis_types:
                        if atype.value not in all_options:
                            all_options[atype.value] = {}
                        all_options[atype.value]["timeout_seconds"] = timeout_sec
                        
                    api_logger.info(f"Applied task timeout override: {timeout_sec}s")
                except ValueError as e:
                    raise BadRequest(f"Invalid timeout value: {e}")
            
            # Filter options based on selected analysis types
            final_analysis_options = {
                atype.value: all_options[atype.value]
                for atype in selected_analysis_types if atype.value in all_options
            }
            
            api_logger.debug(f"Final analysis options: {final_analysis_options}")
            
            # Prepare job data
            job_data = {
                "name": request.form.get("name", "").strip() or f"Batch Scan - {datetime.now():%Y-%m-%d %H:%M:%S}",
                "description": request.form.get("description", "").strip(),
                "models": selected_models,
                "app_ranges": app_ranges_parsed,
                "analysis_types": selected_analysis_types,
                "analysis_options": final_analysis_options
            }
            
            api_logger.info("Job data prepared for creation")
            
            # Create job
            job = job_storage.create_job(job_data, current_app._get_current_object())
            api_logger.info(f"Created job {job.id}: '{job.name}'")
            
            # Start job execution
            success = batch_service.start_job(job.id)
            
            if success:
                flash(f"Job '{job.name}' (ID:{job.id}) submitted & started", "success")
            else:
                job = job_storage.get_job(job.id)  # Refresh job
                errors = [err.message for err in job.errors][:1] if job and job.errors else ["Unknown error"]
                flash(f"Job '{job.name}' (ID:{job.id}) submitted but start failed: {errors[0]}", "warning")
            
            return redirect(url_for("batch_analysis.batch_dashboard"))
            
        except (BadRequest, ValueError, TypeError) as e:
            api_logger.error(f"Form validation error: {e}")
            flash(str(e), "error")
            return render_template(
                "create_batch_job.html",
                models=all_models,
                analysis_types=analysis_types_available,
                submitted_data=request.form
            ), 400
        
    # GET request - show form
    api_logger.info("Displaying create batch job form (GET)")
    default_job_name = f"Batch Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    return render_template(
        "create_batch_job.html",
        models=all_models,
        analysis_types=analysis_types_available,
        default_job_name=default_job_name
    )

@batch_analysis_bp.route("/job/<int:job_id>")
@error_handler
def view_job(job_id: int):
    """Display detailed view for a specific job."""
    job_log_prefix = f"[Job {job_id}]"
    api_logger.info(f"{job_log_prefix} View job request")
    
    # Get job status
    status_data = batch_service.get_job_status(job_id)
    
    if "error" in status_data:
        raise NotFound(status_data["error"])
        
    # Get job results
    results_list = sorted(
        job_storage.get_results(job_id),
        key=lambda r: (r.model, r.app_num, r.analysis_type.value)
    )
    
    results_dict_list = [r.to_dict() for r in results_list]
    api_logger.info(f"{job_log_prefix} Found {len(results_dict_list)} results")
    
    job_info_dict = status_data.get('job')
    if not job_info_dict:
        api_logger.error(f"{job_log_prefix} Missing 'job' dict in status")
        raise InternalServerError("Job info missing")
        
    return render_template(
        "view_job.html",
        job=job_info_dict,
        status_data=status_data,
        results=results_dict_list,
        JobStatus=JobStatus,
        AnalysisType=AnalysisType
    )

@batch_analysis_bp.route("/job/<int:job_id>/status")
@error_handler
def get_job_status_api(job_id: int):
    """API endpoint to get job status."""
    job_log_prefix = f"[Job {job_id}]"
    api_logger.info(f"{job_log_prefix} API status request")
    
    status_data = batch_service.get_job_status(job_id)
    
    if "error" in status_data:
        raise NotFound(status_data["error"])
        
    return jsonify(status_data)

@batch_analysis_bp.route("/job/<int:job_id>/cancel", methods=["POST"])
@error_handler
def cancel_job_api(job_id: int):
    """API endpoint to cancel a running job."""
    job_log_prefix = f"[Job {job_id}]"
    api_logger.info(f"{job_log_prefix} API cancel request")
    
    success = batch_service.cancel_job(job_id)
    
    if success:
        return jsonify({
            "success": True,
            "status": "cancelling",
            "message": "Job marked for cancellation"
        })
    else:
        # Provide specific reason for failure
        job = job_storage.get_job(job_id)
        
        if not job:
            raise NotFound(f"Job {job_id} not found")
        elif job.status not in [JobStatus.INITIALIZING, JobStatus.RUNNING, JobStatus.QUEUED]:
            raise BadRequest(f"Job cannot be cancelled (status: {job.status.value})")
        else:
            raise InternalServerError("Cancel request failed unexpectedly")

@batch_analysis_bp.route("/job/<int:job_id>/delete", methods=["POST"])
@error_handler
def delete_job_api(job_id: int):
    """API endpoint to delete a job."""
    job_log_prefix = f"[Job {job_id}]"
    api_logger.info(f"{job_log_prefix} API delete request")
    
    # Check job status before attempting delete
    job = job_storage.get_job(job_id)
    
    if not job:
        raise NotFound(f"Job {job_id} not found")
        
    if job.status in [JobStatus.RUNNING, JobStatus.INITIALIZING, JobStatus.CANCELLING]:
        raise BadRequest(f"Cannot delete a {job.status.value} job. Cancel it first.")
        
    success = job_storage.delete_job(job_id)
    
    if success:
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        
        if not is_ajax:
            flash(f"Job {job_id} deleted", "success")
            return redirect(url_for("batch_analysis.batch_dashboard"))
        else:
            return jsonify({
                "success": True,
                "message": f"Job {job_id} deleted"
            })
    else:
        # This should not happen if job exists and isn't running
        if not job_storage.get_job(job_id):
            raise NotFound(f"Job {job_id} not found (disappeared)")
        else:
            raise InternalServerError("Delete failed unexpectedly")

@batch_analysis_bp.route("/result/<int:result_id>")
@error_handler
def view_result(result_id: int):
    """Display detailed view for a specific result."""
    res_log_prefix = f"[Result {result_id}]"
    api_logger.info(f"{res_log_prefix} View result request")
    
    result = job_storage.get_result(result_id)
    
    if not result:
        raise NotFound(f"Result {result_id} not found")
        
    job = job_storage.get_job(result.job_id)
    
    if not job:
        api_logger.error(f"{res_log_prefix} Parent job {result.job_id} missing")
        raise InternalServerError("Parent job missing")
        
    try:
        job_dict = job.to_dict()
        result_dict = result.to_dict()
    except Exception as e:
        api_logger.exception(f"{res_log_prefix} Serialization error: {e}")
        raise InternalServerError("Data preparation error")
        
    # Format details for display
    full_details_json = None
    try:
        # Pretty-print the details
        full_details_json = json.dumps(result.details, indent=2, default=str)
    except Exception as e:
        api_logger.warning(f"{res_log_prefix} Could not JSON format details: {e}")
        full_details_json = f"Error displaying full details: {e}\n\nRaw Details:\n{result.details}"
        
    return render_template(
        "view_result.html",
        result=result_dict,
        job=job_dict,
        full_details_json=full_details_json,
        AnalysisType=AnalysisType,
        JobStatus=JobStatus
    )

# =============================================================================
# Module Initialization
# =============================================================================

def init_batch_analysis(app: Any) -> None:
    """Initialize the batch analysis module with a Flask application."""
    module_logger.info("Initializing Batch Analysis Module...")
    
    # Ensure APP_BASE_PATH is configured
    base_path_key = 'APP_BASE_PATH'
    if base_path_key not in app.config or not app.config[base_path_key]:
        default_path = Path(app.config.get('BASE_DIR', Path(app.root_path).parent))
        app.config[base_path_key] = default_path
        module_logger.warning(f"{base_path_key} not configured. Using default: {app.config[base_path_key]}")
    else:
        app.config[base_path_key] = Path(app.config[base_path_key])
        
    module_logger.info(f"Using {base_path_key}: {app.config[base_path_key]}")
    
    # Register app with service
    try:
        batch_service.set_app(app)
    except Exception as e:
        module_logger.exception(f"Failed to register Flask app with BatchAnalysisService: {e}")
    
    # Add Jinja helpers
    module_logger.debug("Adding helpers to Jinja environment")
    try:
        app.jinja_env.filters['humanize_duration'] = humanize_duration
        app.jinja_env.globals.update(AnalysisType=AnalysisType)
        app.jinja_env.globals.update(JobStatus=JobStatus)
        app.jinja_env.globals.update(TaskStatus=TaskStatus)
        app.jinja_env.globals.update(now_utc=lambda: datetime.now(timezone.utc))
        module_logger.debug("Jinja helpers added successfully")
    except Exception as e:
        module_logger.error(f"Failed to add Jinja helpers: {e}")
    
    # Check for required services
    module_logger.debug("Checking for required service instances on app context")
    required_attrs = {
        AnalysisType.FRONTEND_SECURITY.value: 'frontend_security_analyzer',
        AnalysisType.BACKEND_SECURITY.value: 'backend_security_analyzer',
        AnalysisType.PERFORMANCE.value: 'performance_tester',
        AnalysisType.GPT4ALL.value: 'gpt4all_analyzer',
        AnalysisType.ZAP.value: 'scan_manager'
    }
    
    missing = [f"{attr} (for {atype})" for atype, attr in required_attrs.items() 
               if not hasattr(app, attr) or getattr(app, attr) is None]
    
    if missing:
        module_logger.error(f"Missing required services: {', '.join(missing)}. Related tasks will fail.")
    else:
        module_logger.info("All required service attributes found on app context")
    
    # Check for utility classes/functions
    port_manager_available = False
    try:
        from services import PortManager
        port_manager_available = True
    except ImportError:
        pass
        
    if not port_manager_available:
        module_logger.error("PortManager class unavailable. Performance tasks will fail.")
    else:
        module_logger.info("PortManager class is available")
    
    module_logger.info("Batch Analysis Module initialization complete")

# Initialize module state
module_logger.info("Batch Analysis module loaded (Completely Rewritten Version)")