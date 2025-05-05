import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useParams, useNavigate } from 'react-router-dom';
import { styled } from '@mui/material/styles';
import axios from 'axios';
import { jwtDecode } from 'jwt-decode';
import { Button, TextField, Paper, Typography, CircularProgress, List, ListItem, ListItemIcon, ListItemText, LinearProgress, IconButton } from '@mui/material';
import { Folder, InsertDriveFile, Upload, ArrowBack } from '@mui/icons-material';
import './App.css';

// Configure axios
axios.defaults.baseURL = 'http://localhost:5587/api';
axios.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Main App Component
export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<AuthHandler />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/dashboard/*" element={<Dashboard />} />
        <Route path="/shared/:token" element={<SharedFile />} />
      </Routes>
    </Router>
  );
}

function AuthHandler() {
  const navigate = useNavigate();
  
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        jwtDecode(token);
        navigate('/dashboard');
      } catch {
        navigate('/login');
      }
    } else {
      navigate('/login');
    }
  }, []);

  return <CircularProgress />;
}

function Login() {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const { data } = await axios.post('/login', credentials);
      localStorage.setItem('token', data.access_token);
      navigate('/dashboard');
    } catch (err) {
      setError('Invalid username or password');
    }
  };

  return (
    <AuthContainer>
      <Paper elevation={3} className="auth-paper">
        <Typography variant="h5">Login</Typography>
        <form onSubmit={handleLogin}>
          <TextField
            label="Username"
            value={credentials.username}
            onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
            fullWidth
            margin="normal"
          />
          <TextField
            label="Password"
            type="password"
            value={credentials.password}
            onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
            fullWidth
            margin="normal"
          />
          {error && <Typography color="error">{error}</Typography>}
          <Button type="submit" variant="contained" fullWidth color="primary">
            Login
          </Button>
        </form>
        <Link to="/register">Create an account</Link>
      </Paper>
    </AuthContainer>
  );
}

function Dashboard() {
  const [files, setFiles] = useState([]);
  const [currentPath, setCurrentPath] = useState('');
  const [storageInfo, setStorageInfo] = useState({ used: 0, quota: 100000000 });
  const navigate = useNavigate();

  const loadFiles = async (path = '') => {
    try {
      const { data } = await axios.get('/files', { params: { path } });
      setFiles(data);
      setCurrentPath(path);
    } catch (err) {
      console.error(err);
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append('file', file);
    formData.append('path', currentPath);
    
    try {
      await axios.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      loadFiles(currentPath);
    } catch (err) {
      alert(err.response?.data?.msg || 'Upload failed');
    }
  };

  return (
    <div>
      <nav>
        <input type="file" onChange={handleUpload} hidden id="upload-input" />
        <Button component="label" htmlFor="upload-input" startIcon={<Upload />}>
          Upload
        </Button>
        <StorageProgress value={(storageInfo.used / storageInfo.quota) * 100} />
      </nav>
      
      <FileList>
        {files.map(file => (
          <ListItem button key={file.id} onClick={() => file.is_folder && loadFiles(file.path + '/' + file.name)}>
            <ListItemIcon>
              {file.is_folder ? <Folder /> : <InsertDriveFile />}
            </ListItemIcon>
            <ListItemText primary={file.name} secondary={`${formatBytes(file.size)}`} />
            {!file.is_folder && <ShareButton fileId={file.id} />}
          </ListItem>
        ))}
      </FileList>
    </div>
  );
}

// Additional Components and Styling (shared here to fit single-file constraint)
const AuthContainer = styled('div')({
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  height: '100vh',
  '.auth-paper': {
    padding: '2rem',
    width: '400px',
    textAlign: 'center',
  }
});

const StorageProgress = styled(LinearProgress)({
  margin: '1rem',
  height: '10px',
  borderRadius: '5px',
});

const FileList = styled(List)({
  maxWidth: '800px',
  margin: '0 auto',
});

function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
