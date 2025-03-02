import os
import json
import logging
import asyncio
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

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
    severity: str
    confidence: str
    issue_type: str
    line_range: List[int]
    code: str
    tool: str = "GPT4All"
    suggested_fix: Optional[str] = None
    explanation: Optional[str] = None


class GPT4AllAnalyzer:
    """
    Analyzes code using a local GPT4All API server.
    Supports security, features, and quality analysis.
    """

    @staticmethod
    def adjust_path(p: Path) -> Path:
        """
        If the path contains "z_interface_app" (case-insensitive), remove that component.
        """
        parts = list(p.resolve().parts)
        # Remove any part that matches "z_interface_app" (case-insensitive)
        adjusted_parts = [part for part in parts if part.lower() != "z_interface_app"]
        adjusted = Path(*adjusted_parts)
        if adjusted != p:
            logger.info(f"Adjusted base path from {p} to {adjusted}")
        return adjusted

    def __init__(self, base_path: Path):
        """
        Initialize the analyzer with a base path and API settings.
        The base path is adjusted to remove any "z_interface_app" folder.
        """
        self.base_path = self.adjust_path(base_path)
        self.api_url = os.getenv("GPT4ALL_API_URL", "http://localhost:4891/v1")
        self.model_name = "deepseek-r1-distill-qwen-7b"
        self.max_tokens = 4096

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
        Returns the text response or None if an error occurs.
        """
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/chat/completions", json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"GPT4All API request failed: {error_text}")
                        return None
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.exception(f"Exception during GPT4All API request: {e}")
            return None

    async def analyze_file(self, file_path: Path, analysis_type: str = "security") -> Tuple[Dict, str]:
        """
        Analyzes a single file using the specified analysis type.
        Returns (parsed JSON result as a dictionary, status message).
        """
        if not file_path.exists():
            return {}, f"File not found: {file_path}"

        try:
            code = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return {}, f"Error reading file: {e}"

        max_length = self.max_tokens * 4
        if len(code) > max_length:
            code = code[:max_length] + "\n... (truncated)"
            logger.info(f"File {file_path} truncated for analysis.")

        prompt = f"{self.prompts.get(analysis_type, self.prompts['security'])}\n\nCode:\n{code}"
        response = await self._api_request(prompt)
        if response is None:
            return {}, "Analysis failed: No response from API"

        try:
            result = json.loads(response)
            return result, "Analysis completed successfully"
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON response from GPT4All")
            return {}, "Analysis failed: Invalid JSON response"

    async def analyze_directory(
        self,
        directory: Path = Path("C:/Users/grabowmar/Desktop/ThesisAppsSvelte"),
        file_patterns: Optional[List[str]] = None,
        analysis_type: str = "security"
    ) -> Tuple[List[AnalysisIssue], Dict]:
        """
        Recursively analyzes all files within the directory (and subfolders) that
        match any of the provided file patterns.

        Returns:
          - A list of AnalysisIssue objects.
          - A summary dictionary with statistics.
        """
        file_patterns = file_patterns if file_patterns is not None else ["*.py", "*.js", "*.ts", "*.svelte"]
        all_issues: List[AnalysisIssue] = []
        summary = {
            "total_files": 0,
            "processed_files": 0,
            "error_files": 0,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
        }

        # Traverse all subdirectories using os.walk.
        files_to_analyze = []
        for root, _, files in os.walk(directory):
            for file_name in files:
                for pattern in file_patterns:
                    if Path(file_name).match(pattern):
                        files_to_analyze.append(Path(root) / file_name)
                        break

        summary["total_files"] = len(files_to_analyze)
        if not files_to_analyze:
            raise ValueError(f"No files found in directory {directory}")

        # Analyze each file sequentially.
        for file_path in files_to_analyze:
            result, status = await self.analyze_file(file_path, analysis_type)
            summary["processed_files"] += 1

            try:
                rel_path = file_path.relative_to(directory)
            except ValueError:
                rel_path = file_path

            # Remove "z_interface_app" from the relative path if present.
            if rel_path.parts and rel_path.parts[0].lower() == "z_interface_app":
                rel_path = Path(*rel_path.parts[1:])

            if "issues" in result and isinstance(result["issues"], list):
                for issue in result["issues"]:
                    issue_obj = AnalysisIssue(
                        filename=str(rel_path),
                        line_number=issue.get("line_number", 0),
                        issue_text=issue.get("issue_text", "No description provided"),
                        severity=issue.get("severity", "MEDIUM").upper(),
                        confidence=issue.get("confidence", "MEDIUM"),
                        issue_type=issue.get("issue_type", "unknown"),
                        line_range=issue.get("line_range", [issue.get("line_number", 0)]),
                        code=issue.get("code", ""),
                        suggested_fix=issue.get("suggested_fix"),
                        explanation=issue.get("explanation")
                    )
                    all_issues.append(issue_obj)
                    sev = issue_obj.severity.upper()
                    summary["severity_counts"][sev] = summary["severity_counts"].get(sev, 0) + 1
            else:
                logger.warning(f"No issues found in {file_path}: {status}")

        summary["end_time"] = datetime.now().isoformat()
        return all_issues, summary


def get_analysis_summary(issues: List[AnalysisIssue]) -> Dict:
    """
    Generates a summary dictionary based on a list of AnalysisIssue objects.
    """
    summary = {
        "total_issues": len(issues),
        "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
        "files_affected": 0,
        "issue_types": {},
        "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    affected_files = set()
    for issue in issues:
        affected_files.add(issue.filename)
        sev = issue.severity.upper()
        summary["severity_counts"][sev] = summary["severity_counts"].get(sev, 0) + 1
        itype = issue.issue_type
        summary["issue_types"][itype] = summary["issue_types"].get(itype, 0) + 1

    summary["files_affected"] = len(affected_files)
    return summary
