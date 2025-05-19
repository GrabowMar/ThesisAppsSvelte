import json
import os
import time
import re
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Union, Set

import requests

# Import JsonResultsManager from utils.py
from utils import JsonResultsManager

try:
    from logging_service import create_logger_for_component
    logger = create_logger_for_component('gpt4all')
except (ImportError, Exception) as e:
    import logging
    logger = logging.getLogger('gpt4all')
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.warning(f"Using fallback logging due to error: {e}")


@dataclass
class RequirementResult:
    met: bool = False
    confidence: str = "LOW"
    explanation: str = ""
    error: Optional[str] = None
    frontend_analysis: Optional[Dict] = None
    backend_analysis: Optional[Dict] = None


@dataclass
class RequirementCheck:
    requirement: str
    result: RequirementResult = field(default_factory=RequirementResult)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requirement": self.requirement,
            "result": asdict(self.result)
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RequirementCheck':
        """Create a RequirementCheck instance from a dictionary."""
        result_data = data.get("result", {})
        result = RequirementResult(
            met=result_data.get("met", False),
            confidence=result_data.get("confidence", "LOW"),
            explanation=result_data.get("explanation", ""),
            error=result_data.get("error"),
            frontend_analysis=result_data.get("frontend_analysis"),
            backend_analysis=result_data.get("backend_analysis")
        )
        return cls(
            requirement=data.get("requirement", ""),
            result=result
        )


