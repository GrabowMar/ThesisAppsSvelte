// 1. Imports
import React, { useState, useEffect, createContext, useContext } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// Context for authentication
const AuthContext = createContext();

// Main App Component
function App() {
  // Application state
  const [page, setPage] = useState('login');
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [message, setMessage] = useState({ text: '', type: '' });

  // Check if user is already logged in
  useEffect(() => {
    if (token) {
      const userData = localStorage.getItem('user');
      if (userData) {
        setUser(JSON.parse(userData));
        setPage('dashboard');
      } else {
        handleLogout();
      }
    }
  }, [token]);

  // Authentication functions
  const handleLogin = (userData, authToken) => {
    setUser(userData);
    setToken(authToken);
    localStorage.setItem('token', authToken);
    localStorage.setItem('user', JSON.stringify(userData));
    setPage('dashboard');
  };

  const handleLogout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setPage('login');
  };

  // Message display functions
  const showMessage = (text, type = 'info', duration = 3000) => {
    setMessage({ text, type });
    setTimeout(() => setMessage({ text: '', type: '' }), duration);
  };

  // Render the appropriate page
  const renderPage = () => {
    switch (page) {
      case 'login':
        return <LoginPage onSwitch={() => setPage('register')} />;
      case 'register':
        return <RegisterPage onSwitch={() => setPage('login')} />;
      case 'dashboard':
        return <Dashboard onNavigate={setPage} />;
      case 'bookReservation':
        return <BookReservation onNavigate={setPage} />;
      case 'myReservations':
        return <MyReservations onNavigate={setPage} />;
      default:
        return <LoginPage onSwitch={() => setPage('register')} />;
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, handleLogin, handleLogout, showMessage }}>
      <div className="app-container">
        <Navbar page={page} setPage={setPage} />
        {message.text && <MessageBar message={message} />}
        {renderPage()}
      </div>
    </AuthContext.Provider>
  );
}

// Navbar Component
function Navbar({ page, setPage }) {
  const { user, handleLogout } = useContext(AuthContext);

  return (
    <nav className="navbar">
      <div className="navbar-brand" onClick={() => user ? setPage('dashboard') : setPage('login')}>
        <h1>ResBooker</h1>
      </div>
      
      {user && (
        <div className="navbar-menu">
          <button 
            className={`nav-button ${page === 'dashboard' ? 'active' : ''}`} 
            onClick={() => setPage('dashboard')}>
            Dashboard
          </button>
          <button 
            className={`nav-button ${page === 'bookReservation' ? 'active' : ''}`} 
            onClick={() => setPage('bookReservation')}>
            Book Slot
          </button>
          <button 
            className={`nav-button ${page === 'myReservations' ? 'active' : ''}`} 
            onClick={() => setPage('myReservations')}>
            My Reservations
          </button>
          <div className="user-info">
            <span>Hello, {user.name}</span>
            <button className="logout-button" onClick={handleLogout}>Logout</button>
          </div>
        </div>
      )}
    </nav>
  );
}

// Message Bar Component
function MessageBar({ message }) {
  return (
    <div className={`message-bar ${message.type}`}>
      {message.text}
    </div>
  );
}

// Login Page Component
function LoginPage({ onSwitch }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  const { handleLogin, showMessage } = useContext(AuthContext);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || 'Failed to login');
      }
      
      handleLogin(data.user, data.token);
      showMessage('Login successful!', 'success');
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-form-container">
        <h2>Log In</h2>
        <form className="auth-form" onSubmit={handleSubmit}>
          {error && <div className="error-message">{error}</div>}
          
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
            />
          </div>
          
          <button 
            type="submit" 
            className="auth-button"
            disabled={isLoading}
          >
            {isLoading ? 'Loading...' : 'Login'}
          </button>
        </form>
        
        <p className="auth-switch">
          Don't have an account?{' '}
          <button onClick={onSwitch} className="auth-switch-button">
            Register
          </button>
        </p>
      </div>
    </div>
  );
}

// Register Page Component
function RegisterPage({ onSwitch }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  const { showMessage } = useContext(AuthContext);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      setIsLoading(false);
      return;
    }
    
    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, email, password }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || 'Failed to register');
      }
      
      showMessage('Registration successful! You can now log in', 'success');
      onSwitch(); // Switch to login page
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-form-container">
        <h2>Register</h2>
        <form className="auth-form" onSubmit={handleSubmit}>
          {error && <div className="error-message">{error}</div>}
          
          <div className="form-group">
            <label htmlFor="name">Full Name</label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter your full name"
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm your password"
              required
            />
          </div>
          
          <button 
            type="submit" 
            className="auth-button"
            disabled={isLoading}
          >
            {isLoading ? 'Loading...' : 'Register'}
          </button>
        </form>
        
        <p className="auth-switch">
          Already have an account?{' '}
          <button onClick={onSwitch} className="auth-switch-button">
            Login
          </button>
        </p>
      </div>
    </div>
  );
}

