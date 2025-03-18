import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import "./App.css";

function App() {
  const [date, setDate] = useState("");
  const [timeSlots, setTimeSlots] = useState([]);
  const [selectedTime, setSelectedTime] = useState("");
  const [name, setName] = useState("");
  const [reservations, setReservations] = useState([]);
  const [view, setView] = useState("home");

  useEffect(() => {
    if (date) {
      fetch(`http://localhost:5183/api/available-slots/${date}`)
        .then((response) => response.json())
        .then((data) => setTimeSlots(data))
        .catch(() => setTimeSlots([]));
    }
  }, [date]);

  const handleReserve = () => {
    if (!date || !selectedTime || !name) {
      alert("Please fill out all fields");
      return;
    }

    fetch("http://localhost:5183/api/reserve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ date, time: selectedTime, name }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.error) {
          alert(data.error);
        } else {
          alert("Reservation successful!");
          setView("reservations");
        }
      });
  };

  const fetchReservations = () => {
    fetch("http://localhost:5183/api/reservations")
      .then((response) => response.json())
      .then((data) => setReservations(data));
  };

  useEffect(() => {
    if (view === "reservations") {
      fetchReservations();
    }
  }, [view]);

  return (
    <div className="App">
      <header>
        <h1>Reservation System</h1>
        <nav>
          <button onClick={() => setView("home")}>Home</button>
          <button onClick={() => setView("reservations")}>Reservations</button>
        </nav>
      </header>

      {view === "home" && (
        <div className="booking-form">
          <h2>Book a Time Slot</h2>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
          <select
            value={selectedTime}
            onChange={(e) => setSelectedTime(e.target.value)}
          >
            <option value="">Select a time</option>
            {timeSlots.map((slot, index) => (
              <option key={index} value={slot}>
                {slot}
              </option>
            ))}
          </select>
          <input
            type="text"
            placeholder="Your name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <button onClick={handleReserve}>Reserve</button>
        </div>
      )}

      {view === "reservations" && (
        <div className="reservations-list">
          <h2>Your Reservations</h2>
          {reservations.length === 0 ? (
            <p>No reservations found.</p>
          ) : (
            <ul>
              {reservations.map((reservation, index) => (
                <li key={index}>
                  {reservation.date} at {reservation.time} -{" "}
                  {reservation.name}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
