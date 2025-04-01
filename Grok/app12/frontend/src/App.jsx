import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
  const [currentPage, setCurrentPage] = useState('login');
  const [token, setToken] = useState(null);
  const [calendar, setCalendar] = useState([]);
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedTime, setSelectedTime] = useState('');
  const [reservations, setReservations] = useState({});

  useEffect(() => {
    if (token) {
      fetchCalendar();
      fetchReservations();
    }
  }, [token]);

  const fetchCalendar = async () => {
    try {
      const response = await fetch('/api/get_calendar');
      if (response.ok) {
        const data = await response.json();
        setCalendar(data);
      } else {
        console.error('Failed to fetch calendar');
      }
    } catch (error) {
      console.error('Error fetching calendar:', error);
    }
  };

  const fetchReservations = async () => {
    try {
      const response = await fetch('/api/get_reservations', {
        headers: {
          'Authorization': token
        }
      });
      if (response.ok) {
        const data = await response.json();
        setReservations(data);
      } else {
        console.error('Failed to fetch reservations');
      }
    } catch (error) {
      console.error('Error fetching reservations:', error);
    }
  };

  const handleLogin = async (username, password) => {
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      });
      if (response.ok) {
        const data = await response.json();
        setToken(data.token);
        setCurrentPage('dashboard');
      } else {
        console.error('Login failed');
      }
    } catch (error) {
      console.error('Error during login:', error);
    }
  };

  const handleCheckAvailability = async () => {
    try {
      const response = await fetch('/api/check_availability', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ date: selectedDate, time: selectedTime })
      });
      if (response.ok) {
        const data = await response.json();
        if (data.available) {
          alert('Slot is available');
        } else {
          alert('Slot is not available');
        }
      } else {
        console.error('Failed to check availability');
      }
    } catch (error) {
      console.error('Error checking availability:', error);
    }
  };

  const handleBookSlot = async () => {
    try {
      const response = await fetch('/api/book_slot', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token
        },
        body: JSON.stringify({ date: selectedDate, time: selectedTime })
      });
      if (response.ok) {
        alert('Slot booked successfully');
        fetchCalendar();
        fetchReservations();
      } else {
        const data = await response.json();
        alert(data.error || 'Failed to book slot');
      }
    } catch (error) {
      console.error('Error booking slot:', error);
    }
  };

  const renderLogin = () => (
    <div className="login-page">
      <h1>Login</h1>
      <input type="text" placeholder="Username" id="username" />
      <input type="password" placeholder="Password" id="password" />
      <button onClick={() => {
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        handleLogin(username, password);
      }}>Login</button>
    </div>
  );

  const renderDashboard = () => (
    <div className="dashboard-page">
      <h1>Dashboard</h1>
      <button onClick={() => setCurrentPage('calendar')}>View Calendar</button>
      <button onClick={() => setCurrentPage('reservations')}>View Reservations</button>
      <button onClick={() => setCurrentPage('book')}>Book a Slot</button>
    </div>
  );

  const renderCalendar = () => (
    <div className="calendar-page">
      <h1>Calendar</h1>
      {calendar.map(day => (
        <div key={day.date}>
          <h2>{day.date}</h2>
          <ul>
            {day.slots.map(slot => (
              <li key={slot.time} className={slot.available ? 'available' : 'unavailable'}>
                {slot.time} - {slot.available ? 'Available' : 'Booked'}
              </li>
            ))}
          </ul>
        </div>
      ))}
      <button onClick={() => setCurrentPage('dashboard')}>Back to Dashboard</button>
    </div>
  );

  const renderReservations = () => (
    <div className="reservations-page">
      <h1>My Reservations</h1>
      <ul>
        {Object.entries(reservations).map(([key, value]) => (
          <li key={key}>
            {key.split('_')[0]} at {key.split('_')[1]} - Booked by {value.user}
          </li>
        ))}
      </ul>
      <button onClick={() => setCurrentPage('dashboard')}>Back to Dashboard</button>
    </div>
  );

  const renderBookSlot = () => (
    <div className="book-slot-page">
      <h1>Book a Slot</h1>
      <input type="date" onChange={e => setSelectedDate(e.target.value)} />
      <input type="time" onChange={e => setSelectedTime(e.target.value)} />
      <button onClick={handleCheckAvailability}>Check Availability</button>
      <button onClick={handleBookSlot}>Book Slot</button>
      <button onClick={() => setCurrentPage('dashboard')}>Back to Dashboard</button>
    </div>
  );

  const renderPage = () => {
    switch (currentPage) {
      case 'login':
        return renderLogin();
      case 'dashboard':
        return renderDashboard();
      case 'calendar':
        return renderCalendar();
      case 'reservations':
        return renderReservations();
      case 'book':
        return renderBookSlot();
      default:
        return <div>404 - Page not found</div>;
    }
  };

  return (
    <div className="app">
      {renderPage()}
    </div>
  );
};

// Mounting Logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
