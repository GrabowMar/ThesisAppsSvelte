import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';

// Set up axios defaults
axios.defaults.baseURL = '/api';
axios.defaults.headers.common['Authorization'] = `Bearer ${localStorage.getItem('token')}`;

// Components
const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post('/login', { username, password });
      localStorage.setItem('token', response.data.token);
      window.location.href = '/dashboard';
    } catch (err) {
      setError('Invalid credentials');
    }
  };

  return (
    <form onSubmit={handleLogin}>
      <h2>Login</h2>
      {error && <p className="error">{error}</p>}
      <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" required />
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" required />
      <button type="submit">Login</button>
    </form>
  );
};

const Register = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');

  const handleRegister = async (e) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    try {
      await axios.post('/register', { username, password });
      window.location.href = '/login';
    } catch (err) {
      setError('Registration failed');
    }
  };

  return (
    <form onSubmit={handleRegister}>
      <h2>Register</h2>
      {error && <p className="error">{error}</p>}
      <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" required />
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" required />
      <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="Confirm Password" required />
      <button type="submit">Register</button>
    </form>
  );
};

const NoteList = ({ notes, onEdit, onArchive }) => (
  <ul>
    {notes.map(note => (
      <li key={note.id}>
        <h3>{note.title}</h3>
        <p>{note.content}</p>
        <p>Category: {note.category}</p>
        <p>Created: {new Date(note.created_at).toLocaleString()}</p>
        <p>Updated: {new Date(note.updated_at).toLocaleString()}</p>
        <button onClick={() => onEdit(note)}>Edit</button>
        <button onClick={() => onArchive(note)}>{note.is_archived ? 'Unarchive' : 'Archive'}</button>
      </li>
    ))}
  </ul>
);

const NoteForm = ({ initialNote, onSubmit, onCancel }) => {
  const [note, setNote] = useState(initialNote || { title: '', content: '', category: '' });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(note);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input type="text" value={note.title} onChange={(e) => setNote({ ...note, title: e.target.value })} placeholder="Title" required />
      <textarea value={note.content} onChange={(e) => setNote({ ...note, content: e.target.value })} placeholder="Content" required />
      <input type="text" value={note.category} onChange={(e) => setNote({ ...note, category: e.target.value })} placeholder="Category" required />
      <button type="submit">{initialNote ? 'Update' : 'Create'}</button>
      <button type="button" onClick={onCancel}>Cancel</button>
    </form>
  );
};

const Dashboard = () => {
  const [notes, setNotes] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [showArchived, setShowArchived] = useState(false);
  const [editingNote, setEditingNote] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchNotes();
  }, [searchTerm, categoryFilter, showArchived]);

  const fetchNotes = async () => {
    try {
      const response = await axios.get('/notes', {
        params: {
          search: searchTerm,
          category: categoryFilter,
          archived: showArchived
        }
      });
      setNotes(response.data.notes);
    } catch (err) {
      setError('Failed to fetch notes');
    }
  };

  const createNote = async (note) => {
    try {
      await axios.post('/notes', note);
      fetchNotes();
      setEditingNote(null);
    } catch (err) {
      setError('Failed to create note');
    }
  };

  const updateNote = async (note) => {
    try {
      await axios.put(`/notes/${note.id}`, note);
      fetchNotes();
      setEditingNote(null);
    } catch (err) {
      setError('Failed to update note');
    }
  };

  const deleteNote = async (note) => {
    try {
      await axios.delete(`/notes/${note.id}`);
      fetchNotes();
    } catch (err) {
      setError('Failed to delete note');
    }
  };

  const archiveNote = async (note) => {
    try {
      await axios.put(`/notes/${note.id}`, { ...note, is_archived: !note.is_archived });
      fetchNotes();
    } catch (err) {
      setError('Failed to archive/unarchive note');
    }
  };

  return (
    <div>
      <h1>Dashboard</h1>
      {error && <p className="error">{error}</p>}
      <input type="text" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} placeholder="Search notes" />
      <input type="text" value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)} placeholder="Filter by category" />
      <label>
        <input type="checkbox" checked={showArchived} onChange={(e) => setShowArchived(e.target.checked)} />
        Show archived notes
      </label>
      <button onClick={() => setEditingNote({})}>New Note</button>
      {editingNote ? (
        <NoteForm
          initialNote={editingNote}
          onSubmit={editingNote.id ? updateNote : createNote}
          onCancel={() => setEditingNote(null)}
        />
      ) : (
        <NoteList
          notes={notes}
          onEdit={setEditingNote}
          onArchive={archiveNote}
        />
      )}
    </div>
  );
};

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('token'));

  useEffect(() => {
    axios.interceptors.response.use(
      response => response,
      error => {
        if (error.response && error.response.status === 401) {
          localStorage.removeItem('token');
          setIsAuthenticated(false);
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }, []);

  return (
    <Router>
      <Routes>
        <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" /> : <Login />} />
        <Route path="/register" element={isAuthenticated ? <Navigate to="/dashboard" /> : <Register />} />
        <Route path="/dashboard" element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" />} />
        <Route path="/" element={<Navigate to="/dashboard" />} />
      </Routes>
    </Router>
  );
};

// Mounting logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
