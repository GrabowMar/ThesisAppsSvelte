"""
Batch Security Analysis Module

This module provides functionality for running batch security analysis 
on both frontend and backend code across multiple applications or models.
"""

import asyncio
import json
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set, Union

from flask import Blueprint, current_app, jsonify, render_template, request, url_for, g, redirect, flash

# Setup module-level logger
logger = logging.getLogger(__name__)

# Define Blueprint for routes
batch_analysis_bp = Blueprint("batch_analysis", __name__, template_folder="templates")

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
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        # Convert datetime objects to ISO format strings
        for key in ['created_at', 'started_at', 'completed_at']:
            if result[key] is not None:
                result[key] = result[key].isoformat()
        return result


@dataclass
class BatchAnalysisResult:
    """Represents a single analysis result within a batch job"""
    id: int
    job_id: int
    model: str
    app_num: int
    status: str
    scan_type: ScanType
    issues_count: int = 0
    high_severity: int = 0
    medium_severity: int = 0
    low_severity: int = 0
    scan_time: Optional[datetime] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        if result['scan_time'] is not None:
            result['scan_time'] = result['scan_time'].isoformat()
        return result


# =============================================================================
# In-memory Storage (replace with database in production)
# =============================================================================
class InMemoryJobStorage:
    """Simple in-memory storage for batch analysis jobs and results"""
    def __init__(self):
        self.jobs: Dict[int, BatchAnalysisJob] = {}
        self.results: Dict[int, List[BatchAnalysisResult]] = {}
        self.next_job_id = 1
        self.next_result_id = 1
        self._lock = threading.RLock()
    
    def create_job(self, job_data: Dict[str, Any]) -> BatchAnalysisJob:
        """Create a new batch analysis job"""
        with self._lock:
            job_id = self.next_job_id
            self.next_job_id += 1
            
            job = BatchAnalysisJob(
                id=job_id,
                name=job_data.get('name', f'Batch Job {job_id}'),
                description=job_data.get('description', ''),
                created_at=datetime.now(),
                models=job_data.get('models', []),
                app_ranges=job_data.get('app_ranges', {}),
                scan_options=job_data.get('scan_options', {}),
                scan_type=job_data.get('scan_type', ScanType.FRONTEND),
            )
            
            # Calculate total tasks based on scan type
            total_tasks = 0
            for model in job.models:
                app_range = job.app_ranges.get(model, [])
                if not app_range and model in job.app_ranges:
                    # Empty list means "all apps"
                    # We'll determine the count when running
                    # For now, just use a placeholder
                    total_tasks += 10
                else:
                    app_count = len(app_range)
                    # For BOTH scan type, we count each app twice (frontend + backend)
                    if job.scan_type == ScanType.BOTH:
                        app_count *= 2
                    total_tasks += app_count
            
            job.total_tasks = total_tasks
            self.jobs[job_id] = job
            self.results[job_id] = []
            
            return job
    
    def get_job(self, job_id: int) -> Optional[BatchAnalysisJob]:
        """Get a job by ID"""
        return self.jobs.get(job_id)
    
    def get_all_jobs(self) -> List[BatchAnalysisJob]:
        """Get all jobs"""
        return list(self.jobs.values())
    
    def update_job(self, job_id: int, **kwargs) -> Optional[BatchAnalysisJob]:
        """Update a job"""
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                return None
            
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            
            return job
    
    def add_result(self, job_id: int, result_data: Dict[str, Any]) -> BatchAnalysisResult:
        """Add a result to a job"""
        with self._lock:
            result_id = self.next_result_id
            self.next_result_id += 1
            
            result = BatchAnalysisResult(
                id=result_id,
                job_id=job_id,
                model=result_data.get('model', ''),
                app_num=result_data.get('app_num', 0),
                status=result_data.get('status', 'completed'),
                scan_type=result_data.get('scan_type', ScanType.FRONTEND),
                issues_count=result_data.get('issues_count', 0),
                high_severity=result_data.get('high_severity', 0),
                medium_severity=result_data.get('medium_severity', 0),
                low_severity=result_data.get('low_severity', 0),
                scan_time=result_data.get('scan_time', datetime.now()),
                details=result_data.get('details', {})
            )
            
            if job_id in self.results:
                self.results[job_id].append(result)
            else:
                self.results[job_id] = [result]
            
            # Update job completion stats
            job = self.jobs.get(job_id)
            if job:
                job.completed_tasks += 1
                if job.completed_tasks >= job.total_tasks:
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.now()
            
            return result
    
    def get_results(self, job_id: int) -> List[BatchAnalysisResult]:
        """Get all results for a job"""
        return self.results.get(job_id, [])
    
    def get_result(self, result_id: int) -> Optional[BatchAnalysisResult]:
        """Get a specific result by ID"""
        for results in self.results.values():
            for result in results:
                if result.id == result_id:
                    return result
        return None
    
    def delete_job(self, job_id: int) -> bool:
        """Delete a job and all its results"""
        with self._lock:
            if job_id in self.jobs:
                del self.jobs[job_id]
                if job_id in self.results:
                    del self.results[job_id]
                return True
            return False


