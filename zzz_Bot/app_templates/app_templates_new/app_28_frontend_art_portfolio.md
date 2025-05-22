# Frontend Generation Prompt - React Art Portfolio Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (portfolio, gallery, upload, profile, discover, exhibitions).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**Art Portfolio Management System Frontend**  
A modern React frontend for art portfolio application, featuring elegant artwork showcase, gallery management, portfolio customization, artist networking, exhibition participation, and commission tracking with beautiful, artist-focused design.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Elegant artwork upload and management interface
- Interactive gallery creation and curation tools
- Professional portfolio customization options
- Artist profile management and networking
- Social sharing and community features
- Advanced art categorization and discovery
- Exhibition and commission management
- Responsive design optimized for visual art display

## Frontend Structure (App.jsx)

```jsx
// 1. Imports
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  // - currentView (portfolio, gallery, upload, profile, discover, exhibitions, commissions, auth)
  // - user authentication state
  // - artwork collection and galleries
  // - current artwork for viewing/editing
  // - artist profile and portfolio data
  // - social interactions (likes, comments, follows)
  // - exhibition opportunities and submissions
  // - commission requests and projects
  // - upload progress and file management
  // - search and discovery state
  // - loading states
  // - error states

  // 4. Refs
  // - artworkUploadRef
  // - galleryGridRef
  // - imageViewerRef
  // - portfolioCustomizerRef
  
  // 5. Lifecycle Functions
  // - Load artist portfolio and artworks
  // - Initialize image upload and processing
  // - Setup social interaction features
  // - Check authentication and permissions
  
  // 6. Event Handlers
  // - handleArtworkUpload/Edit/Delete
  // - handleGalleryCreate/Edit/Organize
  // - handleProfileUpdate/Customize
  // - handleSocialInteraction (like, comment, follow)
  // - handleExhibitionSubmission
  // - handleCommissionManagement
  // - handleArtworkDiscovery/Search
  // - handleAuth (login/register/logout)
  
  // 7. Art Management Functions
  // - uploadArtwork
  // - createGallery
  // - customizePortfolio
  // - shareArtwork
  // - submitToExhibition
  // - manageCommission
  
  // 8. API Calls
  // - getArtworks/uploadArtwork
  // - getGalleries/createGallery
  // - getProfile/updateProfile
  // - getSocialData/interact
  // - getExhibitions/submitWork
  // - getCommissions/updateCommission
  // - searchArt/discoverArtists
  // - authenticate
  
  // 9. Utility Functions
  // - formatArtworkData
  // - validateImageFile
  // - generateThumbnail
  // - calculatePortfolioMetrics
  // - formatExhibitionData
  // - optimizeImageDisplay
  
  // 10. Render Methods
  // - renderPortfolio()
  // - renderGalleryView()
  // - renderArtworkUpload()
  // - renderArtistProfile()
  // - renderDiscovery()
  // - renderExhibitions()
  // - renderCommissions()
  // - renderAuthView()
  
  return (
    <main className="art-portfolio-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 11. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Artist Portfolio Dashboard**
   - Artist profile overview with bio and statistics
   - Featured artworks showcase with hero display
   - Recent gallery updates and new additions
   - Social engagement metrics (likes, comments, follows)
   - Quick action buttons for upload and gallery creation
   - Exhibition opportunities and deadline reminders
   - Commission request notifications and status
   - Portfolio analytics and visitor insights

2. **Artwork Upload and Management**
   - Drag-and-drop artwork upload interface
   - Image processing with preview and cropping
   - Artwork metadata form (title, medium, dimensions, price)
   - Category and tag selection with suggestions
   - Batch upload capabilities for multiple works
   - Upload progress tracking with error handling
   - Image optimization and format conversion
   - Copyright and watermark options

3. **Gallery Creation and Curation**
   - Interactive gallery builder with drag-and-drop
   - Gallery themes and layout customization
   - Artwork organization with visual sorting
   - Gallery description and metadata editing
   - Public/private visibility controls
   - Gallery sharing and social media integration
   - Virtual exhibition mode with immersive viewing
   - Gallery analytics and visitor tracking

4. **Artwork Showcase and Viewer**
   - Full-screen artwork viewer with zoom capabilities
   - Artwork details panel with metadata and story
   - Social interaction buttons (like, comment, share)
   - Related artworks and artist recommendations
   - Previous/next navigation within galleries
   - Download and print options (if permitted)
   - Virtual reality and 3D viewing modes
   - Mobile-optimized touch navigation

5. **Artist Profile and Customization**
   - Professional profile editor with portfolio branding
   - Bio and artist statement management
   - Contact information and social media links
   - Portfolio theme and layout customization
   - Featured works and gallery highlights
   - Exhibition history and achievements
   - Commission availability and pricing
   - Professional verification and badges

6. **Art Discovery and Community**
   - Featured artists and trending artworks
   - Advanced search with filters and categories
   - Artist networking and following system
   - Community challenges and themed exhibitions
   - Art style and medium exploration
   - Personalized recommendations and discovery
   - Social feed with followed artists' updates
   - Art critique and feedback communities

7. **Exhibition and Commission Management**
   - Exhibition opportunity browser with filters
   - Application and submission tracking
   - Portfolio preparation and presentation tools
   - Commission request management and communication
   - Project timeline and milestone tracking
   - Client communication and file sharing
   - Invoice and payment tracking integration
   - Professional contract and agreement templates

## Artwork Display Features

```javascript
// Advanced artwork display capabilities:
const ArtworkDisplayFeatures = {
  // - High-resolution image viewer with zoom and pan
  // - Color-accurate display with ICC profile support
  // - Virtual gallery walls with realistic lighting
  // - Augmented reality preview in real spaces
  // - Multi-angle viewing for sculptures and 3D works
  // - Interactive hotspots for artwork details
  // - Slideshow mode with customizable transitions
  // - Mobile-optimized swipe navigation and gestures
};
```

## Portfolio Customization Interface

- **Professional themes** with artist-specific branding and color schemes
- **Layout customization** with grid options, spacing, and arrangement tools
- **Typography selection** with artist-appropriate fonts and styling
- **Logo and watermark** integration with brand consistency
- **Navigation customization** with menu structure and page organization
- **SEO optimization** with meta tags, descriptions, and search visibility
- **Social media integration** with automatic sharing and cross-promotion
- **Mobile responsiveness** with touch-optimized viewing and navigation

## Social and Networking Features

- **Artist following** system with personalized feeds and notifications
- **Artwork interaction** with likes, comments, and constructive feedback
- **Social sharing** with optimized images and professional presentation
- **Collaborative projects** with artist networking and partnership tools
- **Mentorship programs** with experienced artist guidance and feedback
- **Community challenges** with themed competitions and exhibitions
- **Peer critique** systems with structured feedback and improvement
- **Cross-promotion** tools with mutual artist support and visibility

## UI/UX Requirements

- Elegant, gallery-inspired interface design
- High-contrast, color-accurate display for artworks
- Mobile-first responsive layout with touch gestures
- Fast image loading with progressive enhancement
- Visual feedback for all artistic interactions
- Loading states optimized for large image files
- Error handling with artist-friendly guidance
- Accessibility compliance (ARIA labels, keyboard navigation)
- Dark/Light themes optimized for art viewing
- Print-friendly layouts for portfolio presentation

## Exhibition and Sales Interface

```javascript
// Professional exhibition and sales tools:
const ExhibitionSalesFeatures = {
  // - Exhibition submission wizard with requirements checklist
  // - Virtual exhibition creation with 3D gallery spaces
  // - Commission request form with project specifications
  // - Client communication tools with file sharing
  // - Pricing calculator with market analysis
  // - Sales tracking with revenue analytics
  // - Certificate of authenticity generation
  // - Shipping and logistics coordination tools
};
```

## Image Processing and Quality

- **Automatic image optimization** with format conversion and compression
- **Color space management** with sRGB and Adobe RGB support
- **Metadata preservation** with EXIF data and copyright information
- **Watermark application** with customizable opacity and positioning
- **Thumbnail generation** with multiple sizes and aspect ratios
- **Progressive loading** with low-quality placeholders and enhancement
- **Lazy loading** for performance optimization with large portfolios
- **Offline caching** with service worker integration for reliability

## Professional Tools and Analytics

- **Portfolio analytics** with visitor insights, engagement metrics, and trends
- **Market analysis** with pricing recommendations and comparable sales
- **SEO optimization** with search visibility and ranking improvements
- **Social media analytics** with reach, engagement, and audience insights
- **Commission tracking** with project timelines and client communication
- **Exhibition history** with submission tracking and success rates
- **Professional networking** with industry contacts and opportunities
- **Career development** tools with goal setting and achievement tracking

## Mobile and Accessibility Features

- **Touch-optimized navigation** with swipe gestures and pinch-to-zoom
- **Voice descriptions** for accessibility and inclusive viewing
- **High contrast modes** for visually impaired users
- **Keyboard navigation** with full functionality without mouse
- **Screen reader compatibility** with proper ARIA labels and descriptions
- **Responsive images** with appropriate sizing for different devices
- **Offline viewing** with cached portfolios and essential functionality
- **Progressive Web App** features with installation and push notifications

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// Authentication API functions:
// - login(credentials)
// - register(userData)
// - logout()
// - getCurrentUser()

// Artwork management API functions:
// - uploadArtwork(artworkData, imageFile)
// - getArtworks(filters, pagination)
// - updateArtwork(id, artworkData)
// - deleteArtwork(id)
// - getArtworkImage(id, size)

// Gallery management API functions:
// - createGallery(galleryData)
// - getGalleries()
// - updateGallery(id, galleryData)
// - addArtworkToGallery(galleryId, artworkId)

// Social interaction API functions:
// - likeArtwork(artworkId)
// - commentOnArtwork(artworkId, comment)
// - followArtist(artistId)
// - getFeed()

// Exhibition and commission API functions:
// - getExhibitions(filters)
// - submitToExhibition(exhibitionId, submissionData)
// - getCommissions()
// - updateCommissionStatus(id, status)

// Discovery API functions:
// - searchArtworks(query, filters)
// - getFeaturedArtworks()
// - getRecommendations()
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
    <title>Art Portfolio Showcase</title>
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
   - High-quality image display with optimization
   - Responsive design with mobile optimization for art viewing
   - Proper state management for large image collections
   - Performance optimization (lazy loading, image optimization)
   - Accessibility compliance for art applications
   - Clean code with comments
   - User experience enhancements (smooth animations, touch gestures)
   - Progressive Web App features for offline portfolio access
   - SEO optimization for artist discovery

**Very important:** Your frontend should be feature rich, production ready, and provide excellent art portfolio experience with elegant artwork display, intuitive gallery management, professional portfolio customization, and responsive design that showcases art beautifully across all devices.