import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';

const NotesApp = () => {
  const [notes, setNotes] = useState([]);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchNotes();
  }, []);

  const fetchNotes = async () => {
    const response = await axios.get('http://localhost:5091/notes');  // Backend port number
    setNotes(response.data);
  };

  const createNote = async () => {
    await axios.post('http://localhost:5091/notes', { title, content, category });  // Backend port number
    fetchNotes();
    navigate('/');
  };

  const updateNote = async (id) => {
    await axios.put(`http://localhost:5091/notes/${id}`, { title, content, category });  // Backend port number
    fetchNotes();
    navigate('/');
  };

  const archiveNote = async (id) => {
    await axios.delete(`http://localhost:5091/notes/${id}`);  // Backend port number
    fetchNotes();
  };

  const searchNotes = async () => {
    const response = await axios.get(`http://localhost:5091/notes/search?query=${searchQuery}`);  // Backend port number
    setNotes(response.data);
  };

  return (
    <Router>
      <div className="App">
        <nav>
          <Link to="/">Home</Link>
          <Link to="/create">Create Note</Link>
        </nav>
        <Routes>
          <Route path="/" element={
            <div>
              <input
                type="text"
                placeholder="Search notes..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <button onClick={searchNotes}>Search</button>
              <ul>
                {notes.map(note => (
                  <li key={note.id}>
                    <h2>{note.title}</h2>
                    <p>{note.content}</p>
                    <p>{note.category}</p>
                    <button onClick={() => archiveNote(note.id)}>Archive</button>
                    <Link to={`/edit/${note.id}`}>Edit</Link>
                  </li>
                ))}
              </ul>
            </div>
          } />
          <Route path="/create" element={
            <div>
              <input
                type="text"
                placeholder="Title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
              <textarea
                placeholder="Content"
                value={content}
                onChange={(e) => setContent(e.target.value)}
              />
              <input
                type="text"
                placeholder="Category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              />
              <button onClick={createNote}>Create Note</button>
            </div>
          } />
          <Route path="/edit/:id" element={
            <div>
              <input
                type="text"
                placeholder="Title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
              <textarea
                placeholder="Content"
                value={content}
                onChange={(e) => setContent(e.target.value)}
              />
              <input
                type="text"
                placeholder="Category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              />
              <button onClick={() => updateNote(window.location.pathname.split('/').pop())}>Update Note</button>
            </div>
          } />
        </Routes>
      </div>
    </Router>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<NotesApp />);
