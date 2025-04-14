"""
SonarQube Code Quality and Maintainability Analysis Module

Provides comprehensive code quality analysis for projects using SonarQube and SonarCloud:
- Uses pysonar scanner for Python code analysis
- Uses SonarQube API for retrieving analysis results
- Provides detailed code quality metrics and technical debt reporting
- Supports multiple configuration methods including sonar-project.properties and pyproject.toml
- Integrates with existing logging and error handling mechanisms

This module orchestrates the execution of SonarQube analysis, normalizes the outputs
into a consistent format, and provides aggregated results and quality metrics.
"""

# =============================================================================
# FUNCTION GLOSSARY
# =============================================================================
# cmd_name: Returns the proper command name for the current operating system
# SonarQubeIssue: Dataclass representing a SonarQube issue found in code
# SonarMeasure: Dataclass representing a SonarQube quality measure
# SonarQubeAnalyzer: Class that analyzes code using SonarQube
#   __init__: Initializes the SonarQube analyzer with a base path and server settings
#   _check_sonar_available: Verifies if SonarQube scanner is installed and available
#   _get_sonar_project_properties: Extracts SonarQube analysis properties from configuration
#   _build_sonar_command: Builds the SonarQube CLI command
#   _run_sonar_scanner: Runs the SonarQube scanner
#   _get_analysis_results: Retrieves analysis results from SonarQube API
#   _parse_issues: Parses SonarQube issues into SonarQubeIssue objects
#   _parse_measures: Parses SonarQube measures into SonarMeasure objects
#   _create_quality_report: Creates a quality report from the analysis results
#   analyze_project: Main method to analyze a project
#   get_analysis_summary: Generates summary statistics for analysis results
#   get_quality_report: Generates a detailed quality report
#   get_tech_debt_report: Generates a technical debt report

# =============================================================================
# Standard Library Imports
# =============================================================================
import json
import logging
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union, Set, Iterator

# =============================================================================
# Third-Party Imports
# =============================================================================
import requests
from requests.exceptions import RequestException
import toml

# =============================================================================
# Custom Module Imports
# =============================================================================
# Import from the existing application if running within the app context
try:
    from logging_service import create_logger_for_component
except ImportError:
    # Fallback logger if running standalone
    def create_logger_for_component(name):
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

# Configure logging
logger = create_logger_for_component('sonar_analyzer')

# =============================================================================
# Constants
# =============================================================================
SONAR_SCANNER_TIMEOUT = 1800  # 30 minutes
SONAR_API_TIMEOUT = 60  # 60 seconds
DEFAULT_SONAR_URL = "http://localhost:9000"

# Quality metric keys
QUALITY_METRICS = [
    "reliability_rating",
    "security_rating",
    "sqale_rating",  # Maintainability rating
    "coverage",
    "duplicated_lines_density",
    "bugs",
    "vulnerabilities",
    "code_smells",
    "sqale_index",  # Technical debt in minutes
    "ncloc",  # Number of lines of code
    "cognitive_complexity"
]

# Issue severities ordered by priority
class IssueSeverity(Enum):
    BLOCKER = 0
    CRITICAL = 1
    MAJOR = 2
    MINOR = 3
    INFO = 4

# Issue types with categories
ISSUE_TYPES = {
    "BUG": "Reliability",
    "VULNERABILITY": "Security",
    "CODE_SMELL": "Maintainability"
}


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
class SonarQubeIssue:
    """
    Represents an issue found by SonarQube analysis.
    
    Attributes:
        issue_key: Unique identifier for the issue
        component: Component (file) where the issue was found
        project: Project key
        rule: Rule key that was violated
        severity: Severity level (BLOCKER, CRITICAL, MAJOR, MINOR, INFO)
        type: Type of issue (BUG, VULNERABILITY, CODE_SMELL)
        message: Description of the issue
        line: Line number where the issue was found
        effort: Estimated effort to fix the issue (e.g., "30min")
        debt: Technical debt introduced by the issue
        tags: Tags associated with the issue
        creation_date: Date when the issue was created
        code_snippet: Code snippet where the issue was found
        fix_suggestion: Optional suggestion on how to fix the issue
    """
    issue_key: str
    component: str
    project: str
    rule: str
    severity: str
    type: str
    message: str
    line: Optional[int] = None
    effort: Optional[str] = None
    debt: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    creation_date: Optional[str] = None
    code_snippet: Optional[str] = None
    fix_suggestion: Optional[str] = None
    

