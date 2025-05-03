# AI Model Management System Knowledge Base

## 1. Project Identity Card
PROJECT NAME: AI Model Management System  
PRIMARY PURPOSE: Manages deployment and operation of various AI models through Docker containers  
DOMAIN: DevOps, AI Infrastructure, Container Management  
DEVELOPMENT STAGE: Active Development  
REPOSITORY URL: [Not specified in provided code]  
DOCUMENTATION URL: [Not specified in provided code]  

## 2. Project Context

### 2.1 Problem Statement

The project addresses the challenge of managing multiple AI model deployments across different environments. Each AI model (like Llama, Mistral, DeepSeek, etc.) needs its own backend and frontend instances, with proper health monitoring, security analysis, and operational management.

Managing different AI models with varying dependencies and configurations creates significant complexity for organizations working with multiple models. Without a standardized system, teams waste time with ad-hoc deployment methods and face inconsistent monitoring and management.

### 2.2 Solution Overview

The solution is a Flask-based web application that provides a standardized way to manage AI models in Docker containers. It handles container lifecycle operations (start, stop, restart, build), performs health monitoring, runs security analysis, and offers a unified management interface for all supported models.

The system uses Docker as the core containerization technology, allowing each model to be isolated with its own dependencies while maintaining a consistent management interface. The application dynamically assigns ports to different model instances to prevent conflicts.

### 2.3 User Personas

**AI Infrastructure Engineers**: Technical users who manage the deployment and operation of AI models across development and production environments.

**ML Engineers/Data Scientists**: Users who need to deploy models for testing or production use without managing low-level Docker operations directly.

**Security Auditors**: Users who need to verify that model deployments follow security best practices and don't contain vulnerabilities.

## 3. Architecture Map

### 3.1 System Diagram
```
[User Web Browser] → [Flask Web Application]
                           ↓
[DockerManager] ↔ [Docker Engine] → [Model Containers]
      ↓               ↑
[PortManager]   [SecurityAnalyzers]
```

Legend:
→ : Data flow
⟲ : Processing loop
□ : External system
■ : Internal component

### 3.2 Component Inventory

| Component Name | Type | Purpose | Interfaces | Dependencies |
|----------------|------|---------|------------|--------------|
| Flask App | Service | Web UI and API for model management | HTTP | - |
| AppConfig | Class | Application configuration with environment overrides | Config properties | os, pathlib |
| DockerManager | Service | Interfaces with Docker to manage containers | Container management methods | docker |
| PortManager | Service | Manages port allocation for model instances | Port allocation methods | - |
| SecurityAnalyzers | Service | Performs security scans on deployments | Analysis methods | - |
| ScanManager | Service | Manages security scans | Scanning methods | - |

### 3.3 Data Flow Sequences

Operation: Start Container
1. User requests to start a model container via web interface
2. Flask route handler calls `handle_docker_action("start", model, app_num)`
3. Function invokes `run_docker_compose` with "up -d" command
4. Subprocess runs the Docker Compose command in the appropriate directory
5. Function checks container health with `verify_container_health`
6. Returns success/failure status and message to user

Operation: Health Check
1. User requests container health status
2. Flask route handler retrieves container names using `get_container_names`
3. Calls `docker_manager.get_container_status` for backend and frontend containers
4. System checks container existence, running state, and health status
5. Returns container status information to the UI

Operation: Security Analysis
1. User requests security analysis of a deployment
2. System invokes `process_security_analysis` with appropriate analyzer
3. Analyzer scans the application code and configuration
4. System collects issues, tool statuses, and detailed outputs
5. Returns analysis results to the UI for display

## 4. Core Data Structures

DATA STRUCTURE: AppConfig

PURPOSE: Application configuration with environment variable fallbacks

SCHEMA:
- DEBUG: bool [True for development environment]
  Purpose: Controls debug mode for Flask
  Default: Based on FLASK_ENV environment variable
  
- SECRET_KEY: str
  Purpose: Used for session encryption and security
  Default: "your-secret-key-here" (from env var FLASK_SECRET_KEY)
  
- BASE_DIR: Path
  Purpose: Base directory for the application
  Default: Parent directory of utils.py
  
- DOCKER_TIMEOUT: int
  Purpose: Timeout for Docker operations
  Default: 10 seconds (from env var DOCKER_TIMEOUT)
  
