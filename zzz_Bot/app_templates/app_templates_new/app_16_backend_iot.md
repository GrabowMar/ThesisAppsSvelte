# Backend Generation Prompt - Flask IoT Controller Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/devices`, `/api/commands`, `/api/data`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**IoT Controller System Backend**  
A comprehensive Flask backend for IoT device management application, featuring device registration, real-time monitoring, command execution, data processing, automation rules, and secure device communication.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Complete device management and registration system
- Real-time device status monitoring and updates
- Command queuing and execution for device control
- Sensor data collection, processing, and storage
- Simple automation rules and scheduling engine
- Device authentication and security management
- Historical data analytics and reporting
- Real-time communication with WebSocket support
- Device grouping and organization
- CORS support for frontend communication
- Database integration (SQLite or in-memory for simplicity)

## Backend Structure (app.py)

```python
# 1. Imports Section
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import sqlite3
from datetime import datetime, timedelta
import uuid
import json
import threading
import time
from queue import Queue

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# 3. Database Models/Setup
# 4. Device Communication Logic
# 5. Command Processing
# 6. Data Analytics
# 7. Automation Engine
# 8. API Routes:
#    - GET /api/devices (list devices)
#    - GET /api/devices/<id> (get device details)
#    - POST /api/devices (register new device)
#    - PUT /api/devices/<id> (update device)
#    - DELETE /api/devices/<id> (remove device)
#    - POST /api/devices/<id>/commands (send command)
#    - GET /api/devices/<id>/status (get current status)
#    - GET /api/devices/<id>/data (get sensor data)
#    - POST /api/devices/<id>/data (receive sensor data)
#    - GET /api/commands (get command history)
#    - GET /api/analytics (get data analytics)
#    - GET /api/automation/rules (get automation rules)
#    - POST /api/automation/rules (create automation rule)
#    - PUT /api/automation/rules/<id> (update rule)
#    - DELETE /api/automation/rules/<id> (delete rule)
#    - GET /api/groups (get device groups)
#    - POST /api/groups (create device group)
#    - POST /api/auth/register (user registration)
#    - POST /api/auth/login (user login)
#    - POST /api/auth/logout (user logout)
#    - GET /api/auth/user (get current user)
# 9. WebSocket Events
# 10. Error Handlers

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 'YYYY')))
```

## Required API Endpoints

### Authentication Routes

1. **POST /api/auth/register**
   - Accept: username, email, password
   - Validate input and create user account
   - Generate API keys for device access
   - Return user info and session

2. **POST /api/auth/login**
   - Accept: username/email, password
   - Validate credentials
   - Create user session
   - Return user info and device permissions

3. **POST /api/auth/logout**
   - Clear user session
   - Invalidate active device sessions
   - Return success response

4. **GET /api/auth/user**
   - Return current authenticated user info
   - Include device quotas and permissions

### Device Management Routes

5. **GET /api/devices**
   - Return list of registered devices
   - Include device status, type, and last seen
   - Support filtering by status, type, group

6. **GET /api/devices/<id>**
   - Return specific device details
   - Include current status, configuration, and recent data
   - Show command history and performance metrics

7. **POST /api/devices**
   - Register new IoT device
   - Accept: name, type, description, ip_address, auth_token
   - Generate unique device ID
   - Initialize device configuration
   - Return device credentials

8. **PUT /api/devices/<id>**
   - Update device configuration
   - Accept: name, description, settings, group_id
   - Validate device ownership
   - Push configuration updates to device

9. **DELETE /api/devices/<id>**
   - Remove device from system
   - Clean up associated data and commands
   - Revoke device authentication
   - Return confirmation

### Device Communication Routes

10. **POST /api/devices/<id>/commands**
    - Send command to device
    - Accept: command_type, parameters, priority
    - Queue command for execution
    - Return command ID and status

11. **GET /api/devices/<id>/status**
    - Get current device status
    - Include connectivity, health, and operational state
    - Real-time status updates

12. **GET /api/devices/<id>/data**
    - Retrieve sensor data for device
    - Accept: start_date, end_date, sensor_type
    - Support data aggregation and filtering
    - Return historical measurements

13. **POST /api/devices/<id>/data**
    - Receive sensor data from device
    - Accept: sensor_readings, timestamp, device_status
    - Validate and store incoming data
    - Trigger automation rules if applicable

### Command and Control Routes

14. **GET /api/commands**
    - Return command history and queue
    - Include command status and execution results
    - Support filtering by device, status, date

15. **GET /api/analytics**
    - Return device and sensor analytics
    - Include usage statistics, performance metrics
    - Historical trends and patterns
    - Data aggregation and insights

### Automation Routes

