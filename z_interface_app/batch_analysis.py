import json
import threading
import time
from pathlib import Path
from flask import Blueprint, current_app, jsonify, request, render_template, flash, url_for, redirect
from datetime import datetime

from utils import JsonResultsManager, get_apps_for_model, get_scan_manager, APIResponse, get_model_index, PortManager
from logging_service import create_logger_for_component

batch_analysis_bp = Blueprint("batch_analysis", __name__, url_prefix="/batch_analysis")
logger = create_logger_for_component('batch_analysis')

# Lock for managing batch processes
batch_processes_lock = threading.Lock()
active_batch_processes = {} # Store status of ongoing batch processes: key: "model-app_num", value: dict_with_info

_batch_results_manager = None

def get_batch_results_manager():
    """Initializes and returns the JsonResultsManager for batch summaries."""
    global _batch_results_manager
    if _batch_results_manager is None and current_app:
        base_dir = Path(current_app.config.get("BASE_DIR", "."))
        # Batch summaries will be stored in a subdirectory to keep them separate
        # JsonResultsManager saves to base_path / "results" / model_arg / app_num_arg / file_name_arg
        # Here, 'model_arg' will be "_batch_runs" and 'app_num_arg' will be the batch_id.
        _batch_results_manager = JsonResultsManager(base_path=base_dir, module_name="batch_summary_module")
    elif _batch_results_manager is None:
        # Fallback if current_app is not available (e.g., during testing outside app context)
        # This might occur if this function is called too early or from a script without app context
        logger.warning("Attempting to get batch_results_manager without Flask app context. Using default Path.")
        _batch_results_manager = JsonResultsManager(base_path=Path("."), module_name="batch_summary_module_fallback")

    return _batch_results_manager


