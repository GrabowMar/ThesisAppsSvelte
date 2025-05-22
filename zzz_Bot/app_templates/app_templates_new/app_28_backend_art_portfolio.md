# Backend Generation Prompt - Flask Art Portfolio Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/artworks`, `/api/galleries`, `/api/profiles`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**Art Portfolio Management System Backend**  
A comprehensive Flask backend for art portfolio application, featuring artwork upload and management, gallery creation, portfolio customization, artist profile management, social sharing capabilities, art categorization, and exhibition/commission tracking with advanced art showcase and networking features.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Comprehensive artwork upload and management system
- Gallery creation and curation tools
- Portfolio customization and theming options
- Artist profile creation and management
- Social sharing and networking capabilities
- Advanced art categorization and tagging
- Exhibition and commission tracking systems
- User authentication with artist-specific features
- Image processing and optimization for artworks
- Search and discovery algorithms for art
- CORS support for frontend communication
- Database integration (SQLite or in-memory for simplicity)

## Backend Structure (app.py)

```python
# 1. Imports Section
from flask import Flask, jsonify, request, session, send_file
from flask_cors import CORS
import os
import sqlite3
from datetime import datetime, timedelta
import uuid
import json
from PIL import Image, ImageOps
import magic
from werkzeug.utils import secure_filename
import hashlib

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['THUMBNAIL_FOLDER'] = 'thumbnails'

# 3. Database Models/Setup
# 4. Image Processing Logic
# 5. Portfolio Management
# 6. Social Features
# 7. API Routes:
#    - POST /api/auth/register (artist registration)
#    - POST /api/auth/login (artist login)
#    - POST /api/auth/logout (artist logout)
#    - GET /api/auth/user (get current artist)
#    - GET /api/artists/<id> (get artist profile)
#    - PUT /api/artists/<id> (update artist profile)
#    - POST /api/artworks/upload (upload artwork)
#    - GET /api/artworks (get artworks with filtering)
#    - GET /api/artworks/<id> (get specific artwork)
#    - PUT /api/artworks/<id> (update artwork details)
#    - DELETE /api/artworks/<id> (delete artwork)
#    - GET /api/artworks/<id>/image (serve artwork image)
#    - GET /api/artworks/<id>/thumbnail (serve thumbnail)
#    - GET /api/galleries (get galleries)
#    - POST /api/galleries (create gallery)
#    - GET /api/galleries/<id> (get gallery details)
#    - PUT /api/galleries/<id> (update gallery)
#    - DELETE /api/galleries/<id> (delete gallery)
#    - POST /api/galleries/<id>/artworks (add artwork to gallery)
#    - DELETE /api/galleries/<id>/artworks/<artwork_id> (remove from gallery)
#    - GET /api/categories (get art categories)
#    - POST /api/categories (create category)
#    - GET /api/tags (get available tags)
#    - POST /api/artworks/<id>/like (like/unlike artwork)
#    - GET /api/artworks/<id>/likes (get artwork likes)
#    - POST /api/artworks/<id>/comment (comment on artwork)
#    - GET /api/artworks/<id>/comments (get artwork comments)
#    - GET /api/exhibitions (get exhibitions)
#    - POST /api/exhibitions (create exhibition)
#    - POST /api/exhibitions/<id>/submit (submit artwork to exhibition)
#    - GET /api/commissions (get commission requests)
#    - POST /api/commissions (create commission request)
#    - PUT /api/commissions/<id> (update commission status)
#    - GET /api/search (search artworks and artists)
#    - GET /api/featured (get featured artworks)
#    - POST /api/follow/<artist_id> (follow/unfollow artist)
#    - GET /api/feed (get personalized art feed)
# 8. Error Handlers

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'YYYY')))
```

## Required API Endpoints

### Authentication Routes

1. **POST /api/auth/register**
   - Accept: username, email, password, artist_name, bio, location
   - Validate input and create artist account
   - Hash password securely
   - Initialize artist profile and portfolio
   - Return user info and session

