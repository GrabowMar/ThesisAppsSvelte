"""
GPT4All Requirements Analysis Module with real API integration

This module connects to a local GPT4All API server to analyze code against requirements.
Uses the GPT4All API which is compatible with OpenAI's API format.
"""

import asyncio
import json
import logging
import os
import aiohttp
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Union, Set

# Set up logging
try:
    from logging_service import create_logger_for_component
    logger = create_logger_for_component('gpt4all')
except ImportError:
    logger = logging.getLogger('gpt4all')
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

# Server status cache to prevent excessive checks
_server_status_cache = {
    "last_check": 0,
    "status": False
}

@dataclass
class RequirementResult:
    """Result of a requirement check."""
    met: bool = False
    confidence: str = "LOW"
    explanation: str = ""
    error: Optional[str] = None

@dataclass
class RequirementCheck:
    """Complete check for a requirement."""
    requirement: str
    frontend: RequirementResult = field(default_factory=RequirementResult)
    backend: RequirementResult = field(default_factory=RequirementResult)
    
    @property
    def overall(self) -> bool:
        """Whether the requirement is met overall."""
        return self.frontend.met or self.backend.met
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "requirement": self.requirement,
            "frontend": asdict(self.frontend),
            "backend": asdict(self.backend),
            "overall": self.overall
        }

