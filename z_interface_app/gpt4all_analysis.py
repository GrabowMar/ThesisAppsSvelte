"""
Enhanced GPT4All Code Analysis Module

This module provides code analysis capabilities using a local GPT4All API server.
It specializes in analyzing code against predefined requirements and provides
simplified yes/no responses for requirement checks.
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
    concurrent_requests: int = 3  # Reduced to avoid overwhelming server


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
    def adjust_path(p: Optional[Path]) -> Path:
        """
        Correctly adjusts paths containing "z_interface_app" directory.
        
        Args:
            p: Path to adjust
            
        Returns:
            Adjusted path
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
            return p if p else Path.cwd()

    def __init__(self, base_path: Union[Path, str]):
        """
        Initialize the analyzer with a base path and API settings.
        
        Args:
            base_path: Base directory path for analysis
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
                
                # Double-check the new path
                if not self.base_path.exists():
                    logger.warning(f"Adjusted base path still does not exist: {self.base_path}")

        # Define prompt templates for requirements analysis
        self.requirements_prompt = (
            "Analyze the following code against this requirement:\n"
            "{requirement}\n\n"
            "Respond with a JSON object in this format: {{\"met\": true/false, \"confidence\": \"HIGH/MEDIUM/LOW\", \"explanation\": \"brief explanation\"}}\n"
            "where 'met' is true if the requirement is met, false otherwise.\n"
            "Use 'confidence' to indicate how certain you are about your assessment."
        )
        
        # Original security analysis prompt (kept for backward compatibility)
        self.security_prompt = (
            "Analyze the following code for security vulnerabilities.\n"
            "Return a JSON object with an 'issues' array containing security issues.\n"
            "Each issue should have: filename, line_number, issue_text, severity, confidence, issue_type, "
            "line_range, code, suggested_fix, and explanation fields.\n\n"
            "Example: {\"issues\": [{\"filename\": \"app.py\", \"line_number\": 10, ...}]}"
        )
        
        # Define other prompts for different analysis types as needed
        self.prompts = {
            "security": self.security_prompt,
            "requirements": self.requirements_prompt
        }

    async def analyze_directory(
        self,
        directory: Optional[Path] = None,
        file_patterns: Optional[List[str]] = None,
        analysis_type: str = "security",
        max_files: int = 100,
        progress_callback = None
    ) -> Tuple[List[AnalysisIssue], Dict[str, Any]]:
        """
        Recursively analyzes files within the directory that match the provided patterns.
        
        Args:
            directory: Directory to analyze (defaults to base_path)
            file_patterns: List of file patterns to include (defaults to common code files)
            analysis_type: Type of analysis to perform
            max_files: Maximum number of files to analyze
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (list of issues, summary dictionary)
        """
        # Use base_path if directory not specified
        directory = directory or self.base_path
        directory = self.adjust_path(directory)
        
        # Default file patterns cover common code file extensions
        file_patterns = file_patterns or ["*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.html", "*.svelte", "*.vue"]
        
        # Separate frontend and backend files
        frontend_files = []
        backend_files = []
        all_files = []
        
        # Find all matching files and categorize them
        try:
            # Ensure directory exists
            if not directory.exists():
                logger.error(f"Directory does not exist: {directory}")
                raise ValueError(f"Directory does not exist: {directory}")
                
            # Traverse directory and collect files
            for root, _, files in os.walk(directory):
                for file_name in files:
                    file_path = Path(root) / file_name
                    
                    # Skip if the file shouldn't be analyzed
                    if self._should_skip_file(file_path):
                        continue
                        
                    # Check if file matches any pattern
                    if any(file_path.match(pattern) for pattern in file_patterns):
                        # Categorize by file type
                        if file_name.endswith(('.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.vue', '.svelte')):
                            if not any(skip in str(file_path) for skip in ['/node_modules/', '/.git/']):
                                frontend_files.append(file_path)
                                all_files.append(file_path)
                        elif file_name.endswith('.py'):
                            if not any(skip in str(file_path) for skip in ['__pycache__', '/.git/']):
                                backend_files.append(file_path)
                                all_files.append(file_path)
                        else:
                            all_files.append(file_path)
                    
                    # Limit total files
                    if len(all_files) >= max_files:
                        break
                
                if len(all_files) >= max_files:
                    break
                    
        except Exception as e:
            logger.error(f"Error finding files: {e}")
            # Return empty results rather than raising an exception
            return [], {
                "total_issues": 0,
                "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
                "frontend_files": len(frontend_files),
                "backend_files": len(backend_files),
                "files_affected": 0,
                "issue_types": {},
                "tool_counts": {"GPT4All": 0},
                "met_conditions": {"total": 0, "frontend": 0, "backend": 0},
                "unmet_conditions": {"total": 0, "frontend": 0, "backend": 0},
                "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "error": str(e)
            }
        
        # If we're doing requirements analysis, forward to the specific method
        if analysis_type == "requirements":
            # Use default requirements if none provided
            requirements = [
                "The application must handle errors gracefully",
                "The application must sanitize user inputs",
                "The application must implement proper authentication",
                "The application must have adequate test coverage",
                "The application must follow secure coding practices"
            ]
            
            # Limit files to analyze to prevent timeout
            frontend_sample = frontend_files[:3]  # First 3 frontend files
            backend_sample = backend_files[:3]    # First 3 backend files
            
            return await self.analyze_requirements(
                directory=directory,
                requirements=requirements,
                frontend_files=frontend_sample,
                backend_files=backend_sample
            )
        
        # For other analysis types, process each file individually
        all_issues = []
        summary = {
            "total_files": len(all_files),
            "processed_files": 0,
            "total_issues": 0,
            "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "frontend_files": len(frontend_files),
            "backend_files": len(backend_files),
            "files_affected": 0,
            "issue_types": {},
            "tool_counts": {"GPT4All": 0},
            "met_conditions": {"total": 0, "frontend": 0, "backend": 0},
            "unmet_conditions": {"total": 0, "frontend": 0, "backend": 0},
            "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "start_time": datetime.now().isoformat(),
        }
        
        # Process each file and accumulate results
        for file_path in all_files[:max_files]:  # Limit to max_files
            try:
                # Read the file
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    code = f.read()
                
                # Prepare the prompt for this file
                prompt = self.prompts.get(analysis_type, self.security_prompt)
                file_prompt = (
                    f"{prompt}\n\n"
                    f"File: {file_path.name}\n"
                    f"Language: {self._detect_language(file_path)}\n\n"
                    f"Code:\n```\n{code[:5000]}{'...' if len(code) > 5000 else ''}\n```"
                )
                
                # Request analysis from API
                response = await self._api_request(file_prompt)
                if response:
                    # Parse JSON response
                    json_str = self._extract_json_from_markdown(response)
                    try:
                        result = json.loads(json_str)
                        
                        # Process issues
                        if "issues" in result and isinstance(result["issues"], list):
                            file_issues = []
                            for issue in result["issues"]:
                                # Create an AnalysisIssue object
                                issue_obj = AnalysisIssue(
                                    filename=os.path.relpath(file_path, directory),
                                    line_number=issue.get("line_number", 0),
                                    issue_text=issue.get("issue_text", "Unknown issue"),
                                    severity=issue.get("severity", "MEDIUM"),
                                    confidence=issue.get("confidence", "MEDIUM"),
                                    issue_type=issue.get("issue_type", "security_issue"),
                                    line_range=issue.get("line_range", [issue.get("line_number", 0)]),
                                    code=issue.get("code", ""),
                                    tool="GPT4All",
                                    suggested_fix=issue.get("suggested_fix", ""),
                                    explanation=issue.get("explanation", "")
                                )
                                file_issues.append(issue_obj)
                            
                            # Add issues to the global list
                            all_issues.extend(file_issues)
                            
                            # Update summary statistics
                            if file_issues:
                                for issue in file_issues:
                                    severity = issue.severity.upper()
                                    if severity in summary["severity_counts"]:
                                        summary["severity_counts"][severity] += 1
                                    
                                    # Track issue types
                                    issue_type = issue.issue_type
                                    summary["issue_types"][issue_type] = summary["issue_types"].get(issue_type, 0) + 1
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse JSON from analysis: {json_str[:100]}...")
                        # Add a fallback issue when JSON parsing fails
                        fallback_issue = AnalysisIssue(
                            filename=os.path.relpath(file_path, directory),
                            line_number=0,
                            issue_text="Failed to parse analysis results",
                            severity="MEDIUM",
                            confidence="LOW",
                            issue_type="parser_error",
                            line_range=[0],
                            code="",
                            tool="GPT4All",
                            suggested_fix="",
                            explanation=response[:300]
                        )
                        all_issues.append(fallback_issue)
                        
                        # Update summary
                        summary["severity_counts"]["MEDIUM"] += 1
                        issue_type = "parser_error"
                        summary["issue_types"][issue_type] = summary["issue_types"].get(issue_type, 0) + 1
            except Exception as e:
                logger.error(f"Error analyzing file {file_path}: {e}")
                
            # Update processed files count
            summary["processed_files"] += 1
            
            # Update progress if callback provided
            if progress_callback and callable(progress_callback):
                completion_percentage = (summary["processed_files"] / max(1, summary["total_files"])) * 100
                progress_callback(completion_percentage, summary["processed_files"], summary["total_files"])
        
        # Finalize summary
        summary["total_issues"] = len(all_issues)
        summary["files_affected"] = len(set(issue.filename for issue in all_issues))
        summary["tool_counts"]["GPT4All"] = len(all_issues)
        summary["end_time"] = datetime.now().isoformat()
        
        # Sort issues by severity
        sorted_issues = sorted(
            all_issues,
            key=lambda x: (
                {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(x.severity.upper(), 3),
                {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(x.confidence.upper(), 3),
                x.filename,
                x.line_number
            )
        )
        
        return sorted_issues, summary

    async def _api_request(self, prompt: str) -> Optional[str]:
        """
        Sends a request to the GPT4All API with the given prompt.
        Includes retry logic for transient failures.
        
        Args:
            prompt: The prompt to send to the API
            
        Returns:
            Response string or None if failed
        """
        for attempt in range(self.config.max_retries):
            try:
                async with self.semaphore:  # Limit concurrent requests
                    async with aiohttp.ClientSession() as session:
                        payload = {
                            "model": self.config.model_name,
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": self.config.max_tokens,
                            "temperature": 0.1  # Lower temperature for more deterministic responses
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
                                    # Retry on certain status codes (e.g., 429, 500, 502, 503, 504)
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
                            wait_time = self.config.retry_delay * (2 ** attempt)
                            await asyncio.sleep(wait_time)
                            continue
                            
            except asyncio.TimeoutError:
                logger.error(f"Request timed out (attempt {attempt+1}/{self.config.max_retries})")
                # Retry with exponential backoff
                wait_time = self.config.retry_delay * (2 ** attempt)
                await asyncio.sleep(wait_time)
            except Exception as e:
                logger.exception(f"Exception during GPT4All API request (attempt {attempt+1}/{self.config.max_retries}): {e}")
                # Retry with exponential backoff
                wait_time = self.config.retry_delay * (2 ** attempt)
                await asyncio.sleep(wait_time)
                
        logger.error(f"All {self.config.max_retries} attempts failed")
        return None

    def _extract_json_from_markdown(self, text: str) -> str:
        """
        Enhanced extraction of JSON from GPT4All responses, which may include
        markdown formatting, prefixes/suffixes, or other content.
        
        Args:
            text: Text response from API
            
        Returns:
            JSON string (or default JSON if not found)
        """
        if not text:
            return '{"issues": []}'
            
        # Try to extract JSON from various formats
        pattern_options = [
            r'```json\s*([\s\S]*?)\s*```',  # JSON in code block with json tag
            r'```\s*([\s\S]*?)\s*```',      # JSON in generic code block
            r'({[\s\S]*?})',                # JSON with outer braces (non-greedy match)
            r'(\[[\s\S]*?\])',              # JSON outer array (non-greedy match)
            r'({[\s\S]*})',                 # JSON with outer braces (greedy match as fallback)
            r'(\[[\s\S]*\])'                # JSON outer array (greedy fallback)
        ]
        
        for pattern in pattern_options:
            match = re.search(pattern, text)
            if match:
                potential_json = match.group(1)
                try:
                    # Verify it's valid JSON by loading it
                    json.loads(potential_json)
                    return potential_json
                except json.JSONDecodeError:
                    # Not valid JSON, continue to next pattern
                    continue
        
        # If response is for requirements checking, try to parse a simple true/false response
        if "met" in text.lower() and "requirement" in text.lower():
            meets_requirement = "meets the requirement" in text.lower() or "requirement is met" in text.lower()
            # Extract a short explanation
            explanation = ""
            lines = text.split('\n')
            for line in lines:
                if "explan" in line.lower() or "reason" in line.lower():
                    explanation = line.replace("Explanation:", "").replace("Reason:", "").strip()
                    break
            if not explanation and len(lines) > 1:
                explanation = lines[1].strip()
                
            # Sanitize for JSON
            explanation = explanation[:200].replace('\n', ' ').replace('"', '\\"')
            return f'{{\"met\": {str(meets_requirement).lower()}, \"confidence\": \"MEDIUM\", \"explanation\": \"{explanation}\" }}'
        
        # Check if the text contains keywords indicating issues
        if '"issues":' in text or "'issues':" in text:
            try:
                # Try to create a valid JSON with just an issues array by extracting fragments
                issue_pattern = r'"issue_text":\s*"([^"]*)"'
                matches = re.findall(issue_pattern, text)
                if matches:
                    issues_json = []
                    for i, match in enumerate(matches):
                        issues_json.append(
                            '{"filename": "unknown.py", '
                            f'"line_number": {i+1}, '
                            f'"issue_text": "{match}", '
                            '"severity": "MEDIUM", '
                            '"confidence": "LOW", '
                            '"issue_type": "detected_issue", '
                            f'"line_range": [{i+1}], '
                            '"code": ""}'
                        )
                    return '{"issues": [' + ', '.join(issues_json) + ']}'
                return '{"issues": []}'
            except Exception:
                pass
        
        # If no valid JSON could be extracted, return a default structure
        return '{"issues": []}'

    def _detect_language(self, file_path: Path) -> str:
        """
        Detect the programming language based on file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Detected language name
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
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file should be skipped
        """
        try:
            # Skip non-existent files
            if not file_path.exists():
                return True
                
            # Skip files over 500KB (reduced from 1MB to prevent large token usage)
            if file_path.stat().st_size > 500 * 1024:
                logger.info(f"Skipping large file: {file_path} ({file_path.stat().st_size / 1024:.1f} KB)")
                return True
                
            # Skip common binary file types and directories
            binary_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.gif', '.zip', '.tar', '.gz', 
                               '.exe', '.dll', '.so', '.class', '.pyc', '.pyd', '.min.js',
                               '.woff', '.woff2', '.ttf', '.eot', '.ico', '.webp'}
            skip_dirs = {'node_modules', '.git', '__pycache__', 'venv', 'env', '.idea', '.vscode', 
                        'dist', 'build', '.next', 'vendor'}
            
            # Check file extension
            if file_path.suffix.lower() in binary_extensions:
                return True
            
            # Check parent directories
            for part in file_path.parts:
                if part in skip_dirs:
                    return True
                
            # Try to read the first few bytes to check for binary content
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                # Check if the chunk contains null bytes (common in binary files)
                if b'\x00' in chunk:
                    logger.info(f"Skipping binary file: {file_path}")
                    return True
                    
            return False
        except Exception as e:
            logger.debug(f"Error checking file {file_path}, skipping: {e}")
            return True

    async def analyze_requirements(
        self,
        directory: Path,
        requirements: List[str],
        frontend_files: List[Path],
        backend_files: List[Path]
    ) -> Tuple[List[AnalysisIssue], Dict[str, Any]]:
        """
        Analyze code files against provided requirements, separating frontend and backend.
        
        Args:
            directory: Base directory
            requirements: List of requirement strings
            frontend_files: List of frontend files to analyze
            backend_files: List of backend files to analyze
            
        Returns:
            Tuple of (list of issues, summary dictionary)
        """
        all_issues: List[AnalysisIssue] = []
        
        # Initialize counters
        frontend_met = 0
        frontend_unmet = 0
        backend_met = 0
        backend_unmet = 0
        
        # Format the requirements as a single string
        requirements_text = "\n".join(f"{i+1}. {req}" for i, req in enumerate(requirements))
        logger.info(f"Analyzing {len(frontend_files)} frontend files and {len(backend_files)} backend files")
        
        # Prepare the prompt template with the requirements
        prompt_template = self.prompts.get("requirements", self.requirements_prompt)
        
        # Process each requirement separately for frontend files
        for req in requirements:
            req_prompt = prompt_template.format(requirement=req)
            
            # Frontend check
            if frontend_files:
                combined_code = ""
                for file_path in frontend_files[:2]:  # Limit to first 2 files
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                            code = f.read()
                            # Truncate long files
                            if len(code) > 2000:
                                code = code[:2000] + "...[truncated]"
                            combined_code += f"\n\n--- File: {file_path.name} ---\n{code}"
                    except Exception as e:
                        logger.error(f"Error reading frontend file {file_path}: {e}")
                
                if combined_code:
                    file_prompt = (
                        f"{req_prompt}\n\n"
                        f"Code Type: FRONTEND CODE\n\n"
                        f"Code:\n```\n{combined_code}\n```"
                    )
                    
                    # Request analysis
                    response = await self._api_request(file_prompt)
                    if response:
                        json_str = self._extract_json_from_markdown(response)
                        try:
                            result = json.loads(json_str)
                            is_met = result.get("met", False)
                            confidence = result.get("confidence", "LOW")
                            explanation = result.get("explanation", "No explanation provided")
                            
                            if is_met:
                                frontend_met += 1
                            else:
                                frontend_unmet += 1
                                
                            # Add requirement check as an issue
                            all_issues.append(AnalysisIssue(
                                filename="requirements.txt",
                                line_number=0,
                                issue_text=f"Requirement: {req}",
                                severity="LOW" if is_met else "HIGH",
                                confidence=confidence,
                                issue_type=f"Frontend: {'MET' if is_met else 'UNMET'}",
                                line_range=[0],
                                code="",
                                tool="GPT4All",
                                suggested_fix="",
                                explanation=explanation
                            ))
                            
                        except json.JSONDecodeError:
                            # Fallback handling
                            frontend_unmet += 1
                            all_issues.append(AnalysisIssue(
                                filename="requirements.txt",
                                line_number=0,
                                issue_text=f"Requirement: {req}",
                                severity="HIGH",
                                confidence="LOW",
                                issue_type="Frontend: UNMET",
                                line_range=[0],
                                code="",
                                tool="GPT4All",
                                explanation="Failed to parse analysis response"
                            ))
                    else:
                        # API request failed
                        frontend_unmet += 1
                        all_issues.append(AnalysisIssue(
                            filename="requirements.txt",
                            line_number=0,
                            issue_text=f"Requirement: {req}",
                            severity="HIGH",
                            confidence="LOW",
                            issue_type="Frontend: UNMET",
                            line_range=[0],
                            code="",
                            tool="GPT4All",
                            explanation="API request failed"
                        ))
            
            # Backend check (similar to frontend)
            if backend_files:
                combined_code = ""
                for file_path in backend_files[:2]:  # Limit to first 2 files
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                            code = f.read()
                            # Truncate long files
                            if len(code) > 2000:
                                code = code[:2000] + "...[truncated]"
                            combined_code += f"\n\n--- File: {file_path.name} ---\n{code}"
                    except Exception as e:
                        logger.error(f"Error reading backend file {file_path}: {e}")
                
                if combined_code:
                    file_prompt = (
                        f"{req_prompt}\n\n"
                        f"Code Type: BACKEND CODE\n\n"
                        f"Code:\n```\n{combined_code}\n```"
                    )
                    
                    # Request analysis
                    response = await self._api_request(file_prompt)
                    if response:
                        json_str = self._extract_json_from_markdown(response)
                        try:
                            result = json.loads(json_str)
                            is_met = result.get("met", False)
                            confidence = result.get("confidence", "LOW")
                            explanation = result.get("explanation", "No explanation provided")
                            
                            if is_met:
                                backend_met += 1
                            else:
                                backend_unmet += 1
                                
                            # Add requirement check as an issue
                            all_issues.append(AnalysisIssue(
                                filename="requirements.txt",
                                line_number=0,
                                issue_text=f"Requirement: {req}",
                                severity="LOW" if is_met else "HIGH",
                                confidence=confidence,
                                issue_type=f"Backend: {'MET' if is_met else 'UNMET'}",
                                line_range=[0],
                                code="",
                                tool="GPT4All",
                                suggested_fix="",
                                explanation=explanation
                            ))
                        except json.JSONDecodeError:
                            # Fallback handling
                            backend_unmet += 1
                            all_issues.append(AnalysisIssue(
                                filename="requirements.txt",
                                line_number=0,
                                issue_text=f"Requirement: {req}",
                                severity="HIGH",
                                confidence="LOW",
                                issue_type="Backend: UNMET",
                                line_range=[0],
                                code="",
                                tool="GPT4All",
                                explanation="Failed to parse analysis response"
                            ))
                    else:
                        # API request failed
                        backend_unmet += 1
                        all_issues.append(AnalysisIssue(
                            filename="requirements.txt",
                            line_number=0,
                            issue_text=f"Requirement: {req}",
                            severity="HIGH",
                            confidence="LOW",
                            issue_type="Backend: UNMET",
                            line_range=[0],
                            code="",
                            tool="GPT4All",
                            explanation="API request failed"
                        ))
        
        # Create summary with frontend/backend metrics
        summary = {
            "total_issues": len(all_issues),
            "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0},
            "files_affected": len(set(issue.filename for issue in all_issues)),
            "issue_types": {
                "Frontend: MET": frontend_met,
                "Frontend: UNMET": frontend_unmet,
                "Backend: MET": backend_met,
                "Backend: UNMET": backend_unmet
            },
            "tool_counts": {"GPT4All": len(all_issues)},
            "requirements": requirements,
            "total_requirements": len(requirements),
            "frontend_files": len(frontend_files),
            "backend_files": len(backend_files),
            "met_conditions": {
                "total": frontend_met + backend_met,
                "frontend": frontend_met,
                "backend": backend_met
            },
            "unmet_conditions": {
                "total": frontend_unmet + backend_unmet,
                "frontend": frontend_unmet,
                "backend": backend_unmet
            },
            "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat()
        }
        
        # Count severities
        for issue in all_issues:
            severity = issue.severity.upper()
            if severity in summary["severity_counts"]:
                summary["severity_counts"][severity] += 1
        
        return all_issues, summary

    async def check_requirements(self, directory: Path, requirements: List[str]) -> List[Dict[str, Any]]:
        """
        Check multiple requirements against code in the directory.
        
        Args:
            directory: Directory containing code files
            requirements: List of requirements to check
            
        Returns:
            List of dictionaries with requirement and check results
        """
        directory = directory or self.base_path
        directory = self.adjust_path(directory)
        
        # Find frontend and backend files
        frontend_files = []
        backend_files = []
        
        try:
            # Collect frontend and backend files
            for root, _, files in os.walk(directory):
                for file_name in files:
                    file_path = Path(root) / file_name
                    
                    # Skip if the file shouldn't be analyzed
                    if self._should_skip_file(file_path):
                        continue
                        
                    # Frontend files
                    if file_name.endswith(('.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.vue', '.svelte')):
                        if not any(skip in str(file_path) for skip in ['/node_modules/', '/.git/']):
                            frontend_files.append(file_path)
                    # Backend files
                    elif file_name.endswith('.py'):
                        if not any(skip in str(file_path) for skip in ['__pycache__', '/.git/']):
                            backend_files.append(file_path)
                            
            logger.info(f"Found {len(frontend_files)} frontend files and {len(backend_files)} backend files")
            
            # Limit to first 10 files of each type to avoid processing too many
            frontend_files = frontend_files[:10]
            backend_files = backend_files[:10]
        except Exception as e:
            logger.error(f"Error finding files: {e}")
            return [{"requirement": req, "frontend": {"met": False, "confidence": "HIGH", "error": str(e)}, 
                    "backend": {"met": False, "confidence": "HIGH", "error": str(e)}} for req in requirements]
        
        # Check each requirement
        results = []
        for req in requirements:
            # Process frontend files for this requirement
            frontend_result = await self.check_single_requirement(frontend_files, req, is_frontend=True)
            
            # Process backend files for this requirement
            backend_result = await self.check_single_requirement(backend_files, req, is_frontend=False)
            
            # Determine overall result (met if either frontend or backend meets requirement)
            overall = frontend_result.get("met", False) or backend_result.get("met", False)
            
            results.append({
                "requirement": req,
                "frontend": frontend_result,
                "backend": backend_result,
                "overall": overall
            })
            
        return results

    async def check_single_requirement(self, code_files: List[Path], requirement: str, is_frontend: bool = False) -> Dict[str, Any]:
        """
        Check a single requirement against provided code files.
        
        Args:
            code_files: List of code files to analyze
            requirement: The requirement to check
            is_frontend: Whether these are frontend files
            
        Returns:
            Dictionary with met status and confidence
        """
        if not code_files:
            return {"met": False, "confidence": "HIGH", "error": "No files to analyze"}
        
        # Combine code from files (with limits to prevent token overload)
        combined_code = ""
        for file_path in code_files[:3]:  # Limit to first 3 files for analysis
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    code = f.read()
                    # Truncate long files
                    if len(code) > 3000:
                        code = code[:3000] + "...[truncated]"
                    combined_code += f"\n\n--- File: {file_path.name} ---\n{code}"
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
                
        if not combined_code:
            return {"met": False, "confidence": "HIGH", "error": "Could not read any files"}
            
        # Create prompt with the specific requirement
        prompt = self.requirements_prompt.format(requirement=requirement)
        file_type = "FRONTEND" if is_frontend else "BACKEND"
        file_prompt = (
            f"{prompt}\n\n"
            f"Code Type: {file_type} CODE\n\n"
            f"Code:\n```\n{combined_code}\n```"
        )
        
        # Request analysis from API
        response = await self._api_request(file_prompt)
        if not response:
            return {"met": False, "confidence": "LOW", "error": "API request failed"}
            
        # Extract JSON response
        try:
            json_str = self._extract_json_from_markdown(response)
            result = json.loads(json_str)
            return {
                "met": result.get("met", False),
                "confidence": result.get("confidence", "LOW"),
                "explanation": result.get("explanation", "")
            }
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON from analysis: {response[:100]}...")
            # Fallback to text analysis
            is_met = "requirement is met" in response.lower() or "meets the requirement" in response.lower()
            return {"met": is_met, "confidence": "LOW", "explanation": response[:200]}


def get_app_directory(app, model: str, app_num: int) -> Path:
    """Helper function to get app directory path."""
    return app.config["BASE_DIR"] / f"{model}/app{app_num}"


def get_analysis_summary(issues: List[AnalysisIssue]) -> Dict[str, Any]:
    """
    Generate a summary dictionary from a list of analysis issues.
    
    Args:
        issues: List of AnalysisIssue objects
        
    Returns:
        Summary dictionary with statistics
    """
    if not issues:
        return {
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
        "frontend_files": 0,
        "backend_files": 0,
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


# ----- API Route for GPT4All Analysis -----
@gpt4all_bp.route("/analyze-gpt4all/<string:analysis_type>", methods=["POST"])
@error_handler
def analyze_gpt4all(analysis_type: str):
    try:
        data = request.get_json()
        directory = Path(data.get("directory", current_app.config["BASE_DIR"]))
        file_patterns = data.get("file_patterns", ["*.py", "*.js", "*.ts", "*.react"])
        analyzer = GPT4AllAnalyzer(directory)
        
        # Handle asyncio in Flask properly
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        issues, summary = loop.run_until_complete(analyzer.analyze_directory(
            directory=directory, file_patterns=file_patterns, analysis_type=analysis_type
        ))
        loop.close()
        
        if not isinstance(summary, dict):
            summary = get_analysis_summary(issues)
        return jsonify({"issues": [asdict(issue) for issue in issues], "summary": summary})
    except Exception as e:
        logger.error(f"GPT4All analysis failed: {e}")
        return jsonify({"error": str(e)}), 500


# ----- Main Route for Requirements Checking -----
@gpt4all_bp.route("/gpt4all-analysis", methods=["GET", "POST"])
@error_handler
def gpt4all_analysis():
    """Flask route for checking requirements against code."""
    try:
        # Extract parameters
        model = request.args.get("model") or request.form.get("model")
        app_num = request.args.get("app_num") or request.form.get("app_num")
        
        # Validate required parameters
        if not model or not app_num:
            return render_template(
                "requirements_check.html",
                model=None,
                app_num=None,
                requirements=[],
                results=None,
                error="Model and app number are required"
            )
            
        # Find the application directory
        directory = get_app_directory(current_app, model, app_num)
        if not directory.exists():
            return render_template(
                "requirements_check.html",
                model=model,
                app_num=app_num,
                requirements=[],
                results=None,
                error=f"Directory not found: {directory}"
            )
        
        # Setup for requirements analysis
        req_list = []
        results = None
        
        # Handle requirements from POST
        if request.method == "POST" and "requirements" in request.form:
            requirements_text = request.form.get("requirements", "")
            req_list = [r.strip() for r in requirements_text.strip().splitlines() if r.strip()]
            
            if req_list:
                # Initialize analyzer
                analyzer = GPT4AllAnalyzer(directory)
                
                # Run check for each requirement using proper asyncio handling in Flask
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(analyzer.check_requirements(directory, req_list))
                loop.close()
        
        # Render template with form or results
        return render_template(
            "requirements_check.html",
            model=model,
            app_num=app_num,
            requirements=req_list,
            results=results,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Requirements check failed: {e}")
        return render_template(
            "requirements_check.html",
            model=model if "model" in locals() else None,
            app_num=app_num if "app_num" in locals() else None,
            requirements=[],
            results=None,
            error=str(e)
        )