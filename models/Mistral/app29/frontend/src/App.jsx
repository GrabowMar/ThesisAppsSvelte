// app/frontend/src/App.jsx

import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import './App.css';

// Components
const EventList = () => {
    const [events, setEvents] = useState([]);

    useEffect(() => {
        fetch('/api/events')
            .then(response => response.json())
            .then(data => setEvents(data))
            .catch(error => console.error('Error fetching events:', error));
    }, []);

    return (
        <div>
            <h2>Events</h2>
            <ul>
                {events.map(event => (
                    <li key={event.id}>
                        <Link to={`/events/${event.id}`}>{event.name}</Link>
                    </li>
                ))}
            </ul>
        </div>
    );
};

const EventDetail = () => {
    const { eventId } = useParams();
    const [event, setEvent] = useState(null);

    useEffect(() => {
        fetch(`/api/events/${eventId}`)
            .then(response => response.json())
            .then(data => setEvent(data))
            .catch(error => console.error('Error fetching event:', error));
    }, [eventId]);

    if (!event) return <div>Loading...</div>;

    return (
        <div>
            <h2>{event.name}</h2>
            <p>{event.description}</p>
            {/* Add more event details here */}
        </div>
    );
};

const App = () => {
    return (
        <Router>
            <div>
                <nav>
                    <Link to="/">Home</Link>
                    <Link to="/events">Events</Link>
                </nav>
                <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/events" element={<EventList />} />
                    <Route path="/events/:eventId" element={<EventDetail />} />
                </Routes>
            </div>
        </Router>
    );
};

const Home = () => <h2>Welcome to the Event Planning Platform</h2>;

// Mounting Logic
const rootElement = document.getElementById('root');
if (rootElement) {
    ReactDOM.createRoot(rootElement).render(<App />);
}
