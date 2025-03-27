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
    } catch (err
