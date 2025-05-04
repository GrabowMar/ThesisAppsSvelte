"""
Backend Security Analysis Module

Provides comprehensive security scanning for backend code using multiple tools:
- bandit for Python security vulnerability checks
- safety for dependency vulnerability detection
- pylint for code quality analysis and potential security issues
- vulture for dead code detection to reduce attack surface

This module orchestrates the execution of these tools, normalizes their outputs
into a consistent format, and provides aggregated results and summaries.

FIX: Modified tool execution to use `sys.executable -m tool` for reliability.
"""

import json
import logging
import os
import re
import subprocess
import sys # <-- Added import
import threading # <-- Added import for thread safety
import concurrent.futures
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, Callable

# Configure logging for this module
logger = logging.getLogger(__name__)
# Consider setting level via application config rather than hardcoding
# logger.setLevel(logging.DEBUG)

# Constants
TOOL_TIMEOUT = 30  # seconds for subprocess execution
SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
CONFIDENCE_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
DEFAULT_SEVERITY_LEVEL = 3 # Used for sorting unknown severity/confidence


# cmd_name function is no longer needed if running as modules
# def cmd_name(name: str) -> str: ...


@dataclass
class BackendSecurityIssue:
    """
    Represents a security issue found in backend code by an analysis tool.

    Attributes:
        filename: Relative path to the file containing the issue.
        line_number: Line number where the issue was found.
        issue_text: Description of the security issue.
        severity: Severity level (HIGH, MEDIUM, LOW).
        confidence: Confidence level (HIGH, MEDIUM, LOW).
        issue_type: Tool-specific type/ID of the issue.
        line_range: Range of lines affected by the issue.
        code: Code snippet containing the issue, if available.
        tool: Name of the tool that found the issue.
        fix_suggestion: Optional suggestion on how to fix the issue.
    """
    filename: str
    line_number: int
    issue_text: str
    severity: str  # HIGH, MEDIUM, LOW
    confidence: str  # HIGH, MEDIUM, LOW
    issue_type: str
    line_range: List[int]
    code: str
    tool: str
    fix_suggestion: Optional[str] = None


