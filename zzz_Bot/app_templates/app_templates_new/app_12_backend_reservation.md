# Backend Generation Prompt - Flask Reservation Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/reservations`, `/api/availability`, `/api/calendar`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**Reservation System Backend**  
A comprehensive Flask backend for reservation application, featuring time slot management, availability checking, booking confirmation, calendar integration, and conflict prevention with automated notifications.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Time slot booking with conflict prevention
- Real-time availability checking and updates
- Complete reservation management (CRUD)
- Calendar view with date-based operations
- Booking confirmation and notification system
- User authentication and profile management
- Cancellation policies and refund handling
- Resource management (rooms, tables, services)
- Waitlist and overbooking management
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
from email.mime.text import MimeText
import smtplib

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'

# 3. Database Models/Setup
# 4. Availability Logic
# 5. Conflict Prevention
# 6. Notification System
# 7. API Routes:
#    - GET /api/availability (check availability for date/time)
#    - GET /api/calendar (get calendar view data)
#    - GET /api/reservations (list reservations with filtering)
#    - GET /api/reservations/<id> (get specific reservation)
#    - POST /api/reservations (create new reservation)
#    - PUT /api/reservations/<id> (update reservation)
#    - DELETE /api/reservations/<id> (cancel reservation)
#    - GET /api/timeslots (get available time slots)
#    - POST /api/timeslots (create time slot template)
#    - GET /api/resources (get bookable resources)
#    - POST /api/resources (create resource)
#    - PUT /api/resources/<id> (update resource)
#    - GET /api/reservations/my (get user's reservations)
#    - POST /api/reservations/<id>/confirm (confirm reservation)
#    - POST /api/reservations/<id>/cancel (cancel with policy)
#    - GET /api/waitlist (get waitlist entries)
#    - POST /api/waitlist (add to waitlist)
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
   - Accept: username, email, password, phone
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
   - Include reservation history and preferences

### Availability and Calendar Routes

5. **GET /api/availability**
   - Check availability for specific date/time/resource
   - Accept: date, time, duration, resource_id
   - Return available slots and conflicts
   - Support bulk availability checking

6. **GET /api/calendar**
   - Return calendar view data for date range
   - Accept: start_date, end_date, resource_id
   - Include reservations, availability, and blocked times
   - Support different view types (day, week, month)

7. **GET /api/timeslots**
   - Return available time slots for booking
   - Accept: date, resource_id, duration
   - Calculate based on business hours and existing bookings
   - Include pricing and availability status

8. **POST /api/timeslots**
   - Create time slot templates for resources
   - Accept: resource_id, start_time, end_time, days_of_week
   - Define recurring availability patterns
   - Return created slot template

### Reservation Management Routes

9. **GET /api/reservations**
   - Return paginated list of reservations
   - Support filtering by date, status, resource, user
   - Support sorting by date, creation time, status
   - Include reservation details and metadata

10. **GET /api/reservations/<id>**
    - Return specific reservation with full details
    - Include customer info, resource details, payment status
    - Show cancellation policies and options

11. **POST /api/reservations**
    - Create new reservation
    - Accept: resource_id, date, time, duration, customer_info
    - Validate availability and prevent conflicts
    - Generate confirmation code
    - Send confirmation notification

12. **PUT /api/reservations/<id>**
    - Update existing reservation
    - Accept: date, time, duration, special_requests
    - Check new slot availability
    - Handle rescheduling policies
    - Send update notifications

13. **DELETE /api/reservations/<id>**
    - Cancel reservation
    - Apply cancellation policies
    - Calculate refunds if applicable
    - Update availability
    - Send cancellation notification

14. **GET /api/reservations/my**
    - Return current user's reservations
    - Include upcoming and past bookings
    - Show cancellation and modification options

### Confirmation and Status Routes

15. **POST /api/reservations/<id>/confirm**
    - Confirm reservation (if pending)
    - Update status and send confirmation
    - Process payment if required
    - Return confirmation details

16. **POST /api/reservations/<id>/cancel**
    - Cancel reservation with policy application
    - Accept: reason, refund_request
    - Calculate cancellation fees
    - Update waitlist if applicable

### Resource Management Routes

17. **GET /api/resources**
    - Return list of bookable resources
    - Include availability schedules and pricing
    - Support filtering by type, capacity, features

18. **POST /api/resources**
    - Create new bookable resource
    - Accept: name, type, capacity, description, pricing
    - Set availability schedules
    - Return created resource

19. **PUT /api/resources/<id>**
    - Update resource details
    - Accept: name, capacity, pricing, availability
    - Handle existing reservations
    - Return updated resource

