"""
Enhanced GPT4All Code Analysis Module

This module provides code analysis capabilities using a local GPT4All API server.
It specializes in analyzing code against predefined requirements and provides a
detailed breakdown of which requirements are met by frontend and backend code.
"""

import os
import json
import logging
import asyncio
import time
import re
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Set, Union
from functools import wraps

import aiohttp
from flask import request, render_template, url_for, Blueprint, current_app, jsonify, redirect

# Set up module-level logger
logger = logging.getLogger(__name__)

# Blueprint for routes
gpt4all_bp = Blueprint("gpt4all", __name__)


@dataclass
class AnalysisIssue:
    """
    Represents a single issue discovered by GPT4All analysis.
    """
    filename: str
    line_number: int
    issue_text: str
    severity: str  # HIGH, MEDIUM, LOW, INFO
    confidence: str  # HIGH, MEDIUM, LOW
    issue_type: str
    line_range: List[int]
    code: str
    tool: str = "GPT4All"
    suggested_fix: Optional[str] = None
    explanation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class AnalysisConfig:
    """Configuration for the GPT4All analyzer."""
    api_url: str = field(default_factory=lambda: os.getenv("GPT4ALL_API_URL", "http://localhost:4891/v1"))
    model_name: str = field(default_factory=lambda: os.getenv("GPT4ALL_MODEL", "deepseek-r1-distill-qwen-7b"))
    max_tokens: int = 4096
    request_timeout: int = 60
    max_retries: int = 3
    retry_delay: int = 2
    concurrent_requests: int = 2  # Reduced to avoid overwhelming server


