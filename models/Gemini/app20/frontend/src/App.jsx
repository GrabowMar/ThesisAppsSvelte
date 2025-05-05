import React, { useState, useEffect, useRef } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet'; // Import Leaflet

function App() {
    // 1. State Management
    const [locations, setLocations] = useState([]);
    const [newLocation, setNewLocation] = useState({ latitude: '', longitude: '', name: '', description: '' });
    const [routes, setRoutes] = useState([]);
    const [newRouteCoordinates, setNewRouteCoordinates] = useState([{ latitude: '', longitude: '' }]);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);

    const mapRef = useRef(null); // Ref to the map instance
    const [mapInstance, setMapInstance] = useState(null);

    // 2. Lifecycle Functions

    useEffect(() => {
        // Initialize the map after the component mounts
        const map = L.map('map').setView([0, 0], 2); // Default view

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);

        setMapInstance(map);
        mapRef.current = map; // Assign map to ref

        // Load existing locations and routes from the backend
        fetchLocations();
        fetchRoutes();

        // Cleanup function to remove the map instance when the component unmounts
        return () => {
            map.remove();
        };
    }, []);

    useEffect(() => {
        // Update markers and routes when locations or routes change
        if (mapInstance) {
            // Clear existing markers
            mapInstance.eachLayer((layer) => {
                if (layer instanceof L.Marker || layer instanceof L.Polyline) {
                    mapInstance.removeLayer(layer);
                }
            });

            // Add new markers
            locations.forEach(location => {
                L.marker([location.latitude, location.longitude]).addTo(mapInstance)
                    .bindPopup(`<b>${location.name}</b><br>${location.description}`);
            });

            // Add new routes
            routes.forEach(route => {
                const latLngs = route.map(coord => [coord[0], coord[1]]);
                L.polyline(latLngs, { color: 'red' }).addTo(mapInstance);
            });
        }
    }, [locations, routes, mapInstance]);

    // 3. Event Handlers
    const handleInputChange = (event) => {
        const { name, value } = event.target;
        setNewLocation(prev => ({ ...prev, [name]: value }));
    };

    const handleAddLocation = async () => {
        try {
            const response = await fetch('/api/locations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newLocation)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to add location');
            }

            const addedLocation = await response.json();
            setLocations(prev => [...prev, addedLocation]);
            setNewLocation({ latitude: '', longitude: '', name: '', description: '' }); // Reset form

            // Update map view to the new location
            mapInstance.setView([addedLocation.latitude, addedLocation.longitude], 10);

        } catch (error) {
            console.error('Error adding location:', error);
            alert(error.message); // Show error to the user
        }
    };

    const handleDeleteLocation = async (id) => {
        try {
            const response = await fetch(`/api/locations/${id}`, { method: 'DELETE' });
            if (!response.ok) {
                throw new Error('Failed to delete location');
            }
            setLocations(prev => prev.filter(loc => loc.id !== id));
        } catch (error) {
            console.error('Error deleting location:', error);
            alert('Failed to delete location');
        }
    };

    const handleRouteCoordinateChange = (index, event) => {
        const { name, value } = event.target;
        const newCoordinates = [...newRouteCoordinates];
        newCoordinates[index][name] = value;
        setNewRouteCoordinates(newCoordinates);
    };

    const handleAddRouteCoordinate = () => {
        setNewRouteCoordinates(prev => [...prev, { latitude: '', longitude: '' }]);
    };

    const handleRemoveRouteCoordinate = (index) => {
        const newCoordinates = [...newRouteCoordinates];
        newCoordinates.splice(index, 1);
        setNewRouteCoordinates(newCoordinates);
    };

    const handleAddRoute = async () => {
        // Validate coordinates before sending to the server
        const validCoordinates = newRouteCoordinates.map(coord => [parseFloat(coord.latitude), parseFloat(coord.longitude)]);

        try {
            const response = await fetch('/api/routes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(validCoordinates)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to add route');
            }

            await response.json();
            fetchRoutes(); // Refresh routes after adding
            setNewRouteCoordinates([{ latitude: '', longitude: '' }]); // Reset route form

        } catch (error) {
            console.error('Error adding route:', error);
            alert(error.message);
        }
    };

    const handleSearch = () => {
        // Basic search implementation (client-side)
        const results = locations.filter(location =>
            location.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            location.description.toLowerCase().includes(searchQuery.toLowerCase())
        );
        setSearchResults(results);

        // If there are search results, focus the map on the first result
        if (results.length > 0 && mapInstance) {
            mapInstance.setView([results[0].latitude, results[0].longitude], 10);
        }
    };

    // 4. API Calls
    const fetchLocations = async () => {
        try {
            const response = await fetch('/api/locations');
            if (!response.ok) {
                throw new Error('Failed to fetch locations');
            }
            const data = await response.json();
            setLocations(data);
        } catch (error) {
            console.error('Error fetching locations:', error);
            alert('Failed to fetch locations. Check console for details.'); // User-friendly error message
        }
    };

    const fetchRoutes = async () => {
        try {
            const response = await fetch('/api/routes');
            if (!response.ok) {
                throw new Error('Failed to fetch routes');
            }
            const data = await response.json();
            setRoutes(data);
        } catch (error) {
            console.error('Error fetching routes:', error);
        }
    };

    // 5. Return Value
    return (
        <div className="app-container">
            <h1>Map Sharing System</h1>

            <div className="location-input-container">
                <h2>Add Location</h2>
                <input
                    type="text"
                    name="name"
                    placeholder="Location Name"
                    value={newLocation.name}
                    onChange={handleInputChange}
                />
                <input
                    type="number"
                    name="latitude"
                    placeholder="Latitude"
                    value={newLocation.latitude}
                    onChange={handleInputChange}
                />
                <input
                    type="number"
                    name="longitude"
                    placeholder="Longitude"
                    value={newLocation.longitude}
                    onChange={handleInputChange}
                />
                <input
                    type="text"
                    name="description"
                    placeholder="Description"
                    value={newLocation.description}
                    onChange={handleInputChange}
                />
                <button onClick={handleAddLocation}>Add Location</button>
            </div>

            <div className="route-input-container">
                <h2>Add Route</h2>
                {newRouteCoordinates.map((coord, index) => (
                    <div key={index} className="coordinate-input">
                        <input
                            type="number"
                            name="latitude"
                            placeholder={`Latitude ${index + 1}`}
                            value={coord.latitude}
                            onChange={(event) => handleRouteCoordinateChange(index, event)}
                        />
                        <input
                            type="number"
                            name="longitude"
                            placeholder={`Longitude ${index + 1}`}
                            value={coord.longitude}
                            onChange={(event) => handleRouteCoordinateChange(index, event)}
                        />
                        {newRouteCoordinates.length > 1 && (
                            <button type="button" onClick={() => handleRemoveRouteCoordinate(index)}>
                                Remove
                            </button>
                        )}
                    </div>
                ))}
                <button type="button" onClick={handleAddRouteCoordinate}>Add Coordinate</button>
                <button onClick={handleAddRoute}>Add Route</button>
            </div>

            <div className="search-container">
                <h2>Search Locations</h2>
                <input
                    type="text"
                    placeholder="Search by name or description"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
                <button onClick={handleSearch}>Search</button>

                {searchResults.length > 0 && (
                    <div className="search-results">
                        <h3>Search Results</h3>
                        <ul>
                            {searchResults.map(result => (
                                <li key={result.id}>
                                    {result.name} - {result.description}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>

            <div id="map" className="map-container"></div>

            <div className="locations-list">
                <h2>Locations</h2>
                <ul>
                    {locations.map(location => (
                        <li key={location.id}>
                            {location.name} ({location.latitude}, {location.longitude})
                            <button onClick={() => handleDeleteLocation(location.id)}>Delete</button>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<React.StrictMode><App /></React.StrictMode>);

export default App;
