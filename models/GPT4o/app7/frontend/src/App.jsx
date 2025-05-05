import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  // State Variables
  const [selectedFile, setSelectedFile] = useState(null);
  const [filesList, setFilesList] = useState([]);
  const [preview, setPreview] = useState('');

  // Fetch Files on Load
  useEffect(() => {
    fetchFiles();
  }, []);

  // Fetch File List from Backend
  const fetchFiles = async () => {
    try {
      const response = await fetch('/api/files');
      const data = await response.json();
      setFilesList(data.files || []);
    } catch (error) {
      console.error('Error fetching files:', error);
    }
  };

  // Handle File Upload
  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      alert('Please select a file to upload!');
      return;
    }
    const formData = new FormData();
    formData.append('file', selectedFile);
    try {
      const response = await fetch('/api/upload', { method: 'POST', body: formData });
      const result = await response.json();
      alert(result.message || 'Error uploading file');
      setSelectedFile(null);
      fetchFiles(); // Refresh file list
    } catch (error) {
      console.error('Error uploading file:', error);
    }
  };

  // Handle File Download
  const handleFileDownload = async (filename) => {
    const downloadUrl = `/api/download/${filename}`;
    window.open(downloadUrl, '_blank');
  };

  // Handle File Preview
  const handleFilePreview = async (filename) => {
    try {
      const response = await fetch(`/api/preview/${filename}`);
      const data = await response.json();
      if (data.error) alert(data.error);
      setPreview(data.content || 'No content available');
    } catch (error) {
      console.error('Error previewing file:', error);
    }
  };

  return (
    <div className="app-container">
      <h1>File Uploader Application</h1>

      {/* Upload Section */}
      <form onSubmit={handleFileUpload}>
        <label className="upload-label">
          Upload File:
          <input
            type="file"
            onChange={(e) => setSelectedFile(e.target.files[0])}
          />
        </label>
        <button type="submit">Upload</button>
      </form>

      {/* Files List Section */}
      <h2>Uploaded Files</h2>
      {filesList.length === 0 && <p>No files uploaded</p>}
      <ul>
        {filesList.map((file, index) => (
          <li key={index}>
            <span>{file}</span>
            <button onClick={() => handleFileDownload(file)}>Download</button>
            <button onClick={() => handleFilePreview(file)}>Preview</button>
          </li>
        ))}
      </ul>

      {/* File Preview Section */}
      {preview && (
        <div className="preview-box">
          <h3>File Preview</h3>
          <pre>{preview}</pre>
        </div>
      )}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