# Error handler decorator
def error_handler(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {e}")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"error": str(e)}), 500
            return render_template("500.html", error=str(e)), 500
    return wrapped


class GPT4AllAnalyzer:
    """
    Analyzes code using a local GPT4All API server.
    Supports requirements analysis for frontend and backend code.
    """

    @staticmethod
    def adjust_path(p: Path) -> Path:
        """
        Correctly adjusts paths containing "z_interface_app" directory.
        """
        if not p:
            return Path.cwd()
            
        try:
            abs_path = p.resolve()
            parts = list(abs_path.parts)
            
            # Find the z_interface_app component if it exists
            z_app_index = -1
            for i, part in enumerate(parts):
                if part.lower() == "z_interface_app":
                    z_app_index = i
                    break
                    
            # If found, reconstruct the path without it
            if z_app_index >= 0:
                new_parts = parts[:z_app_index] + parts[z_app_index+1:]
                adjusted = Path(*new_parts)
                logger.info(f"Adjusted path from {abs_path} to {adjusted}")
                return adjusted
            
            return abs_path
                
        except Exception as e:
            logger.error(f"Error adjusting path {p}: {e}")
            return p

    def __init__(self, base_path: Union[Path, str]):
        """
        Initialize the analyzer with a base path and API settings.
        """
        # Convert string to Path if needed
        if isinstance(base_path, str):
            base_path = Path(base_path)
            
        self.base_path = self.adjust_path(base_path)
        self.config = AnalysisConfig()
        self.semaphore = asyncio.Semaphore(self.config.concurrent_requests)
        
        # Check if the base path exists
        if not self.base_path.exists():
            logger.warning(f"Base path does not exist: {self.base_path}")
            if not self.base_path.is_absolute():
                self.base_path = Path.cwd() / self.base_path
                logger.info(f"Using current directory + base path: {self.base_path}")

        # Define prompt templates
        self.prompts = {
            "security": (
                "Analyze the following code for security vulnerabilities. "
                "Focus on input validation, authentication/authorization, data exposure, "
                "cryptographic issues, and configuration security. "
                "Return JSON: {\"issues\": [{\"filename\": ..., \"line_number\": ..., "
                "\"issue_text\": ..., \"severity\": ..., \"confidence\": ..., \"issue_type\": ..., "
                "\"line_range\": ..., \"code\": ..., \"suggested_fix\": ..., \"explanation\": ...}]}"
            ),
            "features": (
                "Analyze the following code and suggest feature improvements. "
                "Focus on performance optimizations, error handling, logging, testing coverage, "
                "and code organization. "
                "Return JSON: {\"issues\": [{\"filename\": ..., \"line_number\": ..., "
                "\"issue_text\": ..., \"severity\": ..., \"confidence\": ..., \"issue_type\": ..., "
                "\"line_range\": ..., \"code\": ..., \"suggested_fix\": ..., \"explanation\": ...}]}"
            ),
            "quality": (
                "Review the following code for quality and best practices. "
                "Focus on code structure, naming conventions, function design, documentation, "
                "and maintainability. "
                "Return JSON: {\"issues\": [{\"filename\": ..., \"line_number\": ..., "
                "\"issue_text\": ..., \"severity\": ..., \"confidence\": ..., \"issue_type\": ..., "
                "\"line_range\": ..., \"code\": ..., \"suggested_fix\": ..., \"explanation\": ...}]}"
            ),
            "requirements": (
                "Analyze the following code against these requirements:\n"
                "{requirements}\n\n"
                "For each requirement, determine if the code meets the requirement.\n"
                "Return a JSON object with an 'issues' array. Each issue should have these fields:\n"
                "- filename: the file being analyzed\n"
                "- line_number: relevant line number or -1 if N/A\n"
                "- issue_text: description of the requirement\n"
                "- severity: 'INFO' for met requirements, 'HIGH' for unmet\n"
                "- confidence: 'HIGH', 'MEDIUM', or 'LOW'\n"
                "- issue_type: 'requirement_check'\n"
                "- line_range: array of relevant line numbers\n"
                "- code: relevant code or empty string\n"
                "- suggested_fix: suggestions for improvement\n"
                "- explanation: detailed explanation\n\n"
                "Example format: {\"issues\": [{\"filename\": \"app.py\", \"line_number\": 10, ...}]}"
            )
        }

    async def _api_request(self, prompt: str) -> Optional[str]:
        """
        Sends a request to the GPT4All API with the given prompt.
        Includes retry logic for transient failures.
        """
        for attempt in range(self.config.max_retries):
            try:
                async with self.semaphore:  # Limit concurrent requests
                    async with aiohttp.ClientSession() as session:
                        payload = {
                            "model": self.config.model_name,
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": self.config.max_tokens,
                            "temperature": 0.1,  # Lower temperature for more deterministic responses
                        }
                        logger.info(f"Sending request to GPT4All API at {self.config.api_url}")
                        
                        try:
                            async with session.post(
                                f"{self.config.api_url}/chat/completions", 
                                json=payload,
                                timeout=aiohttp.ClientTimeout(total=self.config.request_timeout)
                            ) as resp:
                                if resp.status != 200:
                                    error_text = await resp.text()
                                    logger.error(f"GPT4All API request failed with status {resp.status}: {error_text}")
                                    if resp.status in {429, 500, 502, 503, 504}:
                                        wait_time = self.config.retry_delay * (attempt + 1)
                                        logger.warning(f"Retrying in {wait_time}s (attempt {attempt+1}/{self.config.max_retries})")
                                        await asyncio.sleep(wait_time)
                                        continue
                                    return None
                                    
                                data = await resp.json()
                                if not data.get("choices"):
                                    logger.error(f"Unexpected API response format: {data}")
                                    return None
                                    
                                return data["choices"][0]["message"]["content"]
                        except aiohttp.ClientError as e:
                            logger.error(f"Connection error: {e}")
                            await asyncio.sleep(self.config.retry_delay)
                            continue
                            
            except asyncio.TimeoutError:
                logger.error(f"Request timed out (attempt {attempt+1}/{self.config.max_retries})")
                await asyncio.sleep(self.config.retry_delay)
            except Exception as e:
                logger.exception(f"API request error: {e}")
                await asyncio.sleep(self.config.retry_delay)
                
        logger.error(f"All {self.config.max_retries} attempts failed")
        return None

    def _extract_json_from_markdown(self, text: str) -> str:
        """
        Extract JSON from markdown code blocks or return the original text.
        """
        json_block_markers = [
            ('```json', '```'),
            ('```', '```'),
            ('{', '}')
        ]
        
        for start_marker, end_marker in json_block_markers:
            if start_marker in text and end_marker in text:
                try:
                    start_idx = text.find(start_marker) + len(start_marker)
                    end_idx = text.rfind(end_marker)
                    
                    if start_idx < end_idx:
                        json_content = text[start_idx:end_idx].strip()
                        # Verify it's valid JSON
                        json.loads(json_content)
                        return json_content
                except (ValueError, json.JSONDecodeError):
                    continue
        
        # Try regex patterns if the above doesn't work
        pattern_options = [
            r'```json\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
            r'({[\s\S]*})'
        ]
        
        for pattern in pattern_options:
            match = re.search(pattern, text)
            if match:
                potential_json = match.group(1)
                try:
                    json.loads(potential_json)
                    return potential_json
                except json.JSONDecodeError:
                    continue
        
        return text

    def _create_fallback_result(self, text: str, file_path: Path) -> Dict[str, Any]:
        """
        Create a fallback result dictionary when JSON parsing fails.
        """
        return {
            "issues": [{
                "filename": file_path.name,
                "line_number": 0,
                "issue_text": "Analysis response could not be parsed as JSON",
                "severity": "MEDIUM",
                "confidence": "LOW",
                "issue_type": "parser_error",
                "line_range": [0],
                "code": "",
                "suggested_fix": "Please review the full text analysis manually",
                "explanation": text[:500] + ("..." if len(text) > 500 else "")
            }]
        }

    def _detect_language(self, file_path: Path) -> str:
        """
        Detect the programming language based on file extension.
        """
        ext = file_path.suffix.lower()
        
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript (React)',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript (React)',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.sass': 'Sass',
            '.vue': 'Vue',
            '.svelte': 'Svelte',
            '.json': 'JSON',
            '.md': 'Markdown',
            '.sql': 'SQL',
            '.c': 'C',
            '.cpp': 'C++',
            '.cs': 'C#',
            '.java': 'Java',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.php': 'PHP',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.rs': 'Rust',
        }
        
        return language_map.get(ext, 'Unknown')

    def _should_skip_file(self, file_path: Path) -> bool:
        """
        Check if a file should be skipped (too large, binary, etc.).
        """
        # Skip files over 500KB
        if file_path.stat().st_size > 500 * 1024:
            logger.info(f"Skipping large file: {file_path} ({file_path.stat().st_size / 1024:.1f} KB)")
            return True
            
        # Skip common binary file types
        binary_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.gif', '.zip', '.tar', '.gz', 
                             '.exe', '.dll', '.so', '.class', '.pyc', '.pyd'}
        if file_path.suffix.lower() in binary_extensions:
            return True
            
        # Try to read the first few bytes to check for binary content
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                # Check if the chunk contains null bytes (common in binary files)
                if b'\x00' in chunk:
                    logger.info(f"Skipping binary file: {file_path}")
                    return True
        except Exception:
            # If we can't read the file, skip it
            return True
            
        return False

    async def analyze_file(self, file_path: Path, analysis_type: str = "security", requirements: List[str] = None) -> Tuple[Dict[str, Any], str]:
        """
        Analyzes a single file using the specified analysis type.
        """
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return {}, f"File not found: {file_path}"

        try:
            # Try different encodings if UTF-8 fails
            encodings = ['utf-8', 'latin-1', 'cp1252']
            code = None
            
            for encoding in encodings:
                try:
                    code = file_path.read_text(encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if code is None:
                logger.error(f"Failed to read file with any encoding: {file_path}")
                return {}, f"Error reading file: Unable to detect encoding"
                
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return {}, f"Error reading file: {str(e)}"

        # Truncate if needed
        max_length = min(self.config.max_tokens * 3, 24000)
        if len(code) > max_length:
            truncated_length = max_length - 100
            code = code[:truncated_length] + "\n\n... (file truncated due to length constraints)"
            logger.info(f"File {file_path} truncated from {len(code)} to {truncated_length} characters")

        # Get the prompt template
        prompt_template = self.prompts.get(analysis_type)
        if not prompt_template:
            logger.warning(f"Unknown analysis type: {analysis_type}, using security analysis")
            prompt_template = self.prompts['security']
        
        # Format the prompt with requirements if needed
        if analysis_type == "requirements" and requirements:
            requirements_text = "\n".join(f"{i+1}. {req}" for i, req in enumerate(requirements))
            prompt_template = prompt_template.format(requirements=requirements_text)
            
        # Add file metadata to help with analysis
        file_info = f"File: {file_path.name}\nLanguage: {self._detect_language(file_path)}\n\n"
        prompt = f"{prompt_template}\n\n{file_info}Code:\n```\n{code}\n```"
        
        # Send request to API
        logger.info(f"Analyzing file: {file_path}")
        response = await self._api_request(prompt)
        
        if response is None:
            return {}, "Analysis failed: No response from API"

        # Try to parse the JSON response
        try:
            json_str = self._extract_json_from_markdown(response)
            result = json.loads(json_str)
            return result, "Analysis completed successfully"
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            fallback_result = self._create_fallback_result(response, file_path)
            return fallback_result, "Analysis completed with parsing issues"

    async def analyze_directory(
        self,
        directory: Optional[Path] = None,
        file_patterns: Optional[List[str]] = None,
        analysis_type: str = "security",
        requirements: Optional[List[str]] = None
    ) -> Tuple[List[AnalysisIssue], Dict[str, Any]]:
        """
        Analyze files in directory against requirements or for security/quality issues.
        
        This is a unified method that supports both the original security analysis
        and the requirements analysis functionality.
        """
        # Default parameters
        directory = directory or self.base_path
        directory = self.adjust_path(directory)
        file_patterns = file_patterns or ["*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.html", "*.svelte", "*.vue"]
        
        # Initialize counters and collections
        all_issues = []
        frontend_files = []
        backend_files = []
        frontend_met = 0
        frontend_unmet = 0
        backend_met = 0
        backend_unmet = 0
        
        # Find all files to analyze
        for root, _, files in os.walk(directory):
            for file_name in files:
                file_path = Path(root) / file_name
                
                # Skip files that should be skipped
                if self._should_skip_file(file_path):
                    continue
                
                # Check if file matches patterns
                if any(file_path.match(pattern) for pattern in file_patterns):
                    # Categorize as frontend or backend
                    if file_name.endswith(('.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.vue', '.svelte')):
                        if not any(skip in str(file_path) for skip in ['/node_modules/', '/.git/']):
                            frontend_files.append(file_path)
                    elif file_name.endswith('.py'):
                        if not any(skip in str(file_path) for skip in ['__pycache__', '/.git/']):
                            backend_files.append(file_path)
        
        # Limit files to analyze to avoid overwhelming
        frontend_files = frontend_files[:5]  # Limit to 5 frontend files
        backend_files = backend_files[:5]  # Limit to 5 backend files
        
        # Set up summary structure
        summary = {
            "total_issues": 0,
            "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0},
            "files_affected": 0,
            "issue_types": {},
            "tool_counts": {"GPT4All": 0},
            "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "start_time": datetime.now().isoformat(),
            "frontend_files": len(frontend_files),
            "backend_files": len(backend_files),
            "met_conditions": {
                "total": 0,
                "frontend": 0,
                "backend": 0
            },
            "unmet_conditions": {
                "total": 0,
                "frontend": 0,
                "backend": 0
            }
        }
        
        # Process frontend files
        for file_path in frontend_files:
            try:
                result, _ = await self.analyze_file(
                    file_path, 
                    analysis_type=analysis_type,
                    requirements=requirements
                )
                
                if "issues" in result and isinstance(result["issues"], list):
                    for issue in result["issues"]:
                        # Determine if requirement is met (if doing requirements analysis)
                        is_met = False
                        if analysis_type == "requirements":
                            severity = issue.get("severity", "").upper()
                            is_met = severity in ["INFO", "LOW"] or "met" in issue.get("issue_text", "").lower()
                            
                            if is_met:
                                frontend_met += 1
                            else:
                                frontend_unmet += 1
                        
                        # Convert numeric confidence to string format if needed
                        confidence = issue.get("confidence", "MEDIUM")
                        if isinstance(confidence, (int, float)):
                            if confidence >= 90:
                                confidence = "HIGH"
                            elif confidence >= 70:
                                confidence = "MEDIUM"
                            else:
                                confidence = "LOW"
                        
                        # Create issue object
                        issue_type = issue.get("issue_type", "unknown")
                        if analysis_type == "requirements":
                            issue_type = f"Frontend: {'MET' if is_met else 'UNMET'}"
                            
                        all_issues.append(AnalysisIssue(
                            filename=os.path.relpath(file_path, directory),
                            line_number=issue.get("line_number", 0),
                            issue_text=issue.get("issue_text", "Unknown issue"),
                            severity=issue.get("severity", "MEDIUM"),
                            confidence=str(confidence),
                            issue_type=issue_type,
                            line_range=issue.get("line_range", [issue.get("line_number", 0)]),
                            code=issue.get("code", ""),
                            tool="GPT4All",
                            suggested_fix=issue.get("suggested_fix", ""),
                            explanation=issue.get("explanation", "")
                        ))
            except Exception as e:
                logger.error(f"Error analyzing frontend file {file_path}: {e}")
        
        # Process backend files
        for file_path in backend_files:
            try:
                result, _ = await self.analyze_file(
                    file_path, 
                    analysis_type=analysis_type,
                    requirements=requirements
                )
                
                if "issues" in result and isinstance(result["issues"], list):
                    for issue in result["issues"]:
                        # Determine if requirement is met (if doing requirements analysis)
                        is_met = False
                        if analysis_type == "requirements":
                            severity = issue.get("severity", "").upper()
                            is_met = severity in ["INFO", "LOW"] or "met" in issue.get("issue_text", "").lower()
                            
                            if is_met:
                                backend_met += 1
                            else:
                                backend_unmet += 1
                        
                        # Convert numeric confidence to string format if needed
                        confidence = issue.get("confidence", "MEDIUM")
                        if isinstance(confidence, (int, float)):
                            if confidence >= 90:
                                confidence = "HIGH"
                            elif confidence >= 70:
                                confidence = "MEDIUM"
                            else:
                                confidence = "LOW"
                        
                        # Create issue object
                        issue_type = issue.get("issue_type", "unknown")
                        if analysis_type == "requirements":
                            issue_type = f"Backend: {'MET' if is_met else 'UNMET'}"
                            
                        all_issues.append(AnalysisIssue(
                            filename=os.path.relpath(file_path, directory),
                            line_number=issue.get("line_number", 0),
                            issue_text=issue.get("issue_text", "Unknown issue"),
                            severity=issue.get("severity", "MEDIUM"),
                            confidence=str(confidence),
                            issue_type=issue_type,
                            line_range=issue.get("line_range", [issue.get("line_number", 0)]),
                            code=issue.get("code", ""),
                            tool="GPT4All",
                            suggested_fix=issue.get("suggested_fix", ""),
                            explanation=issue.get("explanation", "")
                        ))
            except Exception as e:
                logger.error(f"Error analyzing backend file {file_path}: {e}")
                
        # Update summary
        end_time = datetime.now()
        summary["end_time"] = end_time.isoformat()
        summary["duration_seconds"] = (end_time - datetime.fromisoformat(summary["start_time"])).total_seconds()
        summary["total_issues"] = len(all_issues)
        summary["files_affected"] = len(set(issue.filename for issue in all_issues))
        
        # Update met/unmet conditions if doing requirements analysis
        if analysis_type == "requirements":
            summary["requirements"] = requirements or []
            summary["total_requirements"] = len(requirements or [])
            summary["met_conditions"] = {
                "total": frontend_met + backend_met,
                "frontend": frontend_met,
                "backend": backend_met
            }
            summary["unmet_conditions"] = {
                "total": frontend_unmet + backend_unmet,
                "frontend": frontend_unmet,
                "backend": backend_unmet
            }
            
        # Count by severity and issue type
        for issue in all_issues:
            # Count severity
            severity = issue.severity.upper()
            if severity in summary["severity_counts"]:
                summary["severity_counts"][severity] += 1
            
            # Count issue type
            issue_type = issue.issue_type
            summary["issue_types"][issue_type] = summary["issue_types"].get(issue_type, 0) + 1
        
        # Increment GPT4All tool count
        summary["tool_counts"]["GPT4All"] = len(all_issues)
        
        # Sort issues by severity
        sorted_issues = sorted(
            all_issues,
            key=lambda x: (
                {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}.get(x.severity.upper(), 4),
                {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(x.confidence.upper(), 3),
                x.filename,
                x.line_number
            )
        )
        
        return sorted_issues, summary


# ---------------------------------------------------------------------------- #
# Flask route for showing the form                                             #
# ---------------------------------------------------------------------------- #
@gpt4all_bp.route("/gpt4all-analysis", methods=["GET"])
@error_handler
def gpt4all_analysis_form():
    """Display the analysis form."""
    model = request.args.get("model")
    app_num = request.args.get("app_num")
    analysis_type = request.args.get("type", "requirements")
    
    if not model or not app_num:
        return render_template("500.html", error="Model and app number are required"), 400
        
    directory = get_app_directory(current_app, model, app_num)
    if not directory.exists():
        return render_template("500.html", error=f"Directory not found: {directory}"), 404
    
    # Set up empty summary with proper structure
    summary = {
        "total_issues": 0,
        "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0},
        "files_affected": 0,
        "issue_types": {},
        "tool_counts": {"GPT4All": 0},
        "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "frontend_files": 0,
        "backend_files": 0,
        "met_conditions": {"total": 0, "frontend": 0, "backend": 0},
        "unmet_conditions": {"total": 0, "frontend": 0, "backend": 0}
    }
    
    return render_template(
        "gpt4all_analysis.html",
        model=model,
        app_num=app_num,
        directory=str(directory),
        analysis_type=analysis_type,
        requirements=[],
        issues=[],
        summary=summary,
        model_info={
            "name": "DeepSeek-R1-Distill-Qwen-7B",
            "ram_required": "8 GB",
            "parameters": "7 billion",
            "type": "deepseek",
        },
        error="Enter requirements and submit to analyze code"
    )


# ---------------------------------------------------------------------------- #
# Flask route for performing analysis when form is submitted                   #
# ---------------------------------------------------------------------------- #
@gpt4all_bp.route("/gpt4all-analysis", methods=["POST"])
@error_handler
def gpt4all_analysis():
    """Automatically run analysis when requirements form is submitted."""
    try:
        model = request.form.get("model")
        app_num = request.form.get("app_num")
        analysis_type = request.form.get("type", "requirements")
        
        # Get requirements from form
        requirements_text = request.form.get("requirements", "")
        requirements = [r.strip() for r in requirements_text.strip().splitlines() if r.strip()]
        
        if not model or not app_num:
            raise ValueError("Model and app number are required")
            
        directory = get_app_directory(current_app, model, app_num)
        if not directory.exists():
            raise ValueError(f"Directory not found: {directory}")
        
        # Run analysis immediately if requirements provided
        if requirements:
            # Initialize analyzer
            analyzer = GPT4AllAnalyzer(directory)
            
            # Run analysis (using asyncio.run to handle the async function)
            issues, summary = asyncio.run(analyzer.analyze_directory(
                directory=directory, 
                analysis_type=analysis_type,
                requirements=requirements
            ))
            
            # Return results
            return render_template(
                "gpt4all_analysis.html",
                model=model,
                app_num=app_num,
                directory=str(directory),
                analysis_type=analysis_type,
                requirements=requirements,
                issues=issues,
                summary=summary,
                model_info={
                    "name": "DeepSeek-R1-Distill-Qwen-7B",
                    "ram_required": "8 GB",
                    "parameters": "7 billion",
                    "type": "deepseek",
                },
                error=None if issues else "No issues found in analysis"
            )
        else:
            # No requirements specified
            return render_template(
                "gpt4all_analysis.html",
                model=model,
                app_num=app_num,
                directory=str(directory),
                analysis_type=analysis_type,
                requirements=[],
                issues=[],
                summary={
                    "total_issues": 0,
                    "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0},
                    "files_affected": 0,
                    "issue_types": {},
                    "tool_counts": {"GPT4All": 0},
                    "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "frontend_files": 0,
                    "backend_files": 0,
                    "met_conditions": {"total": 0, "frontend": 0, "backend": 0},
                    "unmet_conditions": {"total": 0, "frontend": 0, "backend": 0}
                },
                model_info={
                    "name": "DeepSeek-R1-Distill-Qwen-7B",
                    "ram_required": "8 GB",
                    "parameters": "7 billion",
                    "type": "deepseek",
                },
                error="Please enter requirements to analyze"
            )
        
    except Exception as e:
        logger.error(f"GPT4All analysis failed: {e}")
        
        # Return error template
        return render_template(
            "gpt4all_analysis.html",
            model=model if "model" in locals() else None,
            app_num=app_num if "app_num" in locals() else None,
            directory=str(directory) if "directory" in locals() else "",
            analysis_type=analysis_type if "analysis_type" in locals() else "requirements",
            requirements=requirements if "requirements" in locals() else [],
            issues=[],
            summary={
                "total_issues": 0,
                "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0},
                "files_affected": 0,
                "issue_types": {},
                "tool_counts": {"GPT4All": 0},
                "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "met_conditions": {"total": 0, "frontend": 0, "backend": 0},
                "unmet_conditions": {"total": 0, "frontend": 0, "backend": 0}
            },
            model_info={
                "name": "DeepSeek-R1-Distill-Qwen-7B",
                "ram_required": "8 GB",
                "parameters": "7 billion",
                "type": "deepseek",
            },
            error=str(e)
        )


def get_app_directory(app, model: str, app_num: int) -> Path:
    """Helper function to get app directory path."""
    return app.config["BASE_DIR"] / f"{model}/app{app_num}"


def get_analysis_summary(issues: List[AnalysisIssue]) -> Dict[str, Any]:
    """
    Generate a summary dictionary from a list of analysis issues.
    """
    if not issues:
        return {
            "total_issues": 0,
            "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0},
            "files_affected": 0,
            "issue_types": {},
            "tool_counts": {"GPT4All": 0},
            "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "met_conditions": {"total": 0, "frontend": 0, "backend": 0},
            "unmet_conditions": {"total": 0, "frontend": 0, "backend": 0}
        }
    
    # Initialize counters for met/unmet conditions
    frontend_met = 0
    frontend_unmet = 0
    backend_met = 0
    backend_unmet = 0
    
    # Count issues by type
    issue_types = {}
    
    for issue in issues:
        if issue.issue_type.startswith("Frontend: MET"):
            frontend_met += 1
        elif issue.issue_type.startswith("Frontend: UNMET"):
            frontend_unmet += 1
        elif issue.issue_type.startswith("Backend: MET"):
            backend_met += 1
        elif issue.issue_type.startswith("Backend: UNMET"):
            backend_unmet += 1
        
        # Count by issue type
        issue_types[issue.issue_type] = issue_types.get(issue.issue_type, 0) + 1
    
    # Build summary
    summary = {
        "total_issues": len(issues),
        "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0},
        "files_affected": len(set(issue.filename for issue in issues)),
        "issue_types": issue_types,
        "tool_counts": {},
        "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "met_conditions": {
            "total": frontend_met + backend_met,
            "frontend": frontend_met,
            "backend": backend_met
        },
        "unmet_conditions": {
            "total": frontend_unmet + backend_unmet,
            "frontend": frontend_unmet,
            "backend": backend_unmet
        }
    }
    
    # Count by severity and tool
    for issue in issues:
        # Count severity
        severity = issue.severity.upper()
        if severity in summary["severity_counts"]:
            summary["severity_counts"][severity] += 1
        
        # Count tool usage
        tool = issue.tool
        summary["tool_counts"][tool] = summary["tool_counts"].get(tool, 0) + 1
    
    return summary