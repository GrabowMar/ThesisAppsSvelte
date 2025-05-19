import json
import logging
import os
import re
import socket
import subprocess
import time
import shutil
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable

import requests
from zapv2 import ZAPv2

# Import JsonResultsManager from utils
from utils import JsonResultsManager

# Configuration constants moved to a central location
class ZAPConfig:
    DEFAULT_API_KEY = os.getenv('ZAP_API_KEY', '5tjkc409k4oaacd69qob5p6uri')
    DEFAULT_MAX_SCAN_DURATION = int(os.getenv('ZAP_MAX_SCAN_DURATION', '120'))
    DEFAULT_AJAX_TIMEOUT = int(os.getenv('ZAP_AJAX_TIMEOUT', '180'))
    DEFAULT_THREAD_COUNT = 8
    DEFAULT_MAX_CHILDREN = 30
    DEFAULT_HEAP_SIZE = '4G'
    DEFAULT_PORT_RANGE = (8090, 8099)
    CALLBACK_PORT_RANGE = (8888, 8899)
    SOURCE_CODE_EXTENSIONS = [
        '.js', '.jsx', '.ts', '.tsx', '.php', '.py',
        '.java', '.html', '.css'
    ]
    ESSENTIAL_ADDONS = [
        'ascanrules', 'pscanrules', 'network', 'selenium',
        'openapi', 'reports', 'domxss', 'database'
    ]
    ACTIVE_RULE_CATEGORIES = {
        "Injection": ["SQL Injection", "Command Injection", "LDAP Injection", "XPath Injection", "XML Injection"],
        "XSS": ["Cross Site Scripting", "DOM XSS"],
        "Information Disclosure": ["Information disclosure", "Source Code Disclosure"],
        "Authentication": ["Authentication", "Session Fixation"],
        "Authorization": ["Authorization", "Insecure"],
        "Security Headers": ["Content Security Policy", "Anti-clickjacking Header", "X-Content-Type-Options"],
        "File Upload": ["File Upload", "Path Traversal"],
        "Server Side": ["Server Side Include", "Server Side Template Injection"],
        "Known Vulnerabilities": ["CVE-", "Log4Shell", "Spring4Shell", "Text4Shell"]
    }
    # App port configuration
    BASE_FRONTEND_PORT = 5501
    PORTS_PER_APP = 2
    BUFFER_PORTS = 20
    APPS_PER_MODEL = 30
    # AI Models mapping
    AI_MODELS = ["Llama", "Mistral", "DeepSeek", "GPT4o", "Claude", "Gemini", "Grok", "R1", "O3"]


logger = logging.getLogger("zap_scanner")


@dataclass
class CodeContext:
    snippet: str
    line_number: Optional[int] = None
    file_path: Optional[str] = None
    start_line: int = 0
    end_line: int = 0
    vulnerable_lines: List[int] = field(default_factory=list)
    highlight_positions: List[Tuple[int, int]] = field(default_factory=list)


@dataclass
class ZapVulnerability:
    url: str
    name: str
    alert: str
    risk: str
    confidence: str
    description: str
    solution: str
    reference: str
    evidence: Optional[str] = None
    cwe_id: Optional[str] = None
    parameter: Optional[str] = None
    attack: Optional[str] = None
    wascid: Optional[str] = None
    affected_code: Optional[CodeContext] = None
    source_file: Optional[str] = None


@dataclass
class ScanStatus:
    status: str = "Not Started"
    progress: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    spider_progress: int = 0
    passive_progress: int = 0
    active_progress: int = 0
    ajax_progress: int = 0
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[int] = None


def log_operation(operation_name: str):
    """Decorator for logging operation start/end with consistent formatting."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(f"Starting {operation_name}...")
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.info(f"Completed {operation_name} in {elapsed:.2f} seconds")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"Failed {operation_name} after {elapsed:.2f} seconds: {str(e)}")
                raise
        return wrapper
    return decorator


class NetworkUtils:
    """Utility class for network operations."""
    
    @staticmethod
    @contextmanager
    def port_check(port: int):
        """Context manager to check if a port is available."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('127.0.0.1', port))
            sock.listen(1)
            yield sock
        finally:
            sock.close()
    
    @staticmethod
    def find_free_port(start_port: int, max_port: int) -> int:
        """Find a free port within the specified range."""
        logger.debug(f"Searching for free port between {start_port} and {max_port}...")
        for port in range(start_port, max_port + 1):
            try:
                with NetworkUtils.port_check(port):
                    logger.info(f"Found free port: {port}")
                    return port
            except OSError:
                logger.debug(f"Port {port} is busy, trying next...")
                continue
        error_msg = f"No free ports found between {start_port} and {max_port}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


class FileUtils:
    """Utility class for file operations."""
    
    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """Ensure a directory exists and return the Path object."""
        path_obj = Path(path)
        path_obj.mkdir(parents=True, exist_ok=True)
        return path_obj
    
    @staticmethod
    def find_binary(possible_paths: List[str], env_var: Optional[str] = None) -> Optional[str]:
        """Find a binary from a list of possible paths or environment variable."""
        if env_var:
            env_path = os.getenv(env_var)
            if env_path and os.path.exists(env_path):
                logger.info(f"Found binary from environment variable {env_var}: {env_path}")
                return env_path
                
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found binary at: {path}")
                return path
                
        return None


