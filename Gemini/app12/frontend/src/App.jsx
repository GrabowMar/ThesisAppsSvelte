// app/frontend/src/App.jsx
import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [currentPage, setCurrentPage] = useState('calendar'); // calendar, booking, confirmation, login
  const [selectedDate, setSelectedDate] = useState(null);
  const [availability, setAvailability] = useState({});
  const [selectedTimeslot, setSelectedTimeslot] = useState(null);
  const [bookingConfirmation, setBookingConfirmation] = useState(null);
  const [loginStatus, setLoginStatus] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [authToken, setAuthToken] = useState('');

  // Fetch availability on date change
  useEffect(() => {
    if (selectedDate) {
      fetchAvailability(selectedDate);
    }
  }, [selectedDate]);

  const fetchAvailability = async (date) => {
    const startDate = date; // Use date directly, assuming formatted as '5423-MM-DD'
    const endDate = date;
    try {
      const response = await fetch(`/api/availability?startDate=${startDate}&endDate=${endDate}`);
      if (response.ok) {
        const data = await response.json();
        setAvailability(data);
      } else {
        console.error('Failed to fetch availability:', response.status);
        setAvailability({}); // Clear availability on error
      }
    } catch (error) {
      console.error('Error fetching availability:', error);
      setAvailability({}); // Clear availability on error
    }
  };

  const handleDateSelect = (date) => {
    setSelectedDate(date);
  };

  const handleTimeslotSelect = (timeslot) => {
    setSelectedTimeslot(timeslot);
    setCurrentPage('booking'); // Navigate to booking form
  };


  const handleBookingSubmit = async (userDetails) => {
    if (!authToken) {
      alert('Please login to make a reservation.');
      setCurrentPage('login');
      return;
    }
    try {
      const response = await fetch('/api/reserve', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          date: selectedDate,
          timeslot: selectedTimeslot,
          user: userDetails,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setBookingConfirmation(data.message);
        setCurrentPage('confirmation');
      } else {
        const errorData = await response.json();
        alert(`Booking failed: ${errorData.error}`);
      }
    } catch (error) {
      console.error('Error booking timeslot:', error);
      alert('Failed to book timeslot. Please try again.');
    }
  };

  const handleLogin = async () => {
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username: username, password: password }),
      });

      if (response.ok) {
        const data = await response.json();
        setAuthToken(data.token); // Store the token
        setLoginStatus(true);
        setCurrentPage('calendar');
      } else {
        const errorData = await response.json();
        alert(`Login failed: ${errorData.error}`);
      }
    } catch (error) {
      console.error('Login error:', error);
      alert('Failed to login. Please try again.');
    }
  };

  const handleLogout = () => {
    setAuthToken('');
    setLoginStatus(false);
    setCurrentPage('calendar');
  };

  let content;

  if (!loginStatus) {
    content = (
      <div className="login-container">
        <h2>Login</h2>
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button onClick={handleLogin}>Login</button>
      </div>
    );
  } else if (currentPage === 'calendar') {
    content = (
      <CalendarView
        onDateSelect={handleDateSelect}
        availability={availability}
        onTimeslotSelect={handleTimeslotSelect}
        onLogout={handleLogout}
      />
    );
  } else if (currentPage === 'booking') {
    content = (
      <BookingForm
        date={selectedDate}
        timeslot={selectedTimeslot}
        onSubmit={handleBookingSubmit}
        onCancel={() => setCurrentPage('calendar')}
      />
    );
  } else if (currentPage === 'confirmation') {
    content = <ConfirmationView message={bookingConfirmation} onBackToCalendar={() => setCurrentPage('calendar')} />;
  } else {
    content = <div>Error: Unknown page</div>;
  }

  return (
    <div className="app-container">
      <h1>Reservation System</h1>
      {content}
    </div>
  );
}

function CalendarView({ onDateSelect, availability, onTimeslotSelect, onLogout }) {
  const today = new Date();
  const [currentMonth, setCurrentMonth] = useState(today.getMonth());
  const [currentYear, setCurrentYear] = useState(today.getFullYear());

  const daysInMonth = (month, year) => new Date(year, month + 1, 0).getDate();

  const getFirstDayOfMonth = (month, year) => new Date(year, month, 1).getDay(); // 0=Sunday, 1=Monday...

  const prevMonth = () => {
    setCurrentMonth(currentMonth === 0 ? 11 : currentMonth - 1);
    setCurrentYear(currentMonth === 0 ? currentYear - 1 : currentYear);
  };

  const nextMonth = () => {
    setCurrentMonth(currentMonth === 11 ? 0 : currentMonth + 1);
    setCurrentYear(currentMonth === 11 ? currentYear + 1 : currentYear);
  };

  const monthNames = ["January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  const days = [];
  const totalDays = daysInMonth(currentMonth, currentYear);
  const firstDay = getFirstDayOfMonth(currentMonth, currentYear);

  for (let i = 0; i < firstDay; i++) {
    days.push(<div key={`empty-${i}`} className="calendar-day empty"></div>);
  }

  for (let day = 1; day <= totalDays; day++) {
    const date = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    const availableSlots = availability[date] || [];
    const isAvailable = availableSlots.length > 0;

    days.push(
      <div
        key={day}
        className={`calendar-day ${isAvailable ? 'available' : ''}`}
        onClick={() => {
          if (isAvailable) {
            onDateSelect(date);
          }
        }}
      >
        <div className="day-number">{day}</div>
        {isAvailable && (
          <div className="timeslots">
            {availableSlots.map((timeslot) => (
              <button key={timeslot} onClick={(e) => {
                e.stopPropagation(); // Prevent date click when clicking on timeslot button
                onTimeslotSelect(timeslot);
              }}>
                {timeslot}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="calendar">
      <div className="calendar-header">
        <button onClick={prevMonth}>&lt;</button>
        <h2>{monthNames[currentMonth]} {currentYear}</h2>
        <button onClick={nextMonth}>&gt;</button>
        <button onClick={onLogout}>Logout</button>
      </div>
      <div className="calendar-grid">
        <div className="day-name">Sun</div>
        <div className="day-name">Mon</div>
        <div className="day-name">Tue</div>
        <div className="day-name">Wed</div>
        <div className="day-name">Thu</div>
        <div className="day-name">Fri</div>
        <div className="day-name">Sat</div>
        {days}
      </div>
    </div>
  );
}

function BookingForm({ date, timeslot, onSubmit, onCancel }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (name && email) {
      onSubmit({ name, email });
    } else {
      alert('Please enter your name and email.');
    }
  };

  return (
    <div className="booking-form">
      <h2>Booking Details</h2>
      <p>Date: {date}</p>
      <p>Timeslot: {timeslot}</p>
      <form onSubmit={handleSubmit}>
        <label>Name:</label>
        <input type="text" value={name} onChange={(e) => setName(e.target.value)} required />
        <label>Email:</label>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <button type="submit">Confirm Booking</button>
        <button type="button" onClick={onCancel}>Cancel</button>
      </form>
    </div>
  );
}

function ConfirmationView({ message, onBackToCalendar }) {
  return (
    <div className="confirmation">
      <h2>Booking Confirmed!</h2>
      <p>{message}</p>
      <button onClick={onBackToCalendar}>Back to Calendar</button>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

export default App;
