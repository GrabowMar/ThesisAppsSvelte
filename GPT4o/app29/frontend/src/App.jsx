// app/frontend/src/App.jsx
import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import "./App.css";

const App = () => {
  const [events, setEvents] = useState([]);
  const [eventForm, setEventForm] = useState({
    name: "",
    date: "",
    budget: "",
  });
  const [rsvpForm, setRsvpForm] = useState({
    eventId: "",
    guestName: "",
  });

  // Fetch events from the backend
  useEffect(() => {
    fetch("/api/events")
      .then((res) => res.json())
      .then((data) => {
        setEvents(data);
      })
      .catch((err) => console.error(err));
  }, []);

  // Event handlers
  const handleEventFormChange = (e) => {
    setEventForm({ ...eventForm, [e.target.name]: e.target.value });
  };

  const handleRsvpFormChange = (e) => {
    setRsvpForm({ ...rsvpForm, [e.target.name]: e.target.value });
  };

  const createEvent = () => {
    fetch("/api/events", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(eventForm),
    })
      .then((res) => res.json())
      .then((data) => setEvents([...events, data]))
      .catch((err) => console.error(err));
  };

  const submitRsvp = () => {
    fetch("/api/rsvps", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(rsvpForm),
    })
      .then((res) => res.json())
      .then(() => {
        alert("RSVP submitted!");
        setRsvpForm({ eventId: "", guestName: "" }); // Reset the form
      })
      .catch((err) => console.error(err));
  };

  // Render UI
  return (
    <div>
      <h1>Event Planning Platform</h1>
      <div>
        <h2>Create New Event</h2>
        <input
          type="text"
          name="name"
          value={eventForm.name}
          placeholder="Event Name"
          onChange={handleEventFormChange}
        />
        <input
          type="date"
          name="date"
          value={eventForm.date}
          onChange={handleEventFormChange}
        />
        <input
          type="text"
          name="budget"
          value={eventForm.budget}
          placeholder="Budget"
          onChange={handleEventFormChange}
        />
        <button onClick={createEvent}>Create Event</button>
      </div>

      <div>
        <h2>Events</h2>
        <ul>
          {events.map((event) => (
            <li key={event.id}>
              {event.name} - {event.date} - ${event.budget}
              <ul>
                {event.guests.map((guest, index) => (
                  <li key={index}>{guest}</li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      </div>

      <div>
        <h2>RSVP</h2>
        <select
          name="eventId"
          value={rsvpForm.eventId}
          onChange={handleRsvpFormChange}
        >
          <option value="">Select Event</option>
          {events.map((event) => (
            <option value={event.id} key={event.id}>
              {event.name}
            </option>
          ))}
        </select>
        <input
          type="text"
          name="guestName"
          value={rsvpForm.guestName}
          placeholder="Guest Name"
          onChange={handleRsvpFormChange}
        />
        <button onClick={submitRsvp}>Submit RSVP</button>
      </div>
    </div>
  );
};

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
