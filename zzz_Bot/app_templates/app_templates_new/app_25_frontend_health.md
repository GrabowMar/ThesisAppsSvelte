# Frontend Generation Prompt - React Mental Health Tracking Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (dashboard, mood, journal, wellness, resources, settings).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**Mental Wellness Tracking System Frontend**  
A modern React frontend for mental health application, featuring intuitive mood tracking, secure journaling, stress monitoring, wellness progress visualization, self-care management, and crisis support with compassionate, accessible design.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Intuitive mood and emotion tracking interface
- Secure journaling with privacy controls
- Stress level monitoring and pattern visualization
- Evidence-based coping strategy recommendations
- Progress tracking with motivational elements
- Self-care reminder and goal management
- Professional resource directory with crisis support
- Responsive design with accessibility focus

## Frontend Structure (App.jsx)

```jsx
// 1. Imports
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  // - currentView (dashboard, mood, journal, wellness, resources, settings, crisis, auth)
  // - user authentication state
  // - mood tracking data and history
  // - journal entries with privacy settings
  // - stress monitoring data
  // - wellness goals and progress
  // - self-care reminders and notifications
  // - coping strategies and effectiveness
  // - crisis support state
  // - loading states
  // - error states

  // 4. Refs
  // - moodSliderRef
  // - journalEditorRef
  // - reminderTimerRef
  // - crisisButtonRef
  
  // 5. Lifecycle Functions
  // - Load user wellness data on mount
  // - Initialize mood tracking interface
  // - Setup reminder notifications
  // - Check crisis support needs
  
  // 6. Event Handlers
  // - handleMoodTrack
  // - handleJournalEntry/Save/Delete
  // - handleStressRecord
  // - handleCopingStrategy
  // - handleGoalUpdate
  // - handleReminderSet/Complete
  // - handleCrisisSupport
  // - handleAuth (login/register/logout)
  
  // 7. Wellness Functions
  // - trackMood
  // - saveJournalEntry
  // - recordStress
  // - updateProgress
  // - setReminder
  // - accessCrisisSupport
  
  // 8. API Calls
  // - getMoodHistory/trackMood
  // - getJournalEntries/saveEntry
  // - getStressData/recordStress
  // - getWellnessProgress
  // - getCopingStrategies
  // - getReminders/setReminder
  // - getResources/getCrisisSupport
  // - authenticate
  
  // 9. Utility Functions
  // - formatDate/timeAgo
  // - calculateWellnessScore
  // - generateMoodInsights
  // - validateJournalEntry
  // - formatProgressData
  // - checkCrisisIndicators
  
  // 10. Render Methods
  // - renderDashboard()
  // - renderMoodTracker()
  // - renderJournal()
  // - renderWellnessProgress()
  // - renderResources()
  // - renderCrisisSupport()
  // - renderAuthView()
  
  return (
    <main className="mental-health-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 11. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Wellness Dashboard**
   - Daily wellness score with visual indicator
   - Quick mood tracking with emoji/slider interface
   - Recent journal entries preview
   - Wellness goal progress display
   - Self-care reminder notifications
   - Crisis support quick access button
   - Motivational insights and achievements
   - Weekly/monthly progress summary

2. **Mood Tracking Interface**
   - Interactive mood selection with emotions wheel
   - Energy level and sleep quality sliders
   - Trigger identification with customizable tags
   - Quick note attachment for context
   - Mood history visualization with charts
   - Pattern recognition and insights
   - Correlation analysis with other factors
   - Export mood data for healthcare providers

3. **Secure Journaling System**
   - Rich text editor with privacy indicators
   - Mood tagging and emotion categorization
   - Encrypted storage with local privacy controls
   - Search and filter by date, mood, tags
   - Journal insights and reflection prompts
   - Gratitude and positive focus sections
   - Voice-to-text capability for accessibility
   - Export options for therapeutic use

4. **Stress Monitoring Interface**
   - Stress level tracking with visual scales
   - Stressor identification and categorization
   - Physical symptom tracking checklist
   - Coping strategy effectiveness rating
   - Stress pattern analysis and visualization
   - Breathing exercises and immediate relief tools
   - Stress trigger warning system
   - Relaxation technique recommendations

5. **Wellness Progress View**
   - Goal setting with SMART criteria
   - Progress tracking with milestone celebrations
   - Visual progress charts and trends
   - Achievement badges and motivational elements
   - Wellness score calculation and history
   - Habit tracking for self-care activities
   - Weekly/monthly wellness reports
   - Goal adjustment and optimization tools

6. **Professional Resources and Crisis Support**
   - Mental health professional directory
   - Crisis hotline quick access with location awareness
   - Emergency contact management
   - Safety planning tools and resources
   - Therapeutic technique libraries
   - Support group finder with filters
   - Insurance and accessibility information
   - Immediate crisis intervention interface

## Mood Tracking Features

```javascript
// Advanced mood tracking capabilities:
const MoodTrackingFeatures = {
  // - Intuitive emotion wheel for detailed mood selection
  // - Multiple mood dimensions (happiness, anxiety, energy)
  // - Contextual triggers and environmental factors
  // - Photo mood journal with image recognition
  // - Voice mood notes with transcription
  // - Predictive mood modeling with early warnings
  // - Correlation analysis with sleep, weather, activities
  // - Shareable mood summaries for healthcare providers
};
```

## Journaling and Reflection Interface

- **Guided journaling** with therapeutic prompts and exercises
- **Privacy-first design** with local encryption indicators
- **Mood-based journaling** with emotional context integration
- **Gratitude practices** with daily appreciation logging
- **Reflection tools** for processing difficult emotions
- **Progress narratives** for tracking personal growth
- **Creative expression** options with drawing and multimedia
- **Therapeutic writing** exercises based on evidence-based practices

## Wellness Goal Management

- **Evidence-based goal** templates for mental health improvement
- **Progress visualization** with motivational milestone tracking
- **Habit formation** tools with streak tracking and rewards
- **Goal adjustment** algorithms for realistic target setting
- **Achievement celebration** with positive reinforcement
- **Social accountability** options for trusted support persons
- **Professional goal** sharing for therapy integration
- **Wellness challenge** participation with community support

## UI/UX Requirements

- Compassionate, calming interface design
- High accessibility compliance (WCAG 2.1 AA)
- Mobile-first responsive layout with touch-friendly controls
- Gentle visual feedback for all wellness interactions
- Loading states with calming animations
- Error handling with supportive, non-judgmental messaging
- Crisis-aware design with immediate support access
- Dark/Light themes for comfort and preference
- Intuitive navigation with minimal cognitive load
- Progressive disclosure to prevent overwhelm

## Crisis Support Integration

```javascript
// Crisis intervention and support features:
const CrisisSupportFeatures = {
  // - One-tap crisis hotline access with location awareness
  // - Safety planning tools with personalized coping strategies
  // - Emergency contact quick dial with relationship context
  // - Crisis risk assessment with appropriate resource direction
  // - Immediate coping tool access during crisis moments
  // - Professional referral with urgency level indication
  // - Crisis chat support integration
  // - Post-crisis check-in and recovery planning
};
```

## Privacy and Security Interface

- **Privacy dashboard** with granular data control options
- **Data encryption** status indicators and explanations
- **Sharing permissions** management for healthcare providers
- **Data export** tools for portability and backup
- **Anonymous usage** options for sensitive tracking
- **Secure authentication** with biometric options
- **Data retention** controls with automatic deletion options
- **Privacy education** resources and best practices

## Wellness Analytics and Insights

- **Pattern recognition** with automated insight generation
- **Correlation analysis** between mood, sleep, activities, weather
- **Predictive modeling** for mood and stress pattern forecasting
- **Personalized recommendations** based on individual data patterns
- **Progress benchmarking** against personal historical data
- **Wellness score** calculation with factor breakdown
- **Trend analysis** with actionable improvement suggestions
- **Data storytelling** with narrative progress summaries

## Self-Care and Reminder System

- **Intelligent reminders** based on mood patterns and needs
- **Customizable self-care** activity library with effectiveness tracking
- **Medication reminders** with adherence tracking (if applicable)
- **Mindfulness prompts** with guided meditation integration
- **Social connection** reminders for relationship maintenance
- **Physical wellness** reminders for exercise and nutrition
- **Professional appointment** tracking and preparation tools
- **Emergency plan** reminders and safety check rehearsals

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// Authentication API functions:
// - login(credentials)
// - register(userData)
// - logout()
// - getCurrentUser()

// Mood tracking API functions:
// - trackMood(moodData)
// - getMoodHistory(dateRange)
// - getMoodInsights()

// Journaling API functions:
// - saveJournalEntry(entryData)
// - getJournalEntries(filters)
// - updateJournalEntry(id, entryData)
// - deleteJournalEntry(id)

// Wellness API functions:
// - getWellnessProgress()
// - updateWellnessGoal(goalData)
// - trackSelfCareActivity(activityData)
// - setReminder(reminderData)

// Resources API functions:
// - getProfessionalResources(filters)
// - getCrisisSupport()
// - getCopingStrategies()
// - rateCopingStrategy(strategyId, rating)
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
    <title>Mental Wellness Tracker</title>
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
   - Include React, Vite, accessibility libraries, and any additional libraries needed

3. **Production Ready Features**
   - Comprehensive error handling with supportive messaging
   - Crisis-aware interface with immediate support access
   - High accessibility compliance for mental health applications
   - Privacy-focused design with user control
   - Proper state management for sensitive wellness data
   - Performance optimization (lazy loading, smooth animations)
   - Clean code with comments and mental health considerations
   - User experience enhancements (calming animations, motivational elements)
   - Progressive Web App features for reliable access
   - Offline functionality for crisis situations

**Very important:** Your frontend should be feature rich, production ready, and provide excellent mental wellness experience with compassionate design, intuitive mood tracking, secure journaling, effective progress visualization, and immediate crisis support access with responsive design that prioritizes accessibility and user privacy.