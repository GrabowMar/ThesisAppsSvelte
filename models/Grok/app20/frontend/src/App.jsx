import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import { GoogleMap, LoadScript, Marker, DirectionsRenderer } from '@react-google-maps/api';
import axios from 'axios';

// Set up API base URL
const API_BASE_URL = 'http://localhost:5519/api';

// Map styles
const mapStyles = {
  height: '80vh',
  width: '100%',
};

// Map center (default to New York)
const defaultCenter = {
  lat: 40.7128,
  lng: -74.0060
};

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [locations, setLocations] = useState([]);
  const [newLocation, setNewLocation] = useState('');
  const [mapCenter, setMapCenter] = useState(defaultCenter);
  const [directions, setDirections] = useState(null);

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('token');
    if (token) {
      setIsLoggedIn(true);
    }
  }, []);

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API_BASE_URL}/login`, { username, password });
      localStorage.setItem('token', response.data.access_token);
      setIsLoggedIn(true);
      setUsername('');
      setPassword('');
    } catch (error) {
      console.error('Login failed:', error);
      alert('Invalid credentials');
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_BASE_URL}/register`, { username, password });
      alert('User registered successfully. Please log in.');
    } catch (error) {
      console.error('Registration failed:', error);
      alert('Registration failed. Username may already exist.');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsLoggedIn(false);
  };

  const handleAddLocation = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/locations`, { location: newLocation }, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setLocations([...locations, response.data]);
      setNewLocation('');
    } catch (error) {
      console.error('Failed to add location:', error);
      alert('Failed to add location. Please try again.');
    }
  };

  const handleDeleteLocation = async (locationId) => {
    try {
      await axios.delete(`${API_BASE_URL}/locations/${locationId}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setLocations(locations.filter(loc => loc.id !== locationId));
    } catch (error) {
      console.error('Failed to delete location:', error);
      alert('Failed to delete location. Please try again.');
    }
  };

  const handleSearchLocation = async () => {
    try {
      const response = await axios.get(`https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(newLocation)}&key=YOUR_GOOGLE_MAPS_API_KEY`);
      if (response.data.results.length > 0) {
        const { lat, lng } = response.data.results[0].geometry.location;
        setMapCenter({ lat, lng });
      } else {
        alert('Location not found');
      }
    } catch (error) {
      console.error('Failed to search location:', error);
      alert('Failed to search location. Please try again.');
    }
  };

  const handleCalculateRoute = async () => {
    if (locations.length < 2) {
      alert('Please add at least two locations to calculate a route');
      return;
    }

    const waypoints = locations.slice(1, -1).map(loc => ({
      location: { lat: loc.latitude, lng: loc.longitude },
      stopover: true
    }));

    const directionsService = new window.google.maps.DirectionsService();
    directionsService.route({
      origin: { lat: locations[0].latitude, lng: locations[0].longitude },
      destination: { lat: locations[locations.length - 1].latitude, lng: locations[locations.length - 1].longitude },
      waypoints: waypoints,
      travelMode: window.google.maps.TravelMode.DRIVING
    }, (result, status) => {
      if (status === window.google.maps.DirectionsStatus.OK) {
        setDirections(result);
      } else {
        console.error('Directions request failed:', status);
        alert('Failed to calculate route. Please try again.');
      }
    });
  };

  const LoginForm = () => (
    <form onSubmit={handleLogin}>
      <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" required />
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" required />
      <button type="submit">Login</button>
      <button onClick={handleRegister}>Register</button>
    </form>
  );

  const Dashboard = () => (
    <div>
      <h2>Welcome, {getJwtIdentity()}!</h2>
      <button onClick={handleLogout}>Logout</button>
      <input type="text" value={newLocation} onChange={(e) => setNewLocation(e.target.value)} placeholder="Enter a location" />
      <button onClick={handleAddLocation}>Add Location</button>
      <button onClick={handleSearchLocation}>Search Location</button>
      <button onClick={handleCalculateRoute}>Calculate Route</button>
      <ul>
        {locations.map(loc => (
          <li key={loc.id}>
            {loc.location} - 
            <button onClick={() => handleDeleteLocation(loc.id)}>Delete</button>
          </li>
        ))}
      </ul>
      <LoadScript googleMapsApiKey="YOUR_GOOGLE_MAPS_API_KEY">
        <GoogleMap
          mapContainerStyle={mapStyles}
          center={mapCenter}
          zoom={13}
        >
          {locations.map(loc => (
            <Marker key={loc.id} position={{ lat: loc.latitude, lng: loc.longitude }} />
          ))}
          {directions && <DirectionsRenderer directions={directions} />}
        </GoogleMap>
      </LoadScript>
    </div>
  );

  const getJwtIdentity = () => {
    const token = localStorage.getItem('token');
    if (token) {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.sub;
    }
    return null;
  };

  return (
    <Router>
      <Routes>
        <Route path="/login" element={isLoggedIn ? <Navigate to="/dashboard" /> : <LoginForm />} />
        <Route path="/dashboard" element={isLoggedIn ? <Dashboard /> : <Navigate to="/login" />} />
        <Route path="/" element={isLoggedIn ? <Navigate to="/dashboard" /> : <Navigate to="/login" />} />
      </Routes>
    </Router>
  );
}

// Mounting logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
