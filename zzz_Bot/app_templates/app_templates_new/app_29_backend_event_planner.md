# Backend Generation Prompt - Flask Event Planning Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/events`, `/api/guests`, `/api/budget`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**Event Planning System Backend**  
A comprehensive Flask backend for event planning application, featuring event management, guest coordination, budget tracking, vendor management, RSVP handling, and collaborative planning tools with automated notifications and timeline management.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Complete event creation and management system
- Guest list tracking with RSVP management
- Budget planning and expense tracking
- Vendor coordination and management
- Invitation generation and distribution
- Event timeline and milestone planning
- Collaborative planning with team management
- Real-time notifications and updates
- Document and checklist management
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
from decimal import Decimal
import smtplib
from email.mime.text import MimeText

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'

# 3. Database Models/Setup
# 4. Event Planning Logic
# 5. Budget Calculation
# 6. RSVP Management
# 7. API Routes:
#    - GET /api/events (list events with filtering)
#    - GET /api/events/<id> (get specific event)
#    - POST /api/events (create new event)
#    - PUT /api/events/<id> (update event)
#    - DELETE /api/events/<id> (delete event)
#    - GET /api/events/<id>/guests (get guest list)
#    - POST /api/events/<id>/guests (add guests)
#    - PUT /api/guests/<id> (update guest info)
#    - DELETE /api/guests/<id> (remove guest)
#    - POST /api/guests/<id>/rsvp (record RSVP)
#    - GET /api/events/<id>/budget (get budget details)
#    - POST /api/events/<id>/budget/items (add budget item)
#    - PUT /api/budget/items/<id> (update budget item)
#    - DELETE /api/budget/items/<id> (delete budget item)
#    - GET /api/events/<id>/vendors (get vendors)
#    - POST /api/events/<id>/vendors (add vendor)
#    - PUT /api/vendors/<id> (update vendor)
#    - DELETE /api/vendors/<id> (remove vendor)
#    - GET /api/events/<id>/timeline (get timeline)
#    - POST /api/events/<id>/timeline (add milestone)
#    - PUT /api/timeline/<id> (update milestone)
#    - GET /api/events/<id>/invitations (get invitations)
#    - POST /api/events/<id>/invitations (send invitations)
#    - GET /api/events/<id>/team (get planning team)
#    - POST /api/events/<id>/team (add team member)
#    - GET /api/events/<id>/checklist (get checklist)
#    - POST /api/events/<id>/checklist (add checklist item)
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
   - Accept: username, email, password, full_name
   - Validate input and create user account
   - Hash password securely
   - Return user info and session

2. **POST /api/auth/login**
   - Accept: username/email, password
   - Validate credentials
   - Create user session
   - Return user info

3. **POST /api/auth/logout**
   - Clear user session
   - Return success response

4. **GET /api/auth/user**
   - Return current authenticated user info
   - Include user stats (events created, events attended)

### Event Management Routes

5. **GET /api/events**
   - Return paginated list of events
   - Support filtering by date, status, type, organizer
   - Support sorting by date, name, guest count
   - Include event metadata and statistics

6. **GET /api/events/<id>**
   - Return specific event with full details
   - Include guest count, budget summary, timeline status
   - Show user permissions and access level

7. **POST /api/events**
   - Create new event
   - Accept: name, description, date, time, location, type, capacity
   - Require authentication
   - Initialize default budget and timeline
   - Return created event

8. **PUT /api/events/<id>**
   - Update existing event
   - Require authentication and ownership/permission
   - Handle date changes and notification to guests
   - Return updated event

9. **DELETE /api/events/<id>**
   - Delete event
   - Require authentication and ownership
   - Handle guest notifications and cleanup
   - Return confirmation

### Guest Management Routes

10. **GET /api/events/<id>/guests**
    - Return guest list for event
    - Include RSVP status and contact info
    - Support filtering by RSVP status
    - Show dietary restrictions and special needs

11. **POST /api/events/<id>/guests**
    - Add guests to event
    - Accept: guest_list with emails and names
    - Generate invitation codes
    - Send invitation emails
    - Return added guests

12. **PUT /api/guests/<id>**
    - Update guest information
    - Accept: name, email, dietary_restrictions, plus_one
    - Return updated guest info

