import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [notes, setNotes] = useState([]);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState('');
  const [query, setQuery] = useState('');
  const [archived, setArchived] = useState(false);

  useEffect(() => {
    fetch('/api/notes')
      .then(response => response.json())
      .then(data => setNotes(data));
  }, []);

  const handleCreateNote = () => {
    fetch('/api/create-note', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, content, category }),
    })
      .then(response => response.json())
      .then(data => console.log(data));
  };

  const handleUpdateNote = (id) => {
    fetch('/api/update-note/' + id, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, content, category }),
    })
      .then(response => response.json())
      .then(data => console.log(data));
  };

  const handleDeleteNote = (id) => {
    fetch('/api/delete-note/' + id, {
      method: 'POST',
    })
      .then(response => response.json())
      .then(data => console.log(data));
  };

  const handleArchiveNote = (id) => {
    fetch('/api/archive-note/' + id, {
      method: 'POST',
    })
      .then(response => response.json())
      .then(data => console.log(data));
  };

  const handleSearchNotes = () => {
    fetch('/api/search-notes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    })
      .then(response => response.json())
      .then(data => setNotes(data));
  };

  return (
    <div>
      <h1>Notes App</h1>
      <form>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Title"
        />
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Content"
        />
        <input
          type="text"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          placeholder="Category"
        />
        <button onClick={handleCreateNote}>Create Note</button>
      </form>
      <ul>
        {notes.map((note) => (
          <li key={note.id}>
            <h2>{note.title}</h2>
            <p>{note.content}</p>
            <p>Category: {note.category}</p>
            <button onClick={() => handleUpdateNote(note.id)}>Update</button>
            <button onClick={() => handleDeleteNote(note.id)}>Delete</button>
            <button onClick={() => handleArchiveNote(note.id)}>Archive</button>
          </li>
        ))}
      </ul>
      <form>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search"
        />
        <button onClick={handleSearchNotes}>Search</button>
      </form>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