def run_single_app_analyses(app_context, model: str, app_num: int, analyses_to_run: list, batch_id: str):
    """
    Runs all specified analyses for a single app within the given Flask app context.
    """
    with app_context: # Ensure operations run within the correct Flask app context
        logger.info(f"Thread {threading.get_ident()}: Starting analyses for {model}/app{app_num} in batch {batch_id}")
        results_summary = {
            "model": model,
            "app_num": app_num,
            "batch_id": batch_id,
            "timestamp": datetime.now().isoformat(),
            "status": "in_progress",
            "analyses": {}
        }
        overall_success = True

        try:
            # Backend Security Analysis
            if "backend_security" in analyses_to_run:
                logger.info(f"Starting backend security analysis for {model}/app{app_num}")
                if hasattr(current_app, 'backend_security_analyzer') and current_app.backend_security_analyzer:
                    try:
                        _, tool_status, _ = current_app.backend_security_analyzer.run_security_analysis(model, app_num, use_all_tools=True, force_rerun=True)
                        results_summary["analyses"]["backend_security"] = {"status": "completed", "tool_status": tool_status}
                    except Exception as e:
                        logger.error(f"Backend security analysis failed for {model}/app{app_num}: {e}", exc_info=True)
                        results_summary["analyses"]["backend_security"] = {"status": "failed", "error": str(e)}
                        overall_success = False
                else:
                    results_summary["analyses"]["backend_security"] = {"status": "skipped", "reason": "Backend Security Analyzer not available"}
                    logger.warning(f"Skipping backend security for {model}/app{app_num}: Analyzer not found.")


            # Frontend Security Analysis
            if "frontend_security" in analyses_to_run:
                logger.info(f"Starting frontend security analysis for {model}/app{app_num}")
                if hasattr(current_app, 'frontend_security_analyzer') and current_app.frontend_security_analyzer:
                    try:
                        _, tool_status, _ = current_app.frontend_security_analyzer.run_security_analysis(model, app_num, use_all_tools=True, force_rerun=True)
                        results_summary["analyses"]["frontend_security"] = {"status": "completed", "tool_status": tool_status}
                    except Exception as e:
                        logger.error(f"Frontend security analysis failed for {model}/app{app_num}: {e}", exc_info=True)
                        results_summary["analyses"]["frontend_security"] = {"status": "failed", "error": str(e)}
                        overall_success = False
                else:
                    results_summary["analyses"]["frontend_security"] = {"status": "skipped", "reason": "Frontend Security Analyzer not available"}
                    logger.warning(f"Skipping frontend security for {model}/app{app_num}: Analyzer not found.")

            # Performance Analysis
            if "performance" in analyses_to_run:
                logger.info(f"Starting performance analysis for {model}/app{app_num}")
                if hasattr(current_app, 'performance_tester') and current_app.performance_tester:
                    try:
                        idx = get_model_index(model)
                        if idx is not None:
                            ports = PortManager.get_app_ports(idx, app_num)
                            frontend_port = ports.get("frontend")
                            if frontend_port:
                                test_params = {
                                    "num_users": 5, "duration": 15, "spawn_rate": 1,
                                    "endpoints": [{"path": "/", "method": "GET", "weight": 1}]
                                }
                                current_app.performance_tester.run_test_library(
                                    test_name=f"batch_{model}_app{app_num}", host=f"http://localhost:{frontend_port}",
                                    endpoints=test_params["endpoints"], user_count=test_params["num_users"],
                                    spawn_rate=test_params["spawn_rate"], run_time=test_params["duration"],
                                    model=model, app_num=app_num, force_rerun=True
                                )
                                results_summary["analyses"]["performance"] = {"status": "completed"}
                            else:
                                results_summary["analyses"]["performance"] = {"status": "skipped", "reason": "Frontend port not found for performance test"}
                                logger.warning(f"Skipping performance test for {model}/app{app_num}: Frontend port not found.")
                        else:
                            results_summary["analyses"]["performance"] = {"status": "skipped", "reason": "Model index not found for performance test"}
                            logger.warning(f"Skipping performance test for {model}/app{app_num}: Model index not found.")
                    except Exception as e:
                        logger.error(f"Performance analysis failed for {model}/app{app_num}: {e}", exc_info=True)
                        results_summary["analyses"]["performance"] = {"status": "failed", "error": str(e)}
                        overall_success = False
                else:
                    results_summary["analyses"]["performance"] = {"status": "skipped", "reason": "Performance Tester not available"}
                    logger.warning(f"Skipping performance test for {model}/app{app_num}: Tester not found.")

            # ZAP Scan
            if "zap" in analyses_to_run:
                logger.info(f"Starting ZAP scan for {model}/app{app_num}")
                zap_scanner_instance = getattr(current_app, 'zap_scanner', None)
                if zap_scanner_instance:
                    try:
                        scan_manager = get_scan_manager() # Ensure scan manager is available
                        # ZAP's start_scan is blocking or handles its own threading for the actual scan.
                        # The route version starts a thread for the *route handler*, not ZAP itself.
                        # Here, we call it directly.
                        logger.info(f"Batch: Calling ZAP start_scan for {model}/app{app_num}")
                        success = zap_scanner_instance.start_scan(model, app_num, quick_scan=True) # quick_scan for batch
                        # Fetch the latest scan ID for this app to include in summary
                        latest_scan_info = scan_manager.get_latest_scan_for_app(model, app_num)
                        scan_id_for_summary = latest_scan_info[0] if latest_scan_info else None

                        results_summary["analyses"]["zap"] = {"status": "completed" if success else "failed", "scan_id": scan_id_for_summary}
                        if not success: overall_success = False
                        logger.info(f"Batch: ZAP start_scan for {model}/app{app_num} returned {success}")
                    except Exception as e:
                        logger.error(f"ZAP scan failed for {model}/app{app_num}: {e}", exc_info=True)
                        results_summary["analyses"]["zap"] = {"status": "failed", "error": str(e)}
                        overall_success = False
                else:
                    results_summary["analyses"]["zap"] = {"status": "skipped", "reason": "ZAP Scanner not available"}
                    logger.warning(f"Skipping ZAP scan for {model}/app{app_num}: Scanner not found.")


            # GPT4All Requirements Check
            if "gpt4all" in analyses_to_run:
                logger.info(f"Starting GPT4All requirements check for {model}/app{app_num}")
                if hasattr(current_app, 'gpt4all_analyzer') and current_app.gpt4all_analyzer:
                    try:
                        current_app.gpt4all_analyzer.check_requirements(model, app_num, force_rerun=True)
                        results_summary["analyses"]["gpt4all"] = {"status": "completed"}
                    except Exception as e:
                        logger.error(f"GPT4All analysis failed for {model}/app{app_num}: {e}", exc_info=True)
                        results_summary["analyses"]["gpt4all"] = {"status": "failed", "error": str(e)}
                        overall_success = False
                else:
                    results_summary["analyses"]["gpt4all"] = {"status": "skipped", "reason": "GPT4All Analyzer not available"}
                    logger.warning(f"Skipping GPT4All analysis for {model}/app{app_num}: Analyzer not found.")


            results_summary["status"] = "completed" if overall_success else "completed_with_errors"
            logger.info(f"Analyses for {model}/app{app_num} in batch {batch_id} finished with status: {results_summary['status']}")

        except Exception as e:
            logger.exception(f"Critical error during batch analysis for {model}/app{app_num} in batch {batch_id}: {e}")
            results_summary["status"] = "error"
            results_summary["overall_error"] = str(e)
        finally:
            app_key = f"{model}-{app_num}-{batch_id}" # Make app_key unique per batch instance for active_processes
            # Save the summary of this app's batch run
            try:
                batch_summary_dir = Path(current_app.config["BASE_DIR"]) / "results" / "_batch_runs" / batch_id
                batch_summary_dir.mkdir(parents=True, exist_ok=True)
                # Filename includes model and app_num to avoid clashes if multiple apps are in one batch_id dir
                summary_file_name = f"summary_app_{model}_app{app_num}.json"
                summary_path = batch_summary_dir / summary_file_name
                with open(summary_path, "w") as f:
                    json.dump(results_summary, f, indent=2)
                logger.info(f"Saved batch app summary to {summary_path}")
            except Exception as e_save:
                logger.error(f"Failed to save batch app summary for {model}/app{app_num} of batch {batch_id}: {e_save}", exc_info=True)

            # Update global status for this specific app within the batch
            with batch_processes_lock:
                if app_key in active_batch_processes:
                     active_batch_processes[app_key]["status"] = results_summary["status"]
                     active_batch_processes[app_key]["end_time"] = datetime.now().isoformat()
                     if "overall_error" in results_summary:
                         active_batch_processes[app_key]["error"] = results_summary["overall_error"]
                     active_batch_processes[app_key]["summary_file"] = str(summary_path) # Store path to summary
                else:
                    logger.warning(f"App key {app_key} not found in active_batch_processes at thread completion.")
            logger.info(f"Thread {threading.get_ident()}: Finished analyses for {model}/app{app_num} in batch {batch_id}")


