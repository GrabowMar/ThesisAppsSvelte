# Frontend Generation Prompt - React Polling Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (polls list, create poll, vote, results, analytics, profile).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**Polling System Frontend**  
A modern React frontend for polling application, featuring intuitive poll creation, engaging voting interface, real-time results display, comprehensive analytics, and time-aware poll management with responsive, accessible design.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Interactive poll creation with multiple types
- Engaging voting interface with immediate feedback
- Real-time results display with charts and graphs
- Comprehensive analytics dashboard
- Time-limited polls with countdown timers
- User authentication and profile management
- Poll discovery and search functionality
- Responsive design with mobile optimization

## Frontend Structure (App.jsx)

```jsx
// 1. Imports
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  // - currentView (polls, create, vote, results, analytics, profile, auth)
  // - polls array with pagination
  // - currentPoll for voting/viewing
  // - pollResults with real-time updates
  // - user authentication state
  // - pollCreation form data
  // - votingState and feedback
  // - timers for active polls
  // - loading states
  // - error states

  // 4. Refs
  // - pollFormRef
  // - voteFormRef
  // - resultsChartRef
  // - timerRef for countdowns
  
  // 5. Lifecycle Functions
  // - Load polls and user data on mount
  // - Setup real-time result updates
  // - Initialize poll timers and countdowns
  // - Check authentication status
  
  // 6. Event Handlers
  // - handlePollCreate/Edit/Delete
  // - handleVoteSubmit
  // - handleResultsView
  // - handlePollSearch/Filter
  // - handleAuth (login/register/logout)
  // - handleTimerUpdates
  // - handleNavigation
  
  // 7. Polling Functions
  // - createPoll
  // - submitVote
  // - loadResults
  // - calculatePercentages
  // - updateTimers
  
  // 8. API Calls
  // - getPolls
  // - getPoll
  // - createPoll
  // - votePoll
  // - getResults
  // - getAnalytics
  // - authenticate
  // - getUserPolls
  
  // 9. Utility Functions
  // - formatDate/timeRemaining
  // - calculatePercentage
  // - generateChartData
  // - validatePollForm
  // - formatVoteCount
  
  // 10. Render Methods
  // - renderPollsList()
  // - renderPollCreator()
  // - renderVotingInterface()
  // - renderResults()
  // - renderAnalytics()
  // - renderAuthView()
  // - renderPollCard()
  
  return (
    <main className="polling-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 11. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Polls List View**
   - Header with navigation and search
   - Filter options (active, completed, my polls)
   - Poll cards with preview and status
   - Create new poll button
   - Pagination for large poll collections
   - Sort options (newest, most votes, ending soon)
   - Category filters and tags

2. **Poll Creation View**
   - Poll title and description fields
   - Poll type selection (single, multiple, ranking)
   - Dynamic option input with add/remove
   - End date/time picker with timezone
   - Privacy settings (public, private, link-only)
   - Advanced settings (authentication required, multiple votes)
   - Preview mode before publishing
   - Form validation with real-time feedback

3. **Voting Interface View**
   - Clear poll question and description
   - Interactive option selection (radio, checkbox, drag-drop for ranking)
   - Progress indicators for poll completion
   - Time remaining countdown
   - Vote submission with confirmation
   - Results preview (if allowed)
   - Share poll functionality

4. **Results Display View**
   - Live results with animated charts
   - Percentage and vote count displays
   - Bar charts, pie charts, and other visualizations
   - Real-time updates without page refresh
   - Export results functionality
   - Voter statistics and demographics
   - Time-series voting patterns

5. **Analytics Dashboard View**
   - Comprehensive poll performance metrics
   - Voting pattern analysis with charts
   - Comparative analytics across polls
   - Engagement statistics and trends
   - Export options for detailed analysis
   - Custom date range selection
   - Interactive data visualization

6. **User Profile View**
   - User stats (polls created, votes cast)
   - List of created polls with status
   - Voting history and activity
   - Account settings and preferences
   - Poll creation analytics
   - Achievement badges or milestones

## Voting Interface Features

```javascript
// Interactive voting system:
const VotingFeatures = {
  // - Single-click voting with confirmation
  // - Multiple selection with visual feedback
  // - Drag-and-drop ranking interface
  // - Progress indicators and validation
  // - Vote preview before submission
  // - Real-time vote count updates
  // - Anonymous voting options
  // - Vote change/update capabilities (if allowed)
};
```

## Real-time Results Features

- **Live result updates** without page refresh
- **Animated charts** with smooth transitions
- **Multiple visualization types** (bar, pie, line charts)
- **Interactive result exploration** with hover details
- **Real-time vote count** with percentage calculations
- **Results history** and trend analysis
- **Export capabilities** for sharing results
- **Mobile-optimized** chart displays

## Time Management Interface

- **Countdown timers** for active polls
- **Visual time indicators** (progress bars, clock displays)
- **Time zone awareness** for global polls
- **Automatic poll closure** notifications
- **Poll status badges** (active, ending soon, closed)
- **Schedule poll creation** for future activation
- **Time-based filtering** and sorting

## UI/UX Requirements

- Clean, modern polling interface design
- Mobile-first responsive layout
- Fast poll creation and voting flows
- Visual feedback for all user interactions
- Loading states for all operations
- Error handling with user-friendly messages
- Accessibility compliance (ARIA labels, keyboard navigation)
- Dark/Light theme support
- Smooth animations and transitions
- Touch-friendly interface for mobile voting

## Poll Creation Interface

```javascript
// Advanced poll creation:
const PollCreationFeatures = {
  // - Dynamic option management (add/remove/reorder)
  // - Rich text support for descriptions
  // - Image uploads for poll options
  // - Template selection for common poll types
  // - Bulk option import from CSV/text
  // - Poll preview with live updates
  // - Draft saving and auto-save
  // - Poll duplication for similar polls
};
```

## Analytics and Visualization

- **Interactive charts** with drill-down capabilities
- **Multiple chart types** (bar, pie, line, area charts)
- **Real-time data** with automatic updates
- **Comparative analysis** across multiple polls
- **Export functionality** (PNG, PDF, CSV)
- **Custom date ranges** for historical analysis
- **Responsive chart design** for mobile devices
- **Color-coded visualizations** with accessibility support

## Search and Discovery Features

- **Advanced search** with multiple filters
- **Category-based browsing** with tags
- **Trending polls** and popular content
- **Recently created/updated** poll lists
- **Search suggestions** and autocomplete
- **Saved searches** and bookmarks
- **Poll recommendations** based on user activity

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// Authentication API functions:
// - login(credentials)
// - register(userData)
// - logout()
// - getCurrentUser()

// Poll API functions:
// - getPolls(page, filter, sort)
// - getPoll(id)
// - createPoll(pollData)
// - updatePoll(id, pollData)
// - deletePoll(id)
// - votePoll(id, voteData)

// Results API functions:
// - getResults(id)
// - getAnalytics(id, dateRange)
// - exportResults(id, format)

// Discovery API functions:
// - searchPolls(query, filters)
// - getTrendingPolls()
// - getUserPolls(userId)
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
    <title>Polling Application</title>
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
   - Real-time updates with optimistic UI
   - Responsive design with mobile optimization
   - Proper state management for polling data
   - Performance optimization (lazy loading, memoization)
   - Accessibility compliance
   - Clean code with comments
   - User experience enhancements (smooth animations, shortcuts)
   - Progressive Web App features
   - Social sharing capabilities

**Very important:** Your frontend should be feature rich, production ready, and provide excellent polling experience with intuitive poll creation, engaging voting interface, real-time results visualization, and responsive design that works across all devices.