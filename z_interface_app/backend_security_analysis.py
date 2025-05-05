"""
Backend Security Analysis Module

Provides comprehensive security scanning for backend code using multiple tools:
- bandit for Python security vulnerability checks
- safety for dependency vulnerability detection
- pylint for code quality analysis and potential security issues
- vulture for dead code detection to reduce attack surface

This module orchestrates the execution of these tools, normalizes their outputs
into a consistent format, and provides aggregated results and summaries.
"""

import json
import logging
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional, Tuple, Any, Callable, TypedDict, NamedTuple, Set, Union

# Configure logging for this module
logger = logging.getLogger(__name__)

# Constants
TOOL_TIMEOUT = 30  # seconds for subprocess execution


class Severity(str, Enum):
    """Enumeration for issue severity levels."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Confidence(str, Enum):
    """Enumeration for issue confidence levels."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# Ordering for severity and confidence in sorting
SEVERITY_ORDER = {Severity.HIGH: 0, Severity.MEDIUM: 1, Severity.LOW: 2}
CONFIDENCE_ORDER = {Confidence.HIGH: 0, Confidence.MEDIUM: 1, Confidence.LOW: 2}
DEFAULT_SEVERITY_LEVEL = 3  # Used for sorting unknown severity/confidence


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


class ToolResult(NamedTuple):
    """Result from running a security tool."""
    issues: List[BackendSecurityIssue]
    output: str
    status: str = ""