- CACHE_DURATION: int
  Purpose: Duration to cache data
  Default: 5 minutes (from env var CACHE_DURATION)
  
- HOST: str
  Purpose: Host to bind the Flask server
  Default: "0.0.0.0" for production, "127.0.0.1" for development
  
- PORT: int
  Purpose: Port to bind the Flask server
  Default: 5000 (from env var PORT)
  
- LOG_DIR: str
  Purpose: Directory for log files
  Default: "logs" (from env var LOG_DIR)
  
- LOG_LEVEL: str
  Purpose: Logging verbosity level
  Default: "INFO" for production, "DEBUG" for development

LIFECYCLE:
- Creation: On application initialization
- Mutation: Not mutated after creation
- Termination: Persists for application lifetime

DATA STRUCTURE: AIModel

PURPOSE: Represents an AI model with display properties

SCHEMA:
- name: str
  Purpose: Name of the AI model
  
- color: str
  Purpose: Hex color code for UI display
  
METHODS:
- to_dict(): Converts model to dictionary for JSON serialization

EXAMPLES:
```python
AIModel("Llama", "#f97316")
```

DATA STRUCTURE: DockerStatus

PURPOSE: Represents the status of a Docker container

SCHEMA:
- exists: bool
  Purpose: Whether the container exists
  Default: False
  
- running: bool
  Purpose: Whether the container is running
  Default: False
  
- health: str
  Purpose: Health status of the container
  Default: "unknown"
  
- status: str
  Purpose: Status string from Docker
  Default: "unknown"
  
- details: str
  Purpose: Additional status details
  Default: ""
  
METHODS:
- to_dict(): Converts status to dictionary for JSON serialization

DATA STRUCTURE: APIResponse

PURPOSE: Standard API response format for consistency

SCHEMA:
- success: bool
  Purpose: Indicates if the operation was successful
  Default: True
  
- message: Optional[str]
  Purpose: Human-readable message about the operation
  Default: None
  
- data: Any
  Purpose: Response payload
  Default: None
  
- error: Optional[str]
  Purpose: Error message if operation failed
  Default: None
  
- code: int
  Purpose: HTTP status code
  Default: 200 (OK)
  
METHODS:
- to_response(): Converts to Flask JSON response with appropriate status code

## 5. Function Reference

FUNCTION: ajax_compatible

PURPOSE: Decorator to standardize endpoint responses for AJAX and non-AJAX calls

SIGNATURE:
```python
Callable ajax_compatible(f: Callable) -> Callable
```

PARAMETERS:
- f: Function to decorate

RETURNS:
- Wrapped function that handles different response types

BEHAVIOR:
1. Creates a specific logger for the function
2. Detects if the request is AJAX based on 'X-Requested-With' header
3. Executes the wrapped function and captures the result
4. If result is already a Flask Response tuple, returns it unchanged
5. If result is an APIResponse object, converts it to a response
6. For AJAX requests, wraps other results in a standard JSON structure
7. For non-AJAX requests, returns the result directly
8. Handles exceptions differently for AJAX vs non-AJAX requests
   - AJAX: Returns error as JSON with appropriate status code
   - non-AJAX: Renders 500.html template with error details

EXAMPLES:
```python
@ajax_compatible
def my_endpoint():
    return {"data": "some value"}  # Will be JSON for AJAX, direct for non-AJAX
```

FUNCTION: get_model_index

PURPOSE: Get the index of a model in the AI_MODELS list

SIGNATURE:
```python
Optional[int] get_model_index(model_name: str)
```

PARAMETERS:
- model_name: Name of the model (case-sensitive)

RETURNS:
- Index in the AI_MODELS list or None if not found

BEHAVIOR:
1. Uses Python's `next` with a generator expression to find the first matching model
2. Returns the index if found
3. Returns None if model name is not in the list

EXAMPLES:
```python
idx = get_model_index("Llama")  # Returns 0 if Llama is the first model
```

FUNCTION: get_container_names

PURPOSE: Get the container names for a given model and app number

SIGNATURE:
```python
Tuple[str, str] get_container_names(model: str, app_num: int)
```

PARAMETERS:
- model: Model name
- app_num: Application number (1-based)

RETURNS:
- Tuple of (backend_container_name, frontend_container_name)

BEHAVIOR:
1. Gets the model index using get_model_index
2. Raises ValueError if model is not found
3. Gets ports for the app using PortManager
4. Constructs container names based on model name and port numbers
5. Returns the container name tuple

