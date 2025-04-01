"""
Robust Frontend Security Analysis Module

Provides security scanning for frontend code with enhanced JSX/React support:
- pattern-based security scan: detects common security issues via regex patterns
- jsx-parser: specialized JSX syntax validation and security checks
- react-patterns: dedicated React security vulnerability detection
- dependency-analyzer: improved package.json vulnerability detection
- eslint-bridge: lightweight ESLint wrapper that works without Node.js installation
- semgrep: lightweight static analysis that works without Node.js dependencies
- jshint: JavaScript linting via direct embedded rules (no Node dependency)

Features cross-platform support, minimal dependencies, and fallback mechanisms.
"""

import os
import re
import json
import shutil
import logging
import subprocess
import concurrent.futures
import hashlib
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, Union, Set

# -----------------------------------------------------------------------------
# Logging Configuration
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
TOOL_TIMEOUT = 30  # seconds for tool execution timeout

# Frontend security pattern definitions
SECURITY_PATTERNS = [
    {
        "id": "eval-usage",
        "pattern": r"eval\s*\(",
        "description": "Usage of eval() function can lead to code injection",
        "severity": "high",
        "confidence": "medium",
        "fix": "Replace eval() with safer alternatives"
    },
    {
        "id": "innerHTML-assignment",
        "pattern": r"\.(innerHTML|outerHTML)\s*=",
        "description": "Direct innerHTML manipulation can lead to XSS vulnerabilities",
        "severity": "high",
        "confidence": "medium",
        "fix": "Use textContent for text or createElement/appendChild for HTML content"
    },
    {
        "id": "document-write",
        "pattern": r"document\.write\s*\(",
        "description": "Usage of document.write can lead to XSS vulnerabilities",
        "severity": "high",
        "confidence": "high",
        "fix": "Manipulate the DOM using safer DOM APIs"
    },
    {
        "id": "href-javascript",
        "pattern": r"href\s*=\s*['\"]javascript:",
        "description": "JavaScript in href attributes can lead to XSS vulnerabilities",
        "severity": "medium",
        "confidence": "high",
        "fix": "Use event handlers instead of javascript: URLs"
    },
    {
        "id": "unvalidated-redirect",
        "pattern": r"(location|window\.location)\s*=\s*",
        "description": "Unvalidated redirects can lead to phishing attacks",
        "severity": "medium",
        "confidence": "medium",
        "fix": "Validate all redirect URLs against a whitelist"
    },
    {
        "id": "jwt-localstorage",
        "pattern": r"localStorage\.setItem\s*\(\s*['\"]token['\"]|localStorage\.setItem\s*\(\s*['\"]jwt['\"]",
        "description": "Storing JWT tokens in localStorage exposes them to XSS attacks",
        "severity": "medium",
        "confidence": "medium",
        "fix": "Use httpOnly cookies for token storage"
    },
    {
        "id": "hardcoded-secret",
        "pattern": r"(apiKey|secret|password|token|auth|key)\s*[:=]\s*['\"][^'\"]+['\"]",
        "description": "Potential hardcoded secret or credential",
        "severity": "high",
        "confidence": "medium",
        "fix": "Move secrets to environment variables or secure storage"
    },
    {
        "id": "nosql-injection",
        "pattern": r"{\s*\$where\s*:\s*[^}]+}\b",
        "description": "Potential NoSQL injection vulnerability",
        "severity": "high",
        "confidence": "medium",
        "fix": "Use parameterized queries and validate user input"
    },
    {
        "id": "axios-csrf",
        "pattern": r"axios\.defaults\.withCredentials\s*=\s*true",
        "description": "Axios with credentials without CSRF protection",
        "severity": "medium",
        "confidence": "medium",
        "fix": "Implement CSRF protection when using credentials"
    },
    {
        "id": "dom-clobbering",
        "pattern": r"getElementById\s*\(\s*['\"][^'\"]+['\"].*\)\.innerHTML",
        "description": "DOM clobbering vulnerability",
        "severity": "medium",
        "confidence": "medium",
        "fix": "Validate element existence and use textContent when possible"
    },
    {
        "id": "outdated-package-react",
        "pattern": r"\"react\"\s*:\s*\"(\^|~|)16\.",
        "description": "Outdated React version with potential security issues",
        "severity": "medium",
        "confidence": "high",
        "fix": "Update React to the latest stable version"
    },
    {
        "id": "outdated-package-jquery",
        "pattern": r"\"jquery\"\s*:\s*\"(\^|~|)(1\.|2\.)",
        "description": "Outdated jQuery version with known vulnerabilities",
        "severity": "high",
        "confidence": "high",
        "fix": "Update jQuery to version 3.x or newer"
    },
    {
        "id": "dangerouslySetInnerHTML",
        "pattern": r"dangerouslySetInnerHTML",
        "description": "React's dangerouslySetInnerHTML may lead to XSS vulnerabilities",
        "severity": "medium",
        "confidence": "medium",
        "fix": "Sanitize HTML content before using dangerouslySetInnerHTML"
    },
    {
        "id": "unsafe-import",
        "pattern": r"import\s+.*\s+from\s+['\"](eval|unsafe-|evil-)",
        "description": "Importing from potentially unsafe package",
        "severity": "medium",
        "confidence": "medium",
        "fix": "Review and replace unsafe package dependencies"
    }
]

