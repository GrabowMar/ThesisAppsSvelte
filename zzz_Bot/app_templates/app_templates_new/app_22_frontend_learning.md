# Frontend Generation Prompt - React Language Learning Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (dashboard, lessons, vocabulary, grammar, quizzes, progress, profile).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**Language Learning System Frontend**  
A modern React frontend for language learning application, featuring interactive lessons, vocabulary training, grammar exercises, progress tracking, and gamified learning experience with responsive, multilingual design.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Interactive vocabulary lessons with flashcards
- Grammar exercises with immediate feedback
- Progress tracking with visual analytics
- Quiz and assessment interface
- Pronunciation guides with audio playback
- Multilingual interface support
- Gamification elements and achievements
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
  // - currentView (dashboard, lessons, vocabulary, grammar, quizzes, progress, profile, auth)
  // - user authentication state
  // - current course and lesson data
  // - vocabulary flashcards and review items
  // - quiz questions and progress
  // - grammar exercises and explanations
  // - user progress and analytics
  // - achievements and streaks
  // - audio playback state
  // - loading states
  // - error states

  // 4. Refs
  // - audioPlayerRef for pronunciation
  // - vocabularyCardRef for flashcards
  // - quizTimerRef for timed exercises
  // - progressChartRef for analytics
  
  // 5. Lifecycle Functions
  // - Load user profile and progress
  // - Initialize current course and lessons
  // - Setup audio playback capabilities
  // - Check authentication status
  
  // 6. Event Handlers
  // - handleLessonComplete
  // - handleVocabularyPractice
  // - handleGrammarExercise
  // - handleQuizSubmit
  // - handleAudioPlayback
  // - handleLanguageSwitch
  // - handleProgressUpdate
  // - handleAuth (login/register/logout)
  
  // 7. Learning Functions
  // - practiceVocabulary
  // - completeLesson
  // - submitQuiz
  // - reviewGrammar
  // - trackProgress
  // - playPronunciation
  
  // 8. API Calls
  // - getCourses/getLessons
  // - getVocabulary/practiceWord
  // - getGrammarTopics
  // - getQuizzes/submitQuiz
  // - getProgress/updateProgress
  // - getAchievements
  // - authenticate
  
  // 9. Utility Functions
  // - formatStudyTime
  // - calculateProgress
  // - generateFlashcard
  // - validateAnswer
  // - playAudio
  // - translateInterface
  
  // 10. Render Methods
  // - renderDashboard()
  // - renderLessonView()
  // - renderVocabularyTrainer()
  // - renderGrammarExercise()
  // - renderQuizInterface()
  // - renderProgressView()
  // - renderAuthView()
  
  return (
    <main className="language-learning-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 11. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Dashboard View**
   - Welcome message with current streak
   - Daily learning goals and progress
   - Quick access to recent lessons
   - Vocabulary review reminders
   - Achievement highlights and badges
   - Study time statistics
   - Recommended next activities
   - Language selection and course overview

2. **Lesson Interface**
   - Lesson content with rich media support
   - Interactive exercises and activities
   - Audio playback for pronunciation
   - Progress indicator within lesson
   - Note-taking and bookmarking features
   - Previous/Next lesson navigation
   - Completion confirmation and feedback
   - Related vocabulary and grammar hints

3. **Vocabulary Trainer**
   - Flashcard interface with flip animations
   - Multiple practice modes (recognition, recall, spelling)
   - Spaced repetition scheduling display
   - Progress tracking per word
   - Audio pronunciation for each word
   - Example sentences and usage
   - Difficulty adjustment controls
   - Review session statistics

4. **Grammar Exercise Interface**
   - Interactive grammar explanations
   - Fill-in-the-blank exercises
   - Sentence construction activities
   - Multiple choice questions
   - Immediate feedback with explanations
   - Grammar rule references
   - Progress tracking by topic
   - Error pattern analysis

5. **Quiz and Assessment View**
   - Multiple question type support
   - Timer display for timed quizzes
   - Progress indicator during quiz
   - Immediate or delayed feedback modes
   - Score display and performance analysis
   - Review incorrect answers
   - Retake options and attempt history
   - Certificate generation for completions

6. **Progress Analytics View**
   - Visual progress charts and graphs
   - Study time breakdown by activity
   - Skill level progression indicators
   - Streak tracking and calendar view
   - Performance trends and insights
   - Goal setting and achievement tracking
   - Comparative analytics with peers
   - Export progress reports

## Vocabulary Training Features

```javascript
// Advanced vocabulary learning:
const VocabularyFeatures = {
  // - Spaced repetition flashcards with smart scheduling
  // - Multiple choice recognition exercises
  // - Typing practice with spell checking
  // - Audio pronunciation with playback controls
  // - Image associations for visual learning
  // - Context sentences and real usage examples
  // - Difficulty-based word grouping
  // - Personal vocabulary list management
};
```

## Interactive Learning Interface

- **Gamified exercises** with points and rewards
- **Immediate feedback** with detailed explanations
- **Adaptive difficulty** based on performance
- **Interactive audio** with pronunciation guides
- **Visual progress** indicators and celebrations
- **Streak tracking** with motivational elements
- **Achievement system** with unlockable content
- **Social features** for competition and collaboration

## Grammar Learning Features

- **Interactive grammar rules** with examples
- **Contextual exercises** with real-world sentences
- **Error correction** with detailed explanations
- **Progressive complexity** building on previous lessons
- **Visual grammar** guides and diagrams
- **Practice modes** for different learning styles
- **Grammar reference** library with search
- **Common mistakes** highlighting and prevention

## UI/UX Requirements

- Clean, educational interface design
- Mobile-first responsive layout
- Fast lesson loading and smooth transitions
- Visual feedback for all learning interactions
- Loading states for content and audio
- Error handling with helpful guidance
- Accessibility compliance (ARIA labels, keyboard navigation)
- Multi-language interface support
- Dark/Light theme for comfortable studying
- Offline learning capability with sync

## Assessment and Quiz Interface

```javascript
// Comprehensive assessment system:
const AssessmentFeatures = {
  // - Multiple question types (multiple choice, fill-in, audio)
  // - Adaptive difficulty based on user performance
  // - Timed and untimed quiz modes
  // - Immediate feedback with explanations
  // - Progress tracking through assessment levels
  // - Detailed performance analytics
  // - Retry mechanisms for improvement
  // - Certification and completion badges
};
```

## Progress Visualization

- **Interactive charts** showing learning progression
- **Goal setting** with visual progress tracking
- **Study calendar** with activity heatmaps
- **Skill trees** showing unlocked abilities
- **Leaderboards** for social motivation
- **Time tracking** with detailed breakdowns
- **Achievement galleries** with earned badges
- **Performance insights** with improvement suggestions

## Audio and Pronunciation Features

- **Native speaker** audio for all vocabulary
- **Slow/normal speed** playback options
- **Pronunciation practice** with recording (mock)
- **Phonetic transcriptions** for learning aid
- **Audio exercises** with listening comprehension
- **Accent training** with regional variations
- **Audio controls** with repeat and bookmark
- **Offline audio** download for mobile learning

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// Authentication API functions:
// - login(credentials)
// - register(userData)
// - logout()
// - getCurrentUser()

// Learning API functions:
// - getCourses(language)
// - getLessons(courseId)
// - completeLesson(lessonId)
// - getVocabulary(level, category)
// - practiceVocabulary(wordId, answer)
// - getGrammarTopics(level)
// - submitGrammarExercise(topicId, answers)

// Assessment API functions:
// - getQuizzes(courseId)
// - submitQuiz(quizId, answers)
// - getProgress()
// - getAchievements()

// Audio API functions:
// - getPronunciation(word)
// - checkPronunciation(audioData)
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
    <title>Language Learning App</title>
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
   - Include React, Vite, audio handling libraries, and any additional libraries needed

3. **Production Ready Features**
   - Comprehensive error handling and recovery
   - Progressive learning with adaptive difficulty
   - Responsive design with mobile optimization
   - Proper state management for learning progress
   - Performance optimization (lazy loading, caching)
   - Accessibility compliance for educational content
   - Clean code with comments
   - User experience enhancements (smooth animations, motivation)
   - Offline learning capability with sync
   - Multi-language interface support

**Very important:** Your frontend should be feature rich, production ready, and provide excellent language learning experience with engaging interactive lessons, effective vocabulary training, comprehensive progress tracking, and responsive design that works across all devices.