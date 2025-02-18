"""
gpt4all_analysis.py - GPT4All-powered Local Code Analysis Module

Analyzes code using a local GPT4All API server with the Phi-3 Mini Instruct model for:
- Security vulnerabilities 
- Code quality issues
- Feature recommendations
- Best practices
"""

import json
import logging
import os
import asyncio
import aiohttp
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class AIAnalysisIssue:
    """Represents an issue found by AI analysis."""
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
    """Handles code analysis using a local GPT4All API server."""
    
    def __init__(self, base_path: Path):
        """Initialize the analyzer with the base path and API settings."""
        self.base_path = base_path
        self.api_url = os.getenv("GPT4ALL_API_URL", "http://localhost:4891/v1")
        self.model_name = "deepseek-r1-distill-qwen-7b"
        self.MAX_TOKENS = 4096
        # Analysis prompts with structured output requirements for different analysis types.
        self.analysis_prompts = {
            "security": (
                "Analyze this code for security vulnerabilities. Focus on:\n"
                "1. Input validation\n"
                "2. Authentication/authorization\n"
                "3. Data exposure\n"
                "4. Cryptographic issues\n"
                "5. Configuration security\n"
                "Return JSON: {issues: [{filename, line_number, issue_text, severity, confidence, issue_type, line_range, code, suggested_fix}]}"
            ),
            "features": (
                "Analyze this code and suggest improvements. Focus on:\n"
                "1. Performance optimizations\n"
                "2. Error handling\n"
                "3. Logging improvements\n"
                "4. Testing coverage\n"
                "5. Code organization\n"
                "Return JSON: {suggestions: [{title, description, priority, effort_level, code_example}]}"
            ),
            "quality": (
                "Review this code for quality and best practices. Focus on:\n"
                "1. Code structure\n"
                "2. Variable naming\n"
                "3. Function design\n"
                "4. Documentation\n"
                "5. Maintainability\n"
                "Return JSON: {issues: [{area, description, severity, suggestion, code_example}]}"
            )
        }

    async def _make_api_request(self, messages: List[Dict]) -> Optional[str]:
        """
        Make an API request to the local GPT4All API server with the provided messages.
        
        Returns the content of the response message if successful.
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model_name,
                    "messages": messages,
                    "max_tokens": self.MAX_TOKENS,
                }
                async with session.post(f"{self.api_url}/chat/completions", json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API request failed: {error_text}")
                    data = await response.json()
                    return data['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"GPT4All API request failed: {str(e)}")
            return None

    async def analyze_file(self, file_path: Path, analysis_type: str = "security") -> Tuple[List[Dict], str]:
        """
        Analyze a single file using GPT4All.

        Args:
            file_path: Path to the file to be analyzed.
            analysis_type: Type of analysis to run (e.g., "security").

        Returns:
            A tuple containing the parsed JSON analysis result (as a dictionary)
            and a status message.
        """
        try:
            if not file_path.exists():
                return [], f"File not found: {file_path}"

            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            # Trim code if it exceeds the maximum allowed length.
            if len(code) > self.MAX_TOKENS * 4:
                code = code[:self.MAX_TOKENS * 4] + "\n... (truncated)"

            messages = [{
                "role": "user",
                "content": f"{self.analysis_prompts[analysis_type]}\n\nCode:\n{code}"
            }]

            response_text = await self._make_api_request(messages)
            if not response_text:
                return [], "Analysis failed: No response from API"

            try:
                analysis_result = json.loads(response_text)
                return analysis_result, "Analysis completed successfully"
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON response from GPT4All")
                return [], "Analysis failed: Invalid JSON response"

        except Exception as e:
            logger.error(f"Analysis failed for {file_path}: {str(e)}")
            return [], f"Analysis failed: {str(e)}"

    async def analyze_directory(
        self, 
        directory: Path,
        file_patterns: List[str] = ["*.py", "*.js", "*.ts", "*.react"],
        analysis_type: str = "security"
    ) -> Tuple[List[AIAnalysisIssue], Dict[str, str]]:
        """
        Analyze all files in a directory matching the provided patterns using GPT4All.

        Expected directory structure:
            <base_path>/<model>/app<app_num>/<...>

        Returns:
            A tuple containing:
              - A list of AIAnalysisIssue objects.
              - A dictionary summarizing the analysis (e.g., counts, timings).

        Raises:
            ValueError: If no matching files are found.
        """
        try:
            all_issues = []
            analysis_summary = {
                "total_files": 0,
                "processed_files": 0,
                "error_files": 0,
                "start_time": datetime.now().isoformat(),
                "end_time": None,
                "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
            }

            # Gather files matching the given patterns.
            files_to_analyze = []
            for pattern in file_patterns:
                files_to_analyze.extend(directory.rglob(pattern))
            analysis_summary["total_files"] = len(files_to_analyze)

            # Process files sequentially to avoid overwhelming the local API.
            for file_path in files_to_analyze:
                results, _ = await self.analyze_file(file_path, analysis_type)
                analysis_summary["processed_files"] += 1

                if "issues" in results:
                    file_issues = [
                        AIAnalysisIssue(
                            filename=str(file_path.relative_to(directory)),
                            line_number=issue.get("line_number", 0),
                            issue_text=issue.get("issue_text", "No description"),
                            severity=issue.get("severity", "MEDIUM"),
                            confidence=issue.get("confidence", "MEDIUM"),
                            issue_type=issue.get("issue_type", "unknown"),
                            line_range=[issue.get("line_number", 0)],
                            code=issue.get("code", ""),
                            suggested_fix=issue.get("suggested_fix"),
                            explanation=issue.get("explanation")
                        )
                        for issue in results["issues"]
                    ]
                    all_issues.extend(file_issues)
                    for issue in file_issues:
                        analysis_summary["severity_counts"][issue.severity] += 1

            analysis_summary["end_time"] = datetime.now().isoformat()
            return all_issues, analysis_summary

        except Exception as e:
            logger.error(f"Directory analysis failed: {str(e)}")
            return [], {"error": str(e)}


def get_analysis_summary(issues: List[AIAnalysisIssue]) -> dict:
    """
    Generate a detailed summary of AI analysis issues.

    Returns a dictionary with total issues, severity counts, number of affected files,
    issue types breakdown, and the scan time.
    """
    summary = {
        "total_issues": len(issues),
        "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
        "files_affected": len({issue.filename for issue in issues}),
        "issue_types": {},
        "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    for issue in issues:
        summary["severity_counts"][issue.severity] += 1
        summary["issue_types"][issue.issue_type] = summary["issue_types"].get(issue.issue_type, 0) + 1

    return summary
