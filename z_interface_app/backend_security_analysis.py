import json
import logging
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional, Tuple, Any, Callable, TypedDict, NamedTuple, Set, Union

# Attempt to import JsonResultsManager from utils.py
try:
    from utils import JsonResultsManager
except ImportError:
    # Fallback if utils.py is not in the same directory or path
    class JsonResultsManager:
        def __init__(self, base_path: Path, module_name: str):
            self.base_path = Path(base_path)
            self.module_name = module_name
            print(f"Warning: JsonResultsManager initialized without a proper logger for {module_name}")

        def save_results(self, model: str, app_num: int, results: Any, file_name: str = ".backend_security_results.json", **kwargs) -> Path:
            results_dir = self.base_path / "z_interface_app" / "results" / model / f"app{app_num}"
            results_dir.mkdir(parents=True, exist_ok=True)
            results_path = results_dir / file_name
            
            data_to_save = results
            if hasattr(results, 'to_dict'):
                data_to_save = results.to_dict()
            elif isinstance(results, (list, tuple)) and all(hasattr(item, 'to_dict') for item in results):
                data_to_save = [item.to_dict() for item in results]

            try:
                with open(results_path, "w", encoding='utf-8') as f:
                    json.dump(data_to_save, f, indent=2)
                print(f"Info: [{self.module_name}] Saved results to {results_path}")
            except (IOError, OSError) as e:
                print(f"Error: [{self.module_name}] Error saving results to {results_path}: {e}")
                raise
            return results_path

        def load_results(self, model: str, app_num: int, file_name: str = ".backend_security_results.json", **kwargs) -> Optional[Any]:
            results_path = self.base_path / "results" / model / f"app{app_num}" / file_name
            if not results_path.exists():
                print(f"Warning: [{self.module_name}] Results file not found: {results_path}")
                return None
            try:
                with open(results_path, "r", encoding='utf-8') as f:
                    data = json.load(f)
                print(f"Info: [{self.module_name}] Loaded results from {results_path}")
                return data
            except (IOError, OSError, json.JSONDecodeError) as e:
                print(f"Error: [{self.module_name}] Error loading results from {results_path}: {e}")
                return None

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

# Tool names as constants
TOOL_BANDIT = "bandit"
TOOL_SAFETY = "safety"
TOOL_PYLINT = "pylint"
TOOL_VULTURE = "vulture"


class Severity(str, Enum):
    """Severity levels for security issues."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Confidence(str, Enum):
    """Confidence levels for security issues."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


SEVERITY_ORDER = {Severity.HIGH: 0, Severity.MEDIUM: 1, Severity.LOW: 2}
CONFIDENCE_ORDER = {Confidence.HIGH: 0, Confidence.MEDIUM: 1, Confidence.LOW: 2}
DEFAULT_SEVERITY_LEVEL = 3


def validate_path_security(base_path: Path, target_path: Path) -> bool:
    """
    Validate that target_path is within base_path to prevent traversal attacks.
    
    Args:
        base_path: Base directory that should contain target
        target_path: Path to validate
        
    Returns:
        True if path is safe, False otherwise
    """
    try:
        base = base_path.resolve()
        target = target_path.resolve()
        # Python 3.9+ has is_relative_to, for older versions use this approach
        try:
            target.relative_to(base)
            return True
        except ValueError:
            return False
    except (OSError, ValueError):
        return False


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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return field_values_to_dict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackendSecurityIssue':
        """Create BackendSecurityIssue from dictionary."""
        return cls(**data)


