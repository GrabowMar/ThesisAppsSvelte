# Frontend Generation Prompt - React IoT Controller Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (dashboard, devices, analytics, automation, settings).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**IoT Controller System Frontend**  
A modern React frontend for IoT device management application, featuring real-time device monitoring, control interfaces, data visualization, automation management, and responsive dashboard design.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Real-time device dashboard with status monitoring
- Interactive device control interfaces
- Data visualization with charts and graphs
- Automation rules configuration and management
- Device management and organization tools
- Historical data analysis and reporting
- Real-time updates and notifications
- Mobile-responsive design for remote monitoring

## Frontend Structure (App.jsx)

```jsx
// 1. Imports
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import io from 'socket.io-client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  // - currentView (dashboard, devices, analytics, automation, settings, auth)
  // - devices array with real-time status
  // - selectedDevice for detailed view
  // - sensorData for charts and graphs
  // - automationRules array
  // - user authentication state
  // - notifications and alerts
  // - socket connection state
  // - loading states
  // - error states

  // 4. Refs
  // - socketRef for WebSocket connection
  // - chartRefs for data visualization
  // - deviceControlRef
  // - notificationRef
  
  // 5. Lifecycle Functions
  // - Load devices and data on mount
  // - Setup WebSocket connection
  // - Initialize real-time updates
  // - Check user authentication
  
  // 6. Event Handlers
  // - handleDeviceControl
  // - handleAutomationCreate/Edit/Delete
  // - handleDeviceAdd/Edit/Delete
  // - handleRealTimeUpdates
  // - handleNotifications
  // - handleAuth (login/register/logout)
  // - handleDataVisualization
  
  // 7. Device Control Functions
  // - sendCommand
  // - updateDeviceSettings
  // - toggleDeviceStatus
  // - executeAutomationRule
  // - refreshDeviceData
  
  // 8. API Calls
  // - getDevices
  // - getDevice
  // - sendDeviceCommand
  // - getSensorData
  // - getAutomationRules
  // - createAutomationRule
  // - getAnalytics
  // - authenticate
  
  // 9. Utility Functions
  // - formatSensorValue
  // - calculateUptime
  // - generateChartData
  // - validateRuleConditions
  // - formatTimestamp
  
  // 10. Render Methods
  // - renderDashboard()
  // - renderDeviceGrid()
  // - renderDeviceDetail()
  // - renderAnalytics()
  // - renderAutomationRules()
  // - renderAuthView()
  // - renderDeviceCard()
  
  return (
    <main className="iot-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 11. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Dashboard Overview**
   - Grid of device status cards with real-time updates
   - System health indicators and alerts
   - Quick access controls for common devices
   - Recent activity feed and notifications
   - Key performance metrics and statistics
   - Weather widget and environmental data
   - Favorite devices and quick actions

2. **Device Management View**
   - Device list with status indicators and controls
   - Device detail view with configuration options
   - Add new device wizard with setup steps
   - Device grouping and organization tools
   - Bulk device operations and management
   - Device search and filtering options
   - Device health monitoring and diagnostics

3. **Real-time Control Interface**
   - Interactive device controls (switches, sliders, buttons)
   - Live sensor data displays with gauges and meters
   - Device command interface with feedback
   - Manual override controls for automation
   - Emergency stop and safety controls
   - Device status timeline and history
   - Command queue and execution status

4. **Analytics and Data Visualization**
   - Interactive charts for sensor data trends
   - Historical data analysis with date range selection
   - Device performance metrics and reports
   - Energy usage and efficiency analytics
   - Comparative device analysis and benchmarking
   - Data export and reporting tools
   - Custom dashboard creation and widgets

5. **Automation Management**
   - Automation rules list with status indicators
   - Rule creation wizard with condition builder
   - Visual rule editor with drag-and-drop interface
   - Schedule management for time-based automation
   - Rule testing and simulation tools
   - Automation history and execution logs
   - Conditional logic builder with templates

6. **Device Settings and Configuration**
   - Device-specific configuration panels
   - Network settings and connectivity options
   - Firmware update management interface
   - Security settings and access controls
   - Notification preferences and alerting
   - Device grouping and tagging system
   - Backup and restore configuration

## Real-time Monitoring Features

```javascript
// Real-time IoT functionality:
const RealTimeFeatures = {
  // - Live device status updates via WebSocket
  // - Real-time sensor data streaming and charts
  // - Instant command execution feedback
  // - Automated alert notifications
  // - Live device connectivity monitoring
  // - Real-time automation rule execution
  // - Push notifications for critical events
  // - Live data synchronization across views
};
```

## Device Control Interface

- **Intuitive control widgets** (toggles, sliders, dials)
- **Touch-friendly controls** for mobile devices
- **Voice control integration** (optional)
- **Gesture-based controls** for touch devices
- **Batch control operations** for device groups
- **Scheduled control** with timer interfaces
- **Emergency controls** with confirmation dialogs
- **Control history** and command logging

## Data Visualization Features

- **Real-time charts** with live data updates
- **Historical trend analysis** with zoom and pan
- **Multi-sensor comparisons** on single charts
- **Custom chart configurations** and preferences
- **Interactive legends** and data filtering
- **Chart export** and sharing capabilities
- **Responsive chart layouts** for different screens
- **Performance optimization** for large datasets

## UI/UX Requirements

- Clean, modern IoT dashboard design
- Mobile-first responsive layout
- Real-time visual updates without jarring transitions
- Touch-friendly interface for mobile control
- Visual feedback for all device interactions
- Loading states for device operations
- Error handling with helpful diagnostic information
- Accessibility compliance (ARIA labels, keyboard navigation)
- Dark/Light theme support for different environments
- High contrast mode for industrial environments

## Automation Interface Features

```javascript
// Automation management system:
const AutomationFeatures = {
  // - Visual rule builder with drag-and-drop
  // - Condition testing with real device data
  // - Time-based scheduling with calendar picker
  // - Rule templates for common scenarios
  // - Conditional logic with AND/OR operations
  // - Device state monitoring and triggers
  // - Email/SMS notification integration
  // - Rule execution history and analytics
};
```

## Mobile and Remote Access

- **Progressive Web App** capabilities for offline access
- **Touch-optimized controls** for tablets and phones
- **Responsive grid layouts** that adapt to screen size
- **Swipe gestures** for navigation and control
- **Push notifications** for mobile alerts
- **Offline mode** with data synchronization
- **Quick access widgets** for frequently used controls
- **Mobile-specific shortcuts** and gestures

## Notification and Alert System

- **Real-time alert banners** for critical events
- **Notification center** with alert history
- **Customizable alert thresholds** and conditions
- **Visual and audio alerts** for different severity levels
- **Alert acknowledgment** and resolution tracking
- **Email and SMS integration** for remote alerts
- **Alert filtering** and categorization
- **Snooze and dismiss** functionality

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';
const socket = io('http://localhost:YYYY');

// Authentication API functions:
// - login(credentials)
// - register(userData)
// - logout()
// - getCurrentUser()

// Device API functions:
// - getDevices()
// - getDevice(id)
// - addDevice(deviceData)
// - updateDevice(id, deviceData)
// - deleteDevice(id)
// - sendCommand(deviceId, command)

// Data API functions:
// - getSensorData(deviceId, dateRange)
// - getAnalytics(timeRange, deviceIds)
// - getDeviceHistory(deviceId)

// Automation API functions:
// - getAutomationRules()
// - createRule(ruleData)
// - updateRule(id, ruleData)
// - deleteRule(id)
// - testRule(ruleData)

// WebSocket event handlers:
// - device_status_update
// - sensor_data_update
// - command_response
// - automation_triggered
// - system_alert
```

