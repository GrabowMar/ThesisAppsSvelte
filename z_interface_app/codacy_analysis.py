"""
codacy_analysis.py - Codacy Static Analysis Integration

Integrates Codacy CLI tool for static code analysis, supporting:
- Multiple languages (Python, JavaScript, TypeScript)
- Code quality metrics
- Security vulnerability detection
- Code duplication analysis
"""

import json
import subprocess
import logging
from pathlib import Path
from typing import List, Tuple, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CodacyIssue:
    """Represents a Codacy analysis issue"""
    filename: str
    line_number: int
    issue_text: str
    severity: str
    confidence: str
    issue_type: str
    line_range: List[int]
    code: str
    tool: str = "Codacy"
    
class CodacyAnalyzer:
    """Handles Codacy analysis integration"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.TOOL_TIMEOUT = 300  # 5 minutes timeout for Codacy analysis
        
    def _install_codacy_cli(self) -> bool:
        """Install Codacy CLI if not already installed"""
        try:
            # Check if Codacy CLI is installed
            subprocess.run(["codacy-analysis-cli", "--version"], 
                         capture_output=True, 
                         check=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            try:
                # Install Codacy CLI using npm
                subprocess.run(["npm", "install", "-g", "codacy-analysis-cli"],
                             check=True,
                             timeout=self.TOOL_TIMEOUT)
                return True
            except Exception as e:
                logger.error(f"Failed to install Codacy CLI: {e}")
                return False

    def _map_severity(self, codacy_severity: str) -> str:
        """Map Codacy severity levels to our standard levels"""
        severity_map = {
            "Critical": "HIGH",
            "Error": "HIGH",
            "Warning": "MEDIUM",
            "Info": "LOW",
            "Style": "LOW"
        }
        return severity_map.get(codacy_severity, "LOW")

    def run_analysis(self, project_path: Path) -> Tuple[List[CodacyIssue], str]:
        """Run Codacy analysis on the specified project path"""
        if not self._install_codacy_cli():
            return [], "Failed to install Codacy CLI"

        try:
            # Run Codacy analysis
            result = subprocess.run(
                [
                    "codacy-analysis-cli",
                    "analyze",
                    "--directory", str(project_path),
                    "--format", "json",
                    "--verbose"
                ],
                capture_output=True,
                text=True,
                timeout=self.TOOL_TIMEOUT
            )

            # Handle potential errors
            if result.returncode != 0:
                logger.error(f"Codacy analysis failed: {result.stderr}")
                return [], f"Analysis failed: {result.stderr}"

            # Parse results
            try:
                analysis_results = json.loads(result.stdout)
            except json.JSONDecodeError:
                logger.error("Failed to parse Codacy output")
                return [], "Failed to parse analysis results"

            issues = []
            for finding in analysis_results:
                # Extract code snippet if available
                code_snippet = finding.get("code", "")
                if not code_snippet and "lines" in finding:
                    code_snippet = f"Lines {finding['lines']['begin']}-{finding['lines']['end']}"

                issues.append(
                    CodacyIssue(
                        filename=finding["filename"].replace(str(project_path), "").lstrip('/\\'),
                        line_number=finding.get("lines", {}).get("begin", 0),
                        issue_text=finding.get("message", "No description available"),
                        severity=self._map_severity(finding.get("level", "Info")),
                        confidence="HIGH",  # Codacy doesn't provide confidence levels
                        issue_type=finding.get("pattern", {}).get("category", "unknown"),
                        line_range=[
                            finding.get("lines", {}).get("begin", 0),
                            finding.get("lines", {}).get("end", 0)
                        ],
                        code=code_snippet
                    )
                )

            return issues, result.stdout

        except subprocess.TimeoutExpired:
            logger.error("Codacy analysis timed out")
            return [], "Analysis timed out"
        except Exception as e:
            logger.error(f"Unexpected error during Codacy analysis: {e}")
            return [], f"Unexpected error: {str(e)}"

    def analyze_app(self, model: str, app_num: int, create_config: bool = True) -> Tuple[List[CodacyIssue], str]:
        """Analyze a specific app using Codacy
        
        Args:
            model: The model name (e.g., 'ChatGPT4o')
            app_num: The app number
            create_config: Whether to create a Codacy config file if it doesn't exist
        """
        app_path = self.base_path / f"{model}/app{app_num}"
        if not app_path.exists():
            return [], f"App directory not found: {app_path}"

        return self.run_analysis(app_path)

def integrate_with_security_analyzer(security_analyzer):
    """Integrate Codacy with the main SecurityAnalyzer class"""
    
    # Add Codacy to the available tools
    security_analyzer.all_tools.append("codacy")
    
    # Create Codacy analyzer instance
    codacy_analyzer = CodacyAnalyzer(security_analyzer.base_path)
    
    # Add Codacy analysis method
    def run_codacy_analysis(app_path: Path) -> Tuple[List[SecurityIssue], str]:
        try:
            issues, raw_output = codacy_analyzer.analyze_app(
                str(app_path.parent.parent.name),  # model name
                int(app_path.parent.name.replace("app", ""))  # app number
            )
            
            # Convert CodacyIssue to SecurityIssue
            security_issues = [
                SecurityIssue(
                    filename=issue.filename,
                    line_number=issue.line_number,
                    issue_text=issue.issue_text,
                    severity=issue.severity,
                    confidence=issue.confidence,
                    issue_type=issue.issue_type,
                    line_range=issue.line_range,
                    code=issue.code,
                    tool="Codacy"
                ) for issue in issues
            ]
            
            return security_issues, raw_output
        except Exception as e:
            logger.error(f"Codacy analysis failed: {e}")
            return [], f"Error: {str(e)}"
    
    # Add the Codacy analysis method to the tool map
    security_analyzer.tool_map["codacy"] = run_codacy_analysis

def create_codacy_config(path: Path) -> None:
    """Create a Codacy configuration file if it doesn't exist"""
    config = {
        "tools": {
            "python": {
                "pylint": {
                    "enabled": True
                },
                "bandit": {
                    "enabled": True
                }
            },
            "javascript": {
                "eslint": {
                    "enabled": True
                }
            },
            "typescript": {
                "tslint": {
                    "enabled": True
                }
            }
        },
        "exclude_paths": [
            "tests/**",
            "**/__pycache__/**",
            "node_modules/**"
        ]
    }
    
    config_path = path / ".codacy.json"
    if not config_path.exists():
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)