### Waitlist Management Routes

20. **GET /api/waitlist**
    - Return waitlist entries for date/resource
    - Include customer priority and contact info
    - Support waitlist management

21. **POST /api/waitlist**
    - Add customer to waitlist
    - Accept: resource_id, preferred_date, contact_info
    - Set priority based on signup time
    - Send waitlist confirmation

## Database Schema

```sql
Users table:
- id (TEXT PRIMARY KEY)
- username (TEXT UNIQUE NOT NULL)
- email (TEXT UNIQUE NOT NULL)
- password_hash (TEXT NOT NULL)
- phone (TEXT)
- first_name (TEXT)
- last_name (TEXT)
- created_at (TIMESTAMP)
- total_reservations (INTEGER DEFAULT 0)
- cancellation_count (INTEGER DEFAULT 0)

Resources table:
- id (TEXT PRIMARY KEY)
- name (TEXT NOT NULL)
- type (TEXT) -- 'room', 'table', 'service', etc.
- capacity (INTEGER)
- description (TEXT)
- hourly_rate (DECIMAL)
- is_active (BOOLEAN DEFAULT TRUE)
- created_at (TIMESTAMP)

Reservations table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- resource_id (TEXT)
- start_datetime (TIMESTAMP)
- end_datetime (TIMESTAMP)
- status (TEXT) -- 'pending', 'confirmed', 'cancelled', 'completed'
- confirmation_code (TEXT UNIQUE)
- customer_name (TEXT)
- customer_email (TEXT)
- customer_phone (TEXT)
- special_requests (TEXT)
- total_cost (DECIMAL)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

Time_Slots table:
- id (TEXT PRIMARY KEY)
- resource_id (TEXT)
- day_of_week (INTEGER) -- 0-6 (Monday-Sunday)
- start_time (TIME)
- end_time (TIME)
- is_available (BOOLEAN DEFAULT TRUE)
- max_duration (INTEGER) -- minutes
- created_at (TIMESTAMP)

Availability_Overrides table:
- id (TEXT PRIMARY KEY)
- resource_id (TEXT)
- override_date (DATE)
- start_time (TIME)
- end_time (TIME)
- is_available (BOOLEAN)
- reason (TEXT)
- created_at (TIMESTAMP)

Waitlist table:
- id (TEXT PRIMARY KEY)
- resource_id (TEXT)
- customer_email (TEXT)
- customer_phone (TEXT)
- preferred_date (DATE)
- preferred_time (TIME)
- party_size (INTEGER)
- priority (INTEGER)
- status (TEXT) -- 'waiting', 'contacted', 'booked', 'expired'
- created_at (TIMESTAMP)

Cancellation_Policies table:
- id (INTEGER PRIMARY KEY)
- resource_id (TEXT)
- hours_before (INTEGER)
- refund_percentage (DECIMAL)
- fee_amount (DECIMAL)
- created_at (TIMESTAMP)
```

## Reservation Management Features

- **Real-time availability** checking with conflict prevention
- **Flexible time slot** management with business hour constraints
- **Automated confirmation** with unique booking codes
- **Cancellation policies** with automated fee calculation
- **Waitlist management** with automatic notifications
- **Overbooking protection** with validation rules
- **Resource scheduling** with capacity management
- **Multi-resource booking** support

## Conflict Prevention and Validation

- **Double-booking prevention** with database constraints
- **Availability validation** before reservation creation
- **Time overlap detection** and resolution
- **Resource capacity** checking and management
- **Business hours** validation and enforcement
- **Advance booking limits** and restrictions
- **Minimum/maximum duration** enforcement

## Notification System Features

- **Email confirmations** for new bookings
- **SMS notifications** for important updates
- **Reminder notifications** before appointments
- **Cancellation confirmations** with refund details
- **Waitlist notifications** when slots become available
- **Rescheduling confirmations** for changes
- **Custom notification** templates

## Calendar and Scheduling Features

- **Multi-view calendar** support (day, week, month)
- **Recurring availability** patterns
- **Holiday and closure** management
- **Special event** scheduling
- **Resource allocation** optimization
- **Time zone** support for global bookings
- **Bulk operations** for schedule management

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, datetime handling, email libraries

3. **Production Ready Features**
   - Comprehensive error handling
   - Availability validation and conflict prevention
   - Automated notification system
   - Cancellation policy enforcement
   - Resource management and optimization
   - Performance optimization for calendar operations
   - Audit logging for all booking activities
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all reservation scenarios including booking management, availability checking, conflict prevention, and automated notifications with proper validation and business rule enforcement.