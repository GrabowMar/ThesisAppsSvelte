// 1. Imports
import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import axios from 'axios';

// 2. State Management
const [locations, setLocations] = useState([]);
const [name, setName] = useState('');
const [location, setLocation] = useState([45.5236, -122.6750]);
const [map, setMap] = useState(null);

// 3. Lifecycle Functions
useEffect(() => {
    axios.get('/api/locations')
        .then(response => {
            setLocations(response.data);
        })
        .catch(error => {
            console.error(error);
        });
}, []);

// 4. Event Handlers
const handleSubmit = (event) => {
    event.preventDefault();
    const newLocation = { name, location };
    axios.post('/api/locations', newLocation)
        .then(response => {
            setLocations([...locations, response.data]);
            setName('');
            setLocation([45.5236, -122.6750]);
        })
        .catch(error => {
            console.error(error);
        });
};

const handleMapChange = (event) => {
    setMap(event.target.value);
};

// 5. API Calls
const fetchMap = () => {
    axios.get('/api/map')
        .then(response => {
            setMap(response.data);
        })
        .catch(error => {
            console.error(error);
        });
};

// UI Components
const App = () => {
    return (
        <div>
            <h1>Map Sharing Application</h1>
            <form onSubmit={handleSubmit}>
                <label>
                    Name:
                    <input type="text" value={name} onChange={(event) => setName(event.target.value)} />
                </label>
                <label>
                    Location:
                    <input type="text" value={location} onChange={(event) => setLocation(event.target.value)} />
                </label>
                <button type="submit">Create Location</button>
            </form>
            <button onClick={fetchMap}>Fetch Map</button>
            {map && <div dangerouslySetInnerHTML={{ __html: map }} />}
        </div>
    );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
