# Frontend Generation Prompt - React Career Networking Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (dashboard, profile, connections, jobs, messages, achievements).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**Professional Networking System Frontend**  
A modern React frontend for career networking application, featuring professional profile management, connection building, job marketplace, skill endorsement, real-time messaging, and achievement tracking with intuitive, professional design.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Professional profile creation and management interface
- Connection request and management system
- Job posting and application interface
- Skill endorsement and validation system
- Real-time messaging capabilities
- Professional achievements showcase
- Network analytics and insights
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
  // - currentView (dashboard, profile, connections, jobs, messages, achievements, auth)
  // - user authentication state
  // - user profile data
  // - connections and connection requests
  // - job listings and applications
  // - messages and conversations
  // - achievements and endorsements
  // - search results and filters
  // - notifications and alerts
  // - loading states
  // - error states

  // 4. Refs
  // - profileFormRef
  // - messageInputRef
  // - jobSearchRef
  // - fileUploadRef
  
  // 5. Lifecycle Functions
  // - Load user profile and network data
  // - Initialize real-time messaging
  // - Setup notification system
  // - Check authentication status
  
  // 6. Event Handlers
  // - handleProfileUpdate
  // - handleConnectionRequest/Accept/Decline
  // - handleJobApplication/Posting
  // - handleSkillEndorsement
  // - handleMessageSend/Receive
  // - handleAchievementAdd
  // - handleSearch/Filter
  // - handleAuth (login/register/logout)
  
  // 7. Networking Functions
  // - sendConnectionRequest
  // - endorseSkill
  // - applyToJob
  // - sendMessage
  // - updateProfile
  // - searchProfessionals
  
  // 8. API Calls
  // - getProfile/updateProfile
  // - getConnections/manageConnections
  // - getJobs/applyJob
  // - getMessages/sendMessage
  // - getAchievements/addAchievement
  // - searchProfiles/searchJobs
  // - authenticate
  
  // 9. Utility Functions
  // - formatDate
  // - calculateNetworkSize
  // - generateProfileCompletion
  // - validateJobApplication
  // - formatConnectionCount
  // - generateRecommendations
  
  // 10. Render Methods
  // - renderDashboard()
  // - renderProfile()
  // - renderConnections()
  // - renderJobs()
  // - renderMessages()
  // - renderAchievements()
  // - renderAuthView()
  
  return (
    <main className="networking-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 11. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Professional Dashboard**
   - Profile completion status and recommendations
   - Network activity feed with connection updates
   - Job recommendations based on profile
   - Recent messages and connection requests
   - Achievement highlights and milestones
   - Industry insights and trending topics
   - Quick actions for profile, connections, jobs
   - Network analytics and growth metrics

2. **Profile Management Interface**
   - Comprehensive profile editor with sections
   - Professional photo upload and cropping
   - Experience and education timeline
   - Skills list with proficiency levels
   - Achievement showcase with verification
   - Portfolio and project galleries
   - Contact information and privacy settings
   - Profile preview and completion tracking

3. **Connection Management**
   - Connection grid with search and filtering
   - Connection request inbox with actions
   - Suggested connections with mutual info
   - Connection details with interaction history
   - Network visualization and analytics
   - Bulk connection management tools
   - Connection import from other platforms
   - Professional relationship categorization

4. **Job Marketplace Interface**
   - Job search with advanced filtering
   - Job posting creation and management
   - Application tracking dashboard
   - Job recommendation engine
   - Company profile integration
   - Application materials management
   - Interview scheduling interface
   - Salary insights and market data

5. **Messaging System**
   - Conversation list with search
   - Real-time message interface
   - File sharing and attachment support
   - Professional message templates
   - Group messaging for teams
   - Message organization and archiving
   - Video call integration (mock)
   - Professional etiquette guidelines

6. **Achievement and Recognition**
   - Achievement timeline and showcase
   - Skill endorsement interface
   - Certification management
   - Professional milestone tracking
   - Peer recognition system
   - Achievement sharing and promotion
   - Verification and credential management
   - Professional development tracking

## Professional Profile Features

```javascript
// Comprehensive profile management:
const ProfileFeatures = {
  // - Rich profile editor with drag-and-drop sections
  // - Professional photo editing and optimization
  // - Experience timeline with visual progression
  // - Skills assessment and validation
  // - Portfolio integration with project showcases
  // - Professional summary optimization tools
  // - Privacy controls for sensitive information
  // - Profile optimization tips and suggestions
};
```

## Connection Building Interface

- **Smart connection suggestions** based on network analysis
- **Mutual connection** visibility and introductions
- **Connection request** templates and personalization
- **Network mapping** with visual relationship displays
- **Industry-based networking** with targeted suggestions
- **Professional event** integration for networking opportunities
- **Connection strength** indicators and relationship scoring
- **Networking goals** and target tracking

## Job Marketplace Features

- **Advanced job search** with multiple criteria and saved searches
- **One-click application** with pre-filled profile information
- **Application tracking** with status updates and timeline
- **Job alert system** with custom notification preferences
- **Company research** tools with insider insights
- **Salary negotiation** guidance and market data
- **Interview preparation** resources and scheduling
- **Career path** visualization and progression planning

## UI/UX Requirements

- Clean, professional networking interface design
- Mobile-first responsive layout
- Fast profile and connection loading
- Visual feedback for all networking actions
- Loading states for profile and job operations
- Error handling with professional guidance
- Accessibility compliance (ARIA labels, keyboard navigation)
- Touch-friendly interface for mobile networking
- Professional color scheme and typography
- Progressive Web App features for mobile usage

## Real-time Features

```javascript
// Real-time networking capabilities:
const RealTimeFeatures = {
  // - Live messaging with typing indicators
  // - Real-time connection request notifications
  // - Activity feed updates without refresh
  // - Job application status updates
  // - Online status indicators for connections
  // - Live endorsement and achievement notifications
  // - Real-time search suggestions and results
  // - Instant professional recommendations
};
```

## Skill and Endorsement System

- **Skill categorization** with industry-specific groupings
- **Peer endorsement** interface with validation
- **Skill assessment** tools and benchmarking
- **Professional certification** integration and verification
- **Skill gap analysis** with learning recommendations
- **Expertise scoring** based on endorsements and experience
- **Skill-based matching** for jobs and connections
- **Professional development** tracking and goal setting

## Analytics and Insights Interface

- **Profile view analytics** with visitor insights
- **Network growth** tracking and visualization
- **Connection quality** metrics and recommendations
- **Job application** success rates and optimization
- **Professional influence** scoring and trending
- **Industry benchmarking** and competitive analysis
- **Career progression** tracking and planning
- **Networking ROI** measurement and optimization

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// Authentication API functions:
// - login(credentials)
// - register(userData)
// - logout()
// - getCurrentUser()

// Profile API functions:
// - getProfile(userId)
// - updateProfile(profileData)
// - searchProfiles(query, filters)
// - getProfileAnalytics()

// Connection API functions:
// - getConnections(filters)
// - sendConnectionRequest(userId, message)
// - acceptConnection(requestId)
// - declineConnection(requestId)
// - getConnectionSuggestions()

// Job API functions:
// - getJobs(filters)
// - getJobDetails(jobId)
// - applyToJob(jobId, applicationData)
// - createJobPosting(jobData)
// - getApplications()

// Messaging API functions:
// - getConversations()
// - getMessages(conversationId)
// - sendMessage(recipientId, content)

// Achievement API functions:
// - getAchievements(userId)
// - addAchievement(achievementData)
// - endorseSkill(userId, skillId)
// - getEndorsements(userId)
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
    <title>Professional Networking Platform</title>
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
   - Include React, Vite, real-time communication libraries, and any additional libraries needed

3. **Production Ready Features**
   - Comprehensive error handling and recovery
   - Real-time networking updates with optimistic UI
   - Responsive design with mobile optimization
   - Proper state management for professional data
   - Performance optimization (lazy loading, caching)
   - Accessibility compliance for professional applications
   - Clean code with comments
   - User experience enhancements (smooth animations, shortcuts)
   - Progressive Web App features for mobile networking
   - Privacy and security considerations for professional data

**Very important:** Your frontend should be feature rich, production ready, and provide excellent professional networking experience with intuitive profile management, effective connection building, comprehensive job marketplace, and responsive design that works across all devices.