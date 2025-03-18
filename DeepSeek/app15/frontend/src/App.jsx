import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
  const [files, setFiles] = useState([]);
  const [storageInfo, setStorageInfo] = useState({ used: 0, quota: 0 });
  const [error, setError] = useState('');

  const fetchFiles = async () => {
    try {
      const response = await fetch('/files');
      const data = await response.json();
      setFiles(data.files);
    } catch (err) {
      setError('Failed to fetch files');
    }
  };

  const fetchStorageInfo = async () => {
    try {
      const response = await fetch('/storage');
      const data = await response.json();
      setStorageInfo(data);
    } catch (err) {
      setError('Failed to fetch storage info');
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (response.ok) {
        fetchFiles();
        fetchStorageInfo();
      } else {
        setError(data.error || 'Upload failed');
      }
    } catch (err) {
      setError('Upload failed');
    }
  };

  const handleDownload = async (filename) => {
    window.open(`/download/${filename}`, '_blank');
  };

  useEffect(() => {
    fetchFiles();
    fetchStorageInfo();
  }, []);

  return (
    <div className="App">
      <h1>File Storage System</h1>
      {error && <p className="error">{error}</p>}
      <div className="storage-info">
        <p>Storage Used: {(storageInfo.used / 1024 / 1024).toFixed(2)} MB</p>
        <p>Storage Quota: {(storageInfo.quota / 1024 / 1024).toFixed(2)} MB</p>
      </div>
      <input type="file" onChange={handleUpload} />
      <ul>
        {files.map((file, index) => (
          <li key={index}>
            {file} <button onClick={() => handleDownload(file)}>Download</button>
          </li>
        ))}
      </ul>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
