# AI Model Management System Documentation

Based on the provided code, I've created a comprehensive documentation for the AI Model Management System project, following your template structure.

## 1. Project Identity Card

**PROJECT NAME:** AI Model Management System  
**PRIMARY PURPOSE:** Web-based dashboard to manage, monitor, and test AI model applications running in Docker containers  
**DOMAIN:** MLOps / AI Infrastructure Management  
**DEVELOPMENT STAGE:** Production (based on feature completeness)  
**REPOSITORY URL:** [Not specified in provided code]  
**DOCUMENTATION URL:** [Not specified in provided code]  

## 2. Project Context

### 2.1 Problem Statement

This project solves the problem of managing multiple AI model deployments running in Docker containers. It provides a unified interface for monitoring application status, performing security testing, and conducting performance analysis.

The users experiencing this problem are MLOps engineers, data scientists, and DevOps personnel who need to manage multiple AI model deployments.

Without this system, organizations would face:
- Manual container management for each deployment
- Lack of centralized monitoring and health checks
- No standardized security scanning or performance benchmarking
- Increased operational overhead and risk

### 2.2 Solution Overview

Core approach:
- Flask-based web dashboard with modular blueprints for different functionality
- Docker integration for container management
- Security scanning with ZAP integration
- Performance testing with Locust
- GPT4All integration for requirements analysis

Key differentiators:
- Unified dashboard for both operations and security
- Multiple specialized analysis tools in one interface
- Comprehensive logging and monitoring

Critical constraints:
- Requires Docker for containerization
- Depends on external tools (ZAP, GPT4All) for advanced features
- Web-based interface rather than CLI/API-only approach

### 2.3 User Personas

Primary users:
- MLOps engineers: Technical expertise in both ML and operations
- DevOps personnel: Container and infrastructure expertise
- Data scientists: ML expertise with limited operations knowledge

Key user workflows:
- Monitoring app deployment status and health
- Starting/stopping/restarting containers
- Running security scans and viewing vulnerabilities
- Conducting performance tests under various load scenarios
- Analyzing security issues with AI assistance

User expectations:
- Real-time application status
- Detailed logs and diagnostics
- Comprehensive security analysis
- Reliable performance metrics

## 3. Architecture Map

### 3.1 System Diagram

```
┌───────────────────────┐
│  AI Model Management  │
│       System          │
└───────────┬───────────┘
            │
            v
┌───────────────────────┐
│    Flask Application   │
└───────────┬───────────┘
            │
 ┌──────────┴───────────┐
 │                      │
 v                      v
┌────────────┐    ┌─────────────┐
│ Blueprints │    │  Services   │
└───┬────────┘    └──────┬──────┘
    │                    │
    v                    v
┌────────────┐    ┌─────────────────────────────┐
│ main_bp    │    │ DockerManager               │
│ api_bp     │◄───►SystemHealthMonitor          │
│ analysis_bp│    │ ScanManager                 │
│ perf_bp    │    │ Backend/Frontend Analyzers  │
│ zap_bp     │    │ GPT4All Analyzer            │
│ gpt4all_bp │    └─────────────────────────────┘
└────┬───────┘
     │
     v
┌────────────────────────┐
│ External Integrations  │
│ - Docker               │
│ - ZAP Scanner          │
│ - Locust               │
│ - GPT4All              │
└────────────────────────┘
```

**Legend:**
→ : Data flow
⟲ : Processing loop
□ : External system
■ : Internal component

### 3.2 Component Inventory