def field_values_to_dict(obj: Any) -> Dict[str, Any]:
    """Helper to convert dataclass to dict, handling nested dataclasses if any."""
    if hasattr(obj, "__dataclass_fields__"):
        result = {}
        for field_name in obj.__dataclass_fields__:
            value = getattr(obj, field_name)
            if hasattr(value, "__dataclass_fields__"):
                result[field_name] = field_values_to_dict(value)
            elif isinstance(value, list) and value and hasattr(value[0], "__dataclass_fields__"):
                result[field_name] = [field_values_to_dict(item) for item in value]
            else:
                result[field_name] = value
        return result
    return obj


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

    def __init__(self, base_path: Union[str, Path]):
        """
        Initialize the analyzer with the base path for the application.

        Args:
            base_path: Base directory for the application
        """
        self.base_path = Path(base_path).resolve()
        if not self.base_path.is_dir():
            logger.warning(f"Base path '{self.base_path}' does not exist or is not a directory.")
        
        # Initialize JsonResultsManager
        self.results_manager = JsonResultsManager(base_path=self.base_path, module_name="backend_security")

        self.default_tools: Set[str] = {TOOL_BANDIT}
        self.all_tools: Set[str] = {TOOL_BANDIT, TOOL_SAFETY, TOOL_PYLINT, TOOL_VULTURE}

        self.tool_configs: Dict[str, Callable[[Path], ToolResult]] = {
            TOOL_BANDIT: self._run_bandit,
            TOOL_SAFETY: self._run_safety,
            TOOL_PYLINT: self._run_pylint,
            TOOL_VULTURE: self._run_vulture
        }
        self.analysis_lock = Lock()

    def _find_application_path(self, model: str, app_num: int) -> Optional[Path]:
        """
        Find the application backend directory path for a specific model and app number.
        
        Args:
            model: Model name
            app_num: Application number
            
        Returns:
            Path to backend directory or None if not found
        """
        logger.debug(f"Finding backend path for {model}/app{app_num}")
        
        # Try multiple possible locations
        # First, check if base_path already contains 'models'
        workspace_root = self.base_path.parent
        
        # Try parent directory structure first (preferred)
        candidates = [
            workspace_root / "models" / model / f"app{app_num}" / "backend",
            self.base_path / model / f"app{app_num}" / "backend",
            self.base_path / "models" / model / f"app{app_num}" / "backend",
        ]
        
        for candidate in candidates:
            if candidate.is_dir():
                logger.info(f"Found backend directory at: {candidate}")
                # Security check
                if not validate_path_security(workspace_root, candidate):
                    logger.error(f"Security violation: {candidate} is outside allowed paths")
                    return None
                return candidate
        
        logger.error(f"Backend directory not found for {model}/app{app_num}")
        logger.debug(f"Tried paths: {[str(c) for c in candidates]}")
        return None

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

        try:
            source_files = []
            for file_path in directory.rglob('*.py'):
                # Security check for each file
                if validate_path_security(directory, file_path):
                    source_files.append(str(file_path))
                else:
                    logger.warning(f"Skipping file outside allowed path: {file_path}")
            
            return bool(source_files), source_files
        except (OSError, PermissionError) as e:
            logger.error(f"Error scanning directory {directory}: {e}")
            return False, []

    def _check_tool_availability(self, tool_name: str) -> bool:
        """
        Check if a tool is available in the system.

        Args:
            tool_name: Name of the tool to check

        Returns:
            True if the tool is available, False otherwise
        """
        try:
            if tool_name == TOOL_SAFETY:
                # Check if safety is available via pip
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "show", "safety"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return result.returncode == 0
            elif tool_name in (TOOL_BANDIT, TOOL_PYLINT, TOOL_VULTURE):
                # Check if the module is importable
                result = subprocess.run(
                    [sys.executable, "-c", f"import {tool_name}"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return result.returncode == 0
            return False
        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout checking availability of {tool_name}")
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
            working_directory: Directory to run the command in
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
                cwd=str(effective_cwd),
                input=input_data,
                encoding='utf-8',
                errors='replace'
            )

            logger.info(f"[{tool_name}] Process finished with return code: {result.returncode}")
            raw_output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

            if result.returncode != 0 and not result.stdout:
                logger.warning(f"{tool_name} exited with code {result.returncode}")
                status = STATUS_ERROR_WITH_CODE.format(code=result.returncode)
            elif result.stdout:
                try:
                    issues = parser(result.stdout)
                    if issues:
                        status = STATUS_FOUND_ISSUES.format(count=len(issues))
                    else:
                        status = STATUS_NO_ISSUES
                    logger.info(f"{tool_name} found {len(issues)} issues.")
                except (ValueError, KeyError, json.JSONDecodeError) as e:
                    logger.error(f"Failed to parse {tool_name} output: {e}")
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
            cmd_executed = command[0] if command else "unknown"
            logger.error(f"{tool_name} command not found: {cmd_executed}")
            raw_output = f"{tool_name} command not found: {cmd_executed}"
            status = STATUS_COMMAND_NOT_FOUND
        except OSError as e:
            logger.error(f"OS error running {tool_name}: {e}")
            raw_output = f"OS error running {tool_name}: {str(e)}"
            status = f"{STATUS_ERROR}: OS error"

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
                    # Path is not relative to base_dir
                    # Try to find a common ancestor
                    base_str = str(abs_base_dir)
                    file_str = str(abs_file_path)
                    if file_str.startswith(base_str):
                        return file_str[len(base_str):].lstrip('/\\')

                    logger.debug(f"Path '{file_path}' not relative to '{base_dir}'")
                    return file_path
            else:
                return file_path
        except (OSError, ValueError) as e:
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
                    issue = self._create_bandit_issue(issue_data)
                    if issue:
                        issues.append(issue)
                except KeyError as ke:
                    logger.warning(f"Missing expected key in Bandit issue: {ke}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error processing Bandit issue: {e}")
                    
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Bandit JSON: {e}")

        return issues

    def _create_bandit_issue(self, issue_data: Dict[str, Any]) -> Optional[BackendSecurityIssue]:
        """Create a BackendSecurityIssue from Bandit issue data."""
        relative_filename = self._make_relative_path(
            issue_data["filename"], self.base_path
        )

        return BackendSecurityIssue(
            filename=relative_filename,
            line_number=issue_data["line_number"],
            issue_text=issue_data["issue_text"],
            severity=issue_data["issue_severity"].upper(),
            confidence=issue_data["issue_confidence"].upper(),
            issue_type=issue_data["test_name"],
            line_range=issue_data["line_range"],
            code=issue_data.get("code", "N/A"),
            tool="Bandit",
            fix_suggestion=issue_data.get("more_info")
        )

    def _run_bandit(self, app_path: Path) -> ToolResult:
        """
        Run Bandit security analysis on the application path.

        Args:
            app_path: Path to the application backend

        Returns:
            ToolResult with Bandit analysis results
        """
        if not self._check_tool_availability(TOOL_BANDIT):
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

        # Pattern for vulnerability lines
        vuln_pattern = re.compile(
            r"([\w\-\[\]]+)\s+([\d.]+)\s+([<>=]+[\d.]+)\s+(High|Medium|Low) Severity\s+ID: (\d+)"
        )

        for line in output.splitlines():
            match = vuln_pattern.search(line)
            if match:
                issue = self._create_safety_vuln_issue(match.groups())
                if issue:
                    issues.append(issue)

        # Check for unpinned dependencies
        unpinned_pattern = re.compile(r"Warning: unpinned requirement '([\w\-\[\]]+)'")
        for match in unpinned_pattern.finditer(output):
            package_name = match.group(1)
            if not any(issue.code.startswith(f"{package_name}==") for issue in issues):
                issue = self._create_safety_unpinned_issue(package_name)
                if issue:
                    issues.append(issue)

        return issues

    def _create_safety_vuln_issue(self, match_groups: Tuple[str, ...]) -> Optional[BackendSecurityIssue]:
        """Create a vulnerability issue from Safety output match."""
        package, installed_version, affected_versions, severity, vuln_id = match_groups
        
        return BackendSecurityIssue(
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
        )

    def _create_safety_unpinned_issue(self, package_name: str) -> BackendSecurityIssue:
        """Create an unpinned dependency issue."""
        return BackendSecurityIssue(
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
        )

    def _run_safety(self, app_path: Path) -> ToolResult:
        """
        Run Safety security analysis on the application dependencies.

        Args:
            app_path: Path to the application backend

        Returns:
            ToolResult with Safety analysis results
        """
        if not self._check_tool_availability(TOOL_SAFETY):
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
            with open(requirements_file, 'r', encoding='utf-8') as f:
                req_content = f.read()
        except (IOError, OSError) as e:
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
            # Extract JSON part - pylint sometimes includes other text
            json_output = self._extract_json_from_output(output)
            if not json_output:
                return issues

            pylint_data = json.loads(json_output)
            severity_map = {"F": "HIGH", "E": "HIGH", "W": "MEDIUM", "R": "LOW", "C": "LOW"}

            for issue_data in pylint_data:
                try:
                    issue = self._create_pylint_issue(issue_data, severity_map)
                    if issue:
                        issues.append(issue)
                except KeyError as ke:
                    logger.warning(f"Missing expected key in Pylint issue: {ke}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error processing Pylint issue: {e}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Pylint JSON: {e}")

        return issues

    def _extract_json_from_output(self, output: str) -> Optional[str]:
        """Extract JSON array from tool output that may contain extra text."""
        json_start_index = output.find('[')
        if json_start_index == -1:
            logger.warning("Could not find start of JSON array in output")
            return None

        json_output = output[json_start_index:]
        if not json_output.strip().startswith('['):
            logger.warning("Expected JSON array to start with '['")
            return None

        return json_output

    def _create_pylint_issue(self, issue_data: Dict[str, Any], severity_map: Dict[str, str]) -> Optional[BackendSecurityIssue]:
        """Create a BackendSecurityIssue from Pylint issue data."""
        relative_filename = self._make_relative_path(
            issue_data["path"], self.base_path
        )

        return BackendSecurityIssue(
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
        )

    def _run_pylint(self, app_path: Path) -> ToolResult:
        """
        Run Pylint analysis on the application code.

        Args:
            app_path: Path to the application backend

        Returns:
            ToolResult with Pylint analysis results
        """
        if not self._check_tool_availability(TOOL_PYLINT):
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

        # Convert to relative paths for Pylint
        relative_source_files = []
        for f in source_files:
            try:
                rel_path = str(Path(f).relative_to(app_path))
                relative_source_files.append(rel_path)
            except ValueError:
                logger.warning(f"Path '{f}' cannot be made relative to '{app_path}'")
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
                    issue = self._create_vulture_issue(match.groups())
                    if issue:
                        issues.append(issue)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error processing Vulture line '{line}': {e}")
            else:
                logger.debug(f"Could not parse Vulture line: {line}")

        return issues

    def _create_vulture_issue(self, match_groups: Tuple[str, ...]) -> Optional[BackendSecurityIssue]:
        """Create a BackendSecurityIssue from Vulture output match."""
        file_path, line_num_str, desc, conf_str = match_groups
        line_num = int(line_num_str)
        confidence_val = int(conf_str)

        # Map confidence percentage to levels
        if confidence_val >= 80:
            confidence = "HIGH"
        elif confidence_val >= 50:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        relative_filename = self._make_relative_path(file_path, self.base_path)
        
        return BackendSecurityIssue(
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
        )

    def _run_vulture(self, app_path: Path) -> ToolResult:
        """
        Run Vulture to find unused code in the application.

        Args:
            app_path: Path to the application backend

        Returns:
            ToolResult with Vulture analysis results
        """
        if not self._check_tool_availability(TOOL_VULTURE):
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
        use_all_tools: bool = False,
        force_rerun: bool = False
    ) -> Tuple[List[BackendSecurityIssue], Dict[str, str], Dict[str, str]]:
        """
        Run security analysis on a specific model and app number.
        Results are cached for full scans unless force_rerun is True.

        Args:
            model: Model name
            app_num: App number
            use_all_tools: Whether to use all available tools
            force_rerun: If True, ignore cached results and rerun all tools

        Returns:
            Tuple of (issues, tool_status, tool_outputs)

        Raises:
            ValueError: If the application path doesn't exist or required files aren't found
        """
        with self.analysis_lock:
            logger.info(f"Starting backend security analysis for {model}/app{app_num}")
            
            # Check cache for full scans
            results_filename = ".backend_security_results.json"
            if use_all_tools and not force_rerun:
                cached_results = self._load_cached_results(model, app_num, results_filename)
                if cached_results:
                    return cached_results

            # Find application path
            app_path = self._find_application_path(model, app_num)
            if not app_path:
                raise ValueError(f"Application backend path not found for {model}/app{app_num}")

            # Validate path exists
            if not app_path.is_dir():
                raise ValueError(f"Application backend path does not exist: {app_path}")

            # Run analysis
            return self._execute_analysis(app_path, model, app_num, use_all_tools, results_filename)

    def _load_cached_results(self, model: str, app_num: int, filename: str) -> Optional[Tuple[List[BackendSecurityIssue], Dict[str, str], Dict[str, str]]]:
        """Load cached analysis results if available."""
        cached_data = self.results_manager.load_results(model, app_num, file_name=filename)
        if cached_data and isinstance(cached_data, dict):
            issues_data = cached_data.get("issues", [])
            tool_status = cached_data.get("tool_status", {})
            tool_outputs = cached_data.get("tool_outputs", {})
            issues = [BackendSecurityIssue.from_dict(item) for item in issues_data]
            logger.info(f"Using cached results for {model}/app{app_num}")
            return issues, tool_status, tool_outputs
        return None

    def _execute_analysis(self, app_path: Path, model: str, app_num: int, 
                         use_all_tools: bool, results_filename: str) -> Tuple[List[BackendSecurityIssue], Dict[str, str], Dict[str, str]]:
        """Execute the security analysis on the given path."""
        has_files, _ = self._check_source_files(app_path)
        tools_to_run = self.all_tools if use_all_tools else self.default_tools

        # Check if Python files are required
        requires_py_files = any(tool for tool in tools_to_run if tool != TOOL_SAFETY)
        if requires_py_files and not has_files:
            raise ValueError(
                f"No Python source files found in {app_path}, "
                f"cannot run tools like {', '.join(t for t in tools_to_run if t != TOOL_SAFETY)}."
            )

        if not has_files:
            logger.warning(f"No Python source files in {app_path}, only running Safety if selected.")

        # Run tools
        all_issues, tool_status, tool_outputs = self._run_tools(app_path, tools_to_run, has_files)

        # Sort issues
        sorted_issues = self._sort_issues(all_issues)

        # Save results for full scans
        if use_all_tools:
            self._save_results(model, app_num, sorted_issues, tool_status, tool_outputs, results_filename)

        logger.info(f"Backend analysis complete. Total issues: {len(sorted_issues)}")
        return sorted_issues, tool_status, tool_outputs

    def _run_tools(self, app_path: Path, tools_to_run: Set[str], has_files: bool) -> Tuple[List[BackendSecurityIssue], Dict[str, str], Dict[str, str]]:
        """Run the specified security tools."""
        all_issues: List[BackendSecurityIssue] = []
        tool_status: Dict[str, str] = {}
        tool_outputs: Dict[str, str] = {}

        logger.info(f"Running tools: {', '.join(tools_to_run)}")

        max_workers = min(len(tools_to_run), os.cpu_count() or 4)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_tool = {}

            for tool in tools_to_run:
                if tool != TOOL_SAFETY and not has_files:
                    tool_status[tool] = STATUS_SKIPPED_NO_FILES
                    tool_outputs[tool] = "No Python files to analyze"
                    continue

                if tool not in self.tool_configs:
                    tool_status[tool] = STATUS_NOT_CONFIGURED
                    tool_outputs[tool] = "Tool not configured"
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

        # Fill in status for tools not run
        for tool in self.all_tools:
            if tool not in tool_status:
                tool_status[tool] = STATUS_SKIPPED_REASON.format(reason="not selected")
                tool_outputs[tool] = "Tool was not selected for this run"

        return all_issues, tool_status, tool_outputs

    def _sort_issues(self, issues: List[BackendSecurityIssue]) -> List[BackendSecurityIssue]:
        """Sort issues by severity, confidence, filename, and line number."""
        return sorted(
            issues,
            key=lambda issue: (
                SEVERITY_ORDER.get(issue.severity, DEFAULT_SEVERITY_LEVEL),
                CONFIDENCE_ORDER.get(issue.confidence, DEFAULT_SEVERITY_LEVEL),
                issue.filename,
                issue.line_number
            )
        )

    def _save_results(self, model: str, app_num: int, issues: List[BackendSecurityIssue],
                     tool_status: Dict[str, str], tool_outputs: Dict[str, str], filename: str):
        """Save analysis results to file."""
        results_to_save = {
            "issues": [issue.to_dict() for issue in issues],
            "tool_status": tool_status,
            "tool_outputs": tool_outputs,
            "analysis_timestamp": datetime.now().isoformat()
        }
        self.results_manager.save_results(model, app_num, results_to_save, file_name=filename)
        logger.info(f"Saved backend security analysis results for {model}/app{app_num}")

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
            severity = issue.severity
            confidence = issue.confidence
            
            summary["severity_counts"][severity] = summary["severity_counts"].get(severity, 0) + 1
            summary["confidence_counts"][confidence] = summary["confidence_counts"].get(confidence, 0) + 1
            summary["issue_types"][issue.issue_type] = summary["issue_types"].get(issue.issue_type, 0) + 1
            summary["tool_counts"][issue.tool] = summary["tool_counts"].get(issue.tool, 0) + 1

        return summary

    def analyze_single_file(self, file_path: Path) -> Tuple[List[BackendSecurityIssue], Dict[str, str], Dict[str, str]]:
        """
        Run security analysis on a single Python file using Bandit.

        Args:
            file_path: Path to the Python file

        Returns:
            Tuple of (issues, tool_status, tool_outputs)
            
        Raises:
            ValueError: If the file is invalid or not a Python file
        """
        with self.analysis_lock:
            file_path = Path(file_path)
            logger.info(f"Starting single-file backend security analysis for: {file_path}")

            # Validate file
            if not file_path.exists() or not file_path.is_file():
                raise ValueError(f"File does not exist: {file_path}")
            
            if file_path.suffix != '.py':
                raise ValueError(f"Not a Python file: {file_path}")

            # Security check
            if not validate_path_security(self.base_path, file_path):
                raise ValueError(f"Security violation: {file_path} is outside allowed paths")

            return self._analyze_single_file_with_bandit(file_path)

    def _analyze_single_file_with_bandit(self, file_path: Path) -> Tuple[List[BackendSecurityIssue], Dict[str, str], Dict[str, str]]:
        """Run Bandit on a single file."""
        all_issues: List[BackendSecurityIssue] = []
        tool_status: Dict[str, str] = {}
        tool_outputs: Dict[str, str] = {}

        # Only run Bandit for single file analysis
        tool = TOOL_BANDIT
        if not self._check_tool_availability(tool):
            tool_status[tool] = STATUS_COMMAND_NOT_FOUND
            tool_outputs[tool] = "Bandit tool not found in the system"
        else:
            try:
                command = [sys.executable, "-m", "bandit", str(file_path), "-f", "json", "-ll", "-ii"]
                working_dir = file_path.parent
                result = self._run_tool(tool, command, self._parse_bandit_output, working_directory=working_dir)

                all_issues.extend(result.issues)
                tool_outputs[tool] = result.output
                tool_status[tool] = result.status
            except Exception as e:
                logger.exception(f"Error running {tool} on {file_path}: {e}")
                tool_status[tool] = f"{STATUS_ERROR}: {str(e)}"
                tool_outputs[tool] = f"Error running tool: {str(e)}"

        # Mark other tools as not run
        for t in self.all_tools:
            if t not in tool_status:
                tool_status[t] = STATUS_SKIPPED_REASON.format(reason="single file analysis")
                tool_outputs[t] = "Not applicable for single file analysis"

        sorted_issues = self._sort_issues(all_issues)
        logger.info(f"Single-file analysis complete. Total issues: {len(sorted_issues)}")
        return sorted_issues, tool_status, tool_outputs