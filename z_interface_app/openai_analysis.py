"""
openai_analysis.py - OpenAI-powered Code Analysis Module

Analyzes code using OpenAI APIs for:
- Security vulnerabilities 
- Code quality issues
- Feature recommendations
- Best practices
"""

import json
import logging
import os
import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import aiohttp
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class AIAnalysisIssue:
    """Represents an issue found by AI analysis"""
    filename: str
    line_number: int
    issue_text: str
    severity: str
    confidence: str
    issue_type: str
    line_range: List[int]
    code: str
    tool: str = "OpenAI"
    suggested_fix: Optional[str] = None
    explanation: Optional[str] = None

class OpenAIAnalyzer:
    """Handles code analysis using OpenAI APIs"""
    
    def __init__(self, base_path: Path):
        """Initialize the analyzer with base path and API key"""
        self.base_path = base_path
        load_dotenv()
        
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.MAX_TOKENS = 4000
        self.analysis_prompts = {
            "security": """Analyze this code for security vulnerabilities. Focus on:
                1. Input validation
                2. Authentication/authorization
                3. Data exposure
                4. Cryptographic issues
                5. Configuration security
                Return findings in JSON format with fields:
                {issues: [{filename, line_number, issue_text, severity, confidence, issue_type, line_range, code, suggested_fix}]}
                """,
            "features": """Analyze this code and suggest potential feature improvements. Consider:
                1. Performance optimizations
                2. Error handling
                3. Logging improvements
                4. Testing coverage
                5. Code organization
                Return suggestions in JSON format with fields:
                {suggestions: [{title, description, priority, effort_level, code_example}]}
                """,
            "quality": """Review this code for quality and best practices. Focus on:
                1. Code structure
                2. Variable naming
                3. Function design
                4. Documentation
                5. Maintainability
                Return findings in JSON format with fields:
                {issues: [{area, description, severity, suggestion, code_example}]}
                """
        }

    async def analyze_file(self, file_path: Path, analysis_type: str = "security") -> Tuple[List[Dict], str]:
        """Analyze a single file using OpenAI"""
        try:
            if not file_path.exists():
                return [], f"File not found: {file_path}"

            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            # Trim code if too long
            if len(code) > self.MAX_TOKENS * 4:  # Conservative limit
                code = code[:self.MAX_TOKENS * 4] + "\n... (truncated)"

            messages = [
                {"role": "system", "content": "You are an expert code analyzer focusing on security and best practices."},
                {"role": "user", "content": f"{self.analysis_prompts[analysis_type]}\n\nCode to analyze:\n{code}"}
            ]

            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.3,
                max_tokens=self.MAX_TOKENS,
                response_format={"type": "json_object"}
            )

            analysis_result = json.loads(response.choices[0].message.content)
            return analysis_result, "Analysis completed successfully"

        except Exception as e:
            logger.error(f"OpenAI analysis failed for {file_path}: {str(e)}")
            return [], f"Analysis failed: {str(e)}"

    async def analyze_directory(
        self, 
        directory: Path,
        file_patterns: List[str] = ["*.py", "*.js", "*.ts", "*.svelte"],
        analysis_type: str = "security"
    ) -> Tuple[List[AIAnalysisIssue], Dict[str, str]]:
        """Analyze all matching files in a directory"""
        try:
            all_issues = []
            analysis_summary = {
                "total_files": 0,
                "processed_files": 0,
                "error_files": 0,
                "start_time": datetime.now().isoformat(),
                "end_time": None
            }

            files_to_analyze = []
            for pattern in file_patterns:
                files_to_analyze.extend(directory.rglob(pattern))

            analysis_summary["total_files"] = len(files_to_analyze)

            async def analyze_file_wrapper(file_path: Path) -> Optional[List[AIAnalysisIssue]]:
                try:
                    results, _ = await self.analyze_file(file_path, analysis_type)
                    analysis_summary["processed_files"] += 1
                    
                    if "issues" in results:
                        return [
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
                    return []
                except Exception as e:
                    logger.error(f"Error analyzing {file_path}: {e}")
                    analysis_summary["error_files"] += 1
                    return []

            # Analyze files concurrently with rate limiting
            semaphore = asyncio.Semaphore(3)  # Limit concurrent API calls
            async def analyze_with_semaphore(file_path: Path):
                async with semaphore:
                    return await analyze_file_wrapper(file_path)

            tasks = [analyze_with_semaphore(f) for f in files_to_analyze]
            results = await asyncio.gather(*tasks)
            
            for file_issues in results:
                if file_issues:
                    all_issues.extend(file_issues)

            analysis_summary["end_time"] = datetime.now().isoformat()
            return all_issues, analysis_summary

        except Exception as e:
            logger.error(f"Directory analysis failed: {str(e)}")
            return [], {"error": str(e)}

    async def analyze_app(
        self,
        model: str,
        app_num: int,
        analysis_type: str = "security"
    ) -> Tuple[List[AIAnalysisIssue], Dict[str, str]]:
        """Analyze a specific app's code"""
        app_path = self.base_path / f"{model}/app{app_num}"
        if not app_path.exists():
            return [], {"error": f"App directory not found: {app_path}"}

        return await self.analyze_directory(app_path, analysis_type=analysis_type)

    def get_analysis_summary(self, issues: List[AIAnalysisIssue]) -> dict:
        """Generate a detailed summary of AI analysis issues"""
        if not issues:
            return {
                "total_issues": 0,
                "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
                "confidence_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
                "files_affected": 0,
                "issue_types": {},
                "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        summary = {
            "total_issues": len(issues),
            "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "confidence_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "files_affected": len(set(issue.filename for issue in issues)),
            "issue_types": {},
            "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        for issue in issues:
            summary["severity_counts"][issue.severity] += 1
            summary["confidence_counts"][issue.confidence] += 1
            summary["issue_types"][issue.issue_type] = summary["issue_types"].get(issue.issue_type, 0) + 1

        return summary

def integrate_with_security_analyzer(security_analyzer):
    """Integrate OpenAI analyzer with the main security analyzer"""
    
    # Add OpenAI analysis to available tools
    security_analyzer.all_tools.append("openai")
    
    # Create analyzer instance
    openai_analyzer = OpenAIAnalyzer(security_analyzer.base_path)
    
    # Add OpenAI analysis method
    async def run_openai_analysis(app_path: Path) -> Tuple[List[AIAnalysisIssue], str]:
        try:
            issues, summary = await openai_analyzer.analyze_directory(app_path)
            
            if not issues:
                return [], "No issues found"
                
            return issues, json.dumps(summary, indent=2)
            
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            return [], f"Error: {str(e)}"
    
    # Add the analysis method to the tool map
    security_analyzer.tool_map["openai"] = run_openai_analysis