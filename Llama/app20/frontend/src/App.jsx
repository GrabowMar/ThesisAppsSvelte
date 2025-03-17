import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import axios from 'axios';

function App() {
    const [locations, setLocations] = useState({});
    const [marker, setMarker] = useState('');
    const [route, setRoute] = useState('');
    const [latitude, setLatitude] = useState('');
    const [longitude, setLongitude] = useState('');
    const [query, setQuery] = useState('');

    useEffect(() => {
        axios.get('http://localhost:5039/locations')
            .then(response => {
                setLocations(response.data);
            })
            .catch(error => {
                console.error(error);
            });
    }, []);

    const handleShareLocation = (event) => {
        event.preventDefault();
        axios.post('http://localhost:5039/share-location', {
            latitude: latitude,
            longitude: longitude,
            marker: marker,
            route: route
        })
            .then(response => {
                console.log(response.data);
            })
            .catch(error => {
                console.error(error);
            });
    };

    const handleSearchLocations = (event) => {
        event.preventDefault();
        axios.post('http://localhost:5039/search-locations', {
            query: query
        })
            .then(response => {
                console.log(response.data);
            })
            .catch(error => {
                console.error(error);
            });
    };

    return (
        <div>
            <h1>Map Sharing Application</h1>
            <form onSubmit={handleShareLocation}>
                <label>
                    Marker:
                    <input type="text" value={marker} onChange={(event) => setMarker(event.target.value)} />
                </label>
                <br />
                <label>
                    Route:
                    <input type="text" value={route} onChange={(event) => setRoute(event.target.value)} />
                </label>
                <br />
                <label>
                    Latitude:
                    <input type="text" value={latitude} onChange={(event) => setLatitude(event.target.value)} />
                </label>
                <br />
                <label>
                    Longitude:
                    <input type="text" value={longitude} onChange={(event) => setLongitude(event.target.value)} />
                </label>
                <br />
                <button type="submit">Share Location</button>
            </form>
            <form onSubmit={handleSearchLocations}>
                <label>
                    Query:
                    <input type="text" value={query} onChange={(event) => setQuery(event.target.value)} />
                </label>
                <br />
                <button type="submit">Search Locations</button>
            </form>
            <h2>Shared Locations:</h2>
            <ul>
                {Object.keys(locations).map((locationId) => (
                    <li key={locationId}>
                        Marker: {locations[locationId].marker}, Route: {locations[locationId].route}, Latitude: {locations[locationId].latitude}, Longitude: {locations[locationId].longitude}
                    </li>
                ))}
            </ul>
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
