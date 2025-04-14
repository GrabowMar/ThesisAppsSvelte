"""
GPT4All Requirements Analysis Module

This module connects to a local GPT4All API server to analyze code against requirements.
It uses the GPT4All API (compatible with OpenAI's API format) to determine if applications
meet specified requirements.
"""

import json
import os
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Union, Set
import aiohttp
import requests
import logging

# Try to import from logging_service, but use basic logging if it fails
try:
    from logging_service import create_logger_for_component
    logger = create_logger_for_component('gpt4all')
except (ImportError, Exception) as e:
    # Set up basic logging as fallback
    logger = logging.getLogger('gpt4all')
    handler = logging.StreamHandler()
    # Use a simple formatter that doesn't require request_id
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.warning(f"Using fallback logging due to error: {e}")

@dataclass
class RequirementResult:
    """Result of a requirement check."""
    met: bool = False
    confidence: str = "LOW"
    explanation: str = ""
    error: Optional[str] = None
    frontend_analysis: Optional[Dict] = None
    backend_analysis: Optional[Dict] = None

@dataclass
class RequirementCheck:
    """Complete check for a requirement."""
    requirement: str
    result: RequirementResult = field(default_factory=RequirementResult)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "requirement": self.requirement,
            "result": asdict(self.result)
        }