class ZAPScanner:
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.api_key = os.getenv('ZAP_API_KEY', ZAPConfig.DEFAULT_API_KEY)
        self.proxy_host = "127.0.0.1"
        self.proxy_port = NetworkUtils.find_free_port(
            ZAPConfig.DEFAULT_PORT_RANGE[0], 
            ZAPConfig.DEFAULT_PORT_RANGE[1]
        )
        self.zap_log = self.base_path / "zap.log"
        self.zap: Optional[ZAPv2] = None
        self.daemon_process: Optional[subprocess.Popen] = None
        self._scans: Dict[str, Dict] = {}
        self.max_children = ZAPConfig.DEFAULT_MAX_CHILDREN
        self.scan_recursively = True
        self.max_scan_duration_minutes = ZAPConfig.DEFAULT_MAX_SCAN_DURATION
        self.thread_per_host = ZAPConfig.DEFAULT_THREAD_COUNT
        self.ajax_timeout = ZAPConfig.DEFAULT_AJAX_TIMEOUT
        self.active_rule_categories = ZAPConfig.ACTIVE_RULE_CATEGORIES
        self.source_code_mapping = {}
        self.source_root_dir = None
        self.source_file_extensions = ZAPConfig.SOURCE_CODE_EXTENSIONS
        self.firefox_binary_path = None
        self.oast_service_configured = False
        self.callback_port = None
        

        if "z_interface_app" in str(self.base_path):
            self.base_path = self.base_path.parent
        else:
            self.base_path = self.base_path
        # Initialize JsonResultsManager for standardized JSON handling
        self.results_manager = JsonResultsManager(base_path=self.base_path, module_name="zap_scanner")
        
        logger.info(f"ZAPScanner initialized with base path: {self.base_path}")
        logger.info(f"ZAP proxy configuration: {self.proxy_host}:{self.proxy_port}")

    def _find_firefox_binary(self) -> Optional[str]:
        return FileUtils.find_binary(
            possible_paths=[
                "C:/Program Files/Mozilla Firefox/firefox.exe",
                "C:/Program Files (x86)/Mozilla Firefox/firefox.exe",
                "/usr/bin/firefox",
                "/usr/local/bin/firefox",
                "/Applications/Firefox.app/Contents/MacOS/firefox"
            ],
            env_var="FIREFOX_BIN"
        )

    def _find_chrome_binary(self) -> Optional[str]:
        return FileUtils.find_binary(
            possible_paths=[
                "C:/Program Files/Google/Chrome/Application/chrome.exe",
                "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
                "/usr/bin/google-chrome",
                "/usr/local/bin/google-chrome",
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            ],
            env_var="CHROME_BIN"
        )

    def _find_zap_installation(self) -> Path:
        zap_home = os.getenv("ZAP_HOME")
        possible_paths = [
            self.base_path / "ZAP_2.14.0",
            self.base_path,
            Path(zap_home) if zap_home else None,
            Path("C:/Program Files/OWASP/Zed Attack Proxy"),
            Path("C:/Program Files (x86)/OWASP/Zed Attack Proxy"),
            Path("C:/Program Files/ZAP/Zed Attack Proxy"),
            Path("/usr/share/zaproxy"),
            Path("/Applications/OWASP ZAP.app/Contents/Java"),
        ]
        logger.debug(f"Searching for ZAP installation in paths: {possible_paths}")
        for path in filter(None, possible_paths):
            if not path.exists():
                logger.debug(f"Path {path} does not exist, skipping")
                continue
            jar_files = list(path.glob("zap*.jar"))
            if jar_files:
                logger.info(f"Found ZAP JAR at: {jar_files[0]}")
                return jar_files[0]
            for exe in ["zap.bat", "zap.sh", "zap.exe"]:
                exe_path = path / exe
                if exe_path.exists():
                    logger.info(f"Found ZAP executable at: {exe_path}")
                    return exe_path
        error_msg = "ZAP installation not found. Please install ZAP and set ZAP_HOME environment variable."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    def _build_zap_command(self, zap_path: Path) -> List[str]:
        logger.debug("Building ZAP command with optimized settings")
        java_opts = self._get_java_opts()
        zap_args = self._get_zap_args()
        if zap_path.suffix == '.jar':
            return ['java'] + java_opts + ['-jar', str(zap_path)] + zap_args
        return [str(zap_path)] + zap_args

    def _get_java_opts(self) -> List[str]:
        return [
            f'-Xmx{ZAPConfig.DEFAULT_HEAP_SIZE}',
            f'-Djava.io.tmpdir={self.base_path / "tmp"}',
            '-Djava.net.preferIPv4Stack=true',
            '-XX:+UseG1GC',
            '-XX:MaxGCPauseMillis=100',
            '-XX:+UseStringDeduplication',
        ]

    def _get_zap_args(self) -> List[str]:
        """
        Get ZAP command line arguments for optimal configuration.
        All configuration is centralized here.
        """
        return [
            '-daemon', '-port', str(self.proxy_port), '-host', self.proxy_host,
            '-config', f'api.key={self.api_key}',
            '-config', 'api.addrs.addr.name=.*',
            '-config', 'api.addrs.addr.regex=true',
            '-config', 'connection.timeoutInSecs=1200',
            '-config', f'ascan.maxScanDurationInMins={self.max_scan_duration_minutes}',
            '-config', f'ascan.threadPerHost={self.thread_per_host}',
            '-config', 'view.mode=standard',
            '-config', 'ascan.attackStrength=HIGH',
            '-config', 'ascan.alertThreshold=LOW',
            '-config', 'pscan.maxAlertsPerRule=0',
            '-config', 'pscan.maxBodySizeInBytes=10000000',
            '-config', 'ajaxSpider.browserId=chrome-headless',
            '-config', f'ajaxSpider.maxDuration={self.ajax_timeout}',
            '-config', 'ajaxSpider.clickDefaultElems=true',
            '-config', 'ajaxSpider.clickElemsOnce=false',
            '-config', 'ajaxSpider.eventWait=2000',
            '-config', 'ajaxSpider.maxCrawlDepth=10',
            '-config', 'ajaxSpider.maxCrawlStates=0',
            '-config', 'ajaxSpider.numberOfBrowsers=4',
            '-config', 'ajaxSpider.randomInputs=true',
            # Standard passive scan rules
            '-config', 'pscans.pscanner(10020).enabled=true', '-config', 'pscans.pscanner(10020).alertThreshold=LOW',
            '-config', 'pscans.pscanner(10021).enabled=true', '-config', 'pscans.pscanner(10021).alertThreshold=LOW',
            '-config', 'pscans.pscanner(10038).enabled=true', '-config', 'pscans.pscanner(10038).alertThreshold=LOW',
            '-config', 'pscans.pscanner(10035).enabled=true', '-config', 'pscans.pscanner(10035).alertThreshold=LOW',
            '-config', 'pscans.pscanner(10063).enabled=true', '-config', 'pscans.pscanner(10063).alertThreshold=LOW',
            '-config', 'pscans.pscanner(10054).enabled=true', '-config', 'pscans.pscanner(10054).alertThreshold=LOW',
            '-config', 'pscans.pscanner(10024).enabled=true', '-config', 'pscans.pscanner(10024).alertThreshold=LOW',
            '-config', 'pscans.pscanner(10025).enabled=true', '-config', 'pscans.pscanner(10025).alertThreshold=LOW',
            '-config', 'pscans.pscanner(10027).enabled=true', '-config', 'pscans.pscanner(10027).alertThreshold=LOW',
            '-config', 'pscans.pscanner(10096).enabled=true', '-config', 'pscans.pscanner(10096).alertThreshold=LOW',
            '-config', 'pscans.pscanner(10097).enabled=true', '-config', 'pscans.pscanner(10097).alertThreshold=LOW',
            '-config', 'pscans.pscanner(10094).enabled=true', '-config', 'pscans.pscanner(10094).alertThreshold=LOW',
            '-config', 'pscans.pscanner(90022).enabled=true', '-config', 'pscans.pscanner(90022).alertThreshold=LOW',
            '-config', 'pscans.pscanner(10109).enabled=true', '-config', 'pscans.pscanner(10109).alertThreshold=LOW',
            '-config', 'pscans.pscanner(10110).enabled=true', '-config', 'pscans.pscanner(10110).alertThreshold=LOW',
            # Ensure active scan settings are applied
            '-config', 'ascan.attackStrength=HIGH',
            '-config', 'ascan.alertThreshold=LOW',
        ]

    def set_source_code_mapping(self, mapping: Dict[str, str], root_dir: Optional[str] = None):
        self.source_code_mapping = mapping
        self.source_root_dir = root_dir
        logger.info(f"Set source code mapping with {len(mapping)} entries")
        if root_dir:
            logger.info(f"Source code root directory: {root_dir}")

    def _url_to_source_file(self, url: str) -> Optional[str]:
        """
        Convert a URL to a source file path.
        """
        if not self.source_code_mapping and not self.source_root_dir:
            return None
            
        # Check explicit mappings first
        for url_prefix, file_path in self.source_code_mapping.items():
            if url.startswith(url_prefix):
                relative_path = url[len(url_prefix):]
                return os.path.join(file_path, relative_path)
                
        # If no explicit mapping, try inferring from source root
        if self.source_root_dir:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                path = parsed.path
                
                # Security: Prevent path traversal by normalizing and validating path
                if path.startswith('/'):
                    path = path[1:]
                # Ensure the path doesn't try to escape with '..'
                if '..' in path:
                    logger.warning(f"Potential path traversal attempt detected in URL: {url}")
                    return None
                    
                # Try common locations in source directory
                possibilities = [
                    os.path.join(self.source_root_dir, path),
                    os.path.join(self.source_root_dir, 'src', path),
                    os.path.join(self.source_root_dir, 'public', path)
                ]
                
                for possibility in possibilities:
                    # Verify the path is within the source root dir to prevent traversal
                    if os.path.abspath(possibility).startswith(os.path.abspath(self.source_root_dir)):
                        if os.path.isfile(possibility):
                            return possibility
                        # Try with different extensions if no extension specified
                        base_path, ext = os.path.splitext(possibility)
                        if not ext:
                            for extension in self.source_file_extensions:
                                path_with_ext = f"{base_path}{extension}"
                                if os.path.isfile(path_with_ext):
                                    return path_with_ext
            except Exception as e:
                logger.debug(f"Error inferring source file from URL {url}: {str(e)}")
                
        return None

    def _fetch_source_from_url(self, url: str) -> Optional[str]:
        try:
            if any(url.endswith(ext) for ext in self.source_file_extensions):
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    return response.text
        except Exception as e:
            logger.debug(f"Error fetching source from URL {url}: {str(e)}")
        return None

    def _get_affected_code(self, alert: Dict[str, Any]) -> Optional[CodeContext]:
        url = alert.get('url', '')
        evidence = alert.get('evidence', '')
        if not evidence or not url:
            return None
            
        # Get source code from file or URL
        source_file = self._url_to_source_file(url)
        source_code = None
        
        # Try to load source from file
        if source_file and os.path.isfile(source_file):
            try:
                with open(source_file, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                logger.debug(f"Loaded source code from: {source_file}")
            except Exception as e:
                logger.debug(f"Error reading source file {source_file}: {str(e)}")
                
        # If file loading failed, try to fetch from URL
        if not source_code:
            source_code = self._fetch_source_from_url(url)
            if source_code:
                logger.debug(f"Fetched source code from URL: {url}")
                
        # As a last resort, try to extract from ZAP messages
        if not source_code:
            try:
                messages = []
                try:
                    if hasattr(self.zap.core, 'messages'):
                        messages = self.zap.core.messages(baseurl=url)
                        logger.debug(f"Found {len(messages)} messages for URL: {url}")
                except Exception as e:
                    logger.debug(f"Error getting messages for URL {url}: {str(e)}")
                    
                for message in messages:
                    if isinstance(message, dict) and 'responseBody' in message:
                        response_body = message.get('responseBody', '')
                        if evidence in response_body:
                            source_code = response_body
                            logger.debug(f"Using response body as source code for URL: {url}")
                            break
                    elif hasattr(message, 'get') and callable(message.get):
                        message_id = message.get('id')
                        if message_id:
                            try:
                                full_message = self.zap.core.message(message_id)
                                if (full_message and 'responseBody' in full_message):
                                    response_body = full_message.get('responseBody', '')
                                    if evidence in response_body:
                                        source_code = response_body
                                        logger.debug(f"Found evidence in message ID {message_id}")
                                        break
                            except Exception as e:
                                logger.debug(f"Error retrieving message {message_id}: {str(e)}")
            except Exception as e:
                logger.debug(f"Error trying to extract source from ZAP messages: {str(e)}")
                
        # If no source code found, just return the evidence
        if not source_code:
            logger.debug(f"No source code available for URL: {url}")
            if evidence:
                return CodeContext(snippet=evidence, line_number=None, file_path=source_file, highlight_positions=[(0, len(evidence))])
            return None
            
        # Extract context from source code
        try:
            pattern = re.escape(evidence)
            matches = list(re.finditer(pattern, source_code))
            if not matches:
                logger.debug(f"Evidence not found in source code for URL: {url}")
                return CodeContext(snippet=evidence, line_number=None, file_path=source_file, highlight_positions=[(0, len(evidence))])
                
            match = matches[0]
            start_pos, end_pos = match.span()
            line_number = source_code[:start_pos].count('\n') + 1
            
            # Extract code context with surrounding lines
            lines = source_code.splitlines()
            start_line = max(0, line_number - 6)
            end_line = min(len(lines), line_number + 5)
            context_lines = lines[start_line:end_line]
            context_snippet = '\n'.join(context_lines)
            
            # Adjust highlight position for extracted context
            if start_line > 0:
                prefix_length = len('\n'.join(lines[:start_line])) + 1
                adjusted_start = start_pos - prefix_length
                adjusted_end = end_pos - prefix_length
            else:
                adjusted_start = start_pos
                adjusted_end = end_pos
                
            adjusted_start = max(0, adjusted_start)
            adjusted_end = min(len(context_snippet), adjusted_end)
            
            return CodeContext(
                snippet=context_snippet, 
                line_number=line_number, 
                file_path=source_file, 
                start_line=start_line + 1, 
                end_line=end_line, 
                vulnerable_lines=[line_number], 
                highlight_positions=[(adjusted_start, adjusted_end)]
            )
        except Exception as e:
            logger.debug(f"Error extracting code context: {str(e)}")
            return CodeContext(
                snippet=evidence, 
                line_number=None, 
                file_path=source_file, 
                highlight_positions=[(0, len(evidence))]
            )

    @log_operation("ZAP process cleanup")
    def _cleanup_existing_zap(self):
        try:
            if self.daemon_process:
                logger.info("Terminating existing ZAP process...")
                self.daemon_process.terminate()
                try:
                    self.daemon_process.wait(timeout=15)
                    logger.debug("ZAP process terminated normally")
                except subprocess.TimeoutExpired:
                    logger.warning("ZAP process didn't terminate in time, forcing kill")
                    self.daemon_process.kill()
                    self.daemon_process.wait()
                    logger.debug("ZAP process forcibly killed")
                self.daemon_process = None
                
            # Platform-specific process cleanup
            if os.name == 'nt':
                logger.debug("Attempting to kill stray ZAP processes on Windows...")
                for proc in ['java.exe', 'zap.exe']:
                    try:
                        result = subprocess.run(['taskkill', '/f', '/im', proc], capture_output=True, check=False)
                        logger.debug(f"Taskkill result for {proc}: {result.returncode}")
                    except Exception as e:
                        logger.debug(f"Error running taskkill for {proc}: {str(e)}")
            else:
                logger.debug("Attempting to kill stray ZAP processes on Unix...")
                try:
                    result = subprocess.run(['pkill', '-f', 'zap.jar'], capture_output=True, check=False)
                    logger.debug(f"pkill result: {result.returncode}")
                except Exception as e:
                    logger.debug(f"Error running pkill: {str(e)}")
                    
            time.sleep(5)
            logger.info("ZAP process cleanup complete")
        except Exception as e:
            logger.warning(f"Error during ZAP cleanup: {str(e)}")

    def _verify_addons_integrity(self) -> List[str]:
        logger.info("Verifying add-on integrity...")
        corrupted_addons = []
        plugin_dir = os.path.join(os.path.expanduser("~"), "ZAP", "plugin")
        
        if os.path.exists(plugin_dir):
            try:
                for file in os.listdir(plugin_dir):
                    if file.endswith(".zap"):
                        if ". " in file:
                            addon_id = file.split("-")[0]
                            corrupted_addons.append(addon_id)
                            logger.warning(f"Found likely corrupted add-on file: {file}")
                if corrupted_addons:
                    logger.warning(f"Found {len(corrupted_addons)} potentially corrupted add-ons: {', '.join(corrupted_addons)}")
            except Exception as e:
                logger.error(f"Error checking add-on integrity: {str(e)}")
                
        # Check for missing essential add-ons
        for addon in ZAPConfig.ESSENTIAL_ADDONS:
            if addon not in corrupted_addons:
                addon_file = None
                for file in os.listdir(plugin_dir) if os.path.exists(plugin_dir) else []:
                    if file.startswith(f"{addon}-"):
                        addon_file = file
                        break
                if not addon_file:
                    corrupted_addons.append(addon)
                    logger.warning(f"Essential add-on missing: {addon}")
                    
        return corrupted_addons

    def _fix_corrupted_addons(self, corrupted_addons: List[str]):
        if not corrupted_addons:
            return
            
        logger.info(f"Attempting to fix {len(corrupted_addons)} corrupted add-ons...")
        plugin_dir = os.path.join(os.path.expanduser("~"), "ZAP", "plugin")
        backup_dir = os.path.join(os.path.expanduser("~"), "ZAP", "plugin_backup")
        
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            
        for addon_id in corrupted_addons:
            try:
                for file in os.listdir(plugin_dir):
                    if file.startswith(f"{addon_id}-") or file == f"{addon_id}.zap":
                        src_path = os.path.join(plugin_dir, file)
                        dst_path = os.path.join(backup_dir, file)
                        shutil.move(src_path, dst_path)
                        logger.info(f"Moved corrupted add-on {file} to backup directory")
            except Exception as e:
                logger.error(f"Error fixing corrupted add-on {addon_id}: {str(e)}")
                
        logger.info("Corrupted add-ons have been moved to backup directory")
        logger.info("After ZAP starts, please reinstall these add-ons from the marketplace")

    @log_operation("Browser configuration")
    def _configure_browser_settings(self):
        try:
            if not self.firefox_binary_path:
                self.firefox_binary_path = self._find_firefox_binary()
                
            if self.firefox_binary_path and hasattr(self.zap, 'selenium'):
                logger.info(f"Setting Firefox binary path to: {self.firefox_binary_path}")
                self.zap.selenium.set_option_firefox_binary_path(self.firefox_binary_path)
                
                try:
                    if hasattr(self.zap.selenium, 'set_option_firefox_driver_path'):
                        geckodriver_paths = [
                            os.path.join(self.base_path, "geckodriver.exe"),
                            os.path.join(self.base_path, "geckodriver"),
                            os.path.join(os.path.expanduser("~"), "geckodriver.exe"),
                            os.path.join(os.path.expanduser("~"), "geckodriver"),
                            "/usr/local/bin/geckodriver"
                        ]
                        for path in geckodriver_paths:
                            if os.path.exists(path):
                                logger.info(f"Setting Firefox driver path to: {path}")
                                self.zap.selenium.set_option_firefox_driver_path(path)
                                break
                except Exception as driver_error:
                    logger.warning(f"Error setting Firefox driver path: {str(driver_error)}")
                    
                return True
            else:
                chrome_path = self._find_chrome_binary()
                if chrome_path and hasattr(self.zap, 'selenium'):
                    logger.info(f"Setting Chrome binary path to: {chrome_path}")
                    self.zap.selenium.set_option_chrome_binary_path(chrome_path)
                    return True
                    
                logger.warning("No browser binaries found for DOM XSS scanning")
                return False
        except Exception as e:
            logger.error(f"Error configuring browser settings: {str(e)}")
            return False

    @log_operation("OAST service configuration")
    def _configure_oast_service(self) -> bool:
        try:
            # Check if OAST service is already running
            if hasattr(self.zap, 'oast') and hasattr(self.zap.oast, 'services'):
                services = self.zap.oast.services
                if services:
                    for service in services:
                        if service.get('running', False):
                            logger.info(f"OAST service already running: {service.get('name')}")
                            self.oast_service_configured = True
                            return True
                            
            # Find a free port for callback service
            if not self.callback_port:
                self.callback_port = NetworkUtils.find_free_port(
                    ZAPConfig.CALLBACK_PORT_RANGE[0],
                    ZAPConfig.CALLBACK_PORT_RANGE[1]
                )
                
            # Configure the callback service
            if hasattr(self.zap, 'callbackservice'):
                status = self.zap.callbackservice.status
                logger.info(f"Callback service status: {status}")
                
                if "Running" not in status:
                    self.zap.callbackservice.set_option_port(self.callback_port)
                    self.zap.callbackservice.set_option_remote_address("0.0.0.0")
                    self.zap.callbackservice.start_service()
                    logger.info(f"Started callback service on port {self.callback_port}")
                    
                status = self.zap.callbackservice.status
                if "Running" in status:
                    self.oast_service_configured = True
                    if hasattr(self.zap.ascan, 'set_option_scan_null_json_values'):
                        self.zap.ascan.set_option_scan_null_json_values(True)
                        logger.info("Enabled scanning of null JSON values")
                    return True
                else:
                    logger.warning(f"Failed to start callback service, status: {status}")
                    return False
            else:
                logger.warning("Callback service not available in this ZAP version")
                return False
        except Exception as e:
            logger.error(f"Error configuring OAST service: {str(e)}")
            return False

    @log_operation("ZAP daemon startup")
    def _start_zap_daemon(self) -> bool:
        start_time = datetime.now()
        try:
            # Clean up any existing ZAP processes
            self._cleanup_existing_zap()
            
            # Verify and fix add-ons
            corrupted_addons = self._verify_addons_integrity()
            if corrupted_addons:
                logger.warning(f"Found corrupted add-ons: {', '.join(corrupted_addons)}")
                self._fix_corrupted_addons(corrupted_addons)
                
            # Create temp directory
            tmp_dir = FileUtils.ensure_directory(self.base_path / "tmp")
            logger.debug(f"Created temporary directory: {tmp_dir}")
            
            # Find ZAP installation
            zap_path = self._find_zap_installation()
            if not zap_path.exists():
                error_msg = f"ZAP not found at {zap_path}"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
                
            # Build and execute ZAP command
            cmd = self._build_zap_command(zap_path)
            logger.info(f"Starting ZAP with command: {' '.join(cmd)}")
            
            # Use with statement to properly close the log file
            with open(self.zap_log, 'w') as log_file:
                logger.debug(f"ZAP log will be written to: {self.zap_log}")
                creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                self.daemon_process = subprocess.Popen(
                    cmd, 
                    stdout=log_file, 
                    stderr=subprocess.STDOUT, 
                    creationflags=creationflags
                )
                
            logger.debug(f"ZAP process started with PID: {self.daemon_process.pid}")
            logger.info("Waiting for ZAP to initialize (15 seconds)...")
            time.sleep(15)
            
            # Check if process is still running
            if self.daemon_process.poll() is not None:
                with open(self.zap_log, 'r') as f: 
                    error_log = f.read()
                error_msg = (f"ZAP failed to start. Exit code: {self.daemon_process.returncode}\n"
                             f"Log excerpt:\n{error_log[-2000:]}")
                logger.error(error_msg)
                raise RuntimeError(error_msg)
                
            # Try to connect to ZAP API
            for attempt in range(1, 6):
                try:
                    logger.info(f"Connecting to ZAP API (attempt {attempt}/5)...")
                    self.zap = ZAPv2(
                        apikey=self.api_key, 
                        proxies={
                            'http': f'http://{self.proxy_host}:{self.proxy_port}', 
                            'https': f'http://{self.proxy_host}:{self.proxy_port}'
                        }
                    )
                    version = self.zap.core.version
                    logger.info(f"Successfully connected to ZAP {version}")
                    
                    # Configure browser and OAST service
                    browser_configured = self._configure_browser_settings()
                    if browser_configured: 
                        logger.info("Browser settings configured successfully")
                    else: 
                        logger.warning("No browsers configured. DOM XSS scanning will be limited.")
                        
                    oast_configured = self._configure_oast_service()
                    if oast_configured: 
                        logger.info("OAST service configured successfully")
                    else: 
                        logger.warning("OAST service not configured. Some scanners will be limited.")
                        
                    elapsed = (datetime.now() - start_time).total_seconds()
                    logger.info(f"ZAP startup completed in {elapsed:.2f} seconds")
                    return True
                except Exception as e:
                    logger.warning(f"Connection attempt {attempt} failed: {str(e)}")
                    if attempt < 5:
                        logger.info("Waiting 5 seconds before next attempt...")
                        time.sleep(5)
                        
            error_msg = "Failed to connect to ZAP after 5 attempts"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            logger.error(f"Failed to start ZAP: {str(e)}")
            self._cleanup_existing_zap()
            raise RuntimeError(f"Failed to start ZAP: {str(e)}")

    def _log_with_rate_limit(self, message: str, progress: int, elapsed: float,
                             last_logged_progress: int, log_interval: int = 30) -> bool:
        if progress != last_logged_progress or elapsed % log_interval < 5:
            logger.info(f"{message}: {progress}% (elapsed: {elapsed:.1f}s)")
            return True
        return False

    def _monitor_scan_progress(
            self, status_func: Callable, scan_id: str, scan_type: str, interval: int = 5):
        logger.info(f"Monitoring {scan_type} progress for scan ID: {scan_id}")
        start_time = datetime.now()
        last_logged_progress = -1
        
        while True:
            try:
                progress = int(status_func(scan_id))
                elapsed = (datetime.now() - start_time).total_seconds()
                
                if self._log_with_rate_limit(f"{scan_type} progress", progress, elapsed, last_logged_progress):
                    last_logged_progress = progress
                    
                if progress >= 100:
                    logger.info(f"{scan_type} scan completed in {elapsed:.1f} seconds")
                    break
                    
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error monitoring {scan_type} progress: {str(e)}")
                raise

    def _monitor_ajax_spider_until_complete(
            self, interval: int = 5, max_time: int = 180):
        logger.info("Monitoring AJAX Spider progress...")
        start_time = datetime.now()
        last_result_count = 0
        stagnant_cycles = 0
        
        while True:
            try:
                status = self.zap.ajaxSpider.status
                elapsed = (datetime.now() - start_time).total_seconds()
                progress_percent = min(int((elapsed / max_time) * 100), 99)
                
                if status == "running":
                    current_results = self.zap.ajaxSpider.results()
                    current_count = len(current_results)
                    
                    if elapsed % 10 < interval or abs(current_count - last_result_count) > 5:
                        logger.info(f"AJAX Spider running... ({progress_percent}%, {current_count} URLs, elapsed: {elapsed:.1f}s)")
                        
                    # Check for stalled progress
                    if current_count == last_result_count:
                        stagnant_cycles += 1
                        if stagnant_cycles >= 3 and elapsed > 60:
                            logger.info(f"AJAX Spider stopping early - no new results for {stagnant_cycles} cycles")
                            self.zap.ajaxSpider.stop()
                            break
                    else:
                        stagnant_cycles = 0
                        last_result_count = current_count
                else:
                    logger.info(f"AJAX Spider completed with status: {status} (elapsed: {elapsed:.1f}s)")
                    result_count = len(self.zap.ajaxSpider.results())
                    logger.info(f"AJAX Spider found {result_count} results")
                    break
                    
                # Check if maximum time exceeded
                if elapsed > max_time:
                    logger.warning(f"AJAX Spider reached maximum time of {max_time} seconds. Stopping...")
                    self.zap.ajaxSpider.stop()
                    break
                    
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error monitoring AJAX Spider: {str(e)}")
                self._attempt_stop_ajax()
                break

    def _attempt_stop_ajax(self):
        try:
            self.zap.ajaxSpider.stop()
            logger.info("Successfully stopped AJAX Spider")
        except Exception as e:
            logger.warning(f"Error stopping AJAX Spider: {str(e)}")

    @log_operation("Passive scan completion")
    def _wait_for_passive_scan_completion(self, max_wait_time: int = 300):
        start_time = datetime.now()
        max_wait_seconds = max_wait_time
        last_records = -1
        
        try:
            while True:
                records_to_scan = int(self.zap.pscan.records_to_scan)
                elapsed = (datetime.now() - start_time).total_seconds()
                
                if records_to_scan != last_records or elapsed % 30 < 5:
                    logger.info(f"Passive scan in progress: {records_to_scan} records left to scan (elapsed: {elapsed:.1f}s)")
                    last_records = records_to_scan
                    
                if records_to_scan == 0:
                    logger.info(f"Passive scan completed in {elapsed:.1f} seconds")
                    break
                    
                if elapsed > max_wait_seconds:
                    logger.warning(f"Reached maximum wait time ({max_wait_seconds}s) for passive scan. Continuing with {records_to_scan} records left to scan.")
                    break
                    
                time.sleep(5)
        except Exception as e:
            logger.error(f"Error waiting for passive scan: {str(e)}")
            raise

    @log_operation("Passive scan configuration")
    def _configure_passive_scanning(self):
        try:
            logger.info("Enabling ALL passive scanners...")
            self.zap.pscan.enable_all_scanners()
            
            logger.info("Setting passive scan to analyze ALL traffic (not just in-scope)...")
            self.zap.pscan.set_scan_only_in_scope(False)
            
            logger.info("Setting LOW alert threshold for all passive scanners to increase detection rate...")
            scanners = self.zap.pscan.scanners
            for scanner in scanners:
                scanner_id = scanner.get('id')
                self.zap.pscan.set_scanner_alert_threshold(scanner_id, "LOW")
                
            logger.info("Setting unlimited maximum alerts per rule...")
            self.zap.pscan.set_max_alerts_per_rule(0)
            
            enabled_count = 0
            for scanner in scanners:
                if scanner.get('enabled') == 'true':
                    enabled_count += 1
                    logger.debug(f" - {scanner.get('id')}: {scanner.get('name')}")
                    
            logger.info(f"Passive scanning fully configured with {enabled_count} enabled scanners.")
        except Exception as e:
            logger.error(f"Error configuring passive scanning: {str(e)}")
            raise

    @log_operation("Active scan configuration")
    def _configure_active_scanning(self):
        try:
            logger.info("Enabling ALL active scanners...")
            self.zap.ascan.enable_all_scanners()
            
            logger.info("Setting HIGH attack strength for all policies...")
            for policy_id in range(0, 5):
                self.zap.ascan.set_policy_attack_strength(id=policy_id, attackstrength="HIGH")
                
            logger.info("Setting LOW alert threshold for all policies...")
            for policy_id in range(0, 5):
                self.zap.ascan.set_policy_alert_threshold(id=policy_id, alertthreshold="LOW")
                
            logger.info("Configuring scan policy options...")
            self.zap.ascan.set_option_handle_anti_csrf_tokens(True)
            self.zap.ascan.set_option_scan_headers_all_requests(True)
            self.zap.ascan.set_option_add_query_param(True)
            
            if hasattr(self.zap.ascan, 'set_option_scan_null_json_values'):
                self.zap.ascan.set_option_scan_null_json_values(True)
                logger.info("Enabled scanning of null JSON values")
                
            if hasattr(self.zap.ascan, 'set_option_inject_plugin_id_in_header'):
                self.zap.ascan.set_option_inject_plugin_id_in_header(True)
                logger.info("Enabled plugin ID injection in headers")
                
            self.zap.ascan.set_option_max_alerts_per_rule(0)
            self.zap.ascan.set_option_max_rule_duration_in_mins(5)
            self.zap.ascan.set_option_max_scan_duration_in_mins(self.max_scan_duration_minutes)
            self.zap.ascan.set_option_thread_per_host(self.thread_per_host)
            
            # Configure OAST-dependent scanners
            if self.oast_service_configured:
                logger.info("OAST service is configured, enabling blind vulnerability scanners...")
                log4shell_id = "90001"
                if hasattr(self.zap.ascan, 'set_scanner_alert_threshold'):
                    try:
                        self.zap.ascan.set_scanner_alert_threshold(log4shell_id, "LOW")
                        logger.info("Enabled Log4Shell scanner")
                    except Exception as e:
                        logger.debug(f"Error enabling Log4Shell scanner: {str(e)}")
                        
                for scanner_name in ["SSRF", "SSTI Blind", "Log4Shell"]:
                    try:
                        scanners = self.zap.ascan.scanners()
                        for scanner in scanners:
                            if scanner_name.lower() in scanner.get('name', '').lower():
                                scanner_id = scanner.get('id')
                                self.zap.ascan.enable_scanners(scanner_id)
                                self.zap.ascan.set_scanner_alert_threshold(scanner_id, "LOW")
                                logger.info(f"Enabled {scanner.get('name')} scanner")
                                break
                    except Exception as e:
                        logger.debug(f"Error enabling {scanner_name} scanner: {str(e)}")
                        
            # Log summary of enabled scanners
            scanners = self.zap.ascan.scanners()
            enabled_count = 0
            category_counts = {}
            for scanner in scanners:
                if scanner.get('enabled') == 'true':
                    enabled_count += 1
                    category = scanner.get('category', 'Other')
                    if category not in category_counts:
                        category_counts[category] = 0
                    category_counts[category] += 1
                    
            for category, count in category_counts.items():
                logger.info(f"Enabled {count} active scanners in category: {category}")
                
            logger.info(f"Active scanning fully configured with {enabled_count} enabled scanners")
        except Exception as e:
            logger.error(f"Error configuring active scanning: {str(e)}")
            raise

    def _perform_extended_spidering(self, target_url: str):
        logger.info("Performing extended spidering...")
        common_paths = [
            "/robots.txt", "/sitemap.xml", "/.well-known/security.txt", 
            "/crossdomain.xml", "/clientaccesspolicy.xml", "/manifest.json", 
            "/package.json", "/humans.txt"
        ]
        
        base_url = target_url.rstrip("/")
        for path in common_paths:
            try:
                url = f"{base_url}{path}"
                logger.debug(f"Accessing: {url}")
                self.zap.core.access_url(url, followredirects=True)
                time.sleep(0.3)
            except Exception as e:
                logger.debug(f"Error accessing {url}: {str(e)}")
                
        logger.info("Extended spidering completed")

    @log_operation("AJAX Spider")
    def _run_ajax_spider(self, target_url: str, focused: bool = False):
        spider_type = 'focused' if focused else 'full'
        logger.info(f"Starting {spider_type} AJAX Spider for JavaScript-rendered content...")
        
        try:
            # Check if AJAX Spider is already running
            try:
                current_status = self.zap.ajaxSpider.status
                if current_status == "running":
                    logger.info("Stopping previously running AJAX Spider...")
                    self.zap.ajaxSpider.stop()
                    time.sleep(2)
            except Exception as e:
                logger.warning(f"Error checking AJAX Spider status: {str(e)}")
                
            # Configure AJAX Spider settings
            if focused:
                logger.info("Setting focused element selector configuration...")
                self.zap.ajaxSpider.set_option_element_id("input, button, a, select, form, [role=button], [type=submit]")
                self.zap.ajaxSpider.set_option_number_of_browsers(2)
                self.zap.ajaxSpider.set_option_max_crawl_depth(3)
            else:
                self.zap.ajaxSpider.set_option_element_id(None)
                
            # Select browser
            if not self.firefox_binary_path:
                logger.info("Firefox not found, using Chrome-headless for AJAX Spider")
                self.zap.ajaxSpider.set_option_browser_id("chrome-headless")
                
            # Start AJAX Spider
            logger.info(f"Running AJAX Spider on target: {target_url}")
            result = self.zap.ajaxSpider.scan(url=target_url, inscope=None, contextname=None, subtreeonly=None)
            logger.info(f"AJAX Spider started: {result}")
            
            # Monitor progress
            self._monitor_ajax_spider_until_complete(interval=5, max_time=self.ajax_timeout)
            
            # Report results
            results = self.zap.ajaxSpider.results()
            logger.info(f"AJAX Spider completed with {len(results)} URLs discovered")
            if results:
                logger.info("Sample of AJAX-discovered URLs:")
                for url in results[:min(5, len(results))]:
                    logger.info(f" - {url.get('url', 'Unknown URL')}")
                    
            return True
        except requests.RequestException as e:
            logger.error(f"Network error during AJAX Spider: {str(e)}")
            self._attempt_stop_ajax()
            return False
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in AJAX Spider: {str(e)}")
            self._attempt_stop_ajax()
            return False
        except Exception as e:
            logger.error(f"Unexpected error running AJAX Spider: {str(e)}", exc_info=True)
            self._attempt_stop_ajax()
            return False

    def _collect_source_files(self, target_url: str) -> Dict[str, str]:
        logger.info("Collecting source files for code analysis...")
        collected_files = {}
        
        if hasattr(self.zap, 'core') and hasattr(self.zap.core, 'messages'):
            try:
                messages = self.zap.core.messages(baseurl=target_url)
                for message in messages:
                    url = message.get('url', '')
                    if not url: 
                        continue
                        
                    if any(url.endswith(ext) for ext in self.source_file_extensions):
                        message_id = message.get('id')
                        if message_id:
                            try:
                                full_message = self.zap.core.message(message_id)
                                if full_message and 'responseBody' in full_message:
                                    logger.debug(f"Collected source from URL: {url}")
                                    collected_files[url] = full_message['responseBody']
                            except Exception as e:
                                logger.debug(f"Error retrieving message {message_id}: {str(e)}")
            except Exception as e:
                logger.warning(f"Error collecting source files: {str(e)}")
                
        logger.info(f"Collected {len(collected_files)} potential source files for analysis")
        return collected_files

    def _calculate_app_url(self, model: str, app_num: int) -> str:
        """Calculate the URL for a specific app based on its model and number."""
        model_idx = self._get_model_index(model)
        total_block_size = ZAPConfig.APPS_PER_MODEL * ZAPConfig.PORTS_PER_APP + ZAPConfig.BUFFER_PORTS
        frontend_port_start = ZAPConfig.BASE_FRONTEND_PORT + (model_idx * total_block_size)
        frontend_port = frontend_port_start + ((app_num - 1) * ZAPConfig.PORTS_PER_APP)
        return f"http://localhost:{frontend_port}"

    def save_scan_results(self, model: str, app_num: int, vulnerabilities: List[ZapVulnerability], summary: Dict) -> Optional[Path]:
        """
        Save scan results to a JSON file using JsonResultsManager.
        
        Args:
            model: Model name
            app_num: Application number
            vulnerabilities: List of ZapVulnerability objects
            summary: Dictionary with scan summary information
        
        Returns:
            Path where results were saved or None if there was an error
        """
        try:
            # Prepare data for saving
            results_dict = {
                "alerts": [],
                "summary": summary,
                "scan_time": datetime.now().isoformat()
            }
            
            # Convert vulnerabilities to dictionaries
            for vuln in vulnerabilities:
                vuln_dict = asdict(vuln)
                if vuln.affected_code:
                    vuln_dict['affected_code'] = asdict(vuln.affected_code)
                results_dict['alerts'].append(vuln_dict)
            
            # Use JsonResultsManager to save the results
            file_name = ".zap_results.json"
            results_path = self.results_manager.save_results(
                model=model,
                app_num=app_num,
                results=results_dict,
                file_name=file_name,
                maintain_legacy=False
            )
            
            logger.info(f"Saved scan results to {results_path}")
            return results_path
        except Exception as e:
            logger.error(f"Error saving scan results: {e}")
            return None

    def load_scan_results(self, model: str, app_num: int) -> Optional[Dict[str, Any]]:
        """
        Load scan results from a JSON file using JsonResultsManager.
        
        Args:
            model: Model name
            app_num: Application number
        
        Returns:
            Dictionary containing scan results or None if not found
        """
        try:
            file_name = ".zap_results.json"
            data = self.results_manager.load_results(
                model=model,
                app_num=app_num,
                file_name=file_name
            )
            
            if data:
                logger.info(f"Successfully loaded scan results for {model}/app{app_num}")
                return data
            else:
                logger.warning(f"No scan results found for {model}/app{app_num}")
                return None
        except Exception as e:
            logger.error(f"Error loading scan results for {model}/app{app_num}: {e}")
            return None

    def get_scan_vulnerabilities(self, model: str, app_num: int) -> List[ZapVulnerability]:
        """
        Load scan vulnerabilities from results and reconstruct ZapVulnerability objects.
        
        Args:
            model: Model name
            app_num: Application number
        
        Returns:
            List of ZapVulnerability objects
        """
        results = self.load_scan_results(model, app_num)
        vulnerabilities = []
        
        if not results or 'alerts' not in results:
            return vulnerabilities
            
        try:
            for alert in results['alerts']:
                # Create CodeContext object if present
                affected_code = None
                if 'affected_code' in alert and alert['affected_code']:
                    ac_data = alert['affected_code']
                    affected_code = CodeContext(
                        snippet=ac_data.get('snippet', ''),
                        line_number=ac_data.get('line_number'),
                        file_path=ac_data.get('file_path'),
                        start_line=ac_data.get('start_line', 0),
                        end_line=ac_data.get('end_line', 0),
                        vulnerable_lines=ac_data.get('vulnerable_lines', []),
                        highlight_positions=ac_data.get('highlight_positions', [])
                    )
                
                # Create ZapVulnerability object
                vuln = ZapVulnerability(
                    url=alert.get('url', ''),
                    name=alert.get('name', ''),
                    alert=alert.get('alert', ''),
                    risk=alert.get('risk', ''),
                    confidence=alert.get('confidence', ''),
                    description=alert.get('description', ''),
                    solution=alert.get('solution', ''),
                    reference=alert.get('reference', ''),
                    evidence=alert.get('evidence'),
                    cwe_id=alert.get('cwe_id'),
                    parameter=alert.get('parameter'),
                    attack=alert.get('attack'),
                    wascid=alert.get('wascid'),
                    affected_code=affected_code,
                    source_file=alert.get('source_file')
                )
                vulnerabilities.append(vuln)
                
            logger.info(f"Loaded {len(vulnerabilities)} vulnerabilities for {model}/app{app_num}")
            return vulnerabilities
        except Exception as e:
            logger.error(f"Error processing scan results for {model}/app{app_num}: {e}")
            return []

    @log_operation("Target scan")
    def scan_target(self, target_url: str, quick_scan: bool = False) -> Tuple[List[ZapVulnerability], Dict]:
        scan_start_time = datetime.now()
        vulnerabilities: List[ZapVulnerability] = []
        summary: Dict = {
            "start_time": scan_start_time.isoformat(), 
            "target_url": target_url, 
            "status": "in_progress", 
            "scan_mode": "quick" if quick_scan else "comprehensive"
        }
        
        scan_type = 'quick' if quick_scan else 'comprehensive'
        logger.info(f"Starting {scan_type} scan of target: {target_url}")
        
        try:
            # Start ZAP daemon
            if not self._start_zap_daemon():
                error_msg = "Failed to start ZAP daemon"
                logger.error(error_msg)
                return [], {"status": "failed", "error": error_msg}
                
            # Configure and run passive scan
            self._configure_passive_scanning()
            logger.info(f"Accessing target URL: {target_url}")
            self.zap.core.access_url(target_url, followredirects=True)
            logger.info("Initial target access complete")
            time.sleep(2)
            
            # Additional discovery
            self._perform_extended_spidering(target_url)
            logger.info("Checking passive scan status after initial discovery...")
            self._wait_for_passive_scan_completion(max_wait_time=60)
            
            # Traditional spider scan
            logger.info(f"Starting traditional spider scan with maxChildren={self.max_children}")
            spider_id = self.zap.spider.scan(
                url=target_url, 
                maxchildren=self.max_children, 
                recurse=self.scan_recursively
            )
            logger.info(f"Spider scan started with ID: {spider_id}")
            self._monitor_scan_progress(self.zap.spider.status, spider_id, "Spider", interval=2)
            
            # AJAX spider for dynamic content
            if quick_scan:
                logger.info("Quick scan: Performing focused AJAX crawling...")
                self._run_ajax_spider(target_url, focused=True)
            else:
                self._run_ajax_spider(target_url, focused=False)
                
            # Wait for passive scan to process discovered content
            logger.info("Waiting for passive scan to process all discovered content...")
            passive_wait_time = 300 if quick_scan else 600
            self._wait_for_passive_scan_completion(max_wait_time=passive_wait_time)
            
            # Configure and run active scan
            self._configure_active_scanning()
            logger.info("Starting active scan with comprehensive settings...")
            scan_id = self.zap.ascan.scan(
                url=target_url, 
                recurse=self.scan_recursively, 
                inscopeonly=False, 
                scanpolicyname=None, 
                method=None, 
                postdata=True
            )
            
            if not str(scan_id).isdigit():
                error_msg = f"Active scan did not start properly; scan id: {scan_id}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
                
            logger.info(f"Active scan started with ID: {scan_id}")
            self._monitor_scan_progress(self.zap.ascan.status, scan_id, "Active scan", interval=5)
            
            # Final passive scan check
            logger.info("Performing final passive scan check...")
            final_wait_time = 120 if quick_scan else 300
            self._wait_for_passive_scan_completion(max_wait_time=final_wait_time)
            
            # Collect source files for code analysis
            source_files = self._collect_source_files(target_url)
            logger.info(f"Collected {len(source_files)} source files for code analysis")
            
            # Process alerts
            logger.info("Retrieving final scan alerts...")
            alerts = self.zap.core.alerts(baseurl=target_url)
            logger.info(f"Found {len(alerts)} total alerts")
            
            # Track statistics
            risk_counts = {"High": 0, "Medium": 0, "Low": 0, "Info": 0}
            logger.info("Processing alert details and extracting affected code...")
            alert_names = set()
            alert_categories = {}
            
            # Process each alert
            for idx, alert in enumerate(alerts):
                try:
                    risk = alert.get('risk', '')
                    if risk in risk_counts: 
                        risk_counts[risk] += 1
                        
                    name = alert.get('name', alert.get('alert', ''))
                    alert_names.add(name)
                    
                    # Categorize alert
                    category = None
                    for cat_name, keywords in self.active_rule_categories.items():
                        if any(keyword.lower() in name.lower() for keyword in keywords):
                            category = cat_name
                            break
                    if category is None: 
                        category = "Other"
                        
                    if category not in alert_categories: 
                        alert_categories[category] = []
                    alert_categories[category].append(name)
                    
                    # Extract affected code
                    affected_code = self._get_affected_code(alert)
                    source_file = None
                    if affected_code and affected_code.file_path: 
                        source_file = affected_code.file_path
                        
                    # Create vulnerability object
                    vuln = ZapVulnerability(
                        url=alert.get('url', ''), 
                        name=name, 
                        alert=alert.get('alert', ''), 
                        risk=risk, 
                        confidence=alert.get('confidence', ''), 
                        description=alert.get('description', ''), 
                        solution=alert.get('solution', ''), 
                        reference=alert.get('reference', ''), 
                        evidence=alert.get('evidence', ''), 
                        cwe_id=alert.get('cweid', ''), 
                        parameter=alert.get('param', ''), 
                        attack=alert.get('attack', ''), 
                        wascid=alert.get('wascid', ''), 
                        affected_code=affected_code, 
                        source_file=source_file
                    )
                    vulnerabilities.append(vuln)
                    
                    # Log high and medium risk findings
                    if risk in ["High", "Medium"]:
                        log_message = f"[{risk}] {vuln.name} - URL: {vuln.url}"
                        if vuln.parameter: 
                            log_message += f" - Parameter: {vuln.parameter}"
                        if affected_code and affected_code.snippet:
                            log_message += f" - Affected code identified"
                            if affected_code.line_number: 
                                log_message += f" at line {affected_code.line_number}"
                        logger.info(log_message)
                except Exception as e:
                    logger.error(f"Error processing alert #{idx}: {str(e)}")
                    continue
                    
            # Log alert categories
            logger.info("Alert categories summary:")
            for category, alerts_list in alert_categories.items():
                logger.info(f"Category '{category}': {len(alerts_list)} alerts")
                examples = alerts_list[:min(3, len(alerts_list))]
                if examples: 
                    logger.info(f"  Examples: {', '.join(examples)}")
                    
            # Prepare summary
            scan_end_time = datetime.now()
            duration_seconds = int((scan_end_time - scan_start_time).total_seconds())
            logger.info(f"Scan completed in {duration_seconds} seconds ({duration_seconds/60:.1f} minutes)")
            logger.info(f"Risk breakdown: High={risk_counts['High']}, Medium={risk_counts['Medium']}, Low={risk_counts['Low']}, Info={risk_counts['Info']}")
            
            with_code = sum(1 for v in vulnerabilities if v.affected_code and v.affected_code.snippet)
            logger.info(f"Vulnerabilities with affected code identified: {with_code}/{len(vulnerabilities)}")
            
            summary.update({
                "status": "success", 
                "end_time": scan_end_time.isoformat(), 
                "duration_seconds": duration_seconds, 
                "total_alerts": len(vulnerabilities), 
                "risk_counts": risk_counts, 
                "passive_scan_enabled": True, 
                "ajax_spider_enabled": True, 
                "unique_alert_types": len(alert_names), 
                "alert_categories": {k: len(v) for k, v in alert_categories.items()}, 
                "vulnerabilities_with_code": with_code, 
                "browser_configured": self.firefox_binary_path is not None, 
                "oast_service_configured": self.oast_service_configured
            })
            
            return vulnerabilities, summary
        except Exception as e:
            error_msg = f"Scan error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            summary["status"] = "failed"
            summary["error"] = error_msg
            summary["end_time"] = datetime.now().isoformat()
            return [], summary
        finally:
            # Always clean up resources
            logger.info("Cleaning up ZAP resources...")
            self._cleanup_existing_zap()

    @log_operation("Affected code report generation")
    def generate_affected_code_report(self, vulnerabilities: List[ZapVulnerability], output_file: str = None) -> str:
        """Generate a Markdown report of affected code from vulnerability findings."""
        # Group vulnerabilities by risk level
        vuln_by_risk = {"High": [], "Medium": [], "Low": [], "Informational": []}
        for vuln in vulnerabilities:
            risk = vuln.risk
            if risk == "Info": 
                risk = "Informational"
            if risk in vuln_by_risk: 
                vuln_by_risk[risk].append(vuln)
                
        # Create report
        report = ["# Security Vulnerability Report with Affected Code\n"]
        report.append("## Summary\n")
        for risk, vulns in vuln_by_risk.items():
            if vulns: 
                report.append(f"- **{risk}**: {len(vulns)} vulnerabilities\n")
                
        # Add findings by risk level
        for risk in ["High", "Medium", "Low", "Informational"]:
            vulns = vuln_by_risk[risk]
            if not vulns: 
                continue
                
            report.append(f"\n## {risk} Risk Vulnerabilities\n")
            for i, vuln in enumerate(vulns, 1):
                report.append(f"### {i}. {vuln.name}\n")
                report.append(f"- **URL**: {vuln.url}\n")
                if vuln.parameter: 
                    report.append(f"- **Parameter**: {vuln.parameter}\n")
                report.append(f"- **Confidence**: {vuln.confidence}\n")
                report.append(f"- **Description**: {vuln.description}\n")
                report.append(f"- **Solution**: {vuln.solution}\n")
                if vuln.cwe_id: 
                    report.append(f"- **CWE ID**: {vuln.cwe_id}\n")
                    
                # Include affected code if available
                if vuln.affected_code and vuln.affected_code.snippet:
                    code = vuln.affected_code
                    report.append("\n#### Affected Code\n")
                    if code.file_path: 
                        report.append(f"**File**: {code.file_path}\n")
                    if code.line_number: 
                        report.append(f"**Line**: {code.line_number}\n")
                    report.append("\n```\n")
                    
                    # Format code with line numbers if available
                    if code.start_line > 0:
                        lines = code.snippet.split('\n')
                        numbered_lines = []
                        for i_line, line_content in enumerate(lines, code.start_line):
                            line_num_str = f"{i_line:4d} | "
                            if i_line in code.vulnerable_lines: 
                                numbered_lines.append(f"{line_num_str}{line_content}  <-- VULNERABILITY")
                            else: 
                                numbered_lines.append(f"{line_num_str}{line_content}")
                        report.append('\n'.join(numbered_lines))
                    else: 
                        report.append(code.snippet)
                    report.append("\n```\n")
                # Include evidence if no code context is available
                elif vuln.evidence and (not vuln.affected_code or not vuln.affected_code.snippet):
                    report.append("\n#### Evidence\n")
                    report.append("\n```\n")
                    report.append(vuln.evidence)
                    report.append("\n```\n")
                    
                report.append("\n---\n")
                
        report_content = '\n'.join(report)
        
        # Save report to file if requested
        if output_file:
            try:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f: 
                    f.write(report_content)
                logger.info(f"Saved affected code report to: {output_path}")
                
                # Use JsonResultsManager for legacy file links/copies
                if "zap_reports" in str(output_path):
                    path_parts = Path(output_file).parts
                    if len(path_parts) >= 4 and path_parts[-4] == "zap_reports":
                        model = path_parts[-3]
                        app_num_str = path_parts[-2]
                        if app_num_str.startswith("app") and app_num_str[3:].isdigit():
                            app_num = int(app_num_str[3:])
                            
                            # Save the markdown report using JsonResultsManager
                            self.results_manager.save_results(
                                model=model,
                                app_num=app_num,
                                results=report_content,  # Simple string content
                                file_name=".zap_code_report.md",
                                maintain_legacy=True
                            )
                            logger.info(f"Saved code report with JsonResultsManager for {model}/app{app_num}")
            except Exception as e:
                logger.error(f"Error saving report to {output_file}: {str(e)}")
                
        return report_content

    def set_source_code_root(self, root_dir: str):
        """Set the root directory for source code to enable code context in findings."""
        if os.path.isdir(root_dir):
            self.source_root_dir = root_dir
            logger.info(f"Source code root directory set to: {root_dir}")
        else:
            logger.warning(f"Source code root directory not found: {root_dir}")

    @log_operation("ZAP Scan")
    def start_scan(self, model: str, app_num: int, quick_scan: bool = False) -> bool:
        """Start a ZAP scan for a specific app."""
        scan_key = f"{model}-{app_num}"
        scan_status = ScanStatus(start_time=datetime.now().isoformat())
        scan_status.status = "Starting"
        
        # Calculate target URL
        target_url = self._calculate_app_url(model, app_num)
        
        # Set source code root directory
        app_path = self.base_path / f"{model}/app{app_num}"
        if app_path.exists() and app_path.is_dir():
            self.set_source_code_root(str(app_path))
            
        # Initialize scan data
        self._scans[scan_key] = {
            "status": scan_status, 
            "target_url": target_url, 
            "start_time": datetime.now().isoformat(), 
            "quick_scan": quick_scan
        }
        
        scan_type = 'quick' if quick_scan else 'comprehensive'
        logger.info(f"Starting {scan_type} scan {scan_key} for {target_url}")
        
        # Save original AJAX timeout to restore later
        original_ajax_timeout = self.ajax_timeout
        
        try:
            # Adjust timeout for quick scan
            if quick_scan:
                self.ajax_timeout = min(60, self.ajax_timeout)
                logger.info(f"Quick scan enabled - AJAX timeout reduced to {self.ajax_timeout} seconds")
                
            # Update scan status
            scan_status.status = "Running"
            
            # Run the scan
            vulnerabilities, summary = self.scan_target(target_url, quick_scan)
            
            # Save results using JsonResultsManager
            self.save_scan_results(model, app_num, vulnerabilities, summary)
            
            # Update scan status
            scan_status.status = "Complete"
            scan_status.progress = 100
            scan_status.end_time = datetime.now().isoformat()
            scan_status.duration_seconds = summary.get("duration_seconds", 0)
            
            # Update risk counts
            if "risk_counts" in summary:
                scan_status.high_count = summary["risk_counts"]["High"]
                scan_status.medium_count = summary["risk_counts"]["Medium"]
                scan_status.low_count = summary["risk_counts"]["Low"]
                scan_status.info_count = summary["risk_counts"]["Info"]
                
            logger.info(f"Scan {scan_key} completed successfully with {scan_status.high_count} high, {scan_status.medium_count} medium, {scan_status.low_count} low risks")
            return True
        except Exception as e:
            error_msg = f"Scan failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            scan_status.status = f"Failed: {error_msg}"
            scan_status.end_time = datetime.now().isoformat()
            return False
        finally:
            # Restore original Ajax timeout
            self.ajax_timeout = original_ajax_timeout

    def _get_model_index(self, model_name: str) -> int:
        """Get the index of a model in the AI_MODELS list."""
        return next((i for i, m in enumerate(ZAPConfig.AI_MODELS) if m == model_name), 0)

    def stop_scan(self, model: str = None, app_num: int = None) -> bool:
        """Stop a running scan."""
        logger.info(f"Attempting to stop scan for {model}/app{app_num}")
        try:
            if model and app_num:
                scan_key = f"{model}-{app_num}"
                scan_info = self._scans.get(scan_key)
                if scan_info and scan_info.get("status", {}).status == "Running":
                    logger.info(f"Stopping specific scan for {scan_key}")
                    scan_info["status"].status = "Stopped"
                    scan_info["status"].end_time = datetime.now().isoformat()
            self._cleanup_existing_zap()
            logger.info("ZAP resources cleaned up")
            return True
        except Exception as e:
            logger.error(f"Error stopping scan: {str(e)}", exc_info=True)
            return False


def create_scanner(base_path: Path) -> ZAPScanner:
    """Factory function to create and initialize a ZAP scanner."""
    logger.info("Creating comprehensive ZAP scanner instance...")
    
    # Check Java installation first
    try:
        java_version = subprocess.check_output(['java', '-version'], stderr=subprocess.STDOUT, text=True)
        logger.info(f"Found Java: {java_version.splitlines()[0]}")
    except Exception as e:
        error_msg = "Java runtime not found. Install Java 11+ and ensure it's in PATH."
        logger.error(f"{error_msg} Error: {str(e)}")
        raise RuntimeError(error_msg) from e
    
    # Create the scanner
    scanner = ZAPScanner(base_path)
    logger.info(f"Comprehensive ZAP scanner created with base path: {base_path}")
    return scanner


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("zap_scanner.log")
        ]
    )
    
    try:
        base_path = Path("./zap_output")
        scanner = create_scanner(base_path)
        target_url = "http://localhost:8080"
        logger.info(f"Scanning target: {target_url}")
        vulnerabilities, summary = scanner.scan_target(target_url)
        report_file = base_path / "vulnerability_report.md"
        scanner.generate_affected_code_report(vulnerabilities, str(report_file))
        logger.info(f"Scan complete. Found {len(vulnerabilities)} vulnerabilities.")
        logger.info(f"Report saved to {report_file}")
    except Exception as e:
        logger.error(f"Error running scanner: {str(e)}", exc_info=True)