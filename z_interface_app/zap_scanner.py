import json
import logging
import os
import time
import subprocess
import socket
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager

from zapv2 import ZAPv2

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@dataclass
class ZapVulnerability:
    """Represents a security vulnerability found by ZAP."""
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

@dataclass
class ScanStatus:
    """Tracks scan status."""
    status: str = "Not Started"
    progress: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0

class ZAPScanner:
    def __init__(self, base_path: Path):
        """Initialize ZAP Scanner with improved configuration."""
        self.base_path = Path(base_path)
        self.zap: Optional[ZAPv2] = None
        self.daemon_process: Optional[subprocess.Popen] = None
        
        # Configuration
        self.api_key = os.getenv('ZAP_API_KEY', '5tjkc409k4oaacd69qob5p6uri')
        self.proxy_host = "127.0.0.1"
        self.proxy_port = self._find_free_port()
        self.zap_log = self.base_path / "zap.log"
        
        # Store scans in memory
        self._scans: Dict[str, Dict] = {}
        
        # Ensure base directory exists
        self.base_path.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _port_check(self, port: int):
        """Context manager for checking port availability."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('127.0.0.1', port))
            sock.listen(1)
            yield sock
        finally:
            sock.close()
        
    def _find_free_port(self, start_port: int = 8090, max_port: int = 8099) -> int:
        """Find an available port with improved error handling."""
        for port in range(start_port, max_port + 1):
            try:
                with self._port_check(port):
                    logger.info(f"Found free port: {port}")
                    return port
            except OSError:
                continue
        raise RuntimeError(f"No free ports found between {start_port} and {max_port}")

    def _find_zap_installation(self) -> Path:
        """Locate ZAP installation with improved path handling."""
        zap_home = os.getenv("ZAP_HOME")
        possible_paths = [
            self.base_path / "ZAP_2.14.0",
            self.base_path,
            Path(zap_home) if zap_home else None,
            Path("C:/Program Files/OWASP/Zed Attack Proxy"),
            Path("C:/Program Files (x86)/OWASP/Zed Attack Proxy"),
            Path("C:/Program Files/ZAP/Zed Attack Proxy"),  # Added your installation path
            Path("/usr/share/zaproxy"),
            Path("/Applications/OWASP ZAP.app/Contents/Java"),
        ]

        logger.debug(f"Searching for ZAP installation in paths: {possible_paths}")
        
        for path in filter(None, possible_paths):
            if not path.exists():
                continue
                
            # Check for JAR file
            jar_files = list(path.glob("zap*.jar"))
            if jar_files:
                logger.info(f"Found ZAP JAR at: {jar_files[0]}")
                return jar_files[0]
                
            # Check for executables
            for exe in ["zap.bat", "zap.sh", "zap.exe"]:
                exe_path = path / exe
                if exe_path.exists():
                    logger.info(f"Found ZAP executable at: {exe_path}")
                    return exe_path

        raise FileNotFoundError(
            "ZAP installation not found. Please install ZAP and set ZAP_HOME environment variable."
        )

    def _build_zap_command(self, zap_path: Path) -> List[str]:
        """Build ZAP command with improved JVM options."""
        java_opts = [
            '-Xmx1G',
            f'-Djava.io.tmpdir={self.base_path / "tmp"}',
            '-Djava.net.preferIPv4Stack=true',
        ]

        zap_args = [
            '-daemon',
            '-port', str(self.proxy_port),
            '-host', self.proxy_host,
            '-config', f'api.key={self.api_key}',
            '-config', 'api.addrs.addr.name=.*',
            '-config', 'api.addrs.addr.regex=true',
            '-config', 'connection.timeoutInSecs=300',
        ]

        if zap_path.suffix == '.jar':
            return ['java'] + java_opts + ['-jar', str(zap_path)] + zap_args
        return [str(zap_path)] + zap_args

    def _start_zap_daemon(self) -> bool:
        """Start ZAP daemon with improved error handling."""
        try:
            # Clean up any existing processes first
            self._cleanup_existing_zap()
            
            # Create temp directory if needed
            tmp_dir = self.base_path / "tmp"
            tmp_dir.mkdir(parents=True, exist_ok=True)
            
            # Find and verify ZAP installation
            zap_path = self._find_zap_installation()
            if not zap_path.exists():
                raise FileNotFoundError(f"ZAP not found at {zap_path}")
            
            # Build and log command
            cmd = self._build_zap_command(zap_path)
            logger.info(f"Starting ZAP with command: {' '.join(cmd)}")
            
            # Start ZAP process
            self.daemon_process = subprocess.Popen(
                cmd,
                stdout=open(self.zap_log, 'w'),
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Wait for process to start
            time.sleep(10)  # Initial wait for process to start
            
            if self.daemon_process.poll() is not None:
                with open(self.zap_log, 'r') as f:
                    error_log = f.read()
                raise RuntimeError(f"ZAP failed to start. Exit code: {self.daemon_process.returncode}\nLog:\n{error_log}")
            
            # Initialize ZAP client with retry
            retry_count = 0
            while retry_count < 5:
                try:
                    self.zap = ZAPv2(
                        apikey=self.api_key,
                        proxies={
                            'http': f'http://{self.proxy_host}:{self.proxy_port}',
                            'https': f'http://{self.proxy_host}:{self.proxy_port}'
                        }
                    )
                    # Test connection
                    version = self.zap.core.version
                    logger.info(f"Successfully connected to ZAP {version}")
                    return True
                except Exception as e:
                    logger.warning(f"Connection attempt {retry_count + 1} failed: {e}")
                    retry_count += 1
                    time.sleep(5)
            
            raise RuntimeError("Failed to connect to ZAP after 5 attempts")
            
        except Exception as e:
            logger.error(f"Failed to start ZAP: {str(e)}")
            self._cleanup_existing_zap()
            raise RuntimeError(f"Failed to start ZAP: {str(e)}")

    def _cleanup_existing_zap(self):
        """Clean up existing ZAP processes with improved detection."""
        try:
            if self.daemon_process:
                logger.info("Terminating existing ZAP process...")
                self.daemon_process.terminate()
                try:
                    self.daemon_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning("ZAP process didn't terminate, forcing kill")
                    self.daemon_process.kill()
                    self.daemon_process.wait()

            # Kill any remaining ZAP processes
            if os.name == 'nt':
                for process in ['java.exe', 'zap.exe']:
                    subprocess.run(['taskkill', '/f', '/im', process], capture_output=True, check=False)
            else:
                subprocess.run(['pkill', '-f', 'zap.jar'], capture_output=True, check=False)
                
            time.sleep(2)  # Wait for cleanup
            
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")

    def scan_target(self, target_url: str, scan_policy: Optional[str] = None) -> Tuple[List[ZapVulnerability], Dict]:
        """Run a scan against a target URL with improved error handling."""
        vulnerabilities = []
        summary = {
            "start_time": datetime.now().isoformat(),
            "target_url": target_url,
            "status": "failed"
        }
        
        try:
            logger.info(f"Starting scan of target: {target_url}")
            if not self._start_zap_daemon():
                return [], {"status": "failed", "error": "Failed to start ZAP"}

            # Spider scan
            logger.info("Starting spider scan...")
            spider_id = self.zap.spider.scan(target_url)
            while int(self.zap.spider.status(spider_id)) < 100:
                progress = int(self.zap.spider.status(spider_id))
                logger.info(f"Spider progress: {progress}%")
                time.sleep(2)
            
            # Active scan using positional parameters:
            # Parameters: url, recurse, inScopeOnly, scanPolicyName, method, postData
            logger.info("Starting active scan...")
            recurse = "true"
            in_scope_only = "false"
            policy = scan_policy if scan_policy else ""
            method = ""
            post_data = ""
            scan_id = self.zap.ascan.scan(target_url, recurse, in_scope_only, policy, method, post_data)
            
            while int(self.zap.ascan.status(scan_id)) < 100:
                progress = int(self.zap.ascan.status(scan_id))
                logger.info(f"Active scan progress: {progress}%")
                time.sleep(5)
            
            # Process alerts
            alerts = self.zap.core.alerts()
            for alert in alerts:
                try:
                    vuln = ZapVulnerability(
                        url=alert.get('url', ''),
                        name=alert.get('name', alert.get('alert', '')),
                        alert=alert.get('alert', ''),
                        risk=alert.get('risk', ''),
                        confidence=alert.get('confidence', ''),
                        description=alert.get('description', ''),
                        solution=alert.get('solution', ''),
                        reference=alert.get('reference', ''),
                        evidence=alert.get('evidence', ''),
                        cwe_id=alert.get('cweid', '')
                    )
                    vulnerabilities.append(vuln)
                except Exception as e:
                    logger.error(f"Error processing alert: {e}")
                    continue

            summary.update({
                "status": "success",
                "end_time": datetime.now().isoformat(),
                "total_alerts": len(vulnerabilities),
                "risk_counts": {
                    "High": len([v for v in vulnerabilities if v.risk == "High"]),
                    "Medium": len([v for v in vulnerabilities if v.risk == "Medium"]),
                    "Low": len([v for v in vulnerabilities if v.risk == "Low"]),
                    "Info": len([v for v in vulnerabilities if v.risk == "Info"])
                }
            })
            
            return vulnerabilities, summary
            
        except Exception as e:
            logger.error(f"Scan error: {e}")
            summary["error"] = str(e)
            return [], summary
            
        finally:
            self._cleanup_existing_zap()

    def start_scan(self, model: str, app_num: int, scan_options: Dict) -> bool:
        """Start a new scan with improved error handling."""
        scan_key = f"{model}-{app_num}"
        scan_status = ScanStatus()
        self._scans[scan_key] = {
            "status": scan_status,
            "options": scan_options,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            frontend_port = 5501 + ((app_num - 1) * 2)
            target_url = f"http://localhost:{frontend_port}"
            
            scan_status.status = "Starting"
            vulnerabilities, summary = self.scan_target(target_url, scan_options.get("scanPolicy"))
            
            # Save results
            results_path = self.base_path / f"{model}/app{app_num}/.zap_results.json"
            results_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(results_path, "w") as f:
                json.dump({
                    "alerts": [asdict(v) for v in vulnerabilities],
                    "summary": summary,
                    "scan_time": datetime.now().isoformat()
                }, f, indent=2)
            
            scan_status.status = "Complete"
            scan_status.progress = 100
            scan_status.high_count = summary["risk_counts"]["High"]
            scan_status.medium_count = summary["risk_counts"]["Medium"]
            scan_status.low_count = summary["risk_counts"]["Low"]
            scan_status.info_count = summary["risk_counts"]["Info"]
            
            return True
            
        except Exception as e:
            error_msg = f"Scan failed: {str(e)}"
            logger.error(error_msg)
            scan_status.status = f"Failed: {error_msg}"
            return False

def create_scanner(base_path: Path) -> ZAPScanner:
    """Create a ZAP scanner with improved initialization checks."""
    try:
        # Verify Java installation
        java_version = subprocess.check_output(
            ['java', '-version'], 
            stderr=subprocess.STDOUT,
            text=True
        )
        logger.info(f"Found Java: {java_version.splitlines()[0]}")
    except Exception as e:
        raise RuntimeError(
            "Java runtime not found. Install Java 11+ and ensure it's in PATH."
        ) from e

    return ZAPScanner(base_path)
