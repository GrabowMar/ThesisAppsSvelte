import json
import time
import logging
import os
import subprocess
import socket
import re
import requests
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Any
from contextlib import contextmanager

from zapv2 import ZAPv2


# Configure comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("zap_scanner")
# Add file handler for persistent logs
file_handler = logging.FileHandler("zap_scanner.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

@dataclass
class CodeContext:
    """Represents source code context around vulnerable code"""
    snippet: str
    line_number: Optional[int] = None
    file_path: Optional[str] = None
    start_line: int = 0
    end_line: int = 0
    vulnerable_lines: List[int] = field(default_factory=list)
    highlight_positions: List[Tuple[int, int]] = field(default_factory=list)  # [(start, end), ...]

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

class ZAPScanner:
    """
    A comprehensive ZAP wrapper that performs thorough security scanning with all available rules.
    """

    def __init__(self, base_path: Path):
        """
        Initialize the ZAPScanner with the base directory for logs and temporary files.
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Fixed configuration for railroaded operation
        self.api_key = os.getenv('ZAP_API_KEY', '5tjkc409k4oaacd69qob5p6uri')
        self.proxy_host = "127.0.0.1"
        self.proxy_port = self._find_free_port()
        self.zap_log = self.base_path / "zap.log"
        self.zap: Optional[ZAPv2] = None
        self.daemon_process: Optional[subprocess.Popen] = None
        self._scans: Dict[str, Dict] = {}
        
        # Optimized scan configuration
        self.max_children = 30                 # Increased max children for spider
        self.scan_recursively = True           # Always scan recursively
        self.max_scan_duration_minutes = 120   # Cap scan duration at 120 minutes
        self.thread_per_host = 8               # Optimized thread count
        self.ajax_timeout = 600                # AJAX spider timeout in seconds
        
        # ZAP scan rule categories to track
        self.active_rule_categories = {
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
        
        # Source code mapping configuration
        self.source_code_mapping = {}  # Maps URL paths to local source files
        self.source_root_dir = None    # Root directory for source code
        self.source_file_extensions = ['.js', '.jsx', '.ts', '.tsx', '.php', '.py', '.java', '.html', '.css']
        
        logger.info(f"ZAPScanner initialized with base path: {self.base_path}")
        logger.info(f"ZAP proxy configuration: {self.proxy_host}:{self.proxy_port}")

    # ---------------- Utility Methods ----------------

    @contextmanager
    def _port_check(self, port: int):
        """
        Context manager to check if a port is free.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('127.0.0.1', port))
            sock.listen(1)
            yield sock
        finally:
            sock.close()

    def _find_free_port(self, start_port: int = 8090, max_port: int = 8099) -> int:
        """
        Find and return a free port in the specified range.
        """
        logger.debug(f"Searching for free port between {start_port} and {max_port}...")
        for port in range(start_port, max_port + 1):
            try:
                with self._port_check(port):
                    logger.info(f"Found free port: {port}")
                    return port
            except OSError:
                logger.debug(f"Port {port} is busy, trying next...")
                continue
        error_msg = f"No free ports found between {start_port} and {max_port}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    def _find_zap_installation(self) -> Path:
        """
        Locate the ZAP installation and return the path to the executable or JAR file.
        """
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
            # Check for a jar file first
            jar_files = list(path.glob("zap*.jar"))
            if jar_files:
                logger.info(f"Found ZAP JAR at: {jar_files[0]}")
                return jar_files[0]
            # Check for an executable file
            for exe in ["zap.bat", "zap.sh", "zap.exe"]:
                exe_path = path / exe
                if exe_path.exists():
                    logger.info(f"Found ZAP executable at: {exe_path}")
                    return exe_path
        error_msg = "ZAP installation not found. Please install ZAP and set ZAP_HOME environment variable."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    def _build_zap_command(self, zap_path: Path) -> List[str]:
        """
        Build the command list to start the ZAP daemon with optimized settings for full coverage.
        """
        # Optimize JVM settings for better performance
        java_opts = [
            '-Xmx4G',  # Increased heap size for better performance with many rules
            f'-Djava.io.tmpdir={self.base_path / "tmp"}',
            '-Djava.net.preferIPv4Stack=true',
            # Additional JVM options for better performance
            '-XX:+UseG1GC',                     # Use G1 garbage collector
            '-XX:MaxGCPauseMillis=100',         # Target for max GC pause time
            '-XX:+UseStringDeduplication',      # Deduplicate strings for memory efficiency
        ]
        
        # Enhanced ZAP configuration for comprehensive scanning
        zap_args = [
            '-daemon',
            '-port', str(self.proxy_port),
            '-host', self.proxy_host,
            '-config', f'api.key={self.api_key}',
            '-config', 'api.addrs.addr.name=.*',
            '-config', 'api.addrs.addr.regex=true',
            '-config', 'connection.timeoutInSecs=1200',     # 20 minutes timeout
            '-config', f'ascan.maxScanDurationInMins={self.max_scan_duration_minutes}',
            '-config', f'ascan.threadPerHost={self.thread_per_host}',
            '-config', 'view.mode=standard',                # Always use standard mode for scans
            '-config', 'ascan.attackStrength=HIGH',         # Set to HIGH for more thorough scanning
            '-config', 'ascan.alertThreshold=LOW',          # Set to LOW to catch more issues
            '-config', 'pscan.maxAlertsPerRule=0',          # No limit on passive scan alerts
            '-config', 'pscan.maxBodySizeInBytes=10000000', # 10MB body size limit
            
            # Ajax spider configurations
            '-config', 'ajaxSpider.browserId=chrome-headless',
            '-config', f'ajaxSpider.maxDuration={self.ajax_timeout}',
            '-config', 'ajaxSpider.clickDefaultElems=true',
            '-config', 'ajaxSpider.clickElemsOnce=false',
            '-config', 'ajaxSpider.eventWait=2000',
            '-config', 'ajaxSpider.maxCrawlDepth=10',
            '-config', 'ajaxSpider.maxCrawlStates=0',  # No limit
            '-config', 'ajaxSpider.numberOfBrowsers=4',
            '-config', 'ajaxSpider.randomInputs=true',
            
            # Ensure all key passive scanners are enabled
            '-config', 'pscans.pscanner(10020).enabled=true',  # Missing Anti-Clickjacking Header
            '-config', 'pscans.pscanner(10020).alertThreshold=LOW',
            '-config', 'pscans.pscanner(10021).enabled=true',  # X-Content-Type-Options Header
            '-config', 'pscans.pscanner(10021).alertThreshold=LOW',
            '-config', 'pscans.pscanner(10038).enabled=true',  # Content Security Policy Header
            '-config', 'pscans.pscanner(10038).alertThreshold=LOW',
            '-config', 'pscans.pscanner(10035).enabled=true',  # Strict-Transport-Security Header
            '-config', 'pscans.pscanner(10035).alertThreshold=LOW',
            '-config', 'pscans.pscanner(10063).enabled=true',  # Permissions Policy Header
            '-config', 'pscans.pscanner(10063).alertThreshold=LOW',
            '-config', 'pscans.pscanner(10054).enabled=true',  # Cookie Without SameSite
            '-config', 'pscans.pscanner(10054).alertThreshold=LOW',
            
            # Information disclosure scanners
            '-config', 'pscans.pscanner(10024).enabled=true',  # Sensitive Info in URL
            '-config', 'pscans.pscanner(10024).alertThreshold=LOW',
            '-config', 'pscans.pscanner(10025).enabled=true',  # Sensitive Info in Referrer
            '-config', 'pscans.pscanner(10025).alertThreshold=LOW',
            '-config', 'pscans.pscanner(10027).enabled=true',  # Suspicious Comments
            '-config', 'pscans.pscanner(10027).alertThreshold=LOW',
            '-config', 'pscans.pscanner(10096).enabled=true',  # Timestamp Disclosure
            '-config', 'pscans.pscanner(10096).alertThreshold=LOW',
            '-config', 'pscans.pscanner(10097).enabled=true',  # Hash Disclosure
            '-config', 'pscans.pscanner(10097).alertThreshold=LOW',
            '-config', 'pscans.pscanner(10094).enabled=true',  # Base64 Disclosure
            '-config', 'pscans.pscanner(10094).alertThreshold=LOW',
            
            # Application errors
            '-config', 'pscans.pscanner(90022).enabled=true',  # Application Error
            '-config', 'pscans.pscanner(90022).alertThreshold=LOW',
            
            # Modern web app detection
            '-config', 'pscans.pscanner(10109).enabled=true',  # Modern Web Application
            '-config', 'pscans.pscanner(10109).alertThreshold=LOW',
            
            # Dangerous functions
            '-config', 'pscans.pscanner(10110).enabled=true',  # Dangerous JS Functions
            '-config', 'pscans.pscanner(10110).alertThreshold=LOW',
            
            # Security configurations
            '-config', 'ascan.attackStrength=HIGH',         # HIGH attack strength
            '-config', 'ascan.alertThreshold=LOW',          # LOW alert threshold
        ]

        logger.debug(f"Building ZAP command with optimized settings for comprehensive scanning")
        if zap_path.suffix == '.jar':
            return ['java'] + java_opts + ['-jar', str(zap_path)] + zap_args
        return [str(zap_path)] + zap_args

    # --------------- Source Code Mapping Methods ---------------

    def set_source_code_mapping(self, mapping: Dict[str, str], root_dir: Optional[str] = None):
        """
        Set the mapping between URL paths and local source code file paths.
        
        Args:
            mapping: Dict mapping URL paths to local file paths
            root_dir: Optional root directory for source code
        """
        self.source_code_mapping = mapping
        self.source_root_dir = root_dir
        logger.info(f"Set source code mapping with {len(mapping)} entries")
        if root_dir:
            logger.info(f"Source code root directory: {root_dir}")
    
    def _url_to_source_file(self, url: str) -> Optional[str]:
        """
        Convert a URL to a local source file path if possible.
        """
        if not self.source_code_mapping and not self.source_root_dir:
            return None
            
        # Try direct mapping first
        for url_prefix, file_path in self.source_code_mapping.items():
            if url.startswith(url_prefix):
                relative_path = url[len(url_prefix):]
                return os.path.join(file_path, relative_path)
                
        # If no direct mapping and we have a root directory, try to infer
        if self.source_root_dir:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                path = parsed.path
                
                # Remove leading slash and query/fragments
                if path.startswith('/'):
                    path = path[1:]
                    
                # Try different possibilities
                possibilities = [
                    os.path.join(self.source_root_dir, path),
                    os.path.join(self.source_root_dir, 'src', path),
                    os.path.join(self.source_root_dir, 'public', path)
                ]
                
                # Try each possibility with each extension
                for possibility in possibilities:
                    # If the file exists directly
                    if os.path.isfile(possibility):
                        return possibility
                        
                    # Try with different extensions if needed
                    base_path, ext = os.path.splitext(possibility)
                    if not ext:
                        for extension in self.source_file_extensions:
                            if os.path.isfile(f"{base_path}{extension}"):
                                return f"{base_path}{extension}"
            except Exception as e:
                logger.debug(f"Error inferring source file from URL {url}: {str(e)}")
                
        return None

    def _fetch_source_from_url(self, url: str) -> Optional[str]:
        """
        Attempts to fetch source code directly from the URL if it's a static file.
        """
        try:
            # Check if it's likely a static file
            if any(url.endswith(ext) for ext in ['.js', '.html', '.css', '.tsx', '.ts', '.jsx']):
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    return response.text
        except Exception as e:
            logger.debug(f"Error fetching source from URL {url}: {str(e)}")
        return None

    def _get_affected_code(self, alert: Dict[str, Any]) -> Optional[CodeContext]:
        """
        Extracts affected code context from an alert if possible.
        """
        url = alert.get('url', '')
        evidence = alert.get('evidence', '')
        
        if not evidence or not url:
            return None
            
        # Try to get source code from local file or by fetching URL
        source_file = self._url_to_source_file(url)
        source_code = None
        
        if source_file and os.path.isfile(source_file):
            try:
                with open(source_file, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                logger.debug(f"Loaded source code from: {source_file}")
            except Exception as e:
                logger.debug(f"Error reading source file {source_file}: {str(e)}")
        
        if not source_code:
            # Try to fetch source from URL if it's a static file
            source_code = self._fetch_source_from_url(url)
            if source_code:
                logger.debug(f"Fetched source code from URL: {url}")
        
        if not source_code:
            # If we still don't have source, try to extract from response
            try:
                # Use correct ZAP API methods to get messages
                messages = []
                try:
                    # Get messages using the correct API method
                    if hasattr(self.zap.core, 'messages'):
                        # Use the messages method with baseurl parameter
                        messages = self.zap.core.messages(baseurl=url)
                        logger.debug(f"Found {len(messages)} messages for URL: {url}")
                except Exception as e:
                    logger.debug(f"Error getting messages for URL {url}: {str(e)}")
                
                # Process messages to find evidence
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
                            # Fetch full message details if we only have IDs
                            try:
                                full_message = self.zap.core.message(message_id)
                                if full_message and 'responseBody' in full_message:
                                    response_body = full_message.get('responseBody', '')
                                    if evidence in response_body:
                                        source_code = response_body
                                        logger.debug(f"Found evidence in message ID {message_id}")
                                        break
                            except Exception as e:
                                logger.debug(f"Error retrieving message {message_id}: {str(e)}")
            except Exception as e:
                logger.debug(f"Error trying to extract source from ZAP messages: {str(e)}")
        
        if not source_code:
            logger.debug(f"No source code available for URL: {url}")
            # Create minimal code context with just the evidence
            if evidence:
                return CodeContext(
                    snippet=evidence,
                    line_number=None,
                    file_path=source_file,
                    highlight_positions=[(0, len(evidence))]
                )
            return None
            
        # Find evidence in source code and extract context
        try:
            # Escape regex special characters in evidence
            pattern = re.escape(evidence)
            matches = list(re.finditer(pattern, source_code))
            
            if not matches:
                logger.debug(f"Evidence not found in source code for URL: {url}")
                # Create context with just the evidence
                return CodeContext(
                    snippet=evidence,
                    line_number=None,
                    file_path=source_file,
                    highlight_positions=[(0, len(evidence))]
                )
            
            # Take the first match for simplicity
            match = matches[0]
            start_pos, end_pos = match.span()
            
            # Find line number
            line_number = source_code[:start_pos].count('\n') + 1
            
            # Extract contextual lines (5 before and after)
            lines = source_code.splitlines()
            start_line = max(0, line_number - 6)
            end_line = min(len(lines), line_number + 5)
            
            context_lines = lines[start_line:end_line]
            context_snippet = '\n'.join(context_lines)
            
            # Calculate positions for highlighting in the context
            # First, find the start position in the context
            if start_line > 0:
                # Adjust for removed lines
                prefix_length = len('\n'.join(lines[:start_line])) + 1  # +1 for the newline
                adjusted_start = start_pos - prefix_length
                adjusted_end = end_pos - prefix_length
            else:
                adjusted_start = start_pos
                adjusted_end = end_pos
                
            # Ensure positions are within bounds
            adjusted_start = max(0, adjusted_start)
            adjusted_end = min(len(context_snippet), adjusted_end)
            
            return CodeContext(
                snippet=context_snippet,
                line_number=line_number,
                file_path=source_file,
                start_line=start_line + 1,  # 1-based line numbering
                end_line=end_line,
                vulnerable_lines=[line_number],
                highlight_positions=[(adjusted_start, adjusted_end)]
            )
            
        except Exception as e:
            logger.debug(f"Error extracting code context: {str(e)}")
            # Fallback to just showing the evidence
            return CodeContext(
                snippet=evidence,
                line_number=None,
                file_path=source_file,
                highlight_positions=[(0, len(evidence))]
            )

    # --------------- ZAP Process Management ---------------

    def _cleanup_existing_zap(self):
        """
        Terminate any existing ZAP processes to ensure a clean start.
        """
        logger.info("Cleaning up any existing ZAP processes...")
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
            
            # Kill any stray processes
            if os.name == 'nt':
                logger.debug("Attempting to kill stray ZAP processes on Windows...")
                for proc in ['java.exe', 'zap.exe']:
                    result = subprocess.run(['taskkill', '/f', '/im', proc], capture_output=True, check=False)
                    logger.debug(f"Taskkill result for {proc}: {result.returncode}")
            else:
                logger.debug("Attempting to kill stray ZAP processes on Unix...")
                result = subprocess.run(['pkill', '-f', 'zap.jar'], capture_output=True, check=False)
                logger.debug(f"pkill result: {result.returncode}")
            
            # Allow time for processes to fully terminate
            time.sleep(5)
            logger.info("ZAP process cleanup complete")
        except Exception as e:
            logger.warning(f"Error during ZAP cleanup: {str(e)}")

    def _start_zap_daemon(self) -> bool:
        """
        Start the ZAP daemon and connect to it, with enhanced logging.
        """
        start_time = datetime.now()
        logger.info("Starting ZAP daemon...")
        try:
            self._cleanup_existing_zap()
            
            # Create the tmp directory
            tmp_dir = self.base_path / "tmp"
            tmp_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created temporary directory: {tmp_dir}")
            
            # Find and verify ZAP installation
            zap_path = self._find_zap_installation()
            if not zap_path.exists():
                error_msg = f"ZAP not found at {zap_path}"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
                
            # Build and execute the ZAP command
            cmd = self._build_zap_command(zap_path)
            logger.info(f"Starting ZAP with command: {' '.join(cmd)}")
            
            # Open log file for ZAP output
            log_file = open(self.zap_log, 'w')
            logger.debug(f"ZAP log will be written to: {self.zap_log}")
            
            # Start the ZAP process
            self.daemon_process = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            logger.debug(f"ZAP process started with PID: {self.daemon_process.pid}")
            
            # Wait for ZAP to initialize
            logger.info("Waiting for ZAP to initialize (15 seconds)...")
            time.sleep(15)
            
            # Check if ZAP is still running
            if self.daemon_process.poll() is not None:
                with open(self.zap_log, 'r') as f:
                    error_log = f.read()
                error_msg = f"ZAP failed to start. Exit code: {self.daemon_process.returncode}\nLog excerpt:\n{error_log[-2000:]}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)

            # Attempt to connect to the ZAP API
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
                    
                    # Log time taken to start ZAP
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

    # ---------------- Scanning Methods ----------------

    def _monitor_scan_progress(self, status_func, scan_id: str, scan_type: str, interval: int = 5):
        """
        Monitor the scan progress until it reaches 100% with enhanced logging.
        """
        logger.info(f"Monitoring {scan_type} progress for scan ID: {scan_id}")
        start_time = datetime.now()
        last_logged_progress = -1
        
        while True:
            try:
                progress = int(status_func(scan_id))
                elapsed = (datetime.now() - start_time).total_seconds()
                
                # Only log if progress changed or every 30 seconds
                if progress != last_logged_progress or elapsed % 30 < interval:
                    logger.info(f"{scan_type} progress: {progress}% (elapsed: {elapsed:.1f}s)")
                    last_logged_progress = progress
                
                if progress >= 100:
                    logger.info(f"{scan_type} scan completed in {elapsed:.1f} seconds")
                    break
                    
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error monitoring {scan_type} progress: {str(e)}")
                raise

    def _monitor_ajax_spider_until_complete(self, interval: int = 5, max_time: int = 900):
        """
        Monitor AJAX Spider until it's stopped.
        """
        logger.info("Monitoring AJAX Spider progress...")
        start_time = datetime.now()
        
        while True:
            try:
                status = self.zap.ajaxSpider.status
                elapsed = (datetime.now() - start_time).total_seconds()
                
                # Calculate a pseudo-progress percentage based on time
                progress_percent = min(int((elapsed / max_time) * 100), 99)
                
                if status == "running":
                    logger.info(f"AJAX Spider is running... (estimated progress: {progress_percent}%, elapsed: {elapsed:.1f}s)")
                else:
                    logger.info(f"AJAX Spider completed with status: {status} (elapsed: {elapsed:.1f}s)")
                    # Get the result count
                    result_count = len(self.zap.ajaxSpider.results())
                    logger.info(f"AJAX Spider found {result_count} results")
                    break
                
                # Check if we've exceeded the maximum time
                if elapsed > max_time:
                    logger.warning(f"AJAX Spider exceeded maximum time of {max_time} seconds. Stopping...")
                    self.zap.ajaxSpider.stop()
                    break
                
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error monitoring AJAX Spider: {str(e)}")
                try:
                    self.zap.ajaxSpider.stop()
                except:
                    pass
                break

    def _wait_for_passive_scan_completion(self, max_wait_time: int = 300):
        """
        Wait for passive scan to complete with progress monitoring and enhanced logging.
        Makes sure all passive scan rules are processed completely.
        """
        logger.info("Waiting for passive scan to complete...")
        start_time = datetime.now()
        max_wait_seconds = max_wait_time
        last_records = -1
        
        try:
            # Monitor passive scan progress
            while True:
                records_to_scan = int(self.zap.pscan.records_to_scan)
                elapsed = (datetime.now() - start_time).total_seconds()
                
                # Only log if records changed or every 30 seconds
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

    def _configure_passive_scanning(self):
        """
        Configure passive scanning to detect all security issues including missing headers and information disclosure.
        """
        logger.info("Configuring comprehensive passive scanning...")
        
        try:
            # Enable all passive scanners
            logger.info("Enabling ALL passive scanners...")
            self.zap.pscan.enable_all_scanners()
            
            # Set scan only in scope to false to scan everything
            logger.info("Setting passive scan to analyze ALL traffic (not just in-scope)...")
            self.zap.pscan.set_scan_only_in_scope(False)
            
            # Set alert threshold to LOW for all scanners to catch more issues
            logger.info("Setting LOW alert threshold for all passive scanners to increase detection rate...")
            scanners = self.zap.pscan.scanners
            for scanner in scanners:
                scanner_id = scanner.get('id')
                self.zap.pscan.set_scanner_alert_threshold(scanner_id, "LOW")
            
            # Increase maximum alerts per rule to ensure no alerts are missed
            logger.info("Setting unlimited maximum alerts per rule...")
            self.zap.pscan.set_max_alerts_per_rule(0)  # 0 = unlimited
            
            # Log enabled scanners for debugging
            enabled_count = 0
            for scanner in scanners:
                if scanner.get('enabled') == 'true':
                    enabled_count += 1
                    logger.debug(f" - {scanner.get('id')}: {scanner.get('name')}")
            
            logger.info(f"Passive scanning fully configured with {enabled_count} enabled scanners.")
        except Exception as e:
            logger.error(f"Error configuring passive scanning: {str(e)}")
            raise

    def _configure_active_scanning(self):
        """
        Configure active scanning to use all available scan rules.
        """
        logger.info("Configuring comprehensive active scanning...")
        
        try:
            # Enable all active scanners
            logger.info("Enabling ALL active scanners...")
            self.zap.ascan.enable_all_scanners()
            
            # Set HIGH attack strength for all policies
            logger.info("Setting HIGH attack strength for all policies...")
            for policy_id in range(0, 5):  # There are 5 policies (0-4)
                self.zap.ascan.set_policy_attack_strength(id=policy_id, attackstrength="HIGH")
            
            # Set LOW alert threshold for all policies to catch more issues
            logger.info("Setting LOW alert threshold for all policies...")
            for policy_id in range(0, 5):
                self.zap.ascan.set_policy_alert_threshold(id=policy_id, alertthreshold="LOW")
            
            # Configure scan policy options
            logger.info("Configuring scan policy options...")
            self.zap.ascan.set_option_handle_anti_csrf_tokens(True)
            self.zap.ascan.set_option_scan_headers_all_requests(True)
            self.zap.ascan.set_option_add_query_param(True)
            self.zap.ascan.set_option_scan_null_json_values(True)
            self.zap.ascan.set_option_inject_plugin_id_in_header(True)
            self.zap.ascan.set_option_max_alerts_per_rule(0)  # Unlimited
            self.zap.ascan.set_option_max_rule_duration_in_mins(5)  # 5 minutes max per rule
            self.zap.ascan.set_option_max_scan_duration_in_mins(self.max_scan_duration_minutes)
            self.zap.ascan.set_option_thread_per_host(self.thread_per_host)
            
            # Log active scanners for debugging
            scanners = self.zap.ascan.scanners()
            enabled_count = 0
            
            # Group by category for better overview
            category_counts = {}
            for scanner in scanners:
                if scanner.get('enabled') == 'true':
                    enabled_count += 1
                    category = scanner.get('category', 'Other')
                    if category not in category_counts:
                        category_counts[category] = 0
                    category_counts[category] += 1
            
            # Log counts by category
            for category, count in category_counts.items():
                logger.info(f"Enabled {count} active scanners in category: {category}")
            
            logger.info(f"Active scanning fully configured with {enabled_count} enabled scanners")
        except Exception as e:
            logger.error(f"Error configuring active scanning: {str(e)}")
            raise

    def _perform_extended_spidering(self, target_url: str):
        """
        Perform extended spidering to discover more content.
        This includes checking common files and directories.
        """
        logger.info("Performing extended spidering...")
        
        # List of common files/paths to check - extended with more popular URLs
        common_paths = [
            # Common files
            "/robots.txt",
            "/sitemap.xml",
            "/.well-known/security.txt",
            "/crossdomain.xml",
            "/clientaccesspolicy.xml",
            "/manifest.json",
            "/package.json",
            "/humans.txt",
            
            # Application paths
            "/login",
            "/register",
            "/signup",
            "/signin",
            "/join",
            "/auth",
            "/authentication",
            "/account",
            "/profile",
            "/user",
            "/admin",
            "/administrator",
            "/backend",
            "/manage",
            "/management",
            "/control",
            "/dashboard",
            "/cp",
            "/portal",
            
            # API paths
            "/api",
            "/api/v1",
            "/api/v2",
            "/api/docs",
            "/swagger",
            "/swagger-ui",
            "/swagger-ui.html",
            "/graphql",
            "/graphiql",
            "/playground",
            
            # Documentation
            "/docs",
            "/documentation",
            "/help",
            "/manual",
            "/guide",
            "/tutorial",
            "/readme",
            "/changelog",
            "/license",
            
            # Common application directories
            "/js/",
            "/javascript/",
            "/css/",
            "/styles/",
            "/images/",
            "/img/",
            "/media/",
            "/assets/",
            "/static/",
            "/public/",
            "/dist/",
            "/build/",
            "/uploads/",
            "/files/",
            "/downloads/",
            "/vendor/",
            "/lib/",
            "/libs/",
            "/node_modules/",
            "/components/",
            "/plugins/",
            "/modules/",
            "/themes/",
            "/templates/",
            
            # Common config files and dev artifacts
            "/.git/",
            "/.svn/",
            "/.env",
            "/.editorconfig",
            "/.gitignore",
            "/.npmrc",
            "/config.js",
            "/config.php",
            "/config.json",
            "/settings.json",
            "/web.config",
            "/server.xml",
            "/composer.json",
            
            # Debug/info endpoints
            "/phpinfo.php",
            "/info.php",
            "/server-status",
            "/server-info",
            "/test",
            "/test.php",
            "/test.html",
            "/debug",
            "/status",
            "/health",
            "/metrics",
            
            # WordPress specific
            "/wp-login.php",
            "/wp-admin/",
            "/wp-config.php",
            "/wp-content/",
            "/wp-includes/",
            
            # Spring Boot
            "/actuator",
            "/actuator/health",
            "/actuator/info",
            "/actuator/metrics",
            "/actuator/env",
            "/actuator/heapdump",
            "/actuator/trace",
            
            # .Net / ASP
            "/web.config",
            "/elmah.axd",
            "/trace.axd",
            "/app_data",
            
            # Java
            "/WEB-INF/web.xml",
            "/META-INF/",
            "/console/",
            
            # Misc
            "/backup/",
            "/bak/",
            "/old/",
            "/dev/",
            "/temp/",
            "/tmp/",
            "/private/",
            "/archive/",
            
            # Error pages
            "/404",
            "/500",
            "/403",
            "/error",
            
            # Cloud metadata endpoints
            "/.aws/",
            "/.azure/",
            "/.gcp/",
            "/.well-known/",
            
            # Popular JavaScript frameworks
            "/angular/",
            "/react/",
            "/vue/",
            "/svelte/",
            "/app/",
            "/src/",
            
            # Auth related
            "/oauth/",
            "/auth/",
            "/sso/",
            "/logout",
            "/reset-password",
            "/forgot-password",
            "/verify",
            "/activate",
            
            # Shopping carts/ecommerce
            "/cart",
            "/checkout",
            "/order",
            "/shop",
            "/store",
            "/catalog",
            "/product",
            "/category",
            
            # Contact/support
            "/contact",
            "/support",
            "/feedback",
            "/about",
            "/faq",
            
            # Social media
            "/share",
            "/social",
            "/connect",
            "/follow",
            
            # User content
            "/comments",
            "/reviews",
            "/ratings",
            "/forum",
            "/blog",
            "/news",
            "/events",
            
            # Search related
            "/search",
            "/query",
            "/find",
            "/results",
            
            # Mobile
            "/mobile",
            "/m/",
            "/app/",
            "/api/mobile",
            
            # Common file extensions
            "/.json",
            "/.xml",
            "/.yaml",
            "/.yml",
            "/.csv",
            "/.log",
            "/.bak",
            "/.txt",
            "/.sql",
            "/.config",
            "/.sample",
            "/.example",
            "/.old",
            "/.zip",
            "/.tar.gz"
        ]
        
        base_url = target_url.rstrip("/")
        for path in common_paths:
            try:
                url = f"{base_url}{path}"
                logger.debug(f"Accessing: {url}")
                self.zap.core.access_url(url, followredirects=True)
                # Short delay to not overload server
                time.sleep(0.3)
            except Exception as e:
                logger.debug(f"Error accessing {url}: {str(e)}")
    
        logger.info("Extended spidering completed")

    def _run_ajax_spider(self, target_url: str):
        """
        Run the AJAX Spider to discover JavaScript-rendered content.
        """
        logger.info("Starting AJAX Spider for JavaScript-rendered content...")
        
        try:
            # Stop any running AJAX spider
            try:
                current_status = self.zap.ajaxSpider.status
                if current_status == "running":
                    logger.info("Stopping previously running AJAX Spider...")
                    self.zap.ajaxSpider.stop()
                    time.sleep(2)
            except Exception as e:
                logger.warning(f"Error checking AJAX Spider status: {str(e)}")
            
            # Start AJAX Spider with optimized settings
            logger.info(f"Running AJAX Spider on target: {target_url}")
            result = self.zap.ajaxSpider.scan(
                url=target_url,
                inscope=None,          # Spider everything, not just in-scope URLs
                contextname=None,      # No context restrictions
                subtreeonly=None       # Don't restrict to subtree
            )
            
            logger.info(f"AJAX Spider started: {result}")
            
            # Monitor until complete
            self._monitor_ajax_spider_until_complete(interval=5, max_time=self.ajax_timeout)
            
            # Get results count
            results = self.zap.ajaxSpider.results()
            logger.info(f"AJAX Spider completed with {len(results)} URLs discovered")
            
            # Log a sample of discovered URLs
            if results:
                logger.info("Sample of AJAX-discovered URLs:")
                for url in results[:min(5, len(results))]:
                    logger.info(f" - {url.get('url', 'Unknown URL')}")
            
            return True
        except Exception as e:
            logger.error(f"Error running AJAX Spider: {str(e)}")
            try:
                self.zap.ajaxSpider.stop()
            except:
                pass
            return False

    def _collect_source_files(self, target_url: str):
        """
        Attempt to identify and collect source files after scanning.
        """
        logger.info("Collecting source files for code analysis...")
        collected_files = {}
        
        # Use ZAP messages to get responses that might contain source code
        if hasattr(self.zap, 'core') and hasattr(self.zap.core, 'messages'):
            try:
                # Get all messages matching target URL
                messages = self.zap.core.messages(baseurl=target_url)
                
                # Identify potential source files from responses
                for message in messages:
                    url = message.get('url', '')
                    if not url:
                        continue
                        
                    # Look for known source file extensions
                    if any(url.endswith(ext) for ext in self.source_file_extensions):
                        message_id = message.get('id')
                        
                        if message_id:
                            try:
                                # Get full message content
                                full_message = self.zap.core.message(message_id)
                                
                                if full_message and 'responseBody' in full_message:
                                    # Store source code with URL as key
                                    logger.debug(f"Collected source from URL: {url}")
                                    collected_files[url] = full_message['responseBody']
                            except Exception as e:
                                logger.debug(f"Error retrieving message {message_id}: {str(e)}")
            except Exception as e:
                logger.warning(f"Error collecting source files: {str(e)}")
        
        logger.info(f"Collected {len(collected_files)} potential source files for analysis")
        return collected_files

    def scan_target(self, target_url: str) -> Tuple[List[ZapVulnerability], Dict]:
        """
        Comprehensive scan of the target URL using ZAP with enhanced passive and active scanning.
        Returns a list of vulnerabilities and a summary.
        """
        scan_start_time = datetime.now()
        vulnerabilities: List[ZapVulnerability] = []
        summary: Dict = {
            "start_time": scan_start_time.isoformat(),
            "target_url": target_url,
            "status": "in_progress"
        }
        
        logger.info(f"Starting comprehensive scan of target: {target_url}")
        
        try:
            # Start ZAP daemon with increased heap size
            if not self._start_zap_daemon():
                error_msg = "Failed to start ZAP daemon"
                logger.error(error_msg)
                return [], {"status": "failed", "error": error_msg}
            
            # Configure enhanced passive scanning
            self._configure_passive_scanning()
            
            # Access the target to ensure it's in the site tree
            logger.info(f"Accessing target URL: {target_url}")
            self.zap.core.access_url(target_url, followredirects=True)
            logger.info("Initial target access complete")
            time.sleep(2)  # Allow time for the site to be added to the tree
            
            # Perform extended spidering to discover common files/directories
            self._perform_extended_spidering(target_url)
            
            # First passive scan check after initial discovery
            logger.info("Checking passive scan status after initial discovery...")
            self._wait_for_passive_scan_completion(max_wait_time=60)
            
            # Run traditional spider
            logger.info(f"Starting traditional spider scan with maxChildren={self.max_children}")
            spider_id = self.zap.spider.scan(url=target_url, maxchildren=self.max_children, recurse=self.scan_recursively)
            logger.info(f"Spider scan started with ID: {spider_id}")
            self._monitor_scan_progress(self.zap.spider.status, spider_id, "Spider", interval=2)
            
            # Run AJAX Spider to find JavaScript-rendered content
            self._run_ajax_spider(target_url)
            
            # Wait for passive scan to process all discovered content
            logger.info("Waiting for passive scan to process all discovered content...")
            self._wait_for_passive_scan_completion(max_wait_time=600)  # 10 minutes timeout
            
            # Configure and run active scanning
            self._configure_active_scanning()
            
            # Start active scan with optimal configuration
            logger.info("Starting active scan with comprehensive settings...")
            scan_id = self.zap.ascan.scan(
                url=target_url,
                recurse=self.scan_recursively,
                inscopeonly=False,
                scanpolicyname=None,  # Using default policy with all scanners enabled
                method=None,
                postdata=True  # Scan POST data as well
            )
            
            if not str(scan_id).isdigit():
                error_msg = f"Active scan did not start properly; scan id: {scan_id}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
                
            logger.info(f"Active scan started with ID: {scan_id}")
            self._monitor_scan_progress(self.zap.ascan.status, scan_id, "Active scan", interval=5)
            
            # Final passive scan wait
            logger.info("Performing final passive scan check...")
            self._wait_for_passive_scan_completion(max_wait_time=300)
            
            # Collect source code files
            source_files = self._collect_source_files(target_url)
            logger.info(f"Collected {len(source_files)} source files for code analysis")

            # Retrieve alerts with detailed logging
            logger.info("Retrieving final scan alerts...")
            alerts = self.zap.core.alerts(baseurl=target_url)
            logger.info(f"Found {len(alerts)} total alerts")
            
            # Process and categorize alerts
            risk_counts = {"High": 0, "Medium": 0, "Low": 0, "Info": 0}
            
            logger.info("Processing alert details and extracting affected code...")
            alert_names = set()  # Track unique alert names
            alert_categories = {}  # Group alerts by category
            
            for idx, alert in enumerate(alerts):
                try:
                    risk = alert.get('risk', '')
                    if risk in risk_counts:
                        risk_counts[risk] += 1
                
                    name = alert.get('name', alert.get('alert', ''))
                    alert_names.add(name)
                    
                    # Track alert category
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
                    
                    # Get affected code context
                    affected_code = self._get_affected_code(alert)
                    source_file = None
                    if affected_code and affected_code.file_path:
                        source_file = affected_code.file_path
                    
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
                    
                    # Log high and medium risks in detail with affected code info
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

            # Log alert categories summary
            logger.info("Alert categories summary:")
            for category, alerts_list in alert_categories.items():
                logger.info(f"Category '{category}': {len(alerts_list)} alerts")
                # Log up to 3 examples per category
                examples = alerts_list[:min(3, len(alerts_list))]
                if examples:
                    logger.info(f"  Examples: {', '.join(examples)}")
            
            # Get scan completion time and duration
            scan_end_time = datetime.now()
            duration_seconds = int((scan_end_time - scan_start_time).total_seconds())
            
            # Log detailed statistics
            logger.info(f"Scan completed in {duration_seconds} seconds ({duration_seconds/60:.1f} minutes)")
            logger.info(f"Risk breakdown: High={risk_counts['High']}, Medium={risk_counts['Medium']}, "
                        f"Low={risk_counts['Low']}, Info={risk_counts['Info']}")
            
            # Log affected code stats
            with_code = sum(1 for v in vulnerabilities if v.affected_code and v.affected_code.snippet)
            logger.info(f"Vulnerabilities with affected code identified: {with_code}/{len(vulnerabilities)}")
            
            # Update summary with final results
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
                "vulnerabilities_with_code": with_code
            })
            
            return vulnerabilities, summary

        except Exception as e:
            error_msg = f"Scan error: {str(e)}"
            logger.error(error_msg)
            summary["status"] = "failed"
            summary["error"] = error_msg
            summary["end_time"] = datetime.now().isoformat()
            return [], summary
        finally:
            logger.info("Cleaning up ZAP resources...")
            self._cleanup_existing_zap()

    def generate_affected_code_report(self, vulnerabilities: List[ZapVulnerability], output_file: str = None) -> str:
        """
        Generates a report focusing on the affected code for each vulnerability.
        
        Args:
            vulnerabilities: List of ZapVulnerability objects
            output_file: Optional file path to save the report
            
        Returns:
            The report content as a string
        """
        logger.info("Generating affected code report...")
        
        # Group vulnerabilities by risk level for better organization
        vuln_by_risk = {
            "High": [],
            "Medium": [],
            "Low": [],
            "Informational": []
        }
        
        for vuln in vulnerabilities:
            risk = vuln.risk
            if risk == "Info":
                risk = "Informational"
            if risk in vuln_by_risk:
                vuln_by_risk[risk].append(vuln)
        
        # Generate report
        report = ["# Security Vulnerability Report with Affected Code\n"]
        
        # Add summary section
        report.append("## Summary\n")
        for risk, vulns in vuln_by_risk.items():
            if vulns:
                report.append(f"- **{risk}**: {len(vulns)} vulnerabilities\n")
        
        # Add detailed findings with code
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
                
                # Add affected code section if available
                if vuln.affected_code and vuln.affected_code.snippet:
                    code = vuln.affected_code
                    report.append("\n#### Affected Code\n")
                    
                    if code.file_path:
                        report.append(f"**File**: {code.file_path}\n")
                    
                    if code.line_number:
                        report.append(f"**Line**: {code.line_number}\n")
                    
                    # Add code snippet with syntax highlighting
                    report.append("\n```\n")
                    # Add line numbers to code
                    if code.start_line > 0:
                        lines = code.snippet.split('\n')
                        numbered_lines = []
                        for i, line in enumerate(lines, code.start_line):
                            line_num = f"{i:4d} | "
                            # Highlight vulnerable lines
                            if i in code.vulnerable_lines:
                                numbered_lines.append(f"{line_num}{line}  <-- VULNERABILITY")
                            else:
                                numbered_lines.append(f"{line_num}{line}")
                        report.append('\n'.join(numbered_lines))
                    else:
                        # If we don't have line numbers, just show the snippet
                        report.append(code.snippet)
                    report.append("\n```\n")
                
                # Add evidence if available but no code snippet
                elif vuln.evidence and (not vuln.affected_code or not vuln.affected_code.snippet):
                    report.append("\n#### Evidence\n")
                    report.append("\n```\n")
                    report.append(vuln.evidence)
                    report.append("\n```\n")
                
                report.append("\n---\n")
        
        # Save report to file if specified
        report_content = '\n'.join(report)
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                logger.info(f"Saved affected code report to: {output_file}")
            except Exception as e:
                logger.error(f"Error saving report to {output_file}: {str(e)}")
        
        return report_content

    def set_source_code_root(self, root_dir: str):
        """
        Set the root directory for source code to help with mapping URLs to local files.
        
        Args:
            root_dir: Path to the source code root directory
        """
        if os.path.isdir(root_dir):
            self.source_root_dir = root_dir
            logger.info(f"Source code root directory set to: {root_dir}")
        else:
            logger.warning(f"Source code root directory not found: {root_dir}")

    def start_scan(self, model: str, app_num: int) -> bool:
        """
        Start a scan for the specified model and app number.
        """
        scan_key = f"{model}-{app_num}"
        scan_status = ScanStatus(start_time=datetime.now().isoformat())
        scan_status.status = "Starting"
        
        # Calculate target URL based on model and app_num
        BASE_FRONTEND_PORT = 5501
        PORTS_PER_APP = 2
        BUFFER_PORTS = 20
        APPS_PER_MODEL = 30
        total_needed = APPS_PER_MODEL * PORTS_PER_APP + BUFFER_PORTS
        
        # Get model index using helper function
        model_idx = self._get_model_index(model)
        
        # Calculate frontend port
        frontend_port_start = BASE_FRONTEND_PORT + (model_idx * total_needed)
        frontend_port = frontend_port_start + ((app_num - 1) * PORTS_PER_APP)
        target_url = f"http://localhost:{frontend_port}"
        
        # Try to set source code root if possible
        app_path = self.base_path / f"{model}/app{app_num}"
        if app_path.exists() and app_path.is_dir():
            self.set_source_code_root(str(app_path))
        
        # Store scan info
        self._scans[scan_key] = {
            "status": scan_status,
            "target_url": target_url,
            "start_time": datetime.now().isoformat()
        }
        
        logger.info(f"Starting comprehensive scan {scan_key} for {target_url}")
        
        try:
            # Update status to running
            scan_status.status = "Running"
            
            # Run the scan
            vulnerabilities, summary = self.scan_target(target_url)
            
            # Generate affected code report
            report_path = self.base_path / f"{model}/app{app_num}/.zap_code_report.md"
            self.generate_affected_code_report(vulnerabilities, str(report_path))
            
            # Save results
            results_path = self.base_path / f"{model}/app{app_num}/.zap_results.json"
            results_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Saving scan results to {results_path}")
            with open(results_path, "w") as f:
                # Convert to dict but handle affected_code specially
                results_dict = {
                    "alerts": [],
                    "summary": summary,
                    "scan_time": datetime.now().isoformat()
                }
                
                # Serialize each vulnerability
                for vuln in vulnerabilities:
                    vuln_dict = asdict(vuln)
                    # Convert code context to dict if it exists
                    if vuln.affected_code:
                        vuln_dict['affected_code'] = asdict(vuln.affected_code)
                    results_dict['alerts'].append(vuln_dict)
                
                json.dump(results_dict, f, indent=2)
                
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
                
            logger.info(f"Scan {scan_key} completed successfully with {scan_status.high_count} high, "
                       f"{scan_status.medium_count} medium, {scan_status.low_count} low risks")
            return True

        except Exception as e:
            error_msg = f"Scan failed: {str(e)}"
            logger.error(error_msg)
            scan_status.status = f"Failed: {error_msg}"
            scan_status.end_time = datetime.now().isoformat()
            return False
    
    def _get_model_index(self, model_name: str) -> int:
        """
        Get the index of a model in the list of supported models.
        """
        AI_MODELS = [
            "Llama", "Mistral", "DeepSeek", "GPT4o", "Claude", 
            "Gemini", "Grok", "R1", "O3"
        ]
        return next((i for i, m in enumerate(AI_MODELS) if m == model_name), 0)

def create_scanner(base_path: Path) -> ZAPScanner:
    """
    Factory function to create a ZAPScanner instance after verifying Java is installed.
    """
    logger.info("Creating comprehensive ZAP scanner instance...")
    try:
        java_version = subprocess.check_output(
            ['java', '-version'],
            stderr=subprocess.STDOUT,
            text=True
        )
        logger.info(f"Found Java: {java_version.splitlines()[0]}")
    except Exception as e:
        error_msg = "Java runtime not found. Install Java 11+ and ensure it's in PATH."
        logger.error(f"{error_msg} Error: {str(e)}")
        raise RuntimeError(error_msg) from e
        
    scanner = ZAPScanner(base_path)
    logger.info(f"Comprehensive ZAP scanner created with base path: {base_path}")
    return scanner