13. **DELETE /api/guests/<id>**
    - Remove guest from event
    - Send notification if already invited
    - Return confirmation

14. **POST /api/guests/<id>/rsvp**
    - Record guest RSVP response
    - Accept: status (attending, not_attending, maybe), plus_one_count
    - Update event attendance numbers
    - Send confirmation to guest

### Budget Management Routes

15. **GET /api/events/<id>/budget**
    - Return budget breakdown for event
    - Include categories, items, costs, payments
    - Calculate totals and remaining budget

16. **POST /api/events/<id>/budget/items**
    - Add budget item
    - Accept: category, description, estimated_cost, vendor
    - Return created budget item

17. **PUT /api/budget/items/<id>**
    - Update budget item
    - Accept: description, estimated_cost, actual_cost, paid
    - Return updated item

18. **DELETE /api/budget/items/<id>**
    - Delete budget item
    - Update budget totals
    - Return confirmation

### Vendor Management Routes

19. **GET /api/events/<id>/vendors**
    - Return vendor list for event
    - Include contact info, services, costs, status

20. **POST /api/events/<id>/vendors**
    - Add vendor to event
    - Accept: name, contact_info, service_type, cost, notes
    - Return created vendor

21. **PUT /api/vendors/<id>**
    - Update vendor information
    - Accept: contact_info, cost, status, notes
    - Return updated vendor

22. **DELETE /api/vendors/<id>**
    - Remove vendor from event
    - Return confirmation

### Timeline and Planning Routes

23. **GET /api/events/<id>/timeline**
    - Return event timeline with milestones
    - Include deadlines, completed tasks, responsible parties
    - Show critical path and dependencies

24. **POST /api/events/<id>/timeline**
    - Add milestone or task to timeline
    - Accept: title, description, due_date, assigned_to, priority
    - Return created timeline item

25. **PUT /api/timeline/<id>**
    - Update timeline item
    - Accept: status, notes, completion_date
    - Return updated item

### Invitation and Communication Routes

26. **GET /api/events/<id>/invitations**
    - Return invitation history and status
    - Include sent dates, open rates, response rates

27. **POST /api/events/<id>/invitations**
    - Send invitations to guests
    - Accept: guest_ids, invitation_template, send_date
    - Generate unique invitation links
    - Return sending confirmation

### Team Collaboration Routes

28. **GET /api/events/<id>/team**
    - Return planning team members
    - Include roles, permissions, contact info

29. **POST /api/events/<id>/team**
    - Add team member to event planning
    - Accept: user_id, role, permissions
    - Send invitation to collaborate
    - Return team member info

### Checklist Management Routes

30. **GET /api/events/<id>/checklist**
    - Return event planning checklist
    - Include categories, items, completion status

31. **POST /api/events/<id>/checklist**
    - Add checklist item
    - Accept: category, task, due_date, assigned_to
    - Return created item

## Database Schema

