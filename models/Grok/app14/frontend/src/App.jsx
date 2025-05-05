import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// State Management
const [currentPage, setCurrentPage] = useState('login');
const [user, setUser] = useState(null);
const [files, setFiles] = useState([]);
const [folders, setFolders] = useState([]);
const [storageInfo, setStorageInfo] = useState({ used: 0, quota: 0, percentage: 0 });
const [selectedFolder, setSelectedFolder] = useState(null);
const [fileTypeFilter, setFileTypeFilter] = useState('');

// API Calls
const apiUrl = 'http://localhost:6007/api';

const login = async (username, password) => {
  try {
    const response = await fetch(`${apiUrl}/login`, {
      method: 'POST',
      headers: {
        'Authorization': 'Basic ' + btoa(`${username}:${password}`)
      }
    });
    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('token', data.token);
      setUser({ username });
      setCurrentPage('dashboard');
    } else {
      alert('Login failed');
    }
  } catch (error) {
    console.error('Login error:', error);
    alert('An error occurred during login');
  }
};

const register = async (username, password) => {
  try {
    const response = await fetch(`${apiUrl}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ username, password })
    });
    if (response.ok) {
      alert('Registration successful. Please log in.');
      setCurrentPage('login');
    } else {
      alert('Registration failed');
    }
  } catch (error) {
    console.error('Registration error:', error);
    alert('An error occurred during registration');
  }
};

const fetchFiles = async () => {
  try {
    const response = await fetch(`${apiUrl}/files`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    if (response.ok) {
      const data = await response.json();
      setFiles(data);
    } else {
      console.error('Failed to fetch files');
    }
  } catch (error) {
    console.error('Error fetching files:', error);
  }
};

const fetchFolders = async () => {
  try {
    const response = await fetch(`${apiUrl}/folders`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    if (response.ok) {
      const data = await response.json();
      setFolders(data);
    } else {
      console.error('Failed to fetch folders');
    }
  } catch (error) {
    console.error('Error fetching folders:', error);
  }
};

const fetchStorageInfo = async () => {
  try {
    const response = await fetch(`${apiUrl}/storage`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    if (response.ok) {
      const data = await response.json();
      setStorageInfo(data);
    } else {
      console.error('Failed to fetch storage info');
    }
  } catch (error) {
    console.error('Error fetching storage info:', error);
  }
};

const uploadFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  if (selectedFolder) {
    formData.append('folder_id', selectedFolder);
  }
  try {
    const response = await fetch(`${apiUrl}/files`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: formData
    });
    if (response.ok) {
      alert('File uploaded successfully');
      fetchFiles();
      fetchStorageInfo();
    } else {
      alert('File upload failed');
    }
  } catch (error) {
    console.error('Error uploading file:', error);
    alert('An error occurred during file upload');
  }
};

const createFolder = async (name, parentId = null) => {
  try {
    const response = await fetch(`${apiUrl}/folders`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({ name, parent_id: parentId })
    });
    if (response.ok) {
      alert('Folder created successfully');
      fetchFolders();
    } else {
      alert('Folder creation failed');
    }
  } catch (error) {
    console.error('Error creating folder:', error);
    alert('An error occurred during folder creation');
  }
};

const shareFile = async (fileId) => {
  try {
    const response = await fetch(`${apiUrl}/share/${fileId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    if (response.ok) {
      const data = await response.json();
      const shareUrl = `${window.location.origin}/share/${data.share_token}`;
      alert(`File shared successfully. Share URL: ${shareUrl}`);
    } else {
      alert('File sharing failed');
    }
  } catch (error) {
    console.error('Error sharing file:', error);
    alert('An error occurred during file sharing');
  }
};

// Lifecycle Functions
useEffect(() => {
  if (user) {
    fetchFiles();
    fetchFolders();
    fetchStorageInfo();
  }
}, [user]);

// Event Handlers
const handleLogin = (e) => {
  e.preventDefault();
  const username = e.target.username.value;
  const password = e.target.password.value;
  login(username, password);
};

const handleRegister = (e) => {
  e.preventDefault();
  const username = e.target.username.value;
  const password = e.target.password.value;
  register(username, password);
};

const handleFileUpload = (e) => {
  const file = e.target.files[0];
  uploadFile(file);
};

const handleFolderCreation = (e) => {
  e.preventDefault();
  const name = e.target.name.value;
  createFolder(name, selectedFolder);
};

const handleFileShare = (fileId) => {
  shareFile(fileId);
};

const handleFolderSelect = (folderId) => {
  setSelectedFolder(folderId);
  fetchFiles();
};

const handleFileTypeFilter = (e) => {
  setFileTypeFilter(e.target.value);
};

// UI Components
const LoginPage = () => (
  <form onSubmit={handleLogin}>
    <input type="text" name="username" placeholder="Username" required />
    <input type="password" name="password" placeholder="Password" required />
    <button type="submit">Login</button>
    <button type="button" onClick={() => setCurrentPage('register')}>Register</button>
  </form>
);

const RegisterPage = () => (
  <form onSubmit={handleRegister}>
    <input type="text" name="username" placeholder="Username" required />
    <input type="password" name="password" placeholder="Password" required />
    <button type="submit">Register</button>
    <button type="button" onClick={() => setCurrentPage('login')}>Back to Login</button>
  </form>
);

const DashboardPage = () => (
  <div>
    <h2>Welcome, {user.username}</h2>
    <div>
      <h3>Storage Usage</h3>
      <p>Used: {Math.round(storageInfo.used / (1024 * 1024))} MB / {Math.round(storageInfo.quota / (1024 * 1024))} MB</p>
      <progress value={storageInfo.percentage} max="100"></progress>
    </div>
    <div>
      <h3>File Type Filter</h3>
      <select onChange={handleFileTypeFilter}>
        <option value="">All</option>
        <option value="txt">Text</option>
        <option value="pdf">PDF</option>
        <option value="png,jpg,jpeg,gif">Images</option>
      </select>
    </div>
    <div>
      <h3>Folders</h3>
      <button onClick={() => setSelectedFolder(null)}>Root</button>
      {folders.map(folder => (
        <button key={folder.id} onClick={() => handleFolderSelect(folder.id)}>
          {folder.name}
        </button>
      ))}
      <form onSubmit={handleFolderCreation}>
        <input type="text" name="name" placeholder="New Folder Name" required />
        <button type="submit">Create Folder</button>
      </form>
    </div>
    <div>
      <h3>Files</h3>
      <input type="file" onChange={handleFileUpload} />
      {files
        .filter(file => !fileTypeFilter || fileTypeFilter.split(',').includes(file.name.split('.').pop().toLowerCase()))
        .filter(file => !selectedFolder || file.folder_id === selectedFolder)
        .map(file => (
          <div key={file.id}>
            <a href={`${apiUrl}/files/${file.id}`} download>{file.name}</a>
            <button onClick={() => handleFileShare(file.id)}>Share</button>
          </div>
        ))}
    </div>
    <button onClick={() => {
      localStorage.removeItem('token');
      setUser(null);
      setCurrentPage('login');
    }}>Logout</button>
  </div>
);

// Main App Component
const App = () => {
  return (
    <div className="app">
      <h1>File Storage System</h1>
      {currentPage === 'login' && <LoginPage />}
      {currentPage === 'register' && <RegisterPage />}
      {currentPage === 'dashboard' && user && <DashboardPage />}
    </div>
  );
};

// Mounting Logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
