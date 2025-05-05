import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// API service
const API_URL = 'http://localhost:5347/api';

const apiService = {
  // Auth
  register: async (userData) => {
    const response = await fetch(`${API_URL}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });
    return response.json();
  },
  
  login: async (credentials) => {
    const response = await fetch(`${API_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    });
    return response.json();
  },
  
  getProfile: async (token) => {
    const response = await fetch(`${API_URL}/profile`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
  },
  
  // Folders
  getFolders: async (token, parentId = null) => {
    const url = parentId 
      ? `${API_URL}/folders?parent_id=${parentId}` 
      : `${API_URL}/folders`;
    const response = await fetch(url, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
  },
  
  createFolder: async (token, folderData) => {
    const response = await fetch(`${API_URL}/folders`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}` 
      },
      body: JSON.stringify(folderData)
    });
    return response.json();
  },
  
  updateFolder: async (token, folderId, folderData) => {
    const response = await fetch(`${API_URL}/folders/${folderId}`, {
      method: 'PUT',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}` 
      },
      body: JSON.stringify(folderData)
    });
    return response.json();
  },
  
  deleteFolder: async (token, folderId) => {
    const response = await fetch(`${API_URL}/folders/${folderId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
  },
  
  // Files
  getFiles: async (token, folderId = null, fileType = null) => {
    let url = `${API_URL}/files`;
    const params = new URLSearchParams();
    
    if (folderId) params.append('folder_id', folderId);
    if (fileType) params.append('file_type', fileType);
    
    if (params.toString()) {
      url += `?${params.toString()}`;
    }
    
    const response = await fetch(url, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
  },
  
  uploadFile: async (token, fileData, folderId) => {
    const formData = new FormData();
    formData.append('file', fileData);
    if (folderId) formData.append('folder_id', folderId);
    
    const response = await fetch(`${API_URL}/files`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    });
    return response.json();
  },
  
  updateFile: async (token, fileId, fileData) => {
    const response = await fetch(`${API_URL}/files/${fileId}`, {
      method: 'PUT',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}` 
      },
      body: JSON.stringify(fileData)
    });
    return response.json();
  },
  
  deleteFile: async (token, fileId) => {
    const response = await fetch(`${API_URL}/files/${fileId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
  },
  
  downloadFile: (token, fileId) => {
    window.open(`${API_URL}/files/${fileId}?token=${token}`);
  },
  
  shareFile: async (token, fileId) => {
    const response = await fetch(`${API_URL}/share`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}` 
      },
      body: JSON.stringify({ file_id: fileId })
    });
    return response.json();
  },
  
  unshareFile: async (token, fileId) => {
    const response = await fetch(`${API_URL}/share/${fileId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
  },
  
  // Quota
  getStorageInfo: async (token) => {
    const response = await fetch(`${API_URL}/quota`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
  }
};

// Auth context for managing user state
const AuthContext = React.createContext();

function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const verifyToken = async () => {
      if (token) {
        try {
          const userData = await apiService.getProfile(token);
          setUser(userData);
        } catch (error) {
          console.error('Token verification failed', error);
          logout();
        } finally {
          setLoading(false);
        }
      } else {
        setLoading(false);
      }
    };

    verifyToken();
  }, [token]);

  const login = async (credentials) => {
    try {
      const response = await apiService.login(credentials);
      if (response.token) {
        localStorage.setItem('token', response.token);
        setToken(response.token);
        setUser(response.user);
        return { success: true };
      } else {
        return { success: false, error: response.error };
      }
    } catch (error) {
      console.error('Login error', error);
      return { success: false, error: 'An unexpected error occurred' };
    }
  };

  const register = async (userData) => {
    try {
      const response = await apiService.register(userData);
      if (response.token) {
        localStorage.setItem('token', response.token);
        setToken(response.token);
        setUser(response.user);
        return { success: true };
      } else {
        return { success: false, error: response.error };
      }
    } catch (error) {
      console.error('Registration error', error);
      return { success: false, error: 'An unexpected error occurred' };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Components
const LoginPage = () => {
  const { login } = React.useContext(AuthContext);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    
    if (!username || !password) {
      setError('Username and password are required');
      setIsLoading(false);
      return;
    }
    
    try {
      const result = await login({ username, password });
      if (!result.success) {
        setError(result.error || 'Invalid credentials');
      }
        } catch (err) {
      setError('Login failed. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-form">
        <h2>Login to Your Account</h2>
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={isLoading}
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
            />
          </div>
          <button type="submit" disabled={isLoading} className="btn primary">
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>
      </div>
    </div>
  );
};

const RegisterPage = () => {
  const { register } = React.useContext(AuthContext);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    // Validate form
    if (!formData.username || !formData.email || !formData.password) {
      setError('All fields are required');
      return;
    }
    
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    setIsLoading(true);
    
    try {
      const { confirmPassword, ...userData } = formData;
      const result = await register(userData);
      if (!result.success) {
        setError(result.error || 'Registration failed');
      }
    } catch (err) {
      setError('Registration failed. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-form">
        <h2>Create Account</h2>
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              disabled={isLoading}
            />
          </div>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              disabled={isLoading}
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              disabled={isLoading}
            />
          </div>
          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              id="confirmPassword"
              type="password"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              disabled={isLoading}
            />
          </div>
          <button type="submit" disabled={isLoading} className="btn primary">
            {isLoading ? 'Creating Account...' : 'Register'}
          </button>
        </form>
      </div>
    </div>
  );
};

// Dashboard components
const StorageQuota = () => {
  const { token } = React.useContext(AuthContext);
  const [storageInfo, setStorageInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchStorageInfo = async () => {
      try {
        const info = await apiService.getStorageInfo(token);
        setStorageInfo(info);
      } catch (err) {
        setError('Failed to load storage info');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchStorageInfo();
  }, [token]);

  if (loading) return <div className="storage-quota loading">Loading storage info...</div>;
  if (error) return <div className="storage-quota error">{error}</div>;

  const formatSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="storage-quota">
      <h3>Storage Quota</h3>
      <div className="progress-container">
        <div 
          className="progress-bar" 
          style={{ width: `${storageInfo.percentage_used}%` }}
        ></div>
      </div>
      <div className="quota-info">
        <span>{formatSize(storageInfo.used)} used</span>
        <span>{formatSize(storageInfo.available)} available</span>
      </div>
      <div className="quota-percentage">
        {storageInfo.percentage_used.toFixed(1)}% of {formatSize(storageInfo.quota)}
      </div>
    </div>
  );
};

const FileTypeIcon = ({ fileType }) => {
  let icon = '📄'; // Default document icon
  
  if (fileType.includes('image')) {
    icon = '🖼️';
  } else if (fileType.includes('video')) {
    icon = '🎬';
  } else if (fileType.includes('audio')) {
    icon = '🎵';
  } else if (fileType.includes('pdf')) {
    icon = '📕';
  } else if (fileType.includes('zip') || fileType.includes('compressed')) {
    icon = '🗜️';
  } else if (fileType.includes('text')) {
    icon = '📝';
  } else if (fileType.includes('spreadsheet') || fileType.includes('excel')) {
    icon = '📊';
  } else if (fileType.includes('presentation') || fileType.includes('powerpoint')) {
    icon = '📑';
  }
  
  return <span className="file-icon">{icon}</span>;
};

const FileItem = ({ file, onSelect, isSelected, onDelete, onShare }) => {
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString();
  };

  const formatSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div 
      className={`file-item ${isSelected ? 'selected' : ''}`} 
      onClick={() => onSelect(file)}
    >
      <div className="file-icon-name">
        <FileTypeIcon fileType={file.file_type} />
        <span className="file-name">{file.filename}</span>
      </div>
      <div className="file-info">
        <span className="file-size">{formatSize(file.file_size)}</span>
        <span className="file-date">{formatDate(file.upload_date)}</span>
      </div>
      <div className="file-actions">
        {file.is_public && (
          <button className="btn share" title="Shared">
            🔗
          </button>
        )}
        <button 
          className="btn share" 
          onClick={(e) => {
            e.stopPropagation();
            onShare(file);
          }}
          title={file.is_public ? "Manage Share" : "Share File"}
        >
          {file.is_public ? '🔗' : '📤'}
        </button>
        <button 
          className="btn delete" 
          onClick={(e) => {
            e.stopPropagation();
            onDelete(file);
          }}
          title="Delete File"
        >
          🗑️
        </button>
      </div>
    </div>
  );
};

const FolderItem = ({ folder, onOpen, onDelete, onRename }) => {
  return (
    <div className="folder-item" onClick={() => onOpen(folder)}>
      <div className="folder-icon-name">
        <span className="folder-icon">📁</span>
        <span className="folder-name">{folder.name}</span>
      </div>
      <div className="folder-actions">
        <button 
          className="btn rename" 
          onClick={(e) => {
            e.stopPropagation();
            onRename(folder);
          }}
          title="Rename Folder"
        >
          ✏️
        </button>
        <button 
          className="btn delete" 
          onClick={(e) => {
            e.stopPropagation();
            onDelete(folder);
          }}
          title="Delete Folder"
        >
          🗑️
        </button>
      </div>
    </div>
  );
};

const CreateFolderModal = ({ isOpen, onClose, onSubmit, parentId }) => {
  const [folderName, setFolderName] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!folderName.trim()) {
      setError('Folder name is required');
      return;
    }
    onSubmit({ name: folderName, parent_id: parentId });
    setFolderName('');
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h3>Create New Folder</h3>
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="folderName">Folder Name</label>
            <input
              id="folderName"
              type="text"
              value={folderName}
              onChange={(e) => setFolderName(e.target.value)}
            />
          </div>
          <div className="modal-actions">
            <button type="button" className="btn secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn primary">
              Create
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const RenameFolderModal = ({ isOpen, folder, onClose, onSubmit }) => {
  const [folderName, setFolderName] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (folder && isOpen) {
      setFolderName(folder.name);
    }
  }, [folder, isOpen]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!folderName.trim()) {
      setError('Folder name is required');
      return;
    }
    onSubmit(folder.id, { name: folderName });
    onClose();
  };

  if (!isOpen || !folder) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h3>Rename Folder</h3>
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="folderName">Folder Name</label>
            <input
              id="folderName"
              type="text"
              value={folderName}
              onChange={(e) => setFolderName(e.target.value)}
            />
          </div>
          <div className="modal-actions">
            <button type="button" className="btn secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn primary">
              Rename
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const ShareFileModal = ({ isOpen, file, onClose, onShare, onUnshare }) => {
  const [copied, setCopied] = useState(false);
  
  if (!isOpen || !file) return null;
  
  const shareUrl = file.is_public ? `${window.location.origin}/share/${file.share_token}` : '';
  
  const copyToClipboard = () => {
    navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h3>Share File</h3>
        <p className="file-share-name">{file.filename}</p>
        
        {file.is_public ? (
          <div className="share-options">
            <p>Anyone with the link can access this file:</p>
            <div className="share-link">
              <input type="text" value={shareUrl} readOnly />
              <button 
                className="btn primary" 
                onClick={copyToClipboard}
              >
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </div>
            <button 
              className="btn danger" 
              onClick={() => {
                onUnshare(file.id);
                onClose();
              }}
            >
              Stop Sharing
            </button>
          </div>
        ) : (
          <div className="share-options">
            <p>This file is currently private.</p>
            <button 
              className="btn primary" 
              onClick={() => {
                onShare(file.id);
                onClose();
              }}
            >
              Make Public & Generate Link
            </button>
          </div>
        )}
        
        <div className="modal-actions mt-20">
          <button type="button" className="btn secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

const FileExplorer = () => {
  const { token } = React.useContext(AuthContext);
  const [currentPath, setCurrentPath] = useState([]);
  const [folders, setFolders] = useState([]);
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [createFolderModalOpen, setCreateFolderModalOpen] = useState(false);
  const [renameFolderModalOpen, setRenameFolderModalOpen] = useState(false);
  const [folderToRename, setFolderToRename] = useState(null);
  const [shareFileModalOpen, setShareFileModalOpen] = useState(false);
  const [fileToShare, setFileToShare] = useState(null);
  const [fileTypeFilter, setFileTypeFilter] = useState('');

  // Get current folder ID from path
  const getCurrentFolderId = () => {
    return currentPath.length > 0 ? currentPath[currentPath.length - 1].id : null;
  };

  // Load current folder contents
  const loadFolderContents = async (folderId = null) => {
    setLoading(true);
    setError('');
    
    try {
      // Load folders in current directory
      const folderData = await apiService.getFolders(token, folderId);
      setFolders(folderData);
      
      // Load files in current directory
      const fileData = await apiService.getFiles(token, folderId, fileTypeFilter);
      setFiles(fileData);
    } catch (err) {
      setError('Failed to load folder contents');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    loadFolderContents();
  }, [token]);

  // Load when path or filter changes
  useEffect(() => {
    const folderId = getCurrentFolderId();
    loadFolderContents(folderId);
  }, [currentPath, fileTypeFilter, token]);

  // Navigate to a folder
  const handleFolderOpen = (folder) => {
    setCurrentPath([...currentPath, folder]);
  };

  // Navigate up one level
  const handleGoBack = () => {
    if (currentPath.length === 0) return;
    setCurrentPath(currentPath.slice(0, -1));
  };

  // Create new folder
  const handleCreateFolder = async (folderData) => {
    try {
      await apiService.createFolder(token, folderData);
      loadFolderContents(getCurrentFolderId());
      setCreateFolderModalOpen(false);
    } catch (err) {
      console.error('Failed to create folder', err);
    }
  };

  // Rename folder
  const handleRenameFolder = async (folderId, folderData) => {
    try {
      await apiService.updateFolder(token, folderId, folderData);
      loadFolderContents(getCurrentFolderId());
    } catch (err) {
      console.error('Failed to rename folder', err);
    }
  };

  // Delete folder
  const handleDeleteFolder = async (folder) => {
    if (!window.confirm(`Are you sure you want to delete "${folder.name}" and all its contents?`)) {
      return;
    }
    
    try {
      await apiService.deleteFolder(token, folder.id);
      loadFolderContents(getCurrentFolderId());
    } catch (err) {
      console.error('Failed to delete folder', err);
    }
  };

  // Handle file upload
  const handleFileUpload = async (e) => {
    const files = e.target.files;
    if (!files.length) return;
    
    try {
      for (let i = 0; i < files.length; i++) {
        await apiService.uploadFile(token, files[i], getCurrentFolderId());
      }
      
      // Reload current folder contents
      loadFolderContents(getCurrentFolderId());
    } catch (err) {
      console.error('File upload failed', err);
    }
  };

  // Download selected file
  const handleFileDownload = (file) => {
    apiService.downloadFile(token, file.id);
  };

  // Delete file
  const handleDeleteFile = async (file) => {
    if (!window.confirm(`Are you sure you want to delete "${file.filename}"?`)) {
      return;
    }
    
    try {
      await apiService.deleteFile(token, file.id);
      loadFolderContents(getCurrentFolderId());
    } catch (err) {
      console.error('Failed to delete file', err);
    }
  };

  // Share file
  const handleShareFile = async (fileId) => {
    try {
      await apiService.shareFile(token, fileId);
      loadFolderContents(getCurrentFolderId());
    } catch (err) {
      console.error('Failed to share file', err);
    }
  };

  // Unshare file
  const handleUnshareFile = async (fileId) => {
    try {
      await apiService.unshareFile(token, fileId);
      loadFolderContents(getCurrentFolderId());
    } catch (err) {
      console.error('Failed to unshare file', err);
    }
  };

  // File type filter options
  const fileTypeOptions = [
    { value: '', label: 'All Files' },
    { value: 'image/', label: 'Images' },
    { value: 'video/', label: 'Videos' },
    { value: 'audio/', label: 'Audio' },
    { value: 'application/pdf', label: 'PDF Documents' },
    { value: 'text/', label: 'Text Files' },
    { value: 'application/vnd.ms-excel', label: 'Excel Files' },
    { value: 'application/zip', label: 'Archives' }
  ];

  return (
    <div className="file-explorer">
      <div className="explorer-header">
        <div className="path-navigation">
          <button 
            className="btn back"
            onClick={handleGoBack}
            disabled={currentPath.length === 0}
          >
            ← Back
          </button>
          
          <div className="current-path">
            <span className="path-item root" onClick={() => setCurrentPath([])}>
              Home
            </span>
            {currentPath.map((folder, index) => (
              <React.Fragment key={folder.id}>
                <span className="path-separator">/</span>
                <span 
                  className="path-item"
                  onClick={() => setCurrentPath(currentPath.slice(0, index + 1))}
                >
                  {folder.name}
                </span>
              </React.Fragment>
            ))}
          </div>
        </div>
        
        <div className="explorer-actions">
          <div className="file-type-filter">
            <select
              value={fileTypeFilter}
              onChange={(e) => setFileTypeFilter(e.target.value)}
            >
              {fileTypeOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          
          <button 
            className="btn create-folder"
            onClick={() => setCreateFolderModalOpen(true)}
          >
            New Folder
          </button>
          
          <label className="btn upload">
            Upload File
            <input 
              type="file" 
              onChange={handleFileUpload} 
              multiple 
              style={{ display: 'none' }} 
            />
          </label>
        </div>
      </div>
      
      <div className="explorer-content">
        {loading ? (
          <div className="loading-indicator">Loading...</div>
        ) : error ? (
          <div className="error-message">{error}</div>
        ) : (
          <div>
            {folders.length === 0 && files.length === 0 ? (
              <div className="empty-folder">
                <p>This folder is empty</p>
              </div>
            ) : (
              <>
                {folders.length > 0 && (
                  <div className="folders-section">
                    <h3>Folders</h3>
                    <div className="folders-list">
                      {folders.map(folder => (
                        <FolderItem 
                          key={folder.id}
                          folder={folder}
                          onOpen={handleFolderOpen}
                          onDelete={handleDeleteFolder}
                          onRename={(folder) => {
                            setFolderToRename(folder);
                            setRenameFolderModalOpen(true);
                          }}
                        />
                      ))}
                    </div>
                  </div>
                )}
                
                {files.length > 0 && (
                  <div className="files-section">
                    <h3>Files</h3>
                    <div className="files-list">
                      {files.map(file => (
                        <FileItem 
                          key={file.id}
                          file={file}
                          isSelected={selectedFile && selectedFile.id === file.id}
                          onSelect={(file) => {
                            setSelectedFile(file);
                            handleFileDownload(file);
                          }}
                          onDelete={handleDeleteFile}
                          onShare={(file) => {
                            setFileToShare(file);
                            setShareFileModalOpen(true);
                          }}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
      
      {/* Modals */}
      <CreateFolderModal 
        isOpen={createFolderModalOpen}
        onClose={() => setCreateFolderModalOpen(false)}
        onSubmit={handleCreateFolder}
        parentId={getCurrentFolderId()}
      />
      
      <RenameFolderModal 
        isOpen={renameFolderModalOpen}
        folder={folderToRename}
        onClose={() => {
          setRenameFolderModalOpen(false);
          setFolderToRename(null);
        }}
        onSubmit={handleRenameFolder}
      />
      
      <ShareFileModal 
        isOpen={shareFileModalOpen}
        file={fileToShare}
        onClose={() => {
          setShareFileModalOpen(false);
          setFileToShare(null);
        }}
        onShare={handleShareFile}
        onUnshare={handleUnshareFile}
      />
    </div>
  );
};

// Dashboard page
const DashboardPage = () => {
  return (
    <div className="dashboard">
      <StorageQuota />
      <FileExplorer />
    </div>
  );
};

// Layout components
const Navbar = () => {
  const { logout, isAuthenticated } = React.useContext(AuthContext);

  return (
    <nav className="navbar">
      <div className="nav-brand">
        <span className="logo">☁️</span>
        <h1>CloudStore</h1>
      </div>
      {isAuthenticated && (
        <div className="nav-actions">
          <button className="btn logout" onClick={logout}>
            Logout
          </button>
        </div>
      )}
    </nav>
  );
};

// Main App component
const App = () => {
  const [currentPage, setCurrentPage] = useState('login');
  const { loading, isAuthenticated } = React.useContext(AuthContext);
  
  // Handle navigation logic
  useEffect(() => {
    if (isAuthenticated) {
      setCurrentPage('dashboard');
    } else if (!loading) {
      setCurrentPage('login');
    }
  }, [isAuthenticated, loading]);

  // Render page based on current state
  const renderPage = () => {
    if (loading) {
      return <div className="loading-app">Loading...</div>;
    }
    
    if (isAuthenticated) {
      return <DashboardPage />;
    }
    
    return currentPage === 'login' ? (
      <div className="auth-container">
        <LoginPage />
        <p className="auth-switch">
          Don't have an account? 
          <button className="link-btn" onClick={() => setCurrentPage('register')}>
            Register
          </button>
        </p>
      </div>
    ) : (
      <div className="auth-container">
        <RegisterPage />
        <p className="auth-switch">
          Already have an account? 
          <button className="link-btn" onClick={() => setCurrentPage('login')}>
            Login
          </button>
        </p>
      </div>
    );
  };

  return (
    <div className="app-container">
      <Navbar />
      <main className="main-content">
        {renderPage()}
      </main>
    </div>
  );
};

// Wrap the App with the AuthProvider and render
const AppWithAuth = () => (
  <AuthProvider>
    <App />
  </AuthProvider>
);

// Mount to DOM
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<AppWithAuth />);

export default AppWithAuth;


