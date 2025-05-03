# ZAP Scanner Project Knowledge Base

## 1. Project Identity Card
**PROJECT NAME**: ZAP Scanner  
**PRIMARY PURPOSE**: A comprehensive wrapper for OWASP ZAP security scanning with enhanced source code mapping and vulnerability reporting  
**DOMAIN**: Application Security / Web Vulnerability Assessment  
**DEVELOPMENT STAGE**: Production  
**REPOSITORY URL**: [Not specified in source]  
**DOCUMENTATION URL**: [Not specified in source]  

## 2. Project Context

### 2.1 Problem Statement

**What specific problem does this project solve?**  
Security scanning of web applications is complex, requiring deep technical expertise, configuration of various scanning tools, and manual correlation between detected vulnerabilities and source code. The ZAP Scanner module solves the problem of difficulty in setting up, configuring, and interpreting results from OWASP ZAP security scans, particularly when trying to map vulnerabilities back to source code.

**Who experiences this problem?**  
Security engineers, developers, and QA teams who need to identify security vulnerabilities in web applications but lack specialized security testing expertise or face time constraints.

**What are the consequences of not solving it?**  
Without this solution, organizations face:
- Undetected security vulnerabilities that could lead to breaches
- Inefficient manual configuration of security tools
- Difficulty correlating discovered vulnerabilities with actual code
- Increased time spent on security assessment and remediation
- Limited ability to scale security testing across multiple applications

### 2.2 Solution Overview

**Core approach to solving the problem**  
ZAP Scanner provides an optimized and enhanced wrapper around OWASP ZAP that:
1. Automates the configuration and execution of comprehensive security scans
2. Maps discovered vulnerabilities to source code for faster remediation
3. Provides detailed reports with contextual source code information
4. Optimizes scanning parameters for better performance and accuracy
5. Offers quick scan options for faster execution when needed

**Key differentiators from alternatives**  
- Intelligent source code mapping to correlate vulnerabilities with code snippets
- Performance-optimized configurations for ZAP scanning operations
- Extended spidering capabilities for better content discovery
- Detailed vulnerability reporting with contextual information
- Automatic resource management and cleanup
- Support for both quick and comprehensive scanning modes

**Critical constraints that shaped design decisions**  
- Need to work with varying quality of source code and mapping
- Performance optimization to keep scan times reasonable
- Memory limitations requiring careful JVM configuration
- Supporting both traditional and JavaScript-heavy applications
- Cross-platform compatibility (Windows, Linux, MacOS)
- Adapting to varying ZAP installation locations across environments

### 2.3 User Personas

**Primary users and their technical expertise**  
1. **Security Engineers**: High technical expertise in security concepts but may need automation for efficiency
2. **DevOps Engineers**: Medium to high technical expertise in automation, moderate security knowledge
3. **Developers**: High technical expertise in programming, variable security knowledge
4. **QA Engineers**: Medium technical expertise, basic security knowledge, focused on testing workflows

**Key user workflows and goals**  
1. **Automated Security Assessment**: Integrating security scanning into CI/CD pipelines
2. **Vulnerability Discovery**: Identifying security issues in web applications
3. **Code Remediation**: Quickly finding and fixing security vulnerabilities in code
4. **Compliance Verification**: Ensuring applications meet security requirements and standards

**User expectations and requirements**  
- Fast scan execution with minimal configuration
- Clear mapping between vulnerabilities and source code
- Detailed reporting with actionable remediation steps
- Reliable operation across different environments
- Minimal false positives in vulnerability detection
- Support for modern web application technologies

## 3. Architecture Map

### 3.1 System Diagram
```
                              ┌───────────────────┐
                              │                   │
                              │  Target Web App   │
                              │                   │
                              └─────────┬─────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                                 ZAP Scanner                              │
│  ┌────────────────┐  ┌──────────────────────────────┐  ┌──────────────┐ │
│  │   ZAP Daemon   │◄─┤      ZAPScanner Class        │─►│ Source Code  │ │
│  │    Process     │  │                              │  │   Mapping    │ │
│  └────────┬───────┘  │ ┌──────────┐   ┌──────────┐ │  └──────────────┘ │
│           │          │ │  Spider  │   │   AJAX   │ │                   │
│           ▼          │ │  Scan    │──►│  Spider  │ │  ┌──────────────┐ │
│  ┌────────────────┐  │ └──────────┘   └──────────┘ │  │   Report     │ │
│  │                │  │                              │  │ Generation   │ │
│  │     ZAPv2      │◄─┤ ┌──────────┐   ┌──────────┐ │─►│              │ │
│  │      API       │  │ │ Passive  │   │  Active  │ │  └──────────────┘ │
│  │                │  │ │   Scan   │──►│   Scan   │ │                   │
│  └────────────────┘  │ └──────────┘   └──────────┘ │                   │
│                      └──────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘
```

Legend:
→ : Data flow
⟲ : Processing loop
□ : External system
■ : Internal component

### 3.2 Component Inventory

| Component Name | Type | Purpose | Interfaces | Dependencies |
|----------------|------|---------|------------|--------------|
| ZAPScanner | Class | Main class handling all scanning operations | scan_target(), start_scan(), generate_affected_code_report() | ZAPv2 |
| ZAP Daemon | Process | Running instance of ZAP as a background service | Command-line flags, API endpoints | Java Runtime |
| ZAPv2 API | Library | Python API for interacting with ZAP | ZAPv2 client methods | requests |
| Spider | Module | Traditional crawling for content discovery | scan(), status() | ZAPv2 API |
| AJAX Spider | Module | JavaScript-rendered content discovery | scan(), status(), results() | ZAPv2 API, Browser |
| Passive Scan | Module | Non-intrusive security testing | set_scanner_alert_threshold(), enable_all_scanners() | ZAPv2 API |
| Active Scan | Module | Intrusive security testing | scan(), status(), scan_policies | ZAPv2 API |
| Source Code Mapping | Component | Maps URLs to source code files | set_source_code_mapping(), _url_to_source_file() | Local filesystem |
| Report Generation | Component | Creates vulnerability reports with code context | generate_affected_code_report() | Markdown formatting |
| ZapVulnerability | DataClass | Represents a detected security issue | Properties for vulnerability details | N/A |
| CodeContext | DataClass | Represents source code context around vulnerable code | Properties for code snippets and line numbers | N/A |
| ScanStatus | DataClass | Tracks scan progress and statistics | Properties for progress, counts, timing | N/A |

### 3.3 Data Flow Sequences

