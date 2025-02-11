"""
zap_scanner.py - OWASP ZAP Security Scanner Integration

Uses the official ZAP Python API to perform security scanning
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import subprocess
import json

logger = logging.getLogger(__name__)

@dataclass
class ZapVulnerability:
    """Represents a vulnerability found by ZAP"""
    url: str
    alert: str
    risk: str
    confidence: str
    description: str
    solution: str
    reference: str
    param: Optional[str] = None
    attack: Optional[str] = None
    evidence: Optional[str] = None
    cwe_id: Optional[str] = None
    wasc_id: Optional[str] = None

class ZAPScanner:
    """Main ZAP scanning class using official API"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.zap: Optional[ZAPv2] = None
        self.daemon_process: Optional[subprocess.Popen] = None
        self.port = 8090
        self.api_key = 'changeme'  # Should be configurable
        
    def _start_zap_daemon(self) -> bool:
        """Start ZAP in daemon mode"""
        try:
            logger.info("Starting ZAP daemon...")
            cmd = [
                'java', '-jar', 'zap.jar',  # Will need full path in production
                '-daemon',
                '-port', str(self.port),
                '-config', f'api.key={self.api_key}',
                '-config', 'api.addrs.addr.name=.*',
                '-config', 'api.addrs.addr.regex=true'
            ]
            
            self.daemon_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for ZAP to start
            time.sleep(10)  # Adjust as needed
            
            # Initialize API client
            self.zap = ZAPv2(
                apikey=self.api_key,
                proxies={'http': f'http://localhost:{self.port}', 'https': f'http://localhost:{self.port}'}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start ZAP: {e}")
            return False

    def _stop_zap_daemon(self):
        """Stop ZAP daemon"""
        try:
            if self.zap:
                self.zap.core.shutdown()
                time.sleep(2)
            if self.daemon_process:
                self.daemon_process.terminate()
                self.daemon_process.wait(timeout=10)
        except Exception as e:
            logger.error(f"Error stopping ZAP: {e}")
            if self.daemon_process:
                self.daemon_process.kill()

    def scan_target(self, target_url: str, scan_policy: Optional[str] = None) -> Tuple[List[ZapVulnerability], Dict]:
        """Perform a full security scan of the target"""
        vulnerabilities = []
        summary = {
            "start_time": datetime.now().isoformat(),
            "target_url": target_url,
            "status": "failed",
            "alerts_count": 0
        }
        
        try:
            if not self._start_zap_daemon():
                return [], {"status": "failed", "error": "Failed to start ZAP"}

            logger.info(f"Scanning target: {target_url}")
            
            # Configure scan context
            context_id = self.zap.context.new_context("scan_context")
            self.zap.context.include_in_context("scan_context", f".*{target_url}.*")
            
            # Spider the target
            logger.info("Starting spider scan...")
            spider_scan_id = self.zap.spider.scan(url=target_url)
            
            # Wait for spider to complete
            while int(self.zap.spider.status(spider_scan_id)) < 100:
                logger.info(f"Spider progress: {self.zap.spider.status(spider_scan_id)}%")
                time.sleep(2)
            
            # Run passive scan (always runs automatically)
            logger.info("Waiting for passive scan to complete...")
            time.sleep(5)  # Give passive scan time to catch up
            
            # Run active scan
            logger.info("Starting active scan...")
            scan_id = self.zap.ascan.scan(
                url=target_url,
                scanpolicyname=scan_policy if scan_policy else None,
                contextid=context_id
            )
            
            # Wait for active scan to complete
            while int(self.zap.ascan.status(scan_id)) < 100:
                logger.info(f"Active scan progress: {self.zap.ascan.status(scan_id)}%")
                time.sleep(5)
            
            # Get all alerts
            alerts = self.zap.core.alerts()
            
            # Process alerts into vulnerabilities
            for alert in alerts:
                vuln = ZapVulnerability(
                    url=alert.get('url', ''),
                    alert=alert.get('alert', ''),
                    risk=alert.get('risk', ''),
                    confidence=alert.get('confidence', ''),
                    description=alert.get('description', ''),
                    solution=alert.get('solution', ''),
                    reference=alert.get('reference', ''),
                    param=alert.get('param', ''),
                    attack=alert.get('attack', ''),
                    evidence=alert.get('evidence', ''),
                    cwe_id=alert.get('cweid', ''),
                    wasc_id=alert.get('wascid', '')
                )
                vulnerabilities.append(vuln)
            
            # Generate scan summary
            summary.update({
                "status": "success",
                "end_time": datetime.now().isoformat(),
                "alerts_count": len(vulnerabilities),
                "risk_counts": {
                    "High": len([v for v in vulnerabilities if v.risk == "High"]),
                    "Medium": len([v for v in vulnerabilities if v.risk == "Medium"]),
                    "Low": len([v for v in vulnerabilities if v.risk == "Low"]),
                    "Informational": len([v for v in vulnerabilities if v.risk == "Informational"])
                }
            })
            
            return vulnerabilities, summary
            
        except Exception as e:
            logger.error(f"Scan error: {e}")
            summary["error"] = str(e)
            return [], summary
            
        finally:
            self._stop_zap_daemon()

def integrate_with_security_analyzer(security_analyzer):
    """Integrate ZAP scanner with the main security analyzer"""
    
    # Add ZAP to available tools
    security_analyzer.all_tools.append("zap")
    
    # Create scanner instance
    scanner = ZAPScanner(security_analyzer.base_path)
    
    # Add scanning method
    def run_zap_scan(app_path: Path) -> Tuple[List['SecurityIssue'], str]:
        try:
            model = app_path.parent.parent.name
            app_num = int(app_path.parent.name.replace("app", ""))
            
            # Calculate frontend URL
            frontend_port = 5501 + ((app_num - 1) * 2)
            target_url = f"http://localhost:{frontend_port}"
            
            # Run scan
            vulnerabilities, summary = scanner.scan_target(target_url)
            
            # Convert ZapVulnerability to SecurityIssue
            security_issues = [
                SecurityIssue(
                    filename=vuln.url,
                    line_number=0,
                    issue_text=f"{vuln.alert}\nDescription: {vuln.description}\nSolution: {vuln.solution}",
                    severity=vuln.risk.upper(),
                    confidence=vuln.confidence.upper(),
                    issue_type=f"CWE-{vuln.cwe_id}" if vuln.cwe_id else vuln.alert,
                    line_range=[0],
                    code=vuln.evidence if vuln.evidence else vuln.attack,
                    tool="OWASP ZAP"
                ) for vuln in vulnerabilities
            ]
            
            return security_issues, json.dumps(summary, indent=2)
            
        except Exception as e:
            logger.error(f"ZAP scan failed: {e}")
            return [], f"Error: {str(e)}"
    
    # Add the scanning method to the tool map
    security_analyzer.tool_map["zap"] = run_zap_scan