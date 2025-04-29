# The issue is in the serialization of security issues in _analyze_app_task method
# Here's the corrected code for the relevant section:

def _analyze_app_task(
    self, job_id: int, model: str, app_num: int, analysis_type: AnalysisType,
    analysis_options: Dict[str, Any], analyzer_service: Any, port_manager_class: Optional[Type[PortManager]]
) -> None:
    """
    Performs analysis for a single app/type. Runs in Executor thread.
    Handles internal errors, timeouts, and updates storage.
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
                # *** THIS IS THE POTENTIALLY BLOCKING CALL ***
                issues, tool_status, raw_out = analyzer_service.run_security_analysis(model, app_num, use_all_tools=full_scan)
                # *** CALL COMPLETED ***
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
                    host_url = f"http://localhost:{ports['frontend']}"
                    task_logger.debug(f"{log_prefix} Target host URL: {host_url}")
                except Exception as port_err: raise RuntimeError(f"Port determination failed: {port_err}") from port_err
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
                scan_id = analyzer_service.create_scan(model, app_num, type_options)
                if not scan_id: raise RuntimeError("ScanManager failed to return a scan ID.")
                task_logger.info(f"{log_prefix} ZAP scan triggered. Scan ID: {scan_id}")
                analysis_q.put(("triggered", {"zap_scan_id": scan_id})) # Special status

            # --- Unknown Type ---
            else:
                raise ValueError(f"Unsupported analysis type: {analysis_type.value}")

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
                issues_count = len(issues)
                high_sev = summary.get("severity_counts", {}).get("HIGH", 0)
                med_sev = summary.get("severity_counts", {}).get("MEDIUM", 0)
                low_sev = summary.get("severity_counts", {}).get("LOW", 0)
                
                # FIX: Properly serialize issues using correct method for each analyzer type
                serializable_issues = []
                for issue in issues:
                    if hasattr(issue, 'to_dict') and callable(issue.to_dict):
                        # Use to_dict method if available (better than asdict for custom serialization)
                        serializable_issues.append(issue.to_dict())
                    elif hasattr(issue, '__dataclass_fields__'):
                        # Fallback to asdict for standard dataclasses
                        from dataclasses import asdict
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
                        from dataclasses import asdict
                        issues_list.append(asdict(res) if hasattr(res, '__dataclass_fields__') else {"requirement": str(res)})
                
                met_count = sum(1 for r in issues_list if r.get('result', {}).get('met', False))
                summary = {"requirements_checked": len(issues_list), "met_count": met_count}
                task_logger.debug(f"{log_prefix} GPT4All Summary: {summary}")
                result_details.update({"issues": issues_list, "summary": summary})
                issues_count = len(issues_list)
                try: raw_output_preview = json.dumps(issues_list, indent=2)
                except Exception: raw_output_preview = str(issues_list)

        elif q_status == "skipped":
            status = "skipped"
            result_details["error"] = str(q_payload)
            task_logger.info(f"{log_prefix} Task skipped: {q_payload}")
        elif q_status == "triggered":
            status = "triggered"
            result_details.update(q_payload) # e.g., {"zap_scan_id": ...}
            raw_output_preview = f"ZAP scan triggered: {q_payload}. Monitor ZAP status separately."
            task_logger.info(f"{log_prefix} Task triggered async action: {q_payload}")
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
        # Timeout occurred
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