class ToolConfig(TypedDict):
    """Configuration for a security tool."""
    command_args: List[str]
    parser: Callable[[str], List[BackendSecurityIssue]]
    requires_files: bool


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
        
        # Tool sets for different scan modes
        self.default_tools: Set[str] = {"bandit"}  # Tools run in quick scan mode
        self.all_tools: Set[str] = {"bandit", "safety", "pylint", "vulture"}
        
        # Tool configurations
        self.tool_configs: Dict[str, Callable[[Path], ToolResult]] = {
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
        working_directory: Optional[Path] = None,
        input_data: Optional[str] = None
    ) -> ToolResult:
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
            ToolResult containing issues found, raw output, and status message.
        """
        issues: List[BackendSecurityIssue] = []
        raw_output = f"{tool_name} execution failed."  # Default error message
        status = "❌ Error"
        
        try:
            # Determine if running as a module for logging
            is_module_execution = (len(command) > 2 and 
                                  command[0] == sys.executable and 
                                  command[1] == "-m")
            
            run_description = f"module {command[2]}" if is_module_execution else f"command {' '.join(command)}"
            effective_cwd = working_directory or self.base_path
            
            logger.info(f"[{tool_name}] Running: {run_description} in '{effective_cwd}'")

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=TOOL_TIMEOUT,
                check=False,  # Don't raise exception on non-zero exit code
                cwd=effective_cwd,
                input=input_data
            )

            logger.info(f"[{tool_name}] Subprocess finished with return code: {result.returncode}")
            raw_output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

            if result.returncode != 0 and not result.stdout:
                logger.warning(f"{tool_name} exited with code {result.returncode}. Stderr: {result.stderr}")
                status = f"❌ Error (code {result.returncode})"
            elif result.stdout:
                try:
                    issues = parser(result.stdout)
                    if issues:
                        status = f"ℹ️ Found {len(issues)} issues"
                    else:
                        status = "✅ No issues found"
                    logger.info(f"{tool_name} found {len(issues)} issues.")
                except Exception as e:
                    logger.error(f"Failed to parse {tool_name} output: {e}\nOutput:\n{result.stdout[:500]}...")
                    raw_output += f"\nPARSING_ERROR: {str(e)}"
                    status = f"❌ Parser error: {str(e)}"
            else:
                logger.info(f"{tool_name} produced no standard output.")
                status = "⚠️ No output"

        except subprocess.TimeoutExpired:
            logger.error(f"{tool_name} timed out after {TOOL_TIMEOUT} seconds.")
            raw_output = f"{tool_name} timed out after {TOOL_TIMEOUT} seconds."
            status = f"❌ Timeout after {TOOL_TIMEOUT}s"
        except FileNotFoundError:
            cmd_executed = command[0]
            logger.error(f"{tool_name} command/interpreter not found: {cmd_executed}")
            raw_output = f"{tool_name} command/interpreter not found: {cmd_executed}"
            status = "❌ Command not found"
        except Exception as e:
            logger.exception(f"An unexpected error occurred while running {tool_name}: {e}")
            raw_output = f"Unexpected error running {tool_name}: {str(e)}"
            status = f"❌ Error: {str(e)}"

        return ToolResult(issues=issues, output=raw_output, status=status)

    def _make_relative_path(self, file_path: str, base_dir: Path) -> str:
        """
        Helper to create a relative path string from an absolute path.
        
        Args:
            file_path: The file path to make relative
            base_dir: The base directory to make the path relative to
            
        Returns:
            A string with the path relative to base_dir, or the original path if it cannot be made relative
        """
        try:
            # Convert to Path objects for proper path handling
            file_path_obj = Path(file_path)
            
            # Handle both absolute and relative paths
            if file_path_obj.is_absolute():
                abs_file_path = file_path_obj.resolve()
                abs_base_dir = base_dir.resolve()
                
                try:
                    # Try to make the path relative
                    relative = abs_file_path.relative_to(abs_base_dir)
                    return str(relative)
                except ValueError:
                    # If the path is not within the base directory, try stripping prefix
                    base_str = str(abs_base_dir)
                    file_str = str(abs_file_path)
                    if file_str.startswith(base_str):
                        return file_str[len(base_str):].lstrip('/\\')
                    
                    # If that doesn't work, return the original path
                    logger.warning(f"Path '{file_path}' cannot be made relative to '{base_dir}'")
                    return file_path
            else:
                # The path is already relative, return as is
                return file_path
        except Exception as e:
            logger.warning(f"Error processing path '{file_path}': {e}")
            return file_path

    def _parse_bandit_output(self, output: str) -> List[BackendSecurityIssue]:
        """
        Parse Bandit JSON output into BackendSecurityIssue objects.
        
        Args:
            output: JSON output from Bandit tool
            
        Returns:
            List of BackendSecurityIssue objects parsed from the output
        """
        issues: List[BackendSecurityIssue] = []
        
        try:
            analysis = json.loads(output)
            
            if "errors" in analysis and analysis["errors"]:
                logger.warning(f"Bandit reported errors: {analysis['errors']}")

            for issue_data in analysis.get("results", []):
                try:
                    # Make file path relative to base path
                    relative_filename = self._make_relative_path(
                        issue_data["filename"], self.base_path
                    )
                    
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

        return issues

    def _run_bandit(self, app_path: Path) -> ToolResult:
        """
        Run Bandit security analysis as a module.
        
        Args:
            app_path: Path to the application code to analyze
            
        Returns:
            ToolResult containing issues found, raw output, and status
        """
        # Use sys.executable to call the bandit module
        command = [sys.executable, "-m", "bandit", "-r", ".", "-f", "json", "-ll", "-ii"]
        return self._run_tool("Bandit", command, self._parse_bandit_output, working_directory=app_path)

    def _parse_safety_output(self, output: str) -> List[BackendSecurityIssue]:
        """
        Parse Safety CLI output into BackendSecurityIssue objects.
        
        Args:
            output: Text output from Safety tool
            
        Returns:
            List of BackendSecurityIssue objects parsed from the output
        """
        issues: List[BackendSecurityIssue] = []
        
        # Pattern for vulnerability lines
        vuln_pattern = re.compile(
            r"([\w-]+)\s+([\d.]+)\s+([<>=]+[\d.]+)\s+(High|Medium|Low) Severity\s+ID: (\d+)"
        )
        
        for line in output.splitlines():
            match = vuln_pattern.search(line)
            if match:
                package, installed_version, affected_versions, severity, vuln_id = match.groups()
                issues.append(BackendSecurityIssue(
                    filename="requirements.txt / dependencies",
                    line_number=0,
                    issue_text=f"Vulnerable dependency: {package} ({installed_version}). "
                              f"Affected: {affected_versions}. Safety ID: {vuln_id}",
                    severity=severity.upper(),
                    confidence="HIGH",  # If Safety reports it, confidence is high
                    issue_type=f"safety_{vuln_id}",
                    line_range=[0],
                    code=f"{package}=={installed_version}",
                    tool="Safety",
                    fix_suggestion=f"Update {package} to a version not matching {affected_versions}."
                ))

        # Check for unpinned dependencies
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
                    fix_suggestion=f"Pin '{package_name}' to a specific, secure version "
                                  f"(e.g., {package_name}==x.y.z)."
                ))

        return issues

    def _run_safety(self, app_path: Path) -> ToolResult:
        """
        Run Safety check on dependencies as a module.
        
        Args:
            app_path: Path to the application directory with requirements.txt
            
        Returns:
            ToolResult containing issues found, raw output, and status
        """
        requirements_file = app_path / "requirements.txt"
        if not requirements_file.exists():
            return ToolResult(
                issues=[], 
                output="No requirements.txt found",
                status="⚠️ No requirements.txt found"
            )

        # Read requirements file content
        try:
            with open(requirements_file, 'r') as f:
                req_content = f.read()
        except Exception as e:
            error_msg = f"Error reading requirements file: {e}"
            logger.error(error_msg)
            return ToolResult(
                issues=[], 
                output=error_msg,
                status=f"❌ {error_msg}"
            )

        # Use sys.executable to call the safety module
        command = [sys.executable, "-m", "safety", "check", "--stdin"]
        return self._run_tool(
            "Safety", command, self._parse_safety_output, 
            working_directory=app_path, input_data=req_content
        )

    def _parse_pylint_output(self, output: str) -> List[BackendSecurityIssue]:
        """
        Parse Pylint JSON output into BackendSecurityIssue objects.
        
        Args:
            output: JSON output from Pylint
            
        Returns:
            List of BackendSecurityIssue objects parsed from the output
        """
        issues: List[BackendSecurityIssue] = []
        
        try:
            # Find the start of JSON array
            json_start_index = output.find('[')
            if json_start_index == -1:
                logger.warning(f"Could not find start of JSON array in Pylint output")
                return []

            json_output = output[json_start_index:]
            
            # Verify valid JSON format
            if not json_output.strip().startswith('['):
                logger.warning(f"Expected JSON array to start with '[', got: {json_output[:20]}...")
                return []
                
            pylint_data = json.loads(json_output)
            
            # Map Pylint message types to severity levels
            severity_map = {"F": "HIGH", "E": "HIGH", "W": "MEDIUM", "R": "LOW", "C": "LOW"}

            for issue_data in pylint_data:
                try:
                    relative_filename = self._make_relative_path(
                        issue_data["path"], self.base_path
                    )
                    
                    issues.append(BackendSecurityIssue(
                        filename=relative_filename,
                        line_number=issue_data["line"],
                        issue_text=f"[{issue_data['symbol']} ({issue_data['message-id']})] "
                                  f"{issue_data['message']}",
                        severity=severity_map.get(issue_data["type"], "LOW"),
                        confidence="MEDIUM",  # Pylint issues are generally medium confidence
                        issue_type=f"pylint_{issue_data['symbol']}",
                        line_range=[issue_data["line"]],
                        code="N/A",  # Pylint JSON format doesn't include code snippet
                        tool="Pylint",
                        fix_suggestion=None
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

    def _run_pylint(self, app_path: Path) -> ToolResult:
        """
        Run Pylint for code quality analysis as a module.
        
        Args:
            app_path: Path to the application code to analyze
            
        Returns:
            ToolResult containing issues found, raw output, and status
        """
        has_files, source_files = self._check_source_files(app_path)
        if not has_files:
            return ToolResult(
                issues=[], 
                output="No Python source files found for Pylint.",
                status="⚠️ No Python files found"
            )

        # Convert to paths relative to app_path
        relative_source_files = []
        for f in source_files:
            try:
                rel_path = str(Path(f).relative_to(app_path))
                relative_source_files.append(rel_path)
            except ValueError:
                logger.warning(f"Path '{f}' cannot be made relative to '{app_path}', using as is.")
                relative_source_files.append(f)

        # Use sys.executable to call the pylint module
        command = [
            sys.executable, "-m", "pylint", 
            "--output-format=json", "--exit-zero"
        ] + relative_source_files
        
        return self._run_tool("Pylint", command, self._parse_pylint_output, working_directory=app_path)

    def _parse_vulture_output(self, output: str) -> List[BackendSecurityIssue]:
        """
        Parse Vulture text output into BackendSecurityIssue objects.
        
        Args:
            output: Text output from Vulture
            
        Returns:
            List of BackendSecurityIssue objects parsed from the output
        """
        issues: List[BackendSecurityIssue] = []
        
        # Pattern for Vulture output lines
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

                    # Map confidence percentage to HIGH/MEDIUM/LOW
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
                        severity="LOW",  # Dead code is generally low severity
                        confidence=confidence,
                        issue_type="dead_code",
                        line_range=[line_num],
                        code="N/A",  # Vulture doesn't provide code snippet
                        tool="Vulture",
                        fix_suggestion="Verify if code is unused and remove it to reduce "
                                      "clutter and potential attack surface."
                    ))
                except Exception as e:
                    logger.warning(f"Error processing Vulture line '{line}': {e}")
            else:
                logger.debug(f"Could not parse Vulture line: {line}")

        return issues

    def _run_vulture(self, app_path: Path) -> ToolResult:
        """
        Run Vulture to detect dead code as a module.
        
        Args:
            app_path: Path to the application code to analyze
            
        Returns:
            ToolResult containing issues found, raw output, and status
        """
        # Use sys.executable to call the vulture module
        command = [sys.executable, "-m", "vulture", ".", "--min-confidence", "50"]
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
            - Dictionary mapping tool names to status messages.
            - Dictionary mapping tool names to their raw output strings.

        Raises:
            ValueError: If the target application path does not exist or contains no Python files
                      (unless only Safety is being run).
        """
        # Construct path relative to the base path
        app_path = self.base_path / "models" / f"{model}/app{app_num}/backend"
        logger.info(f"Starting backend security analysis for: {app_path}")

        if not app_path.is_dir():
            raise ValueError(f"Application backend path does not exist: {app_path}")

        has_files, _ = self._check_source_files(app_path)
        tools_to_run = self.all_tools if use_all_tools else self.default_tools

        # Check if source files are needed but missing
        requires_py_files = any(tool for tool in tools_to_run if tool != "safety")
        if requires_py_files and not has_files:
            raise ValueError(
                f"No Python source files found in {app_path}, "
                f"cannot run tools like Bandit, Pylint, Vulture."
            )
        elif not has_files:
            logger.warning(f"No Python source files in {app_path}, only running Safety if selected.")

        all_issues: List[BackendSecurityIssue] = []
        tool_status: Dict[str, str] = {}
        tool_outputs: Dict[str, str] = {}
        
        logger.info(f"Running tools: {', '.join(tools_to_run)}")

        # Use ThreadPoolExecutor for concurrent tool execution
        with ThreadPoolExecutor(max_workers=len(tools_to_run)) as executor:
            future_to_tool = {}
            
            # Submit all tool tasks at once
            for tool in tools_to_run:
                # Skip tools requiring Python files if none exist
                if tool != "safety" and not has_files:
                    tool_status[tool] = "⚪ Skipped (no .py files)"
                    continue
                    
                # Skip tools with missing runners
                if tool not in self.tool_configs:
                    tool_status[tool] = "❓ Not configured"
                    continue
                    
                # Submit the tool task
                future_to_tool[executor.submit(self.tool_configs[tool], app_path)] = tool

            # Process results as they complete
            for future in as_completed(future_to_tool):
                tool = future_to_tool[future]
                try:
                    # Get result from the completed future
                    result = future.result()
                    
                    # Store issues, output, and status
                    all_issues.extend(result.issues)
                    tool_outputs[tool] = result.output
                    tool_status[tool] = result.status
                except Exception as e:
                    logger.exception(f"Error running tool {tool}: {e}")
                    tool_status[tool] = f"❌ Error: {str(e)}"
                    tool_outputs[tool] = f"Error running tool: {str(e)}"

        # Mark tools that were not run
        for tool in self.all_tools:
            if tool not in tool_status:
                reason = "quick scan" if not use_all_tools else "not configured"
                tool_status[tool] = f"⚪ Skipped ({reason})"

        # Sort issues by severity, confidence, filename, and line number
        sorted_issues = sorted(
            all_issues,
            key=lambda issue: (
                SEVERITY_ORDER.get(issue.severity, DEFAULT_SEVERITY_LEVEL),
                CONFIDENCE_ORDER.get(issue.confidence, DEFAULT_SEVERITY_LEVEL),
                issue.filename,
                issue.line_number
            )
        )
        
        logger.info(f"Backend analysis complete. Total issues: {len(sorted_issues)}")
        return sorted_issues, tool_status, tool_outputs

    def get_analysis_summary(self, issues: List[BackendSecurityIssue]) -> Dict[str, Any]:
        """
        Generate summary statistics for the analysis results.

        Args:
            issues: List of BackendSecurityIssue objects found.

        Returns:
            Dictionary containing summary statistics.
        """
        # Initialize the summary structure
        summary = {
            "total_issues": len(issues),
            "severity_counts": {sev.value: 0 for sev in Severity},
            "confidence_counts": {conf.value: 0 for conf in Confidence},
            "files_affected": len({issue.filename for issue in issues}),
            "issue_types": {},
            "tool_counts": {},
            "scan_time": datetime.now().isoformat()
        }

        # Count issues by various attributes
        for issue in issues:
            summary["severity_counts"][issue.severity] = (
                summary["severity_counts"].get(issue.severity, 0) + 1
            )
            summary["confidence_counts"][issue.confidence] = (
                summary["confidence_counts"].get(issue.confidence, 0) + 1
            )
            summary["issue_types"][issue.issue_type] = (
                summary["issue_types"].get(issue.issue_type, 0) + 1
            )
            summary["tool_counts"][issue.tool] = (
                summary["tool_counts"].get(issue.tool, 0) + 1
            )

        return summary