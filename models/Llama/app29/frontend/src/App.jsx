import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [events, setEvents] = useState([]);
  const [eventName, setEventName] = useState('');
  const [eventDate, setEventDate] = useState('');
  const [eventLocation, setEventLocation] = useState('');
  const [guestName, setGuestName] = useState('');
  const [guestEmail, setGuestEmail] = useState('');
  const [selectedEventId, setSelectedEventId] = useState(null);

  useEffect(() => {
    fetch('/api/events')
      .then(response => response.json())
      .then(data => setEvents(Object.values(data)));
  }, []);

  const handleCreateEvent = () => {
    fetch('/api/events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: eventName, date: eventDate, location: eventLocation }),
    })
      .then(response => response.json())
      .then(data => {
        setEvents([...events, { id: data.event_id, name: eventName, date: eventDate, location: eventLocation }]);
        setEventName('');
        setEventDate('');
        setEventLocation('');
      });
  };

  const handleAddGuest = () => {
    if (selectedEventId) {
      fetch(`/api/events/${selectedEventId}/guests`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: guestName, email: guestEmail }),
      })
        .then(response => response.json())
        .then(data => {
          console.log(`Guest added with ID ${data.guest_id}`);
          setGuestName('');
          setGuestEmail('');
        });
    }
  };

  const handleSelectEvent = (eventId) => {
    setSelectedEventId(eventId);
  };

  return (
    <div className="App">
      <h1>Event Planning Platform</h1>
      <section>
        <h2>Create Event</h2>
        <input type="text" value={eventName} onChange={(e) => setEventName(e.target.value)} placeholder="Event Name" />
        <input type="date" value={eventDate} onChange={(e) => setEventDate(e.target.value)} placeholder="Event Date" />
        <input type="text" value={eventLocation} onChange={(e) => setEventLocation(e.target.value)} placeholder="Event Location" />
        <button onClick={handleCreateEvent}>Create Event</button>
      </section>
      <section>
        <h2>Events</h2>
        <ul>
          {events.map((event) => (
            <li key={event.id}>
              <span>{event.name} on {event.date} at {event.location}</span>
              <button onClick={() => handleSelectEvent(event.id)}>Select</button>
            </li>
          ))}
        </ul>
      </section>
      {selectedEventId && (
        <section>
          <h2>Add Guest to Event {selectedEventId}</h2>
          <input type="text" value={guestName} onChange={(e) => setGuestName(e.target.value)} placeholder="Guest Name" />
          <input type="email" value={guestEmail} onChange={(e) => setGuestEmail(e.target.value)} placeholder="Guest Email" />
          <button onClick={handleAddGuest}>Add Guest</button>
        </section>
      )}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