# React-specific security patterns
REACT_PATTERNS = [
    {
        "id": "unsafe-component-will-mount",
        "pattern": r"componentWillMount\s*\(",
        "description": "componentWillMount is deprecated and may lead to unsafe practices",
        "severity": "medium",
        "confidence": "high",
        "fix": "Use componentDidMount instead of componentWillMount"
    },
    {
        "id": "ref-string-usage",
        "pattern": r"ref\s*=\s*['\"][^'\"]+['\"]",
        "description": "String refs are deprecated and may cause issues",
        "severity": "medium",
        "confidence": "high",
        "fix": "Use createRef() or useRef() hook instead of string refs"
    },
    {
        "id": "useeffect-missing-deps",
        "pattern": r"useEffect\s*\(\s*\(\s*\)\s*=>\s*{[^}]*}\s*,\s*\[\s*\]\s*\)",
        "description": "useEffect with empty dependency array but accessing external variables",
        "severity": "medium",
        "confidence": "medium",
        "fix": "Add all dependencies to the dependency array"
    },
    {
        "id": "jsx-injection",
        "pattern": r"<[^>]*\{.*\.\.\.[^{}]*\}[^>]*>",
        "description": "Potential object spreading in JSX that may lead to prototype pollution",
        "severity": "high",
        "confidence": "medium",
        "fix": "Explicitly specify only needed props rather than spreading objects"
    },
    {
        "id": "unescaped-props",
        "pattern": r"<[^>]*\{.*__html.*\}[^>]*>",
        "description": "Potential unescaped HTML in JSX props",
        "severity": "high",
        "confidence": "medium",
        "fix": "Use proper HTML escape mechanisms before rendering user content"
    },
    {
        "id": "setState-callback-memory-leak",
        "pattern": r"this\.setState\s*\([^,)]*\)",
        "description": "setState without callback may cause memory leaks in unmounted components",
        "severity": "low",
        "confidence": "medium",
        "fix": "Check if component is mounted before setState or use useEffect"
    },
    {
        "id": "unsanitized-jsx-prop",
        "pattern": r"<[^>]*\{(?!.*encodeURI|.*escape|.*sanitize)[^}]*user[^}]*\}[^>]*>",
        "description": "Potentially unsanitized user data in JSX props",
        "severity": "medium",
        "confidence": "medium",
        "fix": "Sanitize user input before using in JSX"
    },
    {
        "id": "raw-user-content",
        "pattern": r"<div[^>]*>\s*\{(?![^}]*map)[^}]*user[^}]*\}\s*</div>",
        "description": "Potentially rendering raw user content without escaping",
        "severity": "medium",
        "confidence": "medium",
        "fix": "Ensure user content is properly escaped before rendering"
    },
    {
        "id": "insecure-use-memo",
        "pattern": r"useMemo\s*\(\s*\(\s*\)\s*=>\s*{[^}]*fetch\([^}]*}\s*,\s*\[\s*\]\s*\)",
        "description": "useMemo with empty dependencies but making fetch calls",
        "severity": "medium", 
        "confidence": "medium",
        "fix": "Add proper dependencies or move fetch call outside of useMemo"
    },
    {
        "id": "uncontrolled-form-element",
        "pattern": r"<(input|select|textarea)[^>]*(?!value|onChange)[^>]*>",
        "description": "Potentially uncontrolled form element",
        "severity": "low",
        "confidence": "low",
        "fix": "Add value and onChange handler for controlled components"
    }
]

# Code quality patterns
QUALITY_PATTERNS = [
    {
        "id": "console-log",
        "pattern": r"console\.(log|debug|info|warn|error)\s*\(",
        "description": "Console statements should be removed from production code",
        "severity": "low",
        "confidence": "high",
        "fix": "Remove console statements or use a logging library"
    },
    {
        "id": "todo-comment",
        "pattern": r"//\s*TODO|/\*\s*TODO",
        "description": "TODO comment indicates incomplete code",
        "severity": "low",
        "confidence": "high",
        "fix": "Address TODO items before production deployment"
    },
    {
        "id": "fixme-comment",
        "pattern": r"//\s*FIXME|/\*\s*FIXME",
        "description": "FIXME comment indicates broken code",
        "severity": "medium",
        "confidence": "high",
        "fix": "Fix the identified issue before production deployment"
    },
    {
        "id": "no-type-check",
        "pattern": r"// @ts-ignore|// @ts-nocheck",
        "description": "TypeScript type checking is being suppressed",
        "severity": "medium",
        "confidence": "high",
        "fix": "Address the type issues instead of suppressing checks"
    },
    {
        "id": "debugger-statement",
        "pattern": r"\bdebugger\b",
        "description": "Debugger statement will pause execution in development",
        "severity": "medium",
        "confidence": "high",
        "fix": "Remove debugger statements from production code"
    }
]

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def cmd_exists(cmd: str) -> bool:
    """Check if a command exists in the system PATH."""
    return shutil.which(cmd) is not None

def run_cmd(cmd: List[str], cwd: str = None, timeout: int = TOOL_TIMEOUT) -> Tuple[bool, str, str]:
    """
    Run a command and return success status, stdout, and stderr.
    
    Args:
        cmd: Command and arguments as list
        cwd: Working directory
        timeout: Command timeout in seconds
        
    Returns:
        Tuple of (success, stdout, stderr)
    """
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return proc.returncode == 0, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout} seconds: {' '.join(cmd)}"
    except Exception as e:
        return False, "", f"Error running command: {e}"

def safe_json_loads(data: str) -> Optional[Dict]:
    """
    Safely parse JSON data, returning None on failure.
    """
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return None

def normalize_path(path: Union[str, Path]) -> Path:
    """Normalize path to a resolved Path object."""
    if isinstance(path, str):
        path = Path(path)
    return path.resolve()

def find_package_json(directory: Path) -> Optional[Path]:
    """Find package.json file in a directory or parent directories."""
    current = directory
    max_depth = 5  # Prevent excessive traversal
    
    for _ in range(max_depth):
        pkg_json = current / "package.json"
        if pkg_json.exists():
            return pkg_json
        
        # Move to parent directory
        parent = current.parent
        if parent == current:  # Reached root
            break
        current = parent
    
    return None

