# Frontend Generation Prompt - React Reservation Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (calendar, booking, reservations, profile, confirmation).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**Reservation System Frontend**  
A modern React frontend for reservation application, featuring interactive calendar booking, real-time availability checking, reservation management, and confirmation workflows with intuitive, responsive design.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Interactive calendar with time slot selection
- Real-time availability checking and booking
- Comprehensive reservation management interface
- Booking confirmation and status tracking
- User authentication and profile management
- Mobile-responsive booking interface
- Multi-step booking workflow
- Payment integration interface (mock)

## Frontend Structure (App.jsx)

```jsx
// 1. Imports
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  // - currentView (calendar, booking, reservations, profile, confirmation, auth)
  // - calendar data and selected dates
  // - available time slots
  // - booking form data
  // - user reservations
  // - user authentication state
  // - selected resource and time slot
  // - booking step progress
  // - loading states
  // - error states

  // 4. Refs
  // - calendarRef
  // - bookingFormRef
  // - timeSlotRef
  // - paymentFormRef
  
  // 5. Lifecycle Functions
  // - Load calendar data and availability
  // - Check user authentication
  // - Initialize booking workflow
  // - Setup real-time availability updates
  
  // 6. Event Handlers
  // - handleDateSelect
  // - handleTimeSlotSelect
  // - handleBookingSubmit
  // - handleReservationCancel/Modify
  // - handleAvailabilityCheck
  // - handleAuth (login/register/logout)
  // - handleNavigationStep
  
  // 7. Booking Functions
  // - checkAvailability
  // - createReservation
  // - updateReservation
  // - cancelReservation
  // - processPayment (mock)
  
  // 8. API Calls
  // - getAvailability
  // - getCalendarData
  // - createReservation
  // - getReservations
  // - cancelReservation
  // - getResources
  // - authenticate
  // - getUserProfile
  
  // 9. Utility Functions
  // - formatDate/time
  // - calculateDuration
  // - formatPrice
  // - validateBookingForm
  // - generateTimeSlots
  
  // 10. Render Methods
  // - renderCalendarView()
  // - renderBookingForm()
  // - renderReservationsList()
  // - renderConfirmation()
  // - renderAuthView()
  // - renderTimeSlotSelector()
  // - renderResourceSelector()
  
  return (
    <main className="reservation-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 11. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Calendar View**
   - Interactive monthly/weekly calendar display
   - Date selection with availability indicators
   - Resource filter and selection
   - Quick availability overview
   - Navigation between months/weeks
   - Today/current time highlighting
   - Booking density visualization

2. **Booking Workflow**
   - Multi-step booking process
   - Resource selection with details and pricing
   - Date and time slot selection
   - Customer information form
   - Special requests and preferences
   - Booking summary and review
   - Payment information (mock)
   - Confirmation and booking code display

3. **Time Slot Selection**
   - Visual time slot grid for selected date
   - Real-time availability checking
   - Duration selection options
   - Pricing display per time slot
   - Unavailable slot indicators
   - Quick booking for popular times
   - Alternative date suggestions

4. **Reservations Management**
   - List of user's current and past reservations
   - Reservation details with status
   - Modify/reschedule functionality
   - Cancel with policy display
   - Download/print confirmation
   - Add to calendar options
   - Review and rating system

5. **User Profile and Settings**
   - Personal information management
   - Booking preferences and defaults
   - Notification settings
   - Payment methods (mock)
   - Booking history and statistics
   - Loyalty program status
   - Account security settings

6. **Confirmation and Status**
   - Booking confirmation display
   - QR code for check-in
   - Cancellation policy information
   - Contact information and support
   - Social sharing options
   - Calendar integration buttons

## Calendar Interface Features

```javascript
// Advanced calendar functionality:
const CalendarFeatures = {
  // - Interactive date selection with hover states
  // - Availability color coding (available, busy, blocked)
  // - Multiple view modes (month, week, day)
  // - Quick date navigation and shortcuts
  // - Resource-specific availability display
  // - Booking density indicators
  // - Holiday and special event marking
  // - Mobile-optimized touch interactions
};
```

## Booking Workflow Features

- **Multi-step wizard** with progress indicators
- **Real-time validation** at each step
- **Step-by-step guidance** with helpful tips
- **Save and resume** booking capability
- **Alternative suggestions** for unavailable slots
- **Pricing calculator** with real-time updates
- **Booking summary** with all details
- **Confirmation codes** and receipts

## Time Slot Management Interface

- **Visual time grid** with intuitive selection
- **Duration slider** for flexible booking lengths
- **Availability animations** with smooth transitions
- **Quick selection** for common time slots
- **Time zone display** and conversion
- **Buffer time** visualization between bookings
- **Popular times** highlighting and recommendations

## UI/UX Requirements

- Clean, professional booking interface design
- Mobile-first responsive layout
- Fast booking flows with minimal friction
- Visual feedback for all user interactions
- Loading states for availability checks
- Error handling with helpful suggestions
- Accessibility compliance (ARIA labels, keyboard navigation)
- Touch-friendly interface for mobile booking
- Smooth animations and transitions
- Offline booking capability with sync

## Real-time Features

```javascript
// Real-time booking functionality:
const RealTimeFeatures = {
  // - Live availability updates while browsing
  // - Automatic conflict detection and prevention
  // - Real-time pricing updates
  // - Booking status notifications
  // - Waitlist position updates
  // - Calendar synchronization
  // - Multi-user booking conflict resolution
  // - Instant confirmation and updates
};
```

## Availability and Resource Display

- **Color-coded availability** indicators
- **Resource comparison** with features and pricing
- **Capacity and size** information
- **Photo galleries** for resources
- **360° virtual tours** (if supported)
- **Amenities and features** listing
- **Reviews and ratings** from other users
- **Availability trends** and recommendations

## Booking Management Interface

- **Drag-and-drop rescheduling** in calendar view
- **Bulk operations** for multiple bookings
- **Quick actions** (cancel, modify, extend)
- **Status tracking** with progress indicators
- **Notification preferences** management
- **Automatic reminders** and alerts
- **Conflict resolution** assistance

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// Authentication API functions:
// - login(credentials)
// - register(userData)
// - logout()
// - getCurrentUser()

// Availability API functions:
// - checkAvailability(date, time, resource)
// - getCalendarData(startDate, endDate)
// - getTimeSlots(date, resource)

// Booking API functions:
// - createReservation(bookingData)
// - getReservations(userId)
// - updateReservation(id, updates)
// - cancelReservation(id, reason)
// - confirmReservation(id)

// Resource API functions:
// - getResources(filters)
// - getResourceDetails(id)
// - getResourceAvailability(id, dateRange)
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
    <title>Reservation System</title>
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
   - Include React, Vite, calendar libraries, and any additional libraries needed

3. **Production Ready Features**
   - Comprehensive error handling and recovery
   - Real-time availability updates with optimistic UI
   - Responsive design with mobile optimization
   - Proper state management for booking workflows
   - Performance optimization (lazy loading, caching)
   - Accessibility compliance
   - Clean code with comments
   - User experience enhancements (smooth animations, shortcuts)
   - Progressive Web App features
   - Offline booking with sync capability

**Very important:** Your frontend should be feature rich, production ready, and provide excellent reservation experience with intuitive calendar interface, smooth booking workflow, comprehensive reservation management, and responsive design that works across all devices.