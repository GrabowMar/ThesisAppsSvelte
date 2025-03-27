import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Switch, Link } from 'react-router-dom';
import axios from 'axios';
import './App.css';

const App = () => {
  const [notes, setNotes] = useState([]);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchNotes();
  }, []);

  const fetchNotes = async () => {
    const response = await axios.get('/api/notes');
    setNotes(response.data);
  };

  const createNote = async () => {
    const newNote = { title, content, archived: false };
    await axios.post('/api/notes', newNote);
    fetchNotes();
    setTitle('');
    setContent('');
  };

  const updateNote = async (id) => {
    const updatedNote = { title, content, archived: false };
    await axios.put(`/api/notes/${id}`, updatedNote);
    fetchNotes();
  };

  const deleteNote = async (id) => {
    await axios.delete(`/api/notes/${id}`);
    fetchNotes();
  };

  const archiveNote = async (id) => {
    await axios.post(`/api/notes/archive/${id}`);
    fetchNotes();
  };

  const searchNotes = async () => {
    const response = await axios.get(`/api/notes/search?query=${searchQuery}`);
    setNotes(response.data);
  };

  return (
    <Router>
      <div className="App">
        <nav>
          <Link to="/">Home</Link>
          <Link to="/create">Create Note</Link>
        </nav>
        <Switch>
          <Route exact path="/">
            <div>
              <input
                type="text"
                placeholder="Search notes..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <button onClick={searchNotes}>Search</button>
              <ul>
                {notes.map((note, index) => (
                  <li key={index}>
                    <h3>{note.title}</h3>
                    <p>{note.content}</p>
                    <button onClick={() => updateNote(index)}>Edit</button>
                    <button onClick={() => deleteNote(index)}>Delete</button>
                    <button onClick={() => archiveNote(index)}>Archive</button>
                  </li>
                ))}
              </ul>
            </div>
          </Route>
          <Route path="/create">
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
              ></textarea>
              <button onClick={createNote}>Create Note</button>
            </div>
          </Route>
        </Switch>
      </div>
    </Router>
  );
};

export default App;
