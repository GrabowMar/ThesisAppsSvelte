import React, { useState, useEffect, useRef } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';
import './App.css';

// API URL Configuration
const API_URL = 'http://localhost:5333';

// File Icon Component
const FileIcon = ({ extension }) => {
  const getIconClass = () => {
    switch(extension.toLowerCase()) {
      case 'pdf': return 'fa-file-pdf';
      case 'doc': 
      case 'docx': return 'fa-file-word';
      case 'xls':
      case 'xlsx': return 'fa-file-excel';
      case 'csv': return 'fa-file-csv';
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif': return 'fa-file-image';
      case 'txt': return 'fa-file-alt';
      default: return 'fa-file';
    }
  };
  
  return <i className={`fas ${getIconClass()}`}></i>;
};

// Format file size to be human readable
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Dashboard Component
const Dashboard = () => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const fileInputRef = useRef(null);
  const [dragActive, setDragActive] = useState(false);
  const [notification, setNotification] = useState({show: false, message: '', type: ''});

  // Fetch all files
  const fetchFiles = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/files`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      
      const data = await response.json();
      setFiles(data.files || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching files:', err);
      setError('Failed to load files. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  // Load files on component mount
  useEffect(() => {
    fetchFiles();
  }, []);

  // Handle file upload
  const handleFileUpload = async (file) => {
    if (!file) return;
    
    // Check file size
    if (file.size > 16 * 1024 * 1024) {
      showNotification('File size exceeds the limit (16MB)', 'error');
      return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      setUploading(true);
      setUploadProgress(0);
      
      const xhr = new XMLHttpRequest();
      
      xhr.open('POST', `${API_URL}/api/files`);
      
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const progress = Math.round((event.loaded / event.total) * 100);
          setUploadProgress(progress);
        }
      });
      
      xhr.onload = function() {
        if (xhr.status === 201) {
          const response = JSON.parse(xhr.responseText);
          setFiles(prevFiles => [...prevFiles, response.file]);
          showNotification('File uploaded successfully!', 'success');
        } else {
          const errorData = JSON.parse(xhr.responseText);
          showNotification(errorData.error || 'Failed to upload file', 'error');
        }
        setUploading(false);
      };
      
      xhr.onerror = function() {
        showNotification('Network error occurred', 'error');
        setUploading(false);
      };
      
      xhr.send(formData);
    } catch (err) {
      console.error('Error uploading file:', err);
      showNotification('Failed to upload file', 'error');
      setUploading(false);
    }
  };

  // Handle file selection from input
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  // Handle file download
  const handleDownload = (fileId) => {
    window.location.href = `${API_URL}/api/files/${fileId}`;
  };

  // Handle file deletion
  const handleDelete = async (fileId) => {
    if (!confirm('Are you sure you want to delete this file?')) return;
    
    try {
      const response = await fetch(`${API_URL}/api/files/${fileId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        setFiles(files.filter(file => file.id !== fileId));
        showNotification('File deleted successfully', 'success');
        
        // Close preview if the deleted file is currently being previewed
        if (selectedFile && selectedFile.id === fileId) {
          setSelectedFile(null);
          setShowPreview(false);
        }
      } else {
        showNotification('Failed to delete file', 'error');
      }
    } catch (err) {
      console.error('Error deleting file:', err);
      showNotification('Error deleting file', 'error');
    }
  };

  // Show notification
  const showNotification = (message, type) => {
    setNotification({
      show: true,
      message,
      type
    });
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
      setNotification({show: false, message: '', type: ''});
    }, 3000);
  };

  // Preview file
  const handlePreview = (file) => {
    setSelectedFile(file);
    setShowPreview(true);
  };

  // Filter files based on search term
  const filteredFiles = files.filter(file => 
    file.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Drag and drop handlers
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };
  
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="dashboard">
      {/* Notification component */}
      {notification.show && (
        <div className={`notification ${notification.type}`}>
          {notification.message}
        </div>
      )}
      
      <div className="dashboard-header">
        <h1>File Manager</h1>
        <div className="search-bar">
          <input
            type="text"
            placeholder="Search files..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <i className="fas fa-search"></i>
        </div>
      </div>
      
      <div 
        className={`upload-area ${dragActive ? 'active' : ''}`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
        
        {uploading ? (
          <div className="upload-progress">
            <div className="progress-bar">
              <div 
                className="progress"
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
            <span>{uploadProgress}%</span>
          </div>
        ) : (
          <>
            <i className="fas fa-cloud-upload-alt"></i>
            <p>Drag & Drop a file here, or</p>
            <button 
              className="upload-btn"
              onClick={() => fileInputRef.current.click()}
            >
              Browse Files
            </button>
            <p className="upload-info">Max file size: 16MB</p>
          </>
        )}
      </div>
      
      <div className="files-container">
        <h2>Your Files</h2>
        {loading ? (
          <div className="loading">
            <i className="fas fa-spinner fa-spin"></i>
            <p>Loading files...</p>
          </div>
        ) : error ? (
          <div className="error">
            <i className="fas fa-exclamation-circle"></i>
            <p>{error}</p>
            <button onClick={fetchFiles}>Try Again</button>
          </div>
        ) : filteredFiles.length === 0 ? (
          <div className="no-files">
            <i className="fas fa-folder-open"></i>
            <p>No files found</p>
          </div>
        ) : (
          <div className="files-list">
            {filteredFiles.map((file) => (
              <div key={file.id} className="file-card">
                <div className="file-icon">
                  <FileIcon extension={file.extension} />
                </div>
                <div className="file-details">
                  <div className="file-name" title={file.name}>{file.name}</div>
                  <div className="file-info">
                    <span>{formatFileSize(file.size)}</span>
                    <span>{file.uploadDate}</span>
                  </div>
                </div>
                <div className="file-actions">
                  <button
                    onClick={() => handlePreview(file)}
                    className="action-btn preview-btn"
                    title="Preview"
                  >
                    <i className="fas fa-eye"></i>
                  </button>
                  <button
                    onClick={() => handleDownload(file.id)}
                    className="action-btn download-btn"
                    title="Download"
                  >
                    <i className="fas fa-download"></i>
                  </button>
                  <button
                    onClick={() => handleDelete(file.id)}
                    className="action-btn delete-btn"
                    title="Delete"
                  >
                    <i className="fas fa-trash"></i>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* File Preview Modal */}
      {showPreview && selectedFile && (
        <div className="preview-modal">
          <div className="preview-content">
            <div className="preview-header">
              <h3>{selectedFile.name}</h3>
              <button 
                onClick={() => setShowPreview(false)}
                className="close-btn"
              >
                <i className="fas fa-times"></i>
              </button>
            </div>
            <div className="preview-body">
              {selectedFile.type.startsWith('image/') ? (
                <img 
                  src={`${API_URL}/api/files/preview/${selectedFile.id}`}
                  alt={selectedFile.name}
                  className="preview-image"
                />
              ) : selectedFile.type === 'application/pdf' ? (
                <iframe
                  src={`${API_URL}/api/files/preview/${selectedFile.id}`}
                  className="preview-frame"
                  title={selectedFile.name}
                ></iframe>
              ) : (
                <div className="preview-unavailable">
                  <i className="fas fa-file"></i>
                  <p>Preview not available</p>
                  <button
                    onClick={() => handleDownload(selectedFile.id)}
                    className="download-btn"
                  >
                    <i className="fas fa-download"></i> Download
                  </button>
                </div>
              )}
            </div>
            <div className="preview-footer">
              <div className="file-details">
                <p><strong>Size:</strong> {formatFileSize(selectedFile.size)}</p>
                <p><strong>Type:</strong> {selectedFile.type}</p>
                <p><strong>Upload Date:</strong> {selectedFile.uploadDate}</p>
              </div>
              <div className="preview-actions">
                <button
                  onClick={() => handleDownload(selectedFile.id)}
                  className="action-btn"
                >
                  <i className="fas fa-download"></i> Download
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// About Component
const About = () => {
  return (
    <div className="about-page">
      <h1>About File Manager</h1>
      <div className="about-content">
        <p>
          This file manager application allows you to easily upload, organize, preview, and download 
          your files. It's built with a Flask backend and React frontend.
        </p>
        
        <h2>Features</h2>
        <ul>
          <li><i className="fas fa-cloud-upload-alt"></i> Upload files (up to 16MB)</li>
          <li><i className="fas fa-eye"></i> Preview images and PDFs directly in the browser</li>
          <li><i className="fas fa-download"></i> Download your files anytime</li>
          <li><i className="fas fa-search"></i> Search through your uploaded files</li>
          <li><i className="fas fa-trash"></i> Delete files you no longer need</li>
          <li><i className="fas fa-mouse-pointer"></i> Drag and drop file upload support</li>
        </ul>
      </div>
      <div className="back-link">
        <Link to="/">
          <i className="fas fa-arrow-left"></i> Back to Dashboard
        </Link>
      </div>
    </div>
  );
};

// Main App Component
const App = () => {
  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <div className="app-logo">
            <i className="fas fa-file-upload"></i>
            <h1>FileVault</h1>
          </div>
          <nav className="app-nav">
            <Link to="/" className="nav-link">
              <i className="fas fa-home"></i> Home
            </Link>
            <Link to="/about" className="nav-link">
              <i className="fas fa-info-circle"></i> About
            </Link>
          </nav>
        </header>
        <main className="app-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </main>
        <footer className="app-footer">
          <p>&copy; {new Date().getFullYear()} FileVault. All rights reserved.</p>
        </footer>
      </div>
    </Router>
  );
};

// Mount the app to the DOM
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

export default App;
