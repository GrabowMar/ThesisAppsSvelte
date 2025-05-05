import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

function App() {
  const [currentPage, setCurrentPage] = useState('login');
  const [user, setUser] = useState(null);
  const [events, setEvents] = useState([]);
  const [currentEvent, setCurrentEvent] = useState(null);
  
  // Authentication state
  const [authData, setAuthData] = useState({
    email: '',
    password: '',
    name: ''
  });
  
  // Event form state
  const [eventForm, setEventForm] = useState({
    title: '',
    description: '',
    start_date: '',
    end_date: '',
    location: ''
  });
  
  // Check if user is logged in on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await fetch('/api/events', {
          credentials: 'include'
        });
        
        if (response.ok) {
          const data = await response.json();
          setEvents(data);
          setCurrentPage('dashboard');
        }
      } catch (error) {
        console.error('Auth check failed:', error);
      }
    };
    
    checkAuth();
  }, []);
  
  // Authentication handlers
  const handleAuthChange = (e) => {
    const { name, value } = e.target;
    setAuthData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(authData),
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setCurrentPage('dashboard');
        // Fetch events after registration
        fetchEvents();
      } else {
        alert('Registration failed');
      }
    } catch (error) {
      console.error('Registration error:', error);
    }
  };
  
  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: authData.email,
          password: authData.password
        }),
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setCurrentPage('dashboard');
        // Fetch events after login
        fetchEvents();
      } else {
        alert('Login failed');
      }
    } catch (error) {
      console.error('Login error:', error);
    }
  };
  
  const handleLogout = async () => {
    try {
      await fetch('/api/logout', {
        method: 'POST',
        credentials: 'include'
      });
      setUser(null);
      setEvents([]);
      setCurrentPage('login');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };
  
  // Event handlers
  const handleEventChange = (e) => {
    const { name, value } = e.target;
    setEventForm(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const fetchEvents = async () => {
    try {
      const response = await fetch('/api/events', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setEvents(data);
      }
    } catch (error) {
      console.error('Failed to fetch events:', error);
    }
  };
  
  const handleCreateEvent = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/events', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(eventForm),
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setEventForm({
          title: '',
          description: '',
          start_date: '',
          end_date: '',
          location: ''
        });
        setCurrentPage('dashboard');
        fetchEvents();
      }
    } catch (error) {
      console.error('Failed to create event:', error);
    }
  };
  
  const viewEventDetails = (event) => {
    setCurrentEvent(event);
    setCurrentPage('event-detail');
  };
  
  const deleteEvent = async (eventId) => {
    try {
      const response = await fetch(`/api/events/${eventId}`, {
        method: 'DELETE',
        credentials: 'include'
      });
      
      if (response.ok) {
        fetchEvents();
        setCurrentPage('dashboard');
      }
    } catch (error) {
      console.error('Failed to delete event:', error);
    }
  };
  
  // Render login page
  const renderLogin = () => (
    <div className="auth-container">
      <h2>Login</h2>
      <form onSubmit={handleLogin}>
        <div className="form-group">
          <label>Email:</label>
          <input 
            type="email" 
            name="email" 
            value={authData.email} 
            onChange={handleAuthChange} 
            required 
          />
        </div>
        <div className="form-group">
          <label>Password:</label>
          <input 
            type="password" 
            name="password" 
            value={authData.password} 
            onChange={handleAuthChange} 
            required 
          />
        </div>
        <button type="submit">Login</button>
      </form>
      <p>
        Don't have an account? 
        <button className="link-button" onClick={() => setCurrentPage('register')}>
          Register
        </button>
      </p>
    </div>
  );
  
  // Render registration page
  const renderRegister = () => (
    <div className="auth-container">
      <h2>Register</h2>
      <form onSubmit={handleRegister}>
        <div className="form-group">
          <label>Name:</label>
          <input 
            type="text" 
            name="name" 
            value={authData.name} 
            onChange={handleAuthChange} 
            required 
          />
        </div>
        <div className="form-group">
          <label>Email:</label>
          <input 
            type="email" 
            name="email" 
            value={authData.email} 
            onChange={handleAuthChange} 
            required 
          />
        </div>
        <div className="form-group">
          <label>Password:</label>
          <input 
            type="password" 
            name="password" 
            value={authData.password} 
            onChange={handleAuthChange} 
            required 
          />
        </div>
        <button type="submit">Register</button>
      </form>
      <p>
        Already have an account? 
        <button className="link-button" onClick={() => setCurrentPage('login')}>
          Login
        </button>
      </p>
    </div>
  );
  
  // Render dashboard with event list
  const renderDashboard = () => (
    <div className="dashboard">
      <header>
        <h1>My Events</h1>
        <button className="logout-button" onClick={handleLogout}>Logout</button>
      </header>
      
      <button 
        className="create-event-button" 
        onClick={() => setCurrentPage('create-event')}
      >
        Create New Event
      </button>
      
      <div className="events-list">
        {events.length > 0 ? (
          events.map(event => (
            <div key={event.id} className="event-card">
              <h3>{event.title}</h3>
              <p><strong>Date:</strong> {event.start_date} to {event.end_date}</p>
              <p><strong>Location:</strong> {event.location || 'Not specified'}</p>
              <div className="event-actions">
                <button onClick={() => viewEventDetails(event)}>View Details</button>
                <button 
                  className="danger" 
                  onClick={() => deleteEvent(event.id)}
                >
                  Delete
                </button>
              </div>
            </div>
          ))
        ) : (
          <p>No events found. Create your first event!</p>
        )}
      </div>
    </div>
  );
  
  // Render event creation form
  const renderCreateEvent = () => (
    <div className="event-form">
      <h2>Create New Event</h2>
      <form onSubmit={handleCreateEvent}>
        <div className="form-group">
          <label>Event Title:</label>
          <input 
            type="text" 
            name="title" 
            value={eventForm.title} 
            onChange={handleEventChange} 
            required 
          />
        </div>
        <div className="form-group">
          <label>Description:</label>
          <textarea 
            name="description" 
            value={eventForm.description} 
            onChange={handleEventChange}
          />
        </div>
        <div className="form-group">
          <label>Start Date:</label>
          <input 
            type="date" 
            name="start_date" 
            value={eventForm.start_date} 
            onChange={handleEventChange} 
            required 
          />
        </div>
        <div className="form-group">
          <label>End Date:</label>
          <input 
            type="date" 
            name="end_date" 
            value={eventForm.end_date} 
            onChange={handleEventChange} 
            required 
          />
        </div>
        <div className="form-group">
          <label>Location:</label>
          <input 
            type="text" 
            name="location" 
            value={eventForm.location} 
            onChange={handleEventChange} 
          />
        </div>
        <div className="form-actions">
          <button type="submit">Create Event</button>
          <button 
            type="button" 
            className="cancel"
            onClick={() => setCurrentPage('dashboard')}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
  
  // Render event details
  const renderEventDetail = () => (
    <div className="event-detail">
      <button 
        className="back-button"
        onClick={() => setCurrentPage('dashboard')}
      >
        ← Back to Events
      </button>
      
      <h2>{currentEvent.title}</h2>
      
      <div className="event-info">
        <p><strong>Date:</strong> {currentEvent.start_date} to {currentEvent.end_date}</p>
        <p><strong>Location:</strong> {currentEvent.location || 'Not specified'}</p>
        {currentEvent.description && (
          <div className="event-description">
            <p>{currentEvent.description}</p>
          </div>
        )}
      </div>
      
      <div className="event-sections">
        <div className="event-section">
          <h3>Guest Management</h3>
          {/* Guest list would be rendered here */}
          <button className="secondary">Invite Guests</button>
        </div>
        
        <div className="event-section">
          <h3>Budget Planning</h3>
          <p>Total: $0.00</p>
          <button className="secondary">Add Budget Item</button>
        </div>
        
        <div className="event-section">
          <h3>Vendors</h3>
          <button className="secondary">Add Vendor</button>
        </div>
        
        <div className="event-section">
          <h3>Timeline</h3>
          <button className="secondary">Add Timeline Item</button>
        </div>
      </div>
      
      <button 
        className="download-ical"
        onClick={async () => {
          try {
            const response = await fetch(`/api/events/${currentEvent.id}/ical`);
            const { content } = await response.json();
            // In a real app, we'd use this to generate a downloadable file
            alert('iCal content generated (would download in production)');
          } catch (error) {
            console.error('Failed to generate iCal:', error);
          }
        }}
      >
        Download iCal
      </button>
    </div>
  );
  
  // Main render function with routing
  return (
    <div className="app">
      {currentPage === 'login' && renderLogin()}
      {currentPage === 'register' && renderRegister()}
      {currentPage === 'dashboard' && renderDashboard()}
      {currentPage === 'create-event' && renderCreateEvent()}
      {currentPage === 'event-detail' && currentEvent && renderEventDetail()}
    </div>
  );
}

// Mounting logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