**Operation: Comprehensive Security Scan**
1. **ZAPScanner** receives target URL from user
2. **ZAPScanner** starts ZAP daemon process with optimized configurations
3. **ZAPScanner** connects to ZAP API
4. **ZAPScanner** configures passive scanning with all rules enabled
5. **ZAPScanner** performs initial access to target URL
6. **ZAPScanner** executes extended spidering to discover common files
7. **Spider** crawls the target website to discover content
8. **ZAPScanner** monitors spider progress until completion
9. **AJAX Spider** crawls JavaScript-rendered content
10. **ZAPScanner** monitors AJAX spider until completion
11. **ZAPScanner** waits for passive scanning to process discovered content
12. **ZAPScanner** configures and starts active scanning
13. **ZAPScanner** monitors active scanning until completion
14. **ZAPScanner** collects source files for code mapping
15. **ZAPScanner** retrieves all detected alerts from ZAP
16. **ZAPScanner** attempts to map vulnerabilities to source code
17. **ZAPScanner** generates vulnerability objects with code context
18. **ZAPScanner** returns list of vulnerabilities and summary statistics

**Operation: Quick Security Scan**
1. **ZAPScanner** receives target URL and quick_scan=True parameter
2. **ZAPScanner** starts ZAP daemon with optimized configurations
3. **ZAPScanner** configures passive scanning with all rules enabled
4. **ZAPScanner** performs initial access to target URL
5. **Spider** crawls the target website to discover content
6. **AJAX Spider** performs focused crawling with limited depth
7. **ZAPScanner** waits for passive scanning with reduced timeout
8. **ZAPScanner** configures and starts active scanning
9. **ZAPScanner** monitors active scanning until completion
10. **ZAPScanner** processes results with source code mapping
11. **ZAPScanner** returns list of vulnerabilities and summary statistics

## 4. Core Data Structures

### DATA STRUCTURE: ZapVulnerability

**PURPOSE**: Represents a security vulnerability found by ZAP scans, enriched with source code context

**SCHEMA**:
- url: str
  Purpose: URL where the vulnerability was detected
  Valid values: Any valid URL string
  
- name: str
  Purpose: Name of the vulnerability
  Valid values: Non-empty string
  
- alert: str
  Purpose: Alert message describing the vulnerability
  Valid values: Non-empty string
  
- risk: str
  Purpose: Risk level assessment
  Valid values: ["High", "Medium", "Low", "Info"]
  
- confidence: str
  Purpose: Confidence level in the finding
  Valid values: ["High", "Medium", "Low"]
  
- description: str
  Purpose: Detailed description of the vulnerability
  Valid values: Any string
  
- solution: str
  Purpose: Recommended fix for the vulnerability
  Valid values: Any string
  
- reference: str
  Purpose: Reference links for more information
  Valid values: Any string
  
- evidence: Optional[str]
  Purpose: Evidence of the vulnerability from the response
  Valid values: Any string or None
  Default: None
  
- cwe_id: Optional[str]
  Purpose: Common Weakness Enumeration ID
  Valid values: String containing numeric ID or None
  Default: None
  
- parameter: Optional[str]
  Purpose: Affected parameter name
  Valid values: Any string or None
  Default: None
  
- attack: Optional[str]
  Purpose: Attack vector used to detect the vulnerability
  Valid values: Any string or None
  Default: None
  
- wascid: Optional[str]
  Purpose: Web Application Security Consortium ID
  Valid values: String containing numeric ID or None
  Default: None
  
- affected_code: Optional[CodeContext]
  Purpose: Source code context for the vulnerability
  Valid values: CodeContext object or None
  Default: None
  
- source_file: Optional[str]
  Purpose: Path to the source file where vulnerability exists
  Valid values: Valid file path or None
  Default: None

**RELATIONSHIPS**:
- CONTAINS [CodeContext] (through affected_code)

**INVARIANTS**:
- url, name, alert, risk, confidence, description, solution, and reference must be non-empty

**LIFECYCLE**:
- Creation: Created when processing ZAP alerts after a scan
- Mutation: Immutable after creation
- Termination: Destroyed when scan results are no longer needed

**EXAMPLES**:
```python
# Valid instance example:
{
  "url": "http://localhost:5501/login",
  "name": "Cross Site Scripting (Reflected)",
  "alert": "Cross Site Scripting (Reflected)",
  "risk": "High",
  "confidence": "Medium",
  "description": "Cross-site Scripting (XSS) is when...",
  "solution": "Phase: Architecture and Design\nUse a vetted library...",
  "reference": "https://owasp.org/www-community/attacks/xss/",
  "evidence": "<script>alert(1)</script>",
  "cwe_id": "79",
  "parameter": "username",
  "attack": "<script>alert(1)</script>",
  "wascid": "8",
  "affected_code": {
    "snippet": "function validate(username) {\n  document.write(username);\n}",
    "line_number": 24,
    "file_path": "/app/js/validate.js",
    "start_line": 23,
    "end_line": 25,
    "vulnerable_lines": [24],
    "highlight_positions": [[23, 41]]
  },
  "source_file": "/app/js/validate.js"
}
```

### DATA STRUCTURE: CodeContext

**PURPOSE**: Represents source code context around vulnerable code, with highlighting information

**SCHEMA**:
- snippet: str
  Purpose: The code snippet containing the vulnerability
  Valid values: Any string containing source code
  
- line_number: Optional[int]
  Purpose: Line number of the vulnerability in the source file
  Valid values: Positive integer or None
  Default: None
  
- file_path: Optional[str]
  Purpose: Path to the source file
  Valid values: Valid file path string or None
  Default: None
  
- start_line: int
  Purpose: Starting line number of the snippet in the source file
  Valid values: Non-negative integer
  Default: 0
  
- end_line: int
  Purpose: Ending line number of the snippet in the source file
  Valid values: Non-negative integer
  Default: 0
  
- vulnerable_lines: List[int]
  Purpose: List of line numbers containing vulnerabilities
  Valid values: List of integers
  Default: []
  
- highlight_positions: List[Tuple[int, int]]
  Purpose: Pairs of (start, end) positions to highlight in the snippet
  Valid values: List of integer tuples
  Default: []

**RELATIONSHIPS**:
- BELONGS_TO [ZapVulnerability]

**INVARIANTS**:
- snippet must not be empty
- start_line <= end_line
- If line_number is present, it must be within start_line and end_line

