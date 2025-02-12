"""
zap_scanner.py - OWASP ZAP Security Scanner Integration

Uses the official ZAP Python API to perform security scanning.
"""

import logging
import time
import subprocess
import json
import socket
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from zapv2 import ZAPv2

logger = logging.getLogger(__name__)


@dataclass
class ZapVulnerability:
    """Represents a vulnerability found by ZAP."""
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


@dataclass
class SecurityIssue:
    """Represents a security issue in a standardized format."""
    filename: str
    line_number: int
    issue_text: str
    severity: str
    confidence: str
    issue_type: str
    line_range: List[int]
    code: str
    tool: str


class ZAPScanner:
    """Main ZAP scanning class using the official API."""
    
    def __init__(self, base_path: Path):
        """
        Initialize the ZAPScanner.

        Args:
            base_path: Path to the project root.
        """
        self.base_path: Path = base_path
        self.zap: Optional[ZAPv2] = None
        self.daemon_process: Optional[subprocess.Popen] = None

        # Configuration
        self.api_key: str = 'midbe6c4fupbc055m5ood126ae'  # Should be configurable
        self.proxy_host: str = "127.0.0.1"
        self.proxy_port: int = self._find_free_port(8080)
        self.local_proxy: Dict[str, str] = {
            "http": f"http://{self.proxy_host}:{self.proxy_port}",
            "https": f"http://{self.proxy_host}:{self.proxy_port}"
        }

        # Session tracking
        self.scan_id: Optional[str] = None
        self.context_id: Optional[str] = None
        self.session_name: Optional[str] = None

        # Progress tracking
        self.scan_messages: List[str] = []
        self.status: str = "Not started"
        self.progress: int = 0

    def add_scan_message(self, message: str, level: str = "info") -> None:
        """Log and store a scan message."""
        if level.lower() == "error":
            logger.error(message)
        else:
            logger.info(message)
        self.scan_messages.append(message)

    def _find_free_port(self, starting_port: int) -> int:
        """
        Find a free port starting from 'starting_port'.

        Returns:
            An available port number.
        """
        port = starting_port
        while True:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind((self.proxy_host, port))
                    return port
                except OSError:
                    port += 1

    def configure_session(self, session_name: str, is_new: bool = True) -> bool:
        """
        Configure a ZAP session.

        Args:
            session_name: Name of the session.
            is_new: If True, create a new session; otherwise load an existing session.

        Returns:
            True if the session is configured successfully; otherwise False.
        """
        try:
            self.session_name = session_name
            if is_new:
                self.add_scan_message("Creating new ZAP session...")
                self.zap.core.new_session(name=session_name, overwrite=True)
            else:
                self.add_scan_message("Loading existing ZAP session...")
                self.zap.core.load_session(name=session_name)
            return True
        except Exception as e:
            self.add_scan_message(f"Session configuration failed: {e}", "error")
            return False

    def configure_context(
        self,
        context_name: str,
        target_url: str,
        include_urls: Optional[List[str]] = None,
        exclude_urls: Optional[List[str]] = None
    ) -> bool:
        """
        Configure scanning context.

        Args:
            context_name: Name of the context.
            target_url: The target URL.
            include_urls: List of URL patterns to include.
            exclude_urls: List of URL patterns to exclude.

        Returns:
            True if context configuration is successful; otherwise False.
        """
        try:
            self.add_scan_message(f"Creating context: {context_name}")
            self.context_id = self.zap.context.new_context(contextname=context_name)

            if include_urls:
                for url in include_urls:
                    self.add_scan_message(f"Including URL in context: {url}")
                    self.zap.context.include_in_context(contextname=context_name, regex=url)
            else:
                self.zap.context.include_in_context(
                    contextname=context_name,
                    regex=f"{target_url}.*"
                )

            if exclude_urls:
                for url in exclude_urls:
                    self.add_scan_message(f"Excluding URL from context: {url}")
                    self.zap.context.exclude_from_context(contextname=context_name, regex=url)

            return True
        except Exception as e:
            self.add_scan_message(f"Context configuration failed: {e}", "error")
            return False

    def configure_authentication(
        self,
        auth_method: str,
        auth_params: Dict[str, str],
        login_indicator: Optional[str] = None,
        logout_indicator: Optional[str] = None
    ) -> bool:
        """
        Configure authentication for the context.

        Args:
            auth_method: The authentication method to use.
            auth_params: Dictionary of authentication parameters.
            login_indicator: Regex to indicate logged in state.
            logout_indicator: Regex to indicate logged out state.

        Returns:
            True if authentication configuration is successful; otherwise False.
        """
        try:
            if not self.context_id:
                raise ValueError("Context must be configured first")

            self.add_scan_message(f"Setting up {auth_method} authentication")
            auth_config = "&".join(f"{k}={v}" for k, v in auth_params.items())
            self.zap.authentication.set_authentication_method(
                contextid=self.context_id,
                authmethodname=auth_method,
                authmethodconfigparams=auth_config
            )

            if login_indicator:
                self.zap.authentication.set_logged_in_indicator(
                    contextid=self.context_id,
                    loggedinindicatorregex=login_indicator
                )
            if logout_indicator:
                self.zap.authentication.set_logged_out_indicator(
                    contextid=self.context_id,
                    loggedoutindicatorregex=logout_indicator
                )

            return True
        except Exception as e:
            self.add_scan_message(f"Authentication configuration failed: {e}", "error")
            return False

    def add_context_user(self, username: str, credentials: Dict[str, str]) -> Optional[str]:
        """
        Add a user to the context with credentials.

        Args:
            username: The username.
            credentials: Dictionary of credential parameters.

        Returns:
            The user ID if successful; otherwise None.
        """
        try:
            if not self.context_id:
                raise ValueError("Context must be configured first")

            self.add_scan_message(f"Creating user: {username}")
            user_id = self.zap.users.new_user(contextid=self.context_id, name=username)
            cred_config = "&".join(f"{k}={v}" for k, v in credentials.items())
            self.zap.users.set_authentication_credentials(
                contextid=self.context_id,
                userid=user_id,
                authcredentialsconfigparams=cred_config
            )
            self.zap.users.set_user_enabled(
                contextid=self.context_id,
                userid=user_id,
                enabled=True
            )
            return user_id
        except Exception as e:
            self.add_scan_message(f"Failed to add user {username}: {e}", "error")
            return None

    def configure_scan_policy(
        self,
        policy_name: str,
        enable_ids: Optional[List[int]] = None,
        disable_ids: Optional[List[int]] = None
    ) -> bool:
        """
        Configure a custom scan policy.

        Args:
            policy_name: The name of the scan policy.
            enable_ids: List of scanner IDs to enable.
            disable_ids: List of scanner IDs to disable.

        Returns:
            True if the scan policy is configured successfully; otherwise False.
        """
        try:
            self.add_scan_message(f"Configuring scan policy: {policy_name}")

            try:
                self.zap.ascan.remove_scan_policy(scanpolicyname=policy_name)
            except Exception:
                pass

            self.zap.ascan.add_scan_policy(scanpolicyname=policy_name)

            if enable_ids:
                self.zap.ascan.disable_all_scanners(scanpolicyname=policy_name)
                self.add_scan_message("Enabling specific scan rules...")
                self.zap.ascan.enable_scanners(
                    ids=",".join(map(str, enable_ids)),
                    scanpolicyname=policy_name
                )
            elif disable_ids:
                self.zap.ascan.enable_all_scanners(scanpolicyname=policy_name)
                self.add_scan_message("Disabling specific scan rules...")
                self.zap.ascan.disable_scanners(
                    ids=",".join(map(str, disable_ids)),
                    scanpolicyname=policy_name
                )
            return True
        except Exception as e:
            self.add_scan_message(f"Scan policy configuration failed: {e}", "error")
            return False

    def _start_zap_daemon(self) -> bool:
        """
        Start ZAP in daemon mode.

        Returns:
            True if the daemon starts successfully; otherwise False.
        """
        try:
            logger.info("Starting ZAP daemon...")
            cmd = [
                'java', '-jar', 'zap.jar',  # Adjust path to zap.jar as needed
                '-daemon',
                '-port', str(self.proxy_port),
                '-config', f'api.key={self.api_key}',
                '-config', 'api.addrs.addr.name=.*',
                '-config', 'api.addrs.addr.regex=true'
            ]
            self.daemon_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(10)  # Allow time for ZAP to start

            self.zap = ZAPv2(
                apikey=self.api_key,
                proxies={
                    'http': f'http://{self.proxy_host}:{self.proxy_port}',
                    'https': f'http://{self.proxy_host}:{self.proxy_port}'
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to start ZAP: {e}")
            return False

    def _stop_zap_daemon(self) -> None:
        """Stop the ZAP daemon."""
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
        """
        Perform a full security scan of the target URL.

        Args:
            target_url: The target URL to scan.
            scan_policy: Optional custom scan policy name.

        Returns:
            A tuple containing a list of ZapVulnerability objects and a summary dictionary.
        """
        vulnerabilities: List[ZapVulnerability] = []
        summary: Dict = {
            "start_time": datetime.now().isoformat(),
            "target_url": target_url,
            "status": "failed",
            "alerts_count": 0
        }

        try:
            if not self._start_zap_daemon():
                return [], {"status": "failed", "error": "Failed to start ZAP"}

            logger.info(f"Scanning target: {target_url}")

            # Configure scanning context.
            context_id = self.zap.context.new_context("scan_context")
            self.zap.context.include_in_context("scan_context", f".*{target_url}.*")

            # Spider the target.
            logger.info("Starting spider scan...")
            spider_scan_id = self.zap.spider.scan(url=target_url)
            while int(self.zap.spider.status(spider_scan_id)) < 100:
                logger.info(f"Spider progress: {self.zap.spider.status(spider_scan_id)}%")
                time.sleep(2)

            # Wait briefly for passive scan to complete.
            logger.info("Waiting for passive scan to complete...")
            time.sleep(5)

            # Run active scan.
            logger.info("Starting active scan...")
            scan_id = self.zap.ascan.scan(
                url=target_url,
                scanpolicyname=scan_policy if scan_policy else None,
                contextid=context_id
            )
            while int(self.zap.ascan.status(scan_id)) < 100:
                logger.info(f"Active scan progress: {self.zap.ascan.status(scan_id)}%")
                time.sleep(5)

            # Retrieve alerts.
            alerts = self.zap.core.alerts()
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

    def integrate_with_security_analyzer(self, security_analyzer) -> None:
        """
        Integrate ZAP scanner with the main security analyzer.

        This method adds a 'zap' scanning method to the security analyzer's tool map.
        """
        security_analyzer.all_tools.append("zap")
        scanner = ZAPScanner(security_analyzer.base_path)

        def run_zap_scan(app_path: Path) -> Tuple[List[SecurityIssue], str]:
            try:
                model = app_path.parent.parent.name
                app_num = int(app_path.parent.name.replace("app", ""))
                # Calculate frontend URL (assumes a specific port allocation scheme).
                frontend_port = 5501 + ((app_num - 1) * 2)
                target_url = f"http://localhost:{frontend_port}"
                vulnerabilities, summary = scanner.scan_target(target_url)
                security_issues = [
                    SecurityIssue(
                        filename=vuln.url,
                        line_number=0,
                        issue_text=(
                            f"{vuln.alert}\nDescription: {vuln.description}\nSolution: {vuln.solution}"
                        ),
                        severity=vuln.risk.upper(),
                        confidence=vuln.confidence.upper(),
                        issue_type=f"CWE-{vuln.cwe_id}" if vuln.cwe_id else vuln.alert,
                        line_range=[0],
                        code=vuln.evidence if vuln.evidence else vuln.attack,
                        tool="OWASP ZAP"
                    )
                    for vuln in vulnerabilities
                ]
                return security_issues, json.dumps(summary, indent=2)
            except Exception as e:
                logger.error(f"ZAP scan failed: {e}")
                return [], f"Error: {e}"

        security_analyzer.tool_map["zap"] = run_zap_scan
