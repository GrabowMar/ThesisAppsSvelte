import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
  const [images, setImages] = useState([]);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'
  const [selectedImage, setSelectedImage] = useState(null);

  // Fetch images from the backend
  useEffect(() => {
    fetch('http://localhost:5185/gallery')
      .then((response) => response.json())
      .then((data) => setImages(data.images))
      .catch((error) => console.error('Error fetching images:', error));
  }, []);

  // Handle image upload
  const handleUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    fetch('http://localhost:5185/upload', {
      method: 'POST',
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.message === 'File uploaded successfully') {
          setImages([...images, data.filename]);
        } else {
          alert(data.error || 'Failed to upload file');
        }
      })
      .catch((error) => {
        console.error('Error uploading file:', error);
        alert('Failed to upload file');
      });
  };

  // Handle image click to show details
  const handleImageClick = (filename) => {
    setSelectedImage(filename);
  };

  // Close image details view
  const closeDetails = () => {
    setSelectedImage(null);
  };

  return (
    <div className="app">
      <header className="header">
        <h1>Gallery App</h1>
        <label className="upload-button">
          Upload Image
          <input type="file" onChange={handleUpload} style={{ display: 'none' }} />
        </label>
        <div className="view-toggle">
          <button
            className={`toggle-button ${viewMode === 'grid' ? 'active' : ''}`}
            onClick={() => setViewMode('grid')}
          >
            Grid
          </button>
          <button
            className={`toggle-button ${viewMode === 'list' ? 'active' : ''}`}
            onClick={() => setViewMode('list')}
          >
            List
          </button>
        </div>
      </header>
      <div className={`gallery ${viewMode}`}>
        {images.map((filename, index) => (
          <div
            key={index}
            className="image-item"
            onClick={() => handleImageClick(filename)}
          >
            <img
              src={`http://localhost:5185/uploads/${filename}`}
              alt={`Image ${index}`}
            />
            {selectedImage === filename && (
              <div className="image-details">
                <p><strong>Filename:</strong> {filename}</p>
                <button onClick={closeDetails}>Close</button>
              </div>
            )}
          </div>
        ))}
      </div>
      {selectedImage && (
        <div className="overlay" onClick={closeDetails}>
          <div className="detail-view">
            <img
              src={`http://localhost:5185/uploads/${selectedImage}`}
              alt="Selected Image"
            />
            <p><strong>Filename:</strong> {selectedImage}</p>
          </div>
        </div>
      )}
    </div>
  );
};

// Mount the React app to the DOM
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
