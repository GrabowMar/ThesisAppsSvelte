// 1. Imports
import { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  const [currentPage, setCurrentPage] = useState('home');
  const [artists, setArtists] = useState([]);
  const [artworks, setArtworks] = useState([]);
  const [galleries, setGalleries] = useState([]);
  const [selectedArtist, setSelectedArtist] = useState(null);
  
  // 4. Lifecycle Functions
  useEffect(() => {
    // Load initial data
    fetchArtists();
    fetchArtworks();
    fetchGalleries();
  }, []);

  // 5. API Calls
  const fetchArtists = async () => {
    try {
      const response = await fetch('http://localhost:5215/api/artist');
      const data = await response.json();
      setArtists(data);
    } catch (error) {
      console.error('Error fetching artists:', error);
    }
  };

  const fetchArtistById = async (id) => {
    try {
      const response = await fetch(`http://localhost:5215/api/artist/${id}`);
      const data = await response.json();
      setSelectedArtist(data);
    } catch (error) {
      console.error('Error fetching artist:', error);
    }
  };

  const fetchArtworks = async () => {
    try {
      const response = await fetch('http://localhost:5215/api/artwork');
      const data = await response.json();
      setArtworks(data);
    } catch (error) {
      console.error('Error fetching artworks:', error);
    }
  };

  const fetchGalleries = async () => {
    try {
      const response = await fetch('http://localhost:5215/api/gallery');
      const data = await response.json();
      setGalleries(data);
    } catch (error) {
      console.error('Error fetching galleries:', error);
    }
  };

  // Event Handlers
  const handleArtistSelect = (artistId) => {
    setCurrentPage('artistDetail');
    fetchArtistById(artistId);
  };

  const handleUploadArtwork = async (file, formData) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      Object.keys(formData).forEach(key => formData.append(key, formData[key]));
      
      const response = await fetch('http://localhost:5215/api/artwork', {
        method: 'POST',
        body: formData,
      });
      
      if (response.ok) {
        fetchArtworks();
      }
    } catch (error) {
      console.error('Error uploading artwork:', error);
    }
  };

  // 6. Page Components
  const HomePage = () => (
    <div className="home">
      <h1>Art Portfolio Showcase</h1>
      <div className="featured-artworks">
        <h2>Featured Artworks</h2>
        <div className="artwork-grid">
          {artworks.filter(a => a.is_featured).map(artwork => (
            <div key={artwork.id} className="artwork-card">
              <img src={artwork.image_url} alt={artwork.title} />
              <h3>{artwork.title}</h3>
              <p>{artwork.medium}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const ArtistsPage = () => (
    <div className="artists">
      <h1>Artists</h1>
      <button onClick={() => setCurrentPage('createArtist')}>Add New Artist</button>
      <div className="artist-list">
        {artists.map(artist => (
          <div key={artist.id} className="artist-card" onClick={() => handleArtistSelect(artist.id)}>
            <h3>{artist.name}</h3>
            <p>{artist.bio.substring(0, 100)}...</p>
          </div>
        ))}
      </div>
    </div>
  );

  const ArtistDetailPage = () => (
    <div className="artist-detail">
      <button onClick={() => setCurrentPage('artists')}>Back to Artists</button>
      <div className="artist-info">
        <h2>{selectedArtist?.name}</h2>
        <p>{selectedArtist?.bio}</p>
      </div>
      <div className="artist-galleries">
        <h3>Galleries</h3>
        <div className="gallery-grid">
          {galleries.filter(g => g.artist_id === selectedArtist?.id).map(gallery => (
            <div key={gallery.id} className="gallery-card">
              <h4>{gallery.name}</h4>
              <p>{gallery.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const GalleryPage = () => (
    <div className="galleries">
      <h1>Galleries</h1>
      <div className="gallery-list">
        {galleries.map(gallery => (
          <div key={gallery.id} className="gallery-card">
            <h3>{gallery.name}</h3>
            <p>{gallery.description}</p>
          </div>
        ))}
      </div>
    </div>
  );

  const UploadArtworkPage = () => {
    const [formData, setFormData] = useState({
      title: '',
      description: '',
      medium: '',
      creation_date: '',
      category: 'General',
      artist_id: ''
    });
    const [file, setFile] = useState(null);

    const handleChange = (e) => {
      setFormData({
        ...formData,
        [e.target.name]: e.target.value
      });
    };

    const handleFileChange = (e) => {
      setFile(e.target.files[0]);
    };

    const handleSubmit = (e) => {
      e.preventDefault();
      handleUploadArtwork(file, formData);
      setCurrentPage('artworks');
    };

    return (
      <div className="upload-artwork">
        <h2>Upload New Artwork</h2>
        <form onSubmit={handleSubmit}>
          <div>
            <label>Artwork Image: </label>
            <input type="file" onChange={handleFileChange} required />
          </div>
          <div>
            <label>Title: </label>
            <input type="text" name="title" value={formData.title} onChange={handleChange} required />
          </div>
          <div>
            <label>Description: </label>
            <textarea name="description" value={formData.description} onChange={handleChange} />
          </div>
          <div>
            <label>Medium: </label>
            <input type="text" name="medium" value={formData.medium} onChange={handleChange} />
          </div>
          <div>
            <label>Creation Date: </label>
            <input type="date" name="creation_date" value={formData.creation_date} onChange={handleChange} />
          </div>
          <div>
            <label>Category: </label>
            <select name="category" value={formData.category} onChange={handleChange}>
              <option value="Painting">Painting</option>
              <option value="Sculpture">Sculpture</option>
              <option value="Photography">Photography</option>
              <option value="Digital">Digital</option>
              <option value="General">General</option>
            </select>
          </div>
          <div>
            <label>Artist ID: </label>
            <input type="text" name="artist_id" value={formData.artist_id} onChange={handleChange} required />
          </div>
          <button type="submit">Upload Artwork</button>
        </form>
      </div>
    );
  };

  // 7. Navigation
  const NavBar = () => (
    <nav className="navbar">
      <button onClick={() => setCurrentPage('home')}>Home</button>
      <button onClick={() => setCurrentPage('artists')}>Artists</button>
      <button onClick={() => setCurrentPage('galleries')}>Galleries</button>
      <button onClick={() => setCurrentPage('upload')}>Upload Artwork</button>
    </nav>
  );

  // 8. Render Current Page
  const renderPage = () => {
    switch (currentPage) {
      case 'home': return <HomePage />;
      case 'artists': return <ArtistsPage />;
      case 'artistDetail': return <ArtistDetailPage />;
      case 'galleries': return <GalleryPage />;
      case 'upload': return <UploadArtworkPage />;
      default: return <HomePage />;
    }
  };

  return (
    <div className="app">
      <NavBar />
      {renderPage()}
    </div>
  );
}

// Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