@batch_analysis_bp.route("/run", methods=["POST"])
def run_batch_analysis():
    """
    Endpoint to trigger batch analysis for a model or specific app.
    """
    data = request.json
    if not data or "model" not in data:
        return APIResponse(success=False, error="Missing 'model' in request", code=400).to_response()

    model_name = data["model"]
    target_app_num_str = data.get("app_num")
    analyses_to_run = data.get("analyses", ["backend_security", "frontend_security", "performance", "zap", "gpt4all"])
    force_all_rerun = data.get("force_rerun", True) # Default to True for batch runs

    apps_to_process_specs = []
    if target_app_num_str:
        try:
            target_app_num = int(target_app_num_str)
            if target_app_num <=0: raise ValueError("App number must be positive.")
            # Basic validation: check if model exists
            if not any(m.name == model_name for m in current_app.utils.AI_MODELS): # Assuming utils is on current_app
                 return APIResponse(success=False, error=f"Model '{model_name}' not found.", code=404).to_response()
            apps_to_process_specs.append({"model": model_name, "app_num": target_app_num})
        except ValueError:
            return APIResponse(success=False, error="Invalid 'app_num'", code=400).to_response()
    else:
        model_apps = get_apps_for_model(model_name)
        if not model_apps:
            return APIResponse(success=False, error=f"No apps found for model {model_name}", code=404).to_response()
        for app_info in model_apps:
            apps_to_process_specs.append({"model": app_info["model"], "app_num": app_info["app_num"]})

    batch_id_suffix = f"_app{target_app_num_str}" if target_app_num_str else "_all_apps"
    batch_id = f"batch_{model_name.lower()}{batch_id_suffix}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    with batch_processes_lock:
        # Check if any of the specific apps in this new batch request are already part of an "in_progress" batch
        for app_spec in apps_to_process_specs:
            # An app is identified by its model-app_num AND the batch_id it belongs to.
            # A simpler check: is there *any* active batch for this model-app_num? This might be too restrictive.
            # For now, let's allow multiple batch_ids to reference the same app, but a single app_key (model-app_num-batch_id)
            # should only be "in_progress" once. The current design of active_batch_processes uses model-app_num-batch_id as key.
            app_key_for_this_batch = f'{app_spec["model"]}-{app_spec["app_num"]}-{batch_id}'
            if app_key_for_this_batch in active_batch_processes and active_batch_processes[app_key_for_this_batch]["status"] == "in_progress":
                 return APIResponse(success=False, error=f"Batch process for {app_spec['model']}/app{app_spec['app_num']} with ID {batch_id} seems to be already running or in a conflicting state.", code=409).to_response()


        for app_spec in apps_to_process_specs:
            app_key_for_this_batch = f'{app_spec["model"]}-{app_spec["app_num"]}-{batch_id}' # Unique key for this app in this batch
            active_batch_processes[app_key_for_this_batch] = {
                "batch_id": batch_id, # Grouping ID for the overall request
                "model": app_spec["model"],
                "app_num": app_spec["app_num"],
                "status": "starting",
                "start_time": datetime.now().isoformat(),
                "analyses_requested": analyses_to_run
            }
            # Get the current Flask app instance to pass to the thread
            thread_app_context = current_app._get_current_object()
            thread = threading.Thread(
                target=run_single_app_analyses,
                args=(thread_app_context, app_spec["model"], app_spec["app_num"], analyses_to_run, batch_id),
                daemon=True
            )
            thread.name = f"batch-worker-{app_spec['model']}-{app_spec['app_num']}-{batch_id[:8]}"
            thread.start()
            logger.info(f"Started thread {thread.name} for {app_spec['model']}/app{app_spec['app_num']} in batch {batch_id}")


    return APIResponse(success=True, message=f"Batch analysis initiated for {len(apps_to_process_specs)} app(s). Batch ID: {batch_id}", data={"batch_id": batch_id}).to_response()