# Global storage instance
job_storage = InMemoryJobStorage()


# =============================================================================
# Batch Analysis Functionality
# =============================================================================
class BatchAnalysisService:
    """Service for executing batch analysis jobs"""
    def __init__(self, storage: InMemoryJobStorage, app=None):
        self.storage = storage
        self._running_jobs: Dict[int, threading.Thread] = {}
        self._cancel_flags: Set[int] = set()
        self.max_concurrent_jobs = 2
        self.max_concurrent_tasks = 5
        self.app = app  # Store the Flask app instance
    
    def set_app(self, app):
        """Set the Flask app instance"""
        self.app = app
    
    def start_job(self, job_id: int) -> bool:
        """Start a batch analysis job in a background thread"""
        job = self.storage.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return False
        
        if job.status == JobStatus.RUNNING:
            logger.warning(f"Job {job_id} is already running")
            return False
        
        if len(self._running_jobs) >= self.max_concurrent_jobs:
            logger.warning(f"Maximum number of concurrent jobs ({self.max_concurrent_jobs}) reached")
            return False
        
        # Update job status
        self.storage.update_job(
            job_id, 
            status=JobStatus.RUNNING,
            started_at=datetime.now()
        )
        
        # Start job in a background thread
        thread = threading.Thread(
            target=self._run_job,
            args=(job_id,),
            daemon=True
        )
        self._running_jobs[job_id] = thread
        thread.start()
        
        return True
    
    def _run_job(self, job_id: int) -> None:
        """Execute the batch analysis job"""
        job = self.storage.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        try:
            logger.info(f"Starting batch job {job_id}: {job.name}")
            
            # Generate task list
            tasks = []
            for model in job.models:
                app_range = job.app_ranges.get(model, [])
                if not app_range and model in job.app_ranges:
                    # Empty list means "all apps" - get apps from file system
                    apps = self._get_all_apps_for_model(model)
                    for app_num in apps:
                        if job.scan_type == ScanType.FRONTEND or job.scan_type == ScanType.BOTH:
                            tasks.append((model, app_num, ScanType.FRONTEND))
                        if job.scan_type == ScanType.BACKEND or job.scan_type == ScanType.BOTH:
                            tasks.append((model, app_num, ScanType.BACKEND))
                else:
                    for app_num in app_range:
                        if job.scan_type == ScanType.FRONTEND or job.scan_type == ScanType.BOTH:
                            tasks.append((model, app_num, ScanType.FRONTEND))
                        if job.scan_type == ScanType.BACKEND or job.scan_type == ScanType.BOTH:
                            tasks.append((model, app_num, ScanType.BACKEND))
            
            # Update total tasks count
            total_tasks = len(tasks)
            self.storage.update_job(job_id, total_tasks=total_tasks)
            
            # Execute tasks
            with ThreadPoolExecutor(max_workers=self.max_concurrent_tasks) as executor:
                future_to_task = {
                    executor.submit(self._analyze_app, job_id, model, app_num, scan_type, job.scan_options): (model, app_num, scan_type)
                    for model, app_num, scan_type in tasks
                }
                
                # Check for cancellation before waiting for results
                if job_id in self._cancel_flags:
                    logger.info(f"Job {job_id} was canceled")
                    self.storage.update_job(job_id, status=JobStatus.CANCELED)
                
                # Wait for all tasks to complete
                for future in concurrent.futures.as_completed(future_to_task):
                    try:
                        future.result()
                        # Check for cancellation after each task
                        if job_id in self._cancel_flags:
                            logger.info(f"Job {job_id} was canceled after a task completed")
                            self.storage.update_job(job_id, status=JobStatus.CANCELED)
                            break
                    except Exception as e:
                        model, app_num, scan_type = future_to_task[future]
                        error_msg = f"Error analyzing {model}/app{app_num} ({scan_type}): {str(e)}"
                        logger.error(error_msg)
                        self.storage.update_job(
                            job_id,
                            errors=job.errors + [error_msg]
                        )
            
            # Update job status if not canceled
            if job_id not in self._cancel_flags:
                self.storage.update_job(
                    job_id,
                    status=JobStatus.COMPLETED,
                    completed_at=datetime.now()
                )
            
        except Exception as e:
            logger.exception(f"Error running batch job {job_id}: {e}")
            self.storage.update_job(
                job_id,
                status=JobStatus.FAILED,
                errors=job.errors + [str(e)]
            )
        finally:
            # Remove from running jobs
            if job_id in self._running_jobs:
                del self._running_jobs[job_id]
            
            # Clear cancel flag if present
            if job_id in self._cancel_flags:
                self._cancel_flags.remove(job_id)
    
    def _get_all_apps_for_model(self, model: str) -> List[int]:
        """Get all app numbers for a model from the file system"""
        base_path = Path(model)
        if not base_path.exists():
            return []
        
        app_nums = []
        for app_dir in base_path.iterdir():
            if app_dir.is_dir() and app_dir.name.startswith("app"):
                try:
                    app_num = int(app_dir.name.replace("app", ""))
                    app_nums.append(app_num)
                except ValueError:
                    continue
        
        return sorted(app_nums)
    
    def _analyze_app(self, job_id: int, model: str, app_num: int, scan_type: ScanType, scan_options: Dict[str, Any]) -> None:
        """
        Run security analysis for a single app based on the scan type
        """
        if job_id in self._cancel_flags:
            logger.info(f"Skipping analysis of {model}/app{app_num} ({scan_type}) - job {job_id} was canceled")
            return
        
        logger.info(f"Analyzing {model}/app{app_num} ({scan_type}) for job {job_id}")
        
        try:
            # Check if we have the Flask app
            if not self.app:
                raise RuntimeError("Flask app not available. Make sure to set it with set_app()")
                
            # Use app context to access extensions
            with self.app.app_context():
                # Determine scan mode from options
                full_scan = scan_options.get("full_scan", False)
                
                if scan_type == ScanType.FRONTEND:
                    # Run frontend security analysis
                    analyzer = self.app.frontend_security_analyzer
                    issues, tool_status, _ = analyzer.run_security_analysis(
                        model, app_num, use_all_tools=full_scan
                    )
                    summary = analyzer.get_analysis_summary(issues)
                
                elif scan_type == ScanType.BACKEND:
                    # Run backend security analysis
                    from backend_security_analysis import BackendSecurityAnalyzer
                    
                    # Create analyzer with the app's base path
                    base_path = Path(self.app.config.get('APP_BASE_PATH', '.'))
                    analyzer = BackendSecurityAnalyzer(base_path)
                    
                    # Run backend analysis
                    issues, tool_status, _ = analyzer.run_security_analysis(
                        model, app_num, use_all_tools=full_scan
                    )
                    summary = analyzer.get_analysis_summary(issues)
                
                else:
                    raise ValueError(f"Unsupported scan type: {scan_type}")
            
            # Store result (outside app context)
            self.storage.add_result(
                job_id,
                {
                    "model": model,
                    "app_num": app_num,
                    "scan_type": scan_type,
                    "status": "completed",
                    "issues_count": len(issues),
                    "high_severity": summary["severity_counts"]["HIGH"],
                    "medium_severity": summary["severity_counts"]["MEDIUM"],
                    "low_severity": summary["severity_counts"]["LOW"],
                    "scan_time": datetime.now(),
                    "details": {
                        "issues": [asdict(issue) for issue in issues],
                        "summary": summary,
                        "tool_status": tool_status
                    }
                }
            )
            
            logger.info(f"Completed analysis of {model}/app{app_num} ({scan_type}) for job {job_id}")
            
        except Exception as e:
            logger.error(f"Error analyzing {model}/app{app_num} ({scan_type}) for job {job_id}: {e}")
            
            # Store error result
            self.storage.add_result(
                job_id,
                {
                    "model": model,
                    "app_num": app_num,
                    "scan_type": scan_type,
                    "status": "failed",
                    "scan_time": datetime.now(),
                    "details": {
                        "error": str(e)
                    }
                }
            )
    
    def cancel_job(self, job_id: int) -> bool:
        """Cancel a running job"""
        job = self.storage.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return False
        
        if job.status != JobStatus.RUNNING:
            logger.warning(f"Cannot cancel job {job_id} - not running")
            return False
        
        # Mark for cancellation
        self._cancel_flags.add(job_id)
        
        # Update job status
        self.storage.update_job(job_id, status=JobStatus.CANCELED)
        
        return True
    
    def get_job_status(self, job_id: int) -> Dict[str, Any]:
        """Get detailed status information for a job"""
        job = self.storage.get_job(job_id)
        if not job:
            return {"error": "Job not found"}
        
        results = self.storage.get_results(job_id)
        
        # Group results by scan type for the summary
        frontend_results = [r for r in results if r.scan_type == ScanType.FRONTEND]
        backend_results = [r for r in results if r.scan_type == ScanType.BACKEND]
        
        return {
            "id": job.id,
            "name": job.name,
            "models": job.models,
            "status": job.status,
            "scan_type": job.scan_type,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "progress": {
                "total": job.total_tasks,
                "completed": job.completed_tasks,
                "percent": int(job.completed_tasks / max(1, job.total_tasks) * 100)
            },
            "results_summary": {
                "total": len(results),
                "completed": sum(1 for r in results if r.status == "completed"),
                "failed": sum(1 for r in results if r.status == "failed"),
                "frontend": {
                    "total": len(frontend_results),
                    "completed": sum(1 for r in frontend_results if r.status == "completed"),
                    "failed": sum(1 for r in frontend_results if r.status == "failed"),
                    "issues": {
                        "total": sum(r.issues_count for r in frontend_results),
                        "high": sum(r.high_severity for r in frontend_results),
                        "medium": sum(r.medium_severity for r in frontend_results),
                        "low": sum(r.low_severity for r in frontend_results)
                    }
                },
                "backend": {
                    "total": len(backend_results),
                    "completed": sum(1 for r in backend_results if r.status == "completed"),
                    "failed": sum(1 for r in backend_results if r.status == "failed"),
                    "issues": {
                        "total": sum(r.issues_count for r in backend_results),
                        "high": sum(r.high_severity for r in backend_results),
                        "medium": sum(r.medium_severity for r in backend_results),
                        "low": sum(r.low_severity for r in backend_results)
                    }
                },
                "issues": {
                    "total": sum(r.issues_count for r in results),
                    "high": sum(r.high_severity for r in results),
                    "medium": sum(r.medium_severity for r in results),
                    "low": sum(r.low_severity for r in results)
                }
            },
            "errors": job.errors,
            "scan_options": job.scan_options
        }