2. **POST /api/auth/login**
   - Accept: username/email, password
   - Validate credentials
   - Create user session
   - Return user info and portfolio status

3. **POST /api/auth/logout**
   - Clear user session
   - Return success response

4. **GET /api/auth/user**
   - Return current authenticated artist info
   - Include portfolio statistics and preferences

### Artist Profile Routes

5. **GET /api/artists/<id>**
   - Return artist profile with portfolio overview
   - Include bio, location, specialties, social links
   - Show featured artworks and gallery previews

6. **PUT /api/artists/<id>**
   - Update artist profile information
   - Accept: bio, location, specialties, contact_info, social_links
   - Require authentication and ownership
   - Return updated profile

### Artwork Management Routes

7. **POST /api/artworks/upload**
   - Upload artwork with metadata
   - Accept: image_file, title, description, medium, dimensions, price
   - Process image and generate thumbnails
   - Extract EXIF data and validate format
   - Return uploaded artwork details

8. **GET /api/artworks**
   - Return artworks with filtering and pagination
   - Support filtering by artist, category, medium, price range
   - Support sorting by date, popularity, price
   - Include thumbnail URLs and metadata

9. **GET /api/artworks/<id>**
   - Return specific artwork with full details
   - Include artist info, creation details, exhibition history
   - Track artwork views and engagement

10. **PUT /api/artworks/<id>**
    - Update artwork metadata
    - Accept: title, description, medium, price, availability
    - Require authentication and ownership
    - Return updated artwork

11. **DELETE /api/artworks/<id>**
    - Delete artwork and associated files
    - Require authentication and ownership
    - Clean up thumbnails and gallery associations
    - Return confirmation

12. **GET /api/artworks/<id>/image**
    - Serve full-resolution artwork image
    - Support different size parameters
    - Implement watermarking options
    - Track image views

13. **GET /api/artworks/<id>/thumbnail**
    - Serve thumbnail version of artwork
    - Multiple size options available
    - Optimized for web display

### Gallery Management Routes

14. **GET /api/galleries**
    - Return artist's galleries
    - Include gallery previews and artwork counts
    - Support public/private gallery filtering

15. **POST /api/galleries**
    - Create new gallery/collection
    - Accept: name, description, theme, visibility
    - Return created gallery

16. **GET /api/galleries/<id>**
    - Return gallery with artwork list
    - Include gallery metadata and statistics
    - Support pagination for large galleries

17. **PUT /api/galleries/<id>**
    - Update gallery details
    - Accept: name, description, theme, visibility
    - Return updated gallery

18. **DELETE /api/galleries/<id>**
    - Delete gallery (not artworks)
    - Return confirmation

19. **POST /api/galleries/<id>/artworks**
    - Add artwork to gallery
    - Accept: artwork_id, position
    - Return updated gallery

20. **DELETE /api/galleries/<id>/artworks/<artwork_id>**
    - Remove artwork from gallery
    - Return confirmation

### Categorization Routes

21. **GET /api/categories**
    - Return art categories and mediums
    - Include usage counts and descriptions

22. **POST /api/categories**
    - Create new art category
    - Accept: name, description, parent_category
    - Return created category

23. **GET /api/tags**
    - Return popular and trending tags
    - Include usage statistics

### Social Interaction Routes

24. **POST /api/artworks/<id>/like**
    - Like or unlike artwork
    - Require authentication
    - Update like count
    - Return like status

25. **GET /api/artworks/<id>/likes**
    - Return users who liked artwork
    - Include like count and recent likes

26. **POST /api/artworks/<id>/comment**
    - Add comment to artwork
    - Accept: comment_text
    - Require authentication
    - Return created comment

27. **GET /api/artworks/<id>/comments**
    - Return artwork comments
    - Support pagination and threading
    - Include commenter profiles

### Exhibition and Commission Routes

