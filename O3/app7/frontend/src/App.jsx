import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css'; // Optional styling import

/**
 * Main App component that implements multipage routing using state.
 * It contains pages for Home, File Upload, File Listing, and File Preview.
 */
function App() {
  // State values for routing, files list, upload feedback, etc.
  const [page, setPage] = useState('home');
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [message, setMessage] = useState('');
  const [previewUrl, setPreviewUrl] = useState('');

  // Effect hook to fetch file list when the "files" page is selected.
  useEffect(() => {
    if (page === 'files') {
      fetch('/api/files')
        .then(response => response.json())
        .then(data => {
          if (data.error) {
            setMessage(data.error);
          } else {
            setFiles(data.files);
          }
        })
        .catch(err => setMessage('Error fetching files.'));
    }
  }, [page]);

  // Handle file selection in the upload form
  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
  };

  // Handle file upload form submission
  const handleUpload = (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setMessage('Please select a file to upload.');
      return;
    }
    const formData = new FormData();
    formData.append('file', selectedFile);

    fetch('/api/upload', {
      method: 'POST',
      body: formData,
    })
      .then(response => response.json())
      .then(data => {
        if (data.error) {
          setMessage(data.error);
        } else {
          setMessage(data.message);
          // Optionally, reset file input
          setSelectedFile(null);
        }
      })
      .catch(err => setMessage('File upload failed.'));
  };

  // Initiate file download by creating a temporary link
  const handleDownload = (filename) => {
    const a = document.createElement('a');
    a.href = `/api/download/${encodeURIComponent(filename)}`;
    a.click();
  };

  // Set preview URL and navigate to preview page
  const handlePreview = (filename) => {
    setPreviewUrl(`/api/preview/${encodeURIComponent(filename)}`);
    setPage('preview');
  };

  // Render page content based on the current state
  const renderContent = () => {
    switch(page) {
      case 'home':
        return (
          <div className="home">
            <h2>Welcome to the File Uploader System</h2>
            <p>Select one of the pages from the navigation bar.</p>
          </div>
        );
      case 'upload':
        return (
          <div className="upload">
            <h2>Upload File</h2>
            <form onSubmit={handleUpload}>
              <input type="file" onChange={handleFileChange} />
              <button type="submit">Upload</button>
            </form>
            {message && <p className="message">{message}</p>}
          </div>
        );
      case 'files':
        return (
          <div className="files">
            <h2>Uploaded Files</h2>
            {message && <p className="message">{message}</p>}
            <ul>
              {files.map((file, idx) => (
                <li key={idx}>
                  {file}
                  <button onClick={() => handleDownload(file)}>Download</button>
                  <button onClick={() => handlePreview(file)}>Preview</button>
                </li>
              ))}
            </ul>
          </div>
        );
      case 'preview':
        return (
          <div className="preview">
            <h2>File Preview</h2>
            {previewUrl ? (
              <>
                <iframe title="preview" src={previewUrl} width="600" height="400"></iframe>
                <br />
                <button onClick={() => setPage('files')}>Back to Files</button>
              </>
            ) : (
              <p>No file selected for preview.</p>
            )}
          </div>
        );
      default:
        return (
          <div className="home">
            <h2>Welcome to the File Uploader System</h2>
          </div>
        );
    }
  };

  return (
    <div className="App">
      <nav className="navbar">
        <button onClick={() => { setPage('home'); setMessage(''); }}>Home</button>
        <button onClick={() => { setPage('upload'); setMessage(''); }}>Upload</button>
        <button onClick={() => { setPage('files'); setMessage(''); }}>Files</button>
      </nav>
      <main>
        {renderContent()}
      </main>
    </div>
  );
}

// Mounting Logic: Attach App component to the DOM element with id 'root'
const rootElement = document.getElementById('root');
const root = ReactDOM.createRoot(rootElement);
root.render(<App />);

export default App;
