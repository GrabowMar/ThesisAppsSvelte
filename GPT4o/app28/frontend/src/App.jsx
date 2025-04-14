// frontend/src/App.jsx

import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
  const [page, setPage] = useState('home');
  const [artworks, setArtworks] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadMessage, setUploadMessage] = useState('');

  // Fetch artworks from the backend
  const fetchArtworks = async () => {
    try {
      const res = await fetch('/api/artworks');
      const data = await res.json();
      setArtworks(data.artworks || []);
    } catch (err) {
      console.error('Error fetching artworks:', err);
    }
  };

  // Upload artwork
  const uploadArtwork = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('artwork', selectedFile);

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      const result = await res.json();
      setUploadMessage(result.message || 'Upload failed');
      fetchArtworks(); // Refresh artworks
      setSelectedFile(null); // Reset input
    } catch (err) {
      console.error('Error uploading artwork:', err);
    }
  };

  // Load artworks on page mount
  useEffect(() => {
    fetchArtworks();
  }, []);

  return (
    <div className="App">
      <header>
        <h1>Art Portfolio Showcase</h1>
        <nav>
          <button onClick={() => setPage('home')}>Home</button>
          <button onClick={() => setPage('gallery')}>Gallery</button>
          <button onClick={() => setPage('upload')}>Upload</button>
        </nav>
      </header>

      <main>
        {page === 'home' && (
          <div>
            <h2>Welcome!</h2>
            <p>Your platform for managing and showcasing your creative works.</p>
          </div>
        )}

        {page === 'gallery' && (
          <div className="gallery">
            <h2>Gallery</h2>
            {artworks.length > 0 ? (
              artworks.map((artwork, index) => (
                <div key={index} className="artwork">
                  <img alt={artwork} src={`/api/artworks/${artwork}`} />
                  <p>{artwork}</p>
                </div>
              ))
            ) : (
              <p>No artworks available.</p>
            )}
          </div>
        )}

        {page === 'upload' && (
          <div>
            <h2>Upload Artwork</h2>
            <form onSubmit={uploadArtwork}>
              <input
                type="file"
                onChange={(e) => setSelectedFile(e.target.files[0])}
                required
              />
              <button type="submit">Upload</button>
            </form>
            {uploadMessage && <p>{uploadMessage}</p>}
          </div>
        )}
      </main>
    </div>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
