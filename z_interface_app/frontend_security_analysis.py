#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Frontend Security Analysis Module (Rewritten)

Provides security scanning for frontend code using multiple tools:
- npm audit for dependency vulnerabilities
- ESLint for code quality and potential React or Svelte linting
- retire.js for known vulnerable JavaScript libraries
- snyk for additional security checks

This rewritten version aims to simplify path detection, improve logging,
and handle common edge cases more gracefully.
"""

import os
import json
import subprocess
import logging
import concurrent.futures
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Dict

# -----------------------------------------------------------------------------
# Logging Configuration
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
TOOL_TIMEOUT = 30  # seconds
SEVERITY_MAP = {
    "critical": "HIGH",
    "high": "HIGH",
    "moderate": "MEDIUM",
    "medium": "MEDIUM",
    "low": "LOW"
}

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def cmd_name(name: str) -> str:
    """
    Return the proper command name for Windows if needed.
    For example, "npm" -> "npm.cmd" on Windows.
    """
    return f"{name}.cmd" if os.name == "nt" else name

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

# -----------------------------------------------------------------------------
# Data Classes
# -----------------------------------------------------------------------------
@dataclass
class FrontendSecurityIssue:
    """
    Represents a security issue found in frontend code.
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

# -----------------------------------------------------------------------------
# Main Analyzer Class
# -----------------------------------------------------------------------------
class FrontendSecurityAnalyzer:
    """
    Analyzes frontend code for security issues using multiple tools:
    - npm-audit
    - ESLint
    - retire.js
    - Snyk
    """

    def __init__(self, base_path: Path):
        """
        :param base_path: The root directory where the frontend code resides.
        """
        self.base_path = base_path.resolve()
        # Default quick-scan tools vs. full-scan
        self.default_tools = ["eslint"]
        self.all_tools = ["npm-audit", "eslint", "retire-js", "snyk"]

    # -------------------------------------------------------------------------
    # Path Detection
    # -------------------------------------------------------------------------
    def _find_application_path(self, model: str, app_num: int) -> Path:
        """
        Attempt to locate the frontend application path. Checks several
        common paths in order of preference, then falls back to base_path.
        """

        # 1) Potentially check 'model/app{num}/frontend'
        candidate = self.base_path / model / f"app{app_num}" / "frontend"
        if candidate.exists() and candidate.is_dir():
            logger.info(f"Using frontend directory: {candidate}")
            return candidate.resolve()

        # 2) Potentially check 'model/app{num}'
        candidate = self.base_path / model / f"app{app_num}"
        if candidate.exists() and candidate.is_dir():
            logger.info(f"Using app directory: {candidate}")
            return candidate.resolve()

        # 3) Check 'z_interface_app' (if it exists)
        candidate = self.base_path / "z_interface_app"
        if candidate.exists() and candidate.is_dir():
            logger.info(f"Using z_interface_app directory: {candidate}")
            return candidate.resolve()

        # 4) Fallback to base_path
        logger.warning("No specific frontend path found; using base_path.")
        return self.base_path

    def _check_source_files(self, directory: Path) -> Tuple[bool, List[str]]:
        """
        Check if the directory contains any typical frontend source files.

        :param directory: Path to the directory to scan.
        :return: (bool, list_of_files)
                 bool indicates whether any source files were found.
        """
        if not directory.exists() or not directory.is_dir():
            return False, []

        exts = (".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte")
        found_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(exts):
                    found_files.append(os.path.join(root, file))

        return bool(found_files), found_files

    # -------------------------------------------------------------------------
    # Individual Tool Runners
    # -------------------------------------------------------------------------
    def _run_npm_audit(self, app_path: Path) -> Tuple[List[FrontendSecurityIssue], str]:
        """
        Run `npm audit --json` to check for dependency vulnerabilities.
        """
        if not (app_path / "package.json").exists():
            msg = f"No package.json found in {app_path}. Skipping npm audit."
            logger.warning(msg)
            return [], msg

        # Attempt to ensure package-lock.json exists
        if not (app_path / "package-lock.json").exists():
            try:
                logger.info("No package-lock.json found; generating one via `npm i --package-lock-only`.")
                init_cmd = [cmd_name("npm"), "i", "--package-lock-only"]
                subprocess.run(init_cmd, cwd=str(app_path), capture_output=True, text=True, timeout=TOOL_TIMEOUT)
            except Exception as exc:
                msg = f"Failed to generate package-lock.json: {exc}"
                logger.warning(msg)
                return [], msg

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
            return [], "npm audit timed out"
        except Exception as exc:
            return [], f"npm audit failed: {exc}"

        if proc.returncode != 0 and proc.stderr and "ERR!" in proc.stderr:
            msg = f"npm audit error: {proc.stderr}"
            logger.error(msg)
            return [], msg

        raw_output = proc.stdout.strip()
        if not raw_output:
            # If stdout empty, check stderr
            msg = proc.stderr.strip() or "npm audit produced no output"
            return [], msg

        audit_data = safe_json_loads(raw_output)
        if not audit_data or "vulnerabilities" not in audit_data:
            return [], raw_output if raw_output else "No vulnerabilities found"

        issues = []
        for vuln_name, vuln_info in audit_data["vulnerabilities"].items():
            severity = SEVERITY_MAP.get(vuln_info.get("severity", "low"), "LOW")
            issues.append(
                FrontendSecurityIssue(
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

        return issues, raw_output

    def _run_eslint(self, app_path: Path) -> Tuple[List[FrontendSecurityIssue], str]:
        """
        Run ESLint to check code quality and potential security issues.
        Adjust plugin usage for React/Svelte as needed.
        """
        # If there's a src/ folder, scan it; else scan current directory
        scan_dir = "src" if (app_path / "src").exists() else "."

        command = [
            cmd_name("npx"), "eslint",
            # Remove old/unsupported flags if using ESLint Flat Config
            "--ext", ".js,.jsx,.ts,.tsx,.svelte,.vue",
            "--format", "json",
            scan_dir
        ]

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
            return [], "ESLint timed out"
        except Exception as exc:
            return [], f"ESLint failed: {exc}"

        raw_output = proc.stdout.strip()
        if not raw_output:
            # If no output, possibly an error or no matching files
            msg = proc.stderr.strip() or "ESLint produced no output."
            return [], msg

        parsed = safe_json_loads(raw_output)
        if not isinstance(parsed, list):
            # If ESLint didn't produce a list, might be invalid JSON or an error
            return [], raw_output

        issues = []
        for file_result in parsed:
            # Each file_result is a dict with "filePath" and "messages"
            file_path = file_result.get("filePath", "unknown")
            messages = file_result.get("messages", [])

            for msg in messages:
                # Only consider errors or high-severity warnings as "security" issues
                severity = "HIGH" if msg.get("severity", 1) == 2 else "MEDIUM"
                line_num = msg.get("line", 0)
                code_snippet = msg.get("source", "No code snippet available")
                rule_id = msg.get("ruleId", "unknown_rule")

                issues.append(
                    FrontendSecurityIssue(
                        filename=os.path.relpath(file_path, str(app_path)),
                        line_number=line_num,
                        issue_text=msg.get("message", "Unknown ESLint issue"),
                        severity=severity,
                        confidence="MEDIUM",
                        issue_type=rule_id,
                        line_range=[line_num],
                        code=code_snippet,
                        tool="eslint",
                        fix_suggestion=msg.get("fix", {}).get("text", None)
                    )
                )

        return issues, raw_output

    def _run_retire_js(self, app_path: Path) -> Tuple[List[FrontendSecurityIssue], str]:
        """
        Run retire.js to detect known vulnerable libraries in node_modules.
        """
        if not (app_path / "node_modules").exists():
            msg = f"No node_modules found in {app_path}. Skipping retire.js."
            logger.warning(msg)
            return [], msg

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
            return [], "retire.js timed out"
        except Exception as exc:
            return [], f"retire.js failed: {exc}"

        raw_output = proc.stdout.strip()
        if not raw_output:
            msg = proc.stderr.strip() or "retire.js produced no output"
            return [], msg

        retire_data = safe_json_loads(raw_output)
        if not retire_data or "results" not in retire_data:
            return [], raw_output

        issues = []
        for result_item in retire_data.get("results", []):
            if not result_item.get("vulnerabilities"):
                continue

            file_name = result_item.get("file", "unknown_file")
            component = result_item.get("component", "unknown_component")
            version = result_item.get("version", "unknown_version")

            for vuln in result_item["vulnerabilities"]:
                info_list = vuln.get("info", [])
                info_text = info_list[0] if isinstance(info_list, list) and info_list else "No vulnerability info"

                # Retire.js often flags these as high severity by default
                issues.append(
                    FrontendSecurityIssue(
                        filename=file_name,
                        line_number=0,
                        issue_text=info_text,
                        severity="HIGH",
                        confidence="HIGH",
                        issue_type="known_vulnerability",
                        line_range=[0],
                        code=f"{component}@{version}",
                        tool="retire-js",
                        fix_suggestion=f"Update to version {vuln.get('below', 'latest')}"
                    )
                )

        return issues, raw_output

    def _run_snyk(self, app_path: Path) -> Tuple[List[FrontendSecurityIssue], str]:
        """
        Run Snyk to detect vulnerabilities in dependencies.
        """
        if not (app_path / "package.json").exists():
            msg = f"No package.json found in {app_path}. Skipping Snyk."
            logger.warning(msg)
            return [], msg

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
            return [], "Snyk timed out"
        except Exception as exc:
            return [], f"Snyk failed: {exc}"

        raw_output = proc.stdout.strip()
        if "Authentication error" in raw_output:
            msg = "Snyk authentication required. Run 'snyk auth' first."
            logger.error(msg)
            return [], msg

        if not raw_output:
            msg = proc.stderr.strip() or "Snyk produced no output."
            return [], msg

        snyk_data = safe_json_loads(raw_output)
        if not snyk_data or "vulnerabilities" not in snyk_data:
            return [], raw_output

        issues = []
        for vuln in snyk_data["vulnerabilities"]:
            severity = SEVERITY_MAP.get(vuln.get("severity", "low"), "LOW")
            from_chain = vuln.get("from", ["unknown"])
            filename = from_chain[0] if from_chain else "unknown_dependency"

            upgrade_paths = vuln.get("upgradePath", [])
            fix_suggestion = upgrade_paths[0] if upgrade_paths else "No direct upgrade"

            issues.append(
                FrontendSecurityIssue(
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

        return issues, raw_output

    # -------------------------------------------------------------------------
    # Main Entry Point for Security Analysis
    # -------------------------------------------------------------------------
    def run_security_analysis(
        self,
        model: str,
        app_num: int,
        use_all_tools: bool = False
    ) -> Tuple[List[FrontendSecurityIssue], Dict[str, str], Dict[str, str]]:
        """
        Run the frontend security analysis.

        :param model: A model identifier (used in path detection).
        :param app_num: The application number (used in path detection).
        :param use_all_tools: Whether to run all tools or just a quick scan.
        :return: (list_of_issues, tool_status, tool_outputs)
                 - list_of_issues: All FrontendSecurityIssue objects found
                 - tool_status: A dict mapping each tool to a status message
                 - tool_outputs: A dict mapping each tool to its raw output (or errors)
        """
        app_path = self._find_application_path(model, app_num)
        if not app_path.exists():
            msg = f"Application directory not found: {app_path}"
            logger.error(msg)
            return [], {t: f"❌ {msg}" for t in self.all_tools}, {t: msg for t in self.all_tools}

        has_files, _ = self._check_source_files(app_path)
        if not has_files:
            msg = f"No frontend files found in {app_path}"
            logger.error(msg)
            return [], {t: f"❌ {msg}" for t in self.all_tools}, {t: msg for t in self.all_tools}

        tools_to_run = self.all_tools if use_all_tools else self.default_tools
        tool_map = {
            "npm-audit": self._run_npm_audit,
            "eslint": self._run_eslint,
            "retire-js": self._run_retire_js,
            "snyk": self._run_snyk
        }

        all_issues: List[FrontendSecurityIssue] = []
        tool_status: Dict[str, str] = {}
        tool_outputs: Dict[str, str] = {}

        # Run each selected tool in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(tools_to_run)) as executor:
            future_to_tool = {
                executor.submit(tool_map[tool], app_path): tool
                for tool in tools_to_run if tool in tool_map
            }

            for future in concurrent.futures.as_completed(future_to_tool):
                tool_name = future_to_tool[future]
                try:
                    issues, output = future.result()
                    all_issues.extend(issues)
                    tool_outputs[tool_name] = output

                    if not issues:
                        tool_status[tool_name] = "✅ No issues found"
                    else:
                        tool_status[tool_name] = f"⚠️ Found {len(issues)} issues"
                except Exception as exc:
                    error_msg = f"❌ Error running {tool_name}: {exc}"
                    logger.error(error_msg)
                    tool_status[tool_name] = error_msg
                    tool_outputs[tool_name] = error_msg

        # Mark tools that were not run
        for tool_name in self.all_tools:
            if tool_name not in tool_status:
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

        return sorted_issues, tool_status, tool_outputs

    # -------------------------------------------------------------------------
    # Summary Generation
    # -------------------------------------------------------------------------
    def get_analysis_summary(self, issues: List[FrontendSecurityIssue]) -> dict:
        """
        Generate summary statistics for the analysis results.

        :param issues: List of FrontendSecurityIssue objects.
        :return: A dictionary containing summary statistics.
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

        summary = {
            "total_issues": len(issues),
            "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "confidence_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "files_affected": len({iss.filename for iss in issues}),
            "issue_types": {},
            "tool_counts": {},
            "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        for issue in issues:
            # Count severity
            summary["severity_counts"][issue.severity] += 1
            # Count confidence
            summary["confidence_counts"][issue.confidence] += 1
            # Count issue types
            summary["issue_types"][issue.issue_type] = summary["issue_types"].get(issue.issue_type, 0) + 1
            # Count tool usage
            summary["tool_counts"][issue.tool] = summary["tool_counts"].get(issue.tool, 0) + 1

        return summary
