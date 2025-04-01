import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [currentPage, setCurrentPage] = useState('home');

  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    try {
      const response = await fetch('/api/files');
      if (!response.ok) throw new Error('Failed to fetch files');
      const data = await response.json();
      setFiles(data);
    } catch (error) {
      console.error('Error fetching files:', error);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) throw new Error('Failed to upload file');
      const data = await response.json();
      console.log('File uploaded:', data);
      fetchFiles();
    } catch (error) {
      console.error('Error uploading file:', error);
    }
  };

  const handleFileDownload = async (filename) => {
    try {
      const response = await fetch(`/api/download/${filename}`);
      if (!response.ok) throw new Error('Failed to download file');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading file:', error);
    }
  };

  const handleFilePreview = async (filename) => {
    setSelectedFile(filename);
    try {
      const response = await fetch(`/api/preview/${filename}`);
      if (!response.ok) throw new Error('Failed to preview file');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      setPreviewUrl(url);
    } catch (error) {
      console.error('Error previewing file:', error);
      setPreviewUrl(null);
    }
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'home':
        return (
          <div className="home-page">
            <h1>File Uploader</h1>
            <input type="file" onChange={handleFileUpload} />
            <h2>Uploaded Files</h2>
            <ul>
              {files.map((file) => (
                <li key={file.name}>
                  {file.name} - {file.size} bytes - {file.uploaded_at}
                  <button onClick={() => handleFileDownload(file.name)}>Download</button>
                  <button onClick={() => handleFilePreview(file.name)}>Preview</button>
                </li>
              ))}
            </ul>
          </div>
        );
      case 'preview':
        return (
          <div className="preview-page">
            <h1>File Preview</h1>
            {previewUrl ? (
              <img src={previewUrl} alt="File preview" />
            ) : (
              <p>Preview not available for this file type</p>
            )}
            <button onClick={() => setCurrentPage('home')}>Back to Home</button>
          </div>
        );
      default:
        return <div>404 - Page not found</div>;
    }
  };

  return (
    <div className="app">
      <nav>
        <button onClick={() => setCurrentPage('home')}>Home</button>
      </nav>
      {renderPage()}
    </div>
  );
}

// Mounting Logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
