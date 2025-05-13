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

logger = logging.getLogger(__name__)

# Constants
TOOL_TIMEOUT = 30

# Status message constants
STATUS_ERROR = "❌ Error"
STATUS_ERROR_WITH_CODE = "❌ Error (code {code})"
STATUS_PARSER_ERROR = "❌ Parser error: {error}"
STATUS_TIMEOUT = "❌ Timeout after {timeout}s"
STATUS_COMMAND_NOT_FOUND = "❌ Command not found"
STATUS_NO_OUTPUT = "⚠️ No output"
STATUS_NO_ISSUES = "✅ No issues found"
STATUS_FOUND_ISSUES = "ℹ️ Found {count} issues"
STATUS_SKIPPED_NO_FILES = "⚪ Skipped (no .py files)"
STATUS_SKIPPED_REASON = "⚪ Skipped ({reason})"
STATUS_NOT_CONFIGURED = "❓ Not configured"


class Severity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Confidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


SEVERITY_ORDER = {Severity.HIGH: 0, Severity.MEDIUM: 1, Severity.LOW: 2}
CONFIDENCE_ORDER = {Confidence.HIGH: 0, Confidence.MEDIUM: 1, Confidence.LOW: 2}
DEFAULT_SEVERITY_LEVEL = 3


@dataclass
class BackendSecurityIssue:
    """Represents a security issue found in backend code."""
    filename: str
    line_number: int
    issue_text: str
    severity: str
    confidence: str
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
    """Configuration for a security analysis tool."""
    command_args: List[str]
    parser: Callable[[str], List[BackendSecurityIssue]]
    requires_files: bool


