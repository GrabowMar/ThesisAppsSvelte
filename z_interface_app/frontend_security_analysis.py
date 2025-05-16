import os
import json
import shutil
import subprocess
import logging
import concurrent.futures
import platform
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
import tempfile
from typing import List, Optional, Tuple, Dict, Any, Union, Callable, Generator, Set, TypedDict
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from enum import Enum
from threading import Lock # Added Lock

# Attempt to import JsonResultsManager from utils.py
try:
    from utils import JsonResultsManager #
except ImportError:
    # Fallback if utils.py is not in the same directory or path
    class JsonResultsManager:
        def __init__(self, base_path: Path, module_name: str):
            self.base_path = base_path
            self.module_name = module_name
            print(f"Warning: JsonResultsManager initialized without a proper logger for {module_name}")

        def save_results(self, model: str, app_num: int, results: Any, file_name: str = ".frontend_security_results.json", **kwargs) -> Path:
            results_dir = self.base_path / "results" / model / f"app{app_num}"
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
            except Exception as e:
                print(f"Error: [{self.module_name}] Error saving results to {results_path}: {e}")
                raise
            return results_path

        def load_results(self, model: str, app_num: int, file_name: str = ".frontend_security_results.json", **kwargs) -> Optional[Any]:
            results_path = self.base_path / "results" / model / f"app{app_num}" / file_name
            if not results_path.exists():
                print(f"Warning: [{self.module_name}] Results file not found: {results_path}")
                return None
            try:
                with open(results_path, "r", encoding='utf-8') as f:
                    data = json.load(f)
                print(f"Info: [{self.module_name}] Loaded results from {results_path}")
                return data
            except Exception as e:
                print(f"Error: [{self.module_name}] Error loading results from {results_path}: {e}")
                return None

logger = logging.getLogger(__name__)

# Constants
TOOL_TIMEOUT = 45 #
IS_WINDOWS = platform.system() == "Windows" #
SEVERITY_MAP = { #
    "critical": "HIGH", #
    "high": "HIGH", #
    "moderate": "MEDIUM", #
    "medium": "MEDIUM", #
    "low": "LOW", #
    "info": "LOW" #
}
SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2} #
CONFIDENCE_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2} #
DEFAULT_ORDER_VALUE = 99 #


class ToolStatus(str, Enum): #
    """Status codes for tool execution results."""
    SUCCESS = "✅ No issues found" #
    ISSUES_FOUND = "⚠️ Found {count} issues" #
    ISSUES_WITH_ERRORS = "⚠️ Found {count} issues (Errors reported)" #
    ERROR = "❌ Error Reported" #
    AUTH_REQUIRED = "❌ Authentication required" #
    COMMAND_NOT_FOUND = "❌ {tool} command not found" #
    NO_FILES = "❌ No files to analyze" #
    SKIPPED = "⚪ Skipped" #
    NOT_RUN = "⚠️ Not run" #
    UNKNOWN = "❓ Unknown State" #


class ToolConfig(TypedDict, total=False): #
    """Configuration for tool execution."""
    max_files: int #
    timeout: int #
    file_extensions: List[str] #


def get_executable_path(name: str) -> Optional[str]: #
    """Find the executable path for a command."""
    cmd = f"{name}.cmd" if IS_WINDOWS else name #
    path = shutil.which(cmd) #
    if path: #
        logger.debug(f"Found executable for '{name}' at: {path}") #
        return path #
    else: #
        if IS_WINDOWS: #
            path = shutil.which(name) #
            if path: #
                logger.debug(f"Found executable for '{name}' (no .cmd) at: {path}") #
                return path #
        logger.warning(f"Executable '{cmd}' (or '{name}') not found in PATH.") #
        return None #


def safe_json_loads(data: str) -> Optional[Union[dict, list]]: #
    """Safely parse JSON data, handling potential issues."""
    try:
        if data and data.startswith('\ufeff'): #
            data = data.lstrip('\ufeff') #
        if not data: #
            return None #
        return json.loads(data) #
    except json.JSONDecodeError as exc: #
        logger.error(f"Failed to parse JSON: {exc}") #
        logger.debug(f"Raw JSON output snippet causing error: {data[:300]}...") #
        return None #
    except Exception as e: #
        logger.error(f"Unexpected error during JSON parsing: {e}") #
        return None #


def normalize_path(path: Union[str, Path]) -> Path: #
    """Normalize a path to an absolute path."""
    return Path(path).resolve() #


@dataclass
class SecurityIssue: #
    """Represents a security issue found in frontend code."""
    filename: str #
    line_number: int #
    issue_text: str #
    severity: str #
    confidence: str #
    issue_type: str #
    line_range: List[int] #
    code: str #
    tool: str #
    fix_suggestion: Optional[str] = None #

    def to_dict(self) -> Dict[str, Any]: #
        """Convert to dictionary representation."""
        return asdict(self) #

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecurityIssue': #
        return cls(**data) #