16. **GET /api/automation/rules**
    - Return list of automation rules
    - Include rule status and trigger history
    - Support filtering by device and rule type

17. **POST /api/automation/rules**
    - Create new automation rule
    - Accept: name, trigger_conditions, actions, schedule
    - Validate rule logic and conflicts
    - Return created rule

18. **PUT /api/automation/rules/<id>**
    - Update automation rule
    - Accept: trigger_conditions, actions, enabled_status
    - Re-evaluate rule dependencies
    - Return updated rule

19. **DELETE /api/automation/rules/<id>**
    - Delete automation rule
    - Clean up scheduled tasks
    - Return confirmation

### Device Organization Routes

20. **GET /api/groups**
    - Return device groups and organization
    - Include group statistics and device counts
    - Support hierarchical grouping

21. **POST /api/groups**
    - Create device group
    - Accept: name, description, parent_group
    - Return created group

## Database Schema

```sql
Users table:
- id (TEXT PRIMARY KEY)
- username (TEXT UNIQUE NOT NULL)
- email (TEXT UNIQUE NOT NULL)
- password_hash (TEXT NOT NULL)
- api_key (TEXT UNIQUE)
- created_at (TIMESTAMP)
- device_quota (INTEGER DEFAULT 50)

Devices table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- name (TEXT NOT NULL)
- device_type (TEXT)
- description (TEXT)
- ip_address (TEXT)
- mac_address (TEXT)
- auth_token (TEXT UNIQUE)
- status (TEXT DEFAULT 'offline')
- last_seen (TIMESTAMP)
- firmware_version (TEXT)
- group_id (TEXT)
- configuration (TEXT) -- JSON
- created_at (TIMESTAMP)

Sensor_Data table:
- id (TEXT PRIMARY KEY)
- device_id (TEXT)
- sensor_type (TEXT)
- value (DECIMAL)
- unit (TEXT)
- timestamp (TIMESTAMP)
- quality_score (INTEGER)

Commands table:
- id (TEXT PRIMARY KEY)
- device_id (TEXT)
- user_id (TEXT)
- command_type (TEXT)
- parameters (TEXT) -- JSON
- status (TEXT) -- 'pending', 'sent', 'executed', 'failed'
- created_at (TIMESTAMP)
- executed_at (TIMESTAMP)
- response (TEXT)

Automation_Rules table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- name (TEXT NOT NULL)
- description (TEXT)
- trigger_conditions (TEXT) -- JSON
- actions (TEXT) -- JSON
- is_enabled (BOOLEAN DEFAULT TRUE)
- last_triggered (TIMESTAMP)
- created_at (TIMESTAMP)

Device_Groups table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- name (TEXT NOT NULL)
- description (TEXT)
- parent_id (TEXT)
- device_count (INTEGER DEFAULT 0)
- created_at (TIMESTAMP)

Device_Logs table:
- id (TEXT PRIMARY KEY)
- device_id (TEXT)
- event_type (TEXT)
- message (TEXT)
- severity (TEXT)
- timestamp (TIMESTAMP)
```

## IoT Communication Features

- **Real-time device communication** with WebSocket support
- **Command queuing** and execution tracking
- **Device authentication** with secure tokens
- **Heartbeat monitoring** for device connectivity
- **Firmware update** management
- **Device discovery** and auto-registration
- **Protocol abstraction** for different device types
- **Message encryption** for secure communication

## Data Processing Features

- **Real-time sensor data** ingestion and validation
- **Data aggregation** and time-series storage
- **Anomaly detection** for sensor readings
- **Data quality assessment** and filtering
- **Historical data** retention and archiving
- **Data export** capabilities
- **Statistical analysis** and trend detection
- **Alert generation** for threshold violations

## Automation Engine Features

- **Rule-based automation** with flexible conditions
- **Scheduled tasks** and time-based triggers
- **Device state monitoring** and event triggers
- **Conditional logic** with AND/OR operations
- **Action chaining** and workflow automation
- **Rule conflict detection** and resolution
- **Automation history** and execution logs
- **Remote rule management** and updates

## Device Management Features

- **Device registration** with validation
- **Device grouping** and organization
- **Configuration management** and deployment
- **Device health monitoring** and diagnostics
- **Bulk device operations** and management
- **Device templates** for common configurations
- **Access control** and permission management
- **Device lifecycle** management

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in socketio.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-SocketIO, Flask-CORS, data processing libraries

3. **Production Ready Features**
   - Comprehensive error handling
   - Device authentication and security
   - Real-time communication management
   - Data validation and integrity
   - Automation rule processing
   - Performance optimization for IoT scale
   - Device monitoring and diagnostics
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all IoT scenarios including device management, real-time monitoring, command execution, data processing, and automation with proper validation and security measures.