@batch_analysis_bp.route("/status", methods=["GET"])
def batch_status():
    batch_id_filter = request.args.get("batch_id")
    model_filter = request.args.get("model")
    app_num_filter = request.args.get("app_num")

    processes_to_display = {}
    with batch_processes_lock:
        for key, process_info in active_batch_processes.items():
            # Key is "model-app_num-batch_id"
            # process_info already contains "batch_id", "model", "app_num"
            match = True
            if batch_id_filter and process_info.get("batch_id") != batch_id_filter:
                match = False
            if model_filter and process_info.get("model") != model_filter:
                match = False
            if app_num_filter and str(process_info.get("app_num")) != str(app_num_filter):
                match = False
            
            if match:
                # Use the unique app_key (model-app_num-batch_id) as the key for the display
                processes_to_display[key] = process_info
        
    # If a batch_id is provided and no active processes match, try to load from saved summaries.
    # This covers cases where all apps in a batch have completed and might have been cleaned from active_batch_processes.
    if batch_id_filter and not processes_to_display:
        logger.debug(f"No active processes for batch ID {batch_id_filter}, attempting to load from file summaries.")
        batch_summary_dir = Path(current_app.config["BASE_DIR"]) / "results" / "_batch_runs" / batch_id_filter
        if batch_summary_dir.is_dir():
            for summary_file in batch_summary_dir.glob("summary_app_*.json"):
                try:
                    with open(summary_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    # Ensure data matches filter criteria if model/app_num were also provided
                    file_model_match = True if not model_filter else (data.get("model") == model_filter)
                    file_app_num_match = True if not app_num_filter else (str(data.get("app_num")) == str(app_num_filter))

                    if file_model_match and file_app_num_match:
                        app_key_from_file = f'{data["model"]}-{data["app_num"]}-{batch_id_filter}' # Reconstruct the key
                        processes_to_display[app_key_from_file] = {
                            "batch_id": batch_id_filter,
                            "model": data.get("model"),
                            "app_num": data.get("app_num"),
                            "status": data.get("status", "completed_from_file"),
                            "start_time": data.get("timestamp"), # timestamp of the summary file
                            "end_time": data.get("timestamp"), # Best guess from file
                            "analyses_requested": list(data.get("analyses", {}).keys()),
                            "summary_file": str(summary_file),
                            "details_from_file": True
                        }
                except Exception as e:
                    logger.error(f"Failed to load or parse batch summary file {summary_file}: {e}", exc_info=True)
    
    if not processes_to_display and batch_id_filter: # If still no processes after trying files
        return APIResponse(success=False, error=f"No active or completed processes found for Batch ID: {batch_id_filter}", code=404).to_response()

    return APIResponse(success=True, data=processes_to_display).to_response()


@batch_analysis_bp.route("/dashboard", methods=["GET"])
def batch_dashboard():
    batch_runs_dir = Path(current_app.config.get("BASE_DIR", ".")) / "results" / "_batch_runs"
    all_batch_runs_summary = []

    if batch_runs_dir.exists():
        for batch_id_dir in batch_runs_dir.iterdir():
            if batch_id_dir.is_dir():
                batch_run_data = {
                    "batch_id": batch_id_dir.name,
                    "apps_processed": 0,
                    "apps_completed_ok": 0,
                    "apps_with_errors": 0,
                    "apps_failed_analysis":0,
                    "start_time": None,
                    "end_time": None,
                    "status": "Unknown"
                }
                earliest_start = None
                latest_end = None
                contains_in_progress = False
                
                # Check active processes first for this batch_id
                active_apps_in_this_batch = {}
                with batch_processes_lock:
                    for key,p_info in active_batch_processes.items():
                        if p_info.get("batch_id") == batch_id_dir.name:
                            active_apps_in_this_batch[f"{p_info['model']}-{p_info['app_num']}"] = p_info


                app_statuses_in_batch = []

                # Iterate over summary files for this batch
                for summary_file in batch_id_dir.glob("summary_app_*.json"):
                    try:
                        with open(summary_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        app_key_simple = f"{data['model']}-{data['app_num']}"
                        
                        # Prioritize active_process_info if available
                        process_info = active_apps_in_this_batch.get(app_key_simple)
                        if process_info:
                            status = process_info["status"]
                            s_time = process_info.get("start_time")
                            e_time = process_info.get("end_time")
                            if status == "in_progress" or status == "starting":
                                contains_in_progress = True
                        else: # App not in active_processes, must be completed (or error state from file)
                            status = data.get("status", "completed_from_file")
                            s_time = data.get("timestamp") # app summary timestamp
                            e_time = data.get("timestamp") # app summary timestamp

                        app_statuses_in_batch.append(status)
                        
                        if s_time:
                            dt_s_time = datetime.fromisoformat(s_time)
                            if earliest_start is None or dt_s_time < earliest_start:
                                earliest_start = dt_s_time
                        if e_time:
                            dt_e_time = datetime.fromisoformat(e_time)
                            if latest_end is None or dt_e_time > latest_end:
                                latest_end = dt_e_time
                    except Exception as e:
                        logger.error(f"Could not parse summary file {summary_file} for batch dashboard: {e}", exc_info=True)
                
                batch_run_data["apps_processed"] = len(app_statuses_in_batch)
                if app_statuses_in_batch: # only calculate if there were apps
                    batch_run_data["apps_completed_ok"] = app_statuses_in_batch.count("completed")
                    batch_run_data["apps_with_errors"] = app_statuses_in_batch.count("completed_with_errors")
                    batch_run_data["apps_failed_analysis"] = app_statuses_in_batch.count("error") # Overall app analysis error

                    if contains_in_progress or any(s in ["starting", "in_progress"] for s in app_statuses_in_batch):
                        batch_run_data["status"] = "In Progress"
                    elif batch_run_data["apps_with_errors"] > 0 or batch_run_data["apps_failed_analysis"] > 0:
                        batch_run_data["status"] = "Completed with Errors"
                    elif batch_run_data["apps_processed"] == batch_run_data["apps_completed_ok"] and batch_run_data["apps_processed"] > 0:
                         batch_run_data["status"] = "Completed Successfully"
                    elif batch_run_data["apps_processed"] == 0 and not active_apps_in_this_batch: # No summaries and no active
                        batch_run_data["status"] = "No App Data"


                batch_run_data["start_time"] = earliest_start.isoformat() if earliest_start else None
                batch_run_data["end_time"] = latest_end.isoformat() if latest_end and not contains_in_progress else None

                if batch_run_data["apps_processed"] > 0 or active_apps_in_this_batch: # Add if there's any info
                    all_batch_runs_summary.append(batch_run_data)

    all_batch_runs_summary.sort(key=lambda x: x.get("start_time") or x["batch_id"], reverse=True)
    
    # Clean up old entries from active_batch_processes that are terminal and older than, say, 1 hour
    # This prevents memory leak if an app finishes but its summary file isn't immediately checked by dashboard
    # For simplicity, this is not implemented here but would be good for a production system.

    return render_template("batch_dashboard.html", batch_runs=all_batch_runs_summary)


@batch_analysis_bp.route("/results/<batch_id>", methods=["GET"])
def view_batch_results(batch_id: str):
    batch_summary_dir = Path(current_app.config.get("BASE_DIR", ".")) / "results" / "_batch_runs" / batch_id
    app_results_display = []

    if not batch_summary_dir.is_dir():
        flash(f"No results found for Batch ID: {batch_id}", "error")
        return redirect(url_for(".batch_dashboard"))

    for summary_file in batch_summary_dir.glob("summary_app_*.json"):
        try:
            with open(summary_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                app_results_display.append(data)
        except Exception as e:
            logger.error(f"Error loading summary file {summary_file} for batch {batch_id} view: {e}", exc_info=True)
            app_results_display.append({
                "model": "Error", "app_num": "N/A", "batch_id": batch_id,
                "status": "error_loading_summary", "overall_error": f"Could not load: {summary_file.name}",
                "analyses": {}, "timestamp": datetime.now().isoformat()
            })

    # Augment with active data if any app is still running for this batch_id
    with batch_processes_lock:
        for key, p_info in active_batch_processes.items():
            if p_info.get("batch_id") == batch_id:
                # Check if this app is already loaded from file; if so, update its status if active
                found = False
                for res in app_results_display:
                    if res.get("model") == p_info.get("model") and res.get("app_num") == p_info.get("app_num"):
                        if p_info.get("status") in ["starting", "in_progress"]: # Only overwrite if still active
                            res["status"] = p_info.get("status")
                            res["start_time"] = p_info.get("start_time") # Use active start time
                            res["timestamp"] = p_info.get("start_time") # Match for display consistency
                        found = True
                        break
                if not found and p_info.get("status") in ["starting", "in_progress"]: # App is active but no summary file yet
                     app_results_display.append({
                        "model": p_info.get("model"),
                        "app_num": p_info.get("app_num"),
                        "batch_id": batch_id,
                        "status": p_info.get("status"),
                        "analyses": {analysis: {"status":"pending"} for analysis in p_info.get("analyses_requested",[]) },
                        "timestamp": p_info.get("start_time")
                     })


    app_results_display.sort(key=lambda x: (x.get("model", ""), x.get("app_num", 0)))
    return render_template("batch_results_view.html", batch_id=batch_id, app_results=app_results_display)


def init_batch_analysis(app):
    """Initialize batch analysis module components if necessary."""
    logger.info("Initializing batch analysis module for the app.")
    # Example: if JsonResultsManager needs app config. Here it's called with app context already.
    # Ensure `current_app.utils.AI_MODELS` and `current_app.utils.PortManager` are set up if used.
    # This function is called from create_app in app.py.
    # We can also pre-initialize the _batch_results_manager here.
    global _batch_results_manager
    if _batch_results_manager is None:
        base_dir = Path(app.config["BASE_DIR"])
        _batch_results_manager = JsonResultsManager(base_path=base_dir, module_name="batch_summary_module")
        logger.info("Batch results manager initialized via init_batch_analysis.")