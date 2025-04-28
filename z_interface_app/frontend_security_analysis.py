"""
Frontend Security Analysis Module

Provides security scanning for frontend code using multiple tools:
- npm audit: Dependency vulnerability checks.
- ESLint: Code quality and potential React/Svelte/Vue security linting.
- JSHint: Code quality checks focusing on potential security risks.
- Snyk: Dependency vulnerability scanning.

Features path detection, concurrent execution, logging, and error handling.
"""

import os
import json
import shutil
import subprocess
import logging
import concurrent.futures
import platform
from dataclasses import dataclass, asdict # Use asdict for simpler to_dict
from datetime import datetime
from pathlib import Path
import tempfile
from typing import List, Optional, Tuple, Dict, Any, Union, Callable
import xml.etree.ElementTree as ET # Keep import within _run_jshint

# --- Logging Configuration ---
# Assume logger is configured elsewhere or replace with basicConfig if run standalone
logger = logging.getLogger(__name__)
# Example basic config if needed:
# logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

# --- Constants ---
TOOL_TIMEOUT = 45  # seconds for tool execution timeout
IS_WINDOWS = platform.system() == "Windows"
SEVERITY_MAP = {
    "critical": "HIGH",
    "high": "HIGH",
    "moderate": "MEDIUM",
    "medium": "MEDIUM",
    "low": "LOW",
    "info": "LOW"
}
# Define sorting orders at module level for accessibility
SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
CONFIDENCE_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
DEFAULT_ORDER_VALUE = 99 # For sorting unknowns

# --- Helper Functions ---

def cmd_name(name: str) -> str:
    """
    Return the proper command name for Windows if needed.
    Example: "npm" -> "npm.cmd" on Windows.
    """
    return f"{name}.cmd" if IS_WINDOWS else name

def safe_json_loads(data: str) -> Optional[Union[dict, list]]: # Allow list type
    """
    Safely parse JSON data, returning None on failure.
    Logs an error if parsing fails.
    """
    try:
        # Handle BOM if present
        if data and data.startswith('\ufeff'):
            data = data.lstrip('\ufeff')
        if not data: # Handle empty string case
             return None
        return json.loads(data)
    except json.JSONDecodeError as exc:
        logger.error(f"Failed to parse JSON: {exc}")
        # Log only a snippet to avoid huge logs
        logger.debug(f"Raw JSON output snippet causing error: {data[:300]}...")
        return None
    except Exception as e:
         logger.error(f"Unexpected error during JSON parsing: {e}")
         return None

def normalize_path(path: Union[str, Path]) -> Path:
    """
    Normalize a path string or Path object to ensure it's an absolute, resolved Path.
    """
    return Path(path).resolve()

# --- Data Classes ---