class BackendSecurityAnalyzer:
    """Analyzes backend code for security issues using various tools."""

    def __init__(self, base_path: Path):
        """
        Initialize the analyzer with the base path for the application.
        
        Args:
            base_path: Base directory for the application
        """
        if not base_path.is_dir():
            logger.warning(f"Base path '{base_path}' does not exist or is not a directory.")
        self.base_path = base_path

        self.default_tools: Set[str] = {"bandit"}
        self.all_tools: Set[str] = {"bandit", "safety", "pylint", "vulture"}

        self.tool_configs: Dict[str, Callable[[Path], ToolResult]] = {
            "bandit": self._run_bandit,
            "safety": self._run_safety,
            "pylint": self._run_pylint,
            "vulture": self._run_vulture
        }

    def _check_source_files(self, directory: Path) -> Tuple[bool, List[str]]:
        """
        Check if Python source files exist in the given directory.
        
        Args:
            directory: Directory to check for Python files
            
        Returns:
            Tuple of (has_files, file_paths)
        """
        if not directory.is_dir():
            logger.warning(f"Target directory '{directory}' does not exist.")
            return False, []

        source_files = list(directory.rglob('*.py'))
        return bool(source_files), [str(f) for f in source_files]
    
    def _check_tool_availability(self, tool_name: str) -> bool:
        """
        Check if a tool is available in the system.
        
        Args:
            tool_name: Name of the tool to check
            
        Returns:
            True if the tool is available, False otherwise
        """
        try:
            if tool_name == "safety":
                # Check if safety is available
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "show", "safety"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return result.returncode == 0
            elif tool_name in ("bandit", "pylint", "vulture"):
                # Check if the module is importable
                result = subprocess.run(
                    [sys.executable, "-c", f"import {tool_name}"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return result.returncode == 0
            return False
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _run_tool(
        self,
        tool_name: str,
        command: List[str],
        parser: Callable[[str], List[BackendSecurityIssue]],
        working_directory: Optional[Path] = None,
        input_data: Optional[str] = None
    ) -> ToolResult:
        """
        Run a security analysis tool and parse its output.
        
        Args:
            tool_name: Name of the tool to run
            command: Command to execute
            parser: Function to parse the tool's output
            working_directory: Directory to run the command in (defaults to self.base_path)
            input_data: Data to pass to the command via stdin
            
        Returns:
            ToolResult with parsed issues, raw output, and status
        """
        issues: List[BackendSecurityIssue] = []
        raw_output = f"{tool_name} execution failed."
        status = STATUS_ERROR

        try:
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
                check=False,
                cwd=effective_cwd,
                input=input_data
            )

            logger.info(f"[{tool_name}] Subprocess finished with return code: {result.returncode}")
            raw_output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

            if result.returncode != 0 and not result.stdout:
                logger.warning(f"{tool_name} exited with code {result.returncode}. Stderr: {result.stderr}")
                status = STATUS_ERROR_WITH_CODE.format(code=result.returncode)
            elif result.stdout:
                try:
                    issues = parser(result.stdout)
                    if issues:
                        status = STATUS_FOUND_ISSUES.format(count=len(issues))
                    else:
                        status = STATUS_NO_ISSUES
                    logger.info(f"{tool_name} found {len(issues)} issues.")
                except Exception as e:
                    logger.error(f"Failed to parse {tool_name} output: {e}\nOutput:\n{result.stdout[:500]}...")
                    raw_output += f"\nPARSING_ERROR: {str(e)}"
                    status = STATUS_PARSER_ERROR.format(error=str(e))
            else:
                logger.info(f"{tool_name} produced no standard output.")
                status = STATUS_NO_OUTPUT

        except subprocess.TimeoutExpired:
            logger.error(f"{tool_name} timed out after {TOOL_TIMEOUT} seconds.")
            raw_output = f"{tool_name} timed out after {TOOL_TIMEOUT} seconds."
            status = STATUS_TIMEOUT.format(timeout=TOOL_TIMEOUT)
        except FileNotFoundError:
            cmd_executed = command[0]
            logger.error(f"{tool_name} command/interpreter not found: {cmd_executed}")
            raw_output = f"{tool_name} command/interpreter not found: {cmd_executed}"
            status = STATUS_COMMAND_NOT_FOUND
        except Exception as e:
            logger.exception(f"An unexpected error occurred while running {tool_name}: {e}")
            raw_output = f"Unexpected error running {tool_name}: {str(e)}"
            status = f"{STATUS_ERROR}: {str(e)}"

        return ToolResult(issues=issues, output=raw_output, status=status)

    def _make_relative_path(self, file_path: str, base_dir: Path) -> str:
        """
        Convert an absolute path to a path relative to the base directory.
        
        Args:
            file_path: Path to convert
            base_dir: Base directory to make the path relative to
            
        Returns:
            Relative path as a string
        """
        try:
            file_path_obj = Path(file_path)

            if file_path_obj.is_absolute():
                abs_file_path = file_path_obj.resolve()
                abs_base_dir = base_dir.resolve()

                try:
                    relative = abs_file_path.relative_to(abs_base_dir)
                    return str(relative)
                except ValueError:
                    base_str = str(abs_base_dir)
                    file_str = str(abs_file_path)
                    if file_str.startswith(base_str):
                        return file_str[len(base_str):].lstrip('/\\')

                    logger.warning(f"Path '{file_path}' cannot be made relative to '{base_dir}'")
                    return file_path
            else:
                return file_path
        except Exception as e:
            logger.warning(f"Error processing path '{file_path}': {e}")
            return file_path

    def _parse_bandit_output(self, output: str) -> List[BackendSecurityIssue]:
        """
        Parse Bandit JSON output into BackendSecurityIssue objects.
        
        Args:
            output: Bandit output in JSON format
            
        Returns:
            List of BackendSecurityIssue objects
        """
        issues: List[BackendSecurityIssue] = []

        if not output.strip():
            logger.warning("Bandit output is empty")
            return issues

        try:
            analysis = json.loads(output)

            if "errors" in analysis and analysis["errors"]:
                logger.warning(f"Bandit reported errors: {analysis['errors']}")

            for issue_data in analysis.get("results", []):
                try:
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
        Run Bandit security analysis on the application path.
        
        Args:
            app_path: Path to the application backend
            
        Returns:
            ToolResult with Bandit analysis results
        """
        if not self._check_tool_availability("bandit"):
            return ToolResult(
                issues=[],
                output="Bandit tool not found in the system",
                status=STATUS_COMMAND_NOT_FOUND
            )
            
        command = [sys.executable, "-m", "bandit", "-r", ".", "-f", "json", "-ll", "-ii"]
        return self._run_tool("Bandit", command, self._parse_bandit_output, working_directory=app_path)

    def _parse_safety_output(self, output: str) -> List[BackendSecurityIssue]:
        """
        Parse Safety output into BackendSecurityIssue objects.
        
        Args:
            output: Safety output text
            
        Returns:
            List of BackendSecurityIssue objects
        """
        issues: List[BackendSecurityIssue] = []

        if not output.strip():
            logger.warning("Safety output is empty")
            return issues

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
                    confidence="HIGH",
                    issue_type=f"safety_{vuln_id}",
                    line_range=[0],
                    code=f"{package}=={installed_version}",
                    tool="Safety",
                    fix_suggestion=f"Update {package} to a version not matching {affected_versions}."
                ))

        unpinned_match = re.search(r"Warning: unpinned requirement '([\w-]+)'", output)
        if unpinned_match:
            package_name = unpinned_match.group(1)
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
        Run Safety security analysis on the application dependencies.
        
        Args:
            app_path: Path to the application backend
            
        Returns:
            ToolResult with Safety analysis results
        """
        if not self._check_tool_availability("safety"):
            return ToolResult(
                issues=[],
                output="Safety tool not found in the system",
                status=STATUS_COMMAND_NOT_FOUND
            )
            
        requirements_file = app_path / "requirements.txt"
        if not requirements_file.exists():
            return ToolResult(
                issues=[],
                output="No requirements.txt found",
                status="⚠️ No requirements.txt found"
            )

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

        command = [sys.executable, "-m", "safety", "check", "--stdin"]
        return self._run_tool(
            "Safety", command, self._parse_safety_output,
            working_directory=app_path, input_data=req_content
        )

    def _parse_pylint_output(self, output: str) -> List[BackendSecurityIssue]:
        """
        Parse Pylint JSON output into BackendSecurityIssue objects.
        
        Args:
            output: Pylint output in JSON format
            
        Returns:
            List of BackendSecurityIssue objects
        """
        issues: List[BackendSecurityIssue] = []

        if not output.strip():
            logger.warning("Pylint output is empty")
            return issues

        try:
            # Extract JSON part - pylint sometimes includes other text before JSON
            json_start_index = output.find('[')
            if json_start_index == -1:
                logger.warning("Could not find start of JSON array in Pylint output")
                return []

            json_output = output[json_start_index:]

            if not json_output.strip().startswith('['):
                logger.warning(f"Expected JSON array to start with '[', got: {json_output[:20]}...")
                return []

            pylint_data = json.loads(json_output)

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
                        confidence="MEDIUM",
                        issue_type=f"pylint_{issue_data['symbol']}",
                        line_range=[issue_data["line"]],
                        code="N/A",
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
        Run Pylint analysis on the application code.
        
        Args:
            app_path: Path to the application backend
            
        Returns:
            ToolResult with Pylint analysis results
        """
        if not self._check_tool_availability("pylint"):
            return ToolResult(
                issues=[],
                output="Pylint tool not found in the system",
                status=STATUS_COMMAND_NOT_FOUND
            )
            
        has_files, source_files = self._check_source_files(app_path)
        if not has_files:
            return ToolResult(
                issues=[],
                output="No Python source files found for Pylint.",
                status=STATUS_SKIPPED_NO_FILES
            )

        relative_source_files = []
        for f in source_files:
            try:
                rel_path = str(Path(f).relative_to(app_path))
                relative_source_files.append(rel_path)
            except ValueError:
                logger.warning(f"Path '{f}' cannot be made relative to '{app_path}', using as is.")
                relative_source_files.append(f)

        command = [
            sys.executable, "-m", "pylint",
            "--output-format=json", "--exit-zero"
        ] + relative_source_files

        return self._run_tool("Pylint", command, self._parse_pylint_output, working_directory=app_path)

    def _parse_vulture_output(self, output: str) -> List[BackendSecurityIssue]:
        """
        Parse Vulture output into BackendSecurityIssue objects.
        
        Args:
            output: Vulture output text
            
        Returns:
            List of BackendSecurityIssue objects
        """
        issues: List[BackendSecurityIssue] = []

        if not output.strip():
            logger.warning("Vulture output is empty")
            return issues

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
                        severity="LOW",
                        confidence=confidence,
                        issue_type="dead_code",
                        line_range=[line_num],
                        code="N/A",
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
        Run Vulture to find unused code in the application.
        
        Args:
            app_path: Path to the application backend
            
        Returns:
            ToolResult with Vulture analysis results
        """
        if not self._check_tool_availability("vulture"):
            return ToolResult(
                issues=[],
                output="Vulture tool not found in the system",
                status=STATUS_COMMAND_NOT_FOUND
            )
            
        command = [sys.executable, "-m", "vulture", ".", "--min-confidence", "50"]
        return self._run_tool("Vulture", command, self._parse_vulture_output, working_directory=app_path)

    def run_security_analysis(
        self,
        model: str,
        app_num: int,
        use_all_tools: bool = False
    ) -> Tuple[List[BackendSecurityIssue], Dict[str, str], Dict[str, str]]:
        """
        Run security analysis on a specific model and app number.
        
        Args:
            model: Model name
            app_num: App number 
            use_all_tools: Whether to use all available tools (default: False)
            
        Returns:
            Tuple of (issues, tool_status, tool_outputs)
            
        Raises:
            ValueError: If the application path doesn't exist or required Python files aren't found
        """
        app_path = self.base_path / "models" / f"{model}/app{app_num}/backend"
        logger.info(f"Starting backend security analysis for: {app_path}")

        if not app_path.is_dir():
            raise ValueError(f"Application backend path does not exist: {app_path}")

        has_files, _ = self._check_source_files(app_path)
        tools_to_run = self.all_tools if use_all_tools else self.default_tools

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

        # Limit max_workers to CPU count or tools count, whichever is less
        max_workers = min(len(tools_to_run), os.cpu_count() or 4)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_tool = {}

            for tool in tools_to_run:
                if tool != "safety" and not has_files:
                    tool_status[tool] = STATUS_SKIPPED_NO_FILES
                    continue

                if tool not in self.tool_configs:
                    tool_status[tool] = STATUS_NOT_CONFIGURED
                    continue

                future_to_tool[executor.submit(self.tool_configs[tool], app_path)] = tool

            for future in as_completed(future_to_tool):
                tool = future_to_tool[future]
                try:
                    result = future.result()

                    all_issues.extend(result.issues)
                    tool_outputs[tool] = result.output
                    tool_status[tool] = result.status
                except Exception as e:
                    logger.exception(f"Error running tool {tool}: {e}")
                    tool_status[tool] = f"{STATUS_ERROR}: {str(e)}"
                    tool_outputs[tool] = f"Error running tool: {str(e)}"

        for tool in self.all_tools:
            if tool not in tool_status:
                reason = "quick scan" if not use_all_tools else "not configured"
                tool_status[tool] = STATUS_SKIPPED_REASON.format(reason=reason)

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
        Generate a summary of the security analysis results.
        
        Args:
            issues: List of BackendSecurityIssue objects
            
        Returns:
            Dictionary with summary information
        """
        summary = {
            "total_issues": len(issues),
            "severity_counts": {sev.value: 0 for sev in Severity},
            "confidence_counts": {conf.value: 0 for conf in Confidence},
            "files_affected": len({issue.filename for issue in issues}),
            "issue_types": {},
            "tool_counts": {},
            "scan_time": datetime.now().isoformat()
        }

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