import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [galleries, setGalleries] = useState([]);
  const [currentGallery, setCurrentGallery] = useState(null);
  const [images, setImages] = useState([]);
  const [viewMode, setViewMode] = useState('grid');
  const [selectedImage, setSelectedImage] = useState(null);

  useEffect(() => {
    // Fetch galleries on initial load
    fetchGalleries();
  }, []);

  const fetchGalleries = async () => {
    try {
      const response = await fetch('/api/galleries');
      if (!response.ok) throw new Error('Failed to fetch galleries');
      const data = await response.json();
      setGalleries(data);
    } catch (error) {
      console.error('Error fetching galleries:', error);
    }
  };

  const handleLogin = async (username, password) => {
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (!response.ok) throw new Error('Login failed');
      setUser(username);
    } catch (error) {
      console.error('Login error:', error);
    }
  };

  const handleRegister = async (username, password) => {
    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (!response.ok) throw new Error('Registration failed');
      alert('Registration successful. Please log in.');
    } catch (error) {
      console.error('Registration error:', error);
    }
  };

  const createGallery = async (name) => {
    try {
      const response = await fetch('/api/galleries', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      });
      if (!response.ok) throw new Error('Failed to create gallery');
      const newGallery = await response.json();
      setGalleries([...galleries, newGallery]);
    } catch (error) {
      console.error('Error creating gallery:', error);
    }
  };

  const uploadImage = async (file, metadata) => {
    if (!currentGallery) {
      alert('Please select a gallery first');
      return;
    }
    const formData = new FormData();
    formData.append('file', file);
    Object.entries(metadata).forEach(([key, value]) => {
      formData.append(key, value);
    });

    try {
      const response = await fetch(`/api/galleries/${currentGallery.id}/images`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) throw new Error('Failed to upload image');
      const newImage = await response.json();
      setImages([...images, newImage]);
    } catch (error) {
      console.error('Error uploading image:', error);
    }
  };

  const fetchImages = async (galleryId) => {
    try {
      const response = await fetch(`/api/galleries/${galleryId}/images`);
      if (!response.ok) throw new Error('Failed to fetch images');
      const data = await response.json();
      setImages(data);
    } catch (error) {
      console.error('Error fetching images:', error);
    }
  };

  const selectGallery = (gallery) => {
    setCurrentGallery(gallery);
    setImages([]);
    fetchImages(gallery.id);
  };

  const selectImage = async (imageId) => {
    try {
      const response = await fetch(`/api/images/${imageId}`);
      if (!response.ok) throw new Error('Failed to fetch image details');
      const image = await response.json();
      setSelectedImage(image);
    } catch (error) {
      console.error('Error selecting image:', error);
    }
  };

  const toggleViewMode = () => {
    setViewMode(viewMode === 'grid' ? 'list' : 'grid');
  };

  // Render login/register page
  if (!user) {
    return (
      <div className="login-container">
        <h1>Login</h1>
        <form onSubmit={(e) => {
          e.preventDefault();
          handleLogin(e.target.username.value, e.target.password.value);
        }}>
          <input type="text" name="username" placeholder="Username" required />
          <input type="password" name="password" placeholder="Password" required />
          <button type="submit">Login</button>
        </form>
        <h2>Or Register</h2>
        <form onSubmit={(e) => {
          e.preventDefault();
          handleRegister(e.target.username.value, e.target.password.value);
        }}>
          <input type="text" name="username" placeholder="Username" required />
          <input type="password" name="password" placeholder="Password" required />
          <button type="submit">Register</button>
        </form>
      </div>
    );
  }

  // Render main app
  return (
    <div className="app-container">
      <header>
        <h1>Gallery App</h1>
        <button onClick={() => setUser(null)}>Logout</button>
      </header>
      <main>
        <section className="sidebar">
          <h2>Galleries</h2>
          <ul>
            {galleries.map(gallery => (
              <li key={gallery.id} onClick={() => selectGallery(gallery)}>
                {gallery.name}
              </li>
            ))}
          </ul>
          <button onClick={() => {
            const name = prompt('Enter gallery name:');
            if (name) createGallery(name);
          }}>Create New Gallery</button>
        </section>
        <section className="content">
          {currentGallery ? (
            <>
              <h2>{currentGallery.name}</h2>
              <div className="view-mode-toggle">
                <button onClick={toggleViewMode}>
                  {viewMode === 'grid' ? 'Switch to List View' : 'Switch to Grid View'}
                </button>
              </div>
              <div className={`image-container ${viewMode}`}>
                {images.map(image => (
                  <div key={image.id} className="image-item" onClick={() => selectImage(image.id)}>
                    <img src={`/uploads/${image.filename}`} alt={image.filename} />
                    <p>{image.filename}</p>
                  </div>
                ))}
              </div>
              <div className="upload-section">
                <h3>Upload Image</h3>
                <input type="file" onChange={(e) => {
                  const file = e.target.files[0];
                  const metadata = {
                    title: prompt('Enter image title:') || '',
                    description: prompt('Enter image description:') || '',
                  };
                  uploadImage(file, metadata);
                }} />
              </div>
            </>
          ) : (
            <p>Select a gallery to view its images</p>
          )}
        </section>
        {selectedImage && (
          <section className="image-details">
            <h2>Image Details</h2>
            <img src={`/uploads/${selectedImage.filename}`} alt={selectedImage.filename} />
            <p>Title: {selectedImage.metadata.title}</p>
            <p>Description: {selectedImage.metadata.description}</p>
            <p>Filename: {selectedImage.filename}</p>
            <button onClick={() => setSelectedImage(null)}>Close</button>
          </section>
        )}
      </main>
    </div>
  );
}

// Mounting Logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

export default App;