**LIFECYCLE**:
- Creation: Created during vulnerability processing to provide code context
- Mutation: Immutable after creation
- Termination: Destroyed when parent vulnerability is no longer needed

**EXAMPLES**:
```python
# Valid instance example:
{
  "snippet": "function processUser(userData) {\n  const user = JSON.parse(userData);\n  document.write(user.name);\n}",
  "line_number": 3,
  "file_path": "/app/js/user.js",
  "start_line": 1,
  "end_line": 4,
  "vulnerable_lines": [3],
  "highlight_positions": [[58, 80]]
}

# Example with just evidence but no file mapping:
{
  "snippet": "<script>alert(1)</script>",
  "line_number": null,
  "file_path": null,
  "start_line": 0,
  "end_line": 0,
  "vulnerable_lines": [],
  "highlight_positions": [[0, 24]]
}
```

### DATA STRUCTURE: ScanStatus

**PURPOSE**: Tracks the status and progress of a ZAP scan for monitoring and reporting

**SCHEMA**:
- status: str
  Purpose: Current status of the scan
  Valid values: ["Not Started", "Starting", "Running", "Complete", "Failed", "Stopped"]
  Default: "Not Started"
  
- progress: int
  Purpose: Overall scan progress percentage
  Valid values: 0-100
  Default: 0
  
- high_count: int
  Purpose: Number of high-risk vulnerabilities found
  Valid values: Non-negative integer
  Default: 0
  
- medium_count: int
  Purpose: Number of medium-risk vulnerabilities found
  Valid values: Non-negative integer
  Default: 0
  
- low_count: int
  Purpose: Number of low-risk vulnerabilities found
  Valid values: Non-negative integer
  Default: 0
  
- info_count: int
  Purpose: Number of informational findings
  Valid values: Non-negative integer
  Default: 0
  
- spider_progress: int
  Purpose: Progress of traditional spider component
  Valid values: 0-100
  Default: 0
  
- passive_progress: int
  Purpose: Progress of passive scan component
  Valid values: 0-100
  Default: 0
  
- active_progress: int
  Purpose: Progress of active scan component
  Valid values: 0-100
  Default: 0
  
- ajax_progress: int
  Purpose: Progress of AJAX spider component
  Valid values: 0-100
  Default: 0
  
- start_time: Optional[str]
  Purpose: ISO-formatted timestamp when scan started
  Valid values: ISO-8601 timestamp string or None
  Default: None
  
- end_time: Optional[str]
  Purpose: ISO-formatted timestamp when scan ended
  Valid values: ISO-8601 timestamp string or None
  Default: None
  
- duration_seconds: Optional[int]
  Purpose: Total scan duration in seconds
  Valid values: Non-negative integer or None
  Default: None

**RELATIONSHIPS**:
- None (standalone tracking object)

**INVARIANTS**:
- progress must be between 0 and 100
- All count fields must be non-negative
- If end_time is set, start_time must also be set
- If duration_seconds is set, both start_time and end_time must be set

**LIFECYCLE**:
- Creation: Created when a scan is initiated
- Mutation: Updated throughout scan execution to reflect progress
- Termination: Finalized when scan completes or fails

**EXAMPLES**:
```python
# Scan in progress:
{
  "status": "Running",
  "progress": 45,
  "high_count": 2,
  "medium_count": 5,
  "low_count": 8,
  "info_count": 12,
  "spider_progress": 100,
  "passive_progress": 80,
  "active_progress": 30,
  "ajax_progress": 100,
  "start_time": "2023-05-15T14:23:15.123456",
  "end_time": null,
  "duration_seconds": null
}

# Completed scan:
{
  "status": "Complete",
  "progress": 100,
  "high_count": 3,
  "medium_count": 7,
  "low_count": 12,
  "info_count": 18,
  "spider_progress": 100,
  "passive_progress": 100,
  "active_progress": 100,
  "ajax_progress": 100,
  "start_time": "2023-05-15T14:23:15.123456",
  "end_time": "2023-05-15T14:48:22.654321",
  "duration_seconds": 1507
}
```

## 5. Function Reference

### FUNCTION: scan_target

**PURPOSE**: Performs a comprehensive security scan of the target URL using OWASP ZAP with enhanced passive and active scanning

**SIGNATURE**:
```python
def scan_target(self, target_url: str, quick_scan: bool = False) -> Tuple[List[ZapVulnerability], Dict]:
```

