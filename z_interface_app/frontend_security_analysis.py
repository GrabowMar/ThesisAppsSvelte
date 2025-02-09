"""
frontend_security_analysis.py - Frontend Security Analysis Module

Combines multiple security scanning tools for SvelteKit/Frontend code:
- snyk for dependency vulnerabilities
- npm audit for package security
- eslint for code quality and Svelte-specific linting via eslint-plugin-svelte
- retire.js for known vulnerable JavaScript libraries
"""

import json
import os
import subprocess
import concurrent.futures
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from datetime import datetime

# Setup logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def cmd_name(name: str) -> str:
    """Return the proper command name for Windows if needed."""
    return f"{name}.cmd" if os.name == "nt" else name

@dataclass
class FrontendSecurityIssue:
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

class FrontendSecurityAnalyzer:
    def __init__(self, base_path: Path):
        """
        base_path should point to the project root.
        For example, if your folder structure is:
        
        app/
          ChatGPT4o/
            app1/
              frontend/
                src/
          backend/
        
        then base_path should be the path to 'app/'.
        """
        self.base_path = base_path
        self.default_tools = ["npm-audit"]  # Quick scan tool
        self.all_tools = ["npm-audit", "eslint", "retire-js", "snyk"]
        self.TOOL_TIMEOUT = 30  # seconds

    def _check_frontend_files(self, directory: Path) -> Tuple[bool, List[str]]:
        """Check if directory contains frontend files."""
        if not directory.exists():
            return False, []
        js_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.js', '.ts', '.svelte')):
                    js_files.append(os.path.join(root, file))
        return bool(js_files), js_files

    def _run_npm_audit(self, app_path: Path) -> Tuple[List[FrontendSecurityIssue], str]:
        """Run npm audit for dependency vulnerabilities."""
        try:
            command = [cmd_name("npm"), "audit", "--json"]
            result = subprocess.run(
                command,
                cwd=str(app_path),
                capture_output=True,
                text=True,
                timeout=self.TOOL_TIMEOUT
            )
            raw_output = result.stdout
            if result.stderr and "ERR!" in result.stderr:
                logger.error(f"npm audit warning: {result.stderr}")
                return ([], result.stderr)
            if not raw_output.strip():
                logger.error("npm audit returned no output.")
                return ([], "No output")
            audit_data = json.loads(raw_output)
            issues = []
            for vuln in audit_data.get("vulnerabilities", {}).values():
                severity_map = {
                    "critical": "HIGH",
                    "high": "HIGH",
                    "moderate": "MEDIUM",
                    "low": "LOW"
                }
                issues.append(
                    FrontendSecurityIssue(
                        filename="package.json",
                        line_number=0,
                        issue_text=vuln.get("title", "Unknown vulnerability"),
                        severity=severity_map.get(vuln.get("severity", "low"), "LOW"),
                        confidence="HIGH",
                        issue_type="dependency_vulnerability",
                        line_range=[0],
                        code=f"{vuln.get('name')}@{vuln.get('version')}",
                        tool="npm-audit",
                        fix_suggestion=vuln.get("recommendation", "No fix available")
                    )
                )
            return (issues, raw_output)
        except Exception as e:
            logger.error(f"npm audit error: {str(e)}")
            return ([], f"Error: {str(e)}")

    def _run_eslint_security(self, app_path: Path) -> Tuple[List[FrontendSecurityIssue], str]:
        """Run ESLint using the Svelte plugin for Svelte/JS files."""
        try:
            # Use eslint-plugin-svelte as documented at https://sveltejs.github.io/eslint-plugin-svelte/
            command = [
                cmd_name("npx"), "eslint",
                "--plugin", "svelte",
                "--ext", ".js,.svelte",
                "--format", "json",
                "src/"
            ]
            result = subprocess.run(
                command,
                cwd=str(app_path),
                capture_output=True,
                text=True,
                timeout=self.TOOL_TIMEOUT
            )
            raw_output = result.stdout
            if not raw_output.strip():
                logger.error("ESLint returned no output.")
                return ([], "No output")
            try:
                eslint_data = json.loads(raw_output)
            except json.JSONDecodeError as je:
                logger.error(f"ESLint error: {je}. Output: {raw_output}")
                return ([], f"JSON decode error: {raw_output}")
            issues = []
            # Process messages; only include errors (severity 2) for now.
            for file_result in eslint_data:
                for message in file_result.get("messages", []):
                    if message.get("severity", 1) < 2:
                        continue
                    issues.append(
                        FrontendSecurityIssue(
                            filename=file_result["filePath"].replace(str(app_path), "").lstrip('/\\'),
                            line_number=message.get("line", 0),
                            issue_text=message.get("message", "Unknown issue"),
                            severity="HIGH" if message.get("severity") == 2 else "MEDIUM",
                            confidence="MEDIUM",
                            issue_type=message.get("ruleId", "unknown"),
                            line_range=[message.get("line", 0)],
                            code=message.get("source", "Code not available"),
                            tool="eslint-svelte",
                            fix_suggestion=message.get("fix", {}).get("text")
                        )
                    )
            return (issues, raw_output)
        except Exception as e:
            logger.error(f"ESLint error: {str(e)}")
            return ([], f"Error: {str(e)}")

    def _run_retire_js(self, app_path: Path) -> Tuple[List[FrontendSecurityIssue], str]:
        """Run retire.js to find known vulnerable JavaScript libraries."""
        try:
            command = [cmd_name("npx"), "retire", "--path", ".", "--outputformat", "json"]
            result = subprocess.run(
                command,
                cwd=str(app_path),
                capture_output=True,
                text=True,
                timeout=self.TOOL_TIMEOUT
            )
            raw_output = result.stdout
            if not raw_output.strip():
                logger.error("retire.js returned no output.")
                return ([], "No output")
            try:
                retire_data = json.loads(raw_output)
            except json.JSONDecodeError as je:
                logger.error(f"retire.js error: {je}. Output: {raw_output}")
                return ([], f"JSON decode error: {raw_output}")
            issues = []
            for result_item in retire_data.get("results", []):
                for vuln in result_item.get("vulnerabilities", []):
                    issues.append(
                        FrontendSecurityIssue(
                            filename=result_item.get("file", "unknown"),
                            line_number=0,
                            issue_text=vuln.get("info", ["No description"])[0],
                            severity="HIGH",
                            confidence="HIGH",
                            issue_type="known_vulnerability",
                            line_range=[0],
                            code=f"{result_item.get('component')}@{result_item.get('version')}",
                            tool="retire-js",
                            fix_suggestion=f"Update to version {vuln.get('below', 'latest')}"
                        )
                    )
            return (issues, raw_output)
        except Exception as e:
            logger.error(f"retire.js error: {str(e)}")
            return ([], f"Error: {str(e)}")

    def _run_snyk(self, app_path: Path) -> Tuple[List[FrontendSecurityIssue], str]:
        """Run Snyk for dependency and code analysis."""
        try:
            command = [cmd_name("snyk"), "test", "--json"]
            result = subprocess.run(
                command,
                cwd=str(app_path),
                capture_output=True,
                text=True,
                timeout=self.TOOL_TIMEOUT
            )
            raw_output = result.stdout
            if not raw_output.strip():
                logger.error("Snyk returned no output.")
                return ([], "No output")
            if "Authentication error" in raw_output:
                logger.error("Snyk authentication error detected. Please run 'snyk auth' to authenticate.")
                return ([], "Authentication error. Run 'snyk auth'.")
            try:
                snyk_data = json.loads(raw_output)
            except json.JSONDecodeError as je:
                logger.error(f"Snyk error: {je}. Output: {raw_output}")
                return ([], f"JSON decode error: {raw_output}")
            issues = []
            for vuln in snyk_data.get("vulnerabilities", []):
                severity_map = {
                    "critical": "HIGH",
                    "high": "HIGH",
                    "medium": "MEDIUM",
                    "low": "LOW"
                }
                issues.append(
                    FrontendSecurityIssue(
                        filename=vuln.get("from", ["unknown"])[0],
                        line_number=0,
                        issue_text=vuln.get("title", "Unknown vulnerability"),
                        severity=severity_map.get(vuln.get("severity", "low"), "LOW"),
                        confidence="HIGH",
                        issue_type="snyk_vulnerability",
                        line_range=[0],
                        code=f"{vuln.get('package')}@{vuln.get('version')}",
                        tool="snyk",
                        fix_suggestion=vuln.get("upgradePath", ["No direct upgrade"])[0]
                    )
                )
            return (issues, raw_output)
        except Exception as e:
            logger.error(f"Snyk error: {str(e)}")
            return ([], f"Error: {str(e)}")

    def run_security_analysis(
        self, model: str, app_num: int, use_all_tools: bool = False
    ) -> Tuple[List[FrontendSecurityIssue], Dict[str, str], Dict[str, str]]:
        """
        Run a comprehensive security analysis on the frontend code.

        Expected directory structure:
            <base_path>/<model>/app<app_num>/frontend
                └── src/  (contains JS/TS/Svelte files)

        Returns:
            A tuple containing:
              - A sorted list of FrontendSecurityIssue objects.
              - A dictionary (tool_status) mapping each tool to a one-line status summary.
              - A dictionary (tool_output_details) mapping each tool to its full raw text output.

        Raises:
            ValueError: If no frontend files are found in the expected location.
        """
        app_path = self.base_path / f"{model}/app{app_num}/frontend"
        has_files, _ = self._check_frontend_files(app_path / "src")
        if not has_files:
            raise ValueError(
                f"No frontend files found in {(app_path / 'src')}. "
                "Please ensure the 'frontend/src' directory exists and contains JS/TS/Svelte files."
            )
        tools_to_run = self.all_tools if use_all_tools else self.default_tools
        tool_map = {
            "npm-audit": lambda: self._run_npm_audit(app_path),
            "eslint": lambda: self._run_eslint_security(app_path),
            "retire-js": lambda: self._run_retire_js(app_path),
            "snyk": lambda: self._run_snyk(app_path)
        }
        all_issues = []
        tool_status: Dict[str, str] = {}
        tool_output_details: Dict[str, str] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(tools_to_run)) as executor:
            future_to_tool = {
                executor.submit(tool_map[tool]): tool
                for tool in tools_to_run if tool in tool_map
            }
            for future in concurrent.futures.as_completed(future_to_tool):
                tool = future_to_tool[future]
                try:
                    issues, raw_output = future.result()
                    all_issues.extend(issues)
                    tool_output_details[tool] = raw_output
                    tool_status[tool] = "✅ No issues found" if not issues else f"⚠️ Found {len(issues)} issues"
                except Exception as e:
                    tool_status[tool] = f"❌ Error: {str(e)}"
                    tool_output_details[tool] = f"Error: {str(e)}"
        for tool in self.all_tools:
            if tool not in tool_status:
                tool_status[tool] = "⏸️ Not run in quick scan mode"
        sorted_issues = sorted(
            all_issues,
            key=lambda x: (
                {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(x.severity, 3),
                {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(x.confidence, 3),
                x.filename,
                x.line_number
            )
        )
        return sorted_issues, tool_status, tool_output_details

    def get_analysis_summary(self, issues: List[FrontendSecurityIssue]) -> dict:
        """Generate a detailed summary of frontend security issues."""
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
            "files_affected": len(set(issue.filename for issue in issues)),
            "issue_types": {},
            "tool_counts": {},
            "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        for issue in issues:
            summary["severity_counts"][issue.severity] += 1
            summary["confidence_counts"][issue.confidence] += 1
            summary["issue_types"][issue.issue_type] = summary["issue_types"].get(issue.issue_type, 0) + 1
            summary["tool_counts"][issue.tool] = summary["tool_counts"].get(issue.tool, 0) + 1
        return summary
