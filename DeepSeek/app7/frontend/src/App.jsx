import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);

  // Fetch the list of uploaded files
  useEffect(() => {
    fetch('http://localhost:5173/files')
      .then(response => response.json())
      .then(data => setFiles(data.files))
      .catch(error => console.error('Error fetching files:', error));
  }, []);

  // Handle file upload
  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    const formData = new FormData();
    formData.append('file', file);

    fetch('http://localhost:5173/upload', {
      method: 'POST',
      body: formData,
    })
      .then(response => response.json())
      .then(data => {
        alert(data.message);
        window.location.reload(); // Refresh to update file list
      })
      .catch(error => console.error('Error uploading file:', error));
  };

  // Handle file download
  const handleDownload = (filename) => {
    window.open(`http://localhost:5173/download/${filename}`, '_blank');
  };

  // Handle file preview
  const handlePreview = (filename) => {
    fetch(`http://localhost:5173/preview/${filename}`)
      .then(response => response.json())
      .then(data => {
        setSelectedFile(data);
      })
      .catch(error => console.error('Error previewing file:', error));
  };

  return (
    <div className="app">
      <h1>File Uploader</h1>
      <div className="upload-section">
        <input type="file" onChange={handleFileUpload} />
      </div>
      <div className="file-list">
        <h2>Uploaded Files</h2>
        <ul>
          {files.map((file, index) => (
            <li key={index}>
              <span>{file}</span>
              <button onClick={() => handleDownload(file)}>Download</button>
              <button onClick={() => handlePreview(file)}>Preview</button>
            </li>
          ))}
        </ul>
      </div>
      {selectedFile && (
        <div className="preview-section">
          <h2>Preview: {selectedFile.filename}</h2>
          <pre>{selectedFile.content}</pre>
          <button onClick={() => setSelectedFile(null)}>Close</button>
        </div>
      )}
    </div>
  );
};

// Mount the app
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
