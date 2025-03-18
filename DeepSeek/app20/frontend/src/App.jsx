import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
  const [locations, setLocations] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch locations from backend
  useEffect(() => {
    fetch('http://localhost:5199/api/locations')
      .then((response) => response.json())
      .then((data) => setLocations(data))
      .catch((error) => console.error('Error fetching locations:', error));
  }, []);

  // Handle search
  const handleSearch = (e) => {
    e.preventDefault();
    fetch(`http://localhost:5199/api/locations/search?q=${searchQuery}`)
      .then((response) => response.json())
      .then((data) => setLocations(data))
      .catch((error) => console.error('Error searching locations:', error));
  };

  return (
    <div className="App">
      <h1>Map Sharing System</h1>
      <form onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Search for a location..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <button type="submit">Search</button>
      </form>
      <div className="map-container">
        {locations.map((location) => (
          <div key={location.id} className="marker">
            <h2>{location.name}</h2>
            <p>Latitude: {location.lat}, Longitude: {location.lng}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

// Mounting logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