class BackendSecurityAnalyzer:
    """
    Analyzes backend Python code for security issues using multiple tools.

    Orchestrates Bandit, Safety, Pylint, and Vulture execution,
    normalizes results into BackendSecurityIssue objects, and provides summaries.
    """

    def __init__(self, base_path: Path):
        """
        Initialize the security analyzer.

        Args:
            base_path: Base directory containing the code projects (e.g., 'models/').
                       Assumes structure like base_path/model_name/appN/backend/.
        """
        if not base_path.is_dir():
            logger.warning(f"Base path '{base_path}' does not exist or is not a directory.")
        self.base_path = base_path
        self.default_tools = ["bandit"]  # Tools run in quick scan mode
        self.all_tools = ["bandit", "safety", "pylint", "vulture"]

        # Map tool names to their runner and parser methods
        self.tool_runners = {
            "bandit": self._run_bandit,
            "safety": self._run_safety,
            "pylint": self._run_pylint,
            "vulture": self._run_vulture
        }

    def _check_source_files(self, directory: Path) -> Tuple[bool, List[str]]:
        """
        Check if the directory contains any Python source files recursively.

        Args:
            directory: Directory to check.

        Returns:
            Tuple: (bool indicating if .py files were found, list of found .py file paths).
        """
        if not directory.is_dir():
            logger.warning(f"Target directory '{directory}' does not exist.")
            return False, []

        source_files = list(directory.rglob('*.py'))
        return bool(source_files), [str(f) for f in source_files]


    def _run_tool(
        self,
        tool_name: str,
        command: List[str],
        parser: Callable[[str], List[BackendSecurityIssue]],
        working_directory: Optional[Path] = None, # Allow specifying cwd if needed
        input_data: Optional[str] = None # Added for stdin input (e.g., safety)
    ) -> Tuple[List[BackendSecurityIssue], str]:
        """
        Generic method to run an external security tool (potentially as a Python module)
        and parse its output.

        Args:
            tool_name: Name of the tool (for logging).
            command: Command line arguments list for the tool.
            parser: Function to parse the tool's stdout into BackendSecurityIssue objects.
            working_directory: Directory from which to run the command.
            input_data: Optional string data to pass to the process's stdin.

        Returns:
            Tuple: (List of found BackendSecurityIssue objects, Raw stdout/stderr from the tool).
        """
        issues = []
        raw_output = f"{tool_name} execution failed." # Default error message
        try:
            # Determine if running as a module for logging
            is_module_execution = command[0] == sys.executable and command[1] == "-m"
            run_description = f"module {command[2]}" if is_module_execution else f"command {' '.join(command)}"
            logger.info(f"[{tool_name}] Attempting to run: {run_description} in '{working_directory or self.base_path}'") # Enhanced log

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=TOOL_TIMEOUT,
                check=False, # Don't raise exception on non-zero exit code
                cwd=working_directory or self.base_path, # Default to base_path if not specified
                input=input_data # Pass stdin data if provided
            )

            logger.info(f"[{tool_name}] Subprocess finished with return code: {result.returncode}") # Enhanced log
            raw_output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

            if result.returncode != 0 and not result.stdout: # Log warning only if non-zero exit AND no output
                logger.warning(f"{tool_name} exited with code {result.returncode}. Stderr: {result.stderr}")
                # Some tools might output results even with non-zero exit codes (e.g., Pylint)

            if result.stdout:
                try:
                    issues = parser(result.stdout)
                    logger.info(f"{tool_name} found {len(issues)} issues.")
                except Exception as e:
                    logger.error(f"Failed to parse {tool_name} output: {e}\nOutput:\n{result.stdout[:500]}...") # Log partial output
                    raw_output += f"\nPARSING_ERROR: {str(e)}"
            else:
                logger.info(f"{tool_name} produced no standard output.")


        except subprocess.TimeoutExpired:
            logger.error(f"{tool_name} timed out after {TOOL_TIMEOUT} seconds.")
            raw_output = f"{tool_name} timed out after {TOOL_TIMEOUT} seconds."
        except FileNotFoundError:
            # This error is less likely when using sys.executable, but handle it.
            cmd_executed = command[0]
            logger.error(f"{tool_name} command/interpreter not found. Is Python installed and in PATH? Command: {cmd_executed}")
            raw_output = f"{tool_name} command/interpreter not found: {cmd_executed}"
        except Exception as e:
            logger.exception(f"An unexpected error occurred while running {tool_name}: {e}")
            raw_output = f"Unexpected error running {tool_name}: {str(e)}"

        return issues, raw_output

    def _make_relative_path(self, file_path: str, base_dir: Path) -> str:
        """Helper to create a relative path string from an absolute path."""
        try:
            # Ensure both paths are absolute for correct relativity
            abs_file_path = Path(file_path).resolve()
            abs_base_dir = base_dir.resolve()
            relative = abs_file_path.relative_to(abs_base_dir)
            return str(relative)
        except ValueError:
            # If file_path is not within base_dir, return the original path
            logger.warning(f"Could not make path relative: '{file_path}' is not inside '{base_dir}'.")
            # Attempt stripping known base path string as fallback for tools outputting weird paths
            base_str = str(base_dir)
            if file_path.startswith(base_str):
                return file_path[len(base_str):].lstrip('/\\')
            return file_path # Fallback to original/absolute


    def _parse_bandit_output(self, output: str) -> List[BackendSecurityIssue]:
        """Parse Bandit JSON output into BackendSecurityIssue objects."""
        issues = []
        try:
            analysis = json.loads(output)
            if "errors" in analysis and analysis["errors"]:
                logger.warning(f"Bandit reported errors: {analysis['errors']}")

            for issue_data in analysis.get("results", []):
                try:
                    # Bandit paths are usually relative to execution dir already, but ensure consistency
                    relative_filename = self._make_relative_path(issue_data["filename"], self.base_path)
                    issues.append(BackendSecurityIssue(
                        filename=relative_filename,
                        line_number=issue_data["line_number"],
                        issue_text=issue_data["issue_text"],
                        severity=issue_data["issue_severity"].upper(),
                        confidence=issue_data["issue_confidence"].upper(),
                        issue_type=issue_data["test_name"],
                        line_range=issue_data["line_range"],
                        code=issue_data.get("code", "N/A"),
                        tool="Bandit",
                        fix_suggestion=issue_data.get("more_info", None)
                    ))
                except KeyError as ke:
                    logger.warning(f"Missing expected key in Bandit issue data: {ke}")
                except Exception as e:
                    logger.warning(f"Error processing Bandit issue: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Bandit JSON: {e}")
            # Optionally return partial data or raise error

        return issues

    def _run_bandit(self, app_path: Path) -> Tuple[List[BackendSecurityIssue], str]:
        """Run Bandit security analysis as a module."""
        # Use sys.executable to call the bandit module
        command = [sys.executable, "-m", "bandit", "-r", ".", "-f", "json", "-ll", "-ii"]
        return self._run_tool("Bandit", command, self._parse_bandit_output, working_directory=app_path)

    def _parse_safety_output(self, output: str) -> List[BackendSecurityIssue]:
        """Parse Safety CLI output into BackendSecurityIssue objects."""
        issues = []
        # Safety's output is primarily textual reports
        # This parser focuses on detecting if *any* vulnerabilities were found,
        # assuming detailed info is in the raw output.
        # A more robust parser would use safety's JSON output if available (--json).

        # Look for lines indicating found vulnerabilities
        # Example: "Flask    1.1.2    <2.0.1    High Severity    ID: 39606"
        vuln_pattern = re.compile(r"([\w-]+)\s+([\d.]+)\s+([<>=]+[\d.]+)\s+(High|Medium|Low) Severity\s+ID: (\d+)")
        for line in output.splitlines():
            match = vuln_pattern.search(line)
            if match:
                package, installed_version, affected_versions, severity, vuln_id = match.groups()
                issues.append(BackendSecurityIssue(
                    filename="requirements.txt / dependencies", # Indicate source
                    line_number=0, # Line number not applicable
                    issue_text=f"Vulnerable dependency: {package} ({installed_version}). Affected: {affected_versions}. Safety ID: {vuln_id}",
                    severity=severity.upper(),
                    confidence="HIGH", # If Safety reports it, confidence is high
                    issue_type=f"safety_{vuln_id}",
                    line_range=[0],
                    code=f"{package}=={installed_version}",
                    tool="Safety",
                    fix_suggestion=f"Update {package} to a version not matching {affected_versions}."
                ))

        # Check for warnings about unpinned dependencies (less precise)
        unpinned_match = re.search(r"Warning: unpinned requirement '([\w-]+)'", output)
        if unpinned_match:
            package_name = unpinned_match.group(1)
            # Check if we already reported a specific vulnerability for this package
            if not any(issue.code.startswith(f"{package_name}==") for issue in issues):
                issues.append(BackendSecurityIssue(
                    filename="requirements.txt",
                    line_number=0,
                    issue_text=f"Unpinned dependency: {package_name}. May introduce vulnerabilities.",
                    severity="MEDIUM",
                    confidence="MEDIUM",
                    issue_type="unpinned_dependency",
                    line_range=[0],
                    code=package_name,
                    tool="Safety",
                    fix_suggestion=f"Pin '{package_name}' to a specific, secure version (e.g., {package_name}==x.y.z)."
                ))

        return issues

    def _run_safety(self, app_path: Path) -> Tuple[List[BackendSecurityIssue], str]:
        """Run Safety check on dependencies as a module."""
        requirements_file = app_path / "requirements.txt"
        if not requirements_file.exists():
            return [], "No requirements.txt found"

        # Use sys.executable to call the safety module and pass requirements via stdin
        command = [sys.executable, "-m", "safety", "check", "--stdin"]
        req_content = None
        try:
            with open(requirements_file, 'r') as f:
                req_content = f.read()
        except Exception as e:
            logger.error(f"Failed to read requirements file {requirements_file}: {e}")
            return [], f"Error reading requirements file: {e}"

        return self._run_tool("Safety", command, self._parse_safety_output, working_directory=app_path, input_data=req_content)


    def _parse_pylint_output(self, output: str) -> List[BackendSecurityIssue]:
        """Parse Pylint JSON output into BackendSecurityIssue objects."""
        issues = []
        try:
            # Pylint might output non-JSON text before the JSON array on errors/warnings
            # Try to find the start of the JSON array '['
            json_start_index = output.find('[')
            if json_start_index == -1:
                logger.warning(f"Could not find start of JSON array in Pylint output. Output:\n{output}")
                return [] # No JSON found

            json_output = output[json_start_index:]
            
            # Verify we have valid JSON before trying to parse
            if not json_output.strip().startswith('['):
                logger.warning(f"Expected JSON array to start with '[', but got: {json_output[:20]}...")
                return []
                
            pylint_data = json.loads(json_output)
            # Pylint severity: (C)onvention, (R)efactor, (W)arning, (E)rror, (F)atal
            severity_map = {"F": "HIGH", "E": "HIGH", "W": "MEDIUM", "R": "LOW", "C": "LOW"}

            for issue_data in pylint_data:
                # Use try/except to catch any missing keys or data processing errors
                try:
                    relative_filename = self._make_relative_path(issue_data["path"], self.base_path)
                    issues.append(BackendSecurityIssue(
                        filename=relative_filename,
                        line_number=issue_data["line"],
                        issue_text=f"[{issue_data['symbol']} ({issue_data['message-id']})] {issue_data['message']}",
                        severity=severity_map.get(issue_data["type"], "LOW"),
                        confidence="MEDIUM", # Pylint issues are generally medium confidence for security relevance
                        issue_type=f"pylint_{issue_data['symbol']}",
                        line_range=[issue_data["line"]],
                        code="N/A", # Pylint JSON format doesn't typically include code snippet
                        tool="Pylint",
                        fix_suggestion=None # Pylint doesn't provide structured suggestions
                    ))
                except KeyError as ke:
                    logger.warning(f"Missing expected key in Pylint issue data: {ke}")
                except Exception as e:
                    logger.warning(f"Error processing Pylint issue: {e}")
                    
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Pylint JSON: {e}. Output sample:\n{output[:500]}...")
        except Exception as e:
            logger.error(f"Unexpected error parsing Pylint output: {e}")
        return issues

    def _run_pylint(self, app_path: Path) -> Tuple[List[BackendSecurityIssue], str]:
        """Run Pylint for code quality analysis as a module."""
        _, source_files = self._check_source_files(app_path)
        if not source_files:
            return [], "No Python source files found for Pylint."

        # Convert source file paths to be relative to the app_path for the command
        # Use safer approach that won't raise ValueError for non-relative paths
        relative_source_files = []
        for f in source_files:
            try:
                # Try to make path relative if it's within app_path
                rel_path = str(Path(f).relative_to(app_path))
                relative_source_files.append(rel_path)
            except ValueError:
                # If file isn't within app_path, use the original path
                # This could happen with certain tool output formats
                logger.warning(f"Path '{f}' cannot be made relative to '{app_path}', using as is.")
                relative_source_files.append(f)

        # Use sys.executable to call the pylint module
        # Use --exit-zero to prevent non-zero exit code just for finding issues
        command = [sys.executable, "-m", "pylint", "--output-format=json", "--exit-zero"] + relative_source_files
        return self._run_tool("Pylint", command, self._parse_pylint_output, working_directory=app_path)


    def _parse_vulture_output(self, output: str) -> List[BackendSecurityIssue]:
        """Parse Vulture text output into BackendSecurityIssue objects."""
        issues = []
        # Example: "path/to/file.py:123: unused function 'foobar' (60% confidence)"
        line_pattern = re.compile(r"^(.*?):(\d+):\s*(.*?) \((\d+)% confidence\)")

        for line in output.splitlines():
            if not line.strip():
                continue
            match = line_pattern.match(line)
            if match:
                try:
                    file_path, line_num_str, desc, conf_str = match.groups()
                    line_num = int(line_num_str)
                    confidence_val = int(conf_str)

                    if confidence_val >= 80:
                        confidence = "HIGH"
                    elif confidence_val >= 50:
                        confidence = "MEDIUM"
                    else:
                        confidence = "LOW"

                    relative_filename = self._make_relative_path(file_path, self.base_path)
                    issues.append(BackendSecurityIssue(
                        filename=relative_filename,
                        line_number=line_num,
                        issue_text=f"Dead Code: {desc.strip()}",
                        severity="LOW", # Dead code is generally low severity impact
                        confidence=confidence,
                        issue_type="dead_code",
                        line_range=[line_num],
                        code="N/A", # Vulture doesn't provide code snippet easily
                        tool="Vulture",
                        fix_suggestion="Verify if code is unused and remove it to reduce clutter and potential attack surface."
                    ))
                except Exception as e:
                    logger.warning(f"Error processing Vulture line '{line}': {e}")
            else:
                logger.debug(f"Could not parse Vulture line: {line}")

        return issues

    def _run_vulture(self, app_path: Path) -> Tuple[List[BackendSecurityIssue], str]:
        """Run Vulture to detect dead code as a module."""
        # Use sys.executable to call the vulture module
        # Vulture scans the directory passed as argument
        command = [sys.executable, "-m", "vulture", ".", "--min-confidence", "50"] # Scan current dir '.'
        return self._run_tool("Vulture", command, self._parse_vulture_output, working_directory=app_path)


    def run_security_analysis(
        self,
        model: str,
        app_num: int,
        use_all_tools: bool = False
    ) -> Tuple[List[BackendSecurityIssue], Dict[str, str], Dict[str, str]]:
        """
        Run backend security analysis on a specific application path.

        Args:
            model: Model identifier (e.g., "ModelA").
            app_num: Application number (e.g., 1).
            use_all_tools: If True, run all configured tools; otherwise, run defaults.

        Returns:
            Tuple containing:
            - List of BackendSecurityIssue objects, sorted by severity/confidence.
            - Dictionary mapping tool names to status messages (e.g., "✅ No issues found", "❌ Error").
            - Dictionary mapping tool names to their raw output strings.

        Raises:
            ValueError: If the target application path does not exist or contains no Python files
                      (unless only Safety is being run).
        """
        # Construct path relative to the base path stored during initialization
        app_path = self.base_path / f"{model}/app{app_num}/backend"
        logger.info(f"Starting backend security analysis for: {app_path}")

        if not app_path.is_dir():
            raise ValueError(f"Application backend path does not exist: {app_path}")

        has_files, _ = self._check_source_files(app_path)
        tools_to_run = self.all_tools if use_all_tools else self.default_tools

        # Check if source files are needed but missing
        requires_py_files = any(tool for tool in tools_to_run if tool != "safety")
        if requires_py_files and not has_files:
            raise ValueError(f"No Python source files found in {app_path}, cannot run tools like Bandit, Pylint, Vulture.")
        elif not has_files:
            logger.warning(f"No Python source files in {app_path}, only running Safety check if selected.")

        # Thread-safe containers for collecting results
        all_issues = []
        tool_status = {}
        tool_outputs = {}
        
        # Locks for thread safety when modifying shared data
        issues_lock = threading.Lock()
        status_lock = threading.Lock()
        outputs_lock = threading.Lock()

        logger.info(f"Running tools: {', '.join(tools_to_run)}")

        # Use ThreadPoolExecutor for I/O bound tasks (running external processes)
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(tools_to_run)) as executor:
            future_to_tool = {}
            for tool in tools_to_run:
                # Pre-populate tool_status with locks to avoid race conditions
                with status_lock:
                    if tool == "safety" and "safety" not in self.tool_runners:
                        logger.warning("Safety tool runner not configured, skipping.")
                        tool_status[tool] = "❓ Not configured?"
                        continue
                    if tool != "safety" and not has_files:
                        logger.warning(f"Skipping tool {tool} as no Python files were found.")
                        tool_status[tool] = "⚪ Skipped (no .py files)"
                        continue
                    if tool in self.tool_runners:
                        future_to_tool[executor.submit(self.tool_runners[tool], app_path)] = tool
                    else:
                        logger.warning(f"Runner for tool '{tool}' not found.")
                        tool_status[tool] = "❓ Not configured?"

            for future in concurrent.futures.as_completed(future_to_tool):
                tool = future_to_tool[future]
                try:
                    issues, output = future.result()
                    
                    # Thread-safe updates to shared data
                    with issues_lock:
                        all_issues.extend(issues)
                    
                    with outputs_lock:
                        tool_outputs[tool] = output
                    
                    # Update tool status with thread safety
                    with status_lock:
                        # Check for explicit failure markers in output or lack of issues despite error indicators
                        is_error = "error" in output.lower() or "failed" in output.lower() or "timed out" in output.lower() or "not found" in output.lower()
                        if is_error and not issues:
                            tool_status[tool] = f"❌ Error reported, check raw output."
                        elif is_error and issues:
                            tool_status[tool] = f"⚠️ Found {len(issues)} issues (errors reported)."
                        elif not issues:
                            tool_status[tool] = "✅ No issues found"
                        else:
                            tool_status[tool] = f"ℹ️ Found {len(issues)} issues"
                except Exception as e:
                    # Capture errors during future processing itself
                    logger.exception(f"Error processing result for tool {tool}: {e}")
                    
                    with status_lock:
                        tool_status[tool] = f"❌ Error processing results: {str(e)}"
                    
                    with outputs_lock:
                        tool_outputs[tool] = f"Error processing results: {str(e)}"

        # Mark tools that were not run (e.g., in quick scan mode)
        with status_lock:
            for tool in self.all_tools:
                if tool not in tool_status:
                    tool_status[tool] = "⚪ Skipped (quick scan)" if not use_all_tools else "❓ Not configured?"

        # Sort issues: Severity (High->Low) -> Confidence (High->Low) -> Filename -> Line number
        sorted_issues = sorted(
            all_issues,
            key=lambda issue: (
                SEVERITY_ORDER.get(issue.severity, DEFAULT_SEVERITY_LEVEL),
                CONFIDENCE_ORDER.get(issue.confidence, DEFAULT_SEVERITY_LEVEL),
                issue.filename,
                issue.line_number
            )
        )
        logger.info(f"Backend analysis complete for {app_path}. Total issues: {len(sorted_issues)}")
        return sorted_issues, tool_status, tool_outputs


    def get_analysis_summary(self, issues: List[BackendSecurityIssue]) -> Dict[str, Any]:
        """
        Generate summary statistics for the analysis results.

        Args:
            issues: List of BackendSecurityIssue objects found.

        Returns:
            Dictionary containing summary statistics (counts by severity,
            confidence, affected files, issue types, tools, timestamp).
        """
        summary = {
            "total_issues": len(issues),
            "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "confidence_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "files_affected": len({issue.filename for issue in issues}),
            "issue_types": {},
            "tool_counts": {},
            "scan_time": datetime.now().isoformat() # Use ISO format for clarity
        }

        for issue in issues:
            summary["severity_counts"][issue.severity] = summary["severity_counts"].get(issue.severity, 0) + 1
            summary["confidence_counts"][issue.confidence] = summary["confidence_counts"].get(issue.confidence, 0) + 1
            summary["issue_types"][issue.issue_type] = summary["issue_types"].get(issue.issue_type, 0) + 1
            summary["tool_counts"][issue.tool] = summary["tool_counts"].get(issue.tool, 0) + 1

        # Ensure all defined severity/confidence levels are present in the summary keys
        for sev in SEVERITY_ORDER:
            if sev not in summary["severity_counts"]: summary["severity_counts"][sev] = 0
        for conf in CONFIDENCE_ORDER:
            if conf not in summary["confidence_counts"]: summary["confidence_counts"][conf] = 0

        return summary