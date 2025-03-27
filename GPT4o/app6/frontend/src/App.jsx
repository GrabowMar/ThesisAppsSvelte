import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
  const [notes, setNotes] = useState([]);
  const [archivedNotes, setArchivedNotes] = useState([]);
  const [newNote, setNewNote] = useState({ title: '', content: '', category: '' });
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch all notes on load
  useEffect(() => {
    fetchNotes();
  }, []);

  const fetchNotes = async () => {
    const res = await fetch('/api/notes');
    const data = await res.json();
    setNotes(data.notes || []);
  };

  const createNote = async (e) => {
    e.preventDefault();
    const res = await fetch('/api/notes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newNote),
    });
    const data = await res.json();
    if (data.note) {
      setNotes([...notes, data.note]);
      setNewNote({ title: '', content: '', category: '' });
    }
  };

  const deleteNote = async (id) => {
    await fetch(`/api/notes/${id}`, { method: 'DELETE' });
    setNotes(notes.filter(note => note.id !== id));
  };

  const archiveNote = async (id) => {
    const res = await fetch(`/api/notes/archive/${id}`, { method: 'PUT' });
    const data = await res.json();
    if (data.note) {
      setArchivedNotes([...archivedNotes, data.note]);
      setNotes(notes.filter(note => note.id !== id));
    }
  };

  const handleSearch = async (e) => {
    const res = await fetch(`/api/search?q=${encodeURIComponent(searchQuery)}`);
    const data = await res.json();
    setNotes(data.matching_notes || []);
  };

  return (
    <div className="App">
      <header>
        <h1>Notes Application</h1>
        <input
          type="text"
          placeholder="Search notes..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onBlur={handleSearch}
        />
      </header>
      <main>
        <h2>Create Note</h2>
        <form onSubmit={createNote}>
          <input
            type="text"
            placeholder="Note Title"
            value={newNote.title}
            onChange={(e) => setNewNote({ ...newNote, title: e.target.value })}
          />
          <textarea
            placeholder="Content"
            value={newNote.content}
            onChange={(e) => setNewNote({ ...newNote, content: e.target.value })}
          ></textarea>
          <input
            type="text"
            placeholder="Category"
            value={newNote.category}
            onChange={(e) => setNewNote({ ...newNote, category: e.target.value })}
          />
          <button type="submit">Add Note</button>
        </form>
        <h2>Notes</h2>
        {notes.map(note => (
          <div key={note.id} className="note">
            <h3>{note.title}</h3>
            <p>{note.content}</p>
            <span>{note.category}</span>
            <button onClick={() => deleteNote(note.id)}>Delete</button>
            <button onClick={() => archiveNote(note.id)}>Archive</button>
          </div>
        ))}
      </main>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