# Create a service instance - but don't initialize with app yet
batch_service = BatchAnalysisService(job_storage)

# Missing import
import concurrent.futures

# =============================================================================
# Error Handler Decorator
# =============================================================================
def error_handler(f):
    """Error handling decorator for routes"""
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {e}", exc_info=True)
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"error": str(e)}), 500
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for('batch_analysis.batch_dashboard'))
    return wrapped


# =============================================================================
# Blueprint Routes
# =============================================================================
@batch_analysis_bp.route("/")
@error_handler
def batch_dashboard():
    """Display the batch analysis dashboard."""
    jobs = job_storage.get_all_jobs()
    
    # Sort jobs by creation date, newest first
    jobs.sort(key=lambda j: j.created_at, reverse=True)
    
    # Get all available models for the form
    all_models = []
    try:
        # Avoid circular import
        from app import AI_MODELS
        all_models = [m.name for m in AI_MODELS]
    except ImportError:
        logger.warning("Could not import AI_MODELS from app, using empty list")
    
    return render_template(
        "batch_dashboard.html",
        jobs=jobs,
        all_models=all_models,
        active_jobs=sum(1 for j in jobs if j.status == JobStatus.RUNNING),
        completed_jobs=sum(1 for j in jobs if j.status == JobStatus.COMPLETED),
        failed_jobs=sum(1 for j in jobs if j.status in (JobStatus.FAILED, JobStatus.CANCELED))
    )


