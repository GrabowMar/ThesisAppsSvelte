"""
Frontend Security Analysis Module

Provides security scanning for frontend code using multiple tools:
- npm audit for dependency vulnerabilities
- ESLint for code quality and potential React or Svelte linting
- retire.js for known vulnerable JavaScript libraries
- snyk for additional security checks

Features improved path detection, better logging, and more robust error handling.
"""

import os
import json
import subprocess
import logging
import concurrent.futures
import platform
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, Union

# -----------------------------------------------------------------------------
# Logging Configuration
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def cmd_name(name: str) -> str:
    """
    Return the proper command name for Windows if needed.
    For example, "npm" -> "npm.cmd" on Windows.
    """
    return f"{name}.cmd" if IS_WINDOWS else name

def safe_json_loads(data: str) -> Optional[dict]:
    """
    Safely parse JSON data, returning None on failure.
    Logs an error if parsing fails.
    """
    try:
        return json.loads(data)
    except json.JSONDecodeError as exc:
        logger.error(f"Failed to parse JSON: {exc}")
        logger.debug(f"Raw output snippet: {data[:300]}...")
        return None

def normalize_path(path: Union[str, Path]) -> Path:
    """
    Normalize a path string or Path object to ensure it's a resolved Path.
    """
    if isinstance(path, str):
        path = Path(path)
    return path.resolve()

# -----------------------------------------------------------------------------
# Data Classes
# -----------------------------------------------------------------------------
@dataclass
class SecurityIssue:
    """Represents a security issue found in code."""
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
        """Convert to dictionary format for serialization."""
        return {
            "filename": self.filename,
            "line_number": self.line_number,
            "issue_text": self.issue_text,
            "severity": self.severity,
            "confidence": self.confidence,
            "issue_type": self.issue_type,
            "line_range": self.line_range,
            "code": self.code,
            "tool": self.tool,
            "fix_suggestion": self.fix_suggestion
        }