## Configuration Files

### vite.config.js
```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: XXXX,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:YYYY',
        changeOrigin: true,
        secure: false,
      },
      '/socket.io': {
        target: 'http://localhost:YYYY',
        changeOrigin: true,
        ws: true,
      }
    }
  }
});
```

### index.html
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>IoT Controller</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/App.jsx"></script>
  </body>
</html>
```

## Response Requirements

1. **Port Configuration**
   - Use `XXXX` for frontend port in vite.config.js
   - Proxy API calls and WebSocket to backend on port `YYYY`

2. **Dependencies**
   - Generate complete package.json with all necessary npm dependencies
   - Include React, Vite, Socket.IO client, charting libraries, and any additional libraries needed

3. **Production Ready Features**
   - Comprehensive error handling and recovery
   - Real-time updates with connection management
   - Responsive design with mobile optimization
   - Proper state management for IoT device data
   - Performance optimization (efficient chart rendering, data caching)
   - Accessibility compliance
   - Clean code with comments
   - User experience enhancements (smooth animations, intuitive controls)
   - Progressive Web App features
   - Offline functionality with sync capabilities

**Very important:** Your frontend should be feature rich, production ready, and provide excellent IoT management experience with intuitive device control, comprehensive monitoring, real-time data visualization, and responsive design that works across all devices and environments.