import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// Define page names for multipage routing.
const PAGES = {
  HOME: "HOME",
  CREATE: "CREATE",
  ARCHIVE: "ARCHIVE",
  LOGIN: "LOGIN",
  REGISTER: "REGISTER"
};

// Main App component.
function App() {
  const [notes, setNotes] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedPage, setSelectedPage] = useState(PAGES.HOME);
  const [formData, setFormData] = useState({ title: "", content: "", category: "" });
  const [currentEditNote, setCurrentEditNote] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  // Fetch (active) notes from the backend.
  const fetchNotes = async () => {
    try {
      let url = `/api/notes?query=${encodeURIComponent(searchTerm)}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setNotes(data);
      } else {
        setErrorMessage("Failed to fetch notes");
      }
    } catch (err) {
      console.error(err);
      setErrorMessage("Network error while fetching notes");
    }
  };

  useEffect(() => {
    if (selectedPage === PAGES.HOME) {
      fetchNotes();
    }
  }, [selectedPage, searchTerm]);

  // Handle input on the note creation/editing form.
  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  // Create a new note.
  const handleCreateNote = async (e) => {
    e.preventDefault();
    if (!formData.title || !formData.content) {
      setErrorMessage("Title and content are required");
      return;
    }
    try {
      const res = await fetch('/api/notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        setFormData({ title: "", content: "", category: "" });
        setErrorMessage("");
        setSelectedPage(PAGES.HOME);
        fetchNotes();
      } else {
        const errorData = await res.json();
        setErrorMessage(errorData.error || "Failed to create note");
      }
    } catch (err) {
      console.error(err);
      setErrorMessage("Network error while creating note");
    }
  };

  // Update (edit) an existing note.
  const handleUpdateNote = async (e) => {
    e.preventDefault();
    if (!currentEditNote || !formData.title || !formData.content) {
      setErrorMessage("Invalid data for update");
      return;
    }
    try {
      const res = await fetch(`/api/notes/${currentEditNote.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        setFormData({ title: "", content: "", category: "" });
        setCurrentEditNote(null);
        setErrorMessage("");
        setSelectedPage(PAGES.HOME);
        fetchNotes();
      } else {
        const errorData = await res.json();
        setErrorMessage(errorData.error || "Failed to update note");
      }
    } catch (err) {
      console.error(err);
      setErrorMessage("Network error while updating note");
    }
  };

  // Prepare editing for a given note.
  const handleEditNote = (note) => {
    setCurrentEditNote(note);
    setFormData({ title: note.title, content: note.content, category: note.category });
    setSelectedPage(PAGES.CREATE);
  };

  // Archive (soft delete) a note.
  const handleArchiveNote = async (noteId) => {
    try {
      const res = await fetch(`/api/notes/${noteId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        fetchNotes();
      } else {
        const errorData = await res.json();
        setErrorMessage(errorData.error || "Failed to archive note");
      }
    } catch (err) {
      console.error(err);
      setErrorMessage("Network error during archiving note");
    }
  };

  // Navigation bar for switching pages.
  const renderNav = () => (
    <nav className="navbar">
      <button onClick={() => setSelectedPage(PAGES.HOME)}>Home</button>
      <button onClick={() => {
          setCurrentEditNote(null);
          setFormData({ title: "", content: "", category: "" });
          setSelectedPage(PAGES.CREATE);
      }}>
        {currentEditNote ? "Edit Note" : "Create Note"}
      </button>
      <button onClick={() => setSelectedPage(PAGES.ARCHIVE)}>Archive</button>
      <button onClick={() => setSelectedPage(PAGES.LOGIN)}>Login</button>
      <button onClick={() => setSelectedPage(PAGES.REGISTER)}>Register</button>
    </nav>
  );

  // Render the main content based on the selected page.
  const renderContent = () => {
    if (selectedPage === PAGES.HOME) {
      return (
        <div className="notes-list">
          <h2>Notes</h2>
          <input 
            type="text" 
            placeholder="Search Notes..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          {errorMessage && <p className="error">{errorMessage}</p>}
          {notes.length === 0 ? (
            <p>No notes found.</p>
          ) : (
            <ul>
              {notes.map(note => (
                <li key={note.id}>
                  <h3>{note.title}</h3>
                  <p>{note.content}</p>
                  <p><em>Category: {note.category}</em></p>
                  <div>
                    <button onClick={() => handleEditNote(note)}>Edit</button>
                    <button onClick={() => handleArchiveNote(note.id)}>Archive</button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      );
    } else if (selectedPage === PAGES.CREATE) {
      return (
        <div className="note-form">
          <h2>{currentEditNote ? "Edit Note" : "Create Note"}</h2>
          {errorMessage && <p className="error">{errorMessage}</p>}
          <form onSubmit={currentEditNote ? handleUpdateNote : handleCreateNote}>
            <input 
              type="text" 
              name="title" 
              placeholder="Title" 
              value={formData.title} 
              onChange={handleChange} 
            />
            <textarea 
              name="content" 
              placeholder="Content" 
              value={formData.content} 
              onChange={handleChange}
            />
            <input 
              type="text" 
              name="category" 
              placeholder="Category" 
              value={formData.category} 
              onChange={handleChange} 
            />
            <button type="submit">{currentEditNote ? "Update Note" : "Create Note"}</button>
            <button type="button" onClick={() => {
                setSelectedPage(PAGES.HOME);
                setCurrentEditNote(null);
                setErrorMessage("");
            }}>
              Cancel
            </button>
          </form>
        </div>
      );
    } else if (selectedPage === PAGES.ARCHIVE) {
      // For demonstration, filter the archived notes.
      return (
        <div className="notes-list">
          <h2>Archived Notes</h2>
          <button onClick={fetchNotes}>Refresh</