EXAMPLES:
```python
backend_name, frontend_name = get_container_names("Llama", 1)
# Might return ("llama_backend_8000", "llama_frontend_3000")
```

FUNCTION: get_app_info

PURPOSE: Get detailed information for a specific app instance

SIGNATURE:
```python
Optional[Dict[str, Any]] get_app_info(model_name: str, app_num: int)
```

PARAMETERS:
- model_name: Name of the AI model
- app_num: Application number (1-based)

RETURNS:
- Dictionary with app details, or None if model/app is invalid

BEHAVIOR:
1. Gets the model index using get_model_index
2. Returns None if model is not found
3. Gets the AIModel object for the specified model
4. Gets port numbers using PortManager
5. Constructs a dictionary with app details including:
   - name, model, color, ports, app number, and URLs
6. Handles exceptions and returns None if any occur

EXAMPLES:
```python
app_info = get_app_info("Llama", 1)
# Returns dict with app details if valid, None otherwise
```

FUNCTION: run_docker_compose

PURPOSE: Run a docker-compose command for a specific app

SIGNATURE:
```python
Tuple[bool, str] run_docker_compose(command: List[str], model: str, app_num: int, timeout: int = 60, check: bool = True)
```

PARAMETERS:
- command: The docker-compose command arguments (e.g., ["up", "-d"])
- model: The model name
- app_num: The application number (1-based)
- timeout: Command timeout in seconds (default: 60)
- check: Whether to raise CalledProcessError on non-zero exit code (default: True)

RETURNS:
- Tuple of (success_flag, command_output)

BEHAVIOR:
1. Gets the app directory for the specified model and app number
2. Checks if docker-compose.yml or docker-compose.yaml exists
3. Builds a project name from model and app number
4. Constructs the full docker-compose command
5. Runs the command using subprocess.run
6. Captures stdout and stderr, combines them
7. Returns success status and output
8. Handles various error conditions:
   - FileNotFoundError: Docker Compose not installed
   - TimeoutExpired: Command execution took too long
   - CalledProcessError: Command returned non-zero exit code
   - Other exceptions: Permissions, etc.

EXAMPLES:
```python
success, output = run_docker_compose(["up", "-d"], "Llama", 1, timeout=90)
```

FUNCTION: handle_docker_action

PURPOSE: Handle Docker Compose actions (start, stop, restart, build, rebuild)

SIGNATURE:
```python
Tuple[bool, str] handle_docker_action(action: str, model: str, app_num: int)
```

PARAMETERS:
- action: The action ('start', 'stop', 'restart', 'build', 'rebuild')
- model: The model name
- app_num: The application number (1-based)

RETURNS:
- Tuple of (success, message)

BEHAVIOR:
1. Defines command sequences with arguments and timeouts for each action
2. Validates the requested action is supported
3. Executes each command step defined for the action
4. Collects output from each step
5. Returns early if any step fails
6. Returns combined output of all steps on success

EXAMPLES:
```python
success, message = handle_docker_action("start", "Llama", 1)
```

FUNCTION: verify_container_health

PURPOSE: Check if Docker containers are running and healthy

SIGNATURE:
```python
Tuple[bool, str] verify_container_health(docker_manager: DockerManager, model: str, app_num: int, max_retries: int = 15, retry_delay: int = 5)
```

PARAMETERS:
- docker_manager: DockerManager instance
- model: Model name
- app_num: App number (1-based)
- max_retries: Maximum number of health checks to attempt
- retry_delay: Delay between checks in seconds

RETURNS:
- Tuple of (is_healthy, message)

BEHAVIOR:
1. Gets container names for backend and frontend
2. Iteratively checks container health status up to max_retries
3. For each attempt:
   - Gets container status using docker_manager
   - Checks if both containers are running and healthy
   - Returns success if both are healthy
   - Waits retry_delay seconds before next attempt
4. If max_retries is reached without success, returns failure with status info

EXAMPLES:
```python
is_healthy, message = verify_container_health(docker_manager, "Llama", 1)
```

## 6. API Reference

While specific endpoints aren't explicitly defined in the provided code, the utilities support an API with these general patterns:

ENDPOINT: GET /api/models

PURPOSE: Retrieve all configured AI models

RESPONSE:
- Success (200): Array of model objects
```json
{
  "success": true,
  "data": [
    {"name": "Llama", "color": "#f97316"},
    {"name": "Mistral", "color": "#9333ea"},
    ...
  ]
}
```

