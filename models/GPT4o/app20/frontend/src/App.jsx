import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// Map Component
function MapSharingApp() {
  const [locations, setLocations] = useState([]);
  const [newLocation, setNewLocation] = useState({ name: '', lat: '', lng: '' });
  const [route, setRoute] = useState({ origin: '', destination: '' });

  // Fetch locations on load
  useEffect(() => {
    fetch('/api/locations')
      .then((response) => response.json())
      .then((data) => setLocations(data.data))
      .catch((error) => console.error("Error fetching locations:", error));
  }, []);

  // Add new location
  const handleAddLocation = (event) => {
    event.preventDefault();

    // Simple validation
    if (!newLocation.name || !newLocation.lat || !newLocation.lng) {
      alert('Please fill in all input fields');
      return;
    }

    fetch('/api/locations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newLocation)
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          setLocations([...locations, data.data]);
          setNewLocation({ name: '', lat: '', lng: '' });
        } else {
          alert(data.message || "Failed to add location");
        }
      })
      .catch((error) => console.error("Error adding location:", error));
  };

  return (
    <div className="app">
      <header>
        <h1>Map Sharing Application</h1>
      </header>
      <main>
        {/* Location Form */}
        <form onSubmit={handleAddLocation} className="location-form">
          <input
            type="text"
            placeholder="Name"
            value={newLocation.name}
            onChange={(e) => setNewLocation({ ...newLocation, name: e.target.value })}
          />
          <input
            type="number"
            placeholder="Latitude"
            value={newLocation.lat}
            onChange={(e) => setNewLocation({ ...newLocation, lat: e.target.value })}
          />
          <input
            type="number"
            placeholder="Longitude"
            value={newLocation.lng}
            onChange={(e) => setNewLocation({ ...newLocation, lng: e.target.value })}
          />
          <button type="submit">Add Location</button>
        </form>

        {/* Display Locations */}
        <section className="locations">
          <h2>Shared Locations</h2>
          <ul>
            {locations.map((location) => (
              <li key={location.id}>
                {location.name} (Lat: {location.lat}, Lng: {location.lng})
              </li>
            ))}
          </ul>
        </section>
      </main>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<MapSharingApp />);