28. **GET /api/exhibitions**
    - Return available exhibitions and calls for entry
    - Include submission deadlines and requirements

29. **POST /api/exhibitions**
    - Create exhibition or call for entry
    - Accept: title, description, deadline, requirements
    - Return created exhibition

30. **POST /api/exhibitions/<id>/submit**
    - Submit artwork to exhibition
    - Accept: artwork_ids, artist_statement
    - Return submission confirmation

31. **GET /api/commissions**
    - Return commission requests for artist
    - Include client details and requirements

32. **POST /api/commissions**
    - Create commission request
    - Accept: artist_id, description, budget, deadline
    - Return commission request

33. **PUT /api/commissions/<id>**
    - Update commission status
    - Accept: status, progress_notes, completion_date
    - Return updated commission

### Discovery and Social Routes

34. **GET /api/search**
    - Search artworks and artists
    - Accept: query, filters (medium, price, location)
    - Return ranked search results

35. **GET /api/featured**
    - Return featured artworks and artists
    - Use curation algorithm and trending analysis

36. **POST /api/follow/<artist_id>**
    - Follow or unfollow artist
    - Update follower counts
    - Return follow status

37. **GET /api/feed**
    - Return personalized art feed
    - Include followed artists' new works
    - Use recommendation algorithm

## Database Schema

