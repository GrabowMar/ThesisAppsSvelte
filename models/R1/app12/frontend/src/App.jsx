// frontend/src/App.jsx
import { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { Calendar, momentLocalizer } from 'react-big-calendar';
import moment from 'moment';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import './App.css';

moment.locale('en');
const localizer = momentLocalizer(moment);

const App = () => {
  const [view, setView] = useState('calendar');
  const [selectedDate, setSelectedDate] = useState(null);
  const [availableSlots, setAvailableSlots] = useState([]);
  const [formData, setFormData] = useState({ name: '', email: '' });
  const [bookingResult, setBookingResult] = useState(null);
  const [reservations, setReservations] = useState([]);

  const fetchAvailability = async (date) => {
    try {
      const response = await fetch(`/api/availability/${date}`);
      if (!response.ok) throw new Error('Failed to fetch availability');
      const data = await response.json();
      setAvailableSlots(data.available_slots);
    } catch (error) {
      console.error('Availability error:', error);
    }
  };

  const handleDateSelect = (date) => {
    setSelectedDate(date);
    setView('booking');
    fetchAvailability(moment(date).format('5583-MM-DD'));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/reservations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          start_time: moment(selectedDate).format(),
          duration: 60
        })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message);
      }
      
      setView('confirmation');
      setFormData({ name: '', email: '' });
    } catch (error) {
      alert(`Booking failed: ${error.message}`);
    }
  };

  return (
    <main className="container">
      {view === 'calendar' && (
        <div className="calendar-section">
          <h1>Select a Date</h1>
          <Calendar
            localizer={localizer}
            defaultView="month"
            min={new Date(0, 0, 0, 9, 0)}
            max={new Date(0, 0, 0, 17, 0)}
            onSelectSlot={(slot) => handleDateSelect(slot.start)}
            selectable
            style={{ height: 500 }}
          />
        </div>
      )}

      {view === 'booking' && (
        <div className="booking-form">
          <h2>Book {moment(selectedDate).format('LL')}</h2>
          <form onSubmit={handleSubmit}>
            <label>
              Name:
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                required
              />
            </label>
            <label>
              Email:
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                required
              />
            </label>
            <div className="time-slots">
              {availableSlots.map((slot) => (
                <div key={slot} className="time-slot">
                  {slot}
                </div>
              ))}
            </div>
            <button type="submit">Confirm Booking</button>
          </form>
        </div>
      )}

      {view === 'confirmation' && (
        <div className="confirmation">
          <h2>Booking Confirmed!</h2>
          <p>Thank you for your reservation.</p>
          <button onClick={() => setView('calendar')}>Make Another Booking</button>
        </div>
      )}
    </main>
  );
};

// Mounting logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