**PARAMETERS**:
- target_url: str - The URL to scan (e.g., http://localhost:5501)
- quick_scan: bool - If True, performs a faster scan with reduced thoroughness

**RETURNS**:
- Success case: Tuple containing (list of ZapVulnerability objects, dictionary with scan summary)
- Error case: Tuple containing (empty list, dictionary with error information)

**BEHAVIOR**:
1. Initializes scan timing and data structures
2. Starts ZAP daemon with optimized configurations
3. Configures passive scanning with all rules enabled
4. Accesses target URL and performs extended spidering
5. Runs traditional spider to discover content
6. Runs AJAX spider (focused mode if quick_scan=True)
7. Waits for passive scan to process discovered content
8. Configures and runs active scanning
9. Collects source files for code mapping
10. Retrieves and processes all alerts from ZAP
11. Maps vulnerabilities to source code where possible
12. Categorizes vulnerabilities by risk level and type
13. Generates summary statistics
14. Cleans up ZAP resources
15. Returns discovered vulnerabilities and scan summary

**EXAMPLES**:
```python
# Example call:
vulnerabilities, summary = scanner.scan_target("http://localhost:5501", quick_scan=False)

# Expected result:
# vulnerabilities is a list of ZapVulnerability objects
# summary is a dictionary with scan statistics, e.g.:
{
  "status": "success",
  "start_time": "2023-05-15T14:23:15.123456",
  "end_time": "2023-05-15T14:48:22.654321",
  "duration_seconds": 1507,
  "target_url": "http://localhost:5501",
  "total_alerts": 40,
  "risk_counts": {"High": 3, "Medium": 7, "Low": 12, "Info": 18},
  "unique_alert_types": 15,
  "alert_categories": {"XSS": 3, "Information Disclosure": 8, "Security Headers": 5},
  "vulnerabilities_with_code": 25
}

# Error example:
vulnerabilities, summary = scanner.scan_target("http://invalid-host", quick_scan=True)

# Expected result:
# vulnerabilities is an empty list
# summary contains error information:
{
  "status": "failed",
  "error": "Failed to access target URL: Connection refused",
  "start_time": "2023-05-15T14:23:15.123456",
  "end_time": "2023-05-15T14:24:05.654321"
}
```

### FUNCTION: generate_affected_code_report

**PURPOSE**: Generates a comprehensive markdown report focusing on the affected code for each vulnerability

**SIGNATURE**:
```python
def generate_affected_code_report(self, vulnerabilities: List[ZapVulnerability], output_file: str = None) -> str:
```

**PARAMETERS**:
- vulnerabilities: List[ZapVulnerability] - List of vulnerability objects to include in the report
- output_file: Optional[str] - If provided, the report will be saved to this file path

**RETURNS**:
- Success case: String containing the markdown report content
- Error case: Empty string if vulnerabilities list is empty

**BEHAVIOR**:
1. Groups vulnerabilities by risk level (High, Medium, Low, Informational)
2. Generates a summary section with counts for each risk level
3. Creates detailed sections for each risk level
4. For each vulnerability, adds:
   - Vulnerability name and URL
   - Parameter, confidence, and other metadata
   - Detailed description and solution
   - Source code context with line numbers and highlighting
   - Evidence if source code is not available
5. If output_file is provided, saves the report to the specified path
6. Returns the complete report as a string

**EXAMPLES**:
```python
# Example call:
report = scanner.generate_affected_code_report(vulnerabilities, "/path/to/report.md")

# Expected content of report:
"""
# Security Vulnerability Report with Affected Code

## Summary
- **High**: 3 vulnerabilities
- **Medium**: 7 vulnerabilities
- **Low**: 12 vulnerabilities
- **Informational**: 18 vulnerabilities

## High Risk Vulnerabilities

### 1. Cross Site Scripting (Reflected)
- **URL**: http://localhost:5501/login
- **Parameter**: username
- **Confidence**: Medium
- **Description**: Cross-site Scripting (XSS) is when...
- **Solution**: Phase: Architecture and Design\nUse a vetted library...

#### Affected Code
**File**: /app/js/validate.js
**Line**: 24

```
   23 | function validate(username) {
   24 |   document.write(username);  <-- VULNERABILITY
   25 | }
```

---

### 2. SQL Injection
...
"""
```

### FUNCTION: _get_affected_code

**PURPOSE**: Extracts affected code context from an alert if possible, mapping web vulnerabilities to source code

**SIGNATURE**:
```python
def _get_affected_code(self, alert: Dict[str, Any]) -> Optional[CodeContext]:
```

**PARAMETERS**:
- alert: Dict[str, Any] - ZAP alert dictionary containing vulnerability information

**RETURNS**:
- Success case: CodeContext object with source code information
- Error case: None if no code context could be determined

**BEHAVIOR**:
1. Extracts URL and evidence from the alert
2. Attempts to map URL to local source file using source code mapping
3. If local file exists, reads the source code
4. If no local file, attempts to fetch source directly from URL
5. If still no source, tries to extract from ZAP response messages
6. If source code is found, locates the evidence within it
7. Extracts line number and surrounding context (5 lines before and after)
8. Calculates highlighting positions for the vulnerable code
9. Returns CodeContext object with all gathered information
10. If no source code is available but evidence exists, returns minimal context

**EXAMPLES**:
```python
# Example call with successful source mapping:
alert = {
  'url': 'http://localhost:5501/js/validate.js',
  'evidence': 'document.write(username)',
  'parameter': 'username'
}
code_context = scanner._get_affected_code(alert)

# Expected result:
CodeContext(
  snippet="function validate(username) {\n  document.write(username);\n}",
  line_number=24,
  file_path="/app/js/validate.js",
  start_line=23,
  end_line=25,
  vulnerable_lines=[24],
  highlight_positions=[(23, 41)]
)

# Example call with no source mapping:
alert = {
  'url': 'http://localhost:5501/api/users',
  'evidence': '<script>alert(1)</script>',
  'parameter': 'name'
}
code_context = scanner._get_affected_code(alert)

# Expected result:
CodeContext(
  snippet="<script>alert(1)</script>",
  line_number=None,
  file_path=None,
  highlight_positions=[(0, 24)]
)
```

## 6. API Reference

### ENDPOINT: scan_target method

**PURPOSE**: Core method to perform a comprehensive security scan of a target URL

**REQUEST**:
- Parameters:
  - target_url: str - URL to scan
  - quick_scan: bool - Optional flag for faster scanning (default: False)
- Authentication: None required (internal method)

**RESPONSE**:
- Success (Tuple):
  - First element: List of ZapVulnerability objects
  - Second element: Dictionary with scan summary
  
```python
# Example success response:
(
  [ZapVulnerability(...), ZapVulnerability(...), ...],
  {
    "status": "success",
    "start_time": "2023-05-15T14:23:15.123456",
    "end_time": "2023-05-15T14:48:22.654321", 
    "duration_seconds": 1507,
    "target_url": "http://localhost:5501",
    "total_alerts": 40,
    "risk_counts": {"High": 3, "Medium": 7, "Low": 12, "Info": 18}
  }
)
```

- Error (Tuple):
  - First element: Empty list
  - Second element: Dictionary with error information
  
```python
# Example error response:
(
  [],
  {
    "status": "failed",
    "error": "Failed to start ZAP daemon: Java not found",
    "start_time": "2023-05-15T14:23:15.123456",
    "end_time": "2023-05-15T14:24:05.654321"
  }
)
```

### ENDPOINT: start_scan method

**PURPOSE**: Initiates a scan for a specific model and application number

**REQUEST**:
- Parameters:
  - model: str - Model name (e.g., "Llama", "Mistral")
  - app_num: int - Application number
  - quick_scan: bool - Optional flag for faster scanning (default: False)
- Authentication: None required (internal method)

**RESPONSE**:
- Success (bool): True if scan was started successfully
- Error (bool): False if scan failed to start

```python
# Example call:
success = scanner.start_scan("Llama", 1, quick_scan=True)

# Expected result:
# success == True if scan started successfully
# success == False if scan failed to start
```

## 7. Implementation Context

### 7.1 Technology Stack

| Layer | Technology | Purpose | Version | Notes |
|-------|------------|---------|---------|-------|
| Core | Python | Main implementation language | 3.6+ | Uses type hints and dataclasses (3.7+ preferred) |
| Security Testing | OWASP ZAP | Security scanning engine | 2.14.0 | Supports headless operation |
| API Communication | ZAPv2 | Python API for ZAP | Latest | Part of Python OWASP ZAP package |
| Runtime | Java | Required for ZAP operation | 11+ | OpenJDK or Oracle JDK |
| HTTP | Requests | API communication | Latest | Used for fetching source code |
| Process Management | subprocess | Managing ZAP daemon | N/A | Built into Python |
| Concurrency | contextlib | Context managers for resource handling | N/A | Built into Python |
| Data Structures | dataclasses | Structured data representation | N/A | Requires Python 3.7+ |

### 7.2 Dependencies

| Dependency | Version | Purpose | API Surface Used | Alternatives Considered |
|------------|---------|---------|-----------------|-------------------------|
| Python OWASP ZAP | Latest | ZAP API interaction | ZAPv2 class | Direct HTTP API calls, zapv2-weekly |
| requests | Latest | HTTP client | get() | urllib, httpx |
| Java Runtime | 11+ | Running ZAP daemon | N/A | None (required) |
| OWASP ZAP | 2.14.0 | Security scanning engine | Command-line, API | Burp Suite (commercial) |
| logging | N/A | Logging functionality | Logger, handlers | loguru, custom logger |
| dataclasses | N/A | Data structure representation | dataclass decorator | attrs, pydantic |

### 7.3 Environment Requirements

**Runtime dependencies**:
- Python 3.6+ (3.7+ recommended for full dataclass support)
- Java Runtime Environment 11+ 
- OWASP ZAP 2.14.0 or compatible version
- Network access to target application
- File system access for logs and reports

**Configuration requirements**:
- ZAP_HOME environment variable (optional, for custom ZAP installation)
- ZAP_API_KEY environment variable (optional, defaults to predefined key)
- ZAP_MAX_SCAN_DURATION environment variable (optional, defaults to 120 minutes)
- ZAP_AJAX_TIMEOUT environment variable (optional, defaults to 180 seconds)

**Resource needs**:
- Memory: Minimum 8GB RAM (4GB heap for ZAP plus overhead)
- CPU: Multi-core recommended (4+ cores for optimal performance)
- Disk: 500MB for ZAP installation, plus space for logs and reports
- Network: Stable connection to target with minimal latency
- Ports: Available ports in range 8090-8099 for ZAP proxy

## 8. Reasoning Patterns

### 8.1 Key Algorithms

#### ALGORITHM: Source Code Mapping

**PURPOSE**: Maps web URLs to local source code files to correlate vulnerabilities with code

**INPUT**: 
- URL where vulnerability was detected
- Source code mapping configuration (URL prefixes to local paths)
- Source code root directory (optional)

**OUTPUT**: 
- Local file path corresponding to the URL
- Line number and context if evidence is found in the file

**STEPS**:
1. Check if direct mapping exists from URL prefix to local directory
   a. If found, convert URL path to local file path
   b. Return the mapped file path
2. If no direct mapping but root directory exists:
   a. Parse URL to extract the path component
   b. Remove leading slash and query/fragments
   c. Try different path possibilities:
      i. Join root_dir with path
      ii. Join root_dir/src with path
      iii. Join root_dir/public with path
   d. For each possibility:
      i. Check if file exists directly
      ii. If no extension, try with each supported extension
      iii. Return first matching file
3. If no match found, return None
4. If file is found and evidence is provided:
   a. Read file content
   b. Search for evidence using regex
   c. If found, determine line number and extract context
   d. Calculate highlighting positions
   e. Return CodeContext object

**COMPLEXITY**:
- Time: O(n) where n is the number of lines in the source file
- Space: O(m) where m is the size of the source file

**CONSTRAINTS**:
- Requires accurate mapping between URLs and local files
- Performance depends on file system access speed
- May not work with dynamically generated content
- Limited to supported file extensions

#### ALGORITHM: Extended Spidering

**PURPOSE**: Discovers hidden content and files by checking common paths and patterns

**INPUT**: 
- Base URL of the target application

**OUTPUT**: 
- Side effect: ZAP's site tree is populated with discovered resources

**STEPS**:
1. Define list of common files and paths to check (robots.txt, sitemap.xml, etc.)
2. For each path in the list:
   a. Construct full URL by combining base URL with path
   b. Access URL using ZAP API
   c. Add short delay to avoid overloading server
   d. Handle any exceptions gracefully

**COMPLEXITY**:
- Time: O(n) where n is the number of common paths checked
- Space: O(1) as minimal temporary data is stored

**CONSTRAINTS**:
- Limited by the predefined list of common paths
- Respects server load by adding delays between requests
- Depends on ZAP API for URL access

#### ALGORITHM: AJAX Spider Early Termination

**PURPOSE**: Optimizes AJAX crawling by detecting when no new content is being discovered

**INPUT**: 
- Target URL to crawl
- Monitoring interval in seconds
- Maximum time in seconds

**OUTPUT**: 
- Side effect: ZAP's site tree is populated with AJAX-rendered content

**STEPS**:
1. Start AJAX Spider with configured settings
2. Initialize variables for monitoring:
   a. start_time = current time
   b. last_result_count = 0
   c. stagnant_cycles = 0
3. Enter monitoring loop:
   a. Get current AJAX Spider status
   b. Calculate elapsed time
   c. If status is "running":
      i. Get current result count
      ii. Log progress (rate-limited)
      iii. If current_count == last_result_count:
          - Increment stagnant_cycles
          - If stagnant_cycles >= 3 AND elapsed > 60 seconds:
            * Stop AJAX Spider early
            * Break loop
      iv. Otherwise:
          - Reset stagnant_cycles = 0
          - Update last_result_count = current_count
   d. If status is not "running", log completion and break loop
   e. If elapsed time > max_time, stop AJAX Spider and break loop
   f. Sleep for specified interval
4. Log final results count

**COMPLEXITY**:
- Time: O(t) where t is the duration of the AJAX spider run
- Space: O(1) as minimal state is maintained

**CONSTRAINTS**:
- Requires at least 60 seconds of runtime before early termination
- Needs 3 consecutive check cycles with no new results
- Maximum runtime capped by max_time parameter
- Early termination accuracy depends on check interval

### 8.2 Design Decisions

#### DECISION: Enhanced Source Code Mapping

**CONTEXT**: Standard ZAP scans identify vulnerabilities by URL but don't connect them to source code, making remediation difficult.

**OPTIONS CONSIDERED**:
1. **Custom Source Code Mapper** - Pros: Tailored to project structure, flexible mapping rules. Cons: Complex implementation, requires configuration.
2. **Git Integration** - Pros: Automatic code tracking, version aware. Cons: Requires Git, more dependencies, complex setup.
3. **No Source Mapping** - Pros: Simpler implementation, less overhead. Cons: Remediation more difficult, manual correlation needed.

**DECISION OUTCOME**: Implemented custom source code mapper that supports both explicit mapping configuration and automatic inference from root directory.

**CONSEQUENCES**: 
- Positive: Developers can quickly locate vulnerable code
- Positive: Flexibility in mapping configuration
- Negative: Requires some setup for optimal results
- Negative: Slight performance overhead during vulnerability processing

#### DECISION: Combined Traditional and AJAX Spidering

**CONTEXT**: Modern web applications use JavaScript to render content, which traditional crawlers can't discover.

**OPTIONS CONSIDERED**:
1. **Traditional Spider Only** - Pros: Fast, low resource usage. Cons: Misses JavaScript-rendered content.
2. **AJAX Spider Only** - Pros: Finds JavaScript content. Cons: Slow, resource-intensive, potential redundancy.
3. **Combined Approach** - Pros: Comprehensive discovery, optimized workflow. Cons: More complex, longer total scan time.

**DECISION OUTCOME**: Implemented combined approach with traditional spider first, followed by AJAX spider, with early termination logic for AJAX spider.

**CONSEQUENCES**: 
- Positive: Comprehensive content discovery
- Positive: Early termination reduces unnecessary scanning
- Positive: Quick scan option for faster results when needed
- Negative: Full scans take longer than single-spider approach
- Negative: Higher resource usage

#### DECISION: Process-Based ZAP Daemon Management

**CONTEXT**: ZAP can be embedded within Java applications or run as a separate process.

**OPTIONS CONSIDERED**:
1. **Embedded Mode** - Pros: Tighter integration, potentially faster. Cons: JVM constraints, complex Python integration.
2. **Process-Based Daemon** - Pros: Isolation, independent resources, cleaner integration. Cons: Inter-process communication overhead, startup time.
3. **Docker Container** - Pros: Complete isolation, reproducible environment. Cons: Docker dependency, more complex setup.

**DECISION OUTCOME**: Implemented process-based daemon approach with robust cleanup and configuration.

**CONSEQUENCES**: 
- Positive: Clean separation between Python code and ZAP
- Positive: Independent resource allocation and JVM settings
- Positive: Easier to handle ZAP crashes or hangs
- Negative: Startup overhead for each scan
- Negative: Inter-process communication latency

#### DECISION: Optimized Scan Configurations

**CONTEXT**: Default ZAP configurations are balanced but not optimized for specific scanning scenarios.

**OPTIONS CONSIDERED**:
1. **Default ZAP Settings** - Pros: Well-tested, balanced. Cons: Not optimized for performance or thoroughness.
2. **Maximum Coverage Settings** - Pros: Most thorough, finds more vulnerabilities. Cons: Very slow, resource-intensive.
3. **Context-Aware Configurations** - Pros: Balanced approach, quick_scan option. Cons: More complex implementation.

**DECISION OUTCOME**: Implemented context-aware configurations with both comprehensive and quick scan options.

**CONSEQUENCES**: 
- Positive: Flexible scanning options for different needs
- Positive: Performance-optimized configurations
- Positive: Comprehensive scan with all rules enabled
- Negative: More complex configuration management
- Negative: Potential for false positives with low thresholds

## 9. Integration Points

### 9.1 External Systems

#### SYSTEM: OWASP ZAP

**PURPOSE**: Core security scanning engine that performs all vulnerability detection

**INTERFACE**:
- Protocol: Local process + HTTP API
- Authentication: API key (configured at startup)
- Endpoints:
  - core: Basic operations and access to ZAP core functionality
  - spider: Traditional web crawler functionality
  - ajaxSpider: JavaScript-aware crawling
  - ascan: Active scanning operations
  - pscan: Passive scanning operations
  - alerts: Retrieving detected vulnerabilities

**FAILURE MODES**:
- ZAP process crashes: Handled by cleanup and error reporting
- Port conflicts: Resolved by dynamic port selection
- Memory exhaustion: Mitigated by JVM heap configuration
- API connection failures: Automatic retry with exponential backoff

**CONSTRAINTS**:
- Memory usage increases with target size and complexity
- Performance varies with scan configuration
- Some functionality requires specific ZAP versions
- Limited to web application security testing

### 9.2 Internal Interfaces

#### Component Interface: ZAPScanner to Source Code Mapping

- `set_source_code_mapping(mapping: Dict[str, str], root_dir: Optional[str] = None)`: Configures URL to file path mapping
- `set_source_code_root(root_dir: str)`: Sets root directory for source code
- `_url_to_source_file(url: str) -> Optional[str]`: Internal method to convert URL to file path
- `_get_affected_code(alert: Dict[str, Any]) -> Optional[CodeContext]`: Extract code context from alerts

#### Component Interface: ZAPScanner to ZAP Process Management

- `_find_zap_installation() -> Path`: Locates ZAP executable or JAR file
- `_start_zap_daemon() -> bool`: Starts ZAP as a background process
- `_cleanup_existing_zap()`: Terminates ZAP processes
- `_build_zap_command(zap_path: Path) -> List[str]`: Constructs ZAP launch command

#### Component Interface: ZAPScanner to Scan Configuration

- `_configure_passive_scanning()`: Sets up passive scanning rules
- `_configure_active_scanning()`: Sets up active scanning rules
- `_get_java_opts() -> List[str]`: Gets JVM optimization settings
- `_get_zap_args() -> List[str]`: Gets ZAP configuration arguments

## 10. Operational Context

### 10.1 Deployment Model

**Deployment environments**:
- Local development workstations for interactive scanning
- CI/CD pipelines for automated security testing
- Security testing servers for dedicated scanning operations
- Integration into DevSecOps toolchains

**Deployment process**:
1. Install Python 3.7+ and Java 11+
2. Install OWASP ZAP 2.14.0 or later
3. Install Python dependencies (zapv2, requests)
4. Configure environment variables if custom settings needed
5. Initialize ZAPScanner with base path for logs and results
6. Invoke scanning methods with target URLs

**Configuration management**:
- Environment variables for customizing ZAP behavior
- Source code mapping configuration for vulnerability-to-code mapping
- Scan configuration options (e.g., quick_scan flag)
- Optional output file paths for reports

### 10.2 Monitoring

**Key metrics tracked**:
- Scan duration (total and by phase)
- Vulnerability counts by risk level
- Source code mapping success rate
- Memory usage of ZAP process
- Spider and AJAX spider coverage
- Passive and active scan completion percentages

**Alert thresholds**:
- Scan duration exceeding configured maximum
- High-risk vulnerabilities detected
- ZAP process memory exceeding 80% of allocated heap
- Failed scans or unexpected terminations

**Logging strategy**:
- Comprehensive logging with configurable verbosity
- Separate logs for ZAP daemon and Python wrapper
- Detailed progress tracking for long-running operations
- Performance metrics logging for optimization
- File-based logging with rotation for persistence

### 10.3 Common Issues

#### ISSUE: ZAP Process Fails to Start

**SYMPTOMS**: 
- Error messages about ZAP not starting
- Return of empty results
- Java-related error messages

**CAUSES**:
- Missing or incompatible Java installation
- Incorrect ZAP installation path
- Port conflicts with existing services
- Insufficient memory for JVM heap

**RESOLUTION**:
1. Verify Java installation with `java -version`
2. Check ZAP installation by running it manually
3. Check if specified ports are available
4. Check system memory and adjust heap settings if needed
5. Look for detailed errors in ZAP log file

**PREVENTION**:
- Set ZAP_HOME environment variable to correct path
- Ensure Java 11+ is installed and in PATH
- Keep ZAP updated to latest version
- Properly clean up ZAP processes after each scan

#### ISSUE: AJAX Spider Takes Too Long

**SYMPTOMS**: 
- Scans running much longer than expected
- Progress stuck at AJAX Spider phase
- High CPU usage with limited progress

**CAUSES**:
- Complex JavaScript applications with many states
- Single-page applications with deep navigation paths
- Infinite scrolling or dynamically loading content
- Browser rendering performance issues

**RESOLUTION**:
1. Set `quick_scan=True` for faster but less thorough scanning
2. Configure `ZAP_AJAX_TIMEOUT` environment variable to lower value
3. Stop current scan and restart with focused AJAX spider
4. Check network connectivity to target application

**PREVENTION**:
- Configure appropriate timeouts based on application complexity
- Use early termination logic for AJAX spider (implemented in code)
- Consider using contextual scanning for specific application areas

#### ISSUE: Poor Source Code Mapping

**SYMPTOMS**: 
- Vulnerabilities reported without source code context
- Incorrect file mappings
- Missing line numbers or context

**CAUSES**:
- Missing or incorrect source code mapping configuration
- Build processes that transform or minify code
- Dynamic code generation
- URL structure not matching file structure

**RESOLUTION**:
1. Configure explicit source code mapping with `set_source_code_mapping()`
2. Ensure source code root directory is correctly set
3. Check that source files match deployed application versions
4. Try scanning unminified/development version of application

**PREVENTION**:
- Maintain accurate mapping between URLs and source files
- Consider source maps for JavaScript applications
- Use build process that preserves file structure
- Document URL to file path conventions

## 11. Task-Oriented Guides

### 11.1 Common Development Tasks

#### TASK: Scan a Local Web Application

**PREREQUISITES**:
- Python 3.7+ installed
- Java 11+ installed
- OWASP ZAP 2.14.0+ installed
- Local web application running

**STEPS**:
1. Import the ZAPScanner module:
   ```python
   from zap_scanner import create_scanner, ZAPScanner
   from pathlib import Path
   ```

2. Create scanner instance with base path for logs:
   ```python
   scanner = create_scanner(Path("./zap_results"))
   ```

3. Configure source code mapping (optional but recommended):
   ```python
   scanner.set_source_code_root("./my_web_app")
   # Or for more precise mapping:
   scanner.set_source_code_mapping({
       "http://localhost:5501/js/": "./my_web_app/src/js",
       "http://localhost:5501/api/": "./my_web_app/src/api"
   })
   ```

4. Perform the scan:
   ```python
   # For comprehensive scan:
   vulnerabilities, summary = scanner.scan_target("http://localhost:5501")
   
   # For quicker scan:
   vulnerabilities, summary = scanner.scan_target("http://localhost:5501", quick_scan=True)
   ```

5. Generate and save report:
   ```python
   report = scanner.generate_affected_code_report(
       vulnerabilities, 
       "./zap_results/vulnerability_report.md"
   )
   ```

6. Process scan results:
   ```python
   # Print summary
   print(f"Scan completed in {summary['duration_seconds']} seconds")
   print(f"Found {len(vulnerabilities)} vulnerabilities:")
   print(f" - High: {summary['risk_counts']['High']}")
   print(f" - Medium: {summary['risk_counts']['Medium']}")
   print(f" - Low: {summary['risk_counts']['Low']}")
   
   # Access individual vulnerabilities
   for vuln in vulnerabilities:
       if vuln.risk == "High":
           print(f"High risk: {vuln.name} at {vuln.url}")
           if vuln.affected_code:
               print(f"In file: {vuln.source_file}")
               print(f"Snippet: {vuln.affected_code.snippet[:100]}...")
   ```

**VERIFICATION**:
- Check for vulnerability report file
- Verify scan summary contains expected information
- Confirm vulnerabilities are mapped to source code where applicable

#### TASK: Integrate Scanner with CI/CD Pipeline

**PREREQUISITES**:
- CI/CD system (Jenkins, GitHub Actions, GitLab CI, etc.)
- Python and Java installed in CI environment
- Access to target application from CI environment

**STEPS**:
1. Create a script file `security_scan.py`:
   ```python
   import sys
   import json
   from pathlib import Path
   from zap_scanner import create_scanner
   
   # Get target from command line argument
   target_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5501"
   
   # Create scanner with results in CI workspace
   scanner = create_scanner(Path("./security_results"))
   
   # Set source code mapping if needed
   scanner.set_source_code_root("./")
   
   # Run scan
   vulnerabilities, summary = scanner.scan_target(target_url)
   
   # Generate report
   scanner.generate_affected_code_report(
       vulnerabilities, 
       "./security_results/vulnerability_report.md"
   )
   
   # Save JSON results
   with open("./security_results/scan_results.json", "w") as f:
       results = {
           "summary": summary,
           "vulnerabilities": [vars(v) for v in vulnerabilities]
       }
       json.dump(results, f, indent=2, default=str)
   
   # Exit with error code if high risks found
   sys.exit(1 if summary["risk_counts"]["High"] > 0 else 0)
   ```

2. Add CI configuration (e.g., GitHub Actions workflow):
   ```yaml
   name: Security Scan
   
   on:
     push:
       branches: [ main ]
     pull_request:
       branches: [ main ]
   
   jobs:
     zap-scan:
       runs-on: ubuntu-latest
       
       steps:
       - uses: actions/checkout@v2
       
       - name: Set up Python
         uses: actions/setup-python@v2
         with:
           python-version: '3.9'
       
       - name: Set up Java
         uses: actions/setup-java@v2
         with:
           java-version: '11'
           distribution: 'adopt'
       
       - name: Install dependencies
         run: |
           python -m pip install --upgrade pip
           pip install python-owasp-zap-v2.4 requests
       
       - name: Install ZAP
         run: |
           mkdir -p ~/.ZAP
           wget -O zap.zip https://github.com/zaproxy/zaproxy/releases/download/v2.14.0/ZAP_2.14.0_Linux.zip
           unzip zap.zip -d ~/.ZAP
           echo "ZAP_HOME=$HOME/.ZAP/ZAP_2.14.0" >> $GITHUB_ENV
       
       - name: Start test application
         run: |
           # Start your web application here
           # Example: npm start & echo $! > app.pid
       
       - name: Run security scan
         run: python security_scan.py http://localhost:5501
       
       - name: Upload scan results
         uses: actions/upload-artifact@v2
         with:
           name: security-scan-results
           path: ./security_results/
   ```

3. Configure branch protection rules to require passing security scan

**VERIFICATION**:
- CI job completes successfully
- Security scan results are uploaded as artifacts
- CI job fails if high-risk vulnerabilities are found

### 11.2 Debugging Approaches

#### SCENARIO: Scanner Cannot Find ZAP Installation

**DIAGNOSTIC STEPS**:
1. Check error message for clues:
   ```python
   try:
       scanner = create_scanner(Path("./zap_results"))
   except Exception as e:
       print(f"Error: {str(e)}")
   ```

2. Verify ZAP installation:
   - Windows: Check Program Files and Program Files (x86)
   - Linux: Check /usr/share/zaproxy
   - macOS: Check /Applications/OWASP ZAP.app

3. Check ZAP_HOME environment variable:
   ```python
   import os
   print(f"ZAP_HOME: {os.environ.get('ZAP_HOME', 'Not set')}")
   ```

4. Verify Java installation:
   ```bash
   java -version
   ```

**COMMON CAUSES**:
- ZAP not installed or installed in non-standard location
- ZAP_HOME environment variable not set correctly
- Insufficient permissions to access ZAP installation
- Java not installed or incorrect version

**RESOLUTION**:
1. Install ZAP if not present:
   ```bash
   # Download from https://www.zaproxy.org/download/
   # Or use package manager if available
   ```

2. Set ZAP_HOME environment variable:
   ```bash
   # Windows
   set ZAP_HOME=C:\Program Files\OWASP\Zed Attack Proxy
   
   # Linux/macOS
   export ZAP_HOME=/path/to/zaproxy
   ```

3. Specify ZAP location explicitly:
   ```python
   # If modifying code is an option, add search paths
   base_path = Path("./zap_results")
   scanner = ZAPScanner(base_path)
   # Add known installation path
   scanner._find_zap_installation = lambda: Path("/specific/path/to/zap.sh")
   ```

#### SCENARIO: Scan Running Too Slowly

**DIAGNOSTIC STEPS**:
1. Enable more verbose logging:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. Monitor current phase through logs or status object:
   ```python
   # If using start_scan method:
   scan_key = f"{model}-{app_num}"
   status = scanner._scans.get(scan_key, {}).get("status")
   print(f"Current status: {status.status if status else 'Unknown'}")
   print(f"Progress: {status.progress if status else 'Unknown'}%")
   ```

3. Check ZAP log file for bottlenecks:
   ```python
   zap_log_path = scanner.zap_log
   with open(zap_log_path, 'r') as f:
       log_tail = f.readlines()[-50:]  # Last 50 lines
       print("".join(log_tail))
   ```

**COMMON CAUSES**:
- AJAX Spider taking too long on complex applications
- Large number of URLs discovered during spidering
- Target application responding slowly
- Insufficient resources (CPU, memory) for ZAP process

**RESOLUTION**:
1. Use quick scan mode:
   ```python
   vulnerabilities, summary = scanner.scan_target(target_url, quick_scan=True)
   ```

2. Reduce timeouts and duration limits:
   ```python
   # Set environment variables before creating scanner
   import os
   os.environ['ZAP_MAX_SCAN_DURATION'] = '60'  # 60 minutes
   os.environ['ZAP_AJAX_TIMEOUT'] = '60'  # 60 seconds
   ```

3. Increase resources for ZAP process:
   ```python
   # Modify ZAP_DEFAULT_HEAP_SIZE in zap_scanner.py
   # Or if modifying code:
   scanner._get_java_opts = lambda: ['-Xmx6G', '-XX:+UseG1GC']
   ```

4. Limit scan scope to specific paths:
   ```python
   # Not directly supported, but could implement by:
   # 1. Modifying scan target URL to include specific path
   # 2. Extending the module to support includePaths parameter
   ```

## 12. Project Glossary

| Term | Definition | Context |
|------|------------|---------|
| ZAP | Zed Attack Proxy, a free security tool from OWASP | Core scanning engine |
| OWASP | Open Web Application Security Project | Security standards organization |
| Active Scanning | Testing that sends potentially malicious payloads to application | Vulnerability detection method |
| Passive Scanning | Non-intrusive analysis of HTTP traffic | Information gathering method |
| Spider | Web crawler that discovers application content | Content discovery component |
| AJAX Spider | JavaScript-aware crawler using headless browser | Modern web app content discovery |
| Alert | Security issue detected during scanning | Vulnerability reporting |
| Evidence | The specific content that triggered an alert | Vulnerability proof |
| CWE | Common Weakness Enumeration, standard for vulnerability types | Vulnerability classification |
| WASC | Web Application Security Consortium ID | Alternative vulnerability classification |
| Source Code Mapping | Process of linking URLs to local source files | Vulnerability remediation feature |
| Risk Level | Severity classification (High, Medium, Low, Info) | Vulnerability prioritization |
| Quick Scan | Faster scanning mode with reduced thoroughness | Performance optimization feature |
| ZAP API | RESTful API for controlling ZAP programmatically | Integration interface |
| ZAPv2 | Python library for interacting with ZAP API | API client |
| CodeContext | Source code snippet with vulnerability highlighting | Remediation assistance |

This comprehensive knowledge base provides a detailed understanding of the ZAP Scanner project, its architecture, functionality, and usage patterns. It should help users effectively work with and extend the scanner for application security testing.