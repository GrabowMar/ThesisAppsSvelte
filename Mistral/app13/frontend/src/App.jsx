import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Link, useNavigate } from 'react-router-dom';
import './App.css';

const App = () => {
  const [timeSlots, setTimeSlots] = useState([]);
  const [reservations, setReservations] = useState({});
  const [date, setDate] = useState('');
  const [timeSlot, setTimeSlot] = useState('');
  const [message, setMessage] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetch('http://localhost:5103/time-slots')
      .then(response => response.json())
      .then(data => setTimeSlots(data));
  }, []);

  const handleReserve = () => {
    fetch('http://localhost:5103/reserve', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ date, time_slot: timeSlot })
    })
      .then(response => response.json())
      .then(data => setMessage(data.message));
  };

  const handleCheckAvailability = () => {
    fetch(`http://localhost:5103/availability?date=${date}`)
      .then(response => response.json())
      .then(data => {
        if (data.available) {
          setMessage('Time slot is available');
        } else {
          setMessage('Time slot is not available');
        }
      });
  };

  const handleGetBookings = () => {
    fetch('http://localhost:5103/bookings')
      .then(response => response.json())
      .then(data => setReservations(data));
  };

  return (
    <Router>
      <div className="App">
        <nav>
          <Link to="/">Home</Link>
          <Link to="/login">Login</Link>
          <Link to="/register">Register</Link>
          <Link to="/dashboard">Dashboard</Link>
        </nav>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/dashboard" element={<Dashboard onCheckAvailability={handleCheckAvailability} onReserve={handleReserve} onGetBookings={handleGetBookings} message={message} timeSlots={timeSlots} reservations={reservations} date={date} setDate={setDate} timeSlot={timeSlot} setTimeSlot={setTimeSlot} />} />
        </Routes>
      </div>
    </Router>
  );
};

const Home = () => <h1>Welcome to the Reservation System</h1>;

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleLogin = () => {
    fetch('http://localhost:5103/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ username, password })
    })
      .then(response => response.json())
      .then(data => {
        if (data.message === 'Login successful') {
          navigate('/dashboard');
        }
      });
  };

  return (
    <div>
      <h2>Login</h2>
      <input type="text" placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} />
      <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
      <button onClick={handleLogin}>Login</button>
    </div>
  );
};

const Register = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleRegister = () => {
    fetch('http://localhost:5103/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ username, password })
    })
      .then(response => response.json())
      .then(data => {
        if (data.message === 'Registration successful') {
          navigate('/login');
        }
      });
  };

  return (
    <div>
      <h2>Register</h2>
      <input type="text" placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} />
      <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
      <button onClick={handleRegister}>Register</button>
    </div>
  );
};

const Dashboard = ({ onCheckAvailability, onReserve, onGetBookings, message, timeSlots, reservations, date, setDate, timeSlot, setTimeSlot }) => {
  return (
    <div>
      <h2>Dashboard</h2>
      <input type="date" value={date} onChange={e => setDate(e.target.value)} />
      <select value={timeSlot} onChange={e => setTimeSlot(e.target.value)}>
        {timeSlots.map(slot => (
          <option key={slot} value={slot}>{slot}</option>
        ))}
      </select>
      <button onClick={onCheckAvailability}>Check Availability</button>
      <button onClick={onReserve}>Reserve</button>
      <button onClick={onGetBookings}>Get Bookings</button>
      <p>{message}</p>
      <div>
        <h3>Reservations</h3>
        <ul>
          {Object.keys(reservations).map(key => (
            <li key={key}>{key}: {reservations[key]}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
