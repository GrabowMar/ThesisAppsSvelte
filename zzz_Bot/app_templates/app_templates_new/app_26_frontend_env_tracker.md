# Frontend Generation Prompt - React Environmental Impact Tracking Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (dashboard, carbon, challenges, community, insights, goals).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**Environmental Sustainability Tracking System Frontend**  
A modern React frontend for environmental impact application, featuring intuitive carbon footprint tracking, engaging sustainability challenges, resource consumption monitoring, community impact visualization, and personalized eco-recommendations with inspiring, action-oriented design.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Interactive carbon footprint tracking and visualization
- Engaging sustainability challenge participation
- Resource consumption monitoring and optimization
- Evidence-based eco-friendly tips and recommendations
- Community impact comparison and social features
- Progress visualization with motivational elements
- Achievement system with environmental milestones
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
  // - currentView (dashboard, carbon, challenges, community, insights, goals, auth)
  // - user authentication state
  // - carbon footprint data and history
  // - sustainability challenges and participation
  // - resource consumption tracking
  // - community rankings and impact data
  // - environmental goals and progress
  // - achievements and milestones
  // - eco-tips and recommendations
  // - loading states
  // - error states

  // 4. Refs
  // - carbonCalculatorRef
  // - challengeTimerRef
  // - chartRef for visualizations
  // - goalProgressRef
  
  // 5. Lifecycle Functions
  // - Load user environmental data on mount
  // - Initialize carbon tracking interface
  // - Setup challenge notifications
  // - Check achievement progress
  
  // 6. Event Handlers
  // - handleCarbonTrack
  // - handleChallengeJoin/Complete
  // - handleConsumptionLog
  // - handleGoalSet/Update
  // - handleTipRate/Implement
  // - handleCommunityInteraction
  // - handleDataVisualization
  // - handleAuth (login/register/logout)
  
  // 7. Environmental Functions
  // - trackCarbonActivity
  // - joinChallenge
  // - logConsumption
  // - calculateFootprint
  // - updateProgress
  // - shareAchievement
  
  // 8. API Calls
  // - getCarbonFootprint/trackActivity
  // - getChallenges/joinChallenge
  // - getConsumption/logConsumption
  // - getGoals/setGoal
  // - getTips/rateTip
  // - getCommunityData
  // - getAchievements
  // - authenticate
  
  // 9. Utility Functions
  // - formatCarbonValue
  // - calculatePercentage
  // - generateInsights
  // - validateActivityData
  // - formatEnvironmentalData
  // - generateRecommendations
  
  // 10. Render Methods
  // - renderDashboard()
  // - renderCarbonTracker()
  // - renderChallenges()
  // - renderCommunity()
  // - renderInsights()
  // - renderGoals()
  // - renderAuthView()
  
  return (
    <main className="environmental-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 11. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Environmental Dashboard**
   - Personal carbon footprint summary with visual indicators
   - Current sustainability challenges progress
   - Weekly/monthly environmental impact overview
   - Achievement badges and milestone celebrations
   - Quick action buttons for logging activities
   - Community impact comparison and rankings
   - Personalized eco-tips and recommendations
   - Environmental goal progress tracking

2. **Carbon Footprint Tracker**
   - Activity logging interface with category selection
   - Carbon calculator for different activities
   - Real-time emissions calculations and feedback
   - Carbon footprint visualization with charts
   - Historical tracking with trend analysis
   - Category breakdown (transport, energy, food, waste)
   - Offset suggestions and carbon neutrality tracking
   - Comparative analysis with regional averages

3. **Sustainability Challenges**
   - Available challenges grid with difficulty levels
   - Challenge details with goals and duration
   - Progress tracking with milestone indicators
   - Community challenge participation
   - Challenge creation interface for custom goals
   - Leaderboards and friendly competition
   - Challenge completion celebrations
   - Social sharing of achievements

4. **Resource Consumption Monitor**
   - Water, energy, and waste consumption logging
   - Efficiency scoring and optimization tips
   - Consumption trends and pattern analysis
   - Resource-specific recommendations
   - Smart meter integration interface (mock)
   - Household consumption comparison
   - Cost savings calculations
   - Environmental impact correlations

5. **Community Impact Hub**
   - Community leaderboards and rankings
   - Collective impact visualization
   - Social features for sharing achievements
   - Local environmental initiatives
   - Group challenges and team participation
   - Environmental impact stories and success cases
   - Mentorship and knowledge sharing
   - Regional environmental data and comparisons

6. **Environmental Insights and Goals**
   - Personalized environmental insights and trends
   - Goal setting with SMART criteria for sustainability
   - Progress visualization with motivational elements
   - Achievement tracking and milestone celebrations
   - Environmental impact projections
   - Personalized action recommendations
   - Long-term sustainability planning
   - Environmental education and resources

## Carbon Tracking Features

```javascript
// Advanced carbon footprint tracking:
const CarbonTrackingFeatures = {
  // - Activity-specific carbon calculators with scientific accuracy
  // - Real-time emissions feedback and environmental impact
  // - Transportation mode tracking with route optimization
  // - Energy consumption monitoring with efficiency recommendations
  // - Dietary carbon impact with alternative suggestions
  // - Waste tracking with recycling and reduction tips
  // - Offset tracking and carbon neutrality progress
  // - Comparative analysis with personal and community benchmarks
};
```

## Sustainability Challenge Interface

- **Gamified challenge** participation with progress tracking and rewards
- **Challenge categories** covering all aspects of environmental impact
- **Difficulty progression** from beginner to advanced sustainability practices
- **Team challenges** for households, workplaces, and communities
- **Custom challenge** creation with goal setting and tracking tools
- **Challenge discovery** with filtering by category, difficulty, and duration
- **Social elements** with sharing, competition, and mutual support
- **Educational components** with tips, resources, and learning materials

## Environmental Data Visualization

- **Interactive charts** showing carbon footprint trends and patterns
- **Comparative visualizations** with regional and global averages
- **Impact projections** showing future environmental benefits
- **Category breakdowns** with detailed analysis and optimization opportunities
- **Progress tracking** with visual goal achievement indicators
- **Community impact** visualizations showing collective environmental benefits
- **Efficiency metrics** with improvement recommendations and benchmarks
- **Achievement galleries** with environmental milestone celebrations

## UI/UX Requirements

- Clean, nature-inspired interface design
- Mobile-first responsive layout with touch-friendly controls
- Fast data visualization with smooth animations
- Visual feedback for all environmental actions
- Loading states with eco-friendly animations
- Error handling with constructive environmental guidance
- Accessibility compliance (ARIA labels, keyboard navigation)
- Green color palette with nature-inspired themes
- Motivational elements with positive reinforcement
- Educational tooltips and contextual help

## Community and Social Features

```javascript
// Community engagement and social impact:
const CommunityFeatures = {
  // - Leaderboards with privacy-respecting rankings
  // - Team formation for collective environmental challenges
  // - Social sharing of achievements and milestones
  // - Mentorship pairing for sustainability guidance
  // - Community goals with collective impact tracking
  // - Local environmental initiatives and events
  // - Knowledge sharing with tips and success stories
  // - Regional environmental data and community comparisons
};
```

## Goal Setting and Achievement System

- **SMART environmental goals** with specific, measurable targets
- **Progress tracking** with visual indicators and milestone celebrations
- **Achievement badges** for various environmental accomplishments
- **Streak tracking** for consistent environmental actions
- **Long-term planning** with annual sustainability targets
- **Goal adjustment** algorithms for realistic and achievable targets
- **Motivation system** with positive reinforcement and encouragement
- **Educational integration** with learning resources and guidance

## Environmental Education Interface

- **Personalized eco-tips** based on user behavior and environmental impact
- **Evidence-based recommendations** with scientific backing and sources
- **Interactive calculators** for environmental impact assessment
- **Educational content** with tutorials, guides, and sustainability principles
- **Action plans** with step-by-step instructions for environmental improvements
- **Resource library** with articles, videos, and expert recommendations
- **Impact explanations** with clear cause-and-effect relationships
- **Success stories** highlighting achievable environmental improvements

## Data Import and Integration

- **Smart meter integration** for automatic energy consumption tracking
- **Transportation app** integration for carbon footprint calculation
- **Fitness tracker** integration for active transportation monitoring
- **Calendar integration** for challenge reminders and goal tracking
- **Social media sharing** for achievement celebration and awareness
- **Bank transaction** analysis for consumption pattern insights (privacy-focused)
- **Weather data** integration for seasonal activity recommendations
- **Local utility** data integration for regional emission factors

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// Authentication API functions:
// - login(credentials)
// - register(userData)
// - logout()
// - getCurrentUser()

// Carbon tracking API functions:
// - trackCarbonActivity(activityData)
// - getCarbonFootprint(dateRange)
// - getCarbonBreakdown()
// - calculateEmissions(activityType, amount)

// Challenge API functions:
// - getChallenges(filters)
// - joinChallenge(challengeId)
// - updateChallengeProgress(challengeId, progressData)
// - createChallenge(challengeData)

// Community API functions:
// - getCommunityLeaderboard()
// - getCommunityImpact()
// - shareAchievement(achievementData)

// Goals and Analytics API functions:
// - setEnvironmentalGoal(goalData)
// - getGoalProgress()
// - getEnvironmentalInsights()
// - getAchievements()
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
    <title>Environmental Impact Tracker</title>
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
   - Real-time environmental calculations with accurate feedback
   - Responsive design with mobile optimization
   - Proper state management for environmental data
   - Performance optimization (lazy loading, efficient calculations)
   - Accessibility compliance for environmental applications
   - Clean code with comments
   - User experience enhancements (smooth animations, motivational elements)
   - Progressive Web App features for consistent access
   - Educational integration with actionable insights

**Very important:** Your frontend should be feature rich, production ready, and provide excellent environmental tracking experience with intuitive carbon footprint monitoring, engaging sustainability challenges, effective community features, and responsive design that inspires and motivates users toward sustainable living practices.