ENDPOINT: GET /api/apps

PURPOSE: Retrieve all available app instances

RESPONSE:
- Success (200): Array of app information objects
```json
{
  "success": true,
  "data": [
    {
      "name": "Llama App 1",
      "model": "Llama",
      "color": "#f97316",
      "backend_port": 8000,
      "frontend_port": 3000,
      "app_num": 1,
      "backend_url": "http://127.0.0.1:8000",
      "frontend_url": "http://127.0.0.1:3000"
    },
    ...
  ]
}
```

ENDPOINT: POST /api/docker/{action}/{model}/{app_num}

PURPOSE: Perform Docker actions on app instances

PARAMETERS:
- action: "start", "stop", "restart", "build", or "rebuild"
- model: Model name
- app_num: App number

RESPONSE:
- Success (200): 
```json
{
  "success": true,
  "message": "Action 'start' completed successfully.",
  "data": "Full command output..."
}
```
- Error (4xx/5xx):
```json
{
  "success": false,
  "error": "Error details",
  "message": "An error occurred processing your request."
}
```

## 7. Implementation Context

### 7.1 Technology Stack

| Layer | Technology | Purpose | Version | Notes |
|-------|------------|---------|---------|-------|
| Web Framework | Flask | Serves web UI and API | Not specified | Uses standard Flask patterns |
| Container | Docker | Runs AI model instances | Not specified | Uses docker-compose for orchestration |
| Language | Python | Implementation language | 3.x | Uses modern Python features |
| Configuration | Environment Variables | Runtime configuration | N/A | Fallbacks to sensible defaults |
| Logging | Python logging | Application logs | Standard library | Component-specific loggers |

### 7.2 Dependencies

| Dependency | Purpose | API Surface Used |
|------------|---------|-----------------|
| http | HTTP status codes | Constants for response codes |
| json | JSON serialization | dumps, loads |
| os | Environment access | getenv |
| subprocess | Run Docker commands | run |
| time | Delays and timing | sleep |
| pathlib | Path manipulation | Path |
| dataclasses | Data structures | dataclass, asdict, field |
| datetime | Date/time handling | datetime |
| functools | Decorators | wraps |
| typing | Type annotations | Various types |
| flask | Web framework | Response, jsonify, etc. |
| werkzeug | HTTP utilities | HTTPException |
| DockerManager | Docker interface | get_container_status |
| PortManager | Port allocation | get_app_ports |
| logging_service | Logging | create_logger_for_component |

### 7.3 Environment Requirements

- Python 3.x runtime
- Docker and Docker Compose installed and in PATH
- Flask application environment
- Sufficient permissions to manage Docker containers
- Environment variables (optional, with defaults):
  - FLASK_ENV: "development" or "production"
  - FLASK_SECRET_KEY: Secret key for Flask
  - DOCKER_TIMEOUT: Timeout for Docker operations
  - CACHE_DURATION: Duration to cache data
  - PORT: HTTP port for Flask
  - LOG_DIR: Directory for logs
  - LOG_LEVEL: Logging verbosity
  - CORS_ENABLED: Whether to enable CORS
  - CORS_ORIGINS: Allowed origins for CORS
  - AJAX_TIMEOUT: Timeout for AJAX requests

## 8. Reasoning Patterns

### 8.1 Key Algorithms

ALGORITHM: AJAX Response Handling

PURPOSE: Standardize handling of both AJAX and non-AJAX requests

INPUT: 
- Function result (various types)
- Request context

OUTPUT: 
- Appropriate response for request type

STEPS:
1. Detect if request is AJAX based on X-Requested-With header
2. Process function result based on its type:
   - If already a Response, return as-is
   - If APIResponse, convert to standard format
   - If normal object, standardize format based on request type
3. For AJAX requests:
   - Convert all results to JSON with success flag
   - Use standardized error format for exceptions
4. For non-AJAX requests:
   - Return results directly (templates, etc.)
   - Render error templates for exceptions

COMPLEXITY:
- Time: O(1) - Simple transformation
- Space: O(1) - No significant extra memory needed

ALGORITHM: Container Health Verification

PURPOSE: Ensure Docker containers are running and healthy

INPUT:
- DockerManager instance
- Model name and app number
- Retry parameters

OUTPUT:
- Health status (boolean) and status message

