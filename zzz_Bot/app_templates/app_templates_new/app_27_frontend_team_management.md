# Frontend Generation Prompt - React Sports Team Management Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (dashboard, roster, performance, training, matches, health, communication).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**Sports Team Management System Frontend**  
A modern React frontend for sports team management application, featuring comprehensive player roster management, performance tracking dashboards, training coordination, match planning, statistical analysis, health monitoring, and team communication with professional, sports-focused design.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Comprehensive player roster management interface
- Interactive performance tracking and analytics dashboards
- Training schedule creation and management tools
- Match/game planning and lineup management
- Advanced statistical analysis and reporting
- Health and injury monitoring systems
- Team communication and messaging platform
- Role-based interface with coach, player, and staff views
- Responsive design optimized for mobile and tablet use

## Frontend Structure (App.jsx)

```jsx
// 1. Imports
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  // - currentView (dashboard, roster, performance, training, matches, health, communication, auth)
  // - user authentication state and role
  // - team roster and player profiles
  // - performance data and analytics
  // - training schedules and sessions
  // - match schedules and results
  // - injury reports and health status
  // - team messages and communications
  // - equipment inventory and status
  // - loading states
  // - error states

  // 4. Refs
  // - performanceChartRef
  // - rosterTableRef
  // - trainingCalendarRef
  // - matchLineupRef
  
  // 5. Lifecycle Functions
  // - Load team data and roster on mount
  // - Initialize performance tracking
  // - Setup real-time communication
  // - Check user role and permissions
  
  // 6. Event Handlers
  // - handlePlayerAdd/Edit/Remove
  // - handlePerformanceTrack/Update
  // - handleTrainingSchedule/Attendance
  // - handleMatchPlan/LineupSet
  // - handleInjuryReport/Update
  // - handleTeamMessage/Communication
  // - handleStatisticsAnalysis
  // - handleAuth (login/register/logout)
  
  // 7. Team Management Functions
  // - addPlayer
  // - trackPerformance
  // - scheduleTraining
  // - planMatch
  // - reportInjury
  // - sendMessage
  // - analyzeStatistics
  
  // 8. API Calls
  // - getPlayers/addPlayer
  // - getPerformance/trackPerformance
  // - getTraining/scheduleTraining
  // - getMatches/planMatch
  // - getInjuries/reportInjury
  // - getMessages/sendMessage
  // - getAnalytics/getStatistics
  // - authenticate
  
  // 9. Utility Functions
  // - formatPlayerStats
  // - calculateTeamMetrics
  // - generatePerformanceInsights
  // - validateTrainingData
  // - formatMatchData
  // - checkUserPermissions
  
  // 10. Render Methods
  // - renderDashboard()
  // - renderRoster()
  // - renderPerformance()
  // - renderTraining()
  // - renderMatches()
  // - renderHealth()
  // - renderCommunication()
  // - renderAuthView()
  
  return (
    <main className="sports-team-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 11. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Team Dashboard**
   - Team overview with key metrics and stats
   - Upcoming matches and training sessions
   - Recent performance highlights
   - Injury status and player availability
   - Quick action buttons for common tasks
   - Team communication highlights
   - Performance trends and analytics preview
   - Role-based dashboard customization

2. **Player Roster Management**
   - Complete player roster with photos and details
   - Player profile cards with stats and information
   - Add/edit/remove player functionality
   - Position-based filtering and organization
   - Player status indicators (active, injured, suspended)
   - Contact information and emergency contacts
   - Performance summary for each player
   - Bulk operations and roster management tools

3. **Performance Tracking Dashboard**
   - Interactive charts showing individual player metrics
   - Team performance analytics and comparisons
   - Performance trend analysis over time
   - Benchmark comparisons and goal tracking
   - Custom metric tracking and visualization
   - Performance data entry and validation
   - Export capabilities for coaching analysis
   - Performance improvement recommendations

4. **Training Management Interface**
   - Training calendar with session scheduling
   - Training session creation and management
   - Attendance tracking and management
   - Training type categorization and planning
   - Performance correlation with training data
   - Resource allocation and facility management
   - Training effectiveness analysis
   - Player-specific training plans

5. **Match Management System**
   - Match schedule with upcoming games and results
   - Match planning with opponent analysis
   - Lineup creation and formation management
   - Live match statistics and scoring
   - Match report generation and analysis
   - Player performance during matches
   - Tactical planning and strategy tools
   - Post-match analysis and insights

6. **Health and Injury Monitoring**
   - Injury report dashboard with status tracking
   - Player health profiles and medical history
   - Recovery timeline and return-to-play tracking
   - Health checkup scheduling and results
   - Fitness assessment and monitoring
   - Medical clearance management
   - Emergency contact quick access
   - Health trend analysis and risk assessment

7. **Team Communication Hub**
   - Team messaging with role-based channels
   - Announcements and important notifications
   - File sharing for tactics and documents
   - Calendar integration for events and meetings
   - Group messaging for specific positions or units
   - Coach-to-player private messaging
   - Parent communication for youth teams
   - Meeting scheduling and coordination

## Player Management Features

```javascript
// Advanced player management capabilities:
const PlayerManagementFeatures = {
  // - Comprehensive player profiles with photos and statistics
  // - Position-specific data tracking and analysis
  // - Contract and eligibility management
  // - Performance history and development tracking
  // - Skill assessment and improvement planning
  // - Player comparison and benchmarking tools
  // - Recruitment and scouting data integration
  // - Academic progress tracking for student athletes
};
```

## Performance Analytics Interface

- **Interactive dashboards** with customizable metrics and KPIs
- **Trend analysis** with historical performance data visualization
- **Comparative analytics** between players, positions, and seasons
- **Goal setting** and achievement tracking for individual and team objectives
- **Performance correlation** analysis with training, health, and match data
- **Predictive modeling** for performance improvement and injury prevention
- **Export functionality** for detailed coaching analysis and reports
- **Real-time data** integration with training and match statistics

## Training Coordination Tools

- **Calendar integration** with scheduling conflicts detection
- **Session planning** with objective setting and resource allocation
- **Attendance management** with automated notifications and follow-up
- **Performance tracking** during training sessions with immediate feedback
- **Training load** monitoring and periodization planning
- **Skill development** tracking with progression indicators
- **Equipment management** with availability and maintenance tracking
- **Weather integration** for outdoor training planning

## UI/UX Requirements

- Professional sports-focused interface design
- Mobile-first responsive layout for sideline and field use
- Fast data entry with touch-friendly controls
- Visual feedback for all team management actions
- Loading states optimized for sports data operations
- Error handling with context-sensitive guidance
- Accessibility compliance (ARIA labels, keyboard navigation)
- Role-based interface customization (coach vs player view)
- High contrast options for outdoor visibility
- Offline functionality for critical team operations

## Match Management Interface

```javascript
// Comprehensive match management tools:
const MatchManagementFeatures = {
  // - Pre-match planning with opponent analysis and strategy
  // - Lineup management with formation visualization
  // - Live match statistics tracking and real-time updates
  // - Substitution planning and tactical adjustments
  // - Post-match analysis with performance review
  // - Video integration for tactical analysis
  // - Scouting report integration and opponent intelligence
  // - Travel coordination and logistics management
};
```

## Health and Safety Interface

- **Injury reporting** with photo documentation and severity assessment
- **Recovery tracking** with progress monitoring and milestone management
- **Medical integration** with healthcare provider communication
- **Fitness testing** with baseline establishment and progress tracking
- **Concussion protocol** with step-by-step return-to-play procedures
- **Emergency procedures** with quick access to medical information
- **Wellness monitoring** with mood and fatigue tracking
- **Nutrition tracking** with dietary recommendations and monitoring

## Statistical Analysis and Reporting

- **Advanced statistics** with sport-specific metrics and calculations
- **Performance visualization** with charts, graphs, and heat maps
- **Team analytics** with strengths, weaknesses, and improvement areas
- **Seasonal reports** with comprehensive performance summaries
- **Custom metrics** with user-defined KPIs and measurements
- **Export capabilities** for presentations and external analysis
- **Benchmarking tools** with league and historical comparisons
- **Predictive analytics** for performance trends and projections

## Communication and Collaboration

- **Multi-channel messaging** with team, position, and individual channels
- **File sharing** with tactical documents, videos, and presentations
- **Calendar integration** with shared schedules and event coordination
- **Notification system** with priority levels and delivery preferences
- **Voice messaging** for quick communication and motivation
- **Video conferencing** integration for remote meetings and analysis
- **Parent portal** for youth team communication and updates
- **Translation support** for multilingual teams

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// Authentication API functions:
// - login(credentials)
// - register(userData)
// - logout()
// - getCurrentUser()

// Player management API functions:
// - getPlayers()
// - addPlayer(playerData)
// - updatePlayer(id, playerData)
// - deletePlayer(id)
// - getPlayerPerformance(playerId)

// Performance tracking API functions:
// - trackPerformance(performanceData)
// - getTeamPerformance()
// - getPerformanceAnalytics(dateRange)

// Training management API functions:
// - getTrainingSchedule()
// - createTrainingSession(sessionData)
// - markAttendance(sessionId, attendanceData)
// - updateTrainingSession(id, sessionData)

// Match management API functions:
// - getMatches()
// - createMatch(matchData)
// - setLineup(matchId, lineupData)
// - recordMatchStats(matchId, statsData)

// Health monitoring API functions:
// - getInjuries()
// - reportInjury(injuryData)
// - updateInjuryStatus(id, statusData)
// - getHealthRecords(playerId)

// Communication API functions:
// - getMessages()
// - sendMessage(messageData)
// - getAnnouncements()
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
    <title>Sports Team Management</title>
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
   - Include React, Vite, charting libraries, and any additional libraries needed

3. **Production Ready Features**
   - Comprehensive error handling and recovery
   - Real-time sports data updates with optimistic UI
   - Responsive design with mobile optimization for field use
   - Proper state management for complex team data
   - Performance optimization (lazy loading, efficient rendering)
   - Accessibility compliance for sports applications
   - Clean code with comments
   - User experience enhancements (smooth animations, quick actions)
   - Progressive Web App features for offline field use
   - Role-based interface customization

**Very important:** Your frontend should be feature rich, production ready, and provide excellent sports team management experience with intuitive player management, comprehensive performance tracking, effective training coordination, and responsive design that works across all devices including tablets and phones for sideline and field use.