@dataclass
class SecurityIssue:
    """Represents a security issue found in code."""
    filename: str
    line_number: int
    issue_text: str
    severity: str # HIGH, MEDIUM, LOW
    confidence: str # HIGH, MEDIUM, LOW
    issue_type: str
    line_range: List[int]
    code: str
    tool: str
    fix_suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for serialization using dataclasses.asdict."""
        # asdict handles basic conversion; datetime/enum conversion needed if added
        return asdict(self)

# --- Main Analyzer Class ---

class FrontendSecurityAnalyzer:
    """
    Analyzes frontend code for security issues using npm-audit, ESLint, JSHint, and Snyk.
    """

    def __init__(self, base_path: Union[str, Path]): # Accept str or Path
        """
        Initialize the analyzer with the base path.

        Args:
            base_path: The root directory where model/app code resides.
        """
        self.base_path = normalize_path(base_path)
        logger.info(f"Initialized FrontendSecurityAnalyzer with base path: {self.base_path}")

        # Define default tools for quick scan vs. all tools implemented
        self.default_tools = ["eslint"]
        # Update to reflect implemented tools (jshint, not retire.js)
        self.all_tools = ["npm-audit", "eslint", "jshint", "snyk"]

        # Check availability of required tools
        self.available_tools = {
            "npm-audit": self._check_tool("npm"),
            "eslint": self._check_tool("npx"), # Assumes eslint is run via npx
            "jshint": self._check_tool("npx"), # Assumes jshint is run via npx
            "snyk": self._check_tool("snyk")
        }
        logger.info(f"Available tools check: {self.available_tools}")

    def _check_tool(self, cmd: str) -> bool:
        """
        Check if a command exists and is executable in the system PATH.

        Args:
            cmd: Base command name (e.g., "npm", "npx", "snyk").

        Returns:
            True if the command seems available, False otherwise.
        """
        tool_cmd = cmd_name(cmd)
        try:
            # Use a command that typically works for checking existence/version
            check_command = [tool_cmd, "--version"]
            # Special handling for npx check
            if cmd == "npx":
                 # Check if npx itself exists and can execute a basic command like 'eslint --version'
                 # This assumes eslint is likely installed if npx is used with it later
                 check_command = [tool_cmd, "eslint", "--version"]

            proc = subprocess.run(
                check_command,
                capture_output=True,
                timeout=10, # Generous timeout for version check
                text=True,
                encoding='utf-8', errors='ignore' # Be robust about output encoding
            )
            # Check return code AND common "not found" messages in stderr
            if proc.returncode != 0 and proc.stderr and \
               ("not found" in proc.stderr.lower() or "not recognized" in proc.stderr.lower()):
                logger.warning(f"Tool check failed for '{cmd}': Command likely not found.")
                return False
            # If return code is 0 OR the error wasn't 'not found', assume tool exists.
            # (Some tools might have non-zero exit for --version, or npx might show errors from the executed command)
            return True
        except (subprocess.SubprocessError, FileNotFoundError, OSError) as e:
            logger.warning(f"Tool check failed for '{cmd}' (using '{tool_cmd}'): {e}")
            return False

    def _find_application_path(self, model: str, app_num: int) -> Optional[Path]: # Return Optional Path
        """
        Attempt to locate the frontend application path. Checks several
        common paths in order of preference. Returns None if base app dir not found.

        Args:
            model: Model identifier (e.g., 'Llama', 'GPT4o')
            app_num: Application number (e.g., 1, 2, 3)

        Returns:
            Path to the frontend application directory, or None if the base app dir is missing.
        """
        logger.debug(f"Finding application path for {model}/app{app_num}")
        base_app_dir = self.base_path / model / f"app{app_num}"

        if not base_app_dir.is_dir():
            logger.error(f"Base application directory not found: {base_app_dir}")
            return None # Cannot proceed if the appN directory doesn't exist

        # Prioritized list of potential frontend directories relative to base_app_dir
        candidates_rel = ["frontend", "client", "web", "."] # "." represents base_app_dir itself

        for rel_dir in candidates_rel:
            candidate = (base_app_dir / rel_dir).resolve() # Resolve to handle "." correctly
            # Check if the directory exists and contains common frontend indicators
            if candidate.is_dir():
                 # Look for package.json or common framework/build config files
                if (candidate / "package.json").exists() or \
                   any((candidate / f).exists() for f in ["vite.config.js", "webpack.config.js", "angular.json", "svelte.config.js", "next.config.js"]):
                    logger.info(f"Identified frontend application directory: {candidate}")
                    return candidate

        # If no specific subdir found, return the base appN dir, but warn
        logger.warning(f"Could not reliably identify a specific frontend subdirectory within {base_app_dir}. "
                       f"Proceeding with analysis on {base_app_dir} itself, but results may vary.")
        return base_app_dir # Fallback to the base appN directory


    def _check_source_files(self, directory: Path) -> Tuple[bool, List[str]]:
        """
        Check if the directory contains any typical frontend source files, excluding common generated/vendor folders.

        Args:
            directory: Path to the directory to scan recursively.

        Returns:
            Tuple (bool indicating if files were found, list of found file paths).
        """
        if not directory.is_dir(): # Check if it's a directory before scanning
            logger.warning(f"Directory does not exist or is not a directory: {directory}")
            return False, []

        exts = (".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".html", ".css")
        # Use set for faster lookup
        excluded_dirs = {"node_modules", ".git", "dist", "build", "coverage", "vendor", "bower_components"}
        found_files: List[str] = []

        try:
            for root, dirs, files in os.walk(directory, topdown=True): # topdown=True allows modifying dirs
                # Efficiently exclude directories
                dirs[:] = [d for d in dirs if d not in excluded_dirs]

                for file in files:
                    if file.endswith(exts):
                        found_files.append(os.path.join(root, file))

            count = len(found_files)
            logger.info(f"Found {count} frontend source files in {directory}")
            return count > 0, found_files
        except Exception as e:
            logger.error(f"Error checking source files in {directory}: {e}")
            return False, []


    def _run_npm_audit(self, app_path: Path) -> Tuple[List[SecurityIssue], Dict[str, str], str]:
        """
        Run `npm audit --json` to check for dependency vulnerabilities.
        """
        tool_name = "npm-audit"
        issues: List[SecurityIssue] = []
        status = {tool_name: "⚠️ Not run"} # Default status
        raw_output = "" # Store combined output for context

        package_json_path = app_path / "package.json"
        package_lock_path = app_path / "package-lock.json"

        if not package_json_path.exists():
            msg = f"No package.json found in {app_path}, skipping {tool_name}."
            logger.warning(msg)
            status[tool_name] = "❌ No package.json"
            return issues, status, msg

        # Attempt to ensure package-lock.json exists for accurate audit
        if not package_lock_path.exists():
            logger.info(f"No package-lock.json found in {app_path}, attempting `npm i --package-lock-only`...")
            try:
                # Use --no-audit during install to prevent audit running twice
                init_cmd = [cmd_name("npm"), "install", "--package-lock-only", "--ignore-scripts", "--no-audit"]
                # Give more time for potential installations
                init_proc = subprocess.run(init_cmd, cwd=str(app_path), capture_output=True, text=True,
                                           timeout=120, check=False, encoding='utf-8', errors='replace')
                if init_proc.returncode != 0 or not package_lock_path.exists():
                     logger.warning(f"Failed to generate package-lock.json (exit code {init_proc.returncode}). Audit may be inaccurate. Stderr: {init_proc.stderr[:500]}")
                     # Do not return here; proceed with audit but be aware results might be partial
            except Exception as exc:
                logger.warning(f"Error generating package-lock.json: {exc}. Audit results may be incomplete.")
                # Proceed with audit

        # Now run npm audit
        command = [cmd_name("npm"), "audit", "--json"]
        logger.info(f"Running {tool_name} in {app_path}...")
        try:
            proc = subprocess.run(
                command, cwd=str(app_path), capture_output=True, text=True,
                timeout=TOOL_TIMEOUT, check=False, encoding='utf-8', errors='replace' # check=False because audit exits > 0 if vulns found
            )
            raw_output = f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}" # Combine outputs for context

            # npm audit exit codes: 0=no vulns, >0=vulns found or error. We need to parse JSON regardless.
            stdout_data = proc.stdout.strip()
            if not stdout_data and proc.returncode != 0:
                # Handle cases where there's an error *other* than finding vulnerabilities
                msg = f"{tool_name} exited with code {proc.returncode}. Stderr: {proc.stderr}"
                logger.error(msg)
                status[tool_name] = f"❌ Error (Code {proc.returncode})"
                return issues, status, raw_output

            # Handle empty stdout (might indicate success or weird state)
            if not stdout_data:
                 stderr_lower = proc.stderr.lower() if proc.stderr else ""
                 if "found 0 vulnerabilities" in stderr_lower:
                     status[tool_name] = "✅ No issues found"
                 else:
                     status[tool_name] = "❌ Empty Output / Error"
                     logger.warning(f"{tool_name} produced no stdout. Stderr: {proc.stderr}")
                 return issues, status, raw_output


            audit_data = safe_json_loads(stdout_data)
            if not audit_data:
                 # Check stdout/stderr text for clues if JSON parsing failed
                 summary_text = (proc.stdout + proc.stderr).lower()
                 if "found 0 vulnerabilities" in summary_text: status[tool_name] = "✅ No issues found (JSON parse failed)"
                 elif "vulnerabilities" in summary_text: status[tool_name] = "⚠️ Issues found (JSON parse failed)"
                 else: status[tool_name] = "❌ Invalid JSON output"
                 logger.error(f"{tool_name} output was not valid JSON. Output snippet: {stdout_data[:500]}")
                 return issues, status, raw_output

            # Process JSON data (handles different npm versions within the logic)
            vulnerabilities = {}
            if "vulnerabilities" in audit_data: vulnerabilities = audit_data["vulnerabilities"]
            elif "advisories" in audit_data: vulnerabilities = audit_data["advisories"]

            if not vulnerabilities:
                status[tool_name] = "✅ No issues found"
            else:
                 for key, vuln_info in vulnerabilities.items():
                     # Normalize data access
                     severity_str = vuln_info.get("severity", "info") # Default to lowest if missing
                     name = vuln_info.get("name", vuln_info.get("module_name", key)) # Use key as fallback name
                     version = vuln_info.get("range", vuln_info.get("vulnerable_versions", "N/A"))
                     title = vuln_info.get("title", "N/A")
                     fix_text = vuln_info.get("recommendation", "Review advisory") # Default fix text

                     # Try extracting better title/fix from nested structures if possible
                     if isinstance(vuln_info.get("via"), list) and vuln_info["via"]:
                         if isinstance(vuln_info["via"][0], dict):
                             title = vuln_info["via"][0].get("title", title)
                     if isinstance(vuln_info.get("fixAvailable"), dict):
                         fix_ver = vuln_info["fixAvailable"].get("version")
                         if fix_ver: fix_text = f"Update {name} to version {fix_ver}"
                     elif isinstance(vuln_info.get("fixAvailable"), bool) and vuln_info["fixAvailable"] is False:
                          fix_text = "No simple fix available via `npm audit fix`"
                     elif isinstance(vuln_info.get("fixAvailable"), bool) and vuln_info["fixAvailable"] is True:
                          fix_text = "Fix available via `npm audit fix`"


                     severity = SEVERITY_MAP.get(severity_str, "LOW") # Map to standard HIGH/MEDIUM/LOW
                     issues.append(SecurityIssue(
                         filename="package-lock.json", # Issue is in a dependency listed here
                         line_number=0, # Line number not applicable
                         issue_text=f"{title} (Package: {name}, Version(s): {version})",
                         severity=severity, confidence="HIGH", # Confidence is high for known vulns
                         issue_type=f"dependency_vuln_{name}", line_range=[0],
                         code=f"{name}@{version}", tool=tool_name, fix_suggestion=fix_text
                     ))
                 status[tool_name] = f"⚠️ Found {len(issues)} issues"

        except subprocess.TimeoutExpired:
            status[tool_name] = "❌ Timed out"
            raw_output = f"{tool_name} timed out"
        except Exception as exc:
            status[tool_name] = f"❌ Failed: {exc}"
            raw_output = f"{tool_name} execution failed: {exc}"
            logger.exception(f"Error running {tool_name}: {exc}")

        return issues, status, raw_output


    def _run_eslint(self, app_path: Path) -> Tuple[List[SecurityIssue], Dict[str, str], str]:
        """Run ESLint and parse JSON output."""
        tool_name = "eslint"
        issues: List[SecurityIssue] = []
        status = {tool_name: "⚠️ Not run"}
        temp_dir = None
        eslint_config_path = None # Track path to temporary config for deletion
        raw_output = ""

        has_files, _ = self._check_source_files(app_path)
        if not has_files:
            msg = f"No relevant frontend files found in {app_path}, skipping {tool_name}."
            status[tool_name] = "❌ No files to analyze"
            return issues, status, msg

        scan_dir = "src" if (app_path / "src").is_dir() else "."
        logger.info(f"ESLint will scan '{scan_dir}' within {app_path}")

        try:
            # Check for existing ESLint config files
            project_config_exists = any((app_path / f).exists() for f in
                                        [".eslintrc.js", ".eslintrc.json", ".eslintrc.yaml", ".eslintrc.yml", "eslint.config.js"])

            command = [cmd_name("npx"), "eslint", "--ext", ".js,.jsx,.ts,.tsx,.vue,.svelte", "--format", "json", "--quiet"]

            if project_config_exists:
                logger.info(f"Using existing ESLint configuration found in {app_path}")
                # No need to add --config if config is in project root
            else:
                # Create a temporary basic config if none exists
                logger.info("No project ESLint config found, creating temporary basic config.")
                temp_dir = Path(tempfile.mkdtemp(prefix="eslint_config_"))
                eslint_config_path = temp_dir / ".eslintrc.json"
                eslint_config = {
                    "root": True, # Prevent extending further up
                    "env": {"browser": True, "es2021": True, "node": True},
                    "extends": ["eslint:recommended"], # Basic recommended rules
                    "parserOptions": { "ecmaVersion": "latest", "sourceType": "module", "ecmaFeatures": {"jsx": True} },
                    "rules": { "no-eval": "error", "no-implied-eval": "error", "no-alert": "warn" } # Basic security/bad practice rules
                }
                with open(eslint_config_path, "w") as f: json.dump(eslint_config, f, indent=2)
                # Explicitly pass the temporary config path
                command.extend(["--config", str(eslint_config_path)])

            command.append(scan_dir) # Target directory/files

            logger.info(f"Running {tool_name} command: {' '.join(command)}")
            proc = subprocess.run(
                command, cwd=str(app_path), capture_output=True, text=True,
                timeout=TOOL_TIMEOUT, check=False, encoding='utf-8', errors='replace'
            )
            raw_output = f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"

            # ESLint exits 1 if linting errors are found, 0 if none, 2 if config/fatal error
            if proc.returncode == 2:
                 msg = f"ESLint configuration or fatal error (exit code 2). Stderr: {proc.stderr}"
                 logger.error(msg)
                 status[tool_name] = "❌ Config/Fatal Error"
                 return issues, status, raw_output
            elif proc.returncode != 0 and proc.returncode != 1: # Handle unexpected exit codes
                 msg = f"ESLint failed with unexpected exit code {proc.returncode}. Stderr: {proc.stderr}"
                 logger.error(msg)
                 status[tool_name] = f"❌ Error (Code {proc.returncode})"
                 return issues, status, raw_output

            # Process JSON output (present even if exit code is 1)
            parsed = safe_json_loads(proc.stdout.strip())
            if not isinstance(parsed, list):
                # Check if stderr indicates a known issue like missing plugins
                if proc.stderr and "plugin" in proc.stderr.lower() and "was conflicted" not in proc.stderr.lower():
                     status[tool_name] = "❌ Plugin/Config Issue"
                     logger.error(f"ESLint likely failed due to plugin/config issue: {proc.stderr}")
                elif proc.returncode == 0 and not parsed: # No output, no errors
                     status[tool_name] = "✅ No issues found"
                else:
                     status[tool_name] = "❌ Invalid JSON output"
                     logger.error(f"ESLint output was not a valid JSON list. Output: {proc.stdout[:500]}")
                return issues, status, raw_output

            security_patterns = ["security", "inject", "prototype", "csrf", "xss", "sanitize", "escape", "auth", "unsafe", "exploit", "vuln"]
            for file_result in parsed:
                file_path = file_result.get("filePath", "unknown")
                try: rel_path = os.path.relpath(file_path, str(app_path))
                except ValueError: rel_path = file_path

                for msg in file_result.get("messages", []):
                    is_fatal = msg.get("fatal", False)
                    line_num = msg.get("line", 0)
                    severity_value = msg.get("severity", 1) # 1=warn, 2=error
                    rule_id = msg.get("ruleId", "parsing_error" if is_fatal else "unknown_rule")
                    message = msg.get("message", "Unknown issue")

                    # Determine severity and type
                    severity = "HIGH" if severity_value >= 2 or is_fatal else "MEDIUM"
                    confidence = "HIGH" if is_fatal else "MEDIUM"
                    issue_type = rule_id

                    # Check for security keywords to potentially elevate severity
                    rule_id_str = str(rule_id).lower() if rule_id else ""
                    message_str = str(message).lower()
                    if any(pattern in rule_id_str or pattern in message_str for pattern in security_patterns):
                        if severity != "HIGH": severity = "HIGH" # Elevate potential security issues

                    issues.append(SecurityIssue(
                        filename=rel_path, line_number=line_num, issue_text=f"[{rule_id}] {message}",
                        severity=severity, confidence=confidence, issue_type=issue_type,
                        line_range=[line_num], code=msg.get("source", "N/A"), # ESLint JSON provides source line
                        tool=tool_name, fix_suggestion=msg.get("fix", {}).get("text")
                    ))

            status[tool_name] = f"⚠️ Found {len(issues)} issues" if issues else "✅ No issues found"

        except subprocess.TimeoutExpired:
            status[tool_name] = "❌ Timed out"
            raw_output = f"{tool_name} timed out"
        except Exception as exc:
            status[tool_name] = f"❌ Failed: {exc}"
            raw_output = f"{tool_name} failed: {exc}"
            logger.exception(f"Error running {tool_name}: {exc}")
        finally:
            # Clean up temporary config directory if it was created
            if eslint_config_path and temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"Failed to remove temporary ESLint config directory: {e}")

        return issues, status, raw_output


    def _run_jshint(self, app_path: Path) -> Tuple[List[SecurityIssue], Dict[str, str], str]:
        """
        Run JSHint using checkstyle reporter and parse XML output for security issues.
        Limits files scanned for performance.
        """
        tool_name = "jshint"
        issues: List[SecurityIssue] = []
        status = {tool_name: "⚠️ Not run"}
        temp_dir = None # Track temp dir for cleanup
        jshintrc_path_used = None # Track config path used for logging/cleanup
        temp_jshintrc_created = False
        raw_output = "" # Initialize raw_output

        has_files, source_files = self._check_source_files(app_path)
        if not has_files:
            msg = f"No frontend files found in {app_path}, skipping {tool_name}."
            status[tool_name] = "❌ No files to analyze"
            return issues, status, msg

        js_files = [f for f in source_files if f.endswith(('.js', '.jsx'))]
        if not js_files:
            msg = f"No JavaScript/JSX files found in {app_path}, skipping {tool_name}."
            status[tool_name] = "❌ No JS files to analyze"
            return issues, status, msg

        # Limit files passed to JSHint command line for performance/stability
        max_jshint_files = 30
        files_to_scan = js_files[:max_jshint_files]
        if len(js_files) > max_jshint_files:
             logger.warning(f"JSHint analysis limited to the first {max_jshint_files} JS/JSX files found.")

        try:
            # Use project's .jshintrc if it exists, otherwise create a temporary one
            project_jshintrc = app_path / ".jshintrc"
            if project_jshintrc.exists():
                 jshintrc_path_used = str(project_jshintrc)
                 logger.info(f"Using existing project JSHint config: {jshintrc_path_used}")
            else:
                temp_dir = Path(tempfile.mkdtemp(prefix="jshint_config_"))
                jshintrc_path_used = str(temp_dir / ".jshintrc")
                # Security-focused config (enable warnings for eval, Function constructor)
                jshint_config = {
                    "esversion": 9, "browser": True, "node": True,
                    "strict": "implied", "undef": True, "unused": "vars",
                    "evil": True, "-W054": True, "-W061": True, "maxerr": 100 # Limit total errors reported
                }
                with open(jshintrc_path_used, "w") as f: json.dump(jshint_config, f, indent=2)
                temp_jshintrc_created = True # Mark for cleanup
                logger.info(f"Created temporary JSHint config at {jshintrc_path_used}")

            command = [cmd_name("npx"), "jshint", "--reporter=checkstyle", "--config", jshintrc_path_used]
            command.extend(files_to_scan)

            logger.info(f"Running JSHint on {len(files_to_scan)} files...")
            proc = subprocess.run(
                command, cwd=str(app_path), capture_output=True, text=True,
                timeout=TOOL_TIMEOUT, check=False, encoding='utf-8', errors='replace'
            )
            raw_output = f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
            stdout_data = proc.stdout.strip()

            # *** Corrected Logic: Check output validity *before* checking exit code for fatal errors ***
            is_output_valid_xml = stdout_data and stdout_data.startswith("<?xml")

            if not is_output_valid_xml and proc.returncode != 0:
                # If output is NOT valid XML AND there was an error code -> True execution error
                msg = f"JSHint execution failed (exit code {proc.returncode}) with invalid/empty output. Stderr: {proc.stderr}"
                logger.error(msg)
                status[tool_name] = f"❌ Error (Code {proc.returncode})"
                return issues, status, raw_output
            elif not is_output_valid_xml and proc.returncode == 0:
                 # No output, no error code -> Likely no issues found or no files linted
                 status[tool_name] = "✅ No issues found"
                 logger.info(f"JSHint finished with no output and exit code 0.")
                 return issues, status, raw_output

            # --- If we reach here, output is likely valid XML, parse it ---
            logger.info(f"JSHint finished with exit code {proc.returncode}. Parsing XML output...")
            try:
                # import xml.etree.ElementTree as ET # Already imported at module level
                root = ET.fromstring(stdout_data)
                security_keywords = ["eval", "function(", "settimeout", "setinterval", "innerhtml", "document.write", "prototype", "constructor", "unsafe"]
                security_codes = ["W054", "W061"] # Specific JSHint codes

                for file_elem in root.findall("file"):
                    file_path = file_elem.get("name", "unknown")
                    try: rel_path = os.path.relpath(file_path, str(app_path))
                    except ValueError: rel_path = file_path

                    for error in file_elem.findall("error"): # JSHint checkstyle uses <error> tag for warnings too
                        line = int(error.get("line", 0))
                        message = error.get("message", "Unknown JSHint issue")
                        source_code = error.get("source", "") # e.g., jshint.W031

                        # Check if security related
                        # Corrected: use lower() for case-insensitive comparison
                        is_security = source_code in security_codes or \
                                      any(keyword.lower() in message.lower() for keyword in security_keywords)

                        # *** Fix: Process ALL errors/warnings, but classify severity ***
                        severity = "LOW" # Default assumption
                        confidence = "MEDIUM"
                        issue_type = f"jshint_{source_code}" if source_code else "jshint_unknown"

                        if source_code.startswith('E'): # JSHint Error codes
                            severity = "HIGH"
                            confidence = "HIGH"
                        elif source_code.startswith('W'): # JSHint Warning codes
                            severity = "MEDIUM"
                        # else severity remains LOW

                        if is_security: # Elevate severity if security-related
                            severity = "HIGH"
                            confidence = "HIGH" if source_code in security_codes else "MEDIUM"
                            issue_type = f"jshint_security_{source_code}" if source_code else "jshint_security_concern"


                        code_snippet = "N/A (Check file)" # JSHint XML doesn't provide snippet

                        issues.append(SecurityIssue(
                            filename=rel_path, line_number=line, issue_text=f"[{source_code}] {message}",
                            severity=severity, confidence=confidence, issue_type=issue_type,
                            line_range=[line], code=code_snippet, tool=tool_name,
                            fix_suggestion="Review code." # Generic suggestion
                        ))
                # *** Fix: Update status based on *any* issues found ***
                status[tool_name] = f"⚠️ Found {len(issues)} issues" if issues else "✅ No issues found"

            except ET.ParseError as e_xml:
                logger.error(f"Failed to parse JSHint XML output: {e_xml}")
                status[tool_name] = "❌ Invalid XML output"
            except Exception as e_proc:
                logger.error(f"Error processing JSHint output: {e_proc}")
                status[tool_name] = "❌ Error processing output"

        except subprocess.TimeoutExpired:
            status[tool_name] = "❌ Timed out"
            raw_output = "JSHint timed out"
        except Exception as exc:
            status[tool_name] = f"❌ Failed: {exc}"
            raw_output = f"JSHint failed: {exc}"
            logger.exception(f"Error running {tool_name}: {exc}")
        finally:
            # Clean up temporary directory/config if created
            if temp_jshintrc_created and temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                    logger.debug("Cleaned up temporary JSHint directory")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary JSHint directory: {e}")

        return issues, status, raw_output


    def _run_snyk(self, app_path: Path) -> Tuple[List[SecurityIssue], Dict[str, str], str]:
        """Run Snyk test and parse JSON output."""
        tool_name = "snyk"
        issues: List[SecurityIssue] = []
        status = {tool_name: "⚠️ Not run"}
        raw_output = "" # Store combined stdout/stderr for context
        temp_json_file = None # Path object for the temp file

        if not (app_path / "package.json").exists():
            msg = f"No package.json found in {app_path}, skipping {tool_name}."
            logger.warning(msg)
            status[tool_name] = "❌ No package.json"
            return issues, status, msg

        try:
            # Use temp file for reliable JSON output capture
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json", encoding='utf-8') as tmpfile:
                temp_json_file = Path(tmpfile.name)

            command = [cmd_name("snyk"), "test", f"--json-file-output={temp_json_file}"]
            logger.info(f"Running {tool_name} in {app_path}...")
            proc = subprocess.run(
                command, cwd=str(app_path), capture_output=True, text=True,
                timeout=90, check=False, encoding='utf-8', errors='replace' # Longer timeout
            )
            raw_output = f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"

            # Check for common errors before attempting to read JSON file
            combined_output = proc.stdout + proc.stderr
            if "authenticate" in combined_output.lower() or "auth token" in combined_output.lower():
                 msg = "Snyk authentication required. Run 'snyk auth'."
                 logger.error(msg)
                 status[tool_name] = "❌ Authentication required"
                 return issues, status, raw_output # Return early on auth failure

            snyk_data = None
            if temp_json_file.exists() and temp_json_file.stat().st_size > 0:
                 try:
                     with open(temp_json_file, 'r', encoding='utf-8') as f:
                          snyk_data = safe_json_loads(f.read())
                 except Exception as e_read:
                      logger.error(f"Failed to read Snyk JSON output file {temp_json_file}: {e_read}")

            # Determine status based on exit code, JSON content, and summary text
            vulnerabilities = []
            parse_error = False
            if isinstance(snyk_data, dict):
                vulnerabilities = snyk_data.get("vulnerabilities", [])
                if snyk_data.get("error"): # Check for error key in JSON
                     logger.error(f"Snyk reported error in JSON: {snyk_data['error']}")
                     status[tool_name] = "❌ Error Reported by Snyk"
                     # Don't return yet, might still have partial results
            elif isinstance(snyk_data, list): # Handle monorepo output
                 for project in snyk_data:
                     if isinstance(project, dict):
                          vulnerabilities.extend(project.get("vulnerabilities", []))
                          if project.get("error"):
                               logger.error(f"Snyk reported error in multi-project JSON: {project['error']}")
                               status[tool_name] = "❌ Error Reported by Snyk" # Mark error, but continue processing
            else: # JSON load failed or was unexpected type
                 parse_error = True
                 logger.error("Failed to parse Snyk JSON output or unexpected format.")


            if vulnerabilities:
                 status[tool_name] = f"⚠️ Found {len(vulnerabilities)} issues"
                 for vuln in vulnerabilities:
                     severity = SEVERITY_MAP.get(vuln.get("severity", "low"), "LOW")
                     from_chain = vuln.get("from", ["unknown_dependency"]) # Path from direct dep
                     filename = from_chain[0] if from_chain else "dependency_tree" # File is less relevant here

                     fix_suggestion = "Review Snyk report for remediation details."
                     if vuln.get("isUpgradable", False):
                          upgrade_path = vuln.get("upgradePath", [])
                          # Check if upgradePath is a list of strings as expected
                          if upgrade_path and isinstance(upgrade_path[0], str):
                               fix_suggestion = f"Upgrade direct dependency: {upgrade_path[0]}"
                     elif vuln.get("isPatchable", False):
                           fix_suggestion = "Patch available via `snyk wizard` or review Snyk report."

                     issues.append(SecurityIssue(
                         filename=filename, line_number=0,
                         issue_text=f"{vuln.get('title', 'N/A')} ({vuln.get('packageName', 'N/A')}@{vuln.get('version', 'N/A')}) - ID: {vuln.get('id', 'N/A')}",
                         severity=severity, confidence="HIGH", issue_type=f"snyk_vuln_{vuln.get('id', 'N/A')}",
                         line_range=[0], code=f"{vuln.get('packageName', 'N/A')}@{vuln.get('version', 'N/A')}",
                         tool=tool_name, fix_suggestion=fix_suggestion
                     ))
            elif parse_error:
                 # If JSON parsing failed, check stdout/stderr for summary text
                 summary_text = (proc.stdout + proc.stderr).lower()
                 if "tested" in summary_text and ("found 0 issues" in summary_text or "no vulnerable paths found" in summary_text):
                      status[tool_name] = "✅ No issues found (Output Error)"
                 else:
                      status[tool_name] = "❌ Error (Invalid Output)"
            else: # Parsed fine, no vulnerabilities
                  status[tool_name] = "✅ No issues found"

            # If Snyk reported an error earlier, ensure the status reflects that
            # (This check might be redundant if we handle errors above, but keep for safety)
            if status.get(tool_name,"").startswith("✅") and "error reported by snyk" in status.get(tool_name, "").lower():
                 logger.warning("Snyk status was initially OK, but an error was reported in JSON. Keeping Error status.")
                 pass # Keep the error status if previously set

        except subprocess.TimeoutExpired:
            status[tool_name] = "❌ Timed out"
            raw_output = f"{tool_name} timed out"
        except Exception as exc:
            status[tool_name] = f"❌ Failed: {exc}"
            raw_output = f"{tool_name} failed: {exc}"
            logger.exception(f"Error running {tool_name}: {exc}")
        finally:
            # Clean up temporary file
            if temp_json_file and temp_json_file.exists():
                try:
                    temp_json_file.unlink()
                except OSError as e:
                    logger.warning(f"Failed to remove temporary Snyk output file: {e}")

        return issues, status, raw_output


    def run_security_analysis(
        self,
        model: str,
        app_num: int,
        use_all_tools: bool = False
    ) -> Tuple[List[SecurityIssue], Dict[str, str], Dict[str, str]]:
        """
        Run the frontend security analysis using configured tools concurrently.
        """
        target_desc = f"{model}/app{app_num}"
        logger.info(f"Running frontend security analysis for {target_desc} (full scan: {use_all_tools})")

        app_path = self._find_application_path(model, app_num)
        if not app_path: # Handles None return
            msg = f"Application directory not found for {target_desc}"
            logger.error(msg)
            # Use self.all_tools for comprehensive status reporting on failure
            return [], {t: "❌ App path not found" for t in self.all_tools}, {t: msg for t in self.all_tools}

        # Decide which tools to attempt based on selection and availability
        tools_to_attempt = self.all_tools if use_all_tools else self.default_tools
        runnable_tools = [t for t in tools_to_attempt if self.available_tools.get(t)]

        if not runnable_tools:
             msg = f"No runnable tools selected or available for {target_desc}."
             logger.warning(msg)
             # Generate status for all potential tools listed in self.all_tools
             final_status = {}
             for tool in self.all_tools:
                 if tool not in tools_to_attempt: final_status[tool] = "⚪ Skipped"
                 elif not self.available_tools.get(tool): final_status[tool] = "❌ Not Available"
                 else: final_status[tool] = "❓ Not Runnable" # Should not happen
             return [], final_status, {t: msg for t in self.all_tools}

        logger.info(f"Executing tools: {', '.join(runnable_tools)}")

        # Map tool names to their runner functions - Ensure this map is complete
        tool_map = {
            "npm-audit": self._run_npm_audit,
            "eslint": self._run_eslint,
            "jshint": self._run_jshint,
            "snyk": self._run_snyk
        }

        all_issues: List[SecurityIssue] = []
        tool_status: Dict[str, str] = {}
        tool_outputs: Dict[str, str] = {}

        # Run tools concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(runnable_tools), 4)) as executor:
            future_to_tool = {
                executor.submit(tool_map[tool], app_path): tool
                for tool in runnable_tools if tool in tool_map # Check tool exists in map
            }

            for future in concurrent.futures.as_completed(future_to_tool):
                tool_name = future_to_tool[future]
                try:
                    issues, status_dict, output = future.result()
                    all_issues.extend(issues)
                    tool_outputs[tool_name] = output
                    tool_status.update(status_dict) # Get status from the tool's run
                    logger.info(f"Tool '{tool_name}' completed for {target_desc}. Status: {status_dict.get(tool_name, 'Unknown')}")
                except Exception as exc:
                    error_msg = f"❌ Error running {tool_name}: {exc}"
                    logger.exception(f"Failed to get result for {tool_name}: {exc}")
                    tool_status[tool_name] = error_msg
                    tool_outputs[tool_name] = str(exc)

        # Add status for tools not run
        for tool in self.all_tools:
            if tool not in tool_status: # If status wasn't set during execution
                if not self.available_tools.get(tool):
                    tool_status[tool] = "❌ Not available"
                    tool_outputs[tool] = f"{tool} command not found or non-functional."
                elif tool not in runnable_tools: # Available but not selected for this run
                    tool_status[tool] = "⚪ Skipped"
                    tool_outputs[tool] = f"{tool} was available but not selected for this run."
                else: # Should not normally happen
                     tool_status[tool] = "❓ Unknown State"
                     tool_outputs[tool] = "Tool status was not recorded."


        # Sort issues using module-level constants
        sorted_issues = sorted(
            all_issues,
            key=lambda i: (
                SEVERITY_ORDER.get(i.severity, DEFAULT_ORDER_VALUE),
                CONFIDENCE_ORDER.get(i.confidence, DEFAULT_ORDER_VALUE),
                i.filename,
                i.line_number
            )
        )

        logger.info(f"Frontend security analysis for {target_desc} completed. Total issues found: {len(sorted_issues)}")
        return sorted_issues, tool_status, tool_outputs


    def analyze_security(self, model: str, app_num: int, use_all_tools: bool = False):
        """Alias for run_security_analysis for backward compatibility."""
        return self.run_security_analysis(model, app_num, use_all_tools)


    def get_analysis_summary(self, issues: List[SecurityIssue]) -> Dict[str, Any]:
        """
        Generate summary statistics for the analysis results.
        """
        # Initialize with all severity/confidence keys from module constants
        summary = {
            "total_issues": len(issues),
            "severity_counts": {sev: 0 for sev in SEVERITY_ORDER},
            "confidence_counts": {conf: 0 for conf in CONFIDENCE_ORDER},
            "files_affected": len({issue.filename for issue in issues if issue.filename}), # Handle potential None filename
            "issue_types": {},
            "tool_counts": {},
            "scan_time": datetime.now().isoformat() # Use ISO format
        }

        if not issues:
            return summary # Return initialized summary

        # Count metrics
        for issue in issues:
            # Use .get() for safe incrementing in case severity/confidence isn't in ORDER dicts (shouldn't happen)
            summary["severity_counts"][issue.severity] = summary["severity_counts"].get(issue.severity, 0) + 1
            summary["confidence_counts"][issue.confidence] = summary["confidence_counts"].get(issue.confidence, 0) + 1
            summary["issue_types"][issue.issue_type] = summary["issue_types"].get(issue.issue_type, 0) + 1
            summary["tool_counts"][issue.tool] = summary["tool_counts"].get(issue.tool, 0) + 1

        return summary

# Example usage (if run as a script)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    # Replace with the actual path to your projects base directory
    # Assumes structure like: base_dir/Llama/app2/frontend/...
    project_base_path = Path(".") # Example: Current directory or specify "path/to/your/projects"

    analyzer = FrontendSecurityAnalyzer(base_path=project_base_path)

    # Example: Analyze Llama app 2 using all tools
    model_name = "Llama" # Replace with actual model name if needed
    app_number = 2      # Replace with actual app number

    logger.info(f"Starting analysis for {model_name}/app{app_number}")
    found_issues, statuses, outputs = analyzer.run_security_analysis(
        model=model_name,
        app_num=app_number,
        use_all_tools=True # Run all available tools
    )

    logger.info("\n--- Analysis Summary ---")
    summary = analyzer.get_analysis_summary(found_issues)
    print(json.dumps(summary, indent=2))

    logger.info("\n--- Tool Statuses ---")
    print(json.dumps(statuses, indent=2))

    # Optionally print found issues
    if found_issues:
        logger.info("\n--- Found Issues ---")
        for issue in found_issues:
             print(f"- {issue.tool}: {issue.severity} ({issue.filename}:{issue.line_number}) - {issue.issue_text}")
    else:
        logger.info("No issues found.")

    # Optionally print raw outputs (can be very long)
    # logger.info("\n--- Raw Outputs ---")
    # print(json.dumps(outputs, indent=2))