class GPT4AllClient:
    """Client for connecting to a local GPT4All API server."""
    
    def __init__(self, api_url: str = None):
        """Initialize with API URL."""
        # Use environment variable or default to localhost
        self.api_url = api_url or os.getenv("GPT4ALL_API_URL", "http://localhost:4891/v1")
        # Use environment variable or default to model name
        self.model = os.getenv("GPT4ALL_MODEL", "mistral-7b-openorca")
        # Default timeout in seconds
        self.timeout = int(os.getenv("GPT4ALL_TIMEOUT", "30"))
        logger.info(f"Initialized GPT4All client with API URL: {self.api_url}, model: {self.model}")
    
    async def check_server(self) -> bool:
        """Check if the GPT4All server is available."""
        current_time = time.time()
        
        # Use cached result if recent (within 30 seconds)
        if current_time - _server_status_cache["last_check"] < 30:
            return _server_status_cache["status"]
        
        try:
            logger.debug(f"Checking GPT4All server at {self.api_url}")
            timeout = aiohttp.ClientTimeout(total=5)  # Short timeout for status check
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.api_url}/models") as response:
                    if response.status == 200:
                        logger.info("GPT4All server is available")
                        _server_status_cache["status"] = True
                        _server_status_cache["last_check"] = current_time
                        return True
                    else:
                        logger.warning(f"GPT4All server returned {response.status}")
                        _server_status_cache["status"] = False
                        _server_status_cache["last_check"] = current_time
                        return False
        except Exception as e:
            logger.error(f"Error checking GPT4All server: {e}")
            _server_status_cache["status"] = False
            _server_status_cache["last_check"] = current_time
            return False
    
    async def generate_completion(self, prompt: str, system_prompt: str = None) -> Optional[str]:
        """Send a completion request to the GPT4All API."""
        if not await self.check_server():
            logger.error("Cannot send request - GPT4All server is not available")
            return None
        
        logger.debug(f"Sending prompt to GPT4All API (length: {len(prompt)})")
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                messages = []
                
                # Add system prompt if provided
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                
                # Add user prompt
                messages.append({"role": "user", "content": prompt})
                
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.2,  # Lower temperature for more deterministic responses
                    "max_tokens": 1024,  # Adjust based on your needs
                    "top_p": 0.95,
                    "stream": False
                }
                
                async with session.post(
                    f"{self.api_url}/chat/completions", 
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        logger.debug(f"Received response (length: {len(content)})")
                        return content
                    else:
                        error_text = await response.text()
                        logger.error(f"GPT4All API request failed with status {response.status}: {error_text}")
                        return None
        except Exception as e:
            logger.exception(f"Error sending request to GPT4All API: {e}")
            return None

class GPT4AllAnalyzer:
    """Analyzes code against requirements using GPT4All API."""
    
    def __init__(self, base_path: Union[Path, str] = None):
        """Initialize analyzer with optional base path."""
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.client = GPT4AllClient()
        
        # Template for requirement check prompts
        self.requirement_system_prompt = """
You are an expert code reviewer focused on assessing whether code meets specific requirements.
Analyze the code provided and determine if it satisfies the given requirement.
Provide a detailed but concise explanation for your assessment.
Your response should be in JSON format only, with the following structure:
{
  "met": true/false,
  "confidence": "HIGH"/"MEDIUM"/"LOW",
  "explanation": "brief explanation of why the requirement is or is not met"
}
"""
        logger.info(f"Initialized GPT4All analyzer with base path: {self.base_path}")
    
    async def check_server_availability(self) -> bool:
        """Check if the GPT4All server is available."""
        return await self.client.check_server()
    
    def get_requirements_for_app(self, app_num: int) -> Tuple[List[str], str]:
        """Get requirements for a specific app based on app number."""
        logger.info(f"Getting requirements for app {app_num}")
        
        # Load requirements data from JSON or use defaults
        requirements_data = self.load_requirements_data()
        
        # Get general requirements
        general_requirements = requirements_data.get("generalRequirements", [])
        
        # Get template-specific requirements
        template_specs = requirements_data.get("templateSpecificRequirements", [])
        
        # Default values
        template_requirements = []
        template_name = "Unknown"
        
        if template_specs:
            # Map app number to template (cycle through available templates)
            template_index = (app_num - 1) % len(template_specs)
            template_data = template_specs[template_index]
            
            template_name = template_data.get("template", "Unknown")
            template_requirements = template_data.get("requirements", [])
            
            logger.info(f"Mapped app{app_num} to template: {template_name}")
        
        # Combine general and template-specific requirements
        all_requirements = general_requirements + template_requirements
        return all_requirements, template_name
    
    def load_requirements_data(self) -> Dict[str, Any]:
        """Load requirements data from JSON or use defaults."""
        try:
            # Try to find requirements.json in common locations
            possible_paths = [
                self.base_path / "requirements.json",
                self.base_path / "data" / "requirements.json",
                self.base_path / "static" / "requirements.json",
                self.base_path / "config" / "requirements.json",
                Path(__file__).parent / "requirements.json",
                Path(__file__).parent.parent / "requirements.json"
            ]
            
            for path in possible_paths:
                if path.exists():
                    logger.info(f"Loading requirements from {path}")
                    with open(path, 'r', encoding='utf-8') as f:
                        return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load requirements: {e}")
        
        # Default requirements data
        logger.warning("Using default requirements data")
        return {
            "generalRequirements": [
                "Multipage Routing: Extendable routing on both backend and frontend for additional pages/views",
                "Simple and modern UI",
                "Keep all changes within app.py, App.jsx and App.css files",
                "Feature complete production ready app with comments, fail states, etc.",
                "App.jsx must include mounting logic with ReactDOM from react-dom/client"
            ],
            "templateSpecificRequirements": [
                {
                    "template": "Login/Register Application",
                    "requirements": [
                        "User registration functionality",
                        "Login functionality",
                        "Password security",
                        "Session management",
                        "Error handling"
                    ]
                },
                {
                    "template": "Chat Application",
                    "requirements": [
                        "Real-time message exchange",
                        "User identification",
                        "Message history",
                        "Online status indicators",
                        "Multiple chat rooms"
                    ]
                },
                {
                    "template": "Feedback Form Application",
                    "requirements": [
                        "Multi-field feedback form",
                        "Form validation",
                        "Submission handling",
                        "Response storage",
                        "Success notifications"
                    ]
                },
                {
                    "template": "Blog Application",
                    "requirements": [
                        "User authentication (login/register)",
                        "Blog post creation and editing",
                        "Comment system",
                        "Post categorization",
                        "Responsive design"
                    ]
                },
                {
                    "template": "E-Commerce Cart Application",
                    "requirements": [
                        "Product listing page",
                        "Shopping cart management",
                        "Checkout process",
                        "Order summary",
                        "Inventory tracking"
                    ]
                }
            ]
        }
    
    def collect_code_files(self, directory: Path) -> Tuple[List[Path], List[Path]]:
        """Collect frontend and backend files from a directory."""
        frontend_files = []
        backend_files = []
        
        # Skip directories and patterns
        skip_dirs: Set[str] = {
            'node_modules', '.git', '__pycache__', 'venv', 'env',
            'dist', 'build', '.next', 'static'
        }
        
        if not directory.exists():
            logger.error(f"Directory does not exist: {directory}")
            return [], []
        
        # Find files with common extensions
        for root, dirs, files in os.walk(directory):
            # Skip directories in-place to avoid traversing them
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            root_path = Path(root)
            
            for file_name in files:
                file_path = root_path / file_name
                
                # Skip large files (>200KB)
                try:
                    if file_path.stat().st_size > 200 * 1024:
                        continue
                except (PermissionError, OSError):
                    continue
                    
                # Categorize by file extension
                if file_name.endswith(('.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.vue', '.svelte')):
                    frontend_files.append(file_path)
                    if len(frontend_files) >= 5:  # Limit to 5 files
                        break
                        
                elif file_name.endswith('.py'):
                    backend_files.append(file_path)
                    if len(backend_files) >= 5:  # Limit to 5 files
                        break
            
            # Stop if we have enough files
            if len(frontend_files) >= 5 and len(backend_files) >= 5:
                break
                
        logger.info(f"Found {len(frontend_files)} frontend files and {len(backend_files)} backend files")
        return frontend_files, backend_files
    
    def read_code_from_files(self, files: List[Path], max_chars: int = 8000) -> str:
        """Read and combine code from multiple files with length limit."""
        combined_code = ""
        total_chars = 0
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    code = f.read()
                    
                    # Add file header and code
                    file_snippet = f"\n\n--- File: {file_path.name} ---\n{code}"
                    
                    # Check if adding this would exceed the limit
                    if total_chars + len(file_snippet) > max_chars:
                        # Add partial file if possible
                        remaining = max_chars - total_chars
                        if remaining > 200:  # Only add if we can include a meaningful chunk
                            partial = file_snippet[:remaining] + "\n...[truncated]"
                            combined_code += partial
                        break
                    
                    combined_code += file_snippet
                    total_chars += len(file_snippet)
                    
                    if total_chars >= max_chars:
                        break
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
                
        return combined_code
    
    def extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract and parse JSON from API response."""
        if not response:
            return {"met": False, "confidence": "LOW", "explanation": "No response from API"}
            
        # Try to parse the response as JSON directly
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
            
        # Try to extract JSON with regex patterns
        import re
        json_patterns = [
            r'```json\s*([\s\S]*?)\s*```',  # JSON in code block with json tag
            r'```\s*([\s\S]*?)\s*```',      # JSON in generic code block
            r'({[\s\S]*?})'                 # JSON with outer braces
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, response)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    continue
        
        # Fallback: extract information from text
        is_met = "meets the requirement" in response.lower() or "requirement is met" in response.lower()
        
        # Extract some text for explanation
        explanation = response[:200].replace('\n', ' ')
        
        return {
            "met": is_met,
            "confidence": "LOW",
            "explanation": explanation
        }
    
    async def check_requirement(self, requirement: str, code: str, is_frontend: bool) -> RequirementResult:
        """Check a single requirement against code."""
        if not code:
            return RequirementResult(
                met=False,
                confidence="HIGH",
                explanation="No code to analyze",
                error="No code files found"
            )
            
        code_type = "FRONTEND" if is_frontend else "BACKEND"
        
        # Create prompt for requirement check
        prompt = f"""
Requirement: {requirement}

Code type: {code_type}

Analyze if this code meets the requirement. Respond in JSON format only.

Code:
```
{code}
```
"""
        
        # Send prompt to GPT4All
        response = await self.client.generate_completion(prompt, self.requirement_system_prompt)
        
        if not response:
            return RequirementResult(
                met=False,
                confidence="LOW",
                explanation="Could not analyze requirement",
                error="GPT4All API request failed"
            )
            
        # Parse the response
        result = self.extract_json_from_response(response)
        
        return RequirementResult(
            met=result.get("met", False),
            confidence=result.get("confidence", "LOW").upper(),
            explanation=result.get("explanation", "No explanation provided")
        )
    
    async def check_requirements(self, model: str, app_num: int, requirements: List[str]) -> List[RequirementCheck]:
        """Check multiple requirements against app code."""
        # Check server availability first
        if not await self.check_server_availability():
            logger.error("GPT4All server is not available")
            return [
                RequirementCheck(
                    requirement=req,
                    frontend=RequirementResult(error="GPT4All server is not available"),
                    backend=RequirementResult(error="GPT4All server is not available")
                )
                for req in requirements
            ]
        
        # Find app directory
        directory = self.find_app_directory(model, app_num)
        
        # Collect code files
        frontend_files, backend_files = self.collect_code_files(directory)
        
        # Read code
        frontend_code = self.read_code_from_files(frontend_files)
        backend_code = self.read_code_from_files(backend_files)
        
        # Check each requirement
        results = []
        for req in requirements:
            # Create a check for this requirement
            check = RequirementCheck(requirement=req)
            
            # Check frontend code
            if frontend_code:
                check.frontend = await self.check_requirement(req, frontend_code, True)
            else:
                check.frontend = RequirementResult(
                    met=False,
                    confidence="HIGH",
                    explanation="No frontend code to analyze"
                )
                
            # Check backend code
            if backend_code:
                check.backend = await self.check_requirement(req, backend_code, False)
            else:
                check.backend = RequirementResult(
                    met=False,
                    confidence="HIGH",
                    explanation="No backend code to analyze"
                )
                
            results.append(check)
            
        return results
    
    def find_app_directory(self, model: str, app_num: int) -> Path:
        """Find the directory for a specific app with fallbacks."""
        # Try common directory patterns
        patterns = [
            self.base_path / f"{model}/app{app_num}",
            self.base_path / f"{model.lower()}/app{app_num}",
            self.base_path / f"{model}/App{app_num}",
            self.base_path / f"models/{model}/app{app_num}",
            self.base_path / f"z_interface_app/{model}/app{app_num}",
            self.base_path / f"z_interface_app/{model.lower()}/app{app_num}"
        ]
        
        # Try each pattern
        for pattern in patterns:
            if pattern.exists() and pattern.is_dir():
                logger.info(f"Found app directory: {pattern}")
                return pattern
        
        # If no directory is found, return the default pattern
        logger.warning(f"App directory not found for {model}/app{app_num}, using default")
        return self.base_path / f"{model}/app{app_num}"
    
    async def analyze_directory(self, directory: Path, file_patterns: List[str], analysis_type: str) -> Tuple[List[Any], Dict[str, Any]]:
        """Analyze a directory for security, performance, or code quality issues."""
        logger.info(f"Analyzing directory {directory} with patterns {file_patterns}, type: {analysis_type}")
        
        # Check server availability
        if not await self.check_server_availability():
            logger.error("GPT4All server is not available")
            return [], {"error": "GPT4All server is not available"}
        
        # Collect files matching patterns
        files = []
        for pattern in file_patterns:
            try:
                files.extend(list(directory.glob(f"**/{pattern}")))
            except Exception as e:
                logger.error(f"Error glob matching pattern {pattern}: {e}")
        
        files = files[:15]  # Limit number of files to analyze
        
        # Skip directories like node_modules
        files = [f for f in files if not any(sd in str(f) for sd in ['node_modules', '.git', '__pycache__', 'venv'])]
        
        # Read content from files
        file_contents = {}
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    if len(content) > 10000:  # Skip very large files
                        content = content[:10000] + "\n...[truncated]"
                    file_contents[str(file_path.relative_to(directory))] = content
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
        
        # Prepare system prompt based on analysis type
        if analysis_type == "security":
            system_prompt = """
You are a security expert analyzing code for vulnerabilities. Identify security issues such as:
- SQL injection
- XSS vulnerabilities
- Insecure authentication
- Hardcoded credentials
- Command injection
- Insecure file operations
- CSRF vulnerabilities

For each issue, provide:
1. The file and line number
2. The vulnerability type
3. The severity (HIGH, MEDIUM, LOW)
4. A brief description
5. A suggestion for remediation

Structure your response as a JSON array:
[
  {
    "file": "path/to/file.js",
    "line": 42,
    "vulnerability": "SQL Injection",
    "severity": "HIGH",
    "description": "Raw user input is used in SQL query without sanitization",
    "remediation": "Use parameterized queries or an ORM"
  }
]
"""
        elif analysis_type == "performance":
            system_prompt = """
You are a performance optimization expert. Analyze the code for performance issues such as:
- Inefficient algorithms
- Redundant operations
- Memory leaks
- Excessive DOM manipulations
- Unoptimized database queries
- Blocking operations on the main thread
- Inefficient resource loading

Structure your response as a JSON array:
[
  {
    "file": "path/to/file.js",
    "line": 42,
    "issue": "Inefficient loop",
    "severity": "MEDIUM",
    "description": "O(n²) operation that could be optimized",
    "suggestion": "Use Map data structure instead of nested loops"
  }
]
"""
        else:  # Default to code quality
            system_prompt = """
You are a code quality expert. Analyze the code for issues such as:
- Maintainability problems
- Code duplication
- Poor readability
- Inconsistent naming conventions
- Missing error handling
- Inadequate comments/documentation
- Function or class complexity issues

Structure your response as a JSON array:
[
  {
    "file": "path/to/file.js",
    "line": 42,
    "issue": "Complex function",
    "severity": "MEDIUM",
    "description": "Function has too many responsibilities",
    "suggestion": "Break down into smaller functions"
  }
]
"""
        
        # Create the prompt
        files_text = "\n\n".join([f"File: {file_path}\n```\n{content}\n```" for file_path, content in file_contents.items()])
        
        prompt = f"""
Analyze the following code files for {analysis_type} issues:

{files_text}

Provide your analysis in the required JSON format only.
"""
        
        # Send prompt to GPT4All
        logger.info(f"Sending {analysis_type} analysis prompt to GPT4All")
        response = await self.client.generate_completion(prompt, system_prompt)
        
        if not response:
            logger.error("Failed to get response from GPT4All API")
            return [], {"error": "No response from API"}
        
        # Parse the response to get issues
        issues = []
        try:
            # Try to parse as JSON
            import re
            # Look for JSON arrays in the response
            match = re.search(r'\[\s*\{.*\}\s*\]', response, re.DOTALL)
            if match:
                issues_text = match.group(0)
                issues = json.loads(issues_text)
            else:
                # Fallback to extracting from code blocks
                match = re.search(r'```(?:json)?\s*(.*?)```', response, re.DOTALL)
                if match:
                    issues_text = match.group(1)
                    issues = json.loads(issues_text)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            # Create a simple issue with the error
            issues = [{
                "file": "analysis.error",
                "line": 0,
                "issue": "JSON Parsing Error",
                "severity": "LOW",
                "description": f"Could not parse response from GPT4All: {str(e)}",
                "response_excerpt": response[:200] + "..." if len(response) > 200 else response
            }]
        
        # Create summary
        severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for issue in issues:
            severity = issue.get("severity", "LOW").upper()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        summary = {
            "total_issues": len(issues),
            "severity_counts": severity_counts,
            "analysis_type": analysis_type,
            "files_analyzed": len(file_contents)
        }
        
        logger.info(f"Analysis complete. Found {len(issues)} issues")
        return issues, summary