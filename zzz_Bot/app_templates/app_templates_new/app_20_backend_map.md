# Backend Generation Prompt - Flask Map Sharing Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/locations`, `/api/markers`, `/api/routes`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**Map Sharing System Backend**  
A comprehensive Flask backend for map sharing application, featuring location management, marker creation, route calculation, geographic search, real-time location sharing, and collaborative mapping with spatial data processing.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Interactive map display with custom markers and overlays
- Real-time location sharing and tracking
- Marker creation, editing, and management
- Route planning and navigation capabilities
- Advanced location search and geocoding
- User authentication and privacy controls
- Collaborative map sharing and permissions
- Geographic data processing and spatial queries
- Points of interest (POI) management
- Location-based notifications and alerts
- CORS support for frontend communication
- Database integration (SQLite or in-memory for simplicity)

## Backend Structure (app.py)

```python
# 1. Imports Section
from flask import Flask, jsonify, request, session
from flask_cors import CORS
import os
import sqlite3
from datetime import datetime, timedelta
import uuid
import json
import math
import requests
from geopy.distance import geodesic
from geopy.geocoders import Nominatim

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'

# 3. Database Models/Setup
# 4. Geographic Calculations
# 5. Location Processing
# 6. Route Algorithms
# 7. API Routes:
#    - GET /api/maps (list available maps)
#    - GET /api/maps/<id> (get map details)
#    - POST /api/maps (create map)
#    - PUT /api/maps/<id> (update map)
#    - DELETE /api/maps/<id> (delete map)
#    - GET /api/locations (get locations)
#    - POST /api/locations (share location)
#    - PUT /api/locations/<id> (update location)
#    - DELETE /api/locations/<id> (remove location)
#    - GET /api/markers (get markers)
#    - POST /api/markers (create marker)
#    - PUT /api/markers/<id> (update marker)
#    - DELETE /api/markers/<id> (delete marker)
#    - GET /api/routes (get routes)
#    - POST /api/routes (create route)
#    - PUT /api/routes/<id> (update route)
#    - DELETE /api/routes/<id> (delete route)
#    - GET /api/search (search locations)
#    - GET /api/geocode (geocode address)
#    - GET /api/nearby (find nearby places)
#    - POST /api/auth/register (user registration)
#    - POST /api/auth/login (user login)
#    - POST /api/auth/logout (user logout)
#    - GET /api/auth/user (get current user)
# 8. Error Handlers

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'YYYY')))
```

## Required API Endpoints

### Authentication Routes

1. **POST /api/auth/register**
   - Accept: username, email, password, location_preferences
   - Validate input and create user account
   - Set default privacy settings for location sharing
   - Return user info and session

2. **POST /api/auth/login**
   - Accept: username/email, password
   - Validate credentials
   - Create user session
   - Return user info and map preferences

3. **POST /api/auth/logout**
   - Clear user session
   - Stop any active location sharing
   - Return success response

4. **GET /api/auth/user**
   - Return current authenticated user info
   - Include location sharing preferences and privacy settings

### Map Management Routes

5. **GET /api/maps**
   - Return list of available maps
   - Include public maps and user's private maps
   - Support filtering by category, creator, region

6. **GET /api/maps/<id>**
   - Return specific map with all data
   - Include markers, routes, and shared locations
   - Check user permissions for access

7. **POST /api/maps**
   - Create new map
   - Accept: name, description, privacy_level, default_center
   - Initialize empty map with user permissions
   - Return created map

8. **PUT /api/maps/<id>**
   - Update map details
   - Accept: name, description, privacy_level, settings
   - Require appropriate permissions
   - Return updated map

9. **DELETE /api/maps/<id>**
   - Delete map and all associated data
   - Clean up markers, routes, and shared locations
   - Require owner permissions
   - Return confirmation

### Location Sharing Routes

10. **GET /api/locations**
    - Return shared locations on map
    - Accept: map_id, time_range, user_filter
    - Include real-time and historical locations
    - Check privacy permissions

11. **POST /api/locations**
    - Share current location
    - Accept: latitude, longitude, accuracy, timestamp, message
    - Validate coordinates and privacy settings
    - Return confirmation and location ID

12. **PUT /api/locations/<id>**
    - Update shared location
    - Accept: message, visibility, expiry_time
    - Require location ownership
    - Return updated location

13. **DELETE /api/locations/<id>**
    - Remove shared location
    - Clean up associated data
    - Return confirmation

### Marker Management Routes

14. **GET /api/markers**
    - Return markers for specific map
    - Accept: map_id, category, bounds
    - Include marker details and metadata
    - Support clustering for performance

15. **POST /api/markers**
    - Create new marker
    - Accept: map_id, latitude, longitude, title, description, category, icon
    - Validate coordinates and permissions
    - Return created marker

16. **PUT /api/markers/<id>**
    - Update marker details
    - Accept: title, description, category, icon, coordinates
    - Require appropriate permissions
    - Return updated marker

17. **DELETE /api/markers/<id>**
    - Delete marker
    - Require appropriate permissions
    - Return confirmation

### Route Management Routes

18. **GET /api/routes**
    - Return routes for specific map
    - Accept: map_id, route_type, bounds
    - Include route waypoints and metadata

19. **POST /api/routes**
    - Create new route
    - Accept: map_id, waypoints, route_type, name, description
    - Calculate route distance and duration
    - Return created route with calculated data

