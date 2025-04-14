"""
Backend Security Analysis Module

Provides comprehensive security scanning for backend code using multiple tools:
- bandit for Python security vulnerability checks
- safety for dependency vulnerability detection
- pylint for code quality analysis and potential security issues
- vulture for dead code detection to reduce attack surface

This module orchestrates the execution of these tools, normalizes their outputs
into a consistent format, and provides aggregated results and summaries.
"""

# =============================================================================
# FUNCTION GLOSSARY
# =============================================================================
# cmd_name: Returns the proper command name for the current operating system
# BackendSecurityIssue: Dataclass representing a security issue found in backend code
# BackendSecurityAnalyzer: Class that analyzes backend code for security issues
#   __init__: Initializes the security analyzer with a base path
#   _check_source_files: Checks if a directory contains Python source files
#   _run_tool: Generic method to run a security tool and parse its output
#   _parse_bandit_output: Parses Bandit JSON output into BackendSecurityIssue objects
#   _run_bandit: Runs Bandit security analysis on Python code
#   _parse_safety_output: Parses Safety output into BackendSecurityIssue objects
#   _run_safety: Runs Safety check on Python dependencies
#   _parse_pylint_output: Parses Pylint JSON output into BackendSecurityIssue objects
#   _run_pylint: Runs Pylint for code quality analysis
#   _parse_vulture_output: Parses Vulture text output into BackendSecurityIssue objects
#   _run_vulture: Runs Vulture to detect dead code
#   run_security_analysis: Runs security analysis with selected tools
#   get_analysis_summary: Generates summary statistics for analysis results

# Standard library imports
import json
import logging
import os
import re
import subprocess
import concurrent.futures
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, Callable

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Constants
TOOL_TIMEOUT = 30  # seconds
SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
CONFIDENCE_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def cmd_name(name: str) -> str:
    """
    Return the proper command name for the current operating system.
    
    Args:
        name: Base command name
        
    Returns:
        Command name adjusted for the operating system
    """
    return f"{name}.cmd" if os.name == "nt" else name


