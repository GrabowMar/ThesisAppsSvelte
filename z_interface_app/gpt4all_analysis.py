import os
import json
import logging
import asyncio
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Set, Union

import aiohttp

# Set up module-level logger
logger = logging.getLogger(__name__)


@dataclass
class AnalysisIssue:
    """
    Represents a single issue discovered by GPT4All analysis.
    """
    filename: str
    line_number: int
    issue_text: str
    severity: str  # HIGH, MEDIUM, LOW
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
    concurrent_requests: int = 5


class GPT4AllAnalyzer:
    """
    Analyzes code using a local GPT4All API server.
    Supports security, features, and quality analysis.
    """

    @staticmethod
    def adjust_path(p: Path) -> Path:
        """
        Correctly adjusts paths containing "z_interface_app" directory.
        If the path contains a "z_interface_app" parent directory, it's removed
        while preserving the rest of the path structure.
        
        Args:
            p: Path to adjust
            
        Returns:
            Adjusted Path object
        """
        if not p:
            return Path.cwd()
            
        try:
            # Convert to absolute path
            abs_path = p.resolve()
            parts = list(abs_path.parts)
            
            # Find the z_interface_app component if it exists
            z_app_index = -1
            for i, part in enumerate(parts):
                if part.lower() == "z_interface_app":
                    z_app_index = i
                    break
                    
            # If we found z_interface_app, reconstruct the path without it
            if z_app_index >= 0:
                new_parts = parts[:z_app_index] + parts[z_app_index+1:]
                adjusted = Path(*new_parts)
                logger.info(f"Adjusted path from {abs_path} to {adjusted}")
                return adjusted
            
            # No adjustment needed
            return abs_path
                
        except Exception as e:
            logger.error(f"Error adjusting path {p}: {e}")
            return p

    def __init__(self, base_path: Union[Path, str]):
        """
        Initialize the analyzer with a base path and API settings.
        The base path is adjusted to remove any "z_interface_app" folder.
        
        Args:
            base_path: Base directory for code analysis
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

        # Define prompt templates for each analysis type
        self.prompts: Dict[str, str] = {
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
                "Return JSON: {\"suggestions\": [{\"title\": ..., \"description\": ..., "
                "\"priority\": ..., \"effort_level\": ..., \"code_example\": ...}]}"
            ),
            "quality": (
                "Review the following code for quality and best practices. "
                "Focus on code structure, naming conventions, function design, documentation, "
                "and maintainability. "
                "Return JSON: {\"issues\": [{\"area\": ..., \"description\": ..., "
                "\"severity\": ..., \"suggestion\": ..., \"code_example\": ...}]}"
            ),
        }

    async def _api_request(self, prompt: str) -> Optional[str]:
        """
        Sends a request to the GPT4All API with the given prompt.
        Includes retry logic for transient failures.
        
        Args:
            prompt: The prompt to send to the API
            
        Returns:
            Text response or None if all retries failed
        """
        for attempt in range(self.config.max_retries):
            try:
                async with self.semaphore:  # Limit concurrent requests
                    async with aiohttp.ClientSession() as session:
                        payload = {
                            "model": self.config.model_name,
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": self.config.max_tokens,
                        }
                        logger.debug(f"Sending request to GPT4All API at {self.config.api_url}")
                        
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

    async def analyze_file(self, file_path: Path, analysis_type: str = "security") -> Tuple[Dict[str, Any], str]:
        """
        Analyzes a single file using the specified analysis type.
        
        Args:
            file_path: Path to the file to analyze
            analysis_type: Type of analysis to perform ("security", "features", or "quality")
            
        Returns:
            Tuple of (parsed JSON result as a dictionary, status message)
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

        # Calculate a reasonable token limit based on file size
        # Aim for approximately 1 token per 4 characters
        max_length = min(self.config.max_tokens * 3, 24000)  # Hard cap at 24K
        if len(code) > max_length:
            truncated_length = max_length - 100  # Leave room for truncation message
            code = code[:truncated_length] + "\n\n... (file truncated due to length constraints)"
            logger.info(f"File {file_path} truncated from {len(code)} to {truncated_length} characters")

        # Get the appropriate prompt for the analysis type
        prompt_template = self.prompts.get(analysis_type)
        if not prompt_template:
            logger.warning(f"Unknown analysis type: {analysis_type}, using security analysis")
            prompt_template = self.prompts['security']
            
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
            # First try to extract JSON if it's wrapped in markdown code blocks
            json_str = self._extract_json_from_markdown(response)
            result = json.loads(json_str)
            return result, "Analysis completed successfully"
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from GPT4All: {e}\nResponse: {response[:500]}...")
            # As a fallback, try to create a simple issue from the text response
            fallback_result = self._create_fallback_result(response, file_path)
            return fallback_result, "Analysis completed with parsing issues"

    def _detect_language(self, file_path: Path) -> str:
        """
        Detect the programming language based on file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Programming language name
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

    def _extract_json_from_markdown(self, text: str) -> str:
        """
        Extract JSON from markdown code blocks or return the original text.
        
        Args:
            text: Potentially markdown-formatted text with JSON
            
        Returns:
            Extracted JSON string
        """
        # Check for JSON code blocks
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
        
        # Return original text if no JSON blocks found
        return text

    def _create_fallback_result(self, text: str, file_path: Path) -> Dict[str, Any]:
        """
        Create a fallback result dictionary when JSON parsing fails.
        
        Args:
            text: The text response from the API
            file_path: Path to the analyzed file
            
        Returns:
            A dictionary with a single issue
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
        
        # Apply path adjustment to the directory
        directory = self.adjust_path(directory)
        
        # Default file patterns cover common code file extensions
        file_patterns = file_patterns or ["*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.html", "*.svelte", "*.vue"]
        
        all_issues: List[AnalysisIssue] = []
        affected_files: Set[str] = set()
        
        summary = {
            "total_files": 0,
            "processed_files": 0,
            "error_files": 0,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "analysis_type": analysis_type
        }

        # Find all files to analyze
        files_to_analyze = []
        
        try:
            # Ensure directory exists
            if not directory.exists():
                logger.error(f"Directory does not exist: {directory}")
                raise ValueError(f"Directory does not exist: {directory}")
                
            # Traverse directory and collect files
            for root, _, files in os.walk(directory):
                for file_name in files:
                    file_path = Path(root) / file_name
                    
                    # Check if file matches any pattern
                    if any(file_path.match(pattern) for pattern in file_patterns):
                        try:
                            # Skip files that are too large or binary
                            if self._should_skip_file(file_path):
                                continue
                                
                            files_to_analyze.append(file_path)
                            if len(files_to_analyze) >= max_files:
                                logger.warning(f"Reached maximum file limit ({max_files})")
                                break
                        except Exception as e:
                            logger.error(f"Error checking file {file_path}: {e}")
                
                if len(files_to_analyze) >= max_files:
                    break
        except Exception as e:
            logger.error(f"Error traversing directory {directory}: {e}")
            raise ValueError(f"Error traversing directory: {e}")

        # Update total files count
        summary["total_files"] = len(files_to_analyze)
        
        if not files_to_analyze:
            logger.warning(f"No matching files found in directory {directory}")
            raise ValueError(f"No files matching patterns {file_patterns} found in {directory}")

        # Process files with bounded concurrency
        tasks = []
        for file_path in files_to_analyze:
            task = asyncio.create_task(self._process_file(
                file_path, directory, analysis_type, all_issues, summary, affected_files
            ))
            tasks.append(task)
            
            # Update progress if callback provided
            if progress_callback and callable(progress_callback):
                completion_percentage = (summary["processed_files"] / max(1, summary["total_files"])) * 100
                progress_callback(completion_percentage, summary["processed_files"], summary["total_files"])

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
        
        # Set end time and calculate duration
        end_time = datetime.now()
        summary["end_time"] = end_time.isoformat()
        summary["duration_seconds"] = (end_time - datetime.fromisoformat(summary["start_time"])).total_seconds()
        summary["files_affected"] = len(affected_files)
        
        # Sort issues by severity
        sorted_issues = sorted(
            all_issues,
            key=lambda x: (
                {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(x.severity, 3),
                {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(x.confidence, 3),
                x.filename,
                x.line_number
            )
        )
        
        return sorted_issues, summary

    def _should_skip_file(self, file_path: Path) -> bool:
        """
        Check if a file should be skipped (too large, binary, etc.).
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file should be skipped, False otherwise
        """
        # Skip files over 1MB
        if file_path.stat().st_size > 1024 * 1024:
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

    async def _process_file(
        self, 
        file_path: Path, 
        base_dir: Path, 
        analysis_type: str,
        all_issues: List[AnalysisIssue],
        summary: Dict[str, Any],
        affected_files: Set[str]
    ) -> None:
        """
        Process a single file and update the shared issues and summary data.
        
        Args:
            file_path: Path to the file to analyze
            base_dir: Base directory for creating relative paths
            analysis_type: Type of analysis to perform
            all_issues: List to append issues to
            summary: Summary dictionary to update
            affected_files: Set of affected files to update
        """
        try:
            result, status = await self.analyze_file(file_path, analysis_type)
            
            # Get relative path for display - without losing the directory structure
            try:
                # Compute relative path that maintains structure
                rel_path = file_path.relative_to(base_dir)
            except ValueError:
                # If not relative to base_dir, use the full path
                rel_path = file_path
                
            # Convert issues to AnalysisIssue objects
            issues_key = "issues"
            if analysis_type == "features":
                issues_key = "suggestions"
                
            if issues_key in result and isinstance(result[issues_key], list):
                for issue in result[issues_key]:
                    try:
                        issue_obj = AnalysisIssue(
                            filename=str(rel_path),
                            line_number=issue.get("line_number", 0),
                            issue_text=issue.get("issue_text", 
                                               issue.get("description", "No description provided")),
                            severity=issue.get("severity", "MEDIUM").upper(),
                            confidence=issue.get("confidence", "MEDIUM"),
                            issue_type=issue.get("issue_type", 
                                               issue.get("title", "unknown")),
                            line_range=issue.get("line_range", [issue.get("line_number", 0)]),
                            code=issue.get("code", issue.get("code_example", "")),
                            suggested_fix=issue.get("suggested_fix", 
                                                  issue.get("suggestion", None)),
                            explanation=issue.get("explanation", None)
                        )
                        all_issues.append(issue_obj)
                        affected_files.add(str(rel_path))
                        
                        # Update severity counts
                        sev = issue_obj.severity.upper()
                        if sev in summary["severity_counts"]:
                            summary["severity_counts"][sev] += 1
                        else:
                            summary["severity_counts"][sev] = 1
                    except Exception as e:
                        logger.error(f"Error processing issue for {file_path}: {e}")
                        continue
            else:
                logger.debug(f"No {issues_key} found in {file_path}: {status}")
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            summary["error_files"] += 1
        finally:
            summary["processed_files"] += 1


def get_analysis_summary(issues: List[AnalysisIssue]) -> Dict[str, Any]:
    """
    Generates a summary dictionary based on a list of AnalysisIssue objects.
    
    Args:
        issues: List of AnalysisIssue objects
        
    Returns:
        A dictionary with summary statistics
    """
    if not issues:
        return {
            "total_issues": 0,
            "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "files_affected": 0,
            "issue_types": {},
            "tool_counts": {"GPT4All": 0},
            "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    summary = {
        "total_issues": len(issues),
        "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
        "files_affected": 0,
        "issue_types": {},
        "tool_counts": {},
        "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    affected_files = set()
    for issue in issues:
        # Count affected files
        affected_files.add(issue.filename)
        
        # Count issues by severity
        sev = issue.severity.upper()
        summary["severity_counts"][sev] = summary["severity_counts"].get(sev, 0) + 1
        
        # Count issues by type
        itype = issue.issue_type
        summary["issue_types"][itype] = summary["issue_types"].get(itype, 0) + 1
        
        # Count issues by tool
        tool = issue.tool
        summary["tool_counts"][tool] = summary["tool_counts"].get(tool, 0) + 1

    summary["files_affected"] = len(affected_files)
    return summary


async def run_analysis(
    base_path: Union[Path, str],
    directory: Optional[Path] = None, 
    file_patterns: Optional[List[str]] = None,
    analysis_type: str = "security"
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Convenience function to run analysis without instantiating the class directly.
    
    Args:
        base_path: Base path for the analyzer
        directory: Directory to analyze (defaults to base_path)
        file_patterns: File patterns to include
        analysis_type: Type of analysis to perform
        
    Returns:
        Tuple of (list of issue dictionaries, summary dictionary)
    """
    analyzer = GPT4AllAnalyzer(base_path)
    issues, summary = await analyzer.analyze_directory(
        directory=directory or Path(base_path),
        file_patterns=file_patterns,
        analysis_type=analysis_type
    )
    return [issue.to_dict() for issue in issues], summary