@dataclass
class SonarMeasure:
    """
    Represents a quality measure from SonarQube.
    
    Attributes:
        metric: Name of the metric
        value: Value of the metric
        component: Component (file or project) the metric applies to
        best_value: Whether this is the best value for the metric
        description: Description of the metric
    """
    metric: str
    value: Any
    component: str
    best_value: bool = False
    description: Optional[str] = None


class SonarQubeAnalyzer:
    """
    Analyzes code quality and maintainability using SonarQube.
    
    This class manages the execution of SonarQube analysis tools
    and retrieves results from the SonarQube API to provide
    comprehensive code quality metrics and issue reports.
    """
    
    def __init__(
        self, 
        base_path: Path, 
        sonar_url: str = DEFAULT_SONAR_URL,
        sonar_token: Optional[str] = None,
        sonar_user: Optional[str] = None,
        sonar_password: Optional[str] = None
    ):
        """
        Initialize the SonarQube analyzer.
        
        Args:
            base_path: Base directory containing the code to analyze
            sonar_url: URL of the SonarQube server (default: http://localhost:9000)
            sonar_token: Authentication token for SonarQube
            sonar_user: Username for SonarQube authentication
            sonar_password: Password for SonarQube authentication
        """
        self.base_path = Path(base_path)
        self.sonar_url = sonar_url
        self.sonar_token = sonar_token
        self.sonar_user = sonar_user
        self.sonar_password = sonar_password
        
        # Validate that at least one authentication method is provided
        if sonar_token is None and (sonar_user is None or sonar_password is None):
            logger.warning("No authentication provided for SonarQube API. Some features may be limited.")
            
        # Auth header for SonarQube API
        self.auth_header = None
        if sonar_token:
            auth_str = f"{sonar_token}:"
            self.auth_header = {"Authorization": f"Basic {auth_str}"}
        elif sonar_user and sonar_password:
            auth_str = f"{sonar_user}:{sonar_password}"
            self.auth_header = {"Authorization": f"Basic {auth_str}"}
            
        # Check if SonarQube scanner is available
        self._check_sonar_available()

    def _check_sonar_available(self) -> bool:
        """
        Check if SonarQube scanner is available.
        
        Attempts to run 'pysonar --version' to verify if the scanner is installed.
        
        Returns:
            Boolean indicating if SonarQube scanner is available
        """
        try:
            result = subprocess.run(
                ["pysonar", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info(f"SonarQube scanner detected: {version}")
                return True
            else:
                logger.warning("SonarQube scanner command failed")
                logger.debug(f"Error: {result.stderr}")
                return False
        except FileNotFoundError:
            logger.warning("SonarQube scanner (pysonar) not found. Please install it with 'pip install pysonar'")
            return False
        except Exception as e:
            logger.error(f"Error checking SonarQube scanner: {e}")
            return False

    def _get_sonar_project_properties(self, project_dir: Path) -> Dict[str, Any]:
        """
        Get SonarQube project properties from configuration files.
        
        Looks for properties in the following order of priority:
        1. sonar-project.properties file
        2. pyproject.toml [tool.sonar] section
        3. Environment variables
        
        Args:
            project_dir: Project directory to analyze
            
        Returns:
            Dictionary of SonarQube properties
        """
        properties = {}
        
        # Check for sonar-project.properties
        sonar_properties_file = project_dir / "sonar-project.properties"
        if sonar_properties_file.exists():
            logger.info(f"Found sonar-project.properties at {sonar_properties_file}")
            with open(sonar_properties_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            properties[key.strip()] = value.strip()
        
        # Check for pyproject.toml [tool.sonar] section
        pyproject_file = project_dir / "pyproject.toml"
        if pyproject_file.exists():
            try:
                logger.info(f"Found pyproject.toml at {pyproject_file}")
                with open(pyproject_file, 'r', encoding='utf-8') as f:
                    pyproject_data = toml.load(f)
                    
                if 'tool' in pyproject_data and 'sonar' in pyproject_data['tool']:
                    sonar_config = pyproject_data['tool']['sonar']
                    
                    # Convert kebab-case to camelCase and add sonar. prefix
                    for key, value in sonar_config.items():
                        # Convert kebab-case to camelCase
                        if '-' in key:
                            parts = key.split('-')
                            key = parts[0] + ''.join(p.capitalize() for p in parts[1:])
                            
                        properties[f"sonar.{key}"] = value
                        
                    logger.info(f"Loaded SonarQube properties from pyproject.toml")
            except Exception as e:
                logger.error(f"Error parsing pyproject.toml: {e}")
        
        # Check environment variables
        env_properties = {
            key.replace('SONAR_', 'sonar.').lower(): value 
            for key, value in os.environ.items() 
            if key.startswith('SONAR_') and key != 'SONAR_SCANNER_JSON_PARAMS'
        }
        
        if env_properties:
            logger.info(f"Found {len(env_properties)} SonarQube properties in environment variables")
            properties.update(env_properties)
            
        # Also check if JSON params are provided
        if 'SONAR_SCANNER_JSON_PARAMS' in os.environ:
            try:
                json_params = json.loads(os.environ['SONAR_SCANNER_JSON_PARAMS'])
                logger.info(f"Found JSON parameters in SONAR_SCANNER_JSON_PARAMS")
                properties.update(json_params)
            except json.JSONDecodeError:
                logger.error("Invalid JSON in SONAR_SCANNER_JSON_PARAMS")
                
        return properties

    def _build_sonar_command(self, project_dir: Path, additional_properties: Dict[str, str] = None) -> List[str]:
        """
        Build the SonarQube scanner command.
        
        Args:
            project_dir: Project directory to analyze
            additional_properties: Additional properties to pass to the scanner
            
        Returns:
            List of command components to run the scanner
        """
        # Start with base command
        command = ["pysonar"]
        
        # Add properties from configuration
        properties = self._get_sonar_project_properties(project_dir)
        
        # Add additional properties
        if additional_properties:
            properties.update(additional_properties)
            
        # Add auth token if present
        if self.sonar_token and 'sonar.token' not in properties:
            properties['sonar.token'] = self.sonar_token
            
        # Add server URL if present
        if self.sonar_url and 'sonar.host.url' not in properties:
            properties['sonar.host.url'] = self.sonar_url
            
        # Ensure projectBaseDir is set if not present
        if 'sonar.projectBaseDir' not in properties:
            properties['sonar.projectBaseDir'] = str(project_dir)
            
        # Add all properties to command
        for key, value in properties.items():
            command.append(f"-D{key}={value}")
            
        return command

    def _run_sonar_scanner(self, project_dir: Path, additional_properties: Dict[str, str] = None) -> Tuple[bool, str]:
        """
        Run the SonarQube scanner on a project.
        
        Args:
            project_dir: Project directory to analyze
            additional_properties: Additional properties to pass to the scanner
            
        Returns:
            Tuple containing:
            - Boolean indicating success or failure
            - Output from the scanner
        """
        command = self._build_sonar_command(project_dir, additional_properties)
        
        # Mask sensitive information for logging
        log_command = []
        for item in command:
            if 'sonar.token=' in item or 'sonar.login=' in item:
                log_command.append(item.split('=')[0] + '=********')
            else:
                log_command.append(item)
                
        logger.info(f"Running SonarQube scanner with command: {' '.join(log_command)}")
        
        try:
            result = subprocess.run(
                command,
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=SONAR_SCANNER_TIMEOUT
            )
            
            output = result.stdout
            if result.stderr:
                logger.warning(f"SonarQube scanner stderr: {result.stderr}")
                output += "\n" + result.stderr
                
            if result.returncode == 0:
                logger.info("SonarQube analysis completed successfully")
                
                # Extract task ID and URL from output if available
                task_id_match = re.search(r'task\?id=([a-zA-Z0-9_-]+)', output)
                if task_id_match:
                    task_id = task_id_match.group(1)
                    logger.info(f"SonarQube analysis task ID: {task_id}")
                
                dashboard_url_match = re.search(r'(https?://[^\s]+)', output)
                if dashboard_url_match:
                    dashboard_url = dashboard_url_match.group(1)
                    logger.info(f"SonarQube dashboard URL: {dashboard_url}")
                
                return True, output
            else:
                logger.error(f"SonarQube analysis failed with code {result.returncode}")
                return False, output
                
        except subprocess.TimeoutExpired:
            logger.error(f"SonarQube analysis timed out after {SONAR_SCANNER_TIMEOUT} seconds")
            return False, "Analysis timed out"
        except Exception as e:
            logger.error(f"Error running SonarQube analysis: {e}")
            return False, str(e)

    def _get_analysis_results(self, project_key: str) -> Dict[str, Any]:
        """
        Get analysis results from the SonarQube API.
        
        Args:
            project_key: SonarQube project key
            
        Returns:
            Dictionary containing analysis results
        """
        if not self.auth_header:
            logger.warning("Cannot fetch analysis results without authentication")
            return {
                "issues": [],
                "measures": [],
                "error": "Authentication required to fetch results from SonarQube API"
            }
            
        results = {
            "issues": [],
            "measures": [],
            "hotspots": [],
            "project_info": {}
        }
        
        # Wait a moment for analysis to be processed on the server
        time.sleep(2)
        
        try:
            # Get project info
            project_response = requests.get(
                f"{self.sonar_url}/api/components/show",
                params={"component": project_key},
                headers=self.auth_header,
                timeout=SONAR_API_TIMEOUT
            )
            
            if project_response.status_code == 200:
                results["project_info"] = project_response.json().get("component", {})
                logger.info(f"Retrieved project info for {project_key}")
            else:
                logger.warning(f"Failed to get project info: {project_response.status_code}")
            
            # Get issues
            issues_response = requests.get(
                f"{self.sonar_url}/api/issues/search",
                params={"componentKeys": project_key, "ps": 500},  # Page size 500
                headers=self.auth_header,
                timeout=SONAR_API_TIMEOUT
            )
            
            if issues_response.status_code == 200:
                results["issues"] = issues_response.json().get("issues", [])
                logger.info(f"Retrieved {len(results['issues'])} issues for {project_key}")
            else:
                logger.warning(f"Failed to get issues: {issues_response.status_code}")
            
            # Get measures
            metrics_str = ",".join(QUALITY_METRICS)
            
            measures_response = requests.get(
                f"{self.sonar_url}/api/measures/component",
                params={"component": project_key, "metricKeys": metrics_str},
                headers=self.auth_header,
                timeout=SONAR_API_TIMEOUT
            )
            
            if measures_response.status_code == 200:
                component = measures_response.json().get("component", {})
                results["measures"] = component.get("measures", [])
                logger.info(f"Retrieved {len(results['measures'])} measures for {project_key}")
            else:
                logger.warning(f"Failed to get measures: {measures_response.status_code}")
                
            # Get security hotspots
            hotspots_response = requests.get(
                f"{self.sonar_url}/api/hotspots/search",
                params={"projectKey": project_key, "ps": 500},  # Page size 500
                headers=self.auth_header,
                timeout=SONAR_API_TIMEOUT
            )
            
            if hotspots_response.status_code == 200:
                results["hotspots"] = hotspots_response.json().get("hotspots", [])
                logger.info(f"Retrieved {len(results['hotspots'])} security hotspots for {project_key}")
            else:
                logger.warning(f"Failed to get security hotspots: {hotspots_response.status_code}")
                
            return results
            
        except RequestException as e:
            logger.error(f"Error accessing SonarQube API: {e}")
            results["error"] = f"Error accessing SonarQube API: {str(e)}"
            return results
        except Exception as e:
            logger.error(f"Unexpected error fetching analysis results: {e}")
            results["error"] = f"Unexpected error: {str(e)}"
            return results

    def _parse_issues(self, issues: List[Dict[str, Any]]) -> List[SonarQubeIssue]:
        """
        Parse SonarQube API issues into SonarQubeIssue objects.
        
        Args:
            issues: List of issues from the SonarQube API
            
        Returns:
            List of SonarQubeIssue objects
        """
        parsed_issues = []
        
        for issue in issues:
            try:
                parsed_issue = SonarQubeIssue(
                    issue_key=issue.get("key", ""),
                    component=issue.get("component", ""),
                    project=issue.get("project", ""),
                    rule=issue.get("rule", ""),
                    severity=issue.get("severity", ""),
                    type=issue.get("type", ""),
                    message=issue.get("message", ""),
                    line=issue.get("line"),
                    effort=issue.get("effort", ""),
                    debt=issue.get("debt", ""),
                    tags=issue.get("tags", []),
                    creation_date=issue.get("creationDate", ""),
                    # Code snippets would need to be retrieved separately
                    code_snippet=None
                )
                
                # Extract fix suggestions from rule description if available
                if "flows" in issue and issue["flows"]:
                    for flow in issue["flows"]:
                        if "descriptions" in flow and flow["descriptions"]:
                            for desc in flow["descriptions"]:
                                if desc.get("type") == "FIX":
                                    parsed_issue.fix_suggestion = desc.get("text", "")
                                    break
                
                parsed_issues.append(parsed_issue)
            except Exception as e:
                logger.error(f"Error parsing issue: {e}")
                continue
                
        # Sort issues by severity
        return sorted(
            parsed_issues,
            key=lambda x: IssueSeverity[x.severity].value if x.severity in IssueSeverity.__members__ else 999
        )

    def _parse_measures(self, measures: List[Dict[str, Any]], component: str) -> List[SonarMeasure]:
        """
        Parse SonarQube API measures into SonarMeasure objects.
        
        Args:
            measures: List of measures from the SonarQube API
            component: Component the measures apply to
            
        Returns:
            List of SonarMeasure objects
        """
        parsed_measures = []
        
        # Descriptions for metrics
        metric_descriptions = {
            "reliability_rating": "Reliability Rating (A = best, E = worst)",
            "security_rating": "Security Rating (A = best, E = worst)",
            "sqale_rating": "Maintainability Rating (A = best, E = worst)",
            "coverage": "Test Coverage Percentage",
            "duplicated_lines_density": "Duplicated Lines Percentage",
            "bugs": "Number of Bugs",
            "vulnerabilities": "Number of Vulnerabilities",
            "code_smells": "Number of Code Smells",
            "sqale_index": "Technical Debt in minutes",
            "ncloc": "Number of Lines of Code",
            "cognitive_complexity": "Cognitive Complexity"
        }
        
        for measure in measures:
            metric = measure.get("metric", "")
            value = measure.get("value")
            best_value = measure.get("bestValue", False)
            
            # Convert rating values from numbers to letters
            if metric.endswith("_rating") and value:
                try:
                    rating_val = float(value)
                    # SonarQube ratings: 1=A, 2=B, 3=C, 4=D, 5=E
                    if 1 <= rating_val <= 5:
                        value = chr(ord('A') + int(rating_val) - 1)
                except (ValueError, TypeError):
                    pass
            
            # For numeric values, try to convert to the appropriate type
            elif value and isinstance(value, str):
                try:
                    if "." in value:
                        value = float(value)
                    else:
                        value = int(value)
                except (ValueError, TypeError):
                    pass
            
            parsed_measure = SonarMeasure(
                metric=metric,
                value=value,
                component=component,
                best_value=best_value,
                description=metric_descriptions.get(metric)
            )
            
            parsed_measures.append(parsed_measure)
            
        return parsed_measures

    def _create_quality_report(
        self, 
        issues: List[SonarQubeIssue], 
        measures: List[SonarMeasure],
        hotspots: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a quality report from the analysis results.
        
        Args:
            issues: List of issues found
            measures: List of quality measures
            hotspots: List of security hotspots
            
        Returns:
            Dictionary containing a comprehensive quality report
        """
        # Convert measures to a more usable format
        measures_dict = {m.metric: m.value for m in measures}
        
        # Group issues by type
        issues_by_type = {}
        for issue_type in ISSUE_TYPES:
            issues_by_type[issue_type] = [i for i in issues if i.type == issue_type]
        
        # Group issues by severity
        issues_by_severity = {}
        for severity in IssueSeverity.__members__:
            issues_by_severity[severity] = [i for i in issues if i.severity == severity]
            
        # Group issues by component (file)
        issues_by_component = {}
        for issue in issues:
            if issue.component not in issues_by_component:
                issues_by_component[issue.component] = []
            issues_by_component[issue.component].append(issue)
        
        # Sort components by issue count
        components_by_issue_count = sorted(
            issues_by_component.keys(),
            key=lambda c: len(issues_by_component[c]),
            reverse=True
        )
        
        # Get file-level metrics if available
        file_metrics = {}
        for measure in measures:
            component = measure.component
            if component not in file_metrics:
                file_metrics[component] = {}
            file_metrics[component][measure.metric] = measure.value
        
        # Calculate overall quality score (weighted average of ratings)
        overall_score = None
        if all(key in measures_dict for key in ['reliability_rating', 'security_rating', 'sqale_rating']):
            try:
                # Convert letter ratings back to numbers for calculation
                r_rating = ord(measures_dict['reliability_rating']) - ord('A') + 1 if isinstance(measures_dict['reliability_rating'], str) else int(measures_dict['reliability_rating'])
                s_rating = ord(measures_dict['security_rating']) - ord('A') + 1 if isinstance(measures_dict['security_rating'], str) else int(measures_dict['security_rating'])
                m_rating = ord(measures_dict['sqale_rating']) - ord('A') + 1 if isinstance(measures_dict['sqale_rating'], str) else int(measures_dict['sqale_rating'])
                
                # Weight: 40% maintainability, 30% reliability, 30% security
                weighted_avg = (0.3 * r_rating + 0.3 * s_rating + 0.4 * m_rating)
                
                # Convert back to letter grade
                overall_score = chr(ord('A') + int(round(weighted_avg)) - 1)
            except (ValueError, TypeError):
                pass
                
        # Prepare the report
        report = {
            "summary": {
                "overall_score": overall_score,
                "total_issues": len(issues),
                "reliability_rating": measures_dict.get("reliability_rating"),
                "security_rating": measures_dict.get("security_rating"),
                "maintainability_rating": measures_dict.get("sqale_rating"),
                "lines_of_code": measures_dict.get("ncloc"),
                "bugs": measures_dict.get("bugs"),
                "vulnerabilities": measures_dict.get("vulnerabilities"),
                "code_smells": measures_dict.get("code_smells"),
                "security_hotspots": len(hotspots),
                "test_coverage": measures_dict.get("coverage"),
                "duplicated_lines": measures_dict.get("duplicated_lines_density"),
                "technical_debt_in_days": (int(measures_dict.get("sqale_index", 0)) / 480) if measures_dict.get("sqale_index") else None,
            },
            "issues_by_type": {
                issue_type: {
                    "count": len(issues_by_type[issue_type]),
                    "category": ISSUE_TYPES[issue_type],
                } for issue_type in ISSUE_TYPES
            },
            "issues_by_severity": {
                severity: len(issues_by_severity[severity]) for severity in IssueSeverity.__members__
            },
            "most_problematic_files": [
                {
                    "component": component,
                    "issue_count": len(issues_by_component[component]),
                    "issues_by_severity": {
                        severity: len([i for i in issues_by_component[component] if i.severity == severity])
                        for severity in IssueSeverity.__members__
                    }
                }
                for component in components_by_issue_count[:10]  # Top 10 most problematic files
            ],
            "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        return report

    def analyze_project(
        self, 
        project_dir: Path, 
        project_key: Optional[str] = None,
        additional_properties: Dict[str, str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Run SonarQube analysis on a project.
        
        Args:
            project_dir: Project directory to analyze
            project_key: SonarQube project key (if None, will be extracted from properties)
            additional_properties: Additional properties to pass to the scanner
            
        Returns:
            Tuple containing:
            - Boolean indicating success or failure
            - Dictionary with analysis results
        """
        project_dir = Path(project_dir)
        if not project_dir.exists():
            return False, {"error": f"Project directory does not exist: {project_dir}"}
            
        # Get properties
        properties = self._get_sonar_project_properties(project_dir)
        
        # Override with additional properties if provided
        if additional_properties:
            properties.update(additional_properties)
            
        # Get project key from properties if not provided
        if not project_key and "sonar.projectKey" in properties:
            project_key = properties["sonar.projectKey"]
            
        if not project_key:
            return False, {"error": "Project key is required but not provided"}
            
        # Run the scanner
        success, output = self._run_sonar_scanner(project_dir, additional_properties)
        
        if not success:
            return False, {
                "error": "SonarQube analysis failed",
                "output": output
            }
            
        # Get results from API if authentication is provided
        if self.auth_header:
            analysis_results = self._get_analysis_results(project_key)
            
            # Parse issues and measures
            issues = self._parse_issues(analysis_results.get("issues", []))
            
            # Extract the component name from the project_info
            component = analysis_results.get("project_info", {}).get("key", project_key)
            measures = self._parse_measures(analysis_results.get("measures", []), component)
            
            # Create quality report
            quality_report = self._create_quality_report(
                issues, 
                measures, 
                analysis_results.get("hotspots", [])
            )
            
            return True, {
                "success": True,
                "project_key": project_key,
                "scanner_output": output,
                "issues": [asdict(issue) for issue in issues],
                "measures": [asdict(measure) for measure in measures],
                "hotspots": analysis_results.get("hotspots", []),
                "quality_report": quality_report,
                "error": analysis_results.get("error")
            }
        else:
            # Return limited results without API access
            return True, {
                "success": True,
                "project_key": project_key,
                "scanner_output": output,
                "note": "Limited results due to missing authentication for SonarQube API"
            }

    def get_analysis_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of the analysis results.
        
        Args:
            analysis_results: Results from analyze_project
            
        Returns:
            Dictionary with summary information
        """
        if not analysis_results.get("success", False):
            return {
                "status": "failed",
                "error": analysis_results.get("error", "Unknown error")
            }
            
        if "quality_report" in analysis_results:
            # We already have a quality report, return its summary
            return {
                "status": "success",
                "summary": analysis_results["quality_report"]["summary"]
            }
            
        # Limited information available
        return {
            "status": "success",
            "note": "Limited summary available without API access",
            "project_key": analysis_results.get("project_key")
        }
            
    def get_quality_report(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a detailed quality report from the analysis results.
        
        Args:
            analysis_results: Results from analyze_project
            
        Returns:
            Dictionary with quality report
        """
        if not analysis_results.get("success", False):
            return {
                "status": "failed",
                "error": analysis_results.get("error", "Unknown error")
            }
            
        if "quality_report" in analysis_results:
            return {
                "status": "success",
                "quality_report": analysis_results["quality_report"]
            }
            
        # Limited information available
        return {
            "status": "success",
            "note": "Quality report unavailable without API access",
            "project_key": analysis_results.get("project_key")
        }
            
    def get_tech_debt_report(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a technical debt report from the analysis results.
        
        This provides a specialized view focused on technical debt.
        
        Args:
            analysis_results: Results from analyze_project
            
        Returns:
            Dictionary with technical debt information
        """
        if not analysis_results.get("success", False):
            return {
                "status": "failed",
                "error": analysis_results.get("error", "Unknown error")
            }
            
        if "issues" not in analysis_results:
            return {
                "status": "success",
                "note": "Technical debt report unavailable without API access",
                "project_key": analysis_results.get("project_key")
            }
            
        # Create specialized tech debt report
        issues = [SonarQubeIssue(**issue) if isinstance(issue, dict) else issue 
                 for issue in analysis_results.get("issues", [])]
        
        # Group issues by rule
        rules = {}
        for issue in issues:
            if issue.rule not in rules:
                rules[issue.rule] = {
                    "count": 0,
                    "debt": 0,
                    "type": issue.type,
                    "example": issue
                }
            rules[issue.rule]["count"] += 1
            
            # Extract debt value in minutes
            if issue.debt:
                try:
                    # Parse time format like "1h 30min"
                    debt_str = issue.debt
                    debt_minutes = 0
                    
                    if "d" in debt_str:
                        days_part = debt_str.split("d")[0]
                        if days_part.strip():
                            debt_minutes += int(days_part.strip()) * 8 * 60  # 8 hours per day
                        debt_str = debt_str.split("d")[1]
                        
                    if "h" in debt_str:
                        hours_part = debt_str.split("h")[0]
                        if hours_part.strip():
                            debt_minutes += int(hours_part.strip()) * 60
                        debt_str = debt_str.split("h")[1]
                        
                    if "min" in debt_str:
                        min_part = debt_str.split("min")[0]
                        if min_part.strip():
                            debt_minutes += int(min_part.strip())
                    
                    rules[issue.rule]["debt"] += debt_minutes
                except (ValueError, IndexError):
                    pass
        
        # Sort rules by total debt
        sorted_rules = sorted(
            rules.items(),
            key=lambda x: x[1]["debt"],
            reverse=True
        )
        
        # Extract measures
        measures = {}
        for measure in analysis_results.get("measures", []):
            if isinstance(measure, dict):
                measures[measure.get("metric")] = measure.get("value")
            else:
                measures[measure.metric] = measure.value
                
        # Create tech debt report
        tech_debt_report = {
            "total_debt_minutes": measures.get("sqale_index"),
            "total_debt_days": float(measures.get("sqale_index", 0)) / (8 * 60) if measures.get("sqale_index") else None,
            "maintainability_rating": measures.get("sqale_rating"),
            "code_smells": measures.get("code_smells", 0),
            "top_tech_debt_rules": [
                {
                    "rule": rule,
                    "count": data["count"],
                    "debt_minutes": data["debt"],
                    "debt_days": data["debt"] / (8 * 60),
                    "type": data["type"],
                    "example_message": data["example"].message
                }
                for rule, data in sorted_rules[:10]  # Top 10 rules by debt
            ],
            "scan_time": analysis_results.get("quality_report", {}).get("scan_time", 
                         datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        }
        
        return {
            "status": "success",
            "tech_debt_report": tech_debt_report
        }


def get_sonar_analyzer(app=None):
    """
    Get the SonarQube analyzer instance.
    
    If running within a Flask application, retrieves or creates the
    analyzer instance and attaches it to the application.
    
    Args:
        app: Optional Flask application
        
    Returns:
        SonarQubeAnalyzer instance
    """
    if app:
        # Check if analyzer already exists in app context
        if hasattr(app, 'sonar_analyzer'):
            return app.sonar_analyzer
            
        # Create and store analyzer
        base_path = getattr(app.config, "BASE_DIR", Path("."))
        
        # Get SonarQube settings from environment or config
        sonar_url = os.environ.get("SONAR_HOST_URL") or app.config.get("SONAR_URL", DEFAULT_SONAR_URL)
        sonar_token = os.environ.get("SONAR_TOKEN") or app.config.get("SONAR_TOKEN")
        
        analyzer = SonarQubeAnalyzer(
            base_path=base_path,
            sonar_url=sonar_url,
            sonar_token=sonar_token
        )
        
        app.sonar_analyzer = analyzer
        return analyzer
    else:
        # Create standalone analyzer
        base_path = Path(".")
        sonar_url = os.environ.get("SONAR_HOST_URL", DEFAULT_SONAR_URL)
        sonar_token = os.environ.get("SONAR_TOKEN")
        
        return SonarQubeAnalyzer(
            base_path=base_path,
            sonar_url=sonar_url,
            sonar_token=sonar_token
        )


# Command line interface for standalone usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SonarQube Code Quality Analyzer")
    parser.add_argument("path", help="Path to project to analyze")
    parser.add_argument("--key", help="SonarQube project key")
    parser.add_argument("--url", help="SonarQube server URL", default=os.environ.get("SONAR_HOST_URL", DEFAULT_SONAR_URL))
    parser.add_argument("--token", help="SonarQube authentication token", default=os.environ.get("SONAR_TOKEN"))
    parser.add_argument("--report", choices=["full", "summary", "tech-debt"], default="summary", 
                        help="Type of report to generate")
    parser.add_argument("--output", help="Output file path (defaults to stdout)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create analyzer
    analyzer = SonarQubeAnalyzer(
        base_path=Path(args.path).parent,
        sonar_url=args.url,
        sonar_token=args.token
    )
    
    # Run analysis
    success, results = analyzer.analyze_project(
        project_dir=Path(args.path),
        project_key=args.key
    )
    
    # Generate report
    if args.report == "summary":
        report = analyzer.get_analysis_summary(results)
    elif args.report == "tech-debt":
        report = analyzer.get_tech_debt_report(results)
    else:  # full
        report = results
    
    # Output report
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to {args.output}")
    else:
        print(json.dumps(report, indent=2))