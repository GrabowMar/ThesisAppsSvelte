import { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import { MapContainer, TileLayer, Marker, Popup, Polyline } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "./App.css";

const App = () => {
    const [locations, setLocations] = useState([]);
    const [searchResults, setSearchResults] = useState([]);
    const [center, setCenter] = useState([51.505, -0.09]); // Default center (London)

    // Fetch shared locations from the backend
    useEffect(() => {
        fetch("/api/locations")
            .then((response) => response.json())
            .then((data) => setLocations(data))
            .catch((error) => console.error("Error fetching locations:", error));
    }, []);

    // Handle location search
    const handleSearch = (query) => {
        fetch(`/api/search?q=${query}`)
            .then((response) => response.json())
            .then((data) => setSearchResults(data))
            .catch((error) => console.error("Error searching location:", error));
    };

    // Handle sharing a location
    const handleShareLocation = (lat, lng) => {
        fetch("/api/share", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ lat, lng }),
        })
            .then((response) => response.json())
            .then((data) => setLocations([...locations, data.location]))
            .catch((error) => console.error("Error sharing location:", error));
    };

    return (
        <main className="app">
            <h1>Map Sharing System</h1>
            <div className="controls">
                <input
                    type="text"
                    placeholder="Search location..."
                    onChange={(e) => handleSearch(e.target.value)}
                />
                <button
                    onClick={() => handleShareLocation(center[0], center[1])}
                >
                    Share Current Location
                </button>
            </div>
            <MapContainer center={center} zoom={13} style={{ height: "500px", width: "100%" }}>
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                {locations.map((loc, index) => (
                    <Marker key={index} position={[loc.lat, loc.lng]}>
                        <Popup>Shared Location {index + 1}</Popup>
                    </Marker>
                ))}
                {searchResults.length > 0 && (
                    <>
                        <Marker position={[searchResults[0].lat, searchResults[0].lon]}>
                            <Popup>Search Result</Popup>
                        </Marker>
                        <Polyline
                            positions={[
                                [center[0], center[1]],
                                [searchResults[0].lat, searchResults[0].lon],
                            ]}
                        />
                    </>
                )}
            </MapContainer>
        </main>
    );
};

// Mount the app
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