```sql
Artists table:
- id (TEXT PRIMARY KEY)
- username (TEXT UNIQUE NOT NULL)
- email (TEXT UNIQUE NOT NULL)
- password_hash (TEXT NOT NULL)
- artist_name (TEXT NOT NULL)
- bio (TEXT)
- location (TEXT)
- specialties (TEXT) -- JSON array
- social_links (TEXT) -- JSON object
- contact_info (TEXT)
- profile_image_url (TEXT)
- created_at (TIMESTAMP)
- follower_count (INTEGER DEFAULT 0)
- following_count (INTEGER DEFAULT 0)
- artwork_count (INTEGER DEFAULT 0)

Artworks table:
- id (TEXT PRIMARY KEY)
- artist_id (TEXT)
- title (TEXT NOT NULL)
- description (TEXT)
- medium (TEXT)
- dimensions (TEXT)
- creation_date (DATE)
- image_path (TEXT)
- thumbnail_path (TEXT)
- file_size (INTEGER)
- image_width (INTEGER)
- image_height (INTEGER)
- price (DECIMAL)
- currency (TEXT DEFAULT 'USD')
- availability_status (TEXT) -- 'available', 'sold', 'exhibition', 'private'
- view_count (INTEGER DEFAULT 0)
- like_count (INTEGER DEFAULT 0)
- comment_count (INTEGER DEFAULT 0)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

Galleries table:
- id (TEXT PRIMARY KEY)
- artist_id (TEXT)
- name (TEXT NOT NULL)
- description (TEXT)
- theme (TEXT)
- visibility (TEXT) -- 'public', 'private', 'unlisted'
- cover_artwork_id (TEXT)
- artwork_count (INTEGER DEFAULT 0)
- view_count (INTEGER DEFAULT 0)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

Gallery_Artworks table:
- gallery_id (TEXT)
- artwork_id (TEXT)
- position (INTEGER)
- added_at (TIMESTAMP)
- PRIMARY KEY (gallery_id, artwork_id)

Categories table:
- id (INTEGER PRIMARY KEY)
- name (TEXT UNIQUE NOT NULL)
- description (TEXT)
- parent_id (INTEGER)
- artwork_count (INTEGER DEFAULT 0)

Tags table:
- id (INTEGER PRIMARY KEY)
- name (TEXT UNIQUE NOT NULL)
- usage_count (INTEGER DEFAULT 0)

Artwork_Tags table:
- artwork_id (TEXT)
- tag_id (INTEGER)
- PRIMARY KEY (artwork_id, tag_id)

Artwork_Likes table:
- artwork_id (TEXT)
- user_id (TEXT)
- liked_at (TIMESTAMP)
- PRIMARY KEY (artwork_id, user_id)

Artwork_Comments table:
- id (TEXT PRIMARY KEY)
- artwork_id (TEXT)
- commenter_id (TEXT)
- comment_text (TEXT NOT NULL)
- parent_comment_id (TEXT)
- created_at (TIMESTAMP)

Artist_Follows table:
- follower_id (TEXT)
- following_id (TEXT)
- followed_at (TIMESTAMP)
- PRIMARY KEY (follower_id, following_id)

Exhibitions table:
- id (TEXT PRIMARY KEY)
- organizer_id (TEXT)
- title (TEXT NOT NULL)
- description (TEXT)
- submission_deadline (DATE)
- exhibition_start (DATE)
- exhibition_end (DATE)
- location (TEXT)
- requirements (TEXT)
- submission_fee (DECIMAL)
- created_at (TIMESTAMP)

Exhibition_Submissions table:
- id (TEXT PRIMARY KEY)
- exhibition_id (TEXT)
- artist_id (TEXT)
- artwork_ids (TEXT) -- JSON array
- artist_statement (TEXT)
- status (TEXT) -- 'submitted', 'accepted', 'rejected'
- submitted_at (TIMESTAMP)

Commissions table:
- id (TEXT PRIMARY KEY)
- client_id (TEXT)
- artist_id (TEXT)
- title (TEXT)
- description (TEXT)
- budget (DECIMAL)
- deadline (DATE)
- status (TEXT) -- 'requested', 'accepted', 'in_progress', 'completed', 'cancelled'
- progress_notes (TEXT)
- completion_date (DATE)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

## Art Portfolio Features

- **High-quality image processing** with multiple format support and optimization
- **Advanced portfolio customization** with themes, layouts, and branding options
- **Professional presentation** tools with virtual exhibition capabilities
- **Copyright protection** with watermarking and usage tracking
- **Sales integration** with pricing, availability, and commission management
- **Exhibition management** with submission tracking and portfolio preparation
- **Professional networking** with artist-to-artist and artist-to-collector connections
- **Analytics and insights** for portfolio performance and audience engagement

## Image Processing Features

- **Multi-format support** for various image types and sizes
- **Automatic optimization** with compression and format conversion
- **Thumbnail generation** in multiple sizes for different display contexts
- **Watermark application** for copyright protection
- **EXIF data extraction** for artwork metadata and authenticity
- **Color analysis** for automatic tagging and categorization
- **Quality assessment** with technical image analysis
- **Batch processing** for multiple artwork uploads

## Social and Networking Features

- **Artist discovery** with recommendation algorithms and trending analysis
- **Social interactions** with likes, comments, and shares
- **Following system** with personalized feeds and notifications
- **Collaboration tools** with artist networking and project coordination
- **Community features** with groups, challenges, and exhibitions
- **Mentorship programs** with experienced artist guidance
- **Peer feedback** systems with constructive critique and support
- **Cross-promotion** tools for mutual artist support

## Exhibition and Sales Features

- **Exhibition submission** management with tracking and status updates
- **Virtual exhibitions** with online gallery creation and management
- **Commission tracking** with client communication and project management
- **Sales analytics** with pricing insights and market trends
- **Collector relationships** with client management and repeat business
- **Print-on-demand** integration with product creation and fulfillment
- **Licensing management** with usage rights and royalty tracking
- **Portfolio sharing** with professional presentation tools

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, Pillow, image processing, social media libraries

3. **Production Ready Features**
   - Comprehensive error handling
   - Image processing and optimization
   - Portfolio management and customization
   - Social networking and discovery features
   - Exhibition and commission tracking
   - Performance optimization for image serving
   - Copyright protection and watermarking
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all art portfolio scenarios including artwork management, gallery curation, social networking, exhibition participation, and commission tracking with proper image processing and artist-focused features.