class GPT4AllClient:
    """Client for connecting to a local GPT4All API server."""
    
    def __init__(self, api_url: str = None, preferred_model: str = None):
        """
        Initialize the GPT4All client.
        
        Args:
            api_url: Base URL for the GPT4All API server
            preferred_model: Preferred model to use (if available)
        """
        self.api_url = api_url or os.getenv("GPT4ALL_API_URL", "http://localhost:4891/v1")
        self.preferred_model = preferred_model
        self.available_models = []
        self.timeout = int(os.getenv("GPT4ALL_TIMEOUT", "30"))
        self.last_check_time = 0
        self.is_available = False
        logger.info(f"GPT4All client initialized with URL: {self.api_url}")
    
    def check_server(self) -> bool:
        """
        Check if the GPT4All server is available and fetch available models.
        
        Returns:
            bool: True if server is available, False otherwise
        """
        # Limit checks to once every 15 seconds
        current_time = time.time()
        if current_time - self.last_check_time < 15 and self.is_available:
            return self.is_available
            
        self.last_check_time = current_time
        
        try:
            logger.debug(f"Checking GPT4All server at: {self.api_url}/models")
            response = requests.get(f"{self.api_url}/models", timeout=5)
            
            if response.status_code == 200:
                models_data = response.json()
                self.available_models = [model.get('id') for model in models_data.get('data', [])]
                logger.info(f"Available GPT4All models: {self.available_models}")
                self.is_available = True
                return True
            else:
                logger.error(f"GPT4All server returned status code: {response.status_code}")
                self.is_available = False
                return False
        except Exception as e:
            logger.error(f"Error checking GPT4All server: {str(e)}")
            self.is_available = False
            return False
    
    def get_best_model(self) -> str:
        """
        Get the best available model based on preferences or defaults.
        
        Returns:
            str: Name of the best available model to use
        """
        if not self.available_models:
            if not self.check_server():
                logger.warning("Cannot determine best model - server unavailable")
                return self.preferred_model or "Llama 3 8B Instruct"  # Fallback default
        
        # If preferred model is available, use it
        if self.preferred_model and self.preferred_model in self.available_models:
            return self.preferred_model
            
        # Known good models in order of preference
        preferred_models = [
            "Llama 3 8B Instruct",
            "DeepSeek-R1-Distill-Qwen-7B",
            "Nous Hermes 2 Mistral DPO",
            "GPT4All Falcon"
        ]
        
        # Find first available preferred model
        for model in preferred_models:
            if model in self.available_models:
                return model
                
        # If none of the preferred models are available, use the first available model
        if self.available_models:
            return self.available_models[0]
            
        # Fallback to default
        return "Llama 3 8B Instruct"
    
    def analyze_code(self, requirement: str, code: str, is_frontend: bool = True, model: str = None) -> Dict[str, Any]:
        """
        Analyze code to determine if it meets a requirement.
        
        Args:
            requirement: The requirement to check
            code: The code to analyze
            is_frontend: Whether the code is frontend (True) or backend (False)
            model: Model to use for analysis, otherwise use best available
            
        Returns:
            Dict containing the analysis result
        """
        if not self.check_server():
            logger.error("GPT4All server is not available")
            return {
                "met": False,
                "confidence": "LOW",
                "explanation": "GPT4All server is not available"
            }
            
        # Select model
        model_to_use = model or self.get_best_model()
        
        # Create system prompt
        system_prompt = """
You are an expert code reviewer focused on determining if code meets specific requirements.
Analyze the provided code and determine if it satisfies the given requirement.
Focus on concrete evidence in the code, not assumptions.
Respond with JSON containing only the following fields:
{
  "met": true/false,
  "confidence": "HIGH"/"MEDIUM"/"LOW",
  "explanation": "Brief explanation with specific code evidence"
}
"""
        
        # Create user prompt with code to analyze
        code_type = "Frontend" if is_frontend else "Backend"
        user_prompt = f"""
Requirement: {requirement}

Code Type: {code_type}

Analyze if the following code meets the requirement:

```
{code}
```

Respond with JSON containing:
- "met": Whether the requirement is met (true/false)
- "confidence": Your confidence level (HIGH/MEDIUM/LOW)
- "explanation": Specific evidence from the code
"""
        
        try:
            # Prepare the request payload
            payload = {
                "model": model_to_use,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 1024
            }
            
            # Send request to GPT4All API
            logger.info(f"Sending analysis request to GPT4All API using model: {model_to_use}")
            response = requests.post(
                f"{self.api_url}/chat/completions",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # Parse the response content as JSON
                try:
                    result = json.loads(content)
                    logger.info(f"Analysis result: requirement met = {result.get('met', False)}")
                    return result
                except json.JSONDecodeError:
                    # If response is not valid JSON, try to extract JSON from the content
                    return self._extract_json_from_text(content)
            else:
                logger.error(f"GPT4All API request failed: {response.status_code}")
                logger.error(f"Response: {response.text[:500]}")
                return {
                    "met": False,
                    "confidence": "LOW",
                    "explanation": f"API request failed: {response.status_code}"
                }
                
        except Exception as e:
            logger.exception(f"Error analyzing code: {str(e)}")
            return {
                "met": False,
                "confidence": "LOW",
                "explanation": f"Error analyzing code: {str(e)}"
            }
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON data from text that might contain markdown or other formatting.
        
        Args:
            text: Text that might contain JSON
            
        Returns:
            Dict with extracted data or default values
        """
        # Try to find JSON in code blocks
        import re
        json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', text, re.DOTALL)
        
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
                
        # Try to find JSON with outer braces
        json_match = re.search(r'({.*?})', text, re.DOTALL)
        
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # If no JSON found, infer results from text
        result = {
            "met": "meets the requirement" in text.lower() or "requirement is met" in text.lower(),
            "confidence": "LOW",
            "explanation": text[:200] + ("..." if len(text) > 200 else "")
        }
        
        return result


class GPT4AllAnalyzer:
    """
    Analyzer that checks application code against requirements using GPT4All API.
    """
    
    def __init__(self, base_path: Union[Path, str] = None):
        """
        Initialize the analyzer.
        
        Args:
            base_path: Base directory path for application code
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.client = GPT4AllClient()
        self.requirements_cache = {}
        logger.info(f"GPT4All analyzer initialized with base path: {self.base_path}")
    
    def find_app_directory(self, model: str, app_num: int) -> Path:
        """
        Find the correct directory for a specific app.
        
        Args:
            model: Model name
            app_num: App number
            
        Returns:
            Path to the app directory
        """
        # Try common directory patterns
        patterns = [
            self.base_path / f"{model}/app{app_num}",
            self.base_path / f"{model.lower()}/app{app_num}",
            self.base_path / f"{model}/App{app_num}",
            self.base_path / f"models/{model}/app{app_num}",
            self.base_path / f"z_interface_app/{model}/app{app_num}",
            self.base_path / f"z_interface_app/{model.lower()}/app{app_num}",
            Path.cwd() / f"{model}/app{app_num}",
            Path.cwd() / f"z_interface_app/{model}/app{app_num}"
        ]
        
        # Try each pattern
        for pattern in patterns:
            if pattern.exists() and pattern.is_dir():
                logger.info(f"Found app directory: {pattern}")
                return pattern
        
        # If no directory is found, log all attempted paths
        logger.warning(f"App directory not found for {model}/app{app_num}")
        logger.warning(f"Attempted paths: {[str(p) for p in patterns]}")
        
        # Return a default path
        return self.base_path / f"{model}/app{app_num}"
    
    def collect_code_files(self, directory: Path) -> Tuple[List[Path], List[Path]]:
        """
        Collect frontend and backend code files from the app directory.
        
        Args:
            directory: App directory
            
        Returns:
            Tuple of (frontend_files, backend_files)
        """
        frontend_files = []
        backend_files = []
        
        # Skip directories
        skip_dirs = {
            'node_modules', '.git', '__pycache__', 'venv', 'env',
            'dist', 'build', '.next', 'static'
        }
        
        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            # Try to create the directory
            try:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Created directory: {directory}")
            except Exception as e:
                logger.error(f"Failed to create directory: {e}")
            return [], []
        
        try:
            # Find files with common extensions
            for root, dirs, files in os.walk(directory):
                # Skip directories in-place
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
                    if file_name.endswith(('.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.vue')):
                        frontend_files.append(file_path)
                        
                    elif file_name.endswith(('.py', '.flask')):
                        backend_files.append(file_path)
                
                # Prioritize key files
                key_frontend_files = [f for f in frontend_files if f.name in ('App.jsx', 'App.js', 'index.js', 'main.js')]
                key_backend_files = [f for f in backend_files if f.name in ('app.py', 'server.py', 'main.py')]
                
                # If we have key files, put them first
                if key_frontend_files:
                    frontend_files = key_frontend_files + [f for f in frontend_files if f not in key_frontend_files]
                if key_backend_files:
                    backend_files = key_backend_files + [f for f in backend_files if f not in key_backend_files]
                    
                # Limit number of files for analysis
                frontend_files = frontend_files[:5]
                backend_files = backend_files[:5]
                
                if frontend_files or backend_files:
                    break
        except Exception as e:
            logger.error(f"Error collecting code files: {e}")
            
        logger.info(f"Found {len(frontend_files)} frontend files and {len(backend_files)} backend files")
        return frontend_files, backend_files
    
    def read_code_from_files(self, files: List[Path], max_chars: int = 8000) -> str:
        """
        Read and combine code from files with length limit.
        
        Args:
            files: List of file paths
            max_chars: Maximum characters to read
            
        Returns:
            Combined code as string
        """
        if not files:
            return ""
            
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
                        if remaining > 200:
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
    
    def get_requirements_for_app(self, app_num: int) -> Tuple[List[str], str]:
        """
        Get requirements for a specific app from requirements.json file.
        
        Args:
            app_num: App number
            
        Returns:
            Tuple of (requirements_list, template_name)
        """
        # Use cache if available
        if app_num in self.requirements_cache:
            return self.requirements_cache[app_num]
        
        # First, try to find requirements.json in the app directory
        app_directory = self.find_app_directory("Llama", app_num)  # Model doesn't matter for just finding JSON
        requirements_file = app_directory.parent / "requirements.json"
        
        logger.info(f"Looking for requirements.json at: {requirements_file}")
        
        if requirements_file.exists():
            try:
                with open(requirements_file, 'r', encoding='utf-8') as f:
                    app_data = json.load(f)
                logger.info(f"Successfully loaded requirements from {requirements_file}")
                
                # Look for the app with the matching app number
                app_key = f"app_{app_num}"
                app_info = None
                
                # Check in applications array
                if "applications" in app_data:
                    for app in app_data.get("applications", []):
                        if app.get("id") == app_key:
                            app_info = app
                            break
                # Check if app might be directly at root level with app_num key
                elif app_key in app_data:
                    app_info = app_data[app_key]
                
                if app_info:
                    # Extract requirements
                    requirements = []
                    
                    # Add general features if available
                    if "general_features" in app_info:
                        requirements.extend(app_info["general_features"])
                    
                    # Add specific features if available
                    if "specific_features" in app_info:
                        requirements.extend(app_info["specific_features"])
                    
                    # Get template name or default
                    template_name = app_info.get("name", f"App {app_num}")
                    
                    logger.info(f"Found {len(requirements)} requirements for {template_name}")
                    
                    # Cache the result
                    self.requirements_cache[app_num] = (requirements, template_name)
                    return requirements, template_name
            except Exception as e:
                logger.error(f"Error parsing requirements.json: {e}")
        
        # If we get here, either the file doesn't exist or we couldn't extract requirements
        logger.warning(f"Could not load requirements from JSON, using application data or defaults")
        
        # Fallback: Load application data from the paste.txt JSON
        app_data = self.load_application_data()
        
        if app_data and "applications" in app_data:
            # Find app by app number (1-indexed in UI but 0-indexed in data)
            app_index = (app_num - 1) % len(app_data["applications"])
            app_info = app_data["applications"][app_index]
            
            # Extract requirements
            requirements = []
            
            # Add general features
            if "general_features" in app_info:
                requirements.extend(app_info["general_features"])
                
            # Add specific features
            if "specific_features" in app_info:
                requirements.extend(app_info["specific_features"])
                
            # Default template name
            template_name = app_info.get("name", f"App {app_num}")
            
            # Cache the result
            self.requirements_cache[app_num] = (requirements, template_name)
            return requirements, template_name
            
        # Final fallback - default requirements if no app data found
        logger.warning("Using default requirements (no app data found)")
        default_requirements = [
            "Multipage Routing: Extendable routing on both backend and frontend for additional pages/views",
            "Simple and modern UI",
            "Feature complete production ready app with comments, fail states, etc.",
            "App.jsx must include mounting logic with ReactDOM from react-dom/client",
            "Keep all changes within app.py, App.jsx and App.css files"
        ]
        
        template_name = f"App {app_num}"
        
        # Cache the result
        self.requirements_cache[app_num] = (default_requirements, template_name)
        return default_requirements, template_name
    
    def load_application_data(self) -> Dict:
        """
        Load application data from JSON file.
        
        Returns:
            Dictionary with application data
        """
        # Possible locations for the application data
        possible_paths = [
            self.base_path / "applications.json",
            self.base_path / "static" / "applications.json",
            self.base_path / "data" / "applications.json",
            Path(__file__).parent / "applications.json"
        ]
        
        for path in possible_paths:
            try:
                if path.exists():
                    logger.info(f"Loading application data from {path}")
                    with open(path, 'r', encoding='utf-8') as f:
                        return json.load(f)
            except Exception as e:
                logger.error(f"Error loading application data from {path}: {e}")
                
        # If no file is found, return empty dict
        return {}
    
    def check_requirements(self, model: str, app_num: int, requirements: List[str] = None) -> List[RequirementCheck]:
        """
        Check requirements against app code.
        
        Args:
            model: Model name
            app_num: App number
            requirements: List of requirements to check (optional)
            
        Returns:
            List of RequirementCheck objects
        """
        # Check if GPT4All server is available
        if not self.client.check_server():
            logger.error("GPT4All server is not available")
            return self._create_error_checks(
                requirements or ["Server unavailable"],
                "GPT4All server is not available"
            )
            
        # Find app directory
        directory = self.find_app_directory(model, app_num)
        if not directory.exists():
            logger.error(f"App directory not found: {directory}")
            return self._create_error_checks(
                requirements or ["Directory not found"],
                f"App directory not found: {directory}"
            )
            
        # Get requirements if not provided
        if not requirements:
            requirements, _ = self.get_requirements_for_app(app_num)
            
        # Collect code files
        frontend_files, backend_files = self.collect_code_files(directory)
        
        # Read code
        frontend_code = self.read_code_from_files(frontend_files)
        backend_code = self.read_code_from_files(backend_files)
        
        if not frontend_code and not backend_code:
            logger.error(f"No code files found in {directory}")
            return self._create_error_checks(
                requirements,
                "No code files found"
            )
            
        # Check each requirement
        results = []
        for req in requirements:
            # Create a check for this requirement
            check = RequirementCheck(requirement=req)
            
            # Create combined result
            result = RequirementResult()
            
            # Check frontend code
            if frontend_code:
                logger.info(f"Analyzing frontend code for requirement: {req}")
                frontend_analysis = self.client.analyze_code(req, frontend_code, is_frontend=True)
                result.frontend_analysis = frontend_analysis
            else:
                result.frontend_analysis = {
                    "met": False,
                    "confidence": "HIGH",
                    "explanation": "No frontend code found"
                }
                
            # Check backend code
            if backend_code:
                logger.info(f"Analyzing backend code for requirement: {req}")
                backend_analysis = self.client.analyze_code(req, backend_code, is_frontend=False)
                result.backend_analysis = backend_analysis
            else:
                result.backend_analysis = {
                    "met": False,
                    "confidence": "HIGH",
                    "explanation": "No backend code found"
                }
                
            # Combine results - requirement is met if either frontend or backend meets it
            frontend_met = result.frontend_analysis.get("met", False)
            backend_met = result.backend_analysis.get("met", False)
            
            result.met = frontend_met or backend_met
            
            # Determine confidence level
            frontend_confidence = result.frontend_analysis.get("confidence", "LOW")
            backend_confidence = result.backend_analysis.get("confidence", "LOW")
            
            confidence_levels = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
            frontend_score = confidence_levels.get(frontend_confidence, 1)
            backend_score = confidence_levels.get(backend_confidence, 1)
            
            # Use higher confidence
            result.confidence = "HIGH" if max(frontend_score, backend_score) == 3 else \
                              "MEDIUM" if max(frontend_score, backend_score) == 2 else \
                              "LOW"
                              
            # Combine explanations
            frontend_explanation = result.frontend_analysis.get("explanation", "")
            backend_explanation = result.backend_analysis.get("explanation", "")
            
            combined_explanation = ""
            if frontend_explanation:
                combined_explanation += f"Frontend: {frontend_explanation}"
            if backend_explanation:
                if combined_explanation:
                    combined_explanation += "\n\nBackend: "
                else:
                    combined_explanation += "Backend: "
                combined_explanation += backend_explanation
                
            result.explanation = combined_explanation
            
            # Set the result in the check
            check.result = result
            results.append(check)
            
        logger.info(f"Completed requirement checks: {len(results)} requirements checked")
        return results
    
    def _create_error_checks(self, requirements: List[str], error_message: str) -> List[RequirementCheck]:
        """
        Create error checks for all requirements.
        
        Args:
            requirements: List of requirements
            error_message: Error message to include
            
        Returns:
            List of RequirementCheck objects with errors
        """
        return [
            RequirementCheck(
                requirement=req,
                result=RequirementResult(
                    met=False,
                    confidence="HIGH",
                    explanation="Could not analyze requirement",
                    error=error_message
                )
            )
            for req in requirements
        ]