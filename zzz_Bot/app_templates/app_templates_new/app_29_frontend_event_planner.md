# Frontend Generation Prompt - React Event Planning Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (events, planning, guests, budget, vendors, timeline, team).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**Event Planning System Frontend**  
A modern React frontend for event planning application, featuring comprehensive event management, interactive planning tools, guest coordination, budget tracking, and collaborative features with intuitive, responsive design.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Comprehensive event creation and management interface
- Interactive guest list management with RSVP tracking
- Visual budget planning and expense tracking
- Vendor coordination dashboard
- Timeline planning with milestone management
- Collaborative planning tools with team management
- Real-time notifications and updates
- Mobile-responsive planning interface
- Drag-and-drop task organization
- Automated workflow assistance

## Frontend Structure (App.jsx)

```jsx
// 1. Imports
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  // - currentView (events, planning, guests, budget, vendors, timeline, team, auth)
  // - events array with filtering
  // - currentEvent for detailed planning
  // - guests array with RSVP status
  // - budget items and calculations
  // - vendors and their status
  // - timeline items and milestones
  // - team members and roles
  // - user authentication state
  // - notifications and alerts
  // - loading states
  // - error states

  // 4. Refs
  // - eventFormRef
  // - guestListRef
  // - budgetCalculatorRef
  // - timelineRef
  
  // 5. Lifecycle Functions
  // - Load events and user data on mount
  // - Setup real-time notifications
  // - Initialize collaborative features
  // - Check user authentication
  
  // 6. Event Handlers
  // - handleEventCreate/Edit/Delete
  // - handleGuestAdd/Remove/RSVP
  // - handleBudgetItemAdd/Update
  // - handleVendorManagement
  // - handleTimelineUpdate
  // - handleTeamCollaboration
  // - handleAuth (login/register/logout)
  // - handleNotifications
  
  // 7. Planning Functions
  // - createEventPlan
  // - updateGuestList
  // - calculateBudget
  // - manageVendors
  // - trackTimeline
  // - coordinateTeam
  
  // 8. API Calls
  // - getEvents
  // - createEvent
  // - updateEvent
  // - manageGuests
  // - trackRSVPs
  // - manageBudget
  // - coordinateVendors
  // - updateTimeline
  // - manageTeam
  // - authenticate
  
  // 9. Utility Functions
  // - formatDate/time
  // - calculateCosts
  // - formatCurrency
  // - validateEventForm
  // - generateInvitations
  // - trackProgress
  
  // 10. Render Methods
  // - renderEventsList()
  // - renderEventPlanning()
  // - renderGuestManagement()
  // - renderBudgetTracker()
  // - renderVendorDashboard()
  // - renderTimeline()
  // - renderTeamCollaboration()
  // - renderAuthView()
  
  return (
    <main className="event-planner-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 11. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Events Dashboard**
   - Event cards with status indicators
   - Quick action buttons (edit, duplicate, share)
   - Filter and search functionality
   - Calendar view integration
   - Create new event button
   - Event statistics and analytics
   - Recent activity timeline

2. **Event Planning Interface**
   - Multi-step event creation wizard
   - Event details form with validation
   - Location selection with maps integration
   - Date and time picker with timezone support
   - Event type templates and customization
   - Capacity and seating arrangement tools
   - Event description with rich text editor

3. **Guest Management System**
   - Guest list with import/export capabilities
   - RSVP tracking with visual indicators
   - Invitation management and sending
   - Dietary restrictions and special needs tracking
   - Plus-one management interface
   - Guest communication tools
   - Check-in system for event day

4. **Budget Planning Dashboard**
   - Visual budget breakdown with charts
   - Category-based expense tracking
   - Vendor cost integration
   - Payment status indicators
   - Budget vs. actual comparison
   - Cost forecasting and alerts
   - Expense approval workflow

5. **Vendor Coordination Hub**
   - Vendor directory with contact management
   - Service category organization
   - Quote comparison tools
   - Contract status tracking
   - Communication history
   - Vendor rating and review system
   - Payment and invoice management

6. **Timeline and Milestone Tracker**
   - Interactive timeline visualization
   - Milestone creation and tracking
   - Task assignment and deadlines
   - Progress indicators and alerts
   - Critical path analysis
   - Team member responsibility tracking
   - Automated reminder system

7. **Team Collaboration Interface**
   - Team member invitation and management
   - Role and permission assignment
   - Task delegation and tracking
   - Communication and messaging tools
   - Document sharing and version control
   - Activity feed and notifications

## Event Planning Workflow Features

```javascript
// Comprehensive planning workflow:
const PlanningWorkflow = {
  // - Step-by-step event creation wizard
  // - Template selection for different event types
  // - Automated task generation based on event type
  // - Progress tracking with completion percentages
  // - Deadline management with smart reminders
  // - Workflow customization for specific needs
  // - Integration with external calendar systems
  // - Automated vendor suggestions based on requirements
};
```

## Guest Management Features

- **Bulk guest import** from CSV, Excel, or contacts
- **Smart invitation system** with customizable templates
- **Real-time RSVP tracking** with automatic updates
- **Guest categorization** (VIP, family, colleagues, etc.)
- **Dietary restriction management** with vendor integration
- **Check-in system** with QR codes for event day
- **Guest communication** tools with message templates
- **Plus-one tracking** with relationship management

## Budget Visualization and Tracking

- **Interactive budget charts** with drill-down capabilities
- **Real-time expense tracking** with receipt upload
- **Vendor cost integration** with automatic updates
- **Budget alerts** for overspending or milestones
- **Payment scheduling** and reminder system
- **Cost comparison** tools for vendor selection
- **Financial reporting** with export capabilities
- **Multi-currency support** for international events

## UI/UX Requirements

- Clean, professional event planning interface
- Mobile-first responsive design for on-the-go planning
- Fast workflow completion with minimal friction
- Visual feedback for all planning actions
- Loading states for all operations
- Error handling with helpful suggestions
- Accessibility compliance (ARIA labels, keyboard navigation)
- Touch-friendly interface for mobile planning
- Smooth animations and transitions
- Collaborative features with real-time updates

## Timeline and Project Management Interface

```javascript
// Advanced timeline management:
const TimelineFeatures = {
  // - Gantt chart visualization for complex events
  // - Drag-and-drop task scheduling
  // - Dependency management between tasks
  // - Critical path highlighting
  // - Resource allocation and conflict detection
  // - Milestone celebration and progress tracking
  // - Automated task suggestions based on event type
  // - Integration with team member calendars
};
```

## Collaboration and Communication Tools

- **Real-time messaging** between team members
- **Task assignment** with notification system
- **Document sharing** with version control
- **Activity feeds** for team coordination
- **Role-based permissions** for different access levels
- **Video conferencing** integration for planning meetings
- **Shared calendars** with availability checking
- **Mobile notifications** for urgent updates

## Vendor Management Interface

- **Vendor database** with search and filtering
- **Service category** organization and browsing
- **Quote request** system with comparison tools
- **Contract management** with status tracking
- **Review and rating** system for vendor selection
- **Communication history** and note taking
- **Payment tracking** and invoice management
- **Vendor performance** analytics and reporting

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// Authentication API functions:
// - login(credentials)
// - register(userData)
// - logout()
// - getCurrentUser()

// Event API functions:
// - getEvents(filters, sort)
// - createEvent(eventData)
// - updateEvent(id, eventData)
// - deleteEvent(id)
// - getEventDetails(id)

// Guest API functions:
// - getGuests(eventId)
// - addGuests(eventId, guestList)
// - updateGuest(id, guestData)
// - recordRSVP(guestId, rsvpData)
// - sendInvitations(eventId, guestIds)

// Budget API functions:
// - getBudget(eventId)
// - addBudgetItem(eventId, itemData)
// - updateBudgetItem(id, itemData)
// - deleteBudgetItem(id)

// Vendor API functions:
// - getVendors(eventId)
// - addVendor(eventId, vendorData)
// - updateVendor(id, vendorData)
// - removeVendor(id)

// Timeline API functions:
// - getTimeline(eventId)
// - addMilestone(eventId, milestoneData)
// - updateMilestone(id, milestoneData)
// - completeTask(id)

// Team API functions:
// - getTeam(eventId)
// - addTeamMember(eventId, memberData)
// - updatePermissions(memberId, permissions)
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
    <title>Event Planning Platform</title>
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
   - Proxy API calls to backend on port `YYYY`

2. **Dependencies**
   - Generate complete package.json with all necessary npm dependencies
   - Include React, Vite, charting libraries, calendar components, and any additional libraries needed

3. **Production Ready Features**
   - Comprehensive error handling and recovery
   - Real-time updates with optimistic UI
   - Responsive design with mobile optimization
   - Proper state management for complex event data
   - Performance optimization (lazy loading, memoization)
   - Accessibility compliance
   - Clean code with comments
   - User experience enhancements (smooth animations, shortcuts)
   - Offline functionality with sync capability
   - Integration with external services (calendars, maps)

**Very important:** Your frontend should be feature rich, production ready, and provide excellent event planning experience with intuitive management interface, comprehensive planning tools, seamless collaboration features, and responsive design that works across all devices.