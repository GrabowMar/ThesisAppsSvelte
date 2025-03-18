import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
  const [notes, setNotes] = useState([]);
  const [archivedNotes, setArchivedNotes] = useState([]);
  const [newNote, setNewNote] = useState({ title: '', content: '', category: 'Uncategorized' });
  const [editNote, setEditNote] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isArchived, setIsArchived] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchNotes();
    fetchArchivedNotes();
  }, []);

  const fetchNotes = async () => {
    try {
      const response = await fetch('http://localhost:5171/api/notes');
      const data = await response.json();
      setNotes(data);
    } catch (err) {
      setError('Failed to fetch notes.');
    }
  };

  const fetchArchivedNotes = async () => {
    try {
      const response = await.fetch('http://localhost:5171/api/notes/archived');
      const data = await response.json();
      setArchivedNotes(data);
    } catch (err) {
      setError('Failed to fetch archived notes.');
    }
  };

  const handleCreateNote = async () => {
    try {
      const response = await fetch('http://localhost:5171/api/notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newNote),
      });
      const data = await response.json();
      setNotes([...notes, data]);
      setNewNote({ title: '', content: '', category: 'Uncategorized' });
    } catch (err) {
      setError('Failed to create note.');
    }
  };

  const handleUpdateNote = async (noteId, updatedNote) => {
    try {
      const response = await fetch(`http://localhost:5171/api/notes/${noteId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedNote),
      });
      const data = await response.json();
      setNotes(notes.map(note => (note.id === noteId ? data : note)));
      setEditNote(null);
    } catch (err) {
      setError('Failed to update note.');
    }
  };

  const handleDeleteNote = async (noteId) => {
    try {
      await fetch(`http://localhost:5171/api/notes/${noteId}`, { method: 'DELETE' });
      setNotes(notes.filter(note => note.id !== noteId));
    } catch (err) {
      setError('Failed to delete note.');
    }
  };

  const handleToggleArchive = async (noteId, archiveStatus) => {
    try {
      const response = await fetch(`http://localhost:5171/api/notes/${noteId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ archived: !archiveStatus }),
      });
      const data = await response.json();
      fetchNotes();
      fetchArchivedNotes();
    } catch (err) {
      setError('Failed to toggle archive status.');
    }
  };

  const handleSearch = async () => {
    try {
      const response = await fetch(`http://localhost:5171/api/notes/search?q=${searchQuery}`);
      const data = await response.json();
      setNotes(data);
    } catch (err) {
      setError('Failed to search notes.');
    }
  };

  const renderNotes = (notesList) => (
    notesList.map((note) => (
      <div key={note.id} className="note-card">
        <h3>{note.title}</h3>
        <p>{note.content}</p>
        <small>Category: {note.category}</small>
        <div className="note-actions">
          <button onClick={() => setEditNote(note)}>Edit</button>
          <button onClick={() => handleToggleArchive(note.id, note.archived)}>
            {note.archived ? 'Unarchive' : 'Archive'}
          </button>
          <button onClick={() => handleDeleteNote(note.id)}>Delete</button>
        </div>
      </div>
    ))
  );

  return (
    <div className="app">
      <h1>Notes Application</h1>
      {error && <p className="error">{error}</p>}
      <div className="note-form">
        <h2>{editNote ? 'Edit Note' : 'Create Note'}</h2>
        <input
          type="text"
          placeholder="Title"
          value={editNote ? editNote.title : newNote.title}
          onChange={(e) =>
            editNote
              ? setEditNote({ ...editNote, title: e.target.value })
              : setNewNote({ ...newNote, title: e.target.value })
          }
        />
        <textarea
          placeholder="Content"
          value={editNote ? editNote.content : newNote.content}
          onChange={(e) =>
            editNote
              ? setEditNote({ ...editNote, content: e.target.value })
              : setNewNote({ ...newNote, content: e.target.value })
          }
        />
        <select
          value={editNote ? editNote.category : newNote.category}
          onChange={(e) =>
            editNote
              ? setEditNote({ ...editNote, category: e.target.value })
              : setNewNote({ ...newNote, category: e.target.value })
          }
        >
          <option value="Uncategorized">Uncategorized</option>
          <option value="Work">Work</option>
          <option value="Personal">Personal</option>
          <option value="Study">Study</option>
        </select>
        <button
          onClick={
            editNote
              ? () => handleUpdateNote(editNote.id, editNote)
              : handleCreateNote
          }
        >
          {editNote ? 'Update' : 'Create'}
        </button>
        {editNote && <button onClick={() => setEditNote(null)}>Cancel</button>}
      </div>
      <div className="search-bar">
        <input
          type="text"
          placeholder="Search notes..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <button onClick={handleSearch}>Search</button>
      </div>
      <div className="notes-list">
        <h2>{isArchived ? 'Archived Notes' : 'Active Notes'}</h2>
        <button onClick={() => setIsArchived(!isArchived)}>
          {isArchived ? 'View Active Notes' : 'View Archived Notes'}
        </button>
        {isArchived ? renderNotes(archivedNotes) : renderNotes(notes)}
      </div>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