class FrontendSecurityAnalyzer: #
    """Analyzes frontend code for security issues using various tools."""

    def __init__(self, base_path: Union[str, Path]): #
        """Initialize the analyzer with the base path for scans."""
        self.base_path = normalize_path(base_path) #
        logger.info(f"Initialized FrontendSecurityAnalyzer with base path: {self.base_path}") #
        self.results_manager = JsonResultsManager(base_path=self.base_path, module_name="frontend_security") #
        self.analysis_lock = Lock() # Added Lock #

        self.default_tools = ["eslint"] #
        self.all_tools = ["npm-audit", "eslint", "jshint", "snyk"] #

        # Default tool configurations
        self.tool_configs: Dict[str, ToolConfig] = { #
            "jshint": {"max_files": 30}, #
            "eslint": {"timeout": TOOL_TIMEOUT}, #
            "npm-audit": {"timeout": TOOL_TIMEOUT}, #
            "snyk": {"timeout": 90} #
        }

        # Check which tools are available
        self.available_tools = { #
            "npm-audit": bool(get_executable_path("npm")), #
            "eslint": bool(get_executable_path("npx")), # npx is used to run eslint/jshint #
            "jshint": bool(get_executable_path("npx")), #
            "snyk": bool(get_executable_path("snyk")) #
        }
        logger.info(f"Available tools check: {self.available_tools}") #

    @contextmanager
    def _create_temp_config(self, prefix: str, config_content: dict, filename: str) -> Generator[Path, None, None]: #
        """Create a temporary configuration file for a tool."""
        temp_dir = None #
        try:
            temp_dir = Path(tempfile.mkdtemp(prefix=prefix)) #
            config_path = temp_dir / filename #

            with open(config_path, "w") as f: #
                json.dump(config_content, f, indent=2) #

            logger.info(f"Created temporary configuration at {config_path}") #
            yield config_path #

        finally:
            if temp_dir and temp_dir.exists(): #
                try:
                    shutil.rmtree(temp_dir) #
                    logger.debug(f"Cleaned up temporary directory: {temp_dir}") #
                except Exception as e: #
                    logger.warning(f"Failed to remove temporary directory: {e}") #

    def _determine_tool_status(self, tool_name: str, issues: List[SecurityIssue], output: str) -> str: #
        """Determine the status of a tool execution based on output and issues found."""
        output_lower = output.lower() #

        if "authenticate" in output_lower or "auth token" in output_lower: #
            return ToolStatus.AUTH_REQUIRED.value #

        if "error" in output_lower or "failed" in output_lower: #
            if not issues and "found 0 vulnerabilities" not in output_lower: # Snyk says "found 0 vulnerabilities" on success #
                return ToolStatus.ERROR.value #
            else: #
                return ToolStatus.ISSUES_WITH_ERRORS.value.format(count=len(issues)) #


        if issues: #
            return ToolStatus.ISSUES_FOUND.value.format(count=len(issues)) #

        return ToolStatus.SUCCESS.value #

    def _find_application_path(self, model: str, app_num: int) -> Optional[Path]: #
        """Find the application directory path for a specific model and app number."""
        logger.debug(f"Finding application path for {model}/app{app_num}") #
        # Prioritize `models` subdirectory at the same level as the script's parent (workspace root)
        workspace_root = self.base_path.parent #
        base_app_dir = workspace_root / "models" / model / f"app{app_num}" #


        if not base_app_dir.is_dir(): #
            # Fallback to base_path if the above doesn't exist (e.g. if base_path is already workspace_root)
            base_app_dir = self.base_path / "models" / model / f"app{app_num}" #
            if not base_app_dir.is_dir(): #
                logger.error(f"Base application directory not found at either preferred or fallback location: {base_app_dir}") #
                return None #


        candidates_rel = ["frontend", "client", "web", "."] # "." means base_app_dir itself #

        for rel_dir in candidates_rel: #
            candidate = (base_app_dir / rel_dir).resolve() #
            if candidate.is_dir(): #
                # Check for common frontend markers
                if (candidate / "package.json").exists() or \
                   any((candidate / f).exists() for f in ["vite.config.js", "webpack.config.js", "angular.json", "svelte.config.js", "next.config.js"]): #
                    logger.info(f"Identified frontend application directory: {candidate}") #
                    return candidate #

        logger.warning(f"Could not reliably identify a specific frontend subdirectory within {base_app_dir}. " #
                       f"Proceeding with analysis on {base_app_dir} itself, but results may vary.") #
        return base_app_dir #


    def _check_source_files(self, directory: Path, file_exts: Optional[Tuple[str, ...]] = None) -> Tuple[bool, List[str]]: #
        """Check for frontend source files in the given directory."""
        if not directory.is_dir(): #
            logger.warning(f"Directory does not exist or is not a directory: {directory}") #
            return False, [] #

        exts = file_exts or (".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".html", ".css") #
        excluded_dirs = {"node_modules", ".git", "dist", "build", "coverage", "vendor", "bower_components"} #
        found_files: List[str] = [] #

        try:
            for root, dirs, files in os.walk(directory, topdown=True): #
                # Modify dirs in-place to skip excluded directories
                dirs[:] = [d for d in dirs if d not in excluded_dirs] #

                for file in files: #
                    if file.endswith(exts): #
                        found_files.append(os.path.join(root, file)) #

            count = len(found_files) #
            logger.info(f"Found {count} frontend source files in {directory}") #
            return count > 0, found_files #
        except Exception as e: #
            logger.error(f"Error checking source files in {directory}: {e}") #
            return False, [] #


    def _run_frontend_tool( #
        self,
        tool_name: str, #
        base_command: str, # e.g., "npm", "npx", "snyk" #
        args: List[str], #
        working_directory: Path, #
        parser: Optional[Callable[[str], List[SecurityIssue]]] = None, #
        input_data: Optional[str] = None, #
        timeout: int = TOOL_TIMEOUT #
    ) -> Tuple[List[SecurityIssue], str]: # Returns issues and raw_output #
        """Run a frontend security analysis tool and parse its output."""
        issues: List[SecurityIssue] = [] #
        raw_output = f"{tool_name} execution failed." #

        executable_path = get_executable_path(base_command) #
        if not executable_path: #
            raw_output = f"{tool_name} command ('{base_command}') not found in PATH." #
            logger.error(raw_output) #
            return issues, raw_output #

        command = [executable_path] + args #
        logger.info(f"[{tool_name}] Attempting to run: {' '.join(command)} in '{working_directory}'") #

        try:
            proc = subprocess.run( #
                command, #
                cwd=str(working_directory), # Ensure cwd is a string #
                capture_output=True, #
                text=True, # Get output as string #
                timeout=timeout, #
                check=False, # Don't raise exception for non-zero exit codes #
                encoding='utf-8', # Specify encoding #
                errors='replace' # Handle encoding errors gracefully #
            )
            logger.info(f"[{tool_name}] Subprocess finished with return code: {proc.returncode}") #
            raw_output = f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}" #


            if proc.returncode != 0 and proc.stderr: #
                stderr_lower = proc.stderr.lower() #
                if "command not found" in stderr_lower or "not recognized" in stderr_lower: #
                    logger.error(f"{tool_name} execution failed: Command likely not found or inner command failed. Stderr: {proc.stderr}") #
                elif "authenticate" in stderr_lower or "auth token" in stderr_lower: #
                    logger.error(f"{tool_name} execution failed: Authentication required.") #
                    raw_output += "\nERROR_NOTE: Authentication required." #
                else: #
                    logger.warning(f"{tool_name} exited with code {proc.returncode}. Stderr: {proc.stderr}") #


            if parser and proc.stdout: #
                logger.debug(f"[{tool_name}] Attempting to parse stdout...") #
                try:
                    issues = parser(proc.stdout) #
                    logger.info(f"{tool_name} found {len(issues)} issues via parser.") #
                except Exception as e: #
                    logger.error(f"Failed to parse {tool_name} output: {e}\nOutput:\n{proc.stdout[:500]}...") #
                    raw_output += f"\nPARSING_ERROR: {str(e)}" #
            elif proc.stdout: # Log if there's output but no parser #
                logger.debug(f"[{tool_name}] No parser provided or stdout empty, skipping parsing.") #


        except subprocess.TimeoutExpired: #
            logger.error(f"{tool_name} timed out after {timeout} seconds.") #
            raw_output = f"{tool_name} timed out after {timeout} seconds." #
        except FileNotFoundError: # Should be caught by get_executable_path, but as a fallback #
            logger.error(f"{tool_name} executable '{executable_path}' not found during run (unexpected).") #
            raw_output = f"{tool_name} executable not found during run: {executable_path}" #
        except Exception as e: #
            logger.exception(f"An unexpected error occurred while running {tool_name}: {e}") #
            raw_output = f"Unexpected error running {tool_name}: {str(e)}" #

        return issues, raw_output #

    def _parse_npm_audit(self, stdout: str) -> List[SecurityIssue]: #
        """Parse npm audit JSON output into SecurityIssue objects."""
        issues: List[SecurityIssue] = [] #
        audit_data = safe_json_loads(stdout.strip()) #
        if not audit_data: #
            logger.warning("npm audit: Failed to parse JSON data or output was empty.") #
            return issues #

        vulnerabilities = {} #
        if isinstance(audit_data, dict): #
            # npm v6 format
            if "vulnerabilities" in audit_data: #
                vulnerabilities = audit_data["vulnerabilities"] #
            # npm v7+ format
            elif "advisories" in audit_data: # This is how npm v7+ structures it #
                vulnerabilities = audit_data["advisories"] #


        if not vulnerabilities: #
            logger.info("npm audit: No vulnerabilities found in JSON.") #
            return issues #


        for key, vuln_info in vulnerabilities.items(): #
            if not isinstance(vuln_info, dict): continue #

            severity_str = vuln_info.get("severity", "info") #
            name = vuln_info.get("name", vuln_info.get("module_name", key)) # module_name for npm v7+ #
            version = vuln_info.get("range", vuln_info.get("vulnerable_versions", "N/A")) #
            title = vuln_info.get("title", "N/A") #
            fix_text = vuln_info.get("recommendation", "Review advisory") #

            # Try to get a more specific title if nested
            if isinstance(vuln_info.get("via"), list) and vuln_info["via"]: #
                if isinstance(vuln_info["via"][0], dict): # Check if first item is a dict #
                    title = vuln_info["via"][0].get("title", title) #


            fix_available = vuln_info.get("fixAvailable", None) #
            if isinstance(fix_available, dict): # npm v7+ often has fixAvailable as an object #
                fix_ver = fix_available.get("version") #
                if fix_ver : fix_text = f"Update {name} to version {fix_ver}" #
            elif fix_available is False: #
                fix_text = "No simple fix available via `npm audit fix`" #
            elif fix_available is True: # npm v6 #
                 fix_text = "Fix available via `npm audit fix`" #


            severity = SEVERITY_MAP.get(severity_str, "LOW") #
            issues.append(SecurityIssue( #
                filename="package-lock.json", line_number=0, #
                issue_text=f"{title} (Package: {name}, Version(s): {version})", #
                severity=severity, confidence="HIGH", #
                issue_type=f"dependency_vuln_{name}", line_range=[0], #
                code=f"{name}@{version}", tool="npm-audit", fix_suggestion=fix_text #
            ))
        return issues #

    def _parse_eslint(self, stdout: str) -> List[SecurityIssue]: #
        """Parse ESLint JSON output into SecurityIssue objects."""
        issues: List[SecurityIssue] = [] #
        parsed = safe_json_loads(stdout.strip()) # safe_json_loads handles potential BOM #
        if not isinstance(parsed, list): #
            logger.warning(f"ESLint: Expected a list from JSON output, got {type(parsed)}. Cannot parse.") #
            return issues #

        security_patterns = ["security", "inject", "prototype", "csrf", "xss", "sanitize", "escape", "auth", "unsafe", "exploit", "vuln"] #
        for file_result in parsed: #
            if not isinstance(file_result, dict): continue #

            file_path = file_result.get("filePath", "unknown") #
            # Normalize path for consistency (eslint might give absolute paths)
            rel_path = os.path.normpath(file_path) # Keeps it relative if already relative #


            for msg in file_result.get("messages", []): #
                if not isinstance(msg, dict): continue #

                is_fatal = msg.get("fatal", False) #
                line_num = msg.get("line", 0) #
                severity_value = msg.get("severity", 1) # 0:off, 1:warn, 2:error #
                rule_id = msg.get("ruleId", "parsing_error" if is_fatal else "unknown_rule") #
                message = msg.get("message", "Unknown issue") #

                severity = "HIGH" if severity_value >= 2 or is_fatal else "MEDIUM" #
                confidence = "HIGH" if is_fatal else "MEDIUM" #
                issue_type = rule_id #


                # Boost severity if security-related keywords are present
                rule_id_str = str(rule_id).lower() if rule_id else "" #
                message_str = str(message).lower() #
                if any(pattern in rule_id_str or pattern in message_str for pattern in security_patterns): #
                    if severity != "HIGH": # Don't downgrade if already high #
                        severity = "HIGH" #


                issues.append(SecurityIssue( #
                    filename=rel_path, line_number=line_num, issue_text=f"[{rule_id}] {message}", #
                    severity=severity, confidence=confidence, issue_type=issue_type, #
                    line_range=[line_num], code=msg.get("source", "N/A"), # source might not always be present #
                    tool="eslint", fix_suggestion=msg.get("fix", {}).get("text") #
                ))
        return issues #

    def _parse_jshint(self, stdout: str) -> List[SecurityIssue]: #
        """Parse JSHint XML output into SecurityIssue objects."""
        issues: List[SecurityIssue] = [] #
        try:
            root = ET.fromstring(stdout.strip()) # XML output #
            security_keywords = ["eval", "function(", "settimeout", "setinterval", "innerhtml", "document.write", "prototype", "constructor", "unsafe"] #
            security_codes = ["W054", "W061"] # 'Function' constructor, 'eval' #


            for file_elem in root.findall("file"): #
                file_path = file_elem.get("name", "unknown") #
                rel_path = os.path.normpath(file_path) #

                for error in file_elem.findall("error"): #
                    line = int(error.get("line", 0)) #
                    message = error.get("message", "Unknown JSHint issue") #
                    source_code = error.get("code", "") # 'code' attribute is JSHint error code like W033 #

                    is_security = source_code in security_codes or \
                                  any(keyword.lower() in message.lower() for keyword in security_keywords) #


                    # Default severity/confidence
                    severity = "LOW"; confidence = "MEDIUM" #
                    issue_type = f"jshint_{source_code}" if source_code else "jshint_unknown" #


                    if source_code.startswith('E'): # JSHint Errors #
                        severity = "HIGH"; confidence = "HIGH" #
                    elif source_code.startswith('W'): # JSHint Warnings #
                        severity = "MEDIUM" #

                    if is_security: #
                        severity = "HIGH" # Elevate security-related warnings #
                        confidence = "HIGH" if source_code in security_codes else "MEDIUM" #
                        issue_type = f"jshint_security_{source_code}" if source_code else "jshint_security_concern" #


                    issues.append(SecurityIssue( #
                        filename=rel_path, line_number=line, issue_text=f"[{source_code}] {message}", #
                        severity=severity, confidence=confidence, issue_type=issue_type, #
                        line_range=[line], code="N/A (Check file)", tool="jshint", # JSHint XML doesn't provide the code line #
                        fix_suggestion="Review code." #
                    ))
        except ET.ParseError as e_xml: #
            logger.error(f"JSHint: Failed to parse XML output: {e_xml}") #
        except Exception as e_proc: # Catch other potential errors during processing #
            logger.error(f"JSHint: Error processing XML output: {e_proc}") #
        return issues #

    def _parse_snyk(self, stdout: str) -> List[SecurityIssue]: #
        """Parse Snyk JSON output into SecurityIssue objects."""
        issues: List[SecurityIssue] = [] #
        snyk_data = safe_json_loads(stdout.strip()) #
        if not snyk_data: #
            logger.warning("Snyk: Failed to parse JSON data or output was empty.") #
            return issues #

        vulnerabilities = [] #
        if isinstance(snyk_data, dict): # Single project scan #
            vulnerabilities = snyk_data.get("vulnerabilities", []) #
        elif isinstance(snyk_data, list): # Multi-project scan #
            for project in snyk_data: #
                if isinstance(project, dict): #
                    vulnerabilities.extend(project.get("vulnerabilities", [])) #


        if not vulnerabilities: #
            logger.info("Snyk: No vulnerabilities found in JSON.") #
            return issues #

        for vuln in vulnerabilities: #
            if not isinstance(vuln, dict): continue #

            severity = SEVERITY_MAP.get(vuln.get("severity", "low"), "LOW") #
            # 'from' is the dependency chain, first element is the direct dependency
            from_chain = vuln.get("from", ["unknown_dependency"]) #
            filename = from_chain[0] if from_chain else "dependency_tree" # Report against the direct dep #

            fix_suggestion = "Review Snyk report for remediation details." #
            if vuln.get("isUpgradable", False): #
                upgrade_path = vuln.get("upgradePath", []) # Path to upgrade direct dependency #
                if upgrade_path and isinstance(upgrade_path[0], str): # Ensure it's a string #
                    fix_suggestion = f"Upgrade direct dependency: {upgrade_path[0]}" #
            elif vuln.get("isPatchable", False): #
                fix_suggestion = "Patch available via `snyk wizard` or review Snyk report." #


            issues.append(SecurityIssue( #
                filename=filename, line_number=0, # Line number not applicable for dep vulns #
                issue_text=f"{vuln.get('title', 'N/A')} ({vuln.get('packageName', 'N/A')}@{vuln.get('version', 'N/A')}) - ID: {vuln.get('id', 'N/A')}", #
                severity=severity, confidence="HIGH", issue_type=f"snyk_vuln_{vuln.get('id', 'N/A')}", #
                line_range=[0], code=f"{vuln.get('packageName', 'N/A')}@{vuln.get('version', 'N/A')}", #
                tool="snyk", fix_suggestion=fix_suggestion #
            ))
        return issues #

    def _run_tool_with_setup( #
        self,
        tool_name: str, #
        app_path: Path, #
        setup_func: Callable[[Path], Tuple[List[str], Optional[Dict], Optional[str]]], #
        parser_func: Callable[[str], List[SecurityIssue]] #
    ) -> Tuple[List[SecurityIssue], Dict[str, str], str]: #
        """Generic method to run a tool with customized setup."""
        status = {tool_name: ToolStatus.NOT_RUN.value} #
        raw_output = "" #

        try:
            args, config_dict, input_data = setup_func(app_path) # config_dict is for runner, not tool config file #
            if not args: # Setup indicated tool should be skipped (e.g. no files) #
                # The status should have been set by setup_func if skipping
                # but ensure it's something if not.
                if "status" in config_dict: # type: ignore #
                    status[tool_name] = config_dict["status"] # type: ignore #
                else: #
                    status[tool_name] = ToolStatus.SKIPPED.value #
                raw_output = config_dict.get("output", "") if config_dict else "" # type: ignore #
                return [], status, raw_output #

            timeout = self.tool_configs.get(tool_name, {}).get("timeout", TOOL_TIMEOUT) #
            command = args[0] # e.g. "npm", "npx" #
            command_args = args[1:] #

            issues, tool_output = self._run_frontend_tool( #
                tool_name, command, command_args, app_path, #
                parser=parser_func, input_data=input_data, #
                timeout=timeout #
            )
            raw_output = tool_output #
            status[tool_name] = self._determine_tool_status(tool_name, issues, raw_output) #

        except Exception as exc: #
            status[tool_name] = f"❌ Failed: {exc}" #
            raw_output = f"{tool_name} runner failed: {exc}" #
            logger.exception(f"Error running {tool_name}: {exc}") #

        return issues, status, raw_output #


    def _setup_npm_audit(self, app_path: Path) -> Tuple[List[str], Optional[Dict], Optional[str]]: #
        package_json_path = app_path / "package.json" #
        package_lock_path = app_path / "package-lock.json" #

        if not package_json_path.exists(): #
            msg = f"No package.json found in {app_path}, skipping npm-audit." #
            logger.warning(msg) #
            return [], {"status": ToolStatus.NO_FILES.value, "output": msg }, None # type: ignore #

        raw_output = "" #
        # Attempt to generate package-lock.json if it doesn't exist
        if not package_lock_path.exists(): #
            logger.info(f"No package-lock.json found in {app_path}, generating one...") #
            # Use --package-lock-only to avoid modifying node_modules, --ignore-scripts for security
            init_args = ["npm", "install", "--package-lock-only", "--ignore-scripts", "--no-audit"] #
            _, init_output = self._run_frontend_tool( #
                "npm-install", "npm", init_args[1:], app_path, timeout=120 # Longer timeout for install #
            )
            raw_output = f"--- npm install --package-lock-only ---\n{init_output}\n--- End npm install ---\n\n" #
            if not package_lock_path.exists(): #
                logger.warning("Failed to generate package-lock.json. Audit may be inaccurate.") #
                raw_output += "WARNING: Failed to generate package-lock.json.\n" #


        return ["npm", "audit", "--json"], None, None #


    def _setup_eslint(self, app_path: Path) -> Tuple[List[str], Optional[Dict], Optional[str]]: #
        has_files, _ = self._check_source_files(app_path) # Uses default exts #
        if not has_files: #
            msg = f"No relevant frontend files found in {app_path}, skipping eslint." #
            logger.warning(msg) #
            return [], {"status": ToolStatus.NO_FILES.value, "output": msg}, None # type: ignore #

        scan_dir = "src" if (app_path / "src").is_dir() else "." # Prefer src if exists #
        logger.info(f"ESLint will scan '{scan_dir}' within {app_path}") #

        args = ["npx", "eslint", "--ext", ".js,.jsx,.ts,.tsx,.vue,.svelte", "--format", "json", "--quiet"] #

        # Check for project ESLint config
        project_config_exists = any((app_path / f).exists() for f in #
                                  [".eslintrc.js", ".eslintrc.json", ".eslintrc.yaml", ".eslintrc.yml", "eslint.config.js"]) #


        if project_config_exists: #
            logger.info(f"Using existing ESLint configuration found in {app_path}") #
            args.append(scan_dir) # Add scan_dir only when using existing config #
            return args, None, None #
        else: #
            logger.info("No project ESLint config found, a basic temporary config will be created.") #
            # Signal that a temp config is needed, pass scan_dir for context
            return args, {"needs_temp_config": True, "scan_dir": scan_dir}, None #


    def _setup_jshint(self, app_path: Path) -> Tuple[List[str], Optional[Dict], Optional[str]]: #
        has_files, source_files = self._check_source_files(app_path, file_exts=(".js", ".jsx")) #
        if not has_files: #
            msg = f"No JavaScript/JSX files found in {app_path}, skipping jshint." #
            logger.warning(msg) #
            return [], {"status": ToolStatus.NO_FILES.value, "output": msg}, None # type: ignore #

        js_files = [f for f in source_files if f.endswith(('.js', '.jsx'))] # Redundant check, but safe #
        if not js_files: # Should be caught by has_files #
            msg = f"No JavaScript/JSX files found in {app_path} after filtering, skipping jshint." #
            logger.warning(msg) #
            return [], {"status": ToolStatus.NO_FILES.value, "output": msg}, None # type: ignore #

        max_jshint_files = self.tool_configs.get("jshint", {}).get("max_files", 30) #
        files_to_scan_abs = js_files[:max_jshint_files] #
        # JSHint expects relative paths from its CWD (app_path)
        files_to_scan_rel = [os.path.relpath(f, str(app_path)) for f in files_to_scan_abs] #


        if len(js_files) > max_jshint_files: #
            logger.warning(f"JSHint analysis limited to the first {max_jshint_files} JS/JSX files found.") #

        args = ["npx", "jshint", "--reporter=checkstyle"] # XML reporter #

        project_jshintrc = app_path / ".jshintrc" #
        if project_jshintrc.exists(): #
            jshintrc_path_used = str(project_jshintrc) # Ensure it's a string for command line #
            logger.info(f"Using existing project JSHint config: {jshintrc_path_used}") #
            args.extend(["--config", jshintrc_path_used]) #
            args.extend(files_to_scan_rel) #
            return args, None, None #
        else: #
            logger.info("No project JSHint config found, a basic temporary config will be created.") #
            # Signal that a temp config is needed, pass files_to_scan for context
            return args, {"needs_temp_config": True, "files_to_scan": files_to_scan_rel}, None #


    def _setup_snyk(self, app_path: Path) -> Tuple[List[str], Optional[Dict], Optional[str]]: #
        if not (app_path / "package.json").exists(): #
            msg = f"No package.json found in {app_path}, skipping snyk." #
            logger.warning(msg) #
            return [], {"status": ToolStatus.NO_FILES.value, "output": msg}, None # type: ignore #

        return ["snyk", "test"], {"needs_temp_output": True}, None # Signal for temp output file #

    def _run_npm_audit(self, app_path: Path) -> Tuple[List[SecurityIssue], Dict[str, str], str]: #
        return self._run_tool_with_setup( #
            "npm-audit", app_path, self._setup_npm_audit, self._parse_npm_audit #
        )

    def _run_eslint(self, app_path: Path) -> Tuple[List[SecurityIssue], Dict[str, str], str]: #
        tool_name = "eslint" #
        status = {tool_name: ToolStatus.NOT_RUN.value} #
        raw_output = "" #
        issues: List[SecurityIssue] = [] #

        args, config_dict, _ = self._setup_eslint(app_path) #
        if not args: # Skipped by setup #
            return [], config_dict.get("status", status) , config_dict.get("output", raw_output) # type: ignore #


        if config_dict and config_dict.get("needs_temp_config"): #
            scan_dir = config_dict.get("scan_dir", ".") #
            eslint_config = { # Basic ESLint config #
                "root": True, "env": {"browser": True, "es2021": True, "node": True}, #
                "extends": ["eslint:recommended"], #
                "parserOptions": {"ecmaVersion": "latest", "sourceType": "module", "ecmaFeatures": {"jsx": True}}, #
                "rules": {"no-eval": "error", "no-implied-eval": "error", "no-alert": "warn"} #
            }
            try:
                with self._create_temp_config("eslint_config_", eslint_config, ".eslintrc.json") as temp_config_path: #
                    complete_args = args + ["--config", str(temp_config_path), scan_dir] #
                    issues, run_output = self._run_frontend_tool( #
                        tool_name, complete_args[0], complete_args[1:], app_path, parser=self._parse_eslint #
                    )
                    raw_output = run_output #
            except Exception as exc: # Catch errors during temp config creation or tool run #
                status[tool_name] = f"❌ Failed: {exc}" #
                raw_output = f"{tool_name} runner failed with temp config: {exc}" #
                logger.exception(f"Error running {tool_name} with temp config: {exc}") #
                return issues, status, raw_output #
        else: # Use existing project config #
            issues, run_output = self._run_frontend_tool( #
                tool_name, args[0], args[1:], app_path, parser=self._parse_eslint #
            )
            raw_output = run_output #

        status[tool_name] = self._determine_tool_status(tool_name, issues, raw_output) #
        # Check for common ESLint config/plugin errors not always caught by return code
        output_lower = raw_output.lower() #
        if "error" in output_lower and "plugin" in output_lower and "was conflicted" not in output_lower: #
            status[tool_name] = "❌ Plugin/Config Issue" #

        return issues, status, raw_output #


    def _run_jshint(self, app_path: Path) -> Tuple[List[SecurityIssue], Dict[str, str], str]: #
        tool_name = "jshint" #
        status = {tool_name: ToolStatus.NOT_RUN.value} #
        raw_output = "" #
        issues: List[SecurityIssue] = [] #

        args, config_dict, _ = self._setup_jshint(app_path) #
        if not args: # Skipped by setup #
            return [], config_dict.get("status", status), config_dict.get("output", raw_output) # type: ignore #

        if config_dict and config_dict.get("needs_temp_config"): #
            files_to_scan_rel = config_dict.get("files_to_scan", []) #
            if not files_to_scan_rel: # If setup determined no files, even if args were returned #
                 status[tool_name] = ToolStatus.NO_FILES.value #
                 return issues, status, "No JS/JSX files to scan after setup." #

            jshint_config = { # Basic JSHint config #
                "esversion": 9, "browser": True, "node": True, #
                "strict": "implied", "undef": True, "unused": "vars", #
                "evil": True, "-W054": True, "-W061": True, "maxerr": 100 #
            }
            try:
                with self._create_temp_config("jshint_config_", jshint_config, ".jshintrc") as temp_config_path: #
                    complete_args = args + ["--config", str(temp_config_path)] + files_to_scan_rel #
                    issues, run_output = self._run_frontend_tool( #
                        tool_name, complete_args[0], complete_args[1:], app_path, parser=self._parse_jshint #
                    )
                    raw_output = run_output #
            except Exception as exc: #
                status[tool_name] = f"❌ Failed: {exc}" #
                raw_output = f"{tool_name} runner failed with temp config: {exc}" #
                logger.exception(f"Error running {tool_name} with temp config: {exc}") #
                return issues, status, raw_output #
        else: # Use existing project config (args already includes files) #
            issues, run_output = self._run_frontend_tool( #
                tool_name, args[0], args[1:], app_path, parser=self._parse_jshint #
            )
            raw_output = run_output #

        status[tool_name] = self._determine_tool_status(tool_name, issues, raw_output) #
        return issues, status, raw_output #

    def _run_snyk(self, app_path: Path) -> Tuple[List[SecurityIssue], Dict[str, str], str]: #
        tool_name = "snyk" #
        status = {tool_name: ToolStatus.NOT_RUN.value} #
        raw_output = "" #
        issues: List[SecurityIssue] = [] #
        temp_json_file: Optional[Path] = None #

        args, config_dict, _ = self._setup_snyk(app_path) #
        if not args: # Skipped by setup #
            return [], config_dict.get("status", status), config_dict.get("output", raw_output) # type: ignore #

        try:
            # Snyk requires writing output to a file for JSON
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json", encoding='utf-8') as tmpfile: #
                temp_json_file = Path(tmpfile.name) #
            logger.debug(f"Snyk output will be written to temporary file: {temp_json_file}") #

            complete_args = args + [f"--json-file-output={str(temp_json_file)}"] # Ensure path is string #
            timeout = self.tool_configs.get("snyk", {}).get("timeout", 90) #

            _, run_output = self._run_frontend_tool( # Snyk writes JSON to file, not stdout for `snyk test` #
                tool_name, complete_args[0], complete_args[1:], app_path, timeout=timeout #
            )
            raw_output = run_output # Capture stdout/stderr from snyk CLI itself #

            # Parse from the temporary file
            if temp_json_file.exists() and temp_json_file.stat().st_size > 0: #
                logger.debug(f"Parsing Snyk JSON output file: {temp_json_file}") #
                try:
                    with open(temp_json_file, 'r', encoding='utf-8') as f_snyk: #
                        issues = self._parse_snyk(f_snyk.read()) #
                except Exception as e_read: # Catch errors reading/parsing the temp file #
                    logger.error(f"Failed to read or parse Snyk JSON output file {temp_json_file}: {e_read}") #
                    status[tool_name] = "❌ Error Reading Output File" #
                    return issues, status, raw_output # Return early with error #
            else: #
                logger.warning(f"Snyk JSON output file {temp_json_file} not found or empty.") #


            status[tool_name] = self._determine_tool_status(tool_name, issues, raw_output) #

        except Exception as exc: #
            status[tool_name] = f"❌ Failed: {exc}" #
            raw_output = f"{tool_name} runner failed: {exc}" #
            logger.exception(f"Error running {tool_name}: {exc}") #
        finally:
            if temp_json_file and temp_json_file.exists(): #
                try:
                    temp_json_file.unlink() #
                    logger.debug(f"Removed temporary Snyk file: {temp_json_file}") #
                except OSError as e_unlink: # Catch potential errors during unlink #
                    logger.warning(f"Failed to remove temporary Snyk output file: {e_unlink}") #

        return issues, status, raw_output #

    def _sort_issues(self, issues: List[SecurityIssue]) -> List[SecurityIssue]: #
        """Sort issues by severity, confidence, filename, and line number."""
        return sorted( #
            issues, #
            key=lambda i: ( #
                SEVERITY_ORDER.get(i.severity, DEFAULT_ORDER_VALUE), #
                CONFIDENCE_ORDER.get(i.confidence, DEFAULT_ORDER_VALUE), #
                i.filename, #
                i.line_number #
            )
        )

    def run_security_analysis( #
        self,
        model: str, #
        app_num: int, #
        use_all_tools: bool = False, #
        force_rerun: bool = False  # Added force_rerun #
    ) -> Tuple[List[SecurityIssue], Dict[str, str], Dict[str, str]]: #
        """
        Run security analysis on a specific model and app number.
        Results are cached for full scans unless force_rerun is True.

        Args:
            model: Model name
            app_num: App number
            use_all_tools: Whether to use all available tools (default: False)
            force_rerun: If True, ignore cached results and rerun all tools.

        Returns:
            Tuple of (issues, tool_status, tool_outputs)
        """
        with self.analysis_lock: # Ensure only one analysis runs at a time #
            target_desc = f"models/{model}/app{app_num}" #
            logger.info(f"Running frontend security analysis for {target_desc} (full scan: {use_all_tools}, force_rerun: {force_rerun})") #

            # Filename for full scans
            results_filename = ".frontend_security_results.json"

            # Try to load cached results if it's a full scan and not forcing a rerun
            if use_all_tools and not force_rerun: #
                cached_data = self.results_manager.load_results(model, app_num, file_name=results_filename) #
                if cached_data and isinstance(cached_data, dict): #
                    issues_data = cached_data.get("issues", []) #
                    tool_status = cached_data.get("tool_status", {}) #
                    tool_outputs = cached_data.get("tool_outputs", {}) #
                    # Reconstruct SecurityIssue objects
                    issues = [SecurityIssue.from_dict(item) for item in issues_data] #
                    logger.info(f"Loaded cached frontend security analysis results for {model}/app{app_num} from {results_filename}") #
                    return issues, tool_status, tool_outputs #

            app_path = self._find_application_path(model, app_num) #
            if not app_path: #
                msg = f"Application directory not found for {target_desc}" #
                logger.error(msg) #
                # Create a status dict indicating app path not found for all tools
                error_status = {t: "❌ App path not found" for t in (self.all_tools if use_all_tools else self.default_tools)} #
                return [], error_status, {t: msg for t in error_status} #


            tools_to_attempt = self.all_tools if use_all_tools else self.default_tools #
            runnable_tools = [t for t in tools_to_attempt if self.available_tools.get(t)] #

            if not runnable_tools: #
                msg = f"No runnable tools selected or available for {target_desc}." #
                logger.warning(msg) #
                final_status: Dict[str, str] = {} #
                for tool in self.all_tools: # Report status for all configured tools #
                    if tool not in tools_to_attempt: #
                        final_status[tool] = ToolStatus.SKIPPED.value #
                    elif not self.available_tools.get(tool): #
                        final_status[tool] = f"❌ {tool} Not Available" #
                    else: # Was attemptable but not runnable (should not happen if logic is correct) #
                        final_status[tool] = ToolStatus.UNKNOWN.value #
                return [], final_status, {t: msg for t in self.all_tools} #


            logger.info(f"Executing tools: {', '.join(runnable_tools)}") #

            tool_map = { #
                "npm-audit": self._run_npm_audit, #
                "eslint": self._run_eslint, #
                "jshint": self._run_jshint, #
                "snyk": self._run_snyk #
            }

            all_issues: List[SecurityIssue] = [] #
            tool_status: Dict[str, str] = {} #
            tool_outputs: Dict[str, str] = {} #

            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(runnable_tools), 4)) as executor: #
                future_to_tool = { #
                    executor.submit(tool_map[tool], app_path): tool #
                    for tool in runnable_tools if tool in tool_map # Ensure tool exists in map #
                }

                for future in concurrent.futures.as_completed(future_to_tool): #
                    tool_name = future_to_tool[future] #
                    try:
                        issues, status_dict, output = future.result() #
                        all_issues.extend(issues) #
                        tool_outputs[tool_name] = output #
                        tool_status.update(status_dict) # status_dict is like {tool_name: status_value} #
                        logger.info(f"Tool '{tool_name}' completed for {target_desc}. Status: {status_dict.get(tool_name, 'Unknown')}") #
                    except Exception as exc: #
                        error_msg = f"❌ Error running {tool_name}: {exc}" #
                        logger.exception(f"Failed to get result for {tool_name}: {exc}") #
                        tool_status[tool_name] = error_msg #
                        tool_outputs[tool_name] = str(exc) #


            for tool in self.all_tools: # Fill status for tools not run #
                if tool not in tool_status: #
                    if not self.available_tools.get(tool): #
                        tool_status[tool] = f"❌ {tool} Not available" #
                        tool_outputs[tool] = f"{tool} command not found or non-functional." #
                    elif tool not in runnable_tools: # Was available but not selected for this run type #
                        tool_status[tool] = ToolStatus.SKIPPED.value #
                        tool_outputs[tool] = f"{tool} was available but not selected for this run." #
                    else: # Should not happen if logic is correct #
                        tool_status[tool] = ToolStatus.UNKNOWN.value #
                        tool_outputs[tool] = "Tool status was not recorded." #

            sorted_issues = self._sort_issues(all_issues) #

            # Save results only if it was a full scan
            if use_all_tools:
                results_to_save = { #
                    "issues": [issue.to_dict() for issue in sorted_issues], #
                    "tool_status": tool_status, #
                    "tool_outputs": tool_outputs, # Consider truncating long outputs if needed #
                    "analysis_timestamp": datetime.now().isoformat() #
                }
                self.results_manager.save_results(model, app_num, results_to_save, file_name=results_filename) #
                logger.info(f"Saved frontend security analysis results for {model}/app{app_num} to {results_filename}") #
            else:
                logger.info(f"Results for non-full frontend scan of {model}/app{app_num} were not saved.")


            logger.info(f"Frontend security analysis for {target_desc} completed. Total issues found: {len(sorted_issues)}") #
            return sorted_issues, tool_status, tool_outputs #

    def analyze_security(self, model: str, app_num: int, use_all_tools: bool = False): #
        """Alias for run_security_analysis for backward compatibility."""
        return self.run_security_analysis(model, app_num, use_all_tools) #

    def get_analysis_summary(self, issues: List[SecurityIssue]) -> Dict[str, Any]: #
        """
        Generate a summary of the security analysis results.

        Args:
            issues: List of SecurityIssue objects

        Returns:
            Dictionary with summary information
        """
        summary = { #
            "total_issues": len(issues), #
            "severity_counts": {sev: 0 for sev in SEVERITY_ORDER}, #
            "confidence_counts": {conf: 0 for conf in CONFIDENCE_ORDER}, #
            "files_affected": len({issue.filename for issue in issues if issue.filename}), #
            "issue_types": {}, #
            "tool_counts": {}, #
            "scan_time": datetime.now().isoformat() #
        }

        if not issues: #
            return summary #

        for issue in issues: #
            summary["severity_counts"][issue.severity] = summary["severity_counts"].get(issue.severity, 0) + 1 #
            summary["confidence_counts"][issue.confidence] = summary["confidence_counts"].get(issue.confidence, 0) + 1 #
            summary["issue_types"][issue.issue_type] = summary["issue_types"].get(issue.issue_type, 0) + 1 #
            summary["tool_counts"][issue.tool] = summary["tool_counts"].get(issue.tool, 0) + 1 #

        return summary #

    def analyze_single_file(self, file_path: Path) -> Tuple[List[SecurityIssue], Dict[str, str], Dict[str, str]]: #
        """
        Run security analysis on a single frontend file using ESLint and JSHint.

        Args:
            file_path: Path to the frontend file.

        Returns:
            Tuple of (issues, tool_status, tool_outputs)
        """
        with self.analysis_lock: #
            logger.info(f"Starting single-file frontend security analysis for: {file_path}") #

            if not file_path.exists() or not file_path.is_file(): #
                raise ValueError(f"Invalid file provided: {file_path}") #

            all_issues: List[SecurityIssue] = [] #
            tool_status: Dict[str, str] = {} #
            tool_outputs: Dict[str, str] = {} #
            app_path = file_path.parent # Use file's directory as the app_path context #

            single_file_tools = [] #
            if file_path.suffix in ['.js', '.jsx', '.ts', '.tsx', '.vue', '.svelte']: #
                if self.available_tools.get("eslint"): #
                    single_file_tools.append("eslint") #
            if file_path.suffix in ['.js', '.jsx']: # JSHint primarily for JS/JSX #
                 if self.available_tools.get("jshint"): #
                    single_file_tools.append("jshint") #

            if not single_file_tools: #
                msg = f"No applicable tools for single file analysis of {file_path.name}" #
                logger.warning(msg) #
                for tool in ["eslint", "jshint"]: # Default tools we might try #
                    tool_status[tool] = ToolStatus.SKIPPED.value #
                    tool_outputs[tool] = msg #
                return [], tool_status, tool_outputs #


            tool_map = { #
                "eslint": self._run_eslint_single_file, #
                "jshint": self._run_jshint_single_file, #
            }

            for tool_name in single_file_tools: #
                if tool_name in tool_map: #
                    try:
                        issues, status_dict, output = tool_map[tool_name](app_path, file_path) # Pass specific file #
                        all_issues.extend(issues) #
                        tool_outputs[tool_name] = output #
                        tool_status.update(status_dict) #
                        logger.info(f"Tool '{tool_name}' completed for single file {file_path.name}. Status: {status_dict.get(tool_name, 'Unknown')}") #
                    except Exception as exc: #
                        error_msg = f"❌ Error running {tool_name} on {file_path.name}: {exc}" #
                        logger.exception(f"Failed to get result for {tool_name} on {file_path.name}: {exc}") #
                        tool_status[tool_name] = error_msg #
                        tool_outputs[tool_name] = str(exc) #

            # Fill in status for tools that weren't run
            for tool in self.all_tools: #
                if tool not in tool_status: #
                    tool_status[tool] = ToolStatus.SKIPPED.value #
                    tool_outputs[tool] = "Not applicable for single file analysis or this file type." #

            sorted_issues = self._sort_issues(all_issues) #
            logger.info(f"Single-file frontend analysis for {file_path.name} completed. Total issues: {len(sorted_issues)}") #
            return sorted_issues, tool_status, tool_outputs #

    def _run_eslint_single_file(self, app_path: Path, file_to_scan: Path) -> Tuple[List[SecurityIssue], Dict[str, str], str]: #
        tool_name = "eslint" #
        status = {tool_name: ToolStatus.NOT_RUN.value} #
        raw_output = "" #
        issues: List[SecurityIssue] = [] #

        rel_file_to_scan = os.path.relpath(file_to_scan, app_path) #

        args = ["npx", "eslint", "--ext", Path(rel_file_to_scan).suffix, "--format", "json", "--quiet", rel_file_to_scan] #

        project_config_exists = any((app_path / f).exists() for f in #
                                  [".eslintrc.js", ".eslintrc.json", ".eslintrc.yaml", ".eslintrc.yml", "eslint.config.js"]) #

        if project_config_exists: #
            logger.info(f"Using existing ESLint configuration from {app_path} for single file {rel_file_to_scan}") #
            # args already include the file
        else: #
            logger.info(f"No project ESLint config found for single file {rel_file_to_scan}, creating temporary config.") #
            eslint_config = { #
                "root": True, "env": {"browser": True, "es2021": True, "node": True}, #
                "extends": ["eslint:recommended"], #
                "parserOptions": {"ecmaVersion": "latest", "sourceType": "module", "ecmaFeatures": {"jsx": True}}, #
                "rules": {"no-eval": "error", "no-implied-eval": "error", "no-alert": "warn"} #
            }
            try:
                with self._create_temp_config("eslint_single_config_", eslint_config, ".eslintrc.json") as temp_config_path: #
                    args = ["npx", "eslint", "--config", str(temp_config_path), "--ext", Path(rel_file_to_scan).suffix, "--format", "json", "--quiet", rel_file_to_scan] #
            except Exception as exc: #
                status[tool_name] = f"❌ Failed creating temp config: {exc}" #
                raw_output = f"{tool_name} runner failed creating temp config: {exc}" #
                return issues, status, raw_output #

        issues, raw_output = self._run_frontend_tool(tool_name, args[0], args[1:], app_path, parser=self._parse_eslint) #
        status[tool_name] = self._determine_tool_status(tool_name, issues, raw_output) #
        return issues, status, raw_output #

    def _run_jshint_single_file(self, app_path: Path, file_to_scan: Path) -> Tuple[List[SecurityIssue], Dict[str, str], str]: #
        tool_name = "jshint" #
        status = {tool_name: ToolStatus.NOT_RUN.value} #
        raw_output = "" #
        issues: List[SecurityIssue] = [] #

        rel_file_to_scan = os.path.relpath(file_to_scan, app_path) #
        args = ["npx", "jshint", "--reporter=checkstyle", rel_file_to_scan] #

        project_jshintrc = app_path / ".jshintrc" #
        if project_jshintrc.exists(): #
            logger.info(f"Using existing project JSHint config from {app_path} for single file {rel_file_to_scan}") #
            args = ["npx", "jshint", "--config", str(project_jshintrc), "--reporter=checkstyle", rel_file_to_scan] #
        else: #
            logger.info(f"No project JSHint config found for single file {rel_file_to_scan}, creating temporary config.") #
            jshint_config = { #
                "esversion": 9, "browser": True, "node": True, #
                "strict": "implied", "undef": True, "unused": "vars", #
                "evil": True, "-W054": True, "-W061": True, "maxerr": 100 #
            }
            try:
                with self._create_temp_config("jshint_single_config_", jshint_config, ".jshintrc") as temp_config_path: #
                    args = ["npx", "jshint", "--config", str(temp_config_path), "--reporter=checkstyle", rel_file_to_scan] #
            except Exception as exc: #
                status[tool_name] = f"❌ Failed creating temp config: {exc}" #
                raw_output = f"{tool_name} runner failed creating temp config: {exc}" #
                return issues, status, raw_output #

        issues, raw_output = self._run_frontend_tool(tool_name, args[0], args[1:], app_path, parser=self._parse_jshint) #
        status[tool_name] = self._determine_tool_status(tool_name, issues, raw_output) #
        return issues, status, raw_output #