// Dashboard Component
function Dashboard({ onNavigate }) {
  const { user } = useContext(AuthContext);
  const [upcomingReservations, setUpcomingReservations] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const { token } = useContext(AuthContext);

  useEffect(() => {
    const fetchReservations = async () => {
      try {
        const response = await fetch('/api/user/reservations?status=confirmed', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        
        const data = await response.json();
        
        if (!response.ok) {
          throw new Error(data.message || 'Failed to fetch reservations');
        }
        
        setUpcomingReservations(data.reservations);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchReservations();
  }, [token]);

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h2>Welcome, {user.name}!</h2>
        <p>Manage your reservations and book new time slots.</p>
      </div>
      
      <div className="dashboard-actions">
        <div className="action-card" onClick={() => onNavigate('bookReservation')}>
          <h3>Book New Reservation</h3>
          <p>Browse available time slots and make a new reservation.</p>
          <button className="action-button">Book Now</button>
        </div>
        
        <div className="action-card" onClick={() => onNavigate('myReservations')}>
          <h3>My Reservations</h3>
          <p>View and manage your current reservations.</p>
          <button className="action-button">View All</button>
        </div>
      </div>
      
      <div className="upcoming-reservations">
        <h3>Upcoming Reservations</h3>
        {isLoading ? (
          <p>Loading your reservations...</p>
        ) : error ? (
          <p className="error-message">{error}</p>
        ) : upcomingReservations.length === 0 ? (
          <p>You don't have any upcoming reservations.</p>
        ) : (
          <div className="reservations-grid">
            {upcomingReservations.slice(0, 3).map((reservation) => (
              <ReservationCard 
                key={reservation.id} 
                reservation={reservation} 
                showActions={false}
              />
            ))}
          </div>
        )}
        
        {upcomingReservations.length > 0 && (
          <button className="view-all-button" onClick={() => onNavigate('myReservations')}>
            View All Reservations
          </button>
        )}
      </div>
    </div>
  );
}

// Book Reservation Component
function BookReservation({ onNavigate }) {
  const [timeSlots, setTimeSlots] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedDate, setSelectedDate] = useState('');
  const [notes, setNotes] = useState('');
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [bookingInProgress, setBookingInProgress] = useState(false);
  
  const { token, showMessage } = useContext(AuthContext);
  
  // Get available dates (next 14 days)
  const availableDates = [];
  const today = new Date();
  for (let i = 0; i < 14; i++) {
    const date = new Date(today);
    date.setDate(today.getDate() + i);
    availableDates.push(date.toISOString().split('T')[0]);
  }
  
  // Set default selected date to today
  useEffect(() => {
    if (!selectedDate) {
      setSelectedDate(today.toISOString().split('T')[0]);
    }
  }, []);
  
  // Fetch time slots when selected date changes
  useEffect(() => {
    if (!selectedDate) return;
    
    const fetchTimeSlots = async () => {
      setIsLoading(true);
      setError('');
      
      try {
        const response = await fetch(`/api/time-slots?start_date=${selectedDate}&end_date=${selectedDate}`);
        
        const data = await response.json();
        
        if (!response.ok) {
          throw new Error(data.message || 'Failed to fetch time slots');
        }
        
        setTimeSlots(data.time_slots);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchTimeSlots();
  }, [selectedDate]);
  
  // Handle booking a time slot
  const handleBookSlot = async () => {
    if (!selectedSlot) {
      showMessage('Please select a time slot first', 'error');
      return;
    }
    
    setBookingInProgress(true);
    
    try {
      const response = await fetch('/api/reservations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          time_slot_id: selectedSlot,
          notes: notes,
        }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || 'Failed to book reservation');
      }
      
      showMessage('Reservation booked successfully!', 'success');
      
      // Refresh time slots to update availability
      setTimeout(() => {
        onNavigate('myReservations');
      }, 1500);
      
    } catch (err) {
      showMessage(err.message, 'error');
    } finally {
      setBookingInProgress(false);
    }
  };
  
  return (
    <div className="book-reservation-container">
      <h2>Book a Reservation</h2>
      
      <div className="date-selector">
        <label htmlFor="date">Select Date:</label>
        <select
          id="date"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
        >
          {availableDates.map((date) => (
            <option key={date} value={date}>
              {new Date(date).toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </option>
          ))}
        </select>
      </div>
      
      <div className="time-slots-container">
        <h3>Available Time Slots</h3>
        
        {isLoading ? (
          <p>Loading available time slots...</p>
        ) : error ? (
          <p className="error-message">{error}</p>
        ) : timeSlots.length === 0 ? (
          <p>No time slots available for this date.</p>
        ) : (
          <div className="time-slots-grid">
            {timeSlots.map((slot) => (
              <div
                key={slot.id}
                className={`time-slot ${!slot.is_available ? 'unavailable' : ''} ${selectedSlot === slot.id ? 'selected' : ''}`}
                onClick={() => slot.is_available && setSelectedSlot(slot.id)}
              >
                <p className="time">{slot.start_time} - {slot.end_time}</p>
                <p className="status">
                  {slot.is_available
