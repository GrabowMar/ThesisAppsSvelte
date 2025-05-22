# Frontend Generation Prompt - React Microblog Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (home feed, profile, create post, search, notifications).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**Microblog System Frontend**  
A modern React frontend for microblog application, featuring social posting, timeline feeds, user interactions, profile management, and real-time engagement with intuitive, mobile-first design.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Post creation and management (CRUD) interface
- User profile management and customization
- Dynamic timeline/feed with infinite scroll
- Real-time post interactions (likes, comments, shares)
- User discovery and following system
- Advanced search and hashtag exploration
- Responsive design with mobile optimization
- Real-time notifications and updates

## Frontend Structure (App.jsx)

```jsx
// 1. Imports
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  // - currentView (feed, profile, create, search, notifications, auth)
  // - user authentication state
  // - posts array with infinite scroll
  // - currentUser profile data
  // - selectedUser for profile view
  // - searchQuery and results
  // - notifications array
  // - compose post state
  // - loading states
  // - error states

  // 4. Refs
  // - postComposerRef
  // - feedScrollRef for infinite scroll
  // - imageUploadRef
  
  // 5. Lifecycle Functions
  // - Check authentication on mount
  // - Load user feed and profile
  // - Setup real-time updates
  // - Initialize infinite scroll
  
  // 6. Event Handlers
  // - handlePostCreate/Edit/Delete
  // - handleLike/Unlike
  // - handleComment/Reply
  // - handleFollow/Unfollow
  // - handleSearch
  // - handleProfileUpdate
  // - handleAuth (login/register/logout)
  // - handleInfiniteScroll
  
  // 7. Social Interaction Functions
  // - likePost/unlikePost
  // - addComment/deleteComment
  // - followUser/unfollowUser
  // - sharePost
  // - reportContent
  
  // 8. API Calls
  // - getPosts/getFeed
  // - createPost/updatePost/deletePost
  // - getUserProfile/updateProfile
  // - likePost/commentOnPost
  // - followUser/unfollowUser
  // - searchPosts/searchUsers
  // - authenticate
  
  // 9. Utility Functions
  // - formatDate/timeAgo
  // - formatNumber (likes, followers)
  // - parseHashtags/mentions
  // - validatePost/validateProfile
  // - uploadImage
  
  // 10. Render Methods
  // - renderFeed()
  // - renderProfile()
  // - renderPostComposer()
  // - renderSearchView()
  // - renderAuthView()
  // - renderNotifications()
  // - renderPost()
  
  return (
    <main className="microblog-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 11. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Home Feed View**
   - Header with logo, search, and user menu
   - Post composer with character limit
   - Timeline with infinite scroll
   - Post cards with interactions
   - Trending hashtags sidebar
   - Quick navigation buttons
   - Real-time post updates

2. **Post Composer**
   - Text area with character counter
   - Media upload (images/videos)
   - Hashtag and mention autocomplete
   - Privacy settings (public/private)
   - Post button with loading state
   - Draft saving functionality
   - Preview mode

3. **User Profile View**
   - Profile header with avatar and bio
   - Follow/unfollow button
   - Stats display (posts, followers, following)
   - User's posts grid/list
   - Edit profile button (for own profile)
   - Profile customization options

4. **Profile Edit View**
   - Avatar upload and crop
   - Display name and username fields
   - Bio text area with character limit
   - Location and website fields
   - Privacy settings
   - Account settings

5. **Search and Discovery View**
   - Search bar with filters (posts, users, hashtags)
   - Search results with tabs
   - Trending hashtags list
   - Suggested users to follow
   - Search history and saved searches
   - Real-time search suggestions

6. **Post Detail View**
   - Expanded post view
   - Full comment thread
   - Share options
   - Related posts
   - Post analytics (for own posts)

## Post Interaction Features

```javascript
// Social interaction system:
const InteractionFeatures = {
  // - Like/unlike with heart animation
  // - Comment with nested replies
  // - Share/repost functionality
  // - Bookmark posts for later
  // - Report inappropriate content
  // - Real-time interaction counts
  // - Engagement notifications
  // - Mention notifications (@username)
};
```

## Timeline and Feed Features

- **Infinite scroll** with lazy loading
- **Pull-to-refresh** functionality
- **Real-time updates** for new posts
- **Multiple timeline views** (following, trending, recent)
- **Post filtering** and sorting options
- **Engagement-based ranking**
- **Auto-refresh** with visual indicators
- **Offline support** with cached content

## User Profile Features

- **Customizable profiles** with themes
- **Avatar upload** with image cropping
- **Bio editing** with rich text support
- **Link verification** and validation
- **Privacy controls** for profile visibility
- **Follower/following** management
- **Block and mute** functionality
- **Account verification** badges

## UI/UX Requirements

- Clean, modern social media interface
- Mobile-first responsive design
- Fast interactions with optimistic updates
- Smooth animations and transitions
- Visual feedback for all user actions
- Loading states for all operations
- Error handling with user-friendly messages
- Accessibility compliance (ARIA labels, keyboard navigation)
- Dark/Light theme toggle
- Customizable interface preferences

## Real-time Features

```javascript
// Real-time functionality:
const RealTimeFeatures = {
  // - Live like and comment updates
  // - New post notifications
  // - Following activity alerts
  // - Direct message indicators
  // - Online status indicators
  // - Typing indicators for comments
  // - Push notifications support
  // - Real-time follower count updates
};
```

## Search and Discovery Interface

- **Advanced search** with multiple filters
- **Hashtag exploration** with trending analysis
- **User discovery** with follow suggestions
- **Search autocomplete** with recent searches
- **Saved searches** and bookmarks
- **Geographic search** (if location enabled)
- **Content type filtering** (posts, media, users)

## Notification System

- **In-app notifications** with badges
- **Notification center** with categorization
- **Push notification** support
- **Email notification** preferences
- **Real-time alerts** for interactions
- **Mention notifications** with quick reply
- **Follow notifications** and requests

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// Authentication API functions:
// - login(credentials)
// - register(userData)
// - logout()
// - getCurrentUser()

// Post API functions:
// - getFeed(page, type)
// - getPosts(userId, page)
// - createPost(postData)
// - updatePost(id, postData)
// - deletePost(id)
// - likePost(id)
// - commentOnPost(id, comment)

// User API functions:
// - getUserProfile(id)
// - updateProfile(profileData)
// - followUser(id)
// - unfollowUser(id)
// - getFollowers(id)
// - getFollowing(id)

// Search API functions:
// - searchPosts(query, filters)
// - searchUsers(query)
// - getTrending()
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
    <title>Microblog</title>
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
   - Include React, Vite, image processing libraries, and any additional libraries needed

3. **Production Ready Features**
   - Comprehensive error handling and recovery
   - Real-time updates with optimistic UI
   - Responsive design with mobile optimization
   - Proper state management for social features
   - Performance optimization (infinite scroll, image lazy loading)
   - Accessibility compliance
   - Clean code with comments
   - User experience enhancements (smooth animations, shortcuts)
   - Social sharing capabilities
   - Progressive Web App features

**Very important:** Your frontend should be feature rich, production ready, and provide excellent social media experience with intuitive posting interface, engaging timeline, comprehensive user profiles, and responsive design that works across all devices.