@dataclass
class BackendSecurityIssue:
    """
    Represents a security issue found in backend code.
    
    Attributes:
        filename: Relative path to the file containing the issue
        line_number: Line number where the issue was found
        issue_text: Description of the security issue
        severity: Severity level (HIGH, MEDIUM, LOW)
        confidence: Confidence level (HIGH, MEDIUM, LOW)
        issue_type: Type of issue (e.g., hardcoded_password, sql_injection)
        line_range: Range of lines affected by the issue
        code: Code snippet containing the issue
        tool: Name of the tool that found the issue
        fix_suggestion: Optional suggestion on how to fix the issue
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


class BackendSecurityAnalyzer:
    """
    Analyzes backend code for security issues using multiple tools.
    
    This class orchestrates the execution of security analysis tools
    on Python backend code, including:
    - Bandit for detecting security vulnerabilities
    - Safety for checking dependency vulnerabilities
    - Pylint for code quality issues
    - Vulture for detecting dead code
    
    The analysis results are normalized and combined into a single
    list of BackendSecurityIssue objects, sorted by severity.
    """
    
    def __init__(self, base_path: Path):
        """
        Initialize the security analyzer with a base path.
        
        Args:
            base_path: Base directory containing the code to analyze
        """
        self.base_path = base_path
        self.default_tools = ["bandit"]  # Quick scan tool
        self.all_tools = ["bandit", "safety", "pylint", "vulture"]
        
        # Map tool names to their execution functions
        self.tool_functions = {
            "bandit": self._run_bandit,
            "safety": self._run_safety,
            "pylint": self._run_pylint,
            "vulture": self._run_vulture
        }

    def _check_source_files(self, directory: Path) -> Tuple[bool, List[str]]:
        """
        Check if the directory contains Python source files.
        
        Args:
            directory: Directory to check for Python files
            
        Returns:
            Tuple containing:
            - Boolean indicating if Python files were found
            - List of found Python file paths
        """
        if not directory.exists():
            return False, []
            
        source_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    source_files.append(os.path.join(root, file))
                    
        return bool(source_files), source_files

    def _run_tool(
        self, 
        tool_name: str, 
        command: List[str], 
        parser: Callable[[str], List[BackendSecurityIssue]], 
        app_path: Path
    ) -> Tuple[List[BackendSecurityIssue], str]:
        """
        Generic method to run a security tool and parse its output.
        
        Args:
            tool_name: Name of the tool being run
            command: Command line arguments for the tool
            parser: Function to parse the tool's output into BackendSecurityIssue objects
            app_path: Path to the application code
            
        Returns:
            Tuple containing:
            - List of security issues found
            - Raw output from the tool
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=TOOL_TIMEOUT
            )
            
            raw_output = result.stdout
            
            # Log any error output
            if result.stderr and "ERROR" in result.stderr:
                logger.error(f"{tool_name} warning: {result.stderr}")
            
            # Parse the results
            try:
                issues = parser(raw_output)
                return issues, raw_output
            except Exception as e:
                logger.error(f"Failed to parse {tool_name} output: {e}")
                return [], f"Failed to parse output: {str(e)}"
                
        except subprocess.TimeoutExpired:
            logger.error(f"{tool_name} timed out")
            return [], "Command timed out"
        except Exception as e:
            logger.error(f"{tool_name} failed: {e}")
            return [], str(e)

    def _parse_bandit_output(self, output: str) -> List[BackendSecurityIssue]:
        """
        Parse Bandit JSON output into BackendSecurityIssue objects.
        
        Args:
            output: JSON output from Bandit
            
        Returns:
            List of BackendSecurityIssue objects
        """
        issues = []
        
        try:
            analysis = json.loads(output)
            app_path_str = str(self.base_path)
            
            for issue in analysis.get("results", []):
                issues.append(BackendSecurityIssue(
                    filename=issue["filename"].replace(app_path_str, "").lstrip('/\\'),
                    line_number=issue["line_number"],
                    issue_text=issue["issue_text"],
                    severity=issue["issue_severity"].upper(),
                    confidence=issue["issue_confidence"].upper(),
                    issue_type=issue["test_name"],
                    line_range=issue["line_range"],
                    code=issue.get("code", "Code not available"),
                    tool="Bandit",
                    fix_suggestion=issue.get("more_info", "No fix suggestion available")
                ))
        except json.JSONDecodeError:
            logger.error("Failed to parse Bandit output as JSON")
            
        return issues

    def _run_bandit(self, app_path: Path) -> Tuple[List[BackendSecurityIssue], str]:
        """
        Run Bandit security analysis on Python code.
        
        Args:
            app_path: Path to the application code
            
        Returns:
            Tuple containing:
            - List of security issues found
            - Raw output from Bandit
        """
        command = ["bandit", "-r", str(app_path), "-f", "json", "-ll", "-i"]
        return self._run_tool("Bandit", command, self._parse_bandit_output, app_path)

    def _parse_safety_output(self, output: str) -> List[BackendSecurityIssue]:
        """
        Parse Safety output into BackendSecurityIssue objects.
        
        Args:
            output: Text output from Safety
            
        Returns:
            List of BackendSecurityIssue objects
        """
        issues = []
        
        # Check if vulnerabilities were found
        if "0 vulnerabilities reported" in output and "VULNERABILITIES FOUND" not in output:
            return issues
        
        # Look for warnings about unpinned packages
        unpinned_warnings = re.findall(r'Warning: (\d+) known vulnerabilities match the ([\w-]+) versions', output)
        
        for count, package in unpinned_warnings:
            issues.append(BackendSecurityIssue(
                filename="requirements.txt",
                line_number=0,
                issue_text=f"Unpinned package with potential vulnerabilities: {package}",
                severity="MEDIUM",
                confidence="MEDIUM",
                issue_type="unpinned_dependency",
                line_range=[0],
                code=f"{package} (unpinned)",
                tool="Safety",
                fix_suggestion="Pin the dependency to a specific version to ensure security"
            ))
        
        return issues

    def _run_safety(self, app_path: Path) -> Tuple[List[BackendSecurityIssue], str]:
        """
        Run Safety check on Python dependencies.
        
        Args:
            app_path: Path to the application code
            
        Returns:
            Tuple containing:
            - List of security issues found
            - Raw output from Safety
        """
        requirements_file = app_path / "requirements.txt"
        if not requirements_file.exists():
            return [], "No requirements.txt found"
            
        command = ["safety", "check", "-r", str(requirements_file)]
        return self._run_tool("Safety", command, self._parse_safety_output, app_path)

    def _parse_pylint_output(self, output: str) -> List[BackendSecurityIssue]:
        """
        Parse Pylint JSON output into BackendSecurityIssue objects.
        
        Args:
            output: JSON output from Pylint
            
        Returns:
            List of BackendSecurityIssue objects
        """
        issues = []
        app_path_str = str(self.base_path)
        
        try:
            pylint_data = json.loads(output)
            severity_map = {"E": "HIGH", "W": "MEDIUM", "C": "LOW", "R": "LOW"}
            
            for issue in pylint_data:
                issues.append(BackendSecurityIssue(
                    filename=issue["path"].replace(app_path_str, "").lstrip('/\\'),
                    line_number=issue["line"],
                    issue_text=issue["message"],
                    severity=severity_map.get(issue["type"], "LOW"),
                    confidence="MEDIUM",
                    issue_type=f"pylint_{issue['symbol']}",
                    line_range=[issue["line"]],
                    code=issue.get("message-id", "No code available"),
                    tool="Pylint",
                    fix_suggestion=issue.get("suggestion", "No fix suggestion available")
                ))
        except json.JSONDecodeError:
            logger.error("Failed to parse Pylint output as JSON")
            
        return issues

    def _run_pylint(self, app_path: Path) -> Tuple[List[BackendSecurityIssue], str]:
        """
        Run Pylint for code quality analysis.
        
        Args:
            app_path: Path to the application code
            
        Returns:
            Tuple containing:
            - List of code quality issues found
            - Raw output from Pylint
        """
        command = ["pylint", "--output-format=json", str(app_path)]
        return self._run_tool("Pylint", command, self._parse_pylint_output, app_path)

    def _parse_vulture_output(self, output: str) -> List[BackendSecurityIssue]:
        """
        Parse Vulture text output into BackendSecurityIssue objects.
        
        Args:
            output: Text output from Vulture
            
        Returns:
            List of BackendSecurityIssue objects
        """
        issues = []
        app_path_str = str(self.base_path)
        
        for line in output.splitlines():
            # Skip empty lines
            if not line.strip():
                continue
                
            try:
                # Parse line like: "path/file.py:123: unused function 'xyz' (90% confidence)"
                file_part, rest = line.split(':', 1)
                line_num, desc = rest.split(':', 1)
                
                # Extract a confidence value if present
                confidence = "MEDIUM"
                if "confidence" in desc:
                    conf_match = re.search(r'\((\d+)% confidence\)', desc)
                    if conf_match:
                        conf_value = int(conf_match.group(1))
                        if conf_value >= 80:
                            confidence = "HIGH"
                        elif conf_value < 50:
                            confidence = "LOW"
                
                issues.append(BackendSecurityIssue(
                    filename=file_part.replace(app_path_str, "").lstrip('/\\'),
                    line_number=int(line_num.strip()),
                    issue_text=desc.strip(),
                    severity="LOW",
                    confidence=confidence,
                    issue_type="dead_code",
                    line_range=[int(line_num.strip())],
                    code="N/A",
                    tool="Vulture",
                    fix_suggestion="Remove unused code to reduce attack surface"
                ))
            except Exception as e:
                logger.debug(f"Could not parse vulture line: {line}. Error: {e}")
                continue
                
        return issues

    def _run_vulture(self, app_path: Path) -> Tuple[List[BackendSecurityIssue], str]:
        """
        Run Vulture to detect dead code.
        
        Args:
            app_path: Path to the application code
            
        Returns:
            Tuple containing:
            - List of dead code issues found
            - Raw output from Vulture
        """
        command = ["vulture", str(app_path)]
        return self._run_tool("Vulture", command, self._parse_vulture_output, app_path)

    def run_security_analysis(
        self, 
        model: str, 
        app_num: int, 
        use_all_tools: bool = False
    ) -> Tuple[List[BackendSecurityIssue], Dict[str, str], Dict[str, str]]:
        """
        Run backend security analysis.
        
        Args:
            model: Model identifier
            app_num: Application number
            use_all_tools: Whether to run all tools or just quick scan (default: False)

        Returns:
            Tuple containing:
            - List of security issues found, sorted by severity and confidence
            - Dictionary of tool status messages
            - Dictionary of raw tool outputs
            
        Raises:
            ValueError: If no Python files are found in the specified path
        """
        app_path = self.base_path / f"{model}/app{app_num}/backend"
        has_files, _ = self._check_source_files(app_path)
        
        if not has_files:
            raise ValueError(f"No Python files found in {app_path}")

        tools_to_run = self.all_tools if use_all_tools else self.default_tools
        all_issues = []
        tool_status = {}
        tool_outputs = {}

        # Run tools in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(tools_to_run)) as executor:
            future_to_tool = {
                executor.submit(self.tool_functions[tool], app_path): tool
                for tool in tools_to_run if tool in self.tool_functions
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

        # Sort issues by severity, confidence, filename, and line number
        sorted_issues = sorted(
            all_issues,
            key=lambda x: (
                SEVERITY_ORDER.get(x.severity, 3),
                CONFIDENCE_ORDER.get(x.confidence, 3),
                x.filename,
                x.line_number
            )
        )

        return sorted_issues, tool_status, tool_outputs

    def get_analysis_summary(self, issues: List[BackendSecurityIssue]) -> Dict[str, Any]:
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
        # Default summary structure for empty results
        summary = {
            "total_issues": 0,
            "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "confidence_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "files_affected": 0,
            "issue_types": {},
            "tool_counts": {},
            "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if not issues:
            return summary

        # Update summary with actual counts
        summary["total_issues"] = len(issues)
        summary["files_affected"] = len({issue.filename for issue in issues})

        # Count issues by various attributes
        for issue in issues:
            summary["severity_counts"][issue.severity] += 1
            summary["confidence_counts"][issue.confidence] += 1
            summary["issue_types"][issue.issue_type] = summary["issue_types"].get(issue.issue_type, 0) + 1
            summary["tool_counts"][issue.tool] = summary["tool_counts"].get(issue.tool, 0) + 1

        return summary