```sql
Users table:
- id (TEXT PRIMARY KEY)
- username (TEXT UNIQUE NOT NULL)
- email (TEXT UNIQUE NOT NULL)
- password_hash (TEXT NOT NULL)
- full_name (TEXT)
- phone (TEXT)
- created_at (TIMESTAMP)
- events_created (INTEGER DEFAULT 0)
- events_attended (INTEGER DEFAULT 0)

Events table:
- id (TEXT PRIMARY KEY)
- organizer_id (TEXT)
- name (TEXT NOT NULL)
- description (TEXT)
- event_type (TEXT)
- event_date (TIMESTAMP)
- location_name (TEXT)
- location_address (TEXT)
- capacity (INTEGER)
- status (TEXT) -- 'planning', 'confirmed', 'completed', 'cancelled'
- budget_total (DECIMAL)
- guest_count (INTEGER DEFAULT 0)
- rsvp_yes (INTEGER DEFAULT 0)
- rsvp_no (INTEGER DEFAULT 0)
- rsvp_maybe (INTEGER DEFAULT 0)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

Guests table:
- id (TEXT PRIMARY KEY)
- event_id (TEXT)
- name (TEXT NOT NULL)
- email (TEXT)
- phone (TEXT)
- rsvp_status (TEXT) -- 'pending', 'yes', 'no', 'maybe'
- plus_one_count (INTEGER DEFAULT 0)
- dietary_restrictions (TEXT)
- special_needs (TEXT)
- invitation_sent (BOOLEAN DEFAULT FALSE)
- invitation_opened (BOOLEAN DEFAULT FALSE)
- rsvp_date (TIMESTAMP)
- created_at (TIMESTAMP)

Budget_Items table:
- id (TEXT PRIMARY KEY)
- event_id (TEXT)
- category (TEXT) -- 'venue', 'catering', 'entertainment', etc.
- description (TEXT NOT NULL)
- estimated_cost (DECIMAL)
- actual_cost (DECIMAL)
- vendor_id (TEXT)
- payment_status (TEXT) -- 'unpaid', 'partial', 'paid'
- created_at (TIMESTAMP)

Vendors table:
- id (TEXT PRIMARY KEY)
- event_id (TEXT)
- name (TEXT NOT NULL)
- service_type (TEXT)
- contact_person (TEXT)
- email (TEXT)
- phone (TEXT)
- cost (DECIMAL)
- status (TEXT) -- 'contacted', 'quoted', 'booked', 'confirmed'
- notes (TEXT)
- created_at (TIMESTAMP)

Timeline_Items table:
- id (TEXT PRIMARY KEY)
- event_id (TEXT)
- title (TEXT NOT NULL)
- description (TEXT)
- due_date (TIMESTAMP)
- assigned_to (TEXT)
- priority (TEXT) -- 'low', 'medium', 'high', 'critical'
- status (TEXT) -- 'pending', 'in_progress', 'completed'
- completion_date (TIMESTAMP)
- created_at (TIMESTAMP)

Team_Members table:
- id (TEXT PRIMARY KEY)
- event_id (TEXT)
- user_id (TEXT)
- role (TEXT) -- 'organizer', 'coordinator', 'assistant'
- permissions (TEXT) -- JSON object
- invited_at (TIMESTAMP)
- joined_at (TIMESTAMP)

Checklist_Items table:
- id (TEXT PRIMARY KEY)
- event_id (TEXT)
- category (TEXT)
- task (TEXT NOT NULL)
- due_date (TIMESTAMP)
- assigned_to (TEXT)
- completed (BOOLEAN DEFAULT FALSE)
- completed_date (TIMESTAMP)
- created_at (TIMESTAMP)
```

## Event Planning Features

- **Comprehensive event lifecycle** management from planning to completion
- **Guest management** with automated RSVP tracking
- **Budget tracking** with expense categorization and vendor integration
- **Timeline management** with milestone tracking and deadlines
- **Collaborative planning** with team roles and permissions
- **Automated notifications** for deadlines, RSVPs, and updates
- **Vendor coordination** with status tracking and communications
- **Checklist management** with task assignment and completion tracking

## RSVP and Communication Features

- **Automated invitation** generation and distribution
- **RSVP tracking** with real-time updates
- **Guest communication** tools and templates
- **Reminder systems** for important deadlines
- **Event updates** and change notifications
- **Dietary restriction** and special needs tracking
- **Plus-one management** with guest count tracking

## Budget and Financial Management

- **Comprehensive budget** planning with categories
- **Vendor cost tracking** and payment status
- **Expense monitoring** with actual vs. estimated costs
- **Payment tracking** and scheduling
- **Budget alerts** for overspending
- **Financial reporting** with cost breakdowns
- **Multi-currency support** for international events

## Collaboration and Team Management

- **Role-based access** control for team members
- **Task assignment** and responsibility tracking
- **Progress monitoring** with completion status
- **Communication tools** for team coordination
- **Document sharing** and version control
- **Permission management** for different access levels

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, email handling, datetime libraries

3. **Production Ready Features**
   - Comprehensive error handling
   - Input validation and sanitization
   - Event workflow management
   - Automated notification system
   - Budget calculation accuracy
   - Team collaboration features
   - Performance optimization for large events
   - Audit logging for all planning activities
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all event planning scenarios including event management, guest coordination, budget tracking, vendor management, and team collaboration with proper validation and automated workflow management.