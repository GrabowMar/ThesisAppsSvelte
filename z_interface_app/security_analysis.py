"""
security_analysis.py - Optimized Security Analysis Module

Combines multiple security scanning tools with concurrent execution
"""

import json
import os
import re
import subprocess
import concurrent.futures
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Dict
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Define a data class for security issues.
@dataclass
class SecurityIssue:
    filename: str
    line_number: int
    issue_text: str
    severity: str
    confidence: str
    issue_type: str
    line_range: List[int]
    code: str
    tool: str

TOOL_TIMEOUT = 30  # Timeout in seconds for each tool

class SecurityAnalyzer:
    def __init__(self, base_path: Path):
        """
        base_path should point to the project root.
        For example, if your folder structure is:
        
          app/
            ChatGPT4o/
              app1/
                backend/   <-- contains your Python files
          backend/
        
        then base_path should be the path to 'app/'.
        """
        self.base_path = base_path
        self.default_tools = ["bandit"]  # Only run Bandit by default for speed
        self.all_tools = ["bandit", "safety", "pylint", "vulture"]

    def _check_python_files(self, directory: Path) -> Tuple[bool, List[str]]:
        """Check if directory contains Python files."""
        if not directory.exists():
            return False, []
        python_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        return bool(python_files), python_files

    def _run_bandit(self, app_path: Path) -> Tuple[List[SecurityIssue], str]:
        """Run Bandit security analysis and return issues and raw output."""
        try:
            result = subprocess.run(
                ["bandit", "-r", str(app_path), "-f", "json", "-ll", "-i"],
                capture_output=True,
                text=True,
                check=False,
                timeout=TOOL_TIMEOUT
            )
            raw_output = result.stdout
            if result.stderr and "ERROR" in result.stderr:
                logger.error(f"Bandit warning: {result.stderr}")
            analysis = json.loads(raw_output)
            issues = []
            for issue in analysis.get("results", []):
                issues.append(
                    SecurityIssue(
                        filename=issue["filename"].replace(str(app_path), "").lstrip('/\\'),
                        line_number=issue["line_number"],
                        issue_text=issue["issue_text"],
                        severity=issue["issue_severity"],
                        confidence=issue["issue_confidence"],
                        issue_type=issue["test_name"],
                        line_range=issue["line_range"],
                        code=issue.get("code", "Code not available"),
                        tool="Bandit"
                    )
                )
            return issues, raw_output
        except Exception as e:
            logger.error(f"Bandit error: {str(e)}")
            return [], f"Error: {str(e)}"

    def _run_safety(self, app_path: Path) -> Tuple[List[SecurityIssue], str]:
        """Check dependencies using Safety and return issues and raw output."""
        try:
            requirements_file = app_path / "requirements.txt"
            if not requirements_file.exists():
                return [], "No requirements.txt found."
            result = subprocess.run(
                ["safety", "check", "-r", str(requirements_file), "--json"],
                capture_output=True,
                text=True,
                check=False,
                timeout=TOOL_TIMEOUT
            )
            raw_output = result.stdout
            # If the output contains deprecation warnings or extra text, extract the JSON part.
            match = re.search(r'({.*)', raw_output, re.DOTALL)
            if match:
                raw_output = match.group(1)
            if not raw_output.strip():
                logger.error("Safety returned no output.")
                return [], "No vulnerabilities detected."
            try:
                vulnerabilities = json.loads(raw_output)
            except json.JSONDecodeError as je:
                logger.error(f"Safety JSON decode error: {je}. Output: {raw_output}")
                return [], f"JSON decode error: {raw_output}"
            issues = []
            for vuln in vulnerabilities:
                issues.append(
                    SecurityIssue(
                        filename="requirements.txt",
                        line_number=0,
                        issue_text=f"Vulnerable package {vuln['package']}: {vuln.get('description', 'No description')}",
                        severity="HIGH" if vuln.get('severity', '').upper() == 'HIGH' else "MEDIUM",
                        confidence="HIGH",
                        issue_type="dependency_vulnerability",
                        line_range=[0],
                        code=f"{vuln['package']}=={vuln.get('installed_version', 'unknown')}",
                        tool="Safety"
                    )
                )
            return issues, raw_output
        except Exception as e:
            logger.error(f"Safety error: {str(e)}")
            return [], f"Error: {str(e)}"

    def _run_pylint(self, app_path: Path) -> Tuple[List[SecurityIssue], str]:
        """Run Pylint for code quality issues and return issues and raw output."""
        try:
            result = subprocess.run(
                ["pylint", "--output-format=json", str(app_path)],
                capture_output=True,
                text=True,
                check=False,
                timeout=TOOL_TIMEOUT
            )
            raw_output = result.stdout
            issues_json = json.loads(raw_output)
            issues = []
            severity_map = {
                "E": "HIGH",
                "W": "MEDIUM",
                "C": "LOW",
                "R": "LOW"
            }
            # Include all pylint messages.
            for issue in issues_json:
                issues.append(
                    SecurityIssue(
                        filename=issue["path"].replace(str(app_path), "").lstrip('/\\'),
                        line_number=issue["line"],
                        issue_text=issue["message"],
                        severity=severity_map.get(issue["type"], "LOW"),
                        confidence="MEDIUM",
                        issue_type=f"pylint_{issue['symbol']}",
                        line_range=[issue["line"]],
                        code=issue.get("message-id", "No code available"),
                        tool="Pylint"
                    )
                )
            return issues, raw_output
        except Exception as e:
            logger.error(f"Pylint error: {str(e)}")
            return [], f"Error: {str(e)}"

    def _run_vulture(self, app_path: Path) -> Tuple[List[SecurityIssue], str]:
        """Run Vulture to find dead code and return issues and raw output."""
        try:
            result = subprocess.run(
                ["vulture", str(app_path), "--json"],
                capture_output=True,
                text=True,
                check=False,
                timeout=TOOL_TIMEOUT
            )
            raw_output = result.stdout
            if not raw_output.strip():
                logger.error("Vulture returned no output.")
                return [], "No dead code found."
            try:
                dead_code = json.loads(raw_output)
            except json.JSONDecodeError as je:
                logger.error(f"Vulture JSON decode error: {je}. Output: {raw_output}")
                return [], f"JSON decode error: {raw_output}"
            issues = []
            for item in dead_code:
                issues.append(
                    SecurityIssue(
                        filename=item["filename"].replace(str(app_path), "").lstrip('/\\'),
                        line_number=item["first_lineno"],
                        issue_text=f"Unused {item['type']}: Could indicate unnecessary exposed code",
                        severity="LOW",
                        confidence="MEDIUM",
                        issue_type="dead_code",
                        line_range=[item["first_lineno"]],
                        code=str(item.get("size", "No code available")),
                        tool="Vulture"
                    )
                )
            return issues, raw_output
        except Exception as e:
            logger.error(f"Vulture error: {str(e)}")
            return [], f"Error: {str(e)}"

    def run_bandit_analysis(
        self, model: str, app_num: int, use_all_tools: bool = False
    ) -> Tuple[List[SecurityIssue], Dict[str, str], Dict[str, str]]:
        """
        Run a comprehensive security analysis on the backend code.

        Expected directory structure:
            <base_path>/<model>/app<app_num>/backend
            (contains Python files)

        Returns a tuple containing:
          - A sorted list of SecurityIssue objects.
          - A dictionary (tool_status) mapping each tool to a one-line status summary.
          - A dictionary (tool_output_details) mapping each tool to its full raw text output.
        
        Raises:
          ValueError: If no Python files are found in the expected location.
        """
        app_path = self.base_path / f"{model}/app{app_num}/backend"
        has_files, _ = self._check_python_files(app_path)
        if not has_files:
            raise ValueError(
                f"No Python files found in {app_path}. "
                "Please ensure the backend directory exists and contains Python files."
            )
        tools_to_run = self.all_tools if use_all_tools else self.default_tools
        tool_map = {
            "bandit": lambda: self._run_bandit(app_path),
            "safety": lambda: self._run_safety(app_path),
            "pylint": lambda: self._run_pylint(app_path),
            "vulture": lambda: self._run_vulture(app_path)
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
                    tool_status[tool] = "✅ No issues found" if not issues else f"⚠️ Found {len(issues)} issues"
                    tool_output_details[tool] = raw_output
                except Exception as e:
                    tool_status[tool] = f"❌ Error: {str(e)}"
                    tool_output_details[tool] = f"Error: {str(e)}"
                    logger.error(f"{tool} failed: {str(e)}")
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

    def get_analysis_summary(self, issues: List[SecurityIssue]) -> dict:
        """Generate a detailed summary of security issues."""
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
