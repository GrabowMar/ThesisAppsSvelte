import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [date, setDate] = useState('');
  const [timeSlot, setTimeSlot] = useState('');
  const [name, setName] = useState('');
  const [reservations, setReservations] = useState([]);
  const [availability, setAvailability] = useState(null);

  const checkAvailability = async () => {
    try {
      const response = await fetch(`http://localhost:5023/availability?date=${date}&time_slot=${timeSlot}`);
      const data = await response.json();
      setAvailability(data.available);
    } catch (error) {
      console.error(error);
    }
  };

  const makeReservation = async () => {
    try {
      const response = await fetch('http://localhost:5023/reserve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, date, time_slot: timeSlot }),
      });
      const data = await response.json();
      console.log(data);
    } catch (error) {
      console.error(error);
    }
  };

  const getReservations = async () => {
    try {
      const response = await fetch('http://localhost:5023/reservations');
      const data = await response.json();
      setReservations(data);
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    getReservations();
  }, []);

  return (
    <div className="App">
      <h1>Reservation System</h1>
      <form>
        <label>
          Name:
          <input type="text" value={name} onChange={(e) => setName(e.target.value)} />
        </label>
        <label>
          Date:
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        </label>
        <label>
          Time Slot:
          <input type="time" value={timeSlot} onChange={(e) => setTimeSlot(e.target.value)} />
        </label>
        <button type="button" onClick={checkAvailability}>
          Check Availability
        </button>
        {availability !== null && (
          <p>Availability: {availability ? 'Available' : 'Not Available'}</p>
        )}
        <button type="button" onClick={makeReservation}>
          Make Reservation
        </button>
      </form>
      <h2>Reservations:</h2>
      <ul>
        {reservations.map((reservation, index) => (
          <li key={index}>{reservation}</li>
        ))}
      </ul>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
