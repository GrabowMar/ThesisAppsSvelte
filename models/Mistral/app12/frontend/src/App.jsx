import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import axios from 'axios';
import './App.css';

const ReservationList = () => {
  const [reservations, setReservations] = useState([]);

  useEffect(() => {
    axios.get('/api/reservations')
      .then(response => setReservations(response.data))
      .catch(error => console.error('Error fetching reservations:', error));
  }, []);

  const handleDelete = (id) => {
    axios.delete(`/api/reservations/${id}`)
      .then(() => setReservations(reservations.filter(r => r.id !== id)))
      .catch(error => console.error('Error deleting reservation:', error));
  };

  return (
    <div>
      <h2>Reservations</h2>
      <ul>
        {reservations.map(reservation => (
          <li key={reservation.id}>
            {reservation.name} - {reservation.time}
            <button onClick={() => handleDelete(reservation.id)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  );
};

const ReservationForm = () => {
  const [name, setName] = useState('');
  const [time, setTime] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    axios.post('/api/reservations', { name, time })
      .then(() => {
        setMessage('Reservation created successfully!');
        setName('');
        setTime('');
      })
      .catch(error => setMessage('Error creating reservation: ' + error.response.data.error));
  };

  return (
    <div>
      <h2>Create Reservation</h2>
      <form onSubmit={handleSubmit}>
        <input type="text" value={name} onChange={e => setName(e.target.value)} placeholder="Name" required />
        <input type="text" value={time} onChange={e => setTime(e.target.value)} placeholder="Time (e.g., 10:00 AM)" required />
        <button type="submit">Create</button>
      </form>
      {message && <p>{message}</p>}
    </div>
  );
};

const App = () => {
  return (
    <Router>
      <nav>
        <Link to="/">Home</Link>
        <Link to="/reservations">Reservations</Link>
        <Link to="/create">Create Reservation</Link>
      </nav>
      <Routes>
        <Route path="/" element={<h1>Welcome to the Reservation System</h1>} />
        <Route path="/reservations" element={<ReservationList />} />
        <Route path="/create" element={<ReservationForm />} />
      </Routes>
    </Router>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
