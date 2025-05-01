"""
Frontend Security Analysis Module

Provides security scanning for frontend code using multiple tools:
- npm audit: Dependency vulnerability checks.
- ESLint: Code quality and potential React/Svelte/Vue security linting.
- JSHint: Code quality checks focusing on potential security risks.
- Snyk: Dependency vulnerability scanning.

Features path detection, concurrent execution, logging, and error handling.

FIX: Uses shutil.which() to find executable paths for better reliability.
"""

import os
import json
import shutil # <-- Added import
import subprocess
import logging
import concurrent.futures
import platform
import sys # <-- Added import (though not for -m, useful for path checks maybe later)
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

def get_executable_path(name: str) -> Optional[str]:
    """
    Find the full path to an executable using shutil.which().
    Handles '.cmd' extension needed on Windows.

    Args:
        name: Base command name (e.g., "npm", "npx", "snyk").

    Returns:
        The full path to the executable if found, otherwise None.
    """
    cmd = f"{name}.cmd" if IS_WINDOWS else name
    path = shutil.which(cmd)
    if path:
        logger.debug(f"Found executable for '{name}' at: {path}")
        return path
    else:
        # Try finding without .cmd suffix on Windows as a fallback
        if IS_WINDOWS:
            path = shutil.which(name)
            if path:
                logger.debug(f"Found executable for '{name}' (no .cmd) at: {path}")
                return path
        logger.warning(f"Executable '{cmd}' (or '{name}') not found in PATH.")
        return None

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

        # Check availability of required tools using the new helper
        self.available_tools = {
            "npm-audit": bool(get_executable_path("npm")),
            "eslint": bool(get_executable_path("npx")), # Check if npx is available
            "jshint": bool(get_executable_path("npx")), # Check if npx is available
            "snyk": bool(get_executable_path("snyk"))
        }
        logger.info(f"Available tools check: {self.available_tools}")

    # _check_tool is replaced by using get_executable_path directly

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

    def _run_frontend_tool(
        self,
        tool_name: str,
        base_command: str, # e.g., "npm", "npx", "snyk"
        args: List[str],
        working_directory: Path,
        parser: Optional[Callable[[str], List[SecurityIssue]]] = None, # Optional parser for tools outputting structured data
        input_data: Optional[str] = None,
        timeout: int = TOOL_TIMEOUT
    ) -> Tuple[List[SecurityIssue], str]:
        """
        Generic helper to find and run a frontend tool using subprocess.

        Args:
            tool_name: User-friendly name of the tool (for logging).
            base_command: The base command name to find (e.g., "npm").
            args: List of arguments to pass to the command.
            working_directory: The directory to run the command in.
            parser: Optional function to parse stdout into SecurityIssue objects.
            input_data: Optional string data to pass to stdin.
            timeout: Timeout in seconds for the subprocess.

        Returns:
            Tuple: (List of found SecurityIssue objects, Raw stdout/stderr from the tool).
        """
        issues: List[SecurityIssue] = []
        raw_output = f"{tool_name} execution failed."

        executable_path = get_executable_path(base_command)
        if not executable_path:
            raw_output = f"{tool_name} command ('{base_command}') not found in PATH."
            logger.error(raw_output)
            return issues, raw_output # Return early if executable not found

        command = [executable_path] + args
        logger.info(f"[{tool_name}] Attempting to run: {' '.join(command)} in '{working_directory}'")

        try:
            proc = subprocess.run(
                command,
                cwd=str(working_directory),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False, # Don't raise exception on non-zero exit code
                encoding='utf-8',
                errors='replace',
                input=input_data
            )
            logger.info(f"[{tool_name}] Subprocess finished with return code: {proc.returncode}")
            raw_output = f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"

            # Basic check for common execution errors based on stderr
            if proc.returncode != 0 and proc.stderr:
                 stderr_lower = proc.stderr.lower()
                 if "command not found" in stderr_lower or "not recognized" in stderr_lower:
                      logger.error(f"{tool_name} execution failed: Command likely not found or inner command failed. Stderr: {proc.stderr}")
                      # Keep raw_output as is, which contains the error
                 elif "authenticate" in stderr_lower or "auth token" in stderr_lower:
                      logger.error(f"{tool_name} execution failed: Authentication required.")
                      raw_output += "\nERROR_NOTE: Authentication required."
                 else:
                      # Log other non-zero exits as warnings, as some tools use them for finding issues
                      logger.warning(f"{tool_name} exited with code {proc.returncode}. Stderr: {proc.stderr}")

            # Attempt parsing only if a parser is provided and stdout exists
            if parser and proc.stdout:
                logger.debug(f"[{tool_name}] Attempting to parse stdout...")
                try:
                    issues = parser(proc.stdout)
                    logger.info(f"{tool_name} found {len(issues)} issues via parser.")
                except Exception as e:
                    logger.error(f"Failed to parse {tool_name} output: {e}\nOutput:\n{proc.stdout[:500]}...")
                    raw_output += f"\nPARSING_ERROR: {str(e)}"
            elif proc.stdout:
                 logger.debug(f"[{tool_name}] No parser provided or stdout empty, skipping parsing.")

        except subprocess.TimeoutExpired:
            logger.error(f"{tool_name} timed out after {timeout} seconds.")
            raw_output = f"{tool_name} timed out after {timeout} seconds."
        except FileNotFoundError:
             # Should be caught by get_executable_path, but handle defensively
             logger.error(f"{tool_name} executable '{executable_path}' not found during run (unexpected).")
             raw_output = f"{tool_name} executable not found during run: {executable_path}"
        except Exception as e:
            logger.exception(f"An unexpected error occurred while running {tool_name}: {e}")
            raw_output = f"Unexpected error running {tool_name}: {str(e)}"

        return issues, raw_output


    # --- Tool-Specific Runner Methods (using the helper) ---

    def _parse_npm_audit(self, stdout: str) -> List[SecurityIssue]:
        """Parses the JSON output of `npm audit`."""
        issues: List[SecurityIssue] = []
        audit_data = safe_json_loads(stdout.strip())
        if not audit_data:
            logger.warning("npm audit: Failed to parse JSON data or output was empty.")
            return issues

        vulnerabilities = {}
        if isinstance(audit_data, dict): # Standard format
             if "vulnerabilities" in audit_data: vulnerabilities = audit_data["vulnerabilities"]
             elif "advisories" in audit_data: vulnerabilities = audit_data["advisories"] # Older format
        # Note: npm audit doesn't typically return a list at the top level

        if not vulnerabilities:
             logger.info("npm audit: No vulnerabilities found in JSON.")
             return issues

        for key, vuln_info in vulnerabilities.items():
            if not isinstance(vuln_info, dict): continue # Skip invalid entries

            severity_str = vuln_info.get("severity", "info")
            name = vuln_info.get("name", vuln_info.get("module_name", key))
            version = vuln_info.get("range", vuln_info.get("vulnerable_versions", "N/A"))
            title = vuln_info.get("title", "N/A")
            fix_text = vuln_info.get("recommendation", "Review advisory")

            # Try extracting better title/fix
            if isinstance(vuln_info.get("via"), list) and vuln_info["via"]:
                 if isinstance(vuln_info["via"][0], dict): title = vuln_info["via"][0].get("title", title)

            fix_available = vuln_info.get("fixAvailable", None) # Can be bool or dict
            if isinstance(fix_available, dict):
                 fix_ver = fix_available.get("version")
                 if fix_ver: fix_text = f"Update {name} to version {fix_ver}"
            elif fix_available is False: fix_text = "No simple fix available via `npm audit fix`"
            elif fix_available is True: fix_text = "Fix available via `npm audit fix`"


            severity = SEVERITY_MAP.get(severity_str, "LOW")
            issues.append(SecurityIssue(
                filename="package-lock.json", line_number=0,
                issue_text=f"{title} (Package: {name}, Version(s): {version})",
                severity=severity, confidence="HIGH",
                issue_type=f"dependency_vuln_{name}", line_range=[0],
                code=f"{name}@{version}", tool="npm-audit", fix_suggestion=fix_text
            ))
        return issues

    def _run_npm_audit(self, app_path: Path) -> Tuple[List[SecurityIssue], Dict[str, str], str]:
        """
        Run `npm audit --json` to check for dependency vulnerabilities.
        Handles package-lock generation attempt.
        """
        tool_name = "npm-audit"
        status = {tool_name: "⚠️ Not run"}
        raw_output_combined = ""

        package_json_path = app_path / "package.json"
        package_lock_path = app_path / "package-lock.json"

        if not package_json_path.exists():
            msg = f"No package.json found in {app_path}, skipping {tool_name}."
            logger.warning(msg)
            status[tool_name] = "❌ No package.json"
            return [], status, msg

        # Attempt to ensure package-lock.json exists
        if not package_lock_path.exists():
            logger.info(f"No package-lock.json found in {app_path}, attempting `npm i --package-lock-only`...")
            init_args = ["install", "--package-lock-only", "--ignore-scripts", "--no-audit"]
            _, init_output = self._run_frontend_tool(
                "npm-install", "npm", init_args, app_path, timeout=120
            )
            raw_output_combined += f"--- npm install --package-lock-only ---\n{init_output}\n--- End npm install ---\n\n"
            if not package_lock_path.exists():
                 logger.warning(f"Failed to generate package-lock.json. Audit may be inaccurate.")
                 raw_output_combined += "WARNING: Failed to generate package-lock.json.\n"

        # Run npm audit
        audit_args = ["audit", "--json"]
        issues, audit_output = self._run_frontend_tool(
            tool_name, "npm", audit_args, app_path, parser=self._parse_npm_audit
        )
        raw_output_combined += audit_output

        # Determine final status based on errors in output and issues found
        output_lower = raw_output_combined.lower()
        if "error" in output_lower or "failed" in output_lower:
             if not issues and "found 0 vulnerabilities" not in output_lower: # Real error if no issues found despite error text
                 status[tool_name] = "❌ Error Reported"
             else: # Issues found OR "found 0" message present despite error text
                 status[tool_name] = f"⚠️ Found {len(issues)} issues (Errors reported)"
        elif issues:
             status[tool_name] = f"⚠️ Found {len(issues)} issues"
        else:
             status[tool_name] = "✅ No issues found"

        # Handle specific case of auth failure mentioned in output
        if "authenticate" in output_lower or "auth token" in output_lower:
             status[tool_name] = "❌ Authentication required"


        return issues, status, raw_output_combined


    def _parse_eslint(self, stdout: str) -> List[SecurityIssue]:
        """Parses ESLint JSON output."""
        issues: List[SecurityIssue] = []
        parsed = safe_json_loads(stdout.strip())
        if not isinstance(parsed, list):
             logger.warning(f"ESLint: Expected a list from JSON output, got {type(parsed)}. Cannot parse.")
             return issues

        security_patterns = ["security", "inject", "prototype", "csrf", "xss", "sanitize", "escape", "auth", "unsafe", "exploit", "vuln"]
        for file_result in parsed:
            if not isinstance(file_result, dict): continue # Skip invalid entries
            file_path = file_result.get("filePath", "unknown")
            # Path should already be relative from ESLint, but normalize just in case
            rel_path = os.path.normpath(file_path) # Basic normalization

            for msg in file_result.get("messages", []):
                if not isinstance(msg, dict): continue # Skip invalid messages

                is_fatal = msg.get("fatal", False)
                line_num = msg.get("line", 0)
                severity_value = msg.get("severity", 1) # 1=warn, 2=error
                rule_id = msg.get("ruleId", "parsing_error" if is_fatal else "unknown_rule")
                message = msg.get("message", "Unknown issue")

                severity = "HIGH" if severity_value >= 2 or is_fatal else "MEDIUM"
                confidence = "HIGH" if is_fatal else "MEDIUM"
                issue_type = rule_id

                # Check for security keywords
                rule_id_str = str(rule_id).lower() if rule_id else ""
                message_str = str(message).lower()
                if any(pattern in rule_id_str or pattern in message_str for pattern in security_patterns):
                    if severity != "HIGH": severity = "HIGH" # Elevate

                issues.append(SecurityIssue(
                    filename=rel_path, line_number=line_num, issue_text=f"[{rule_id}] {message}",
                    severity=severity, confidence=confidence, issue_type=issue_type,
                    line_range=[line_num], code=msg.get("source", "N/A"),
                    tool="eslint", fix_suggestion=msg.get("fix", {}).get("text")
                ))
        return issues

    def _run_eslint(self, app_path: Path) -> Tuple[List[SecurityIssue], Dict[str, str], str]:
        """Run ESLint using npx and parse JSON output."""
        tool_name = "eslint"
        status = {tool_name: "⚠️ Not run"}
        temp_dir = None
        eslint_config_path = None
        raw_output_combined = ""

        has_files, _ = self._check_source_files(app_path)
        if not has_files:
            msg = f"No relevant frontend files found in {app_path}, skipping {tool_name}."
            status[tool_name] = "❌ No files to analyze"
            return [], status, msg

        scan_dir = "src" if (app_path / "src").is_dir() else "."
        logger.info(f"ESLint will scan '{scan_dir}' within {app_path}")

        args = ["eslint", "--ext", ".js,.jsx,.ts,.tsx,.vue,.svelte", "--format", "json", "--quiet"]

        try:
            project_config_exists = any((app_path / f).exists() for f in
                                        [".eslintrc.js", ".eslintrc.json", ".eslintrc.yaml", ".eslintrc.yml", "eslint.config.js"])

            if project_config_exists:
                logger.info(f"Using existing ESLint configuration found in {app_path}")
            else:
                logger.info("No project ESLint config found, creating temporary basic config.")
                temp_dir = Path(tempfile.mkdtemp(prefix="eslint_config_"))
                eslint_config_path = temp_dir / ".eslintrc.json"
                eslint_config = {
                    "root": True, "env": {"browser": True, "es2021": True, "node": True},
                    "extends": ["eslint:recommended"],
                    "parserOptions": { "ecmaVersion": "latest", "sourceType": "module", "ecmaFeatures": {"jsx": True} },
                    "rules": { "no-eval": "error", "no-implied-eval": "error", "no-alert": "warn" }
                }
                with open(eslint_config_path, "w") as f: json.dump(eslint_config, f, indent=2)
                args.extend(["--config", str(eslint_config_path)])

            args.append(scan_dir)

            issues, run_output = self._run_frontend_tool(
                tool_name, "npx", args, app_path, parser=self._parse_eslint
            )
            raw_output_combined = run_output

            # Determine status based on output and issues
            output_lower = run_output.lower()
            if "error" in output_lower or "failed" in output_lower:
                 # Check for specific config/plugin errors
                 if "plugin" in output_lower and "was conflicted" not in output_lower:
                      status[tool_name] = "❌ Plugin/Config Issue"
                 elif not issues: # If general error and no issues parsed
                      status[tool_name] = "❌ Error Reported"
                 else: # Issues found despite error messages
                      status[tool_name] = f"⚠️ Found {len(issues)} issues (Errors reported)"
            elif issues:
                 status[tool_name] = f"⚠️ Found {len(issues)} issues"
            else:
                 status[tool_name] = "✅ No issues found"

        except Exception as exc: # Catch errors in this runner function itself
            status[tool_name] = f"❌ Failed: {exc}"
            raw_output_combined = f"{tool_name} runner failed: {exc}"
            logger.exception(f"Error running {tool_name}: {exc}")
        finally:
            if eslint_config_path and temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"Failed to remove temporary ESLint config directory: {e}")

        return issues, status, raw_output_combined


    def _parse_jshint(self, stdout: str) -> List[SecurityIssue]:
        """Parses JSHint checkstyle XML output."""
        issues: List[SecurityIssue] = []
        try:
            # import xml.etree.ElementTree as ET # Already imported
            root = ET.fromstring(stdout.strip())
            security_keywords = ["eval", "function(", "settimeout", "setinterval", "innerhtml", "document.write", "prototype", "constructor", "unsafe"]
            security_codes = ["W054", "W061"]

            for file_elem in root.findall("file"):
                file_path = file_elem.get("name", "unknown")
                rel_path = os.path.normpath(file_path) # Assume path is already relative

                for error in file_elem.findall("error"): # JSHint checkstyle uses <error> tag
                    line = int(error.get("line", 0))
                    message = error.get("message", "Unknown JSHint issue")
                    source_code = error.get("source", "") # e.g., jshint.W031

                    is_security = source_code in security_codes or \
                                  any(keyword.lower() in message.lower() for keyword in security_keywords)

                    severity = "LOW"; confidence = "MEDIUM"
                    issue_type = f"jshint_{source_code}" if source_code else "jshint_unknown"

                    if source_code.startswith('E'): severity = "HIGH"; confidence = "HIGH"
                    elif source_code.startswith('W'): severity = "MEDIUM"

                    if is_security:
                        severity = "HIGH"
                        confidence = "HIGH" if source_code in security_codes else "MEDIUM"
                        issue_type = f"jshint_security_{source_code}" if source_code else "jshint_security_concern"

                    issues.append(SecurityIssue(
                        filename=rel_path, line_number=line, issue_text=f"[{source_code}] {message}",
                        severity=severity, confidence=confidence, issue_type=issue_type,
                        line_range=[line], code="N/A (Check file)", tool="jshint",
                        fix_suggestion="Review code."
                    ))
        except ET.ParseError as e_xml:
            logger.error(f"JSHint: Failed to parse XML output: {e_xml}")
        except Exception as e_proc:
            logger.error(f"JSHint: Error processing XML output: {e_proc}")
        return issues

    def _run_jshint(self, app_path: Path) -> Tuple[List[SecurityIssue], Dict[str, str], str]:
        """Run JSHint using npx and parse checkstyle XML output."""
        tool_name = "jshint"
        status = {tool_name: "⚠️ Not run"}
        temp_dir = None
        jshintrc_path_used = None
        temp_jshintrc_created = False
        raw_output_combined = ""

        has_files, source_files = self._check_source_files(app_path)
        if not has_files:
            msg = f"No frontend files found in {app_path}, skipping {tool_name}."
            status[tool_name] = "❌ No files to analyze"
            return [], status, msg

        js_files = [f for f in source_files if f.endswith(('.js', '.jsx'))]
        if not js_files:
            msg = f"No JavaScript/JSX files found in {app_path}, skipping {tool_name}."
            status[tool_name] = "❌ No JS files to analyze"
            return [], status, msg

        max_jshint_files = 30
        files_to_scan_abs = js_files[:max_jshint_files]
        # Convert absolute paths back to relative for the command line within app_path
        files_to_scan_rel = [os.path.relpath(f, str(app_path)) for f in files_to_scan_abs]

        if len(js_files) > max_jshint_files:
            logger.warning(f"JSHint analysis limited to the first {max_jshint_files} JS/JSX files found.")

        args = ["jshint", "--reporter=checkstyle"]

        try:
            project_jshintrc = app_path / ".jshintrc"
            if project_jshintrc.exists():
                jshintrc_path_used = str(project_jshintrc)
                logger.info(f"Using existing project JSHint config: {jshintrc_path_used}")
                args.extend(["--config", jshintrc_path_used]) # Pass existing config explicitly
            else:
                temp_dir = Path(tempfile.mkdtemp(prefix="jshint_config_"))
                jshintrc_path_used = str(temp_dir / ".jshintrc")
                jshint_config = {
                    "esversion": 9, "browser": True, "node": True,
                    "strict": "implied", "undef": True, "unused": "vars",
                    "evil": True, "-W054": True, "-W061": True, "maxerr": 100
                }
                with open(jshintrc_path_used, "w") as f: json.dump(jshint_config, f, indent=2)
                temp_jshintrc_created = True
                logger.info(f"Created temporary JSHint config at {jshintrc_path_used}")
                args.extend(["--config", jshintrc_path_used]) # Pass temporary config

            args.extend(files_to_scan_rel) # Pass relative paths

            issues, run_output = self._run_frontend_tool(
                tool_name, "npx", args, app_path, parser=self._parse_jshint
            )
            raw_output_combined = run_output

            # Determine status
            output_lower = run_output.lower()
            if "error" in output_lower or "failed" in output_lower:
                 if not issues: status[tool_name] = "❌ Error Reported"
                 else: status[tool_name] = f"⚠️ Found {len(issues)} issues (Errors reported)"
            elif issues:
                 status[tool_name] = f"⚠️ Found {len(issues)} issues"
            else:
                 status[tool_name] = "✅ No issues found"

        except Exception as exc:
            status[tool_name] = f"❌ Failed: {exc}"
            raw_output_combined = f"{tool_name} runner failed: {exc}"
            logger.exception(f"Error running {tool_name}: {exc}")
        finally:
            if temp_jshintrc_created and temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                    logger.debug("Cleaned up temporary JSHint directory")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary JSHint directory: {e}")

        return issues, status, raw_output_combined


    def _parse_snyk(self, stdout: str) -> List[SecurityIssue]:
        """Parses Snyk JSON output."""
        # Note: Snyk JSON is usually written to file, this parser is for potential future use
        # if stdout capture becomes viable or for processing the file content.
        issues: List[SecurityIssue] = []
        snyk_data = safe_json_loads(stdout.strip())
        if not snyk_data:
             logger.warning("Snyk: Failed to parse JSON data or output was empty.")
             return issues

        vulnerabilities = []
        if isinstance(snyk_data, dict):
            vulnerabilities = snyk_data.get("vulnerabilities", [])
        elif isinstance(snyk_data, list): # Handle monorepo output
            for project in snyk_data:
                 if isinstance(project, dict): vulnerabilities.extend(project.get("vulnerabilities", []))

        if not vulnerabilities:
             logger.info("Snyk: No vulnerabilities found in JSON.")
             return issues

        for vuln in vulnerabilities:
            if not isinstance(vuln, dict): continue
            severity = SEVERITY_MAP.get(vuln.get("severity", "low"), "LOW")
            from_chain = vuln.get("from", ["unknown_dependency"])
            filename = from_chain[0] if from_chain else "dependency_tree"

            fix_suggestion = "Review Snyk report for remediation details."
            if vuln.get("isUpgradable", False):
                 upgrade_path = vuln.get("upgradePath", [])
                 if upgrade_path and isinstance(upgrade_path[0], str): fix_suggestion = f"Upgrade direct dependency: {upgrade_path[0]}"
            elif vuln.get("isPatchable", False): fix_suggestion = "Patch available via `snyk wizard` or review Snyk report."

            issues.append(SecurityIssue(
                filename=filename, line_number=0,
                issue_text=f"{vuln.get('title', 'N/A')} ({vuln.get('packageName', 'N/A')}@{vuln.get('version', 'N/A')}) - ID: {vuln.get('id', 'N/A')}",
                severity=severity, confidence="HIGH", issue_type=f"snyk_vuln_{vuln.get('id', 'N/A')}",
                line_range=[0], code=f"{vuln.get('packageName', 'N/A')}@{vuln.get('version', 'N/A')}",
                tool="snyk", fix_suggestion=fix_suggestion
            ))
        return issues

    def _run_snyk(self, app_path: Path) -> Tuple[List[SecurityIssue], Dict[str, str], str]:
        """Run Snyk test using --json-file-output and parse the file."""
        tool_name = "snyk"
        status = {tool_name: "⚠️ Not run"}
        raw_output_combined = ""
        temp_json_file = None

        if not (app_path / "package.json").exists():
            msg = f"No package.json found in {app_path}, skipping {tool_name}."
            logger.warning(msg)
            status[tool_name] = "❌ No package.json"
            return [], status, msg

        issues: List[SecurityIssue] = []
        try:
            # Create a temporary file for JSON output
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json", encoding='utf-8') as tmpfile:
                temp_json_file = Path(tmpfile.name)
            logger.debug(f"Snyk output will be written to temporary file: {temp_json_file}")

            # Run snyk test using the generic helper, but without a parser (we parse the file)
            args = ["test", f"--json-file-output={temp_json_file}"]
            _, run_output = self._run_frontend_tool(
                tool_name, "snyk", args, app_path, timeout=90 # Longer timeout for Snyk
            )
            raw_output_combined = run_output

            # Check for common errors before parsing file
            output_lower = run_output.lower()
            if "authenticate" in output_lower or "auth token" in output_lower:
                status[tool_name] = "❌ Authentication required"
                # No need to parse file if auth failed
            elif temp_json_file.exists() and temp_json_file.stat().st_size > 0:
                 logger.debug(f"Attempting to parse Snyk JSON output file: {temp_json_file}")
                 try:
                     with open(temp_json_file, 'r', encoding='utf-8') as f:
                         issues = self._parse_snyk(f.read()) # Use the parser here

                     # Determine status based on parsed issues and errors during run
                     if "error" in output_lower or "failed" in output_lower:
                          if not issues: status[tool_name] = "❌ Error Reported"
                          else: status[tool_name] = f"⚠️ Found {len(issues)} issues (Errors reported)"
                     elif issues:
                          status[tool_name] = f"⚠️ Found {len(issues)} issues"
                     else:
                          status[tool_name] = "✅ No issues found"
                 except Exception as e_read:
                     logger.error(f"Failed to read or parse Snyk JSON output file {temp_json_file}: {e_read}")
                     status[tool_name] = "❌ Error Reading Output File"
            elif "error" in output_lower or "failed" in output_lower: # Handle errors when JSON file is empty/missing
                 status[tool_name] = "❌ Error Reported (No Output File)"
            else: # No errors reported, no file content -> assume no issues
                 status[tool_name] = "✅ No issues found (No Output File)"


        except Exception as exc:
            status[tool_name] = f"❌ Failed: {exc}"
            raw_output_combined = f"{tool_name} runner failed: {exc}"
            logger.exception(f"Error running {tool_name}: {exc}")
        finally:
            if temp_json_file and temp_json_file.exists():
                try:
                    temp_json_file.unlink()
                    logger.debug(f"Removed temporary Snyk file: {temp_json_file}")
                except OSError as e:
                    logger.warning(f"Failed to remove temporary Snyk output file: {e}")

        return issues, status, raw_output_combined


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
    app_number = 2       # Replace with actual app number

    logger.info(f"Starting analysis for {model_name}/app{app_number}")
    try:
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

    except ValueError as e:
         logger.error(f"Analysis failed for {model_name}/app{app_number}: {e}")
    except Exception as e:
         logger.exception(f"An unexpected error occurred during analysis for {model_name}/app{app_number}: {e}")