STEPS:
1. Get container names for backend and frontend
2. Iterate up to max_retries times:
   a. Get current status of both containers
   b. Check if both are running AND have "healthy" health status
   c. If both are healthy, return success
   d. Otherwise wait retry_delay seconds
3. If max_retries reached without success, return failure with status details

COMPLEXITY:
- Time: O(max_retries) - Linear with maximum retry count
- Space: O(1) - Constant space for status tracking

### 8.2 Design Decisions

DECISION: Standardized API Response Format

CONTEXT: The application needs to provide consistent API responses for various endpoints

OPTIONS CONSIDERED:
1. Ad-hoc responses - Each endpoint returns custom format
   - Pros: Flexibility for specific endpoints
   - Cons: Inconsistent client experience, more complex client code
   
2. Standardized APIResponse class
   - Pros: Consistent format, centralized response handling
   - Cons: Slightly more overhead for simple responses

DECISION OUTCOME: Implemented APIResponse class with standard fields

CONSEQUENCES:
- All API responses follow consistent format
- Clients can rely on standard success/error handling
- Code reuse through centralized to_response method

DECISION: Docker Command Sequencing

CONTEXT: Need to manage Docker operations reliably with appropriate timeouts

OPTIONS CONSIDERED:
1. Direct Docker API integration
   - Pros: More programmatic control, no subprocess dependency
   - Cons: Complex API, version compatibility issues
   
2. Subprocess with docker-compose commands
   - Pros: Leverages existing docker-compose.yml files, familiar to users
   - Cons: Command-line dependency, potential subprocess issues

DECISION OUTCOME: Used subprocess with docker-compose for operations

CONSEQUENCES:
- Relies on docker-compose being available in PATH
- Defined command sequences with appropriate timeouts for complex operations
- Captured and processed command output for user feedback

## 9. Integration Points

### 9.1 External Systems

SYSTEM: Docker Engine

PURPOSE: Container management for AI model instances

INTERFACE:
- Protocol: Command-line via subprocess
- Authentication: System-level Docker permissions
- Operations:
  - Container creation/start: docker-compose up
  - Container stop: docker-compose down
  - Container rebuild: docker-compose build
  - Container status: docker ps

FAILURE MODES:
- Docker daemon not running: Commands fail with connection errors
- Permission issues: Commands fail with permission errors
- Resource constraints: Containers may fail to start or become unhealthy

CONSTRAINTS:
- Command timeouts (configurable)
- Docker API version compatibility
- System resource limits

### 9.2 Internal Interfaces

Component: DockerManager
Interface:
- get_container_status(container_name): Returns DockerStatus object

Component: PortManager
Interface:
- get_app_ports(model_index, app_num): Returns port mappings

Component: AppConfig
Interface:
- Configuration properties with environment variable fallbacks

Component: APIResponse
Interface:
- to_response(): Converts to Flask response tuple

## 10. Operational Context

### 10.1 Deployment Model

The application manages Docker deployments with these characteristics:

- Each AI model has multiple app instances (app1, app2, etc.)
- Each app instance consists of a backend and frontend container
- Containers are defined via docker-compose.yml in the app directory
- App instances are identified by model name and app number
- Ports are dynamically assigned to prevent conflicts
- Container names follow the pattern: {model}_backend_{port} and {model}_frontend_{port}

### 10.2 Monitoring

The system includes these monitoring features:

- Component-specific logging with configurable log levels
- Container health monitoring with retry logic
- Docker command execution tracking
- Security analysis reporting
- Error handling with detailed logs

Logs include:
- Docker operation status and outputs
- Container health status
- Security analysis results
- API errors and exceptions

### 10.3 Common Issues

ISSUE: Containers failing health checks

SYMPTOMS:
- verify_container_health returns failure
- Frontend UI shows containers as unhealthy
- Application functionality unavailable

CAUSES:
- Container startup time exceeds health check timeout
- Application errors inside containers
- Resource constraints (memory, CPU)
- Network port conflicts

RESOLUTION:
1. Check container logs for specific errors
2. Increase max_retries or retry_delay for health checks
3. Restart containers with `handle_docker_action("restart", model, app_num)`
4. Rebuild containers if configuration issues are suspected

PREVENTION:
- Ensure sufficient system resources
- Implement more robust health check mechanisms
- Monitor container resource usage

ISSUE: Docker command failures

SYMPTOMS:
- run_docker_compose returns failure status
- Error messages in logs or UI