@batch_analysis_bp.route("/create", methods=["GET", "POST"])
@error_handler
def create_batch_job():
    """Create a new batch analysis job."""
    # Avoid circular import
    all_models = []
    try:
        from app import AI_MODELS
        all_models = [m.name for m in AI_MODELS]
    except ImportError:
        logger.warning("Could not import AI_MODELS from app, using empty list")
        all_models = []  # Default to empty list if import fails
    
    if request.method == "POST":
        try:
            # Parse form data
            models = request.form.getlist("models")
            if not models:
                flash("Please select at least one model", "error")
                return render_template("create_batch_job.html", models=all_models)
            
            job_data = {
                "name": request.form.get("name", "New Batch Job"),
                "description": request.form.get("description", ""),
                "models": models,
                "app_ranges": {},
                "scan_type": request.form.get("scan_type", ScanType.FRONTEND),
                "scan_options": {
                    "full_scan": request.form.get("full_scan") == "on"
                }
            }
            
            # Process app ranges for each model
            for model in job_data["models"]:
                range_str = request.form.get(f"app_range_{model}", "")
                if range_str.strip():
                    # Parse ranges like "1-3,5,7-9"
                    app_nums = []
                    for part in range_str.split(","):
                        part = part.strip()
                        if not part:
                            continue
                            
                        if "-" in part:
                            try:
                                start, end = map(int, part.split("-"))
                                app_nums.extend(range(start, end + 1))
                            except ValueError:
                                logger.warning(f"Invalid range format: {part}")
                        else:
                            try:
                                app_nums.append(int(part.strip()))
                            except ValueError:
                                logger.warning(f"Invalid app number: {part}")
                                continue
                    job_data["app_ranges"][model] = sorted(set(app_nums))
                else:
                    # Empty means "all apps"
                    job_data["app_ranges"][model] = []
            
            # Create job
            job = job_storage.create_job(job_data)
            
            # Start job immediately
            success = batch_service.start_job(job.id)
            if not success:
                flash(f"Batch job '{job.name}' created but could not be started immediately.", "warning")
            else:
                flash(f"Batch job '{job.name}' created and started.", "success")
                
            return redirect(url_for("batch_analysis.view_job", job_id=job.id))
            
        except Exception as e:
            logger.error(f"Error creating batch job: {e}", exc_info=True)
            flash(f"Error creating batch job: {str(e)}", "error")
            return render_template("create_batch_job.html", models=all_models)
    
    # GET request - show form
    return render_template(
        "create_batch_job.html",
        models=all_models
    )


