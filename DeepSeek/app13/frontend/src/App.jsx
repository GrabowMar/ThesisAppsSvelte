import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
  const [images, setImages] = useState([]);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'
  const [selectedImage, setSelectedImage] = useState(null);

  // Fetch images from backend
  useEffect(() => {
    fetch('/api/images')
      .then(response => response.json())
      .then(data => setImages(data))
      .catch(error => console.error('Error fetching images:', error));
  }, []);

  // Handle file upload
  const handleUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const formData = new FormData();
      formData.append('file', file);
      fetch('/api/upload', {
        method: 'POST',
        body: formData,
      })
        .then(response => response.json())
        .then(() => window.location.reload())
        .catch(error => console.error('Error uploading file:', error));
    }
  };

  return (
    <main>
      <h1>Gallery Application</h1>
      <div className="controls">
        <label>
          Upload Image:
          <input type="file" accept="image/*" onChange={handleUpload} />
        </label>
        <button onClick={() => setViewMode('grid')}>Grid View</button>
        <button onClick={() => setViewMode('list')}>List View</button>
      </div>
      {selectedImage && (
        <div className="modal">
          <img src={`/uploads/${selectedImage}`} alt={selectedImage} />
          <button onClick={() => setSelectedImage(null)}>Close</button>
        </div>
      )}
      <div className={viewMode === 'grid' ? 'grid-view' : 'list-view'}>
        {images.map((image, index) => (
          <div key={index} className="image-item" onClick={() => setSelectedImage(image)}>
            <img src={`/uploads/${image}`} alt={image} />
            <p>{image}</p>
          </div>
        ))}
      </div>
    </main>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