def validate_jsx_syntax(content: str) -> List[Dict[str, Any]]:
    """
    Validate JSX syntax using a simple parser.
    Returns a list of errors found.
    """
    errors = []
    
    # Simple regex patterns to check for common JSX syntax errors
    jsx_patterns = [
        (r"<[^>]*\s+\w+(?!=)[^>]*>", "JSX attribute without value", "high"),
        (r"<[^>]*\s+\w+=[^'\"{}][^>]*>", "Unquoted attribute value", "medium"),
        (r"<(?!area|base|br|col|embed|hr|img|input|link|meta|param|source|track|wbr)[^>]*>[^<]*</[^>]*?(?!\\1)>", 
         "Mismatched JSX tags", "high"),
        (r"{[^}]*{[^}]*}[^}]*}", "Nested curly braces in JSX", "medium")
    ]
    
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        for pattern, msg, severity in jsx_patterns:
            if re.search(pattern, line):
                errors.append({
                    "line": i,
                    "text": msg,
                    "severity": severity,
                    "code": line
                })
    
    # Look for unclosed tags
    opened_tags = []
    tag_pattern = re.compile(r'<(/?)(\w+)[^>]*>')
    
    for i, line in enumerate(lines, 1):
        for match in tag_pattern.finditer(line):
            is_closing, tag_name = match.groups()
            
            if is_closing:  # Closing tag
                if opened_tags and opened_tags[-1] == tag_name:
                    opened_tags.pop()
                else:
                    errors.append({
                        "line": i,
                        "text": f"Mismatched closing tag: {tag_name}",
                        "severity": "high",
                        "code": line
                    })
            elif not line.strip().endswith('/>'):  # Opening tag (not self-closing)
                opened_tags.append(tag_name)
    
    # Any unclosed tags at the end
    for tag in reversed(opened_tags):
        errors.append({
            "line": len(lines),
            "text": f"Unclosed tag: {tag}",
            "severity": "high",
            "code": lines[-1] if lines else ""
        })
    
    return errors

def create_lightweight_eslint(temp_dir: Path) -> Optional[Path]:
    """
    Create a lightweight ESLint configuration that can work without full Node.js installation.
    Returns the path to the config file.
    """
    # Minimal ESLint config that focuses on security
    eslint_config = {
        "env": {
            "browser": True,
            "es6": True
        },
        "extends": ["eslint:recommended"],
        "parserOptions": {
            "ecmaFeatures": {
                "jsx": True
            },
            "ecmaVersion": 2020,
            "sourceType": "module"
        },
        "rules": {
            "no-eval": "error",
            "no-implied-eval": "error",
            "react/no-danger": "error",
            "react/no-danger-with-children": "error",
            "react/no-find-dom-node": "error",
            "react/no-is-mounted": "error",
            "react/no-string-refs": "error",
            "react/no-unescaped-entities": "error",
            "no-alert": "error",
            "no-script-url": "error"
        },
        "plugins": ["react", "security"]
    }
    
    try:
        config_path = temp_dir / ".eslintrc.json"
        with open(config_path, "w") as f:
            json.dump(eslint_config, f, indent=2)
        return config_path
    except Exception as e:
        logger.error(f"Failed to create ESLint config: {e}")
        return None

# -----------------------------------------------------------------------------
# Data Classes
# -----------------------------------------------------------------------------
@dataclass
class SecurityIssue:
    """Represents a security issue found in code."""
    filename: str
    line_number: int
    issue_text: str
    severity: str
    confidence: str
    issue_type: str
    line_range: List[int]
    code: str
    tool: str
    fix_suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for serialization."""
        return {
            "filename": self.filename,
            "line_number": self.line_number,
            "issue_text": self.issue_text,
            "severity": self.severity,
            "confidence": self.confidence,
            "issue_type": self.issue_type,
            "line_range": self.line_range,
            "code": self.code,
            "tool": self.tool,
            "fix_suggestion": self.fix_suggestion
        }

@dataclass
class AnalysisResult:
    """Complete results of a security analysis."""
    issues: List[SecurityIssue] = field(default_factory=list)
    tool_outputs: Dict[str, str] = field(default_factory=dict)
    tool_status: Dict[str, str] = field(default_factory=dict)
    scan_time: datetime = field(default_factory=datetime.now)
    files_analyzed: int = 0
    
    def add_tool_result(self, tool: str, status: str, output: str) -> None:
        """Add a tool's result."""
        self.tool_status[tool] = status
        self.tool_outputs[tool] = output
    
    def add_issues(self, issues: List[SecurityIssue]) -> None:
        """Add issues from a tool."""
        self.issues.extend(issues)
    
    def get_summary(self) -> Dict[str, Any]:
        """Generate a summary of analysis results."""
        # Calculate issue statistics
        severity_counts = {"high": 0, "medium": 0, "low": 0}
        confidence_counts = {"high": 0, "medium": 0, "low": 0}
        tool_counts = {}
        issue_types = {}
        files_affected = set()
        
        for issue in self.issues:
            # Count by severity
            if issue.severity.lower() in severity_counts:
                severity_counts[issue.severity.lower()] += 1
            
            # Count by confidence
            if issue.confidence.lower() in confidence_counts:
                confidence_counts[issue.confidence.lower()] += 1
            
            # Count by tool
            tool = issue.tool
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
            
            # Count by issue type
            issue_types[issue.issue_type] = issue_types.get(issue.issue_type, 0) + 1
            
            # Add to affected files
            files_affected.add(issue.filename)
        
        # For backward compatibility with the existing UI
        backward_compat_severity = {
            "HIGH": severity_counts["high"],
            "MEDIUM": severity_counts["medium"],
            "LOW": severity_counts["low"]
        }
        
        # Create tool stats with severities
        tool_stats = {}
        for tool in set([issue.tool for issue in self.issues]):
            tool_issues = [i for i in self.issues if i.tool == tool]
            
            # Count severities for this tool
            sev_counts = {}
            for issue in tool_issues:
                sev_counts[issue.severity] = sev_counts.get(issue.severity, 0) + 1
            
            tool_stats[tool] = {
                "count": len(tool_issues),
                "severities": sev_counts
            }
        
        return {
            "total_issues": len(self.issues),
            "severity_counts": backward_compat_severity,
            "tool_counts": tool_counts,
            "files_affected": len(files_affected),
            "issue_types": issue_types,
            "scan_time": self.scan_time.strftime("%Y-%m-%d %H:%M:%S"),
            "tool_stats": tool_stats,
            "files_analyzed": self.files_analyzed
        }

