import React, { useState, useEffect, useRef } from 'react';
import ReactDOM from 'react-dom/client';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './App.css';

// Fix Leaflet marker icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png'
});

// API Service
const API_BASE_URL = 'http://localhost:5359/api';

const api = {
  register: async (userData) => {
    const response = await fetch(`${API_BASE_URL}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(userData)
    });
    return response.json();
  },

  login: async (credentials) => {
    const response = await fetch(`${API_BASE_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(credentials)
    });
    return response.json();
  },

  logout: async () => {
    const response = await fetch(`${API_BASE_URL}/logout`, {
      method: 'POST',
      credentials: 'include'
    });
    return response.json();
  },

  getCurrentUser: async () => {
    const response = await fetch(`${API_BASE_URL}/user`, { credentials: 'include' });
    if (response.status === 401) return null;
    return response.json();
  },

  getMaps: async () => {
    const response = await fetch(`${API_BASE_URL}/maps`, { credentials: 'include' });
    return response.json();
  },

  getMap: async (mapId) => {
    const response = await fetch(`${API_BASE_URL}/maps/${mapId}`, { credentials: 'include' });
    return response.json();
  },

  createMap: async (mapData) => {
    const response = await fetch(`${API_BASE_URL}/maps`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(mapData)
    });
    return response.json();
  },

  updateMap: async (mapId, mapData) => {
    const response = await fetch(`${API_BASE_URL}/maps/${mapId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(mapData)
    });
    return response.json();
  },

  deleteMap: async (mapId) => {
    const response = await fetch(`${API_BASE_URL}/maps/${mapId}`, {
      method: 'DELETE',
      credentials: 'include'
    });
    return response.json();
  },

  addMarker: async (mapId, markerData) => {
    const response = await fetch(`${API_BASE_URL}/maps/${mapId}/markers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(markerData)
    });
    return response.json();
  },

  deleteMarker: async (markerId) => {
    const response = await fetch(`${API_BASE_URL}/markers/${markerId}`, {
      method: 'DELETE',
      credentials: 'include'
    });
    return response.json();
  },

  addRoute: async (mapId, routeData) => {
    const response = await fetch(`${API_BASE_URL}/maps/${mapId}/routes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(routeData)
    });
    return response.json();
  },

  deleteRoute: async (routeId) => {
    const response = await fetch(`${API_BASE_URL}/routes/${routeId}`, {
      method: 'DELETE',
      credentials: 'include'
    });
    return response.json();
  },
};

// Custom Hook for Search
function useLocationSearch() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Debounce search to avoid too many API calls
  useEffect(() => {
    if (searchQuery.length < 3) {
      setSearchResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setIsLoading(true);
      try {
        const response = await fetch(
          `https://nominatim.openstreetmap.org/search?format=json&q=${searchQuery}&limit=5`
        );
        const data = await response.json();
        setSearchResults(data);
        setError(null);
      } catch (err) {
        setError('Error searching for location');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  return { searchQuery, setSearchQuery, searchResults, isLoading, error };
}

// Component for adding markers when clicking on the map
function MapClickHandler({ onMapClick }) {
  useMapEvents({
    click: (e) => {
      onMapClick(e.latlng);
    },
  });
  return null;
}

// Component for creating a new route
function RouteCreator({ isCreating, onPositionAdd, onFinish }) {
  const [positions, setPositions] = useState([]);

  useMapEvents({
    click: (e) => {
      if (isCreating) {
        const newPosition = [e.latlng.lat, e.latlng.lng];
        setPositions(prev => [...prev, newPosition]);
        onPositionAdd(newPosition);
      }
    },
  });

  useEffect(() => {
    if (!isCreating) {
      onFinish(positions);
      setPositions([]);
    }
  }, [isCreating]);

  return (
    isCreating && positions.length > 1 ? (
      <Polyline positions={positions} color="red" dashArray="5, 5" />
    ) : null
  );
}

