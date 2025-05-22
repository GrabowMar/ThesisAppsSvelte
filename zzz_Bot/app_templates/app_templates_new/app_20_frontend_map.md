# Frontend Generation Prompt - React Map Sharing Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (map, share location, routes, markers, search, settings).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**Map Sharing System Frontend**  
A modern React frontend for map sharing application, featuring interactive map visualization, real-time location sharing, collaborative mapping, route planning, and comprehensive search with intuitive, mobile-optimized design.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Interactive map display with zoom, pan, and layer controls
- Real-time location sharing with privacy controls
- Marker creation, editing, and management interface
- Route planning and navigation tools
- Advanced location search with autocomplete
- Collaborative mapping and sharing features
- Mobile-responsive design with touch gestures
- Geolocation integration for current position

## Frontend Structure (App.jsx)

```jsx
// 1. Imports
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  // - currentView (map, share, routes, markers, search, settings, auth)
  // - mapInstance and map configuration
  // - userLocation and geolocation state
  // - markers array with details
  // - routes array with waypoints
  // - sharedLocations from other users
  // - searchQuery and results
  // - selectedMarker/Route for editing
  // - user authentication state
  // - privacy settings and permissions
  // - loading states
  // - error states

  // 4. Refs
  // - mapRef for map container
  // - geolocationRef for location tracking
  // - searchInputRef
  // - markerPopupRef
  
  // 5. Lifecycle Functions
  // - Initialize map and load user data
  // - Setup geolocation tracking
  // - Load markers and routes for current view
  // - Check user authentication
  
  // 6. Event Handlers
  // - handleMapClick/Drag/Zoom
  // - handleLocationShare/Stop
  // - handleMarkerCreate/Edit/Delete
  // - handleRouteCreate/Edit/Delete
  // - handleSearch/Geocode
  // - handleAuth (login/register/logout)
  // - handlePrivacySettings
  
  // 7. Map Management Functions
  // - initializeMap
  // - addMarker
  // - createRoute
  // - shareLocation
  // - updateMapView
  
  // 8. API Calls
  // - getMapData
  // - shareLocation
  // - createMarker
  // - createRoute
  // - searchLocations
  // - geocodeAddress
  // - getNearbyPlaces
  // - authenticate
  
  // 9. Utility Functions
  // - formatCoordinates
  // - calculateDistance
  // - formatAddress
  // - validateLocation
  // - generateMapUrl
  
  // 10. Render Methods
  // - renderMap()
  // - renderLocationSharing()
  // - renderMarkerManager()
  // - renderRouteBuilder()
  // - renderSearchInterface()
  // - renderPrivacySettings()
  // - renderAuthView()
  
  return (
    <main className="map-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 11. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Interactive Map Display**
   - Full-screen map with zoom and pan controls
   - Layer switching (satellite, terrain, street)
   - Custom markers with popup information
   - Route visualization with waypoints
   - Real-time location indicators
   - Clustering for dense marker areas
   - Drawing tools for custom shapes
   - Measurement tools for distance and area

2. **Location Sharing Interface**
   - Current location display with accuracy
   - Share location button with privacy options
   - Location sharing duration controls
   - Message attachment for shared locations
   - Friend list for targeted sharing
   - Location history and timeline
   - Privacy zone configuration
   - Real-time sharing status indicator

3. **Marker Management System**
   - Marker creation with click-to-place
   - Marker editing with drag-and-drop
   - Category selection and icon customization
   - Bulk marker operations and management
   - Marker search and filtering
   - Import/export marker collections
   - Marker templates for common types
   - Collaborative marker editing

4. **Route Planning Interface**
   - Route creation with waypoint addition
   - Drag-and-drop route modification
   - Multiple route options comparison
   - Transportation mode selection
   - Route sharing and collaboration
   - Turn-by-turn directions display
   - Route optimization and analysis
   - GPX/KML route import/export

5. **Search and Discovery Tools**
   - Location search with autocomplete
   - Address geocoding and validation
   - Nearby places and points of interest
   - Category-based search filtering
   - Search history and saved searches
   - Popular and trending locations
   - Advanced search with multiple criteria
   - Search result clustering and organization

6. **Settings and Privacy Controls**
   - Location sharing privacy settings
   - Default map preferences and layers
   - Notification settings for sharing
   - Account management and security
   - Data export and backup options
   - Accessibility and display preferences
   - Integration settings for external services

## Map Visualization Features

```javascript
// Advanced map functionality:
const MapFeatures = {
  // - Interactive zoom with mouse wheel and touch gestures
  // - Pan and drag with smooth animations
  // - Layer switching between map types
  // - Custom marker icons and styling
  // - Popup windows with rich content
  // - Clustering for performance optimization
  // - Heat maps for density visualization
  // - Drawing tools for shapes and annotations
};
```

## Location Sharing and Tracking

- **Real-time location broadcasting** with smooth updates
- **Privacy controls** with granular sharing options
- **Temporary sharing** with automatic expiry
- **Geofencing** with entry/exit notifications
- **Location accuracy** indicators and validation
- **Battery optimization** for continuous tracking
- **Offline location** storage with sync capabilities
- **Location-based reminders** and notifications

## Marker and Route Management

- **Interactive marker placement** with click-to-create
- **Drag-and-drop editing** for easy repositioning
- **Rich marker popups** with media and descriptions
- **Route visualization** with elevation profiles
- **Waypoint management** with reordering capabilities
- **Route alternatives** with comparison features
- **Custom icons** and marker styling options
- **Collaborative editing** with real-time updates

## UI/UX Requirements

- Clean, map-focused interface design
- Mobile-first responsive layout
- Touch-friendly controls for mobile devices
- Smooth animations and transitions
- Visual feedback for all map interactions
- Loading states for map and data operations
- Error handling with helpful location guidance
- Accessibility compliance for maps and navigation
- Dark/Light theme for different environments
- High contrast mode for outdoor visibility

## Mobile and Touch Optimization

```javascript
// Mobile-optimized mapping:
const MobileFeatures = {
  // - Touch gestures for zoom, pan, and rotation
  // - Responsive map controls and toolbars
  // - GPS integration for current location
  // - Offline map caching for poor connectivity
  // - Battery-efficient location tracking
  // - Compass integration for orientation
  // - Voice-guided navigation support
  // - Quick actions and shortcuts for common tasks
};
```

## Search and Discovery Interface

- **Auto-complete search** with intelligent suggestions
- **Category filtering** with visual icons
- **Proximity search** with radius controls
- **Search result previews** with map highlights
- **Saved searches** and favorite locations
- **Search history** with quick access
- **Multi-language search** support
- **Voice search** integration for hands-free use

## Collaboration and Sharing Features

- **Real-time collaboration** on shared maps
- **Permission management** for different access levels
- **Activity feed** showing recent changes
- **Comment system** for markers and routes
- **Version history** for collaborative maps
- **Share links** with customizable permissions
- **Social features** for following and discovery
- **Group management** for team collaboration

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// Authentication API functions:
// - login(credentials)
// - register(userData)
// - logout()
// - getCurrentUser()

// Map API functions:
// - getMaps()
// - getMap(id)
// - createMap(mapData)
// - updateMap(id, mapData)
// - deleteMap(id)

// Location API functions:
// - shareLocation(locationData)
// - getSharedLocations(mapId, timeRange)
// - updateLocation(id, locationData)
// - stopLocationSharing()

// Marker API functions:
// - getMarkers(mapId, bounds)
// - createMarker(markerData)
// - updateMarker(id, markerData)
// - deleteMarker(id)

// Route API functions:
// - getRoutes(mapId)
// - createRoute(routeData)
// - updateRoute(id, routeData)
// - deleteRoute(id)

// Search API functions:
// - searchLocations(query, bounds)
// - geocodeAddress(address)
// - getNearbyPlaces(lat, lng, radius)
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
    <title>Map Sharing</title>
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
   - Include React, Vite, mapping libraries (Leaflet, OpenLayers, or Mapbox), and any additional libraries needed

3. **Production Ready Features**
   - Comprehensive error handling and recovery
   - Real-time updates with optimistic UI
   - Responsive design with mobile optimization
   - Proper state management for map data
   - Performance optimization (efficient rendering, caching)
   - Accessibility compliance for mapping applications
   - Clean code with comments
   - User experience enhancements (smooth interactions, intuitive controls)
   - Progressive Web App features
   - Offline functionality with map caching

**Very important:** Your frontend should be feature rich, production ready, and provide excellent map sharing experience with intuitive location sharing, comprehensive mapping tools, collaborative features, and responsive design optimized for both mobile and desktop use.