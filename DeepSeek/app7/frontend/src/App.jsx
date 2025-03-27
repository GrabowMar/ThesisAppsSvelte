import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState('');

  // Fetch list of uploaded files
  useEffect(() => {
    fetch('/api/files')
      .then((response) => response.json())
      .then((data) => setFiles(data))
      .catch((err) => setError('Failed to fetch files'));
  }, []);

  // Handle file upload
  const handleUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    fetch('/api/upload', {
      method: 'POST',
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        setFiles((prevFiles) => [...prevFiles, data.filename]);
        setError('');
      })
      .catch((err) => setError('Upload failed'));
  };

  // Handle file download
  const handleDownload = (filename) => {
    window.open(`/api/download/${filename}`, '_blank');
  };

  // Handle file preview
  const handlePreview = (filename) => {
    window.open(`/api/preview/${filename}`, '_blank');
  };

  return (
    <main>
      <h1>File Uploader</h1>
      <div>
        <input type="file" onChange={handleUpload} />
      </div>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <h2>Uploaded Files</h2>
      <ul>
        {files.map((file, index) => (
          <li key={index}>
            {file}{' '}
            <button onClick={() => handleDownload(file)}>Download</button>{' '}
            <button onClick={() => handlePreview(file)}>Preview</button>
          </li>
        ))}
      </ul>
    </main>
  );
};

// Mounting Logic
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
