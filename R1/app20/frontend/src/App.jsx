import { useState, useEffect, useCallback } from 'react';
import ReactDOM from 'react-dom/client';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import './App.css';

// Fix leaflet marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const MapInterface = () => {
  const [locations, setLocations] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [newLocation, setNewLocation] = useState({ name: '', lat: null, lng: null });

  const fetchLocations = useCallback(async (query = '') => {
    try {
      const url = query ? `/api/locations/search?q=${query}` : '/api/locations';
      const response = await fetch(url);
      const data = await response.json();
      setLocations(data);
    } catch (error) {
      console.error('Error fetching locations:', error);
    }
  }, []);

  useEffect(() => {
    fetchLocations(searchTerm);
  }, [searchTerm, fetchLocations]);

  const handleMapClick = useCallback((e) => {
    setNewLocation(prev => ({ ...prev, lat: e.latlng.lat, lng: e.latlng.lng }));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/locations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newLocation.name,
          latitude: newLocation.lat,
          longitude: newLocation.lng
        })
      });
      if (response.ok) {
        fetchLocations();
        setNewLocation({ name: '', lat: null, lng: null });
      }
    } catch (error) {
      console.error('Error saving location:', error);
    }
  };

  const MapClickHandler = () => {
    useMapEvents({ click: handleMapClick });
    return null;
  };

  return (
    <div className="app-container">
      <nav className="navbar">
        <Link to="/" className="brand">MapShare</Link>
        <div className="search-container">
          <input
            type="text"
            placeholder="Search locations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </nav>

      <div className="map-container">
        <MapContainer center={[40.7128, -74.0060]} zoom={13} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          <MapClickHandler />
          {locations?.map(loc => (
            <Marker key={loc.id} position={[loc.latitude, loc.longitude]}>
              <Popup>{loc.name}</Popup>
            </Marker>
          ))}
          {newLocation.lat && (
            <Marker position={[newLocation.lat, newLocation.lng]}>
              <Popup>New Location</Popup>
            </Marker>
          )}
        </MapContainer>
      </div>

      <div className="form-container">
        <h3>Share New Location</h3>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Location name"
            required
            value={newLocation.name}
            onChange={(e) => setNewLocation(prev => ({ ...prev, name: e.target.value }))}
          />
          <button type="submit" disabled={!newLocation.name || !newLocation.lat}>
            Save Location
          </button>
        </form>
        {newLocation.lat && (
          <p>Selected coordinates: {newLocation.lat.toFixed(4)}, {newLocation.lng.toFixed(4)}</p>
        )}
      </div>
    </div>
  );
};

const App = () => (
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<MapInterface />} />
    </Routes>
  </BrowserRouter>
);

// Mounting logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
