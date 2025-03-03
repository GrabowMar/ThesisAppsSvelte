# security_analysis.py
"""
Backend Security Analysis Module

Provides security scanning for backend code using multiple tools:
- bandit for Python security checks
- safety for dependency vulnerabilities
- pylint for code quality
- vulture for dead code detection
"""

import json
import os
import re
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
class BackendSecurityIssue:
	"""Represents a security issue found in backend code."""
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
	"""Analyzes backend code for security issues using multiple tools."""
	
	def __init__(self, base_path: Path):
		self.base_path = base_path
		self.default_tools = ["bandit"]  # Quick scan tool
		self.all_tools = ["bandit", "safety", "pylint", "vulture"]

	def _check_source_files(self, directory: Path) -> Tuple[bool, List[str]]:
		"""Check if directory contains Python source files."""
		if not directory.exists():
			return False, []
		source_files = []
		for root, _, files in os.walk(directory):
			for file in files:
				if file.endswith('.py'):
					source_files.append(os.path.join(root, file))
		return bool(source_files), source_files

	def _run_bandit(self, app_path: Path) -> Tuple[List[BackendSecurityIssue], str]:
		"""Run Bandit security analysis on Python code."""
		try:
			command = ["bandit", "-r", str(app_path), "-f", "json", "-ll", "-i"]
			result = subprocess.run(
				command,
				capture_output=True,
				text=True,
				timeout=TOOL_TIMEOUT
			)
			if result.stderr and "ERROR" in result.stderr:
				logger.error(f"Bandit warning: {result.stderr}")
				
			issues = []
			raw_output = result.stdout
			
			try:
				analysis = json.loads(raw_output)
				for issue in analysis.get("results", []):
					issues.append(BackendSecurityIssue(
						filename=issue["filename"].replace(str(app_path), "").lstrip('/\\'),
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
				return issues, raw_output
			except json.JSONDecodeError:
				logger.error("Failed to parse Bandit output")
				return [], "Invalid JSON output"
				
		except subprocess.TimeoutExpired:
			logger.error("Bandit timed out")
			return [], "Command timed out"
		except Exception as e:
			logger.error(f"Bandit failed: {e}")
			return [], str(e)

	def _run_safety(self, app_path: Path) -> Tuple[List[BackendSecurityIssue], str]:
		"""Run Safety check on Python dependencies."""
		try:
			requirements_file = app_path / "requirements.txt"
			if not requirements_file.exists():
				return [], "No requirements.txt found"
				
			# Use text output format
			command = ["safety", "check", "-r", str(requirements_file)]
			result = subprocess.run(
				command,
				capture_output=True,
				text=True,
				timeout=TOOL_TIMEOUT
			)
			
			issues = []
			raw_output = result.stdout
			
			# Check if vulnerabilities were found
			if "0 vulnerabilities reported" in raw_output and "VULNERABILITIES FOUND" not in raw_output:
				return [], raw_output
			
			# Look for warnings about unpinned packages
			unpinned_warnings = re.findall(r'Warning: (\d+) known vulnerabilities match the ([\w-]+) versions', raw_output)
			
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
			
			# Look for actual vulnerability details (if present)
			# This would require more regex parsing based on the specific format
			
			return issues, raw_output
				
		except subprocess.TimeoutExpired:
			logger.error("Safety timed out")
			return [], "Command timed out"
		except Exception as e:
			logger.error(f"Safety failed: {e}")
			return [], str(e)

	def _run_pylint(self, app_path: Path) -> Tuple[List[BackendSecurityIssue], str]:
		"""Run Pylint for code quality analysis."""
		try:
			command = ["pylint", "--output-format=json", str(app_path)]
			result = subprocess.run(
				command,
				capture_output=True,
				text=True,
				timeout=TOOL_TIMEOUT
			)
			
			issues = []
			raw_output = result.stdout
			
			try:
				pylint_data = json.loads(raw_output)
				severity_map = {"E": "HIGH", "W": "MEDIUM", "C": "LOW", "R": "LOW"}
				for issue in pylint_data:
					issues.append(BackendSecurityIssue(
						filename=issue["path"].replace(str(app_path), "").lstrip('/\\'),
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
				return issues, raw_output
			except json.JSONDecodeError:
				logger.error("Failed to parse Pylint output")
				return [], "Invalid JSON output"
				
		except subprocess.TimeoutExpired:
			logger.error("Pylint timed out")
			return [], "Command timed out"
		except Exception as e:
			logger.error(f"Pylint failed: {e}")
			return [], str(e)

	def _run_vulture(self, app_path: Path) -> Tuple[List[BackendSecurityIssue], str]:
		"""Run Vulture to detect dead code."""
		try:
			# Try running vulture with direct output (no --json flag)
			command = ["vulture", str(app_path)]
			result = subprocess.run(
				command,
				capture_output=True,
				text=True,
				timeout=TOOL_TIMEOUT
			)
			
			issues = []
			raw_output = result.stdout
			
			# Parse the text output format which looks like:
			# filename.py:12: unused function 'my_func' (60% confidence)
			for line in raw_output.splitlines():
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
						filename=file_part.replace(str(app_path), "").lstrip('/\\'),
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
					
			return issues, raw_output
					
		except subprocess.TimeoutExpired:
			logger.error("Vulture timed out")
			return [], "Command timed out"
		except Exception as e:
			logger.error(f"Vulture failed: {e}")
			return [], str(e)

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
			use_all_tools: Whether to run all tools or just quick scan

		Returns:
			- List of security issues found
			- Dictionary of tool status messages
			- Dictionary of raw tool outputs
		"""
		app_path = self.base_path / f"{model}/app{app_num}/backend"
		has_files, _ = self._check_source_files(app_path)
		if not has_files:
			raise ValueError(f"No Python files found in {app_path}")

		tools_to_run = self.all_tools if use_all_tools else self.default_tools
		tool_map = {
			"bandit": lambda: self._run_bandit(app_path),
			"safety": lambda: self._run_safety(app_path),
			"pylint": lambda: self._run_pylint(app_path),
			"vulture": lambda: self._run_vulture(app_path)
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

	def get_analysis_summary(self, issues: List[BackendSecurityIssue]) -> dict:
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