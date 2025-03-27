import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import "./App.css";

const App = () => {
  const [timeSlots, setTimeSlots] = useState([]);
  const [reservations, setReservations] = useState([]);
  const [name, setName] = useState("");
  const [selectedSlot, setSelectedSlot] = useState(null);

  // Fetch time slots
  useEffect(() => {
    fetch("/api/time-slots")
      .then((res) => res.json())
      .then((data) => setTimeSlots(data.time_slots))
      .catch((err) => console.error(err));
  }, []);

  // Fetch reservations
  useEffect(() => {
    fetch("/api/reservations")
      .then((res) => res.json())
      .then((data) => setReservations(data.reservations))
      .catch((err) => console.error(err));
  }, []);

  // Handle reservation
  const handleReservation = () => {
    if (!selectedSlot || !name) {
      alert("Please select a slot and enter your name.");
      return;
    }

    fetch("/api/reservations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ slot_id: selectedSlot, name }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.error) {
          alert(data.error);
        } else {
          setReservations([...reservations, data.reservation]);
          alert("Reservation confirmed!");
        }
      })
      .catch((err) => console.error(err));
  };

  return (
    <main>
      <h1>Reservation System</h1>
      <div className="calendar">
        <h2>Available Time Slots</h2>
        <ul>
          {timeSlots.map((slot) => (
            <li key={slot.id}>
              <button
                onClick={() => setSelectedSlot(slot.id)}
                disabled={reservations.some((r) => r.slot_id === slot.id)}
              >
                {slot.start_time} - {slot.end_time}
              </button>
            </li>
          ))}
        </ul>
      </div>
      <div className="reservation-form">
        <h2>Make a Reservation</h2>
        <input
          type="text"
          placeholder="Your Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button onClick={handleReservation}>Book Slot</button>
      </div>
      <div className="reservations">
        <h2>My Reservations</h2>
        <ul>
          {reservations.map((reservation, index) => (
            <li key={index}>
              {reservation.name} - Slot {reservation.slot_id} (
              {reservation.status})
            </li>
          ))}
        </ul>
      </div>
    </main>
  );
};

// Mounting Logic
ReactDOM.createRoot(document.getElementById("root")).render(<App />);