@batch_analysis_bp.route("/job/<int:job_id>")
@error_handler
def view_job(job_id: int):
    """View details of a specific batch job."""
    job = job_storage.get_job(job_id)
    if not job:
        flash(f"Job {job_id} not found", "error")
        return redirect(url_for("batch_analysis.batch_dashboard"))
    
    # Get results
    results = job_storage.get_results(job_id)
    
    # Sort results by model and app number
    results.sort(key=lambda r: (r.model, r.app_num, r.scan_type))
    
    # Get detailed status for the job
    job_status = batch_service.get_job_status(job_id)
    
    return render_template(
        "view_job.html",
        job=job,
        results=results,
        status=job_status
    )

@batch_analysis_bp.route("/job/<int:job_id>/status")
@error_handler
def get_job_status(job_id: int):
    """Get the status of a batch job."""
    status = batch_service.get_job_status(job_id)
    return jsonify(status)


@batch_analysis_bp.route("/job/<int:job_id>/cancel", methods=["POST"])
@error_handler
def cancel_job(job_id: int):
    """Cancel a batch job."""
    success = batch_service.cancel_job(job_id)
    
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        if success:
            return jsonify({"status": "canceled"})
        else:
            return jsonify({"error": "Failed to cancel job"}), 400
    
    if success:
        flash(f"Job {job_id} canceled successfully", "success")
    else:
        flash(f"Failed to cancel job {job_id}", "error")
    
    return redirect(url_for("batch_analysis.view_job", job_id=job_id))


