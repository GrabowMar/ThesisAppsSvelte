import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import axios from 'axios';
import './App.css';

const App = () => {
  const [images, setImages] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);
  const [file, setFile] = useState(null);

  useEffect(() => {
    fetchImages();
  }, []);

  const fetchImages = async () => {
    try {
      const response = await axios.get('/api/images');
      setImages(response.data.images);
    } catch (error) {
      console.error('Error fetching images:', error);
    }
  };

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    const formData = new FormData();
    formData.append('file', file);
    try {
      await axios.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      fetchImages();
    } catch (error) {
      console.error('Error uploading image:', error);
    }
  };

  const handleImageClick = (filename) => {
    setSelectedImage(filename);
  };

  const handleBack = () => {
    setSelectedImage(null);
  };

  return (
    <div className="app">
      {selectedImage ? (
        <div className="image-details">
          <img src={`/api/image/${selectedImage}`} alt={selectedImage} />
          <button onClick={handleBack}>Back</button>
        </div>
      ) : (
        <div>
          <input type="file" onChange={handleFileChange} />
          <button onClick={handleUpload}>Upload</button>
          <div className="gallery">
            {images.map((filename) => (
              <img
                key={filename}
                src={`/api/image/${filename}`}
                alt={filename}
                onClick={() => handleImageClick(filename)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
