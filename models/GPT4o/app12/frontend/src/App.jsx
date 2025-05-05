import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [currentPage, setCurrentPage] = useState("home"); // For routing
  const [selectedDate, setSelectedDate] = useState("");
  const [availableSlots, setAvailableSlots] = useState({});
  const [reservations, setReservations] = useState([]);
  const [confirmation, setConfirmation] = useState("");

  // Fetch available slots for a selected date
  const fetchAvailability = async (date) => {
    try {
      const response = await fetch(`/api/availability?date=${date}`);
      const data = await response.json();
      if (response.ok) {
        setAvailableSlots(data.slots);
      } else {
        alert(data.error || "Failed to fetch availability");
      }
    } catch (err) {
      console.error("Error fetching availability:", err);
    }
  };

  // Fetch reservations (can be used for "View Reservations" page)
  const fetchReservations = async () => {
    try {
      const response = await fetch(`/api/reservations`);
      const data = await response.json();
      if (response.ok) {
        setReservations(data);
      } else {
        alert(data.error || "Failed to fetch reservations");
      }
    } catch (err) {
      console.error("Error fetching reservations:", err);
    }
  };

  // Reserve a specific time slot
  const bookSlot = async (timeSlot) => {
    try {
      const response = await fetch('/api/reserve', {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ date: selectedDate, timeSlot })
      });

      const data = await response.json();
      if (response.ok) {
        setConfirmation(data.message);
        fetchAvailability(selectedDate); // Refresh available slots
      } else {
        alert(data.error || "Failed to book slot");
      }
    } catch (err) {
      console.error("Error booking slot:", err);
    }
  };

  // Change Routing (Page Navigation)
  const renderPage = () => {
    if (currentPage === "home") {
      return (
        <div>
          <h1>Reservation System</h1>
          <input 
            type="date" 
            onChange={(e) => setSelectedDate(e.target.value)} 
            value={selectedDate}
          />
          <button onClick={() => fetchAvailability(selectedDate)}>Check Availability</button>
          <div className="slots">
            {Object.keys(availableSlots).map((period) => (
              <div key={period}>
                <h3>{period}</h3>
                <ul>
                  {availableSlots[period].map((slot) => (
                    <li key={slot}>
                      {slot} <button onClick={() => bookSlot(slot)}>Book</button>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          <p className="confirmation">{confirmation}</p>
        </div>
      );
    } else if (currentPage === "reservations") {
      return (
        <div>
          <h1>Your Reservations</h1>
          <button onClick={fetchReservations}>Refresh</button>
          <ul>
            {Object.keys(reservations).map((date) => (
              <li key={date}>
                <strong>{date}:</strong> {reservations[date].join(", ")}
              </li>
            ))}
          </ul>
        </div>
      );
    }
  };

  return (
    <div>
      <nav>
        <button onClick={() => setCurrentPage("home")}>Home</button>
        <button onClick={() => setCurrentPage("reservations")}>Reservations</button>
      </nav>
      {renderPage()}
    </div>
  );
}

// Mount app
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
