import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import axios from 'axios';
import './App.css';

const App = () => {
  const [artworks, setArtworks] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);

  useEffect(() => {
    fetchArtworks();
  }, []);

  const fetchArtworks = async () => {
    try {
      const response = await axios.get('/api/artworks');
      setArtworks(response.data);
    } catch (error) {
      console.error('Error fetching artworks:', error);
    }
  };

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleFileUpload = async () => {
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await axios.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      alert('File uploaded successfully');
      fetchArtworks();
    } catch (error) {
      console.error('Error uploading file:', error);
    }
  };

  return (
    <Router>
      <div>
        <nav>
          <ul>
            <li><Link to="/">Home</Link></li>
            <li><Link to="/upload">Upload</Link></li>
            <li><Link to="/gallery">Gallery</Link></li>
          </ul>
        </nav>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/upload" element={<Upload handleFileChange={handleFileChange} handleFileUpload={handleFileUpload} />} />
          <Route path="/gallery" element={<Gallery artworks={artworks} />} />
        </Routes>
      </div>
    </Router>
  );
};

const Home = () => <h1>Welcome to the Art Portfolio Showcase</h1>;

const Upload = ({ handleFileChange, handleFileUpload }) => (
  <div>
    <h1>Upload Artwork</h1>
    <input type="file" onChange={handleFileChange} />
    <button onClick={handleFileUpload}>Upload</button>
  </div>
);

const Gallery = ({ artworks }) => (
  <div>
    <h1>Art Gallery</h1>
    <div className="gallery">
      {artworks.map((artwork) => (
        <img key={artwork} src={`/api/artworks/${artwork}`} alt={artwork} />
      ))}
    </div>
  </div>
);

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