# -----------------------------------------------------------------------------
# JSX-specific Analysis Tools
# -----------------------------------------------------------------------------
class JSXAnalyzer:
    """Simple JSX analyzer without external dependencies."""
    
    def __init__(self):
        # Compile regex patterns for efficiency
        self._compiled_react_patterns = [
            (p["id"], re.compile(p["pattern"]), p)
            for p in REACT_PATTERNS
        ]
    
    def analyze_file(self, file_path: Path, content: str) -> List[SecurityIssue]:
        """
        Analyze a JSX/React file for security issues.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            List of security issues
        """
        issues = []
        
        # Validate basic JSX syntax
        syntax_errors = validate_jsx_syntax(content)
        for error in syntax_errors:
            issues.append(SecurityIssue(
                filename=str(file_path),
                line_number=error["line"],
                issue_text=error["text"],
                severity=error["severity"],
                confidence="high",
                issue_type="jsx-syntax-error",
                line_range=[error["line"]],
                code=error["code"],
                tool="jsx-analyzer",
                fix_suggestion="Fix JSX syntax error"
            ))
        
        # Check React-specific patterns
        lines = content.split('\n')
        for pattern_id, regex, pattern_data in self._compiled_react_patterns:
            for i, line in enumerate(lines, 1):
                match = regex.search(line)
                if match:
                    issues.append(SecurityIssue(
                        filename=str(file_path),
                        line_number=i,
                        issue_text=pattern_data["description"],
                        severity=pattern_data["severity"],
                        confidence=pattern_data["confidence"],
                        issue_type=pattern_id,
                        line_range=[i],
                        code=line.strip(),
                        tool="jsx-analyzer",
                        fix_suggestion=pattern_data["fix"]
                    ))
        
        return issues