# -----------------------------------------------------------------------------
# Main Analyzer Class
# -----------------------------------------------------------------------------
class FrontendSecurityAnalyzer:
    """
    Analyzes frontend code for security issues using multiple tools:
    - npm-audit
    - ESLint
    - retire.js
    - snyk
    """

    def __init__(self, base_path: Path):
        """
        Initialize the analyzer with the base path.
        
        Args:
            base_path: The root directory where all code resides
        """
        self.base_path = normalize_path(base_path)
        logger.info(f"Initialized FrontendSecurityAnalyzer with base path: {self.base_path}")
        
        # Default quick-scan tools vs. full-scan
        self.default_tools = ["eslint"]
        self.all_tools = ["npm-audit", "eslint", "retire-js", "snyk"]
        
        # Check which tools are available
        self.available_tools = {
            "npm-audit": self._check_tool("npm"),
            "eslint": self._check_tool("npx"),
            "retire-js": self._check_tool("npx"),
            "snyk": self._check_tool("snyk")
        }
        
        logger.info(f"Available tools: {', '.join(k for k, v in self.available_tools.items() if v)}")

    def _check_tool(self, cmd: str) -> bool:
        """
        Check if a command exists in the system PATH.
        
        Args:
            cmd: Command to check
            
        Returns:
            True if command exists, False otherwise
        """
        tool_cmd = cmd_name(cmd)
        try:
            proc = subprocess.run(
                [tool_cmd, "--version"], 
                capture_output=True, 
                timeout=5
            )
            return proc.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _find_application_path(self, model: str, app_num: int) -> Path:
        """
        Attempt to locate the frontend application path. Checks several
        common paths in order of preference, then falls back to base_path.
        
        Args:
            model: Model identifier (e.g., 'Llama', 'GPT4o')
            app_num: Application number (e.g., 1, 2, 3)
            
        Returns:
            Path to the frontend application directory
        """
        logger.debug(f"Finding application path for {model}/app{app_num}")
        
        # Try common directory structures
        candidates = [
            self.base_path / model / f"app{app_num}" / "frontend",
            self.base_path / model / f"app{app_num}" / "client",
            self.base_path / model / f"app{app_num}" / "web",
            self.base_path / model / f"app{app_num}"
        ]
        
        # Check each candidate path
        for candidate in candidates:
            if candidate.exists() and candidate.is_dir():
                logger.info(f"Found frontend directory: {candidate}")
                return candidate
        
        # Fallback to base_path/model/app{num}
        fallback = self.base_path / model / f"app{app_num}"
        if not fallback.exists():
            logger.warning(f"Creating directory {fallback} as it doesn't exist")
            try:
                fallback.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"Failed to create directory {fallback}: {e}")
                
        logger.warning(f"No specific frontend path found; using fallback: {fallback}")
        return fallback

    def _check_source_files(self, directory: Path) -> Tuple[bool, List[str]]:
        """
        Check if the directory contains any typical frontend source files.
        
        Args:
            directory: Path to the directory to scan
            
        Returns:
            Tuple containing:
            - Boolean indicating if any source files were found
            - List of found source file paths
        """
        if not directory.exists() or not directory.is_dir():
            logger.warning(f"Directory does not exist or is not a directory: {directory}")
            return False, []

        # Common frontend file extensions
        exts = (".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".html", ".css")
        found_files = []
        
        try:
            # Find all matching files but exclude node_modules and other common dirs to avoid
            # scanning unnecessary files
            excluded_dirs = ("node_modules", ".git", "dist", "build", "coverage")
            
            for root, dirs, files in os.walk(directory):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if d not in excluded_dirs]
                
                for file in files:
                    if file.endswith(exts):
                        file_path = os.path.join(root, file)
                        found_files.append(file_path)
            
            logger.info(f"Found {len(found_files)} frontend source files in {directory}")
            return bool(found_files), found_files
        except Exception as e:
            logger.error(f"Error checking source files in {directory}: {e}")
            return False, []

    def _run_npm_audit(self, app_path: Path) -> Tuple[List[SecurityIssue], Dict[str, str], str]:
        """
        Run `npm audit --json` to check for dependency vulnerabilities.
        
        Args:
            app_path: Path to the frontend application
            
        Returns:
            Tuple containing:
            - List of security issues found
            - Dictionary of tool status messages
            - Raw output from the tool
        """
        tool_name = "npm-audit"
        issues: List[SecurityIssue] = []
        status = {"npm-audit": "⚠️ Not run (no package.json)"}
        
        if not (app_path / "package.json").exists():
            msg = f"No package.json found in {app_path}. Skipping npm audit."
            logger.warning(msg)
            return issues, status, msg

        # Attempt to ensure package-lock.json exists
        if not (app_path / "package-lock.json").exists():
            try:
                logger.info("No package-lock.json found; generating one via `npm i --package-lock-only`.")
                init_cmd = [cmd_name("npm"), "i", "--package-lock-only"]
                subprocess.run(init_cmd, cwd=str(app_path), capture_output=True, text=True, timeout=TOOL_TIMEOUT)
            except Exception as exc:
                msg = f"Failed to generate package-lock.json: {exc}"
                logger.warning(msg)
                status[tool_name] = "❌ Failed to generate package-lock.json"
                return issues, status, msg

        # Now run npm audit
        command = [cmd_name("npm"), "audit", "--json"]
        logger.info(f"Running npm audit in {app_path}...")
        try:
            proc = subprocess.run(
                command,
                cwd=str(app_path),
                capture_output=True,
                text=True,
                timeout=TOOL_TIMEOUT
            )
        except subprocess.TimeoutExpired:
            status[tool_name] = "❌ Timed out"
            return issues, status, "npm audit timed out"
        except Exception as exc:
            status[tool_name] = f"❌ Failed: {exc}"
            return issues, status, f"npm audit failed: {exc}"

        # Special handling for npm audit errors that aren't real errors
        if proc.returncode != 0 and proc.stderr and "ERR!" in proc.stderr:
            # Check if this is actually a "found vulnerabilities" case
            if "found vulnerabilities" in proc.stderr:
                # This is normal - npm audit returns non-zero when finding issues
                logger.info("npm audit found vulnerabilities")
            else:
                msg = f"npm audit error: {proc.stderr}"
                logger.error(msg)
                status[tool_name] = "❌ Error"
                return issues, status, msg

        raw_output = proc.stdout.strip()
        if not raw_output:
            # If stdout empty, check stderr
            msg = proc.stderr.strip() or "npm audit produced no output"
            status[tool_name] = "✅ No issues found" if "found 0 vulnerabilities" in msg else "❌ No output"
            return issues, status, msg

        audit_data = safe_json_loads(raw_output)
        if not audit_data:
            status[tool_name] = "❌ Invalid JSON output"
            return issues, status, raw_output
            
        # Check if vulnerabilities exist in the expected format
        if "vulnerabilities" not in audit_data:
            # Check for newer npm audit format
            if "auditReportVersion" in audit_data:
                # This is the new npm 7+ format
                vulnerabilities = audit_data.get("vulnerabilities", {})
                metadata = audit_data.get("metadata", {})
                
                if not vulnerabilities:
                    status[tool_name] = "✅ No issues found"
                    return issues, status, raw_output
                    
                for vuln_name, vuln_info in vulnerabilities.items():
                    # Get the severity from the vulnerability info
                    severity = SEVERITY_MAP.get(vuln_info.get("severity", "low"), "LOW")
                    
                    # Extract more detailed information about the vulnerability
                    via_info = ""
                    if "via" in vuln_info:
                        if isinstance(vuln_info["via"], list):
                            for via_item in vuln_info["via"]:
                                if isinstance(via_item, dict) and "title" in via_item:
                                    via_info = via_item.get("title", "")
                                    break
                    
                    # Get fix information
                    fix_version = None
                    fix_available = vuln_info.get("fixAvailable", {})
                    if fix_available:
                        if isinstance(fix_available, dict):
                            fix_version = fix_available.get("version")
                    
                    fix_text = f"Update to version {fix_version}" if fix_version else "Update to the latest version"
                    
                    # Create a descriptive issue text
                    issue_text = via_info if via_info else f"Vulnerability in {vuln_name}"
                    
                    # Get affected nodes (file paths)
                    nodes = vuln_info.get("nodes", [])
                    affected_path = nodes[0] if nodes else "package.json"
                    
                    issues.append(
                        SecurityIssue(
                            filename=affected_path,
                            line_number=0,
                            issue_text=issue_text,
                            severity=severity,
                            confidence="HIGH",
                            issue_type="dependency_vulnerability",
                            line_range=[0],
                            code=f"{vuln_name}@{vuln_info.get('version', 'unknown')}",
                            tool="npm-audit",
                            fix_suggestion=fix_text
                        )
                    )
            else:
                status[tool_name] = "✅ No vulnerabilities found"
                return issues, status, raw_output

        # Process vulnerabilities in the standard format
        else:
            for vuln_name, vuln_info in audit_data["vulnerabilities"].items():
                severity = SEVERITY_MAP.get(vuln_info.get("severity", "low"), "LOW")
                issues.append(
                    SecurityIssue(
                        filename="package.json",
                        line_number=0,
                        issue_text=vuln_info.get("title", "Unknown vulnerability"),
                        severity=severity,
                        confidence="HIGH",
                        issue_type="dependency_vulnerability",
                        line_range=[0],
                        code=f"{vuln_info.get('name')}@{vuln_info.get('version')}",
                        tool="npm-audit",
                        fix_suggestion=vuln_info.get("recommendation", "Update to the latest version")
                    )
                )

        # Update status based on results
        if issues:
            status[tool_name] = f"⚠️ Found {len(issues)} issues"
        else:
            status[tool_name] = "✅ No issues found"
            
        return issues, status, raw_output

    def _run_eslint(self, app_path: Path) -> Tuple[List[SecurityIssue], Dict[str, str], str]:
        """
        Run ESLint to check code quality and potential security issues.
        
        Args:
            app_path: Path to the frontend application
            
        Returns:
            Tuple containing:
            - List of security issues found
            - Dictionary of tool status messages
            - Raw output from the tool
        """
        tool_name = "eslint"
        issues: List[SecurityIssue] = []
        status = {tool_name: "⚠️ Not run"}
        
        # Check if we have frontend files to analyze
        has_files, _ = self._check_source_files(app_path)
        if not has_files:
            msg = f"No frontend files found in {app_path}"
            status[tool_name] = "❌ No files to analyze"
            return issues, status, msg

        # Determine what to scan - prefer src/ folder if it exists
        scan_dir = "src" if (app_path / "src").exists() else "."

        # Create temporary ESLint configuration for React/Modern JS
        eslint_config_path = None
        try:
            temp_dir = Path(tempfile.mkdtemp(prefix="eslint_config_"))
            eslint_config_path = temp_dir / ".eslintrc.json"
            
            # Create a basic configuration that handles React/JSX properly
            eslint_config = {
                "env": {
                    "browser": True,
                    "es2021": True,
                    "node": True
                },
                "extends": [
                    "eslint:recommended"
                ],
                "parserOptions": {
                    "ecmaVersion": "latest",
                    "sourceType": "module",
                    "ecmaFeatures": {
                        "jsx": True
                    }
                },
                "rules": {
                    "no-eval": "error",
                    "no-implied-eval": "error",
                    "no-alert": "warn"
                }
            }
            
            with open(eslint_config_path, "w") as f:
                json.dump(eslint_config, f, indent=2)
                
            logger.info(f"Created temporary ESLint config at {eslint_config_path}")
        except Exception as e:
            logger.warning(f"Failed to create temporary ESLint config: {e}")
            # We'll continue without a custom config if this fails

        # Build eslint command with appropriate options
        command = [
            cmd_name("npx"), "eslint",
            "--ext", ".js,.jsx,.ts,.tsx,.svelte,.vue",
            "--format", "json",
        ]
        
        # Check for custom configurations
        if (app_path / ".eslintrc.js").exists() or (app_path / ".eslintrc.json").exists():
            logger.info(f"Found custom ESLint configuration in {app_path}")
        elif eslint_config_path:
            # Use our temporary configuration
            command.extend(["--config", str(eslint_config_path)])
        else:
            # Use a basic configuration for common security rules
            command.extend(["--no-eslintrc", "--no-ignore"])
            
        # Add the scan directory
        command.append(scan_dir)

        logger.info(f"Running ESLint in {app_path} (scanning {scan_dir})...")
        try:
            proc = subprocess.run(
                command,
                cwd=str(app_path),
                capture_output=True,
                text=True,
                timeout=TOOL_TIMEOUT
            )
        except subprocess.TimeoutExpired:
            status[tool_name] = "❌ Timed out"
            return issues, status, "ESLint timed out"
        except Exception as exc:
            status[tool_name] = f"❌ Failed: {exc}"
            return issues, status, f"ESLint failed: {exc}"
        finally:
            # Clean up temporary directory
            if eslint_config_path and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"Failed to remove temporary ESLint config directory: {e}")

        raw_output = proc.stdout.strip()
        if not raw_output:
            # If no output, possibly an error or no matching files
            err_msg = proc.stderr.strip() if proc.stderr else ""
            if err_msg:
                # Check for common setup issues
                if "no such file or directory" in err_msg.lower():
                    status[tool_name] = "❌ ESLint not installed"
                elif "eslint is not recognized" in err_msg.lower():
                    status[tool_name] = "❌ ESLint not in PATH"
                else:
                    status[tool_name] = "❌ ESLint error"
                return issues, status, err_msg
            return issues, status, "ESLint produced no output."

        # Try to parse the JSON output
        parsed = safe_json_loads(raw_output)
        if not parsed:
            status[tool_name] = "❌ Invalid JSON output"
            return issues, status, raw_output
            
        if not isinstance(parsed, list):
            status[tool_name] = "❌ Unexpected output format"
            return issues, status, raw_output

        # Process ESLint results
        for file_result in parsed:
            # Each file_result is a dict with "filePath" and "messages"
            file_path = file_result.get("filePath", "unknown")
            messages = file_result.get("messages", [])

            # Convert to relative path for better display
            try:
                rel_path = os.path.relpath(file_path, str(app_path))
            except ValueError:
                rel_path = file_path

            for msg in messages:
                # Check if this is a fatal parsing error
                is_fatal = msg.get("fatal", False)
                
                # Get line number and severity
                line_num = msg.get("line", 0)
                severity_value = msg.get("severity", 1)
                severity = "HIGH" if severity_value >= 2 or is_fatal else "MEDIUM"
                
                # Handle the case where ruleId is None (often happens with parsing errors)
                rule_id = "parsing_error" if is_fatal and msg.get("ruleId") is None else (msg.get("ruleId") or "unknown_rule")
                
                # Get the error message
                message = msg.get("message", "Unknown ESLint issue")
                
                # For parsing errors, include specific information
                if is_fatal:
                    issue_type = "parsing_error"
                    code_snippet = file_result.get("source", "No code snippet available")
                else:
                    # Normal linting errors
                    issue_type = rule_id
                    code_snippet = msg.get("source", "No code snippet available")
                
                # Check if this is a security-related issue
                security_patterns = ["security", "inject", "prototype", "csrf", "xss", "sanitize", 
                                    "escap", "auth", "unsafe", "exploit", "vuln"]
                
                # Convert to strings and check to avoid None.lower() error
                rule_id_str = str(rule_id).lower() if rule_id else ""
                message_str = str(message).lower() if message else ""
                
                for pattern in security_patterns:
                    if pattern in rule_id_str or pattern in message_str:
                        severity = "HIGH"  # Upgrade severity for security issues
                        break
                
                # Create and add the issue
                issues.append(
                    SecurityIssue(
                        filename=rel_path,
                        line_number=line_num,
                        issue_text=message,
                        severity=severity,
                        confidence="HIGH" if is_fatal else "MEDIUM",
                        issue_type=issue_type,
                        line_range=[line_num],
                        code=code_snippet or "No code available",
                        tool="eslint",
                        fix_suggestion=str(msg.get("fix", {}).get("text", "")) if "fix" in msg else None
                    )
                )

        # Update status based on results
        if issues:
            status[tool_name] = f"⚠️ Found {len(issues)} issues"
        else:
            status[tool_name] = "✅ No issues found"
            
        return issues, status, raw_output

    def _run_retire_js(self, app_path: Path) -> Tuple[List[SecurityIssue], Dict[str, str], str]:
        """
        Run retire.js to detect known vulnerable libraries.
        
        Args:
            app_path: Path to the frontend application
            
        Returns:
            Tuple containing:
            - List of security issues found
            - Dictionary of tool status messages
            - Raw output from the tool
        """
        tool_name = "retire-js"
        issues: List[SecurityIssue] = []
        status = {tool_name: "⚠️ Not run"}
        
        if not (app_path / "node_modules").exists():
            msg = f"No node_modules found in {app_path}. Skipping retire.js."
            logger.warning(msg)
            status[tool_name] = "❌ No node_modules directory"
            return issues, status, msg

        command = [
            cmd_name("npx"), "retire",
            "--path", ".",
            "--outputformat", "json"
        ]

        logger.info(f"Running retire.js in {app_path}...")
        try:
            proc = subprocess.run(
                command,
                cwd=str(app_path),
                capture_output=True,
                text=True,
                timeout=TOOL_TIMEOUT
            )
        except subprocess.TimeoutExpired:
            status[tool_name] = "❌ Timed out"
            return issues, status, "retire.js timed out"
        except Exception as exc:
            status[tool_name] = f"❌ Failed: {exc}"
            return issues, status, f"retire.js failed: {exc}"

        raw_output = proc.stdout.strip()
        if not raw_output:
            err_msg = proc.stderr.strip() if proc.stderr else ""
            status[tool_name] = "❌ No output" if not err_msg else "❌ Error"
            return issues, status, err_msg or "retire.js produced no output"

        retire_data = safe_json_loads(raw_output)
        if not retire_data:
            status[tool_name] = "❌ Invalid JSON output"
            return issues, status, raw_output
            
        if "results" not in retire_data:
            status[tool_name] = "✅ No vulnerabilities found"
            return issues, status, raw_output

        # Process vulnerabilities
        for result_item in retire_data.get("results", []):
            vulnerabilities = result_item.get("vulnerabilities", [])
            if not vulnerabilities:
                continue

            file_name = result_item.get("file", "unknown_file")
            component = result_item.get("component", "unknown_component")
            version = result_item.get("version", "unknown_version")

            # Make file path relative
            try:
                rel_file = os.path.relpath(file_name, str(app_path))
            except ValueError:
                rel_file = file_name

            for vuln in vulnerabilities:
                # Get vulnerability info
                info_list = vuln.get("info", [])
                info_text = info_list[0] if isinstance(info_list, list) and info_list else "No vulnerability info"
                
                # Create issue
                issues.append(
                    SecurityIssue(
                        filename=rel_file,
                        line_number=0,
                        issue_text=info_text,
                        severity="HIGH",  # Retire.js vulnerabilities are typically high
                        confidence="HIGH",
                        issue_type="known_vulnerability",
                        line_range=[0],
                        code=f"{component}@{version}",
                        tool="retire-js",
                        fix_suggestion=f"Update to version {vuln.get('below', 'latest')} or newer"
                    )
                )

        # Update status based on results
        if issues:
            status[tool_name] = f"⚠️ Found {len(issues)} issues"
        else:
            status[tool_name] = "✅ No issues found"
            
        return issues, status, raw_output

    def _run_snyk(self, app_path: Path) -> Tuple[List[SecurityIssue], Dict[str, str], str]:
        """
        Run Snyk to detect vulnerabilities in dependencies.
        
        Args:
            app_path: Path to the frontend application
            
        Returns:
            Tuple containing:
            - List of security issues found
            - Dictionary of tool status messages
            - Raw output from the tool
        """
        tool_name = "snyk"
        issues: List[SecurityIssue] = []
        status = {tool_name: "⚠️ Not run"}
        
        if not (app_path / "package.json").exists():
            msg = f"No package.json found in {app_path}. Skipping Snyk."
            logger.warning(msg)
            status[tool_name] = "❌ No package.json"
            return issues, status, msg

        command = [cmd_name("snyk"), "test", "--json"]
        logger.info(f"Running Snyk in {app_path}...")
        try:
            proc = subprocess.run(
                command,
                cwd=str(app_path),
                capture_output=True,
                text=True,
                timeout=TOOL_TIMEOUT
            )
        except subprocess.TimeoutExpired:
            status[tool_name] = "❌ Timed out"
            return issues, status, "Snyk timed out"
        except Exception as exc:
            status[tool_name] = f"❌ Failed: {exc}"
            return issues, status, f"Snyk failed: {exc}"

        raw_output = proc.stdout.strip()
        
        # Check for authentication errors
        if raw_output and ("Authentication error" in raw_output or "Auth token" in raw_output):
            msg = "Snyk authentication required. Run 'snyk auth' first."
            logger.error(msg)
            status[tool_name] = "❌ Authentication required"
            return issues, status, msg

        if not raw_output:
            err_msg = proc.stderr.strip() if proc.stderr else ""
            status[tool_name] = "❌ No output" if not err_msg else "❌ Error"
            return issues, status, err_msg or "Snyk produced no output."

        # Try to parse the JSON output
        snyk_data = safe_json_loads(raw_output)
        if not snyk_data:
            # Check for test success message
            if "Tested" in raw_output and "No vulnerable paths found." in raw_output:
                status[tool_name] = "✅ No issues found"
                return issues, status, raw_output
            status[tool_name] = "❌ Invalid JSON output"
            return issues, status, raw_output
            
        # Check for vulnerabilities
        vulnerabilities = snyk_data.get("vulnerabilities", [])
        if not vulnerabilities:
            status[tool_name] = "✅ No vulnerabilities found"
            return issues, status, raw_output

        # Process vulnerabilities
        for vuln in vulnerabilities:
            severity = SEVERITY_MAP.get(vuln.get("severity", "low"), "LOW")
            # Try to get useful information about the vulnerability
            from_chain = vuln.get("from", ["unknown"])
            filename = from_chain[0] if from_chain else "unknown_dependency"

            # Get fix suggestion if available
            upgrade_paths = vuln.get("upgradePath", [])
            fix_suggestion = upgrade_paths[0] if upgrade_paths else "No direct upgrade"

            # Create the issue
            issues.append(
                SecurityIssue(
                    filename=filename,
                    line_number=0,
                    issue_text=vuln.get("title", "Unknown vulnerability"),
                    severity=severity,
                    confidence="HIGH",
                    issue_type="snyk_vulnerability",
                    line_range=[0],
                    code=f"{vuln.get('package')}@{vuln.get('version')}",
                    tool="snyk",
                    fix_suggestion=str(fix_suggestion)
                )
            )

        # Update status based on results
        if issues:
            status[tool_name] = f"⚠️ Found {len(issues)} issues"
        else:
            status[tool_name] = "✅ No issues found"
            
        return issues, status, raw_output

    def run_security_analysis(
        self,
        model: str,
        app_num: int,
        use_all_tools: bool = False
    ) -> Tuple[List[SecurityIssue], Dict[str, str], Dict[str, str]]:
        """
        Run the frontend security analysis.
        
        Args:
            model: Model identifier (e.g., 'Llama', 'GPT4o')
            app_num: Application number (e.g., 1, 2, 3)
            use_all_tools: Whether to run all available tools
            
        Returns:
            Tuple containing:
            - List of security issues found
            - Dictionary of tool status messages
            - Dictionary of raw tool outputs
        """
        logger.info(f"Running frontend security analysis for {model}/app{app_num} (full scan: {use_all_tools})")
        
        # Find the application path
        app_path = self._find_application_path(model, app_num)
        if not app_path.exists():
            msg = f"Application directory not found: {app_path}"
            logger.error(msg)
            return [], {t: f"❌ {msg}" for t in self.all_tools}, {t: msg for t in self.all_tools}

        # Check if the directory has frontend files
        has_files, _ = self._check_source_files(app_path)
        if not has_files:
            msg = f"No frontend files found in {app_path}"
            logger.warning(msg)
            return [], {t: f"❌ {msg}" for t in self.all_tools}, {t: msg for t in self.all_tools}

        # Determine which tools to run
        tools_to_run = self.all_tools if use_all_tools else self.default_tools
        
        # Filter out unavailable tools
        tools_to_run = [t for t in tools_to_run if self.available_tools.get(t, False)]
        logger.info(f"Running tools: {', '.join(tools_to_run)}")
        
        # Map tool names to their runner functions
        tool_map = {
            "npm-audit": self._run_npm_audit,
            "eslint": self._run_eslint,
            "retire-js": self._run_retire_js,
            "snyk": self._run_snyk
        }

        all_issues: List[SecurityIssue] = []
        tool_status: Dict[str, str] = {}
        tool_outputs: Dict[str, str] = {}

        # Run each selected tool in parallel for efficiency
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(tools_to_run), 4)) as executor:
            # Start all tool executions
            future_to_tool = {
                executor.submit(tool_map[tool], app_path): tool
                for tool in tools_to_run if tool in tool_map
            }

            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_tool):
                tool_name = future_to_tool[future]
                try:
                    issues, status_dict, output = future.result()
                    # Add issues to the master list
                    all_issues.extend(issues)
                    # Store the output for reference
                    tool_outputs[tool_name] = output
                    # Update the status
                    tool_status.update(status_dict)
                    
                    logger.info(f"Tool {tool_name} completed with {len(issues)} issues")
                except Exception as exc:
                    error_msg = f"❌ Error running {tool_name}: {exc}"
                    logger.error(error_msg)
                    tool_status[tool_name] = error_msg
                    tool_outputs[tool_name] = str(exc)

        # Mark tools that were not run
        for tool_name in self.all_tools:
            if tool_name not in tool_status:
                if not self.available_tools.get(tool_name, False):
                    tool_status[tool_name] = "❌ Not available on this system"
                    tool_outputs[tool_name] = f"{tool_name} not available"
                else:
                    tool_status[tool_name] = "⏸️ Not run in quick scan mode"
                    tool_outputs[tool_name] = "Tool not run"

        # Sort issues by severity (HIGH->MEDIUM->LOW), confidence, then filename/line
        severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        confidence_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

        sorted_issues = sorted(
            all_issues,
            key=lambda i: (
                severity_order.get(i.severity, 99),
                confidence_order.get(i.confidence, 99),
                i.filename,
                i.line_number
            )
        )

        logger.info(f"Frontend security analysis completed with {len(sorted_issues)} total issues")
        return sorted_issues, tool_status, tool_outputs

    # For compatibility with existing code that might call this method
    def analyze_security(self, model: str, app_num: int, use_all_tools: bool = False):
        """Alias for run_security_analysis for backward compatibility"""
        return self.run_security_analysis(model, app_num, use_all_tools)

    def get_analysis_summary(self, issues: List[SecurityIssue]) -> Dict[str, Any]:
        """
        Generate summary statistics for the analysis results.
        
        Args:
            issues: List of security issues found
            
        Returns:
            Dictionary containing summary statistics including:
            - Total number of issues
            - Counts by severity
            - Counts by confidence
            - Number of affected files
            - Counts by issue type
            - Counts by tool
            - Scan timestamp
        """
        if not issues:
            return {
                "total_issues": 0,
                "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
                "confidence_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
                "files_affected": 0,
                "issue_types": {},
                "tool_counts": {},
                "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        # Initialize the summary structure
        summary = {
            "total_issues": len(issues),
            "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "confidence_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "files_affected": len({issue.filename for issue in issues}),
            "issue_types": {},
            "tool_counts": {},
            "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Count by various metrics
        for issue in issues:
            # Count by severity
            summary["severity_counts"][issue.severity] += 1
            # Count by confidence
            summary["confidence_counts"][issue.confidence] += 1
            # Count by issue type
            summary["issue_types"][issue.issue_type] = summary["issue_types"].get(issue.issue_type, 0) + 1
            # Count by tool
            summary["tool_counts"][issue.tool] = summary["tool_counts"].get(issue.tool, 0) + 1

        return summary