| Component Name | Type | Purpose | Interfaces | Dependencies |
|----------------|------|---------|------------|--------------|
| MainBlueprint | Flask Blueprint | Dashboard and container management | Routes: /, /docker-logs, /status, etc. | DockerManager |
| APIBlueprint | Flask Blueprint | API endpoints for system info | Routes: /api/system-info, /api/container, etc. | DockerManager, SystemHealthMonitor |
| AnalysisBlueprint | Flask Blueprint | Security analysis routes | Routes: /analysis/backend-security, etc. | Security analyzers |
| PerformanceBlueprint | Flask Blueprint | Performance testing | Routes: /performance/*, /reports, etc. | Performance tester |
| ZAPBlueprint | Flask Blueprint | ZAP security scanning | Routes: /zap/*, /scan, etc. | ZAP Scanner, ScanManager |
| GPT4AllBlueprint | Flask Blueprint | AI-powered analysis | Routes: /gpt4all/*, /api/*, etc. | GPT4All analyzer |
| DockerManager | Service | Container operations | Container management methods | Docker |
| ScanManager | Service | Manages security scans | Scan state tracking methods | None |
| SystemHealthMonitor | Service | System health checking | Health check methods | psutil (optional) |

### 3.3 Data Flow Sequences

**Operation: View Dashboard**
1. User requests dashboard (`/`)
2. `index()` handler gets all apps with `get_all_apps()`
3. For each app, `get_app_container_statuses()` calls DockerManager
4. DockerManager queries Docker for container status
5. Results formatted and rendered in template

**Operation: ZAP Security Scan**
1. User POSTs to `/zap/scan/{model}/{app_num}`
2. `start_zap_scan()` creates scan entry in ScanManager
3. Background thread initialized with app context
4. Thread creates ZAP scanner and updates status to STARTING
5. Scanner performs scan, updates progress in ScanManager
6. Results saved to file and status updated to COMPLETE/FAILED
7. User polls `/zap/scan/{model}/{app_num}/status` for updates

**Operation: Batch Docker Action**
1. User POSTs to `/batch/{action}/{model}`
2. `batch_docker_action()` gets apps for model
3. For each app, `handle_docker_action()` executed
4. DockerManager performs Docker operations
5. Results collected and returned as JSON response

## 4. Core Data Structures

**DATA STRUCTURE: ScanState (Enum)**

PURPOSE: Defines the possible states for a ZAP scan

SCHEMA:
- NOT_RUN: "Not Run" - Scan has never been initiated for this app
- STARTING: "Starting" - Scan thread initiated, ZAP setup in progress
- SPIDERING: "Spidering" - Spidering phase active
- SCANNING: "Scanning" - Active scanning phase active
- COMPLETE: "Complete" - Scan finished successfully
- FAILED: "Failed" - Scan finished, but reported failure
- ERROR: "Error" - Scan couldn't start/run due to setup/thread error
- STOPPED: "Stopped" - Scan was explicitly stopped by user

INVARIANTS:
- State transitions follow logical progression
- Terminal states: COMPLETE, FAILED, ERROR, STOPPED

**DATA STRUCTURE: APIResponse**

PURPOSE: Standardized API response format

SCHEMA:
- success: bool - Whether the operation succeeded
- message: str [optional] - Human-readable success message
- error: str [optional] - Error message if operation failed
- code: http.HTTPStatus - HTTP status code
- data: dict [optional] - Additional response data

INVARIANTS:
- Either message or error should be present, not both
- If success is False, error should be present

**DATA STRUCTURE: ZapVulnerability**

PURPOSE: Represents a security vulnerability found by ZAP scanner

SCHEMA:
- name: str - Vulnerability name/type
- risk: str - Risk level (High/Medium/Low/Info)
- description: str - Vulnerability details
- affected_code: CodeContext [optional] - Code context if available

RELATIONSHIPS:
- HAS_ONE CodeContext (optional)

EXAMPLES:
```json
{
  "name": "SQL Injection",
  "risk": "High",
  "description": "Possible SQL injection vulnerability...",
  "affected_code": {
    "file": "app.py",
    "line": 42,
    "snippet": "query = 'SELECT * FROM users WHERE id = ' + user_id"
  }
}
```

## 5. Function Reference

**FUNCTION: get_app_container_statuses**

PURPOSE: Retrieves status of Docker containers for a specific app

SIGNATURE:
```python
Dict get_app_container_statuses(str model, int app_num, DockerManager docker_manager)
```

PARAMETERS:
- model: AI model name (e.g., "Llama")
- app_num: Application number (1-based)
- docker_manager: Instance of DockerManager service

RETURNS:
- Success case: Dict with backend and frontend container status
- Error case: Dict with error message

BEHAVIOR:
1. Validates model and app_num
2. Gets container names using get_container_names()
3. Queries Docker for container info
4. Processes and formats status information
5. Returns formatted status dictionary

EXAMPLES:
```python
# Success example:
statuses = get_app_container_statuses("Llama", 1, docker_manager)
# Returns:
{
  "backend": {"running": True, "status": "running", "health": "healthy", "id": "abc123"},
  "frontend": {"running": True, "status": "running", "health": "healthy", "id": "def456"}
}

# Error example:
statuses = get_app_container_statuses("Invalid", 99, docker_manager)
# Returns:
{"error": "Invalid model or app number"}
```

**FUNCTION: start_zap_scan**

PURPOSE: Initiates a ZAP security scan in a background thread

SIGNATURE:
```python
Dict start_zap_scan(str model, int app_num)
```

PARAMETERS:
- model: AI model name
- app_num: Application number

RETURNS:
- Success case: Dict with scan_id and status
- Error case: APIResponse with error details

BEHAVIOR:
1. Checks if scan already running for this app
2. Creates new scan entry in ScanManager
3. Launches background thread for scanning
4. Thread initializes scanner and runs scan
5. Updates scan status throughout process
6. Returns immediately with scan ID for polling

EXAMPLES:
```python
# Success example:
result = start_zap_scan("Llama", 1)
# Returns:
{"status": "started", "scan_id": "abc123"}

# Error example (scan already running):
result = start_zap_scan("Llama", 1)
# Returns:
APIResponse(success=False, error="A scan is already running for this app.")
```

## 6. API Reference

**ENDPOINT: GET /api/system-info**

PURPOSE: Get detailed system information for the dashboard

REQUEST:
- Headers: None required
- Query Parameters: None
- Body: None
- Authentication: None specified

RESPONSE:
- Success (200):
```json
{
  "timestamp": "2023-01-01T12:34:56.789Z",
  "system": {
    "cpu_percent": 25.5,
    "memory_percent": 60.2,
    "memory_used": 8000000000,
    "memory_total": 16000000000,
    "disk_percent": 45.0,
    "disk_used": 256000000000,
    "disk_total": 512000000000,
    "uptime_seconds": 86400
  },
  "docker": {
    "healthy": true,
    "client_available": true,
    "containers": {
      "running": 5,
      "stopped": 2,
      "total": 7
    }
  },
  "apps": {
    "total": 10,
    "models": {
      "Llama": 3,
      "Claude": 5,
      "GPT4": 2
    },
    "status": {
      "running": 6,
      "partial": 2,
      "stopped": 2
    }
  }
}
```

**ENDPOINT: POST /zap/scan/{model}/{app_num}**

PURPOSE: Start a comprehensive ZAP security scan for a specific app

REQUEST:
- Headers: None required
- URL Parameters:
  - model: Model name (string)
  - app_num: App number (integer)
- Body: None
- Authentication: None specified

RESPONSE:
- Success (200):
```json
{
  "status": "started",
  "scan_id": "abc123def456"
}
```
- Error (409): Scan already running
- Error (500): Server error details

**ENDPOINT: GET /zap/scan/{model}/{app_num}/status**

PURPOSE: Get the current status of a ZAP scan

REQUEST:
- Headers: None required
- URL Parameters:
  - model: Model name
  - app_num: App number
- Query Parameters: None
- Authentication: None specified

RESPONSE:
- Success (200):
```json
{
  "status": "scanning",
  "progress": 45,
  "spider_progress": 100,
  "passive_progress": 75,
  "active_progress": 30,
  "ajax_progress": 0,
  "high_count": 2,
  "medium_count": 5,
  "low_count": 10,
  "info_count": 15,
  "scan_id": "abc123def456",
  "start_time": "2023-01-01T12:00:00Z",
  "end_time": null
}
```

## 7. Implementation Context

### 7.1 Technology Stack

| Layer | Technology | Purpose | Version | Notes |
|-------|------------|---------|---------|-------|
| Framework | Flask | Web application framework | Not specified | Blueprint architecture |
| Containerization | Docker | Container management | Not specified | Core for app deployment |
| System Monitoring | psutil | System resource monitoring | Optional | Used for CPU, memory, disk metrics |
| Security Testing | OWASP ZAP | Security scanning | Not specified | Integrated for vulnerability scanning |
| Performance Testing | Locust | Load testing | Not specified | For performance testing |
| AI Integration | GPT4All | Requirements analysis | Not specified | Used for code analysis |

### 7.2 Dependencies

| Dependency | Version | Purpose | API Surface Used | Alternatives Considered |
|------------|---------|---------|-----------------|-------------------------|
| Flask | Not specified | Web framework | Blueprint, request handling | None mentioned |
| psutil | Optional | System metrics | CPU, memory, disk usage | None mentioned |
| Docker | Not specified | Container management | Container operations | None mentioned |
| OWASP ZAP | Not specified | Security scanning | Scanning API | None mentioned |
| Locust | Not specified | Performance testing | Test execution | None mentioned |
| GPT4All | Not specified | AI analysis | API client | None mentioned |

### 7.3 Environment Requirements

- Runtime dependencies: 
  - Docker daemon running
  - Python with required packages
  - ZAP scanner installation (for security scanning)
  - GPT4All server (for AI analysis)

- Configuration requirements:
  - Flask app configuration
  - Docker socket access
  - Base directory for app structure
  - Port configuration (BASE_FRONTEND_PORT, PORTS_PER_APP)

- Resource needs:
  - Memory: Sufficient for ZAP scanner (resource-intensive)
  - Disk: Space for Docker images and scan results
  - Network: Access to Docker daemon and containers

## 8. Reasoning Patterns

### 8.1 Key Algorithms

**ALGORITHM: ZAP Security Scan Process**

PURPOSE: Detect security vulnerabilities in application code and running services

INPUT: 
- Model name
- App number
- App directory path

OUTPUT: 
- JSON file with security vulnerabilities
- Markdown file with code analysis report

STEPS:
1. Initialize ZAP scanner with base directory
2. Set source code root directory to app path
3. Update scan status to STARTING
4. Start comprehensive scan (blocks until complete)
   a. Spider application to discover endpoints
   b. Run passive scan on discovered endpoints
   c. Run active scan for vulnerabilities
   d. Analyze code for vulnerabilities
   e. Process results and generate reports
5. Save results to JSON and markdown files
6. Update final scan status based on outcome

COMPLEXITY:
- Time: O(n) where n is application code size and endpoint count
- Space: O(v) where v is number of vulnerabilities found

CONSTRAINTS:
- ZAP scanner must be available
- Application code must be accessible
- Resource-intensive process (memory, CPU)
- Can take several minutes for complex applications

**ALGORITHM: Performance Test Execution**

PURPOSE: Measure application performance under load

INPUT:
- Model name
- Port number
- Test configuration (users, duration, endpoints)

OUTPUT:
- Performance test results
- Graphs and metrics

STEPS:
1. Validate test parameters
2. Format endpoint configurations
3. Generate test name with timestamp
4. Execute Locust test with parameters
5. Collect and process results
6. Generate visualization graphs
7. Save consolidated results

COMPLEXITY:
- Time: O(d) where d is test duration
- Space: O(r) where r is result data size

CONSTRAINTS:
- Target application must be running
- Test duration impacts overall execution time
- High user counts may impact system performance

### 8.2 Design Decisions

**DECISION: Flask Blueprint Architecture**

CONTEXT: Need to organize different functionality areas while maintaining a single application

OPTIONS CONSIDERED:
1. Single Flask application with all routes - Simple but becomes unwieldy with growth
2. Blueprint architecture - More modular and maintainable
3. Separate microservices - Most scalable but significantly more complex

DECISION OUTCOME: Blueprint architecture for modularity with manageable complexity

CONSEQUENCES:
- Positive: Code organization by functional area
- Positive: Easier to maintain and extend
- Negative: More initial complexity than simple app
- Negative: Shared application state (not as isolated as microservices)

**DECISION: Background Thread for ZAP Scans**

CONTEXT: Need to run potentially long-running security scans without blocking web requests

OPTIONS CONSIDERED:
1. Synchronous scanning - Simpler but blocks request until complete
2. Background threads - Non-blocking but requires thread management
3. Separate worker processes/queue - Most robust but more complex

DECISION OUTCOME: Background threads with status tracking in ScanManager

CONSEQUENCES:
- Positive: Non-blocking user experience
- Positive: Shared memory access to scan state
- Negative: Thread management complexity
- Negative: Potential resource contention

## 9. Integration Points

### 9.1 External Systems

**SYSTEM: Docker**

PURPOSE: Run and manage application containers

INTERFACE:
- Protocol: Docker API
- Authentication: None specified
- Endpoints: Container operations (list, start, stop, logs)

FAILURE MODES:
- Docker daemon unavailable: Dashboard shows error status
- Container operation failure: Operation returns error message

CONSTRAINTS:
- Docker version compatibility
- Access to Docker socket

**SYSTEM: OWASP ZAP**

PURPOSE: Security scanning of applications

INTERFACE:
- Protocol: Process execution and API
- Authentication: None specified
- Endpoints: Scan operations

FAILURE MODES:
- ZAP process fails to start: Scan status updated to ERROR
- Scan operation timeout: Scan status updated to FAILED

CONSTRAINTS:
- ZAP installation and compatibility
- Resource requirements for scanning

**SYSTEM: GPT4All Server**

PURPOSE: AI-powered requirements analysis

INTERFACE:
- Protocol: HTTP API
- Authentication: None specified
- Endpoints: Model operations, completion

FAILURE MODES:
- Server unavailable: Error displayed in UI
- Completion failure: Error in results

CONSTRAINTS:
- GPT4All server must be running
- Model availability and compatibility

### 9.2 Internal Interfaces

- **DockerManager**: Interface for Docker operations
  - Container status, logs, start/stop/restart

- **ScanManager**: Tracking scan status and history
  - Create, update, query scan status

- **SystemHealthMonitor**: System health checking
  - Check disk space, Docker connection

- **Security analyzers**: Backend and frontend security analysis
  - Run analysis, get summary, process results

## 10. Operational Context

### 10.1 Deployment Model

- Deployment environments: Not explicitly specified in code
- Deployment process: Not explicitly defined
- Configuration management: Flask app configuration

### 10.2 Monitoring

- Key metrics tracked:
  - CPU, memory, disk usage
  - Container counts and status
  - Scan status and results
  - Performance test metrics

- Alert thresholds: Not explicitly defined

- Logging strategy:
  - Component-specific loggers (`main_route_logger`, `api_logger`, etc.)
  - Hierarchical logging structure
  - Contextual information in log messages
  - Exception tracebacks for errors

### 10.3 Common Issues

**ISSUE: Docker Connection Failure**

SYMPTOMS:
- Dashboard shows Docker unavailable
- Container operations fail with errors
- System info shows client_available: false

CAUSES:
- Docker daemon not running
- Permission issues accessing Docker socket
- Docker configuration problems

RESOLUTION:
1. Verify Docker daemon is running (`systemctl status docker`)
2. Check Docker socket permissions
3. Restart Docker service if needed
4. Check Docker configuration in app

PREVENTION:
- Regular system health checks
- Proper Docker configuration
- Graceful error handling in UI

**ISSUE: ZAP Scan Hanging**

SYMPTOMS:
- Scan status stuck in STARTING or SCANNING
- No progress updates after extended time
- No results file generated

CAUSES:
- ZAP process issues
- Resource exhaustion
- Target application unreachable

RESOLUTION:
1. Use /zap/scan/{model}/{app_num}/stop endpoint
2. Check for zombie ZAP processes
3. Restart application if necessary
4. Check logs for error messages

PREVENTION:
- Implement timeouts in scanner code
- Resource monitoring during scans
- Process cleanup on application restart

## 11. Task-Oriented Guides

### 11.1 Common Development Tasks

**TASK: Add a New API Endpoint**

PREREQUISITES:
- Understanding of Flask Blueprint structure
- Knowledge of application's error handling

STEPS:
1. Identify appropriate Blueprint for the functionality
2. Add new route function with `@blueprint.route` decorator
3. Add `@ajax_compatible` decorator for error handling
4. Implement endpoint logic
5. Return APIResponse or dictionary structure
6. Document the new endpoint

VERIFICATION:
- Test endpoint with direct API call
- Verify JSON response format
- Test error conditions and handling

**TASK: Add a New Model Type**

PREREQUISITES:
- Understanding of AI_MODELS structure
- Knowledge of Docker container naming conventions

STEPS:
1. Add new model definition to AI_MODELS list/class
2. Create directory structure for the new model
3. Update port allocation if needed
4. Test model listing in dashboard
5. Create test application for the new model

VERIFICATION:
- Check model appears in dashboard
- Verify container operations work
- Test scans and analysis features

### 11.2 Debugging Approaches

**SCENARIO: ZAP Scan Fails with ERROR Status**

DIAGNOSTIC STEPS:
1. Check application logs (`zap_logger`) for exceptions
2. Verify app directory exists and has correct permissions
3. Check if ZAP scanner is properly configured
4. Test ZAP scanner in isolation

COMMON CAUSES:
- Invalid app directory path: Verify path is correct and accessible
- ZAP scanner not available: Check ZAP installation
- Resource limitations: Check memory/disk availability

**SCENARIO: Performance Test Shows No Results**

DIAGNOSTIC STEPS:
1. Check performance_bp logs for errors
2. Verify target application is running on specified port
3. Check for Locust process errors
4. Test endpoints directly to confirm availability

COMMON CAUSES:
- Target application not running: Start the app containers
- Invalid endpoints in test configuration: Verify endpoints exist
- Locust configuration issues: Check test parameters

## 12. Project Glossary

| Term | Definition | Context |
|------|------------|---------|
| Model | AI model type (e.g., Llama, Claude) | Used to categorize applications |
| App | Specific deployment instance of a model | Managed via Docker containers |
| ScanState | Enumeration of possible scan statuses | Used in ZAP scanning workflow |
| Blueprint | Flask modular component | Application organization structure |
| ZAP | OWASP Zed Attack Proxy | Security testing tool |
| Locust | Performance testing framework | Used for load testing |
| GPT4All | Local AI model framework | Used for requirements analysis |

## Example Component Documentation

**COMPONENT: ScanManager**

PURPOSE: Manages and tracks security scan state and history

RESPONSIBILITIES:
- Creates new scan entries
- Updates scan status and progress
- Tracks scan history
- Provides query interfaces for scan status
- Cleans up old scan entries

PUBLIC INTERFACE:
- create_scan(model, app_num, initial_state): scan_id
- update_scan(scan_id, **kwargs): None
- get_scan_status(scan_id): ScanStatus
- get_latest_scan_for_app(model, app_num): (scan_id, ScanStatus)
- cleanup_old_scans(): None

INTERNAL COMPONENTS:
- ScanRegistry: In-memory storage of scan status

KEY DATA STRUCTURES:
- ScanState: Enum of possible scan states
- ScanStatus: Dictionary with scan metadata

STATE MACHINE:
```
[NOT_RUN] → [STARTING] → [SPIDERING] → [SCANNING] → [COMPLETE]
       └→ [ERROR]
                    └→ [FAILED]
                    └→ [STOPPED]
```

ERROR HANDLING:
- Scanner initialization failures: Updates status to ERROR
- Scan process failures: Updates status to FAILED
- User-initiated stops: Updates status to STOPPED

PERFORMANCE CHARACTERISTICS:
- In-memory storage: Fast access, lost on restart
- Thread-safe methods for concurrent updates
- Cleanup policy to prevent memory growth

EXAMPLE USAGE:
```python
# Create a new scan
scan_id = scan_manager.create_scan("Llama", 1, {})

# Update scan progress
scan_manager.update_scan(
    scan_id,
    status="SCANNING",
    progress=45,
    spider_progress=100,
    active_progress=30
)

# Get latest scan status
latest_scan = scan_manager.get_latest_scan_for_app("Llama", 1)
if latest_scan:
    scan_id, scan_status = latest_scan
    print(f"Latest scan: {scan_id}, Status: {scan_status['status']}")
```