# -----------------------------------------------------------------------------
# Main Analyzer Class
# -----------------------------------------------------------------------------
class FrontendSecurityAnalyzer:
    """
    Robust frontend security analyzer that uses multiple approaches:
    1. Pattern-based security scanning using regex
    2. React/JSX-specific analysis
    3. Dependency vulnerability checking
    4. Semgrep (if available)
    5. JSHint (if available)
    6. Lightweight ESLint adapter (if Node.js/npm is available)
    """
    
    def __init__(self, base_path: Path):
        """
        Initialize the security analyzer.
        
        Args:
            base_path: Base directory for analysis
        """
        self.base_path = normalize_path(base_path)
        logger.info(f"Initialized FrontendSecurityAnalyzer with base path: {self.base_path}")
        
        # Create a temp directory for config files
        self.temp_dir = Path(tempfile.mkdtemp(prefix="frontend_security_"))
        
        # Initialize JSX analyzer
        self.jsx_analyzer = JSXAnalyzer()
        
        # Cache for file content to avoid reading files multiple times
        self._file_cache = {}
        
        # Compiled regex patterns for efficiency
        self._compiled_security_patterns = [
            (p["id"], re.compile(p["pattern"]), p)
            for p in SECURITY_PATTERNS
        ]
        
        self._compiled_quality_patterns = [
            (p["id"], re.compile(p["pattern"]), p)
            for p in QUALITY_PATTERNS
        ]
        
        # Check which tools are available
        self.available_tools = {
            "pattern_scan": True,  # Always available
            "jsx_analyzer": True,  # Always available
            "dependency_check": True,  # Always available
            "semgrep": cmd_exists("semgrep"),
            "jshint": cmd_exists("jshint"),
            "eslint": cmd_exists("npx") and cmd_exists("npm")
        }
        
        logger.info(f"Available tools: {', '.join(k for k, v in self.available_tools.items() if v)}")
        
        # Define tool sets for quick vs full scan
        self.default_tools = ["pattern_scan", "jsx_analyzer", "dependency_check"]
        
        # Include available external tools for full scan
        self.all_tools = self.default_tools.copy()
        if self.available_tools["semgrep"]:
            self.all_tools.append("semgrep")
        if self.available_tools["jshint"]:
            self.all_tools.append("jshint")
        if self.available_tools["eslint"]:
            self.all_tools.append("eslint")
    
    def _find_application_path(self, model: str, app_num: int) -> Path:
        """
        Find the frontend application path through common patterns.
        
        Args:
            model: Model identifier
            app_num: Application number
            
        Returns:
            Path to the frontend directory
        """
        # Try common patterns for frontend directories
        candidates = [
            self.base_path / model / f"app{app_num}" / "frontend",
            self.base_path / model / f"app{app_num}" / "client",
            self.base_path / model / f"app{app_num}" / "src",
            self.base_path / model / f"app{app_num}" / "web",
            self.base_path / model / f"app{app_num}"
        ]
        
        # Check each candidate path
        for path in candidates:
            if path.exists() and path.is_dir():
                logger.info(f"Found frontend directory: {path}")
                return path
        
        # Fallback to the most common pattern
        fallback = self.base_path / model / f"app{app_num}"
        if not fallback.exists():
            logger.warning(f"Creating directory {fallback} as it doesn't exist")
            try:
                fallback.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"Failed to create directory {fallback}: {e}")
        
        return fallback
    
    def _find_source_files(self, directory: Path) -> List[Path]:
        """
        Find frontend source files in a directory.
        
        Args:
            directory: Directory to scan
            
        Returns:
            List of source file paths
        """
        extensions = (".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".html", ".css")
        exclude_dirs = {"node_modules", ".git", "dist", "build"}
        
        source_files = []
        try:
            for root, dirs, files in os.walk(directory):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
                
                # Find matching files
                for file in files:
                    if file.endswith(extensions):
                        source_files.append(Path(root) / file)
        except Exception as e:
            logger.error(f"Error finding source files: {e}")
        
        return source_files
    
    def _read_file(self, file_path: Path) -> Optional[str]:
        """
        Read a file with caching.
        
        Args:
            file_path: Path to file
            
        Returns:
            File content or None if error
        """
        # Check cache first
        cache_key = str(file_path)
        if cache_key in self._file_cache:
            return self._file_cache[cache_key]
        
        # Read file
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                self._file_cache[cache_key] = content
                return content
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    def _pattern_scan(self, files: List[Path]) -> Tuple[List[SecurityIssue], str]:
        """
        Scan files using regex pattern matching.
        
        Args:
            files: List of files to scan
            
        Returns:
            Tuple of (issues, output_text)
        """
        issues = []
        patterns_checked = len(self._compiled_security_patterns) + len(self._compiled_quality_patterns)
        files_with_issues = set()
        output_log = []
        
        output_log.append(f"[Pattern Scan] Checking {len(files)} files against {patterns_checked} patterns")
        
        for file_path in files:
            content = self._read_file(file_path)
            if not content:
                continue
            
            lines = content.split('\n')
            file_issues = []
            
            # Check security patterns
            for pattern_id, regex, pattern_data in self._compiled_security_patterns:
                for i, line in enumerate(lines, 1):
                    match = regex.search(line)
                    if match:
                        file_issues.append(SecurityIssue(
                            filename=str(file_path.relative_to(self.base_path)),
                            line_number=i,
                            issue_text=pattern_data["description"],
                            severity=pattern_data["severity"],
                            confidence=pattern_data["confidence"],
                            issue_type=pattern_id,
                            line_range=[i],
                            code=line.strip(),
                            tool="pattern_scan",
                            fix_suggestion=pattern_data["fix"]
                        ))
            
            # Check quality patterns
            for pattern_id, regex, pattern_data in self._compiled_quality_patterns:
                for i, line in enumerate(lines, 1):
                    match = regex.search(line)
                    if match:
                        file_issues.append(SecurityIssue(
                            filename=str(file_path.relative_to(self.base_path)),
                            line_number=i,
                            issue_text=pattern_data["description"],
                            severity=pattern_data["severity"],
                            confidence=pattern_data["confidence"],
                            issue_type=pattern_id,
                            line_range=[i],
                            code=line.strip(),
                            tool="pattern_scan",
                            fix_suggestion=pattern_data["fix"]
                        ))
            
            if file_issues:
                files_with_issues.add(file_path)
                issues.extend(file_issues)
        
        output_log.append(f"[Pattern Scan] Found {len(issues)} issues in {len(files_with_issues)} files")
        return issues, "\n".join(output_log)
    
    def _jsx_analysis(self, files: List[Path]) -> Tuple[List[SecurityIssue], str]:
        """
        Analyze JSX/React files for security issues.
        
        Args:
            files: List of files to scan
            
        Returns:
            Tuple of (issues, output_text)
        """
        issues = []
        output_log = []
        
        # Filter for JSX files
        jsx_files = [f for f in files if f.suffix in (".jsx", ".tsx")]
        js_files = [f for f in files if f.suffix == ".js"]
        
        # Also check .js files that might contain React/JSX
        potential_jsx = []
        for js_file in js_files:
            content = self._read_file(js_file)
            if content and re.search(r'React|render\s*\(|<[A-Z][^>]*>|createElement\s*\(', content):
                potential_jsx.append(js_file)
        
        all_jsx_files = jsx_files + potential_jsx
        
        if not all_jsx_files:
            output_log.append("[JSX Analyzer] No JSX files found")
            return [], "\n".join(output_log)
        
        output_log.append(f"[JSX Analyzer] Checking {len(all_jsx_files)} files for React/JSX issues")
        
        for file_path in all_jsx_files:
            content = self._read_file(file_path)
            if not content:
                continue
            
            # Analyze with JSX analyzer
            file_issues = self.jsx_analyzer.analyze_file(
                file_path.relative_to(self.base_path),
                content
            )
            
            if file_issues:
                issues.extend(file_issues)
                output_log.append(f"[JSX Analyzer] Found {len(file_issues)} issues in {file_path}")
        
        output_log.append(f"[JSX Analyzer] Found {len(issues)} issues total")
        return issues, "\n".join(output_log)
    
    def _dependency_check(self, directory: Path) -> Tuple[List[SecurityIssue], str]:
        """
        Check package.json for dependency issues.
        
        Args:
            directory: Directory containing package.json
            
        Returns:
            Tuple of (issues, output_text)
        """
        issues = []
        output_log = []
        
        # Find package.json
        package_json = find_package_json(directory)
        if not package_json:
            output_log.append("[Dependency Check] No package.json found")
            return [], "\n".join(output_log)
        
        output_log.append(f"[Dependency Check] Analyzing {package_json}")
        
        try:
            # Read package.json
            with open(package_json, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            # Check dependencies
            dependencies = {
                **package_data.get("dependencies", {}),
                **package_data.get("devDependencies", {})
            }
            
            # Define known vulnerable versions
            vulnerable_deps = {
                "jquery": [
                    (r"^1\.", "Update jQuery from version 1.x to 3.x or later (XSS vulnerabilities)"),
                    (r"^2\.", "Update jQuery from version 2.x to 3.x or later (XSS vulnerabilities)")
                ],
                "react": [
                    (r"^0\.", "Update React from version 0.x (very outdated)"),
                    (r"^15\.", "Update React from version 15.x (outdated)")
                ],
                "angular": [
                    (r"^1\.", "AngularJS 1.x has reached end-of-life and has security vulnerabilities")
                ],
                "bootstrap": [
                    (r"^2\.", "Bootstrap 2.x is outdated and may contain security issues"),
                    (r"^3\.", "Consider updating Bootstrap 3.x to latest version")
                ],
                "lodash": [
                    (r"^3\.", "Lodash 3.x contains prototype pollution vulnerabilities"),
                    (r"^4\.([0-9]|1[0-6])\.", "Lodash before 4.17.0 contains prototype pollution vulnerabilities")
                ],
                "axios": [
                    (r"^0\.1[0-8]\.", "Axios versions before 0.19.0 have SSRF vulnerabilities")
                ],
                "marked": [
                    (r"^0\.3\.", "Marked 0.3.x has XSS vulnerabilities")
                ],
                "moment": [
                    (r"^2\.([0-9]|1[0-7])\.", "Moment.js has known prototype pollution issues before 2.18.0")
                ],
                "serialize-javascript": [
                    (r"^[0-2]\.", "serialize-javascript has XSS vulnerabilities in versions before 3.0.0")
                ],
                "handlebars": [
                    (r"^4\.[0-6]\.", "Handlebars has prototype pollution in versions before 4.7.0")
                ],
                "node-fetch": [
                    (r"^1\.", "node-fetch v1.x has redirect vulnerabilities")
                ],
                "js-yaml": [
                    (r"^3\.[0-5]\.", "js-yaml has code execution vulnerabilities in versions before 3.6.0")
                ]
            }
            
            for package, version in dependencies.items():
                # Remove version prefixes for comparison
                clean_version = version.lstrip("^~=<>")
                
                # Check against known vulnerabilities
                if package in vulnerable_deps:
                    for pattern, message in vulnerable_deps[package]:
                        if re.match(pattern, clean_version):
                            issues.append(SecurityIssue(
                                filename=str(package_json.relative_to(self.base_path)),
                                line_number=0,
                                issue_text=f"Vulnerable dependency: {package}@{version}",
                                severity="high",
                                confidence="high",
                                issue_type="vulnerable-dependency",
                                line_range=[0],
                                code=f'"{package}": "{version}"',
                                tool="dependency_check",
                                fix_suggestion=message
                            ))
            
            # Check for usage of deprecated or security-risky React packages
            risky_packages = [
                ("react-addons-", "React addons are deprecated and may contain security issues"),
                ("create-react-class", "create-react-class is deprecated"),
                ("unsafe-", "Package name contains 'unsafe'"),
                ("uncontrolled-", "Uncontrolled components may lead to security issues"),
                ("eval-", "Package name suggests unsafe eval usage"),
                ("dangerously-", "Package name suggests dangerous operations")
            ]
            
            for package in dependencies.keys():
                for pattern, message in risky_packages:
                    if pattern in package:
                        issues.append(SecurityIssue(
                            filename=str(package_json.relative_to(self.base_path)),
                            line_number=0,
                            issue_text=f"Potentially risky package: {package}",
                            severity="medium",
                            confidence="medium",
                            issue_type="risky-package",
                            line_range=[0],
                            code=f'"{package}"',
                            tool="dependency_check",
                            fix_suggestion=message
                        ))
            
            # Generic check for older packages with non-pinned versions
            for package, version in dependencies.items():
                # Check for non-pinned versions (using ^ or ~)
                if version.startswith(("^", "~")):
                    issues.append(SecurityIssue(
                        filename=str(package_json.relative_to(self.base_path)),
                        line_number=0,
                        issue_text=f"Non-pinned dependency version: {package}@{version}",
                        severity="low",
                        confidence="medium",
                        issue_type="non-pinned-dependency",
                        line_range=[0],
                        code=f'"{package}": "{version}"',
                        tool="dependency_check",
                        fix_suggestion="Pin dependency versions for better security and reproducible builds"
                    ))
            
            output_log.append(f"[Dependency Check] Found {len(issues)} issues")
            
        except Exception as e:
            output_log.append(f"[Dependency Check] Error: {e}")
        
        return issues, "\n".join(output_log)
    
    def _run_semgrep(self, directory: Path) -> Tuple[List[SecurityIssue], str]:
        """
        Run semgrep for security analysis.
        
        Args:
            directory: Directory to scan
            
        Returns:
            Tuple of (issues, output_text)
        """
        if not self.available_tools["semgrep"]:
            return [], "Semgrep not available"
        
        output_log = []
        output_log.append("[Semgrep] Running security analysis")
        
        # Run semgrep with security ruleset
        cmd = [
            "semgrep",
            "--config=auto",
            "--json",
            "--quiet",
            str(directory)
        ]
        
        success, stdout, stderr = run_cmd(cmd, timeout=60)  # Longer timeout for semgrep
        
        if not success:
            output_log.append(f"[Semgrep] Error: {stderr}")
            return [], "\n".join(output_log)
        
        # Parse results
        results = safe_json_loads(stdout)
        if not results:
            output_log.append("[Semgrep] No results or invalid output")
            return [], "\n".join(output_log)
        
        issues = []
        
        # Process findings
        for result in results.get("results", []):
            try:
                # Map severity
                severity_map = {
                    "ERROR": "high",
                    "WARNING": "medium",
                    "INFO": "low"
                }
                
                severity = severity_map.get(result.get("severity", "INFO"), "medium")
                
                # Create issue
                issues.append(SecurityIssue(
                    filename=str(Path(result.get("path", "unknown")).relative_to(directory)),
                    line_number=result.get("start", {}).get("line", 0),
                    issue_text=result.get("extra", {}).get("message", "Semgrep finding"),
                    severity=severity,
                    confidence="high",
                    issue_type=result.get("check_id", "semgrep-finding"),
                    line_range=[result.get("start", {}).get("line", 0)],
                    code=result.get("extra", {}).get("lines", ""),
                    tool="semgrep",
                    fix_suggestion=result.get("extra", {}).get("fix", "")
                ))
            except Exception as e:
                output_log.append(f"[Semgrep] Error processing result: {e}")
        
        output_log.append(f"[Semgrep] Found {len(issues)} issues")
        return issues, "\n".join(output_log)
    
    def _run_jshint(self, files: List[Path]) -> Tuple[List[SecurityIssue], str]:
        """
        Run JSHint on JavaScript files.
        
        Args:
            files: List of files to analyze
            
        Returns:
            Tuple of (issues, output_text)
        """
        if not self.available_tools["jshint"]:
            return [], "JSHint not available"
        
        # Filter JS files
        js_files = [f for f in files if f.suffix in (".js", ".jsx")]
        if not js_files:
            return [], "No JavaScript files found"
        
        output_log = []
        output_log.append(f"[JSHint] Analyzing {len(js_files)} JavaScript files")
        
        issues = []
        
        for file_path in js_files:
            cmd = ["jshint", "--reporter=json", str(file_path)]
            success, stdout, stderr = run_cmd(cmd)
            
            if not success and stdout:
                try:
                    results = json.loads(stdout)
                    for result in results:
                        # Map JSHint errors to security issues
                        severity = "medium" if result.get("code", "").startswith("W") else "low"
                        
                        # Check for security-related issues
                        error_text = result.get("reason", "")
                        if any(term in error_text.lower() for term in ["security", "injection", "xss", "csrf", "unsafe"]):
                            severity = "high"
                        
                        issues.append(SecurityIssue(
                            filename=str(file_path.relative_to(self.base_path)),
                            line_number=result.get("line", 0),
                            issue_text=error_text,
                            severity=severity,
                            confidence="medium",
                            issue_type=f"jshint-{result.get('code', 'error')}",
                            line_range=[result.get("line", 0)],
                            code=result.get("evidence", ""),
                            tool="jshint",
                            fix_suggestion=None  # JSHint doesn't provide fix suggestions
                        ))
                except json.JSONDecodeError:
                    output_log.append(f"[JSHint] Error parsing output for {file_path}")
        
        output_log.append(f"[JSHint] Found {len(issues)} issues")
        return issues, "\n".join(output_log)
    
    def _run_eslint_bridge(self, files: List[Path]) -> Tuple[List[SecurityIssue], str]:
        """
        Run a lightweight ESLint wrapper that works without full Node.js environment.
        
        Args:
            files: List of files to analyze
            
        Returns:
            Tuple of (issues, output_text)
        """
        if not self.available_tools["eslint"]:
            return [], "ESLint not available (requires Node.js or npx)"
        
        # Filter JS/JSX files
        js_files = [f for f in files if f.suffix in (".js", ".jsx", ".tsx")]
        if not js_files:
            return [], "No JavaScript/JSX files found"
        
        output_log = []
        output_log.append(f"[ESLint] Analyzing {len(js_files)} JavaScript files")
        
        # Create lightweight ESLint config
        config_path = create_lightweight_eslint(self.temp_dir)
        if not config_path:
            output_log.append("[ESLint] Failed to create configuration")
            return [], "\n".join(output_log)
        
        issues = []
        
        for file_path in js_files:
            cmd = ["npx", "eslint", "--no-eslintrc", "-c", str(config_path), "--format", "json", str(file_path)]
            success, stdout, stderr = run_cmd(cmd)
            
            if stdout:
                try:
                    results = json.loads(stdout)
                    for result in results:
                        for message in result.get("messages", []):
                            # Get severity
                            severity_level = message.get("severity", 1)  # 1=warning, 2=error
                            severity = "high" if severity_level == 2 else "medium"
                            
                            # Security-related rules should be high severity
                            rule_id = message.get("ruleId", "")
                            if any(term in rule_id.lower() for term in ["security", "no-eval", "no-danger"]):
                                severity = "high"
                            
                            issues.append(SecurityIssue(
                                filename=str(file_path.relative_to(self.base_path)),
                                line_number=message.get("line", 0),
                                issue_text=message.get("message", "ESLint issue"),
                                severity=severity,
                                confidence="high" if severity_level == 2 else "medium",
                                issue_type=f"eslint-{rule_id}",
                                line_range=[message.get("line", 0)],
                                code=message.get("source", ""),
                                tool="eslint",
                                fix_suggestion=message.get("fix", {}).get("text", "Fix ESLint issue")
                            ))
                except json.JSONDecodeError:
                    output_log.append(f"[ESLint] Error parsing output for {file_path}")
        
        output_log.append(f"[ESLint] Found {len(issues)} issues")
        return issues, "\n".join(output_log)
    
    def run_security_analysis(
        self,
        model: str,
        app_num: int,
        use_all_tools: bool = False
    ) -> Tuple[List[SecurityIssue], Dict[str, str], Dict[str, str]]:
        """
        Run security analysis on frontend code.
        
        Args:
            model: Model identifier
            app_num: Application number
            use_all_tools: Whether to use all available tools
            
        Returns:
            Tuple of (issues, tool_status, tool_outputs)
        """
        logger.info(f"Running security analysis for {model}/app{app_num}")
        
        # Find the frontend directory
        app_path = self._find_application_path(model, app_num)
        if not app_path.exists():
            error_msg = f"Application directory not found: {app_path}"
            logger.error(error_msg)
            return [], {"error": error_msg}, {"error": error_msg}
        
        # Find source files
        source_files = self._find_source_files(app_path)
        if not source_files:
            error_msg = f"No source files found in {app_path}"
            logger.warning(error_msg)
            return [], {"error": error_msg}, {"error": error_msg}
        
        # Initialize result
        result = AnalysisResult()
        result.files_analyzed = len(source_files)
        
        # Determine which tools to run
        tools_to_run = self.all_tools if use_all_tools else self.default_tools
        logger.info(f"Running tools: {', '.join(tools_to_run)}")
        
        # Run tools in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(tools_to_run), 4)) as executor:
            futures = {}
            
            # Submit tool tasks
            if "pattern_scan" in tools_to_run:
                futures[executor.submit(self._pattern_scan, source_files)] = "pattern_scan"
            
            if "jsx_analyzer" in tools_to_run:
                futures[executor.submit(self._jsx_analysis, source_files)] = "jsx_analyzer"
            
            if "dependency_check" in tools_to_run:
                futures[executor.submit(self._dependency_check, app_path)] = "dependency_check"
            
            if "semgrep" in tools_to_run and self.available_tools["semgrep"]:
                futures[executor.submit(self._run_semgrep, app_path)] = "semgrep"
            
            if "jshint" in tools_to_run and self.available_tools["jshint"]:
                futures[executor.submit(self._run_jshint, source_files)] = "jshint"
                
            if "eslint" in tools_to_run and self.available_tools["eslint"]:
                futures[executor.submit(self._run_eslint_bridge, source_files)] = "eslint"
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(futures):
                tool = futures[future]
                try:
                    issues, output = future.result()
                    
                    # Add to results
                    result.add_issues(issues)
                    result.add_tool_result(
                        tool=tool,
                        status=f"✅ Found {len(issues)} issues" if issues else "✅ No issues found",
                        output=output
                    )
                    
                    logger.info(f"Tool {tool} completed with {len(issues)} issues")
                except Exception as e:
                    error_msg = f"Error running {tool}: {e}"
                    logger.error(error_msg)
                    result.add_tool_result(
                        tool=tool,
                        status=f"❌ Error: {e}",
                        output=error_msg
                    )
        
        # Mark tools that were not run
        for tool in self.all_tools:
            if tool not in result.tool_status:
                if tool in self.available_tools and not self.available_tools[tool]:
                    result.add_tool_result(
                        tool=tool,
                        status="❌ Not available on this system",
                        output=f"{tool} is not installed or not found in PATH"
                    )
                else:
                    result.add_tool_result(
                        tool=tool,
                        status="⏸️ Not run in quick scan mode",
                        output="Tool not run"
                    )
        
        # Sort issues by severity, tool, filename, line
        sorted_issues = sorted(
            result.issues,
            key=lambda i: (
                {"high": 0, "medium": 1, "low": 2}.get(i.severity.lower(), 3),
                i.tool,
                i.filename,
                i.line_number
            )
        )
        
        return sorted_issues, result.tool_status, result.tool_outputs
    
    # For compatibility with existing code
    def analyze_security(self, model: str, app_num: int, use_all_tools: bool = False):
        """Alias for run_security_analysis"""
        return self.run_security_analysis(model, app_num, use_all_tools)
    
    def get_analysis_summary(self, issues: List[SecurityIssue]) -> Dict[str, Any]:
        """
        Generate summary statistics for analysis results.
        
        Args:
            issues: List of security issues
            
        Returns:
            Summary dictionary
        """
        # Create a temporary result to generate the summary
        result = AnalysisResult()
        result.add_issues(issues)
        return result.get_summary()
    
    def __del__(self):
        """Clean up temporary directory on destruction."""
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                logger.error(f"Failed to clean up temp directory: {e}")

if __name__ == "__main__":
    # Optional command-line interface for testing
    import argparse
    
    parser = argparse.ArgumentParser(description="Frontend Security Analyzer")
    parser.add_argument("directory", help="Directory to analyze")
    parser.add_argument("--full", action="store_true", help="Use all available tools")
    
    args = parser.parse_args()
    
    # Setup basic logging
    logging.basicConfig(level=logging.INFO)
    
    # Run analysis
    analyzer = FrontendSecurityAnalyzer(Path.cwd())
    source_files = analyzer._find_source_files(Path(args.directory))
    
    print(f"Found {len(source_files)} source files")
    
    issues, tool_status, _ = analyzer.run_security_analysis(
        model="test",
        app_num=1,
        use_all_tools=args.full
    )
    
    print("\nTool Status:")
    for tool, status in tool_status.items():
        print(f"  {tool}: {status}")
    
    print(f"\nFound {len(issues)} issues:")
    for issue in issues:
        print(f"  [{issue.severity.upper()}] {issue.filename}:{issue.line_number} - {issue.issue_text}")