// Auth Components
function Register({ onRegister, onSwitchToLogin }) {
  const [formData, setFormData] = useState({ username: '', email: '', password: '' });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.register(formData);
      if (response.error) {
        setError(response.error);
      } else {
        onRegister(response.user);
      }
    } catch (err) {
      setError('Registration failed. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <h2>Create Account</h2>
      {error && <div className="error-message">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            type="text"
            id="username"
            name="username"
            value={formData.username}
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            required
          />
        </div>
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Registering...' : 'Register'}
        </button>
      </form>
      <p>
        Already have an account?{' '}
        <button className="link-button" onClick={onSwitchToLogin}>
          Log in
        </button>
      </p>
    </div>
  );
}

function Login({ onLogin, onSwitchToRegister }) {
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.login(formData);
      if (response.error) {
        setError(response.error);
      } else {
        onLogin(response.user);
      }
    } catch (err) {
      setError('Login failed. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <h2>Login</h2>
      {error && <div className="error-message">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            type="text"
            id="username"
            name="username"
            value={formData.username}
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            required
          />
        </div>
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
      <p>
        Don't have an account?{' '}
        <button className="link-button" onClick={onSwitchToRegister}>
          Register
        </button>
      </p>
    </div>
  );
}

// Map List Components
function MapsList({ maps, onMapSelect, onCreateMap, isLoading }) {
  return (
    <div className="maps-list">
      <div className="maps-header">
        <h2>Your Maps</h2>
        <button className="btn btn-primary" onClick={onCreateMap}>
          Create New Map
        </button>
      </div>
      {isLoading ? (
        <div className="loading">Loading maps...</div>
      ) : (
        <div className="maps-grid">
          {maps.user_maps && maps.user_maps.length > 0 ? (
            maps.user_maps.map((map) => (
              <div key={map.id} className="map-card" onClick={() => onMapSelect(map.id)}>
                <h3>{map.title}</h3>
                <p>{map.description || 'No description'}</p>
                <div className="map-meta">
                  <span className={`visibility-badge ${map.is_public ? 'public' : 'private'}`}>
                    {map.is_public ? 'Public' : 'Private'}
                  </span>
                  <span className="date">{new Date(map.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))
          ) : (
            <p className="no-maps">You haven't created any maps yet.</p>
          )}
        </div>
      )}

      {maps.public_maps && maps.public_maps.length > 0 && (
        <>
          <h2>Public Maps</h2>
          <div className="maps-grid">
            {maps.public_maps.map((map) => (
              <div key={map.id} className="map-card" onClick={() => onMapSelect(map.id)}>
                <h3>{map.title}</h3>
                <p>{map.description || 'No description'}</p>
                <div className="map-meta">
                  <span className="owner">By {map.owner}</span>
                  <span className="date">{new Date(map.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
        </div>
  );
}

function CreateMapForm({ onSubmit, onCancel }) {
  const [formData, setFormData] = useState({ title: '', description: '', is_public: true });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setFormData({ ...formData, [e.target.name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.createMap(formData);
      if (response.error) {
        setError(response.error);
      } else {
        onSubmit(response.map);
      }
    } catch (err) {
      setError('Failed to create map. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="create-map-form">
      <h2>Create New Map</h2>
      {error && <div className="error-message">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="title">Title</label>
          <input
            type="text"
            id="title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
          ></textarea>
        </div>
        <div className="form-group checkbox">
          <input
            type="checkbox"
            id="is_public"
            name="is_public"
            checked={formData.is_public}
            onChange={handleChange}
          />
          <label htmlFor="is_public">Make this map public</label>
        </div>
        <div className="form-buttons">
          <button type="button" className="btn btn-secondary" onClick={onCancel}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Creating...' : 'Create Map'}
          </button>
        </div>
      </form>
    </div>
  );
}

// Map Detail Components
function MapDetail({
  map,
  isOwner,
  onBack,
  onDelete,
  onEdit,
  onAddMarker,
  onDeleteMarker,
  onAddRoute,
  onDeleteRoute
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [isAddingMarker, setIsAddingMarker] = useState(false);
  const [isCreatingRoute, setIsCreatingRoute] = useState(false);
  const [newMarkerPosition, setNewMarkerPosition] = useState(null);
  const [newMarkerForm, setNewMarkerForm] = useState({ title: '', description: '', color: 'red' });
  const [routePositions, setRoutePositions] = useState([]);
  const [newRouteForm, setNewRouteForm] = useState({ title: '', description: '', color: 'blue' });
  const [editForm, setEditForm] = useState({
    title: map.title,
    description: map.description,
    is_public: map.is_public
  });
  const [mapCenter, setMapCenter] = useState([51.505, -0.09]); // Default center
  const mapRef = useRef(null);

  const { searchQuery, setSearchQuery, searchResults, isLoading: isSearchLoading } = useLocationSearch();

  useEffect(() => {
    // Center the map on the first marker if available
    if (map.markers && map.markers.length > 0) {
      setMapCenter([map.markers[0].latitude, map.markers[0].longitude]);
    }
  }, [map]);

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    try {
      await onEdit(map.id, editForm);
      setIsEditing(false);
    } catch (err) {
      console.error('Failed to update map', err);
    }
  };

  const handleAddMarkerClick = () => {
    setIsAddingMarker(true);
    setIsCreatingRoute(false);
  };

  const handleMapClick = (latlng) => {
    if (isAddingMarker) {
      setNewMarkerPosition({ lat: latlng.lat, lng: latlng.lng });
    }
  };

  const handleMarkerFormChange = (e) => {
    setNewMarkerForm({ ...newMarkerForm, [e.target.name]: e.target.value });
  };

  const handleMarkerFormSubmit = async (e) => {
    e.preventDefault();
    if (!newMarkerPosition) return;

    const markerData = {
      ...newMarkerForm,
      latitude: newMarkerPosition.lat,
      longitude: newMarkerPosition.lng
    };

    try {
      await onAddMarker(map.id, markerData);
      setNewMarkerPosition(null);
      setNewMarkerForm({ title: '', description: '', color: 'red' });
      setIsAddingMarker(false);
    } catch (err) {
      console.error('Failed to add marker', err);
    }
  };

  const handleStartRouteCreation = () => {
    setIsCreatingRoute(true);
    setIsAddingMarker(false);
    setRoutePositions([]);
  };

  const handleRoutePositionAdd = (position) => {
    setRoutePositions(prev => [...prev, [position[0], position[1]]]);
  };

  const handleFinishRoute = async (positions) => {
    if (positions.length < 2) return;

    try {
      const routeData = {
        ...newRouteForm,
        path: positions
      };
      await onAddRoute(map.id, routeData);
      setNewRouteForm({ title: '', description: '', color: 'blue' });
      setRoutePositions([]);
    } catch (err) {
      console.error('Failed to add route', err);
    }
  };

  const handleRouteFormChange = (e) => {
    setNewRouteForm({ ...newRouteForm, [e.target.name]: e.target.value });
  };

  const handleLocationSelect = (location) => {
    const center = [parseFloat(location.lat), parseFloat(location.lon)];
    setMapCenter(center);
    if (mapRef.current) {
      mapRef.current.setView(center, 13);
    }
    setSearchQuery('');
  };

  return (
    <div className="map-detail">
      <div className="map-controls">
        <button className="btn btn-secondary" onClick={onBack}>
          ← Back to Maps
        </button>
        {isOwner && (
          <div className="owner-controls">
            <button 
              className="btn btn-primary"
              onClick={() => setIsEditing(!isEditing)}
            >
              {isEditing ? 'Cancel Edit' : 'Edit Map'}
            </button>
            <button className="btn btn-danger" onClick={() => onDelete(map.id)}>
              Delete Map
            </button>
          </div>
        )}
      </div>

      {isEditing ? (
        <div className="edit-map-form">
          <h2>Edit Map</h2>
          <form onSubmit={handleEditSubmit}>
            <div className="form-group">
              <label htmlFor="edit-title">Title</label>
              <input
                type="text"
                id="edit-title"
                name="title"
                value={editForm.title}
                onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="edit-description">Description</label>
              <textarea
                id="edit-description"
                name="description"
                value={editForm.description}
                onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
              ></textarea>
            </div>
            <div className="form-group checkbox">
              <input
                type="checkbox"
                id="edit-is_public"
                name="is_public"
                checked={editForm.is_public}
                onChange={(e) => setEditForm({ ...editForm, is_public: e.target.checked })}
              />
              <label htmlFor="edit-is_public">Make this map public</label>
            </div>
            <button type="submit" className="btn btn-primary">Save Changes</button>
          </form>
        </div>
      ) : (
        <div className="map-info">
          <h2>{map.title}</h2>
          <p className="map-description">{map.description || 'No description'}</p>
          <div className="map-meta">
            <span className={`visibility-badge ${map.is_public ? 'public' : 'private'}`}>
              {map.is_public ? 'Public' : 'Private'}
            </span>
            <span className="owner">Created by {map.owner}</span>
            <span className="date">{new Date(map.created_at).toLocaleDateString()}</span>
          </div>
        </div>
      )}

      <div className="map-search-container">
        <input
          type="text"
          placeholder="Search for a location..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="search-input"
        />
        {searchResults.length > 0 && (
          <ul className="search-results">
            {searchResults.map((result) => (
              <li
                key={result.place_id}
                onClick={() => handleLocationSelect(result)}
              >
                {result.display_name}
              </li>
            ))}
          </ul>
        )}
        {isSearchLoading && <div className="search-loading">Searching...</div>}
      </div>

      {isOwner && (
        <div className="map-actions">
          <button
            className={`btn ${isAddingMarker ? 'btn-active' : 'btn-primary'}`}
            onClick={handleAddMarkerClick}
          >
            {isAddingMarker ? 'Cancel Adding Marker' : 'Add Marker'}
          </button>
          <button
            className={`btn ${isCreatingRoute ? 'btn-active' : 'btn-primary'}`}
            onClick={() => setIsCreatingRoute(!isCreatingRoute)}
          >
            {isCreatingRoute ? 'Finish Route' : 'Create Route'}
          </button>
        </div>
      )}

      {newMarkerPosition && (
        <div className="marker-form">
          <h3>Add New Marker</h3>
          <form onSubmit={handleMarkerFormSubmit}>
            <div className="form-group">
              <label htmlFor="marker-title">Title</label>
              <input
                type="text"
                id="marker-title"
                name="title"
                value={newMarkerForm.title}
                onChange={handleMarkerFormChange}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="marker-description">Description</label>
              <textarea
                id="marker-description"
                name="description"
                value={newMarkerForm.description}
                onChange={handleMarkerFormChange}
              ></textarea>
            </div>
            <div className="form-group">
              <label htmlFor="marker-color">Color</label>
              <select
                id="marker-color"
                name="color"
                value={newMarkerForm.color}
                onChange={handleMarkerFormChange}
              >
                <option value="red">Red</option>
                <option value="blue">Blue</option>
                <option value="green">Green</option>
                <option value="yellow">Yellow</option>
                <option value="purple">Purple</option>
              </select>
            </div>
            <div className="form-group">
              <button type="submit" className="btn btn-primary">Add Marker</button>
              <button 
                type="button" 
                className="btn btn-secondary"
                onClick={() => setNewMarkerPosition(null)}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {isCreatingRoute && routePositions.length > 0 && (
        <div className="route-form">
          <h3>Create New Route</h3>
          <p>Points added: {routePositions.length}</p>
          <form onSubmit={(e) => {
            e.preventDefault();
            setIsCreatingRoute(false);
          }}>
            <div className="form-group">
              <label htmlFor="route-title">Title</label>
              <input
                type="text"
                id="route-title"
                name="title"
                value={newRouteForm.title}
                onChange={handleRouteFormChange}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="route-description">Description</label>
              <textarea
                id="route-description"
                name="description"
                value={newRouteForm.description}
                onChange={handleRouteFormChange}
              ></textarea>
            </div>
            <div className="form-group">
              <label htmlFor="route-color">Color</label>
              <select
                id="route-color"
                name="color"
                value={newRouteForm.color}
                onChange={handleRouteFormChange}
              >
                <option value="blue">Blue</option>
                <option value="red">Red</option>
                <option value="green">Green</option>
                <option value="purple">Purple</option>
                <option value="orange">Orange</option>
              </select>
            </div>
            <button type="submit" className="btn btn-primary">Finish Route</button>
          </form>
        </div>
      )}

      <div className="map-container">
        <MapContainer
          center={mapCenter}
          zoom={13}
          style={{ height: '600px', width: '100%' }}
          ref={mapRef}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          
          {map.markers && map.markers.map((marker) => (
            <Marker 
              key={marker.id} 
              position={[marker.latitude, marker.longitude]}
              icon={new L.Icon({
                iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-${marker.color}.png`,
                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41]
              })}
            >
              <Popup>
                <div>
                  <h3>{marker.title}</h3>
                  <p>{marker.description || 'No description'}</p>
                  {isOwner && (
                    <button 
                      className="btn btn-danger btn-sm" 
                      onClick={() => onDeleteMarker(marker.id)}
                    >
                      Delete Marker
                    </button>
                  )}
                </div>
              </Popup>
            </Marker>
          ))}

          {map.routes && map.routes.map((route) => (
            <React.Fragment key={route.id}>
              <Polyline 
                positions={route.path} 
                color={route.color} 
                weight={5}
              >
                <Popup>
                  <div>
                    <h3>{route.title}</h3>
                    <p>{route.description || 'No description'}</p>
                    {isOwner && (
                      <button 
                        className="btn btn-danger btn-sm" 
                        onClick={() => onDeleteRoute(route.id)}
                      >
                        Delete Route
                      </button>
                    )}
                  </div>
                </Popup>
              </Polyline>
            </React.Fragment>
          ))}

          {isAddingMarker && <MapClickHandler onMapClick={handleMapClick} />}
          {isCreatingRoute && (
            <RouteCreator
              isCreating={isCreatingRoute}
              onPositionAdd={handleRoutePositionAdd}
              onFinish={handleFinishRoute}
            />
          )}
        </MapContainer>
      </div>
    </div>
  );
}

// Main App Component
function App() {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [view, setView] = useState('login');
  const [maps, setMaps] = useState({ user_maps: [], public_maps: [] });
  const [currentMap, setCurrentMap] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Check if user is already logged in
    const checkAuth = async () => {
      try {
        const userData = await api.getCurrentUser();
        if (userData && userData.user) {
          setUser(userData.user);
          setView('maps');
          loadMaps();
        } else {
          setView('login');
        }
      } catch (err) {
        console.error('Auth check failed', err);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const loadMaps = async () => {
    setIsLoading(true);
    try {
      const mapsData = await api.getMaps();
      setMaps(mapsData);
    } catch (err) {
      setError('Failed to load maps. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogin = (userData) => {
    setUser(userData);
    setView('maps');
    loadMaps();
  };

  const handleLogout = async () => {
    try {
      await api.logout();
      setUser(null);
      setView('login');
      setMaps({ user_maps: [], public_maps: [] });
      setCurrentMap(null);
    } catch (err) {
      console.error('Logout failed', err);
    }
  };

  const handleMapSelect = async (mapId) => {
    setIsLoading(true);
    try {
      const response = await api.getMap(mapId);
      if (response.error) {
        setError(response.error);
      } else {
        setCurrentMap(response.map);
        setView('map-detail');
      }
    } catch (err) {
      setError('Failed to load map details. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateMap = (mapData) => {
    loadMaps();
    setView('maps');
  };

  const handleDeleteMap = async (mapId) => {
    if (!confirm('Are you sure you want to delete this map?')) return;
    
    try {
      await api.deleteMap(mapId);
      setView('maps');
      loadMaps();
    } catch (err) {
      setError('Failed to delete map. Please try again.');
      console.error(err);
    }
  };

  const handleEditMap = async (mapId, mapData) => {
    try {
      const response = await api.updateMap(mapId, mapData);
      if (response.error) {
        setError(response.error);
      } else {
        // Refresh the current map data
        handleMapSelect(mapId);
      }
    } catch (err) {
      setError('Failed to update map. Please try again.');
      console.error(err);
    }
  };

  const handleAddMarker = async (mapId, markerData) => {
    try {
      await api.addMarker(mapId, markerData);
      handleMapSelect(mapId);
    } catch (err) {
      setError('Failed to add marker. Please try again.');
      console.error(err);
    }
  };

  const handleDeleteMarker = async (markerId) => {
    if (!confirm('Are you sure you want to delete this marker?')) return;
    
    try {
      await api.deleteMarker(markerId);
      handleMapSelect(currentMap.id);
    } catch (err) {
      setError('Failed to delete marker. Please try again.');
      console.error(err);
    }
  };

  const handleAddRoute = async (mapId, routeData) => {
    try {
      await api.addRoute(mapId, routeData);
      handleMapSelect(mapId);
    } catch (err) {
      setError('Failed to add route. Please try again.');
      console.error(err);
    }
  };

  const handleDeleteRoute = async (routeId) => {
    if (!confirm('Are you sure you want to delete this route?')) return;
    
    try {
      await api.deleteRoute(routeId);
      handleMapSelect(currentMap.id);
    } catch (err) {
      setError('Failed to delete route. Please try again.');
      console.error(err);
    }
  };

  if (isLoading && view !== 'create-map') {
    return (
      <div className="app">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      {error && (
        <div className="error-notification">
          <p>{error}</p>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}
      
      <header className="app-header">
        <h1>MapShare</h1>
        {user && (
          <div className="user-controls">
            <span className="username">Welcome, {user.username}</span>
            <button className="btn btn-secondary" onClick={handleLogout}>Logout</button>
          </div>
        )}
      </header>

      <main className="app-content">
        {view === 'login' && (
          <Login onLogin={handleLogin} onSwitchToRegister={() => setView('register')} />
        )}

        {view === 'register' && (
          <Register onRegister={handleLogin} onSwitchToLogin={() => setView('login')} />
        )}

        {view === 'maps' && (
          <MapsList
            maps={maps}
            onMapSelect={handleMapSelect}
            onCreateMap={() => setView('create-map')}
            isLoading={isLoading}
          />
        )}

        {view === 'create-map' && (
          <CreateMapForm
            onSubmit={handleCreateMap}
            onCancel={() => setView('maps')}
          />
        )}

        {view === 'map-detail' && currentMap && (
          <MapDetail
            map={currentMap}
            isOwner={user && currentMap.owner === user.username}
            onBack={() => {
              setView('maps');
              setCurrentMap(null);
            }}
            onDelete={handleDeleteMap}
            onEdit={handleEditMap}
            onAddMarker={handleAddMarker}
            onDeleteMarker={handleDeleteMarker}
            onAddRoute={handleAddRoute}
            onDeleteRoute={handleDeleteRoute}
          />
        )}
      </main>
    </div>
  );
}

// Mount the app to the DOM
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

export default App;


