"""
security_analysis.py - Optimized Security Analysis Module
Combines multiple security scanning tools with concurrent execution
"""

import json
import os
import subprocess
import concurrent.futures
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from datetime import datetime


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

    def _run_bandit(self, app_path: Path) -> List[SecurityIssue]:
        """Run Bandit security analysis."""
        try:
            result = subprocess.run(
                [
                    "bandit",
                    "-r",
                    str(app_path),
                    "-f",
                    "json",
                    "-ll",
                    "-i",
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=TOOL_TIMEOUT
            )

            if result.stderr and "ERROR" in result.stderr:
                print(f"Bandit warning: {result.stderr}")
                return []

            analysis = json.loads(result.stdout)
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
            return issues
        except Exception as e:
            print(f"Bandit error: {str(e)}")
            return []

    def _run_safety(self, app_path: Path) -> List[SecurityIssue]:
        """Check dependencies for known vulnerabilities using Safety."""
        try:
            requirements_file = app_path / "requirements.txt"
            if not requirements_file.exists():
                return []

            result = subprocess.run(
                ["safety", "check", "-r", str(requirements_file), "--json"],
                capture_output=True,
                text=True,
                check=False,
                timeout=TOOL_TIMEOUT
            )

            vulnerabilities = json.loads(result.stdout)
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
            return issues
        except Exception as e:
            print(f"Safety error: {str(e)}")
            return []

    def _run_pylint(self, app_path: Path) -> List[SecurityIssue]:
        """Run Pylint for security-related code quality issues."""
        try:
            result = subprocess.run(
                ["pylint", "--output-format=json", str(app_path)],
                capture_output=True,
                text=True,
                check=False,
                timeout=TOOL_TIMEOUT
            )

            issues_json = json.loads(result.stdout)
            issues = []

            severity_map = {
                "E": "HIGH",
                "W": "MEDIUM",
                "C": "LOW",
                "R": "LOW"
            }

            security_keywords = [
                "password", "secret", "token", "key", "auth", "crack", "hack",
                "vulnerability", "unsafe", "shell", "injection", "overflow",
                "memory", "buffer", "permission"
            ]

            for issue in issues_json:
                if any(kw in issue.get("message", "").lower() for kw in security_keywords):
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
            return issues
        except Exception as e:
            print(f"Pylint error: {str(e)}")
            return []

    def _run_vulture(self, app_path: Path) -> List[SecurityIssue]:
        """Run Vulture to find dead code."""
        try:
            result = subprocess.run(
                ["vulture", str(app_path), "--json"],
                capture_output=True,
                text=True,
                check=False,
                timeout=TOOL_TIMEOUT
            )

            dead_code = json.loads(result.stdout)
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
                        code=item.get("size", "No code available"),
                        tool="Vulture"
                    )
                )
            return issues
        except Exception as e:
            print(f"Vulture error: {str(e)}")
            return []

    def run_bandit_analysis(self, model: str, app_num: int, use_all_tools: bool = False) -> Tuple[List[SecurityIssue], Dict[str, str]]:
        """Run security analysis with concurrent tool execution."""
        app_path = self.base_path / f"{model}/flask_apps/app{app_num}/backend"
        
        has_files, python_files = self._check_python_files(app_path)
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
        tool_status = {}  # Track status of each tool

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(tools_to_run)) as executor:
            future_to_tool = {
                executor.submit(tool_map[tool]): tool 
                for tool in tools_to_run 
                if tool in tool_map
            }

            for future in concurrent.futures.as_completed(future_to_tool):
                tool = future_to_tool[future]
                try:
                    issues = future.result()
                    all_issues.extend(issues)
                    tool_status[tool] = "✅ No issues found" if not issues else f"⚠️ Found {len(issues)} issues"
                except Exception as e:
                    tool_status[tool] = f"❌ Error: {str(e)}"
                    print(f"{tool} failed: {str(e)}")

        # Add status for tools that weren't run
        for tool in self.all_tools:
            if tool not in tool_status:
                tool_status[tool] = "⏸️ Not run in quick scan mode"

        return sorted(
            all_issues,
            key=lambda x: (
                {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[x.severity],
                {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[x.confidence],
                x.filename,
                x.line_number
            )
        ), tool_status

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