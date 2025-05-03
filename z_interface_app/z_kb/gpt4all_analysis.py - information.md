"""
GPT4All Requirements Analysis Module

This module connects to a local GPT4All API server to analyze code against requirements.
It uses the GPT4All API (compatible with OpenAI's API format) to determine if applications
meet specified requirements.
"""

# =============================================================================
# Standard Library Imports
# =============================================================================
import json
import os
import time
import re
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Union, Set

# =============================================================================
# Third-Party Imports
# =============================================================================
import requests

# =============================================================================
# Configure Logging
# =============================================================================
# Try to import from logging_service, but use basic logging if it fails
try:
    from logging_service import create_logger_for_component
    logger = create_logger_for_component('gpt4all')
except (ImportError, Exception) as e:
    # Set up basic logging as fallback
    import logging
    logger = logging.getLogger('gpt4all')
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    handler.setFormatter(formatter)
    if not logger.hasHandlers(): # Avoid adding handler multiple times
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.warning(f"Using fallback logging due to error: {e}")

# =============================================================================
# Domain Models
# =============================================================================
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

# =============================================================================
# GPT4All Client
# =============================================================================
class GPT4AllClient:
    """Client for connecting to a local GPT4All API server."""

    def __init__(self, api_url: str = None, preferred_model: str = None):
        """
        Initialize the GPT4All client.

        Args:
            api_url: Base URL for the GPT4All API server (including /v1 if needed)
            preferred_model: Preferred model to use (if available)
        """
        # Ensure the URL ends with /v1 if not already present
        raw_url = api_url or os.getenv("GPT4ALL_API_URL", "http://localhost:4891/v1")
        if not raw_url.endswith('/v1'):
             if raw_url.endswith('/'):
                  self.api_url = raw_url + 'v1'
             else:
                  self.api_url = raw_url + '/v1'
        else:
             self.api_url = raw_url

        self.preferred_model = preferred_model
        self.available_models = []
        self.timeout = int(os.getenv("GPT4ALL_TIMEOUT", "60")) # Increased default timeout
        self.last_check_time = 0
        self.is_available = False
        logger.info(f"GPT4All client initialized with API URL: {self.api_url}")

    def check_server(self) -> bool:
        """
        Check if the GPT4All server is available and fetch available models.

        Returns:
            bool: True if server is available, False otherwise
        """
        # Limit checks to once every 15 seconds
        current_time = time.time()
        # Always check if currently marked as unavailable
        if not self.is_available or (current_time - self.last_check_time > 15):
            self.last_check_time = current_time
            try:
                models_endpoint = f"{self.api_url}/models"
                logger.debug(f"Checking GPT4All server at: {models_endpoint}")
                response = requests.get(models_endpoint, timeout=5) # Short timeout for check

                if response.status_code == 200:
                    models_data = response.json()
                    # Process the models data - handle different response formats
                    self.available_models = []
                    for model in models_data.get('data', []):
                        # If it's a dict with an 'id' field, extract that
                        if isinstance(model, dict) and 'id' in model:
                            self.available_models.append(model['id'])
                        # If it's a string, use directly
                        elif isinstance(model, str):
                            self.available_models.append(model)

                    logger.info(f"Available GPT4All models: {self.available_models}")
                    self.is_available = True
                    return True
                else:
                    logger.error(f"GPT4All server returned status code: {response.status_code}")
                    logger.error(f"Response content: {response.text[:500]}") # Log first 500 chars
                    self.is_available = False
                    return False
            except requests.exceptions.RequestException as e:
                logger.error(f"Error checking GPT4All server at {self.api_url}: {e}")
                self.is_available = False
                return False
            except Exception as e:
                logger.exception(f"Unexpected error checking GPT4All server: {e}")
                self.is_available = False
                return False
        # Return cached availability if check was recent
        return self.is_available

    def _extract_model_id(self, model_obj) -> str:
        """
        Extract the model ID string from a model object.

        Args:
            model_obj: Model specification (can be string, dict, or None)

        Returns:
            String ID of the model
        """
        if isinstance(model_obj, str):
            return model_obj
        if isinstance(model_obj, dict) and 'id' in model_obj:
            return model_obj['id']
        logger.warning(f"Unknown model format: {model_obj}, using empty string")
        return ""

    def get_best_model(self) -> str:
        """
        Get the best available model based on preferences or defaults.

        Returns:
            str: Name of the best available model to use
        """
        if not self.available_models:
            if not self.check_server(): # Attempt to fetch models if list is empty
                logger.warning("Cannot determine best model - server unavailable")
                # Return preferred if set, otherwise a sensible default
                return self.preferred_model or "Meta-Llama-3-8B-Instruct.Q4_0.gguf"

        # If preferred model is available, use it
        preferred = self._extract_model_id(self.preferred_model)
        if preferred and preferred in self.available_models:
            logger.debug(f"Using preferred model: {preferred}")
            return preferred

        # Known good models in order of preference (update with current models)
        preferred_models_order = [
            "Meta-Llama-3-8B-Instruct.Q4_0.gguf", # Example Llama 3 model name
            "Nous-Hermes-2-Mistral-7B-DPO.Q4_0.gguf", # Example Hermes 2
            "mistral-7b-instruct-v0.1.Q4_0.gguf", # Example Mistral Instruct
            "gpt4all-falcon-q4_0.gguf" # Example Falcon
        ]

        # Find first available preferred model
        for model_name in preferred_models_order:
            if model_name in self.available_models:
                logger.debug(f"Using first available preferred model: {model_name}")
                return model_name

        # If none of the preferred models are available, use the first available model
        if self.available_models:
            first_available = self.available_models[0]
            logger.debug(f"Using first model from server list: {first_available}")
            return first_available

        # Absolute fallback
        fallback_default = "Meta-Llama-3-8B-Instruct.Q4_0.gguf"
        logger.warning(f"No suitable model found, falling back to default: {fallback_default}")
        return fallback_default

    def summarize_code(self, code: str, max_length: int = 8000, is_frontend: bool = True) -> str:
        """
        Intelligently summarize code to reduce size while preserving structure and functionality signatures.

        Args:
            code: Original source code
            max_length: Maximum length to target
            is_frontend: Whether the code is frontend (affects summarization strategies)

        Returns:
            Summarized code that preserves key structural elements
        """
        # If code is already under max length, return as is
        if len(code) <= max_length:
            return code

        logger.info(f"Smart summarizing {'frontend' if is_frontend else 'backend'} code from {len(code)} characters to target < {max_length}")

        lines = code.split('\n')
        file_separator_pattern = re.compile(r'^---\s*File:\s*(.+?)\s*---$')
        current_file = None

        # Track different sections of code: List of (file_name, section_type, section_content, priority)
        sections = []
        current_section_lines = []
        current_section_type = "unknown"

        def add_current_section(priority=1):
            nonlocal current_section_lines, current_section_type, current_file
            if current_section_lines:
                content = '\n'.join(current_section_lines)
                sections.append((current_file, current_section_type, content, priority))
                current_section_lines = [] # Reset for next section

        # Process lines to identify sections
        for line in lines:
            file_match = file_separator_pattern.match(line)
            if file_match:
                add_current_section() # Add previous section before moving to new file
                current_file = file_match.group(1)
                current_section_type = "file_header" # Mark header specifically
                current_section_lines = [line] # Keep the file separator line
                add_current_section(priority=100) # Add header immediately with high priority
                current_section_type = "unknown" # Reset type for content after header
                continue

            # Add line to current section (if not empty or just whitespace)
            if line.strip():
                 current_section_lines.append(line)

            # Try to identify section type based on content
            line_stripped = line.strip()

            # Detect imports (high priority)
            if line_stripped.startswith(('import ', 'from ')):
                if current_section_type != "imports":
                    add_current_section()
                    current_section_type = "imports"
                    current_section_lines = [line] # Start new section with this line

            # Detect function/method definitions (high priority)
            elif re.match(r'^\s*(export\s+)?(async\s+)?function\s+\w+\s*\(', line_stripped) or \
                 re.match(r'^\s*(export\s+)?(const|let|var)\s+\w+\s*=\s*(async\s+)?\(', line_stripped) or \
                 re.match(r'^\s*(public|private|protected|static|async)?\s*\w+\s*\(', line_stripped) or \
                 re.match(r'^\s*def\s+\w+\s*\(', line_stripped):
                if current_section_type != "function_definition":
                    add_current_section()
                    current_section_type = "function_definition"
                    current_section_lines = [line]

            # Detect class/component definitions (high priority)
            elif re.match(r'^\s*(export\s+)?(default\s+)?class\s+\w+', line_stripped) or \
                 re.match(r'^\s*class\s+\w+', line_stripped) or \
                 re.match(r'^\s*(export\s+)?(default\s+)?function\s+[A-Z]', line_stripped) or \
                 re.match(r'^\s*(export\s+)?(const|let|var)\s+[A-Z]\w*\s*=', line_stripped):
                 if current_section_type != "class_definition":
                    add_current_section()
                    current_section_type = "class_definition"
                    current_section_lines = [line]

            # Detect JSX/HTML elements for frontend (medium priority)
            elif is_frontend and (
                 re.match(r'^\s*<\w+.*>$', line_stripped) or
                 "<template>" in line_stripped or
                 "<style" in line_stripped
            ):
                if current_section_type != "ui_template":
                    add_current_section()
                    current_section_type = "ui_template"
                    current_section_lines = [line]
            # If line doesn't match specific types, ensure it's part of 'unknown'
            elif current_section_type not in ["imports", "function_definition", "class_definition", "ui_template"]:
                 if current_section_type != "unknown":
                      add_current_section() # Add previous typed section
                      current_section_type = "unknown"
                      current_section_lines = [line] # Start new unknown section


        # Add final section
        add_current_section()

        # --- Simplification Logic ---
        def simplify_function_body(section_content: str) -> str:
            lines = section_content.split('\n')
            if not lines: return ""

            # Find function signature (first line or lines until opening brace/colon)
            signature_end_index = 0
            brace_level = 0
            in_signature = True
            for i, line in enumerate(lines):
                if in_signature:
                     brace_level += line.count('{') - line.count('}')
                     # Python def ends with :, JS/TS often ends with { or => {
                     if line.strip().endswith(':') or ('{' in line and brace_level > 0) or '=> {' in line:
                          signature_end_index = i
                          in_signature = False
                     # Handle multi-line signatures without immediate brace/colon
                     elif i > 0 and not line.strip().startswith(('#', '//')) and not re.match(r'^\s*$', line):
                          # If it's not a comment or blank and doesn't look like start of body
                          # assume it's part of signature (e.g. params on new lines)
                          continue
                     elif i > 0: # If it's a comment or blank line after first line, signature likely ended
                          signature_end_index = i - 1
                          in_signature = False

                if not in_signature: break # Stop once signature is likely found

            # If no clear end found, assume first line is signature
            if signature_end_index == 0 and len(lines) > 1:
                 signature_end_index = 0

            signature_lines = lines[:signature_end_index + 1]
            body_lines = lines[signature_end_index + 1:]

            # Keep signature and add simplified body placeholder
            simplified = signature_lines
            indent = ""
            if signature_lines:
                 match = re.match(r'^(\s*)', signature_lines[-1])
                 if match: indent = match.group(1) + "    " # Add typical indentation

            placeholder = f"{indent}// ... (Implementation details omitted)"
            if is_frontend: placeholder = f"{indent}// ... (Implementation details omitted)"
            else: placeholder = f"{indent}# ... (Implementation details omitted)"

            simplified.append(placeholder)

            # Add closing brace/dedent if needed
            # This part is tricky and might need refinement based on language specifics
            # For simplicity, we omit smart closing brace handling for now

            return '\n'.join(simplified)

        def simplify_ui_template(section_content: str) -> str:
            lines = section_content.split('\n')
            # Keep first and last few lines of template for context
            if len(lines) <= 10: return section_content # Keep short templates
            return '\n'.join(lines[:5]) + f"\n{' ' * 4}// ... (Template content omitted)\n" + '\n'.join(lines[-3:])

        # --- Process and Prioritize Sections ---
        prioritized_sections = []
        for file_name, section_type, content, base_priority in sections:
            priority = base_priority
            simplified_content = content

            if section_type == "file_header":
                 priority = 100 # Always keep file headers
            elif section_type == "imports":
                priority = 90
            elif section_type == "class_definition":
                priority = 80
                simplified_content = simplify_function_body(content) # Reuse function logic for classes
            elif section_type == "function_definition":
                priority = 70
                simplified_content = simplify_function_body(content)
            elif section_type == "ui_template":
                priority = 60
                simplified_content = simplify_ui_template(content)
            else: # Unknown section type
                priority = 50 # Lower priority for generic code blocks
                # Optionally truncate long unknown blocks
                if len(content) > 1000:
                     simplified_content = content[:500] + "\n// ... (Generic code block truncated)"

            prioritized_sections.append((file_name, simplified_content, priority))

        # Sort sections by priority (descending)
        prioritized_sections.sort(key=lambda x: x[2], reverse=True)

        # Reconstruct code, keeping as much as will fit under max_length
        result_lines = []
        current_length = 0
        current_file = None

        for file_name, content, _ in prioritized_sections:
            # Add file separator if this is a new file and not the first section
            file_line = ""
            if file_name != current_file:
                if result_lines: # Add separator only if not the very first file
                     file_line = f"\n\n--- File: {file_name} ---"
                else: # Handle the very first file header if it exists
                     if content.startswith("--- File:"):
                          file_line = content # Use the existing header
                          content = "" # Clear content as it was just the header
                     else: # Add header if missing
                          file_line = f"--- File: {file_name} ---"

                current_file = file_name

            # Calculate length to add (separator + newline + content)
            length_to_add = len(file_line) + (1 if file_line else 0) + len(content) + (1 if content else 0)

            # Check if adding this section would exceed max length
            if current_length + length_to_add > max_length:
                remaining_space = max_length - current_length
                # Try adding just the file header if possible
                if file_line and len(file_line) < remaining_space:
                     result_lines.append(file_line)
                     current_length += len(file_line) + 1
                     remaining_space -= (len(file_line) + 1)
                # Add truncation note if space allows
                trunc_note = "\n// ... (Code truncated due to length limit)"
                if remaining_space > len(trunc_note):
                     result_lines.append(trunc_note)
                break # Stop adding sections

            # Add the file separator (if any) and the content
            if file_line:
                 result_lines.append(file_line)
                 current_length += len(file_line) + 1 # Account for newline
            if content:
                 result_lines.append(content)
                 current_length += len(content) + 1 # Account for newline


        summarized = '\n'.join(result_lines).strip()

        # Add a final note about summarization if space permits
        summary_note = f"\n\n// Note: Code was intelligently summarized from original length to {len(summarized)} characters"
        if len(summarized) + len(summary_note) <= max_length:
            summarized += summary_note

        logger.info(f"Summarized code size: {len(summarized)} characters")
        return summarized

    def _fallback_analyze_code(self, requirement: str, code: str, is_frontend: bool) -> Dict[str, Any]:
        """
        Basic fallback analysis when the GPT4All API fails.
        Uses regex pattern matching for common code patterns.

        Args:
            requirement: The requirement to check
            code: The code to analyze
            is_frontend: Whether the code is frontend (True) or backend (False)

        Returns:
            Dict containing basic analysis result
        """
        logger.warning(f"Using fallback regex analysis for {'frontend' if is_frontend else 'backend'} code for requirement: '{requirement}'")

        req_lower = requirement.lower()
        code_lower = code.lower() # Analyze lowercase code for patterns

        # Basic analysis based on requirement keywords
        result = {
            "met": False,
            "confidence": "LOW",
            "explanation": f"Fallback regex analysis used. "
        }
        found_evidence = []

        # --- Frontend Patterns ---
        if is_frontend:
            patterns = {
                "routing": [r'<route', r'createbrowserrouter', r'usenavigate', r'userouter', r'usehistory', r'createwebhistory', r'createrouter', r'history\.push', r'this\.router', r'navigate\('],
                "ui": [r'import\s+.*\b(react|vue|svelte)\b', r'<template', r'<style', r'usestate', r'useeffect', r'component', r'classname=', r'class=', r'@tailwind', r'tailwindcss', r'\.css', r'styled'],
                "messaging": [r'socket', r'websocket', r'\.emit', r'\.on\(', r'fetch\(', r'axios', r'\.post\(', r'\.get\(', r'messages\[', r'chat'],
                "state management": [r'usestate', r'usereducer', r'usecontext', r'redux', r'vuex', r'pinia', r'zustand', r'mobx', r'store'],
                "form handling": [r'<form', r'input', r'textarea', r'select', r'onsubmit', r'onchange', r'v-model', r'formik', r'react-hook-form'],
                "api calls": [r'fetch\(', r'axios', r'xmlhttprequest', r'usequery', r'swr', r'apiclient']
            }
            relevant_patterns = []
            if any(kw in req_lower for kw in ["routing", "multipage", "navigation", "route"]): relevant_patterns.extend(patterns["routing"])
            if any(kw in req_lower for kw in ["ui", "interface", "modern", "style", "component"]): relevant_patterns.extend(patterns["ui"])
            if any(kw in req_lower for kw in ["message", "chat", "real-time", "websocket", "socket"]): relevant_patterns.extend(patterns["messaging"])
            if any(kw in req_lower for kw in ["state", "context", "store", "reducer"]): relevant_patterns.extend(patterns["state management"])
            if any(kw in req_lower for kw in ["form", "input", "submit", "validation"]): relevant_patterns.extend(patterns["form handling"])
            if any(kw in req_lower for kw in ["api", "fetch", "data", "ajax", "request"]): relevant_patterns.extend(patterns["api calls"])

            for pattern in set(relevant_patterns): # Use set to avoid duplicate checks
                 if re.search(pattern, code_lower):
                      found_evidence.append(f"found pattern '{pattern}'")
                      result["met"] = True # Mark as met if any relevant pattern found


        # --- Backend Patterns ---
        else:
            patterns = {
                "routing": [r'@app\.route', r'@blueprint\.route', r'app\.get\(', r'app\.post\(', r'router\.', r'blueprint\(', r'urlpatterns', r'path\(', r'url_for\('],
                "database": [r'database', r'db\.', r'model\.', r'query\.', r'find_one', r'find_by', r'save\(', r'cursor\.', r'execute\(', r'collection\.', r'sql', r'alchemy', r'prisma', r'mongoose', r'mongo', r'postgres', r'mysql'],
                "messaging": [r'socket', r'emit\(', r'on\(', r'send\(', r'receive\(', r'message', r'chat', r'websocket', r'kafka', r'rabbitmq', r'celery', r'queue'],
                "auth": [r'authenticate', r'login', r'register', r'password', r'jwt', r'token', r'session', r'cookie', r'authlib', r'passport', r'bcrypt'],
                "api handling": [r'request', r'response', r'json', r'jsonify', r'rest', r'graphql', r'fastapi', r'flask', r'django', r'express']
            }
            relevant_patterns = []
            if any(kw in req_lower for kw in ["routing", "multipage", "endpoint", "route", "url"]): relevant_patterns.extend(patterns["routing"])
            if any(kw in req_lower for kw in ["database", "storage", "history", "persist", "model", "schema", "sql"]): relevant_patterns.extend(patterns["database"])
            if any(kw in req_lower for kw in ["message", "chat", "real-time", "websocket", "socket", "queue", "celery"]): relevant_patterns.extend(patterns["messaging"])
            if any(kw in req_lower for kw in ["auth", "login", "user", "password", "session", "jwt", "token"]): relevant_patterns.extend(patterns["auth"])
            if any(kw in req_lower for kw in ["api", "json", "request", "response", "rest"]): relevant_patterns.extend(patterns["api handling"])

            for pattern in set(relevant_patterns):
                 if re.search(pattern, code_lower):
                      found_evidence.append(f"found pattern '{pattern}'")
                      result["met"] = True

        # Update explanation and confidence
        if result["met"]:
            result["confidence"] = "MEDIUM" # Upgrade confidence if patterns found
            result["explanation"] += "Evidence: " + ", ".join(found_evidence) + "."
        else:
            result["explanation"] += " No matching code patterns found for the requirement."

        return result

    def analyze_code(self, requirement: str, code: str, is_frontend: bool = True, model: str = None) -> Dict[str, Any]:
        """
        Analyze code to determine if it meets a requirement.
        Enhanced with better error handling and smart code summarization.

        Args:
            requirement: The requirement to check
            code: The code to analyze
            is_frontend: Whether the code is frontend (True) or backend (False)
            model: Model to use for analysis, otherwise use best available

        Returns:
            Dict containing the analysis result
        """
        if not self.check_server():
            logger.error("GPT4All server is not available for analysis")
            # Use fallback immediately if server check fails
            return self._fallback_analyze_code(requirement, code, is_frontend)

        # Select model - ensure we have a string, not an object
        model_to_use = self._extract_model_id(model) if model else self.get_best_model()

        # Check if code is too large and summarize if necessary
        code_max_length = 8000  # Maximum safe size for the API
        summarized_note = ""
        if len(code) > code_max_length:
            original_len = len(code)
            code = self.summarize_code(code, code_max_length, is_frontend)
            summarized_note = f"\nNote: Due to size limitations, this code has been intelligently summarized from {original_len} to {len(code)} characters to preserve structure while reducing details."
            logger.info(f"Code summarized for analysis. Original: {original_len}, New: {len(code)}")

        # Create system prompt
        system_prompt = """You are an expert code reviewer. Analyze the provided code to determine if it satisfies the given requirement. Focus on concrete evidence. Respond ONLY with JSON containing 'met' (true/false), 'confidence' ('HIGH'/'MEDIUM'/'LOW'), and 'explanation' (brief evidence-based reason)."""

        # Create user prompt with code to analyze
        code_type = "Frontend" if is_frontend else "Backend"
        user_prompt = f"""Requirement: {requirement}
Code Type: {code_type}
{summarized_note}

Analyze if the following code meets the requirement:
```
{code}
```
Respond ONLY with the required JSON object."""

        # Try multiple models if first one fails
        available_models = self.available_models.copy() if self.available_models else [model_to_use]
        if model_to_use in available_models:
            available_models.remove(model_to_use)
            available_models.insert(0, model_to_use)

        max_attempts = min(2, len(available_models))
        last_error = None

        for attempt in range(max_attempts):
            current_model = available_models[attempt]
            try:
                if not current_model or not isinstance(current_model, str):
                    logger.warning(f"Invalid model identifier: {current_model}, skipping attempt.")
                    continue

                payload = {
                    "model": current_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 256 # Reduced max tokens for faster response & focus on JSON
                }

                logger.info(f"Attempt {attempt+1}/{max_attempts}: Sending analysis request to GPT4All API using model: {current_model}")
                response = requests.post(
                    f"{self.api_url}/chat/completions",
                    json=payload,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                    # Try to parse the response content as JSON
                    try:
                        # Clean potential markdown fences
                        if content.strip().startswith("```json"):
                             content = content.strip()[7:]
                        if content.strip().endswith("```"):
                             content = content.strip()[:-3]

                        result = json.loads(content.strip())
                        # Basic validation of expected fields
                        if 'met' in result and 'confidence' in result and 'explanation' in result:
                             logger.info(f"Analysis successful with model {current_model}. Met: {result.get('met')}")
                             return result
                        else:
                             logger.warning(f"Model {current_model} response missing required fields: {content}")
                             # Treat as invalid JSON and try fallback extraction
                             return self._extract_json_from_text(content)

                    except json.JSONDecodeError:
                        logger.warning(f"Model {current_model} response was not valid JSON: {content}")
                        # If response is not valid JSON, try to extract JSON from the content
                        return self._extract_json_from_text(content)
                else:
                    error_text = response.text[:500]
                    logger.error(f"GPT4All API request failed with model {current_model}: {response.status_code} - {error_text}")
                    last_error = f"API Error {response.status_code}"
                    # Try next model if available
                    if attempt < max_attempts - 1:
                        logger.info(f"Retrying with alternate model: {available_models[attempt+1]}")
                        continue
                    else: # Last attempt failed via API status code
                         logger.error("All API attempts failed.")
                         return self._fallback_analyze_code(requirement, code, is_frontend)

            except requests.exceptions.Timeout:
                 logger.error(f"Timeout error connecting to GPT4All API with model {current_model} after {self.timeout} seconds.")
                 last_error = "API Timeout"
                 if attempt < max_attempts - 1: continue
                 else: return self._fallback_analyze_code(requirement, code, is_frontend)
            except requests.exceptions.RequestException as e:
                 logger.error(f"Network error connecting to GPT4All API with model {current_model}: {e}")
                 last_error = "Network Error"
                 # Don't retry on network errors usually, use fallback immediately
                 return self._fallback_analyze_code(requirement, code, is_frontend)
            except Exception as e:
                logger.exception(f"Unexpected error analyzing code with model {current_model}: {e}")
                last_error = f"Unexpected Error: {e}"
                if attempt < max_attempts - 1: continue
                else: return self._fallback_analyze_code(requirement, code, is_frontend)

        # If loop finishes without returning (should only happen if max_attempts is 0 or errors occurred)
        logger.error(f"Analysis failed after {max_attempts} attempts. Last error: {last_error}")
        return self._fallback_analyze_code(requirement, code, is_frontend)


    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON data from text that might contain markdown or other formatting.

        Args:
            text: Text that might contain JSON

        Returns:
            Dict with extracted data or default values
        """
        logger.debug(f"Attempting to extract JSON from text: {text[:100]}...")
        # Try to find JSON in code blocks ```json ... ```
        json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', text, re.DOTALL | re.IGNORECASE)
        if json_match:
            try:
                extracted = json.loads(json_match.group(1))
                logger.info("Extracted JSON from markdown code block.")
                # Basic validation
                if 'met' in extracted and 'confidence' in extracted and 'explanation' in extracted:
                     return extracted
                else:
                     logger.warning("Extracted JSON missing required fields.")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to decode JSON from markdown block: {e}")

        # Try to find JSON with outer braces { ... }
        # Make this less greedy by looking for balanced braces if possible,
        # but a simple regex is often sufficient for LLM responses.
        json_match = re.search(r'({(?:[^{}]|{[^{}]*})*})', text) # Try to match balanced braces
        if json_match:
            try:
                extracted = json.loads(json_match.group(1))
                logger.info("Extracted JSON using brace matching.")
                if 'met' in extracted and 'confidence' in extracted and 'explanation' in extracted:
                     return extracted
                else:
                     logger.warning("Extracted JSON missing required fields.")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to decode JSON from brace matching: {e}")

        # If no valid JSON found, return a default error structure
        logger.warning("Could not extract valid JSON from LLM response.")
        return {
            "met": False,
            "confidence": "LOW",
            "explanation": f"Could not parse valid JSON response from LLM. Raw response: {text[:200]}...",
            "error": "Invalid JSON response from LLM"
        }

# =============================================================================
# Main Analyzer Class
# =============================================================================
class GPT4AllAnalyzer:
    """
    Analyzer that checks application code against requirements using GPT4All API.
    """

    # ** FIX: Added api_url to __init__ **
    def __init__(self, base_path: Union[Path, str] = None, api_url: Optional[str] = None):
        """
        Initialize the analyzer.

        Args:
            base_path: Base directory path for application code.
            api_url: The URL for the GPT4All API server (optional).
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        # Pass the api_url to the client constructor
        self.client = GPT4AllClient(api_url=api_url)
        self.requirements_cache = {}
        logger.info(f"GPT4All analyzer initialized (Base Path: {self.base_path}, API URL: {self.client.api_url})")

    def find_app_directory(self, model: str, app_num: int) -> Path:
        """
        Find the correct directory for a specific app.

        Args:
            model: Model name
            app_num: App number

        Returns:
            Path to the app directory
        """
        # Use self.base_path which is set during initialization
        # Adjust patterns based on your actual project structure relative to base_path
        patterns = [
            self.base_path / f"{model}/app{app_num}",
            self.base_path / f"{model.lower()}/app{app_num}",
            self.base_path / f"{model}/App{app_num}",
            # Add other potential locations relative to self.base_path if needed
        ]

        for pattern in patterns:
            if pattern.exists() and pattern.is_dir():
                logger.info(f"Found app directory: {pattern}")
                return pattern

        logger.warning(f"App directory not found for {model}/app{app_num}")
        logger.warning(f"Base path searched: {self.base_path}")
        logger.warning(f"Attempted patterns relative to base path: {[p.relative_to(self.base_path) if p.is_relative_to(self.base_path) else str(p) for p in patterns]}")

        # Return a default path (which likely won't exist, causing later errors)
        default_path = self.base_path / f"{model}/app{app_num}"
        logger.warning(f"Returning default (likely non-existent) path: {default_path}")
        return default_path


    def collect_code_files(self, directory: Path) -> Tuple[List[Path], List[Path]]:
        """
        Collect frontend and backend code files from the app directory.
        Specifically looks for frontend/ and backend/ subdirectories first.

        Args:
            directory: App directory

        Returns:
            Tuple of (frontend_files, backend_files)
        """
        frontend_files = []
        backend_files = []
        visited_dirs = set() # To handle potential symlink loops

        skip_dirs = {
            'node_modules', '.git', '__pycache__', 'venv', 'env',
            'dist', 'build', '.next', 'static', 'assets', 'out',
            'coverage', 'logs', 'tmp', 'temp', '.venv' # Added .venv
        }

        frontend_exts = ('.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.vue',
                         '.svelte', '.json', '.less', '.scss', '.sass', '.xml',
                         '.mjs', '.cjs', '.esm.js')
        backend_exts = ('.py', '.flask', '.wsgi', '.django', '.rb', '.java', '.go', '.php') # Added more backend types

        if not directory.exists() or not directory.is_dir():
            logger.warning(f"Directory does not exist or is not a directory: {directory}")
            return [], []

        # Key files to prioritize within their respective areas
        key_frontend_files = {'App.jsx', 'App.js', 'index.js', 'main.js', 'app.jsx',
                              'app.js', 'index.jsx', 'index.tsx', 'App.svelte', 'App.vue', 'index.html'}
        key_backend_files = {'app.py', 'server.py', 'main.py', 'api.py', 'flask_app.py',
                             'django_app.py', 'routes.py', 'views.py', 'models.py', 'controllers.py'}

        all_frontend_files = []
        all_backend_files = []
        processed_whole_dir = False

        # --- Strategy 1: Look for frontend/ and backend/ subdirs ---
        frontend_dir = directory / "frontend"
        backend_dir = directory / "backend"
        found_specific_dirs = False

        if frontend_dir.is_dir():
            logger.info(f"Processing specific frontend directory: {frontend_dir}")
            found_specific_dirs = True
            for root, dirs, files in os.walk(frontend_dir, topdown=True):
                dirs[:] = [d for d in dirs if d not in skip_dirs] # Prune skipped dirs
                current_path = Path(root)
                if current_path in visited_dirs: continue
                visited_dirs.add(current_path)
                for file_name in files:
                    if file_name.endswith(frontend_exts):
                         all_frontend_files.append(current_path / file_name)

        if backend_dir.is_dir():
            logger.info(f"Processing specific backend directory: {backend_dir}")
            found_specific_dirs = True
            for root, dirs, files in os.walk(backend_dir, topdown=True):
                dirs[:] = [d for d in dirs if d not in skip_dirs]
                current_path = Path(root)
                if current_path in visited_dirs: continue
                visited_dirs.add(current_path)
                for file_name in files:
                    if file_name.endswith(backend_exts):
                         all_backend_files.append(current_path / file_name)

        # --- Strategy 2: Scan whole directory if specific dirs not found/empty ---
        if not found_specific_dirs or (not all_frontend_files and not all_backend_files):
            if not found_specific_dirs:
                 logger.info(f"No specific frontend/ or backend/ dirs found. Scanning entire directory: {directory}")
            else:
                 logger.info(f"Specific frontend/backend dirs were empty. Scanning entire directory: {directory}")

            processed_whole_dir = True
            for root, dirs, files in os.walk(directory, topdown=True):
                dirs[:] = [d for d in dirs if d not in skip_dirs]
                current_path = Path(root)
                # Avoid rescanning frontend/backend if they were processed above but empty
                if current_path == frontend_dir or current_path == backend_dir: continue
                if current_path in visited_dirs: continue
                visited_dirs.add(current_path)

                for file_name in files:
                    file_path = current_path / file_name
                    # Check size before adding
                    try:
                         if file_path.stat().st_size > 300 * 1024: continue # Skip large files
                    except (OSError, PermissionError): continue

                    if file_name.endswith(frontend_exts):
                        if file_path not in all_frontend_files: all_frontend_files.append(file_path)
                    elif file_name.endswith(backend_exts):
                        if file_path not in all_backend_files: all_backend_files.append(file_path)


        # --- Prioritize and Limit Files ---
        def prioritize_and_limit(all_files: List[Path], key_files: Set[str], limit: int = 10) -> List[Path]:
            prioritized = []
            # Add key files first
            for f in all_files:
                if f.name in key_files:
                    prioritized.append(f)
            # Add remaining files until limit, ensuring no duplicates
            remaining = [f for f in all_files if f not in prioritized]
            needed = limit - len(prioritized)
            if needed > 0:
                 prioritized.extend(remaining[:needed])
            return prioritized[:limit] # Ensure limit is strictly enforced

        frontend_files = prioritize_and_limit(all_frontend_files, key_frontend_files)
        backend_files = prioritize_and_limit(all_backend_files, key_backend_files)

        logger.info(f"Selected {len(frontend_files)} frontend files and {len(backend_files)} backend files for analysis.")
        logger.debug(f"Selected Frontend: {[f.name for f in frontend_files]}")
        logger.debug(f"Selected Backend: {[f.name for f in backend_files]}")

        return frontend_files, backend_files


    def read_code_from_files(self, files: List[Path], max_chars: int = 12000) -> str:
        """
        Read and combine code from files with length limit.

        Args:
            files: List of file paths
            max_chars: Maximum characters to read

        Returns:
            Combined code as string
        """
        if not files: return ""

        combined_code_parts = []
        total_chars = 0
        files_included_count = 0

        for file_path in files:
            try:
                # Check size before reading - avoid reading huge files unnecessarily
                file_size = file_path.stat().st_size
                if file_size == 0: continue # Skip empty files
                if file_size > max_chars * 2: # Heuristic: skip if file is much larger than total limit
                     logger.warning(f"Skipping large file {file_path.name} ({file_size} bytes)")
                     continue

                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    code = f.read()

                if not code.strip(): continue # Skip files with only whitespace

                # Add file header
                file_header = f"\n\n--- File: {file_path.name} ---\n"
                header_len = len(file_header)

                # Check if adding header and *some* code exceeds limit
                if total_chars + header_len + 50 > max_chars: # 50 chars buffer for code snippet
                    logger.info(f"Stopping code reading; limit ({max_chars} chars) reached.")
                    break # Stop adding more files

                combined_code_parts.append(file_header)
                total_chars += header_len

                # Calculate remaining space for code content
                remaining_space = max_chars - total_chars
                if len(code) <= remaining_space:
                    combined_code_parts.append(code)
                    total_chars += len(code)
                else:
                    # Add truncated code
                    truncated_code = code[:remaining_space - 20] + "\n...[TRUNCATED]" # Ensure space for note
                    combined_code_parts.append(truncated_code)
                    total_chars += len(truncated_code)
                    logger.warning(f"Truncated file {file_path.name} to fit within limit.")
                    files_included_count += 1
                    break # Stop after truncating one file

                files_included_count += 1

            except FileNotFoundError:
                 logger.error(f"File not found during reading: {file_path}")
            except PermissionError:
                 logger.error(f"Permission denied reading file: {file_path}")
            except OSError as e:
                 logger.error(f"OS error reading file {file_path}: {e}")
            except Exception as e:
                logger.exception(f"Unexpected error reading file {file_path}: {e}")

        logger.info(f"Included content from {files_included_count} files (total {total_chars} chars)")
        return "".join(combined_code_parts)


    def get_requirements_for_app(self, app_num: int) -> Tuple[List[str], str]:
        """
        Get requirements for a specific app from requirements.json file.
        Handles various JSON formats flexibly.

        Args:
            app_num: App number (1-based)

        Returns:
            Tuple of (requirements_list, template_name)
        """
        # Use cache if available
        if app_num in self.requirements_cache:
            logger.debug(f"Using cached requirements for app {app_num}")
            return self.requirements_cache[app_num]

        # Look for requirements.json relative to the base_path
        requirements_file = self.base_path.parent / "requirements.json" # Assumes it's one level up
        logger.info(f"Attempting to load requirements from: {requirements_file}")

        found_requirements = []
        template_name = f"App {app_num}" # Default name

        if requirements_file.exists():
            try:
                with open(requirements_file, 'r', encoding='utf-8') as f:
                    app_data = json.load(f)
                logger.info(f"Successfully loaded requirements file: {requirements_file}")

                # --- Flexible Requirement Extraction Logic ---
                app_key_str = f"app_{app_num}"
                app_num_str = str(app_num)

                target_app_info = None

                # 1. Check 'applications' list (most common structure)
                if isinstance(app_data.get("applications"), list):
                    for app in app_data["applications"]:
                        if isinstance(app, dict):
                             # Match by 'id' (string or int) or 'app_num'
                             app_id = app.get("id")
                             app_number_field = app.get("app_num")
                             if str(app_id) == app_key_str or str(app_id) == app_num_str or str(app_number_field) == app_num_str :
                                  target_app_info = app
                                  logger.debug(f"Found app {app_num} in 'applications' list.")
                                  break

                # 2. Check if root is a dict keyed by app_id (e.g., "app_1": {...})
                elif isinstance(app_data, dict) and app_key_str in app_data:
                    target_app_info = app_data[app_key_str]
                    logger.debug(f"Found app {app_num} as key '{app_key_str}'.")

                # 3. Check if root is a dict keyed by app number string (e.g., "1": {...})
                elif isinstance(app_data, dict) and app_num_str in app_data:
                    target_app_info = app_data[app_num_str]
                    logger.debug(f"Found app {app_num} as key '{app_num_str}'.")

                # --- Extract Requirements from Found App Info ---
                if isinstance(target_app_info, dict):
                    template_name = target_app_info.get("name", template_name)
                    # Prioritize specific_features, then requirements, then general_features
                    if isinstance(target_app_info.get("specific_features"), list):
                        found_requirements.extend(target_app_info["specific_features"])
                    if isinstance(target_app_info.get("requirements"), list):
                         # Avoid duplicates if keys overlap
                         for req in target_app_info["requirements"]:
                              if req not in found_requirements: found_requirements.append(req)
                    if isinstance(target_app_info.get("general_features"), list):
                         for req in target_app_info["general_features"]:
                              if req not in found_requirements: found_requirements.append(req)
                    logger.info(f"Extracted {len(found_requirements)} requirements for '{template_name}'")

                # 4. Check if the root JSON is just a flat list of requirements (less common)
                elif isinstance(app_data, list) and not target_app_info:
                    logger.warning("requirements.json is a flat list. Assuming these are global requirements.")
                    found_requirements = [str(item) for item in app_data if isinstance(item, str)]

            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from {requirements_file}: {e}")
            except Exception as e:
                logger.exception(f"Error processing requirements file {requirements_file}: {e}")

        # --- Fallback if no requirements found in file ---
        if not found_requirements:
            logger.warning(f"No specific requirements found for app {app_num} in {requirements_file}. Using defaults.")
            # Provide some basic default requirements
            found_requirements = [
                "The application should have a clear user interface.",
                "Backend should handle requests appropriately.",
                "Frontend should display data fetched from the backend.",
                # Add more generic defaults if needed
            ]
            template_name = f"App {app_num} (Default Reqs)"


        # Cache and return
        self.requirements_cache[app_num] = (found_requirements, template_name)
        return found_requirements, template_name


    def load_application_data(self) -> Dict:
        """
        Load application data from JSON file. (Potentially deprecated if requirements.json is primary)

        Returns:
            Dictionary with application data
        """
        # This might be less relevant if requirements.json is the main source
        logger.warning("load_application_data called - consider using get_requirements_for_app primarily.")
        possible_paths = [
            self.base_path.parent / "applications.json", # One level up from base_path
            self.base_path / "applications.json",
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

        logger.warning("applications.json not found in standard locations.")
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
        # Check if GPT4All server is available first
        if not self.client.check_server():
            error_msg = "GPT4All server is not available"
            logger.error(error_msg)
            reqs_to_check = requirements or ["Server unavailable check"]
            return self._create_error_checks(reqs_to_check, error_msg)

        # Find app directory
        directory = self.find_app_directory(model, app_num)
        if not directory.exists() or not directory.is_dir():
            error_msg = f"App directory not found: {directory}"
            logger.error(error_msg)
            reqs_to_check = requirements or ["Directory not found check"]
            return self._create_error_checks(reqs_to_check, error_msg)

        # Get requirements if not provided
        if not requirements:
            requirements, _ = self.get_requirements_for_app(app_num)
            if not requirements: # Handle case where even defaults failed
                 error_msg = f"Could not load any requirements for app {app_num}"
                 logger.error(error_msg)
                 return self._create_error_checks([f"Requirement loading failed for app {app_num}"], error_msg)


        # Collect code files
        frontend_files, backend_files = self.collect_code_files(directory)

        # Read code (limit size)
        # Consider different limits for FE/BE if needed
        frontend_code = self.read_code_from_files(frontend_files, max_chars=10000)
        backend_code = self.read_code_from_files(backend_files, max_chars=10000)

        if not frontend_code and not backend_code:
            error_msg = f"No readable code files found in {directory}"
            logger.error(error_msg)
            return self._create_error_checks(requirements, error_msg)

        # Check each requirement
        results = []
        logger.info(f"Starting requirement checks for {model}/app{app_num} ({len(requirements)} requirements)")
        for i, req in enumerate(requirements):
            check = RequirementCheck(requirement=req)
            result = RequirementResult() # Combined result for this requirement

            logger.debug(f"Checking requirement {i+1}/{len(requirements)}: '{req}'")

            # Analyze frontend code if present
            fe_analysis = None
            if frontend_code:
                fe_analysis = self.client.analyze_code(req, frontend_code, is_frontend=True)
                result.frontend_analysis = fe_analysis # Store detailed FE analysis
            else:
                 result.frontend_analysis = {"met": False, "confidence": "N/A", "explanation": "No frontend code provided."}


            # Analyze backend code if present
            be_analysis = None
            if backend_code:
                be_analysis = self.client.analyze_code(req, backend_code, is_frontend=False)
                result.backend_analysis = be_analysis # Store detailed BE analysis
            else:
                 result.backend_analysis = {"met": False, "confidence": "N/A", "explanation": "No backend code provided."}


            # --- Combine Results ---
            fe_met = fe_analysis.get("met", False) if fe_analysis else False
            be_met = be_analysis.get("met", False) if be_analysis else False
            result.met = fe_met or be_met # Met if either FE or BE meets it

            # Confidence: Use the higher confidence level if met, otherwise lowest
            fe_conf = fe_analysis.get("confidence", "LOW") if fe_analysis else "LOW"
            be_conf = be_analysis.get("confidence", "LOW") if be_analysis else "LOW"
            conf_map = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "N/A": 0}

            if result.met:
                 # If met, take the confidence of the part that met it (or higher if both met)
                 if fe_met and be_met:
                      result.confidence = max([fe_conf, be_conf], key=lambda c: conf_map.get(c, 0))
                 elif fe_met:
                      result.confidence = fe_conf
                 else: # be_met must be true
                      result.confidence = be_conf
            else:
                 # If not met, confidence is LOW unless there was an error
                 result.confidence = "LOW"


            # Explanation: Combine explanations, prioritizing the 'met' part if applicable
            fe_expl = result.frontend_analysis.get("explanation", "FE Analysis N/A")
            be_expl = result.backend_analysis.get("explanation", "BE Analysis N/A")

            if result.met:
                 if fe_met and be_met: result.explanation = f"FE: {fe_expl}\nBE: {be_expl}"
                 elif fe_met: result.explanation = f"FE: {fe_expl}"
                 else: result.explanation = f"BE: {be_expl}"
            else: # Not met, combine both explanations
                 result.explanation = f"FE: {fe_expl}\nBE: {be_expl}"


            # Error: Report error if either analysis had one
            fe_err = fe_analysis.get("error") if fe_analysis else None
            be_err = be_analysis.get("error") if be_analysis else None
            if fe_err and be_err: result.error = f"FE Error: {fe_err}; BE Error: {be_err}"
            elif fe_err: result.error = f"FE Error: {fe_err}"
            elif be_err: result.error = f"BE Error: {be_err}"


            check.result = result
            results.append(check)

        logger.info(f"Completed requirement checks for {model}/app{app_num}: {len(results)} requirements processed.")
        return results


    def _create_error_checks(self, requirements: List[str], error_message: str) -> List[RequirementCheck]:
        """
        Create error checks for all requirements when analysis cannot proceed.

        Args:
            requirements: List of requirements that were intended to be checked.
            error_message: Error message to include in each check result.

        Returns:
            List of RequirementCheck objects with errors.
        """
        logger.debug(f"Creating error checks for {len(requirements)} requirements due to error: {error_message}")
        return [
            RequirementCheck(
                requirement=req,
                result=RequirementResult(
                    met=False,
                    confidence="N/A", # Indicate analysis didn't run
                    explanation="Analysis could not be performed.",
                    error=error_message
                )
            )
            for req in requirements
        ]


# =============================================================================
# Fix for Logging Issues (Keep as is)
# =============================================================================
def apply_logging_fixes():
    """
    Apply fixes to existing loggers to avoid request_id KeyError.
    Call this function early in your application startup.
    """
    import logging

    class FixedContextFilter(logging.Filter):
        """Add contextual information to log records."""

        def __init__(self, app_name: str = "app"):
            super().__init__()
            self.app_name = app_name

        def filter(self, record):
            # Always add request_id field to avoid KeyError
            if not hasattr(record, 'request_id'):
                try:
                    from flask import g, has_request_context, has_app_context
                    if has_app_context() and has_request_context():
                        record.request_id = getattr(g, 'request_id', '-')
                    else:
                        record.request_id = '-'
                except (RuntimeError, ImportError):
                    record.request_id = '-' # Not in Flask context or Flask not available

            # Add component information if not present
            if not hasattr(record, 'component'):
                if record.name and record.name.find('.') > 0:
                    record.component = record.name.split('.')[0]
                else:
                    record.component = self.app_name

            return True

    # Get the root logger
    root_logger = logging.getLogger()

    # Add our fixed ContextFilter to the root logger if not already present
    filter_name = 'fixed_context_filter'
    if not any(isinstance(f, FixedContextFilter) and f.name == filter_name for f in root_logger.filters):
         context_filter = FixedContextFilter()
         context_filter.name = filter_name # Give it a name to check for existence
         root_logger.addFilter(context_filter)
         logger.debug("Added FixedContextFilter to root logger.")

         # Also fix specific loggers that might be configured separately
         for logger_name in ['werkzeug', 'requests', 'errors', 'gpt4all']: # Add other relevant loggers
             specific_logger = logging.getLogger(logger_name)
             if not any(isinstance(f, FixedContextFilter) and f.name == filter_name for f in specific_logger.filters):
                  specific_logger.addFilter(context_filter)
                  logger.debug(f"Added FixedContextFilter to logger: {logger_name}")


         # Fix handlers as well (to ensure the filter is applied to all output)
         for handler in root_logger.handlers:
              if not any(isinstance(f, FixedContextFilter) and f.name == filter_name for f in handler.filters):
                   handler.addFilter(context_filter)
                   logger.debug(f"Added FixedContextFilter to handler: {handler}")

         logger.info("Applied logging fixes to avoid request_id KeyError")
    else:
         logger.debug("Logging fixes already applied.")


# Apply logging fixes when the module is imported
try:
    apply_logging_fixes()
except Exception as e:
    logger.warning(f"Could not apply logging fixes: {e}")