20. **PUT /api/routes/<id>**
    - Update route details
    - Accept: waypoints, name, description, route_type
    - Recalculate route metrics
    - Return updated route

21. **DELETE /api/routes/<id>**
    - Delete route
    - Clean up waypoints and associated data
    - Return confirmation

### Search and Discovery Routes

22. **GET /api/search**
    - Search for locations, places, and addresses
    - Accept: query, bounds, category, limit
    - Use geocoding services and local data
    - Return ranked search results

23. **GET /api/geocode**
    - Convert address to coordinates
    - Accept: address, region, language
    - Use geocoding service integration
    - Return coordinates and formatted address

24. **GET /api/nearby**
    - Find nearby places and points of interest
    - Accept: latitude, longitude, radius, category
    - Search local database and external APIs
    - Return nearby locations with distances

## Database Schema

```sql
Users table:
- id (TEXT PRIMARY KEY)
- username (TEXT UNIQUE NOT NULL)
- email (TEXT UNIQUE NOT NULL)
- password_hash (TEXT NOT NULL)
- default_privacy (TEXT DEFAULT 'private')
- location_sharing_enabled (BOOLEAN DEFAULT FALSE)
- created_at (TIMESTAMP)
- last_location_update (TIMESTAMP)

Maps table:
- id (TEXT PRIMARY KEY)
- name (TEXT NOT NULL)
- description (TEXT)
- creator_id (TEXT)
- privacy_level (TEXT DEFAULT 'private')
- default_center_lat (DECIMAL)
- default_center_lng (DECIMAL)
- default_zoom (INTEGER DEFAULT 10)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- view_count (INTEGER DEFAULT 0)

Shared_Locations table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- map_id (TEXT)
- latitude (DECIMAL NOT NULL)
- longitude (DECIMAL NOT NULL)
- accuracy (DECIMAL)
- message (TEXT)
- visibility (TEXT DEFAULT 'friends')
- expires_at (TIMESTAMP)
- created_at (TIMESTAMP)

Markers table:
- id (TEXT PRIMARY KEY)
- map_id (TEXT)
- creator_id (TEXT)
- latitude (DECIMAL NOT NULL)
- longitude (DECIMAL NOT NULL)
- title (TEXT NOT NULL)
- description (TEXT)
- category (TEXT)
- icon (TEXT)
- color (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

Routes table:
- id (TEXT PRIMARY KEY)
- map_id (TEXT)
- creator_id (TEXT)
- name (TEXT NOT NULL)
- description (TEXT)
- route_type (TEXT) -- 'driving', 'walking', 'cycling'
- total_distance (DECIMAL)
- estimated_duration (INTEGER)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

Route_Waypoints table:
- id (TEXT PRIMARY KEY)
- route_id (TEXT)
- latitude (DECIMAL NOT NULL)
- longitude (DECIMAL NOT NULL)
- waypoint_order (INTEGER)
- waypoint_type (TEXT) -- 'start', 'waypoint', 'end'
- name (TEXT)

Map_Permissions table:
- map_id (TEXT)
- user_id (TEXT)
- permission_level (TEXT) -- 'view', 'edit', 'admin'
- granted_at (TIMESTAMP)
- granted_by (TEXT)

Places_Cache table:
- id (TEXT PRIMARY KEY)
- name (TEXT NOT NULL)
- latitude (DECIMAL NOT NULL)
- longitude (DECIMAL NOT NULL)
- category (TEXT)
- address (TEXT)
- source (TEXT)
- last_updated (TIMESTAMP)
```

## Geographic Processing Features

- **Coordinate validation** and bounds checking
- **Distance calculations** using geodesic formulas
- **Spatial queries** for nearby locations and regions
- **Route optimization** and path finding algorithms
- **Geocoding and reverse geocoding** integration
- **Map projection** and coordinate system handling
- **Geofencing** and boundary detection
- **Clustering algorithms** for marker optimization

## Location Sharing Features

- **Real-time location broadcasting** with privacy controls
- **Temporary location sharing** with automatic expiry
- **Friend-based sharing** with permission management
- **Location history** tracking and retrieval
- **Privacy zones** and location filtering
- **Batch location updates** for efficiency
- **Location accuracy** validation and filtering
- **Anonymous sharing** options for public events

## Route Planning Features

- **Multi-modal routing** (driving, walking, cycling, transit)
- **Waypoint optimization** for efficient routes
- **Alternative route** suggestions and comparison
- **Real-time traffic** integration (if available)
- **Route sharing** and collaborative planning
- **Turn-by-turn directions** generation
- **Route elevation** and difficulty analysis
- **Custom route creation** with manual waypoints

## Search and Discovery Features

- **Full-text search** across locations and places
- **Category-based filtering** with predefined types
- **Proximity search** with radius and bounds
- **Auto-complete** suggestions for search queries
- **Search history** and saved searches
- **Popular places** and trending locations
- **User-generated content** search and discovery
- **Multi-language search** support

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, geopy, geographic processing libraries

3. **Production Ready Features**
   - Comprehensive error handling
   - Geographic data validation and processing
   - Location privacy and security measures
   - Performance optimization for spatial queries
   - Real-time location sharing capabilities
   - Route calculation and optimization
   - Search indexing and geocoding integration
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all map sharing scenarios including location management, route planning, marker creation, geographic search, and real-time sharing with proper validation and privacy controls.