CAUSES:
- Docker daemon not running
- Permission issues
- Missing docker-compose.yml file
- Command timeout too short
- Docker resource constraints

RESOLUTION:
1. Verify Docker daemon is running
2. Check permissions for Docker socket
3. Confirm docker-compose.yml exists in correct location
4. Increase command timeout
5. Check system resources

PREVENTION:
- Regular validation of Docker configuration
- Proper error handling for Docker operations
- Monitoring of Docker daemon status

## 11. Task-Oriented Guides

### 11.1 Common Development Tasks

TASK: Add a new AI model

PREREQUISITES:
- Understanding of AI_MODELS structure
- UI color selection for the model

STEPS:
1. Edit the AI_MODELS list in utils.py
2. Add a new AIModel entry with name and color:
   ```python
   AIModel("NewModel", "#123456")
   ```
3. Create the directory structure for the model:
   - Create base directory for the model
   - Create app subdirectories (app1, app2, etc.)
   - Add docker-compose.yml in each app directory
4. Test model listing with get_all_apps()
5. Verify UI shows the new model correctly

VERIFICATION:
- Model appears in UI model list
- Container operations work with the new model
- Port assignment works correctly

### 11.2 Debugging Approaches

SCENARIO: Docker container fails to start

DIAGNOSTIC STEPS:
1. Check the app information:
   ```python
   app_info = get_app_info(model_name, app_num)
   print(app_info)
   ```
2. Check docker-compose file existence:
   ```python
   app_dir = get_app_directory(current_app, model_name, app_num)
   compose_file = app_dir / "docker-compose.yml"
   print(f"Compose file exists: {compose_file.exists()}")
   ```
3. Run docker-compose with verbose output:
   ```python
   success, output = run_docker_compose(["up", "-d", "--verbose"], model_name, app_num)
   print(output)
   ```
4. Check container status:
   ```python
   container_status = get_app_container_statuses(model_name, app_num, docker_manager)
   print(container_status)
   ```

COMMON CAUSES:
- Missing or invalid docker-compose.yml: Fix file path or content
- Port conflicts: Check if ports are already in use
- Docker daemon issues: Restart Docker service
- Resource constraints: Increase available resources
- Container startup errors: Check container logs

## 12. Project Glossary

| Term | Definition | Context |
|------|------------|---------|
| AppConfig | Application configuration with environment variable fallbacks | Configuration management |
| AIModel | Representation of an AI model with name and display color | Model management |
| DockerStatus | Container status information including existence, running state, and health | Container monitoring |
| APIResponse | Standardized API response format with success flag, data, and error information | API communication |
| ajax_compatible | Decorator to standardize handling of AJAX and non-AJAX requests | Request processing |
| Container | Docker container running an AI model's backend or frontend | Deployment |
| App Instance | Combination of backend and frontend containers for a specific model | Deployment structure |
| Health Check | Process of verifying container operational status | Monitoring |
| Security Analysis | Process of scanning app code and configuration for security issues | Security |

## Example Component Documentation

COMPONENT: DockerManager

PURPOSE: Interfaces with Docker to manage containers and retrieve their status

RESPONSIBILITIES:
- Get container status information
- Check if containers exist
- Check if containers are running
- Get container health state
- Retrieve detailed container information

PUBLIC INTERFACE:
- get_container_status(container_name): Returns DockerStatus object

INTERNAL COMPONENTS:
- Docker API client
- Container status parser
- Health check interpreter

KEY DATA STRUCTURES:
- DockerStatus: Record of container state

STATE TRANSITIONS:
[NOT_FOUND] → [CREATED] → [RUNNING] → [HEALTHY/UNHEALTHY]
                        ↘ [EXITED]
                        ↘ [RESTARTING]

ERROR HANDLING:
- Connection failures: Returns DockerStatus with exists=False
- Permission issues: Logs error and returns exists=False
- Container not found: Returns DockerStatus with exists=False

PERFORMANCE CHARACTERISTICS:
- Expected latency: ~100ms per container status check
- Caching strategy: Results may be cached based on CACHE_DURATION setting

EXAMPLE USAGE:
```python
docker_manager = DockerManager()
status = docker_manager.get_container_status("llama_backend_8000")
if status.exists and status.running and status.health == "healthy":
    print("Container is healthy")
else:
    print(f"Container issue: {status.status} ({status.details})")
```