@batch_analysis_bp.route("/job/<int:job_id>/results")
@error_handler
def get_job_results(job_id: int):
    """Get all results for a batch job."""
    results = job_storage.get_results(job_id)
    return jsonify({
        "results": [r.to_dict() for r in results]
    })


@batch_analysis_bp.route("/result/<int:result_id>")
@error_handler
def view_result(result_id: int):
    """View detailed information about a specific result."""
    result = job_storage.get_result(result_id)
    if not result:
        flash(f"Result {result_id} not found", "error")
        return redirect(url_for("batch_analysis.batch_dashboard"))
    
    job = job_storage.get_job(result.job_id)
    
    return render_template(
        "view_result.html",
        result=result,
        job=job,
        issues=result.details.get("issues", []),
        summary=result.details.get("summary", {}),
        tool_status=result.details.get("tool_status", {})
    )


@batch_analysis_bp.route("/result/<int:result_id>/data")
@error_handler
def get_result_data(result_id: int):
    """Get the data for a specific result."""
    result = job_storage.get_result(result_id)
    if not result:
        return jsonify({"error": "Result not found"}), 404
    
    return jsonify(result.to_dict())


# =============================================================================
# Initialization Function
# =============================================================================
def init_batch_analysis(app):
    """Initialize batch analysis module."""
    # Pass the Flask app to the service
    batch_service.set_app(app)
    
    # Add templates folder if needed
    if not os.path.exists(os.path.join(app.root_path, "templates")):
        logger.warning("Templates directory not found, batch analysis templates may not be available")
    
    # Check for required templates
    templates_to_create = [
        "batch_dashboard.html",
        "create_batch_job.html",
        "view_job.html",
        "view_result.html"
    ]
    
    templates_dir = os.path.join(app.root_path, "templates")
    os.makedirs(templates_dir, exist_ok=True)
    
    for template in templates_to_create:
        template_path = os.path.join(templates_dir, template)
        if not os.path.exists(template_path):
            logger.warning(f"Template {template} not found, using placeholder")
            # Create a minimal placeholder template
            with open(template_path, "w") as f:
                f.write(f"""
{{% extends "base.html" %}}
{{% block content %}}
<div class="p-4">
    <h1 class="text-xl font-bold mb-4">{template.replace('.html', '').replace('_', ' ').title()}</h1>
    <p>This is a placeholder template. Please create a proper template file at {template_path}</p>
</div>
{{% endblock %}}
""")
    
    logger.info("Batch analysis module initialized")