"""
frontend_security_analysis.py - Frontend Security Analysis Module
Combines multiple security scanning tools for SvelteKit/Frontend code:
- snyk for dependency vulnerabilities
- npm audit for package security
- eslint-security for code security
- retire.js for known vulnerable JavaScript libraries
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

    def _run_npm_audit(self, app_path: Path) -> List[FrontendSecurityIssue]:
        """Run npm audit for dependency vulnerabilities."""
        try:
            result = subprocess.run(
                ["npm", "audit", "--json"],
                cwd=str(app_path),
                capture_output=True,
                text=True,
                timeout=self.TOOL_TIMEOUT
            )

            if result.stderr and "ERR!" in result.stderr:
                print(f"npm audit warning: {result.stderr}")
                return []

            audit_data = json.loads(result.stdout)
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
            return issues
        except Exception as e:
            print(f"npm audit error: {str(e)}")
            return []

    def _run_eslint_security(self, app_path: Path) -> List[FrontendSecurityIssue]:
        """Run ESLint with security plugins."""
        try:
            result = subprocess.run(
                ["npx", "eslint", 
                 "--plugin", "security",
                 "--format", "json",
                 "src/"],
                cwd=str(app_path),
                capture_output=True,
                text=True,
                timeout=self.TOOL_TIMEOUT
            )

            eslint_data = json.loads(result.stdout)
            issues = []

            for file_result in eslint_data:
                for message in file_result.get("messages", []):
                    if message.get("ruleId", "").startswith("security/"):
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
                                tool="eslint-security",
                                fix_suggestion=message.get("fix", {}).get("text")
                            )
                        )
            return issues
        except Exception as e:
            print(f"ESLint security error: {str(e)}")
            return []

    def _run_retire_js(self, app_path: Path) -> List[FrontendSecurityIssue]:
        """Run retire.js to find known vulnerable JavaScript libraries."""
        try:
            result = subprocess.run(
                ["npx", "retire", "--path", ".", "--outputformat", "json"],
                cwd=str(app_path),
                capture_output=True,
                text=True,
                timeout=self.TOOL_TIMEOUT
            )

            retire_data = json.loads(result.stdout)
            issues = []

            for result in retire_data.get("results", []):
                for vuln in result.get("vulnerabilities", []):
                    issues.append(
                        FrontendSecurityIssue(
                            filename=result.get("file", "unknown"),
                            line_number=0,
                            issue_text=vuln.get("info", ["No description"])[0],
                            severity="HIGH",
                            confidence="HIGH",
                            issue_type="known_vulnerability",
                            line_range=[0],
                            code=f"{result.get('component')}@{result.get('version')}",
                            tool="retire-js",
                            fix_suggestion=f"Update to version {vuln.get('below', 'latest')}"
                        )
                    )
            return issues
        except Exception as e:
            print(f"retire.js error: {str(e)}")
            return []

    def _run_snyk(self, app_path: Path) -> List[FrontendSecurityIssue]:
        """Run Snyk for dependency and code analysis."""
        try:
            result = subprocess.run(
                ["snyk", "test", "--json"],
                cwd=str(app_path),
                capture_output=True,
                text=True,
                timeout=self.TOOL_TIMEOUT
            )

            snyk_data = json.loads(result.stdout)
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
            return issues
        except Exception as e:
            print(f"Snyk error: {str(e)}")
            return []

    def run_security_analysis(self, model: str, app_num: int, use_all_tools: bool = False) -> Tuple[List[FrontendSecurityIssue], Dict[str, str]]:
        """Run comprehensive frontend security analysis."""
        app_path = self.base_path / f"{model}/flask_apps/app{app_num}/frontend"
        
        has_files, js_files = self._check_frontend_files(app_path)
        if not has_files:
            raise ValueError(
                f"No frontend files found in {app_path}. "
                "Please ensure the frontend directory exists and contains JS/TS/Svelte files."
            )

        tools_to_run = self.all_tools if use_all_tools else self.default_tools
        tool_map = {
            "npm-audit": lambda: self._run_npm_audit(app_path),
            "eslint": lambda: self._run_eslint_security(app_path),
            "retire-js": lambda: self._run_retire_js(app_path),
            "snyk": lambda: self._run_snyk(app_path)
        }

        all_issues = []
        tool_status = {}

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