class GPT4AllClient:
    def __init__(self, api_url: str = None, preferred_model: str = None):
        self.api_url = api_url or os.getenv("GPT4ALL_API_URL", "http://localhost:4891/v1")
        self.preferred_model = preferred_model
        self.available_models = []
        self.timeout = int(os.getenv("GPT4ALL_TIMEOUT", "30"))
        self.last_check_time = 0
        self.is_available = False
        self.logger = logger  # Use the module-level logger
        logger.info(f"GPT4All client initialized with URL: {self.api_url}")

    def check_server(self) -> bool:
        current_time = time.time()
        if current_time - self.last_check_time < 15 and self.is_available:
            return self.is_available

        self.last_check_time = current_time

        try:
            logger.debug(f"Checking GPT4All server at: {self.api_url}/models")
            response = requests.get(f"{self.api_url}/models", timeout=5)

            if response.status_code == 200:
                models_data = response.json()

                self.available_models = []
                for model in models_data.get('data', []):
                    if isinstance(model, dict) and 'id' in model:
                        self.available_models.append(model['id'])
                    elif isinstance(model, str):
                        self.available_models.append(model)

                logger.info(f"Available GPT4All models: {self.available_models}")
                self.is_available = True
                return True
            else:
                logger.error(f"GPT4All server returned status code: {response.status_code}")
                logger.error(f"Response content: {response.text}")
                self.is_available = False
                return False
        except Exception as e:
            logger.exception(f"Error checking GPT4All server: {e}")
            self.is_available = False
            return False

    def _extract_model_id(self, model_obj) -> str:
        if isinstance(model_obj, str):
            return model_obj

        if isinstance(model_obj, dict) and 'id' in model_obj:
            return model_obj['id']

        logger.warning(f"Unknown model format: {model_obj}, using empty string")
        return ""

    def get_best_model(self) -> str:
        if not self.available_models:
            if not self.check_server():
                logger.warning("Cannot determine best model - server unavailable")
                return self.preferred_model or "Llama 3 8B Instruct"

        preferred = self._extract_model_id(self.preferred_model)
        if preferred and preferred in self.available_models:
            return preferred

        preferred_models = [
            "Llama 3 8B Instruct",
            "DeepSeek-R1-Distill-Qwen-7B",
            "Nous Hermes 2 Mistral DPO",
            "GPT4All Falcon"
        ]

        for model in preferred_models:
            if model in self.available_models:
                return model

        if self.available_models:
            return self.available_models[0]

        return "Llama 3 8B Instruct"

    def summarize_code(self, code: str, max_length: int = 8000, is_frontend: bool = True) -> str:
        import re
        from typing import List, Dict, Tuple

        if len(code) <= max_length:
            return code

        logger.info(f"Smart summarizing {'frontend' if is_frontend else 'backend'} code from {len(code)} characters")

        lines = code.split('\n')
        file_separator_pattern = re.compile(r'^---\s*File:\s*(.+?)\s*---$')
        current_file = None

        sections = []
        current_section_lines = []
        current_section_type = "unknown"

        def add_current_section(priority=1):
            if current_section_lines:
                content = '\n'.join(current_section_lines)
                sections.append((current_file, current_section_type, content, priority))
                current_section_lines.clear()

        for line in lines:
            file_match = file_separator_pattern.match(line)
            if file_match:
                add_current_section()

                current_file = file_match.group(1)
                current_section_type = "unknown"
                current_section_lines = [line]
                continue

            current_section_lines.append(line)

            line_stripped = line.strip()

            if line_stripped.startswith('import ') or line_stripped.startswith('from '):
                if current_section_type != "imports":
                    add_current_section()
                    current_section_type = "imports"
                    current_section_lines = [line]

            elif re.match(r'^\s*(export\s+)?(async\s+)?function\s+\w+\s*\(', line_stripped) or \
                 re.match(r'^\s*(export\s+)?(const|let|var)\s+\w+\s*=\s*(async\s+)?\(', line_stripped) or \
                 re.match(r'^\s*(public|private|protected|static|async)?\s*\w+\s*\(', line_stripped) or \
                 re.match(r'^\s*def\s+\w+\s*\(', line_stripped):
                add_current_section()
                current_section_type = "function_definition"
                current_section_lines = [line]

            elif re.match(r'^\s*(export\s+)?(default\s+)?class\s+\w+', line_stripped) or \
                 re.match(r'^\s*class\s+\w+', line_stripped) or \
                 re.match(r'^\s*(export\s+)?(default\s+)?function\s+[A-Z]', line_stripped) or \
                 re.match(r'^\s*(export\s+)?(const|let|var)\s+[A-Z]\w*\s*=', line_stripped):
                add_current_section()
                current_section_type = "class_definition"
                current_section_lines = [line]

            elif is_frontend and (
                 re.match(r'^\s*<\w+.*>$', line_stripped) or
                 "<template>" in line_stripped or
                 "<style" in line_stripped
            ):
                if current_section_type != "ui_template":
                    add_current_section()
                    current_section_type = "ui_template"
                    current_section_lines = [line]

        add_current_section()

        def simplify_function_body(section_content: str) -> str:
            lines = section_content.split('\n')

            signature_end = 0
            brace_count = 0

            for i, line in enumerate(lines):
                if '{' in line:
                    brace_count += line.count('{')
                if '}' in line:
                    brace_count -= line.count('}')

                if i > 0 and (
                     ('{' in line and brace_count > 0) or
                     (':' in line and line.strip().endswith(':'))
                ):
                    signature_end = i
                    break

            if signature_end == 0:
                signature_end = 1 if len(lines) > 0 else 0

            simplified = lines[:signature_end + 1]

            body_text = ' '.join(lines[signature_end + 1:])
            key_features = []

            if is_frontend:
                if 'useState' in body_text: key_features.append('// Uses state management')
                if 'useEffect' in body_text: key_features.append('// Has side effects/lifecycle')
                if 'fetch(' in body_text or 'axios' in body_text: key_features.append('// Makes API calls')
                if 'socket' in body_text.lower() or 'websocket' in body_text.lower(): key_features.append('// Uses websockets/real-time communication')
                if 'navigate(' in body_text or 'useNavigate' in body_text: key_features.append('// Uses navigation/routing')
                if 'context' in body_text.lower(): key_features.append('// Uses context API')
                if 'reducer' in body_text.lower() or 'dispatch(' in body_text: key_features.append('// Uses reducer pattern')
            else:
                if 'db.' in body_text or 'database' in body_text.lower(): key_features.append('# Uses database')
                if 'request' in body_text.lower() or 'response' in body_text.lower(): key_features.append('# Handles HTTP requests')
                if 'socket' in body_text.lower() or 'emit(' in body_text: key_features.append('# Uses websockets/real-time communication')
                if 'json' in body_text.lower(): key_features.append('# Processes JSON data')
                if 'authenticate' in body_text.lower() or 'login' in body_text.lower(): key_features.append('# Handles authentication')
                if 'session' in body_text.lower() or 'cookie' in body_text.lower(): key_features.append('# Manages sessions/cookies')

            if signature_end < len(lines):
                indent = re.match(r'^(\s*)', lines[signature_end]).group(1)
                key_features = [indent + feature for feature in key_features]

            simplified.extend(key_features)

            if '{' in '\n'.join(lines[:signature_end + 1]) and brace_count > 0:
                if signature_end >= 0:
                    initial_indent = re.match(r'^(\s*)', lines[0]).group(1)
                    simplified.append(f"{initial_indent}{'  ' * brace_count}// ... implementation")
                    simplified.append(f"{initial_indent}" + "}")
            elif lines and lines[0].strip().startswith('def '):
                indent = re.match(r'^(\s*)', lines[0]).group(1)
                simplified.append(f"{indent}    # ... implementation")

            return '\n'.join(simplified)

        def simplify_ui_template(section_content: str) -> str:
            lines = section_content.split('\n')

            if len(lines) <= 5:
                return section_content

            start_tag_pattern = re.compile(r'^\s*<(\w+)[^>]*>$')
            end_tag_pattern = re.compile(r'^\s*</(\w+)>$')

            start_tag_line = -1
            start_tag_name = ""

            for i, line in enumerate(lines):
                match = start_tag_pattern.match(line)
                if match and start_tag_line == -1:
                    start_tag_line = i
                    start_tag_name = match.group(1)
                    break

            if start_tag_line == -1:
                return '\n'.join(lines[:5]) + '\n// ... (template content)'

            end_tag_line = -1
            for i in range(len(lines) - 1, start_tag_line, -1):
                match = end_tag_pattern.match(lines[i])
                if match and match.group(1) == start_tag_name:
                    end_tag_line = i
                    break

            if end_tag_line == -1:
                return '\n'.join(lines[:5]) + '\n// ... (template content)'

            simplified = lines[:start_tag_line + 1]

            ui_text = ' '.join(lines[start_tag_line:end_tag_line])
            features = []

            if 'onClick' in ui_text or 'onChange' in ui_text or '@click' in ui_text: features.append('// Has interactive event handlers')
            if 'v-for' in ui_text or '{' in ui_text and '.map(' in ui_text: features.append('// Uses list rendering')
            if 'v-if' in ui_text or 'v-show' in ui_text or '?' in ui_text and ':' in ui_text: features.append('// Uses conditional rendering')
            if 'v-model' in ui_text or 'value=' in ui_text and 'onChange=' in ui_text: features.append('// Has form inputs with binding')
            if 'className=' in ui_text or 'class=' in ui_text: features.append('// Uses CSS classes for styling')
            if 'style=' in ui_text: features.append('// Uses inline styles')

            if start_tag_line < len(lines):
                indent = re.match(r'^(\s*)', lines[start_tag_line]).group(1) + "  "
                features = [indent + feature for feature in features]

            simplified.extend(features)
            simplified.append(indent + "// ... (template content)")

            simplified.append(lines[end_tag_line])

            return '\n'.join(simplified)

        prioritized_sections = []

        for file_name, section_type, content, base_priority in sections:
            if section_type == "imports":
                prioritized_sections.append((file_name, content, 10))
            elif section_type == "function_definition":
                simplified = simplify_function_body(content)
                prioritized_sections.append((file_name, simplified, 8))
            elif section_type == "class_definition":
                simplified = simplify_function_body(content)
                prioritized_sections.append((file_name, simplified, 9))
            elif section_type == "ui_template":
                simplified = simplify_ui_template(content)
                prioritized_sections.append((file_name, simplified, 6))
            else:
                lower_content = content.lower()
                priority = base_priority

                important_patterns = [
                    'router', 'route', 'navigation', 'socket', 'fetch', 'axios',
                    'usestate', 'useeffect', 'usecontext', 'usereducer',
                    'database', 'model', 'schema', 'authenticate', 'login',
                    'register', 'context', 'provider', 'store', 'redux'
                ]

                for pattern in important_patterns:
                    if pattern in lower_content:
                        priority += 1
                        break

                prioritized_sections.append((file_name, content, priority))

        prioritized_sections.sort(key=lambda x: x[2], reverse=True)

        result = []
        current_length = 0
        current_file = None

        for file_name, content, _ in prioritized_sections:
            if file_name != current_file:
                file_line = f"\n\n--- File: {file_name} ---"
                result.append(file_line)
                current_length += len(file_line)
                current_file = file_name

            if current_length + len(content) + 2 > max_length:
                remaining = max_length - current_length - 2
                if remaining > 200:
                    if len(content) > 500:
                        first_lines = '\n'.join(content.split('\n')[:5])
                        if len(first_lines) < remaining:
                            result.append("\n" + first_lines)
                            result.append("\n// ... (content truncated)")
                            current_length += len(first_lines) + 23
                    else:
                        truncated = content[:remaining-25] + "\n// ... (truncated)"
                        result.append("\n" + truncated)
                        current_length += len(truncated) + 1
                break

            result.append("\n" + content)
            current_length += len(content) + 1

        summarized = ''.join(result)

        summary_note = f"\n\n// Note: Code was intelligently summarized from {len(code)} to {len(summarized)} characters"
        if len(summarized) + len(summary_note) <= max_length:
            summarized += summary_note

        logger.info(f"Summarized code from {len(code)} to {len(summarized)} characters")
        return summarized

    def _fallback_analyze_code(self, requirement: str, code: str, is_frontend: bool) -> Dict[str, Any]:
        import re
        logger.info(f"Using fallback analysis for {'frontend' if is_frontend else 'backend'} code")

        req_lower = requirement.lower()

        result = {
            "met": False,
            "confidence": "LOW",
            "explanation": f"Fallback analysis: Unable to analyze with GPT4All API. Basic pattern matching used."
        }

        if is_frontend:
            if "routing" in req_lower or "multipage" in req_lower:
                router_patterns = [r'import\s+.*\brouter\b',r'import\s+.*\bRouter\b',r'<Route',r'createBrowserRouter',r'useNavigate',r'useRouter',r'useHistory',r'createWebHistory',r'createRouter',r'history\.push',r'this\.router']
                if any(re.search(pattern, code, re.IGNORECASE) for pattern in router_patterns):
                    result["met"] = True
                    result["explanation"] += " Found routing-related code patterns."
            if "ui" in req_lower or "interface" in req_lower or "modern" in req_lower:
                ui_patterns = [r'import\s+.*\b(react|vue|svelte)\b',r'<template',r'<style',r'useState',r'useEffect',r'component',r'className=',r'class=',r'@tailwind',r'tailwindcss',r'\.css']
                if any(re.search(pattern, code, re.IGNORECASE) for pattern in ui_patterns):
                    result["met"] = True
                    result["explanation"] += " Found modern UI code patterns."
            if "message" in req_lower or "chat" in req_lower or "real-time" in req_lower:
                message_patterns = [r'socket',r'websocket',r'\.emit',r'\.on\(',r'fetch\(',r'axios',r'\.post\(',r'\.get\(',r'messages\[',r'chat']
                if any(re.search(pattern, code, re.IGNORECASE) for pattern in message_patterns):
                    result["met"] = True
                    result["explanation"] += " Found messaging/chat-related code patterns."
        else:
            if "routing" in req_lower or "multipage" in req_lower:
                router_patterns = [r'@app\.route',r'@blueprint\.route',r'app\.get\(',r'app\.post\(',r'router\.',r'Blueprint\(',r'urlpatterns',r'path\(',r'url_for\(']
                if any(re.search(pattern, code, re.IGNORECASE) for pattern in router_patterns):
                    result["met"] = True
                    result["explanation"] += " Found routing-related code patterns."
            if "database" in req_lower or "storage" in req_lower or "history" in req_lower:
                db_patterns = [r'database',r'db\.',r'model\.',r'query\.',r'find_one',r'find_by',r'save\(',r'cursor\.',r'execute\(',r'collection\.']
                if any(re.search(pattern, code, re.IGNORECASE) for pattern in db_patterns):
                    result["met"] = True
                    result["explanation"] += " Found database/storage-related code patterns."
            if "message" in req_lower or "chat" in req_lower or "real-time" in req_lower:
                message_patterns = [r'socket',r'emit\(',r'on\(',r'send\(',r'receive\(',r'message',r'chat',r'websocket']
                if any(re.search(pattern, code, re.IGNORECASE) for pattern in message_patterns):
                    result["met"] = True
                    result["explanation"] += " Found messaging/chat-related code patterns."
        if result["met"]:
            result["confidence"] = "MEDIUM"
        return result

    def analyze_code(self, requirement: str, code: str, is_frontend: bool = True, model: str = None) -> Dict[str, Any]:
        if not self.check_server():
            logger.error("GPT4All server is not available")
            return {"met": False, "confidence": "LOW", "explanation": "GPT4All server is not available"}

        model_to_use = self._extract_model_id(model) if model else self.get_best_model()
        code_max_length = 8000
        if len(code) > code_max_length:
            original_len = len(code)
            code = self.summarize_code(code, code_max_length, is_frontend)
            logger.info(f"Code intelligently summarized from {original_len} to {len(code)} characters")

        system_prompt = """
You are an expert code reviewer focused on determining if code meets specific requirements.
Analyze the provided code and determine if it satisfies the given requirement.
Focus on concrete evidence in the code, not assumptions.
Some code may be summarized or simplified - look for key patterns and functionality.
Respond with JSON containing only the following fields:
{
  "met": true/false,
  "confidence": "HIGH"/"MEDIUM"/"LOW",
  "explanation": "Brief explanation with specific code evidence"
}
"""
        code_type = "Frontend" if is_frontend else "Backend"
        user_prompt = f"""
Requirement: {requirement}
Code Type: {code_type}
{f"Note: Due to size limitations, this code has been intelligently summarized to preserve structure while reducing details." if len(code) > code_max_length else ""}
Analyze if the following code meets the requirement:
```
{code}
```
Respond with JSON containing:
- "met": Whether the requirement is met (true/false)
- "confidence": Your confidence level (HIGH/MEDIUM/LOW)
- "explanation": Specific evidence from the code
"""
        available_models = self.available_models.copy() if self.available_models else [model_to_use]
        if model_to_use in available_models:
            available_models.remove(model_to_use)
            available_models.insert(0, model_to_use)

        max_attempts = min(2, len(available_models))
        for attempt in range(max_attempts):
            current_model = available_models[attempt]
            try:
                if not current_model or not isinstance(current_model, str):
                    logger.warning(f"Invalid model: {current_model}, using fallback")
                    current_model = "Llama 3 8B Instruct"
                payload = {"model": current_model, "messages": [{"role": "system", "content": system_prompt},{"role": "user", "content": user_prompt}],"temperature": 0.2,"max_tokens": 1024}
                logger.info(f"Sending analysis request to GPT4All API using model: {current_model}")
                response = requests.post(f"{self.api_url}/chat/completions", json=payload, timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    try:
                        result = json.loads(content)
                        logger.info(f"Analysis result: requirement met = {result.get('met', False)}")
                        return result
                    except json.JSONDecodeError:
                        return self._extract_json_from_text(content)
                else:
                    logger.error(f"GPT4All API request failed: {response.status_code}")
                    logger.error(f"Response: {response.text[:500]}")
                    if attempt < max_attempts - 1:
                        logger.info(f"Retrying with alternate model: {available_models[attempt+1]}")
                        continue
                    return self._fallback_analyze_code(requirement, code, is_frontend)
            except Exception as e:
                logger.exception(f"Error analyzing code: {str(e)}")
                if attempt < max_attempts - 1:
                    logger.info(f"Retrying with alternate model due to exception: {available_models[attempt+1]}")
                    continue
                return self._fallback_analyze_code(requirement, code, is_frontend)
        return self._fallback_analyze_code(requirement, code, is_frontend)

    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        json_match = re.search(r'({.*?})', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        result = {"met": "meets the requirement" in text.lower() or "requirement is met" in text.lower(), "confidence": "LOW", "explanation": text[:200] + ("..." if len(text) > 200 else "")}
        return result


class GPT4AllAnalyzer:
    def __init__(self, base_path: Union[Path, str] = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.client = GPT4AllClient()
        
        if "z_interface_app" in str(self.base_path):
            self.base_path = self.base_path.parent
        else:
            self.base_path = self.base_path
        # Initialize JsonResultsManager
        self.results_manager = JsonResultsManager(base_path=self.base_path, module_name="gpt4all")
        
        # Cache for quick lookup of previously analyzed requirements
        self.requirements_cache = {}
        
        logger.info(f"GPT4All analyzer initialized with base path: {self.base_path}")

    def find_app_directory(self, model: str, app_num: int) -> Path:
        patterns = [
            self.base_path.parent / f"models/{model}/app{app_num}",
            self.base_path.parent / f"models/{model.lower()}/app{app_num}",
            self.base_path.parent / f"models/{model}/App{app_num}",
        ]
        for pattern in patterns:
            if pattern.exists() and pattern.is_dir():
                logger.info(f"Found app directory: {pattern}")
                return pattern
        logger.warning(f"App directory not found for models/{model}/app{app_num}")
        logger.warning(f"Attempted paths: {[str(p) for p in patterns]}")
        return self.base_path / f"models/{model}/app{app_num}"

    def collect_code_files(self, directory: Path) -> Tuple[List[Path], List[Path]]:
        frontend_files = []
        backend_files = []
        skip_dirs = {'node_modules', '.git', '__pycache__', 'venv', 'env', 'dist', 'build', '.next', 'static', 'assets', 'out', 'coverage', 'logs', 'tmp', 'temp'}
        frontend_exts = ('.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.vue', '.svelte', '.json', '.less', '.scss', '.sass', '.xml', '.mjs', '.cjs', '.esm.js')
        backend_exts = ('.py', '.flask', '.wsgi', '.django')
        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return [], []
        key_frontend_files = {'App.jsx', 'App.js', 'index.js', 'main.js', 'app.jsx', 'app.js', 'index.jsx', 'index.tsx', 'App.svelte', 'App.vue'}
        key_backend_files = {'app.py', 'server.py', 'main.py', 'api.py', 'flask_app.py', 'django_app.py', 'routes.py', 'views.py'}
        try:
            frontend_dir = directory / "frontend"
            backend_dir = directory / "backend"
            visited_dirs = set()
            all_frontend_files = []
            all_backend_files = []
            if frontend_dir.exists() and frontend_dir.is_dir():
                logger.info(f"Found frontend directory: {frontend_dir}")
                for root, dirs, files in os.walk(frontend_dir):
                    dirs[:] = [d for d in dirs if d not in skip_dirs]
                    current_dir = os.path.normpath(root)
                    if current_dir in visited_dirs: continue
                    visited_dirs.add(current_dir)
                    root_path = Path(root)
                    for file_name in files:
                        file_path = root_path / file_name
                        try:
                            if file_path.stat().st_size > 300 * 1024: continue
                        except (PermissionError, OSError): continue
                        if file_name.endswith(frontend_exts): all_frontend_files.append(file_path)
            else: logger.warning(f"Frontend directory not found: {frontend_dir}")
            if backend_dir.exists() and backend_dir.is_dir():
                logger.info(f"Found backend directory: {backend_dir}")
                for root, dirs, files in os.walk(backend_dir):
                    dirs[:] = [d for d in dirs if d not in skip_dirs]
                    current_dir = os.path.normpath(root)
                    if current_dir in visited_dirs: continue
                    visited_dirs.add(current_dir)
                    root_path = Path(root)
                    for file_name in files:
                        file_path = root_path / file_name
                        try:
                            if file_path.stat().st_size > 300 * 1024: continue
                        except (PermissionError, OSError): continue
                        if file_name.endswith(backend_exts): all_backend_files.append(file_path)
            else: logger.warning(f"Backend directory not found: {backend_dir}")
            if not all_frontend_files or not all_backend_files:
                logger.info(f"Falling back to scanning entire directory: {directory}")
                for root, dirs, files in os.walk(directory):
                    dirs[:] = [d for d in dirs if d not in skip_dirs]
                    current_dir = os.path.normpath(root)
                    if current_dir in visited_dirs: continue
                    visited_dirs.add(current_dir)
                    root_path = Path(root)
                    for file_name in files:
                        file_path = root_path / file_name
                        try:
                            if file_path.stat().st_size > 300 * 1024: continue
                        except (PermissionError, OSError): continue
                        if file_name.endswith(frontend_exts) and file_path not in all_frontend_files: all_frontend_files.append(file_path)
                        elif file_name.endswith(backend_exts) and file_path not in all_backend_files: all_backend_files.append(file_path)
            for file_path in all_frontend_files:
                if file_path.name in key_frontend_files: frontend_files.append(file_path)
            remaining_frontend = [f for f in all_frontend_files if f not in frontend_files]
            frontend_files.extend(remaining_frontend[:10 - len(frontend_files)])
            for file_path in all_backend_files:
                if file_path.name in key_backend_files: backend_files.append(file_path)
            remaining_backend = [f for f in all_backend_files if f not in backend_files]
            backend_files.extend(remaining_backend[:10 - len(backend_files)])
        except Exception as e:
            logger.error(f"Error collecting code files: {e}")
            logger.exception("Traceback for file collection error:")
        logger.info(f"Found {len(frontend_files)} frontend files and {len(backend_files)} backend files")
        return frontend_files, backend_files

    def read_code_from_files(self, files: List[Path], max_chars: int = 12000) -> str:
        if not files: return ""
        combined_code = ""
        total_chars = 0
        files_included = 0
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    code = f.read()
                    if not code.strip(): continue
                    file_snippet = f"\n\n--- File: {file_path.name} ---\n{code}"
                    if total_chars + len(file_snippet) > max_chars:
                        remaining = max_chars - total_chars
                        if remaining > 200:
                            partial = file_snippet[:remaining] + "\n...[truncated]"
                            combined_code += partial
                            files_included += 1
                        break
                    combined_code += file_snippet
                    total_chars += len(file_snippet)
                    files_included += 1
                    if total_chars >= max_chars: break
            except Exception as e: logger.error(f"Error reading file {file_path}: {e}")
        logger.info(f"Included {files_included} files in code analysis (total {total_chars} chars)")
        return combined_code

    def get_requirements_for_app(self, app_num: int) -> Tuple[List[str], str]:
        if app_num in self.requirements_cache: return self.requirements_cache[app_num]
        app_directory = self.find_app_directory("Claude", 1)
        requirements_file = app_directory.parent.parent / "requirements.json"
        logger.info(f"Looking for requirements.json at: {requirements_file}")
        if requirements_file.exists():
            try:
                with open(requirements_file, 'r', encoding='utf-8') as f: app_data = json.load(f)
                logger.info(f"Successfully loaded requirements from {requirements_file}")
                found_requirements = []
                template_name = f"App {app_num}"
                app_key = f"app_{app_num}"
                if "applications" in app_data:
                    for app in app_data.get("applications", []):
                        if app.get("id") == app_key or str(app.get("id")) == str(app_num):
                            if "specific_features" in app: found_requirements.extend(app["specific_features"]); logger.info(f"Found {len(app['specific_features'])} specific features")
                            if "general_features" in app: found_requirements.extend(app["general_features"]); logger.info(f"Found {len(app['general_features'])} general features")
                            if "requirements" in app: found_requirements.extend(app["requirements"]); logger.info(f"Found {len(app['requirements'])} requirements")
                            if "name" in app: template_name = app["name"]
                            break
                elif app_key in app_data:
                    app_info = app_data[app_key]
                    if "specific_features" in app_info: found_requirements.extend(app_info["specific_features"])
                    if "general_features" in app_info: found_requirements.extend(app_info["general_features"])
                    if "requirements" in app_info: found_requirements.extend(app_info["requirements"])
                    if "name" in app_info: template_name = app_info["name"]
                elif str(app_num) in app_data:
                    app_info = app_data[str(app_num)]
                    if "specific_features" in app_info: found_requirements.extend(app_info["specific_features"])
                    if "general_features" in app_info: found_requirements.extend(app_info["general_features"])
                    if "requirements" in app_info: found_requirements.extend(app_info["requirements"])
                    if "name" in app_info: template_name = app_info["name"]
                elif isinstance(app_data, list):
                    found_requirements = app_data
                    logger.info(f"Found {len(found_requirements)} requirements in flat array")
                if found_requirements:
                    logger.info(f"Found {len(found_requirements)} total requirements for {template_name}")
                    self.requirements_cache[app_num] = (found_requirements, template_name)
                    return found_requirements, template_name
                else: logger.warning("No requirements found in JSON file, using fallbacks")
            except Exception as e: logger.error(f"Error parsing requirements.json: {e}")
        logger.warning(f"Could not load requirements from JSON, using application data or defaults")
        app_data = self.load_application_data()
        if app_data and "applications" in app_data:
            app_index = (app_num - 1) % len(app_data["applications"])
            app_info = app_data["applications"][app_index]
            requirements = []
            if "general_features" in app_info: requirements.extend(app_info["general_features"])
            if "specific_features" in app_info: requirements.extend(app_info["specific_features"])
            template_name = app_info.get("name", f"App {app_num}")
            self.requirements_cache[app_num] = (requirements, template_name)
            return requirements, template_name
        logger.warning("Using default requirements (no app data found)")
        default_requirements = ["Multipage Routing: Extendable routing on both backend and frontend for additional pages/views","Simple and modern UI","Feature complete production ready app with comments, fail states, etc.","App.jsx must include mounting logic with ReactDOM from react-dom/client","Keep all changes within app.py, App.jsx and App.css files"]
        template_name = f"App {app_num}"
        self.requirements_cache[app_num] = (default_requirements, template_name)
        return default_requirements, template_name

    def load_application_data(self) -> Dict:
        possible_paths = [self.base_path / "applications.json",self.base_path / "static" / "applications.json",self.base_path / "data" / "applications.json",Path(__file__).parent / "applications.json"]
        for path in possible_paths:
            try:
                if path.exists():
                    logger.info(f"Loading application data from {path}")
                    with open(path, 'r', encoding='utf-8') as f: return json.load(f)
            except Exception as e: logger.error(f"Error loading application data from {path}: {e}")
        return {}

    # Add method to save requirements analysis results
    def save_requirements(self, model: str, app_num: int, results: List[RequirementCheck]) -> Optional[Path]:
        """
        Save requirement check results to a JSON file.
        
        Args:
            model: Model name
            app_num: Application number
            results: List of RequirementCheck objects
            
        Returns:
            Path where results were saved or None if error
        """
        try:
            # Prepare data for saving
            results_data = {
                "requirements": [check.to_dict() for check in results],
                "metadata": {
                    "model": model,
                    "app_num": app_num,
                    "total_checks": len(results),
                    "met_count": sum(1 for check in results if check.result.met),
                    "scan_time": time.time()
                }
            }
            
            # Save using JsonResultsManager
            file_name = ".gpt4all_requirements.json"
            results_path = self.results_manager.save_results(
                model=model,
                app_num=app_num,
                results=results_data,
                file_name=file_name,
                maintain_legacy=False
            )
            logger.info(f"Saved requirements analysis results to {results_path}")
            return results_path
        except Exception as e:
            logger.error(f"Error saving requirements analysis results: {e}")
            return None
    
    # Add method to load requirements analysis results
    def load_requirements(self, model: str, app_num: int) -> Optional[List[RequirementCheck]]:
        """
        Load requirement check results from a JSON file.
        
        Args:
            model: Model name
            app_num: Application number
            
        Returns:
            List of RequirementCheck objects or None if not found
        """
        try:
            file_name = ".gpt4all_requirements.json"
            data = self.results_manager.load_results(
                model=model,
                app_num=app_num,
                file_name=file_name
            )
            
            if not data or not isinstance(data, dict) or "requirements" not in data:
                logger.warning(f"No valid requirements data found for {model}/app{app_num}")
                return None
                
            requirements_data = data.get("requirements", [])
            
            if not requirements_data:
                logger.warning(f"Empty requirements data found for {model}/app{app_num}")
                return None
                
            logger.info(f"Loaded {len(requirements_data)} requirements checks from saved data for {model}/app{app_num}")
            return [RequirementCheck.from_dict(item) for item in requirements_data]
        except Exception as e:
            logger.error(f"Error loading requirements for {model}/app{app_num}: {e}")
            return None

    def check_requirements(self, model: str, app_num: int, requirements: List[str] = None, force_rerun: bool = False) -> List[RequirementCheck]:
        """
        Check multiple requirements against both frontend and backend code.
        
        Args:
            model: Model name
            app_num: Application number
            requirements: List of requirements to check (if None, loads from a config)
            force_rerun: Whether to force rerun the analysis instead of using cached results
            
        Returns:
            List of RequirementCheck objects
        """
        # Check if the GPT4All server is available
        if not self.client.check_server():
            logger.error("GPT4All server is not available")
            return self._create_error_checks(requirements or ["Server unavailable"], "GPT4All server is not available")
        
        # Try to load saved results if not forcing a rerun
        if not force_rerun:
            saved_checks = self.load_requirements(model, app_num)
            if saved_checks and (not requirements or len(saved_checks) == len(requirements)):
                logger.info(f"Using saved analysis results for {model}/app{app_num}")
                return saved_checks
        
        # Find the application directory
        directory = self.find_app_directory(model, app_num)
        if not directory.exists():
            logger.error(f"App directory not found: {directory}")
            return self._create_error_checks(requirements or ["Directory not found"], f"App directory not found: {directory}")
        
        # Load requirements if not provided
        if not requirements:
            requirements, _ = self.get_requirements_for_app(app_num)
        
        # Collect and read code files
        frontend_files, backend_files = self.collect_code_files(directory)
        frontend_code = self.read_code_from_files(frontend_files)
        backend_code = self.read_code_from_files(backend_files)
        
        if not frontend_code and not backend_code:
            logger.error(f"No code files found in {directory}")
            return self._create_error_checks(requirements, "No code files found")
        
        # Check each requirement
        results = []
        for req in requirements:
            check = RequirementCheck(requirement=req)
            result = RequirementResult()
            
            # Analyze frontend code
            frontend_analysis = None
            if frontend_code:
                logger.info(f"Analyzing frontend code for requirement: {req}")
                frontend_analysis = self.client.analyze_code(req, frontend_code, is_frontend=True)
                result.frontend_analysis = frontend_analysis
            else:
                result.frontend_analysis = {"met": False, "confidence": "HIGH", "explanation": "No frontend code found"}
            
            # Analyze backend code
            backend_analysis = None
            if backend_code:
                logger.info(f"Analyzing backend code for requirement: {req}")
                backend_analysis = self.client.analyze_code(req, backend_code, is_frontend=False)
                result.backend_analysis = backend_analysis
            else:
                result.backend_analysis = {"met": False, "confidence": "HIGH", "explanation": "No backend code found"}
            
            # Determine overall requirement status
            frontend_met = frontend_analysis.get("met", False) if frontend_code else False
            backend_met = backend_analysis.get("met", False) if backend_code else False
            result.met = frontend_met or backend_met
            
            # Determine confidence level
            frontend_confidence = frontend_analysis.get("confidence", "LOW") if frontend_code else "LOW"
            backend_confidence = backend_analysis.get("confidence", "LOW") if backend_code else "LOW"
            confidence_levels = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
            frontend_score = confidence_levels.get(frontend_confidence, 1)
            backend_score = confidence_levels.get(backend_confidence, 1)
            result.confidence = "HIGH" if max(frontend_score, backend_score) == 3 else "MEDIUM" if max(frontend_score, backend_score) == 2 else "LOW"
            
            # Combine explanations
            frontend_explanation = frontend_analysis.get("explanation", "") if frontend_code else "No frontend code found"
            backend_explanation = backend_analysis.get("explanation", "") if backend_code else "No backend code found"
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
            check.result = result
            results.append(check)
        
        # Save the results using JsonResultsManager
        self.save_requirements(model, app_num, results)
        
        logger.info(f"Completed requirement checks: {len(results)} requirements checked")
        return results

    def get_analysis_summary(self, model: str, app_num: int, results: List[RequirementCheck] = None) -> Dict[str, Any]:
        """
        Generate a summary of the requirements analysis results.
        
        Args:
            model: Model name
            app_num: Application number
            results: List of RequirementCheck objects (if None, tries to load from saved results)
            
        Returns:
            Dictionary with summary information
        """
        # If results not provided, try to load from saved data
        if results is None:
            results = self.load_requirements(model, app_num)
            if not results:
                logger.warning(f"No saved results found for {model}/app{app_num} to generate summary")
                return {
                    "model": model,
                    "app_num": app_num,
                    "total_requirements": 0,
                    "met_count": 0,
                    "completion_percentage": 0,
                    "error": "No analysis results available"
                }
        
        # Calculate summary metrics
        summary = {
            "model": model,
            "app_num": app_num,
            "total_requirements": len(results),
            "met_count": sum(1 for check in results if check.result.met),
            "confidence_counts": {
                "HIGH": sum(1 for check in results if check.result.confidence == "HIGH"),
                "MEDIUM": sum(1 for check in results if check.result.confidence == "MEDIUM"),
                "LOW": sum(1 for check in results if check.result.confidence == "LOW"),
            },
            "frontend_met": sum(1 for check in results 
                              if check.result.frontend_analysis and 
                              check.result.frontend_analysis.get("met", False)),
            "backend_met": sum(1 for check in results 
                             if check.result.backend_analysis and 
                             check.result.backend_analysis.get("met", False)),
            "scan_time": time.time(),
            "requirements_list": [check.requirement for check in results]
        }
        
        # Calculate completion percentage
        if results:
            summary["completion_percentage"] = round((summary["met_count"] / summary["total_requirements"]) * 100)
        else:
            summary["completion_percentage"] = 0
            
        return summary

    def _create_error_checks(self, requirements: List[str], error_message: str) -> List[RequirementCheck]:
        return [RequirementCheck(requirement=req, result=RequirementResult(met=False, confidence="HIGH", explanation="Could not analyze requirement", error=error_message)) for req in requirements]


def apply_logging_fixes():
    import logging
    class FixedContextFilter(logging.Filter):
        def __init__(self, app_name: str = "app"):
            super().__init__()
            self.app_name = app_name
        def filter(self, record):
            if not hasattr(record, 'request_id'):
                try:
                    from flask import g, has_request_context, has_app_context
                    if has_app_context() and has_request_context(): record.request_id = getattr(g, 'request_id', '-')
                    else: record.request_id = '-'
                except (RuntimeError, ImportError): record.request_id = '-'
            if not hasattr(record, 'component'):
                if record.name and record.name.find('.') > 0: record.component = record.name.split('.')[0]
                else: record.component = self.app_name
            return True
    root_logger = logging.getLogger()
    context_filter = FixedContextFilter()
    root_logger.addFilter(context_filter)
    for logger_name in ['werkzeug', 'requests', 'errors', 'gpt4all']:
        logger = logging.getLogger(logger_name)
        logger.addFilter(context_filter)
    for handler in root_logger.handlers: handler.addFilter(context_filter)
    logger.info("Applied logging fixes to avoid request_id KeyError")

try:
    apply_logging_fixes()
except Exception as e:
    logger.warning(f"Could not apply logging fixes: {e}")