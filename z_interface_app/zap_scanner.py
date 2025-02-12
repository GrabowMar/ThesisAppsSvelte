"""
ZAP Scanner with internal state management.
Provides security scanning functionality independent of Flask config.
"""

import json
import logging
import os
import time
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from zapv2 import ZAPv2

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
        self.base_path = base_path
        self.zap: Optional[ZAPv2] = None
        self.daemon_process: Optional[subprocess.Popen] = None
        
        # Configuration
        self.api_key = "5tjkc409k4oaacd69qob5p6uri"
        self.proxy_host = "127.0.0.1"
        self.proxy_port = self._find_free_port()
        
        # Store scans in memory
        self._scans: Dict[str, Dict] = {}
        
    def _find_free_port(self, start_port: int = 8080, max_port: int = 8090) -> int:
        """Find an available port between start_port and max_port."""
        import socket
        
        for port in range(start_port, max_port + 1):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                try:
                    sock.bind(('127.0.0.1', port))
                    sock.listen(1)
                    sock.close()
                    logger.info(f"Found free port: {port}")
                    return port
                except OSError:
                    continue
        
        raise RuntimeError(f"No free ports found between {start_port} and {max_port}")
        
    def _test_network_access(self) -> bool:
        """Test if we can bind to the port after cleaning up any existing ZAP processes."""
        import socket
        
        logger.info(f"Testing network access on port {self.proxy_port}")
        
        # Cleanup any existing ZAP processes
        self._cleanup_existing_zap()
        
        # Test if we can bind to the port
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('127.0.0.1', self.proxy_port))
                sock.listen(1)
                logger.info("Successfully bound to port")
        except Exception as e:
            logger.error(f"Cannot bind to port {self.proxy_port}: {e}")
            return False
            
        return True

    def _cleanup_existing_zap(self):
        """Kill any existing ZAP processes."""
        try:
            if os.name == 'nt':  # Windows: try to kill both java.exe and zap.exe
                subprocess.run(['taskkill', '/f', '/im', 'java.exe'], capture_output=True)
                subprocess.run(['taskkill', '/f', '/im', 'zap.exe'], capture_output=True)
            else:  # Linux/Mac
                os.system('pkill -f zap.jar')
            time.sleep(2)  # Wait for processes to die
        except Exception as e:
            logger.warning(f"Error during ZAP cleanup: {e}")

    def _start_zap_daemon(self) -> bool:
        """Start ZAP daemon process."""
        try:
            logger.info("Starting ZAP daemon...")
            # Look for ZAP installation in common locations
            zap_path = None
            possible_paths = [
                self.base_path / "ZAP_2.14.0",  # Local project directory
                Path("C:/Program Files/ZAP/Zed Attack Proxy"),  # Windows default
                Path("C:/Program Files (x86)/OWASP/Zed Attack Proxy"),
                Path("/usr/share/zaproxy"),  # Linux default
            ]
            
            for path in possible_paths:
                if (path / "zap.jar").exists():
                    zap_path = path / "zap.jar"
                    break
                elif (path / "zap.sh").exists():
                    zap_path = path / "zap.sh"
                    break
                elif (path / "zap.exe").exists():
                    zap_path = path / "zap.exe"
                    break
            
            if not zap_path:
                raise FileNotFoundError("Could not find ZAP installation")

            # Configure JVM options for better stability
            java_opts = [
                '-Xmx512m',              # Limit memory usage
                '-XX:+UseG1GC',          # Use G1 garbage collector
                '-XX:+DisableAttachMechanism',  # Improve startup time
            ]
            
            # Build command with Java options
            cmd = [
                'java'
            ] + java_opts + [
                '-jar', str(zap_path),
                '-daemon',
                '-port', str(self.proxy_port),
                '-host', self.proxy_host,
                '-config', f'api.key={self.api_key}',
                '-config', 'api.addrs.addr.name=.*',
                '-config', 'api.addrs.addr.regex=true',
                '-config', 'connection.timeoutInSecs=120',
                '-config', 'spider.maxDuration=1',
                '-silent',   # Reduce console output
                '-nostdout'  # Don't output to stdout
            ]
            
            # Start process with error handling
            try:
                self.daemon_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                logger.info("ZAP process started")
            except Exception as e:
                logger.error(f"Error starting ZAP process: {e}")
                return False
            
            # Wait for ZAP to start with retry
            max_attempts = 10
            for attempt in range(max_attempts):
                try:
                    time.sleep(5)  # Wait between attempts
                    self.zap = ZAPv2(
                        apikey=self.api_key,
                        proxies={
                            'http': f'http://{self.proxy_host}:{self.proxy_port}',
                            'https': f'http://{self.proxy_host}:{self.proxy_port}'
                        }
                    )
                    # Test connection
                    self.zap.core.version
                    logger.info("Successfully connected to ZAP")
                    break
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1}/{max_attempts} to connect to ZAP failed: {e}")
                    if attempt == max_attempts - 1:
                        raise
            return True
            
        except Exception as e:
            logger.error(f"Failed to start ZAP: {e}")
            return False

    def _stop_zap_daemon(self):
        """Stop the ZAP daemon and cleanup."""
        try:
            if self.zap:
                try:
                    self.zap.core.shutdown()
                except Exception as e:
                    logger.warning(f"Could not shutdown ZAP gracefully: {e}")
                self.zap = None
                
            if self.daemon_process:
                try:
                    self.daemon_process.terminate()
                    self.daemon_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning("ZAP process did not terminate, forcing kill")
                    self.daemon_process.kill()
                    self.daemon_process.wait()
                except Exception as e:
                    logger.error(f"Error killing ZAP process: {e}")
                    
            # Force cleanup if process is still running
            if os.name == 'nt':  # Windows
                subprocess.run(['taskkill', '/f', '/im', 'java.exe'], capture_output=True)
                subprocess.run(['taskkill', '/f', '/im', 'zap.exe'], capture_output=True)
            else:  # Linux/Mac
                os.system('pkill -f zap.jar')
        
        except Exception as e:
            logger.error(f"Error during ZAP cleanup: {e}")

    def _get_scan_key(self, model: str, app_num: int) -> str:
        """Generate unique scan key."""
        return f"{model}-{app_num}"
    
    def _get_results_path(self, model: str, app_num: int) -> Path:
        """Get path for storing scan results."""
        return self.base_path / f"{model}/app{app_num}/.zap_results.json"
    
    def scan_target(self, target_url: str, scan_policy: Optional[str] = None) -> Tuple[List[ZapVulnerability], Dict]:
        """Run a scan against a target URL."""
        vulnerabilities = []
        summary = {
            "start_time": datetime.now().isoformat(),
            "target_url": target_url,
            "status": "failed"
        }
        
        try:
            if not self._start_zap_daemon():
                return [], {"status": "failed", "error": "Failed to start ZAP"}

            logger.info(f"Scanning target: {target_url}")
            
            # Spider scan
            logger.info("Starting spider scan...")
            spider_id = self.zap.spider.scan(target_url)
            while int(self.zap.spider.status(spider_id)) < 100:
                logger.info(f"Spider progress: {self.zap.spider.status(spider_id)}%")
                time.sleep(2)
            
            # Active scan
            logger.info("Starting active scan...")
            scan_id = self.zap.ascan.scan(
                url=target_url,
                scanpolicyname=scan_policy
            )
            while int(self.zap.ascan.status(scan_id)) < 100:
                logger.info(f"Active scan progress: {self.zap.ascan.status(scan_id)}%")
                time.sleep(5)
            
            # Process alerts
            alerts = self.zap.core.alerts()
            for alert in alerts:
                vuln = ZapVulnerability(
                    url=alert.get('url', ''),
                    name=alert.get('alert', ''),
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

            summary.update({
                "status": "success",
                "end_time": datetime.now().isoformat(),
                "total_alerts": len(vulnerabilities),
                "risk_counts": {
                    "High": len([v for v in vulnerabilities if v.risk == "High"]),
                    "Medium": len([v for v in vulnerabilities if v.risk == "Medium"]),
                    "Low": len([v for v in vulnerabilities if v.risk == "Low"])
                }
            })
            
            return vulnerabilities, summary
            
        except Exception as e:
            logger.error(f"Scan error: {e}")
            summary["error"] = str(e)
            return [], summary
            
        finally:
            self._stop_zap_daemon()

    def start_scan(self, model: str, app_num: int, scan_options: Dict) -> bool:
        """Start a new scan for a specific app."""
        scan_key = self._get_scan_key(model, app_num)
        scan_status = ScanStatus()
        self._scans[scan_key] = {
            "status": scan_status,
            "options": scan_options,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            frontend_port = 5501 + ((app_num - 1) * 2)
            target_url = f"http://localhost:{frontend_port}"
            
            vulnerabilities, summary = self.scan_target(target_url, scan_options.get("scanPolicy"))
            
            # Save results
            results_path = self._get_results_path(model, app_num)
            with open(results_path, "w") as f:
                json.dump({
                    "alerts": [asdict(v) for v in vulnerabilities],
                    "summary": summary,
                    "scan_time": datetime.now().isoformat()
                }, f, indent=2)
            
            # Update status
            scan_status.status = "Complete"
            scan_status.progress = 100
            scan_status.high_count = summary["risk_counts"]["High"]
            scan_status.medium_count = summary["risk_counts"]["Medium"]
            scan_status.low_count = summary["risk_counts"]["Low"]
            
            return True
            
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            scan_status.status = f"Failed: {str(e)}"
            return False

    def stop_scan(self, model: str, app_num: int) -> bool:
        """Stop an ongoing scan."""
        scan_key = self._get_scan_key(model, app_num)
        try:
            self._stop_zap_daemon()
            if scan_key in self._scans:
                self._scans[scan_key]["status"].status = "Stopped"
            return True
        except Exception as e:
            logger.error(f"Failed to stop scan: {e}")
            return False

    def get_status(self, model: str, app_num: int) -> ScanStatus:
        """Get current scan status."""
        scan_key = self._get_scan_key(model, app_num)
        if scan_key in self._scans:
            return self._scans[scan_key]["status"]
        return ScanStatus()

def create_scanner(base_path: Path) -> ZAPScanner:
    """Create a configured ZAP scanner instance."""
    return ZAPScanner(base_path)