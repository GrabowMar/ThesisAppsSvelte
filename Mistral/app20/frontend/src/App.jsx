import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import axios from 'axios';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './App.css';

const App = () => {
    const [locations, setLocations] = useState([]);
    const [newLocation, setNewLocation] = useState({ name: '', lat: '', lng: '', description: '' });

    useEffect(() => {
        axios.get('http://localhost:5119/locations')
            .then(response => setLocations(response.data))
            .catch(error => console.error("Error fetching locations:", error));
    }, []);

    const addLocation = () => {
        axios.post('http://localhost:5119/locations', newLocation)
            .then(response => {
                setLocations([...locations, response.data]);
                setNewLocation({ name: '', lat: '', lng: '', description: '' });
            })
            .catch(error => console.error("Error adding location:", error));
    };

    return (
        <Router>
            <div>
                <nav>
                    <ul>
                        <li><Link to="/">Home</Link></li>
                        <li><Link to="/map">Map</Link></li>
                        <li><Link to="/add-location">Add Location</Link></li>
                    </ul>
                </nav>

                <Routes>
                    <Route path="/" element={<Home locations={locations} />} />
                    <Route path="/map" element={<MapView locations={locations} />} />
                    <Route path="/add-location" element={<AddLocationForm addLocation={addLocation} newLocation={newLocation} setNewLocation={setNewLocation} />} />
                </Routes>
            </div>
        </Router>
    );
};

const Home = ({ locations }) => (
    <div>
        <h1>Locations</h1>
        <ul>
            {locations.map(location => (
                <li key={location.id}>{location.name} - {location.description}</li>
            ))}
        </ul>
    </div>
);

const MapView = ({ locations }) => (
    <MapContainer center={[34.0522, -118.2437]} zoom={5} style={{ height: "100vh", width: "100%" }}>
        <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {locations.map(location => (
            <Marker key={location.id} position={[location.lat, location.lng]}>
                <Popup>
                    {location.name} <br /> {location.description}
                </Popup>
            </Marker>
        ))}
    </MapContainer>
);

const AddLocationForm = ({ addLocation, newLocation, setNewLocation }) => (
    <div>
        <h1>Add Location</h1>
        <form onSubmit={(e) => { e.preventDefault(); addLocation(); }}>
            <input type="text" placeholder="Name" value={newLocation.name} onChange={(e) => setNewLocation({ ...newLocation, name: e.target.value })} />
            <input type="text" placeholder="Latitude" value={newLocation.lat} onChange={(e) => setNewLocation({ ...newLocation, lat: e.target.value })} />
            <input type="text" placeholder="Longitude" value={newLocation.lng} onChange={(e) => setNewLocation({ ...newLocation, lng: e.target.value })} />
            <input type="text" placeholder="Description" value={newLocation.description} onChange={(e) => setNewLocation({ ...newLocation, description: e.target.value })} />
            <button type="submit">Add Location</button>
        </form>
    </div>
);

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
