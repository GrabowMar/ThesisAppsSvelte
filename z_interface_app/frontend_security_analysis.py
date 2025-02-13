# frontend_security_analysis.py
"""
Frontend Security Analysis Module

Provides security scanning for frontend code using multiple tools:
- npm audit for dependency vulnerabilities
- eslint for code quality and Svelte-specific linting
- retire.js for known vulnerable JavaScript libraries
- snyk for additional security checks
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

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Common timeout for all tools
TOOL_TIMEOUT = 30  # seconds

def cmd_name(name: str) -> str:
    """Return the proper command name for Windows if needed."""
    return f"{name}.cmd" if os.name == "nt" else name

@dataclass
class FrontendSecurityIssue:
    """Represents a security issue found in frontend code."""
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

class FrontendSecurityAnalyzer:
    """Analyzes frontend code for security issues using multiple tools."""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.default_tools = ["npm-audit"]  # Quick scan tool
        self.all_tools = ["npm-audit", "eslint", "retire-js", "snyk"]

    def _check_source_files(self, directory: Path) -> Tuple[bool, List[str]]:
        """Check if directory contains frontend source files."""
        if not directory.exists():
            return False, []
        source_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.js', '.ts', '.svelte')):
                    source_files.append(os.path.join(root, file))
        return bool(source_files), source_files

    def _run_npm_audit(self, app_path: Path) -> Tuple[List[FrontendSecurityIssue], str]:
        """Run npm audit for dependency vulnerabilities."""
        try:
            command = [cmd_name("npm"), "audit", "--json"]
            result = subprocess.run(
                command,
                cwd=str(app_path),
                capture_output=True,
                text=True,
                timeout=TOOL_TIMEOUT
            )
            if result.returncode != 0 and "ERR!" in result.stderr:
                logger.error(f"npm audit error: {result.stderr}")
                return [], result.stderr
                
            issues = []
            raw_output = result.stdout
            
            try:
                audit_data = json.loads(raw_output)
                for vuln in audit_data.get("vulnerabilities", {}).values():
                    severity_map = {
                        "critical": "HIGH",
                        "high": "HIGH",
                        "moderate": "MEDIUM",
                        "low": "LOW"
                    }
                    issues.append(FrontendSecurityIssue(
                        filename="package.json",
                        line_number=0,
                        issue_text=vuln.get("title", "Unknown vulnerability"),
                        severity=severity_map.get(vuln.get("severity", "low"), "LOW"),
                        confidence="HIGH",
                        issue_type="dependency_vulnerability",
                        line_range=[0],
                        code=f"{vuln.get('name')}@{vuln.get('version')}",
                        tool="npm-audit",
                        fix_suggestion=vuln.get("recommendation")
                    ))
                return issues, raw_output
            except json.JSONDecodeError:
                logger.error("Failed to parse npm audit output")
                return [], "Invalid JSON output"
                
        except subprocess.TimeoutExpired:
            logger.error("npm audit timed out")
            return [], "Command timed out"
        except Exception as e:
            logger.error(f"npm audit failed: {e}")
            return [], str(e)

    def _run_eslint(self, app_path: Path) -> Tuple[List[FrontendSecurityIssue], str]:
        """Run ESLint with Svelte plugin for code analysis."""
        try:
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
                timeout=TOOL_TIMEOUT
            )
            
            issues = []
            raw_output = result.stdout
            
            try:
                eslint_data = json.loads(raw_output)
                for file_result in eslint_data:
                    for msg in file_result.get("messages", []):
                        # Only include errors for now
                        if msg.get("severity", 1) < 2:
                            continue
                            
                        issues.append(FrontendSecurityIssue(
                            filename=file_result["filePath"].replace(str(app_path), "").lstrip('/\\'),
                            line_number=msg.get("line", 0),
                            issue_text=msg.get("message", "Unknown issue"),
                            severity="HIGH" if msg.get("severity") == 2 else "MEDIUM",
                            confidence="MEDIUM",
                            issue_type=msg.get("ruleId", "unknown"),
                            line_range=[msg.get("line", 0)],
                            code=msg.get("source", "Code not available"),
                            tool="eslint",
                            fix_suggestion=msg.get("fix", {}).get("text")
                        ))
                return issues, raw_output
            except json.JSONDecodeError:
                logger.error("Failed to parse ESLint output")
                return [], "Invalid JSON output"
                
        except subprocess.TimeoutExpired:
            logger.error("ESLint timed out")
            return [], "Command timed out"
        except Exception as e:
            logger.error(f"ESLint failed: {e}")
            return [], str(e)

    def _run_retire_js(self, app_path: Path) -> Tuple[List[FrontendSecurityIssue], str]:
        """Run retire.js to find known vulnerable libraries."""
        try:
            command = [cmd_name("npx"), "retire", "--path", ".", "--outputformat", "json"]
            result = subprocess.run(
                command,
                cwd=str(app_path),
                capture_output=True,
                text=True,
                timeout=TOOL_TIMEOUT
            )
            
            issues = []
            raw_output = result.stdout
            
            try:
                retire_data = json.loads(raw_output)
                for result_item in retire_data.get("results", []):
                    for vuln in result_item.get("vulnerabilities", []):
                        issues.append(FrontendSecurityIssue(
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
                        ))
                return issues, raw_output
            except json.JSONDecodeError:
                logger.error("Failed to parse retire.js output")
                return [], "Invalid JSON output"
                
        except subprocess.TimeoutExpired:
            logger.error("retire.js timed out")
            return [], "Command timed out"
        except Exception as e:
            logger.error(f"retire.js failed: {e}")
            return [], str(e)

    def _run_snyk(self, app_path: Path) -> Tuple[List[FrontendSecurityIssue], str]:
        """Run Snyk for dependency and code analysis."""
        try:
            command = [cmd_name("snyk"), "test", "--json"]
            result = subprocess.run(
                command,
                cwd=str(app_path),
                capture_output=True,
                text=True,
                timeout=TOOL_TIMEOUT
            )
            
            if "Authentication error" in result.stdout:
                logger.error("Snyk authentication required")
                return [], "Authentication error. Run 'snyk auth'."
                
            issues = []
            raw_output = result.stdout
            
            try:
                snyk_data = json.loads(raw_output)
                for vuln in snyk_data.get("vulnerabilities", []):
                    severity_map = {
                        "critical": "HIGH",
                        "high": "HIGH",
                        "medium": "MEDIUM",
                        "low": "LOW"
                    }
                    issues.append(FrontendSecurityIssue(
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
                    ))
                return issues, raw_output
            except json.JSONDecodeError:
                logger.error("Failed to parse Snyk output")
                return [], "Invalid JSON output"
                
        except subprocess.TimeoutExpired:
            logger.error("Snyk timed out")
            return [], "Command timed out"
        except Exception as e:
            logger.error(f"Snyk failed: {e}")
            return [], str(e)

    def run_security_analysis(
        self, 
        model: str, 
        app_num: int, 
        use_all_tools: bool = False
    ) -> Tuple[List[FrontendSecurityIssue], Dict[str, str], Dict[str, str]]:
        """
        Run frontend security analysis.
        
        Args:
            model: Model identifier
            app_num: Application number
            use_all_tools: Whether to run all tools or just quick scan

        Returns:
            - List of security issues found
            - Dictionary of tool status messages
            - Dictionary of raw tool outputs
        """
        app_path = self.base_path / f"{model}/app{app_num}/frontend"
        has_files, _ = self._check_source_files(app_path / "src")
        if not has_files:
            raise ValueError(f"No frontend files found in {app_path}/src")

        tools_to_run = self.all_tools if use_all_tools else self.default_tools
        tool_map = {
            "npm-audit": lambda: self._run_npm_audit(app_path),
            "eslint": lambda: self._run_eslint(app_path),
            "retire-js": lambda: self._run_retire_js(app_path),
            "snyk": lambda: self._run_snyk(app_path)
        }

        all_issues = []
        tool_status = {}
        tool_outputs = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(tools_to_run)) as executor:
            future_to_tool = {
                executor.submit(tool_map[tool]): tool
                for tool in tools_to_run if tool in tool_map
            }
            
            for future in concurrent.futures.as_completed(future_to_tool):
                tool = future_to_tool[future]
                try:
                    issues, output = future.result()
                    all_issues.extend(issues)
                    tool_outputs[tool] = output
                    tool_status[tool] = "✅ No issues found" if not issues else f"⚠️ Found {len(issues)} issues"
                except Exception as e:
                    tool_status[tool] = f"❌ Error: {str(e)}"
                    tool_outputs[tool] = f"Error: {str(e)}"

        # Mark tools not run
        for tool in self.all_tools:
            if tool not in tool_status:
                tool_status[tool] = "⏸️ Not run in quick scan mode"

        # Sort issues by severity and confidence
        sorted_issues = sorted(
            all_issues,
            key=lambda x: (
                {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(x.severity, 3),
                {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(x.confidence, 3),
                x.filename,
                x.line_number
            )
        )

        return sorted_issues, tool_status, tool_outputs

    def get_analysis_summary(self, issues: List[FrontendSecurityIssue]) -> dict:
        """Generate summary statistics for the analysis results."""
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
            "files_affected": len({issue.filename for issue in issues}),
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