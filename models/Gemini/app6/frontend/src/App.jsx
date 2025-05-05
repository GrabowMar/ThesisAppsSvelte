import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
    const [notes, setNotes] = useState([]);
    const [newNote, setNewNote] = useState({ title: '', content: '', category: 'Uncategorized' });
    const [editingNoteId, setEditingNoteId] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [categoryFilter, setCategoryFilter] = useState('');
    const [showArchived, setShowArchived] = useState(false);
    const [currentPage, setCurrentPage] = useState('list'); // 'list', 'create', 'edit'

    useEffect(() => {
        fetchNotes();
    }, [searchQuery, categoryFilter, showArchived]);

    const fetchNotes = async () => {
        let url = '/api/notes?';
        if (categoryFilter) {
            url += `category=${categoryFilter}&`;
        }
        if (searchQuery) {
            url += `query=${searchQuery}&`;
        }
        if (showArchived) {
            url += `archived=true&`;
        } else {
             url += `archived=false&`;
        }


        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            const data = await response.json();
            setNotes(data);
        } catch (error) {
            console.error("Could not fetch notes:", error);
            // Handle error appropriately (e.g., display an error message)
        }
    };

    const createNote = async () => {
        if (!newNote.title || !newNote.content) {
            alert('Title and content are required');
            return;
        }

        try {
            const response = await fetch('/api/notes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(newNote),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            setNotes([...notes, data]);
            setNewNote({ title: '', content: '', category: 'Uncategorized' });
            setCurrentPage('list'); // Go back to list after creating
        } catch (error) {
            console.error('Error creating note:', error);
            // Handle error appropriately
        }
    };

    const updateNote = async (id, updatedNote) => {
        try {
            const response = await fetch(`/api/notes/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(updatedNote),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            setNotes(notes.map(note => (note.id === id ? data : note)));
            setEditingNoteId(null); // Exit editing mode
            setCurrentPage('list'); // Back to list after update
        } catch (error) {
            console.error('Error updating note:', error);
            // Handle error appropriately
        }
    };

    const deleteNote = async (id) => {
        try {
            const response = await fetch(`/api/notes/${id}`, {
                method: 'DELETE',
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            setNotes(notes.filter(note => note.id !== id));
        } catch (error) {
            console.error('Error deleting note:', error);
            // Handle error appropriately
        }
    };

    const archiveNote = async (id, archived) => {
        await updateNote(id, { archived: !archived });
    }

    let content;

    if (currentPage === 'list') {
        content = (
            <div>
                <h2>Notes</h2>
                <div className="filters">
                    <input
                        type="text"
                        placeholder="Search notes..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
                        <option value="">All Categories</option>
                        <option value="Personal">Personal</option>
                        <option value="Work">Work</option>
                        <option value="Ideas">Ideas</option>
                    </select>
                    <label>
                        Show Archived:
                        <input
                            type="checkbox"
                            checked={showArchived}
                            onChange={(e) => setShowArchived(e.target.checked)}
                        />
                    </label>
                    <button onClick={() => setCurrentPage('create')}>Create New Note</button>
                </div>
                <div className="notes-list">
                    {notes.map(note => (
                        <div key={note.id} className="note">
                            <h3>{note.title}</h3>
                            <p>{note.content}</p>
                            <p>Category: {note.category}</p>
                            <p>Created: {new Date(note.created_at).toLocaleString()}</p>
                            <p>Updated: {new Date(note.updated_at).toLocaleString()}</p>
                            <button onClick={() => {
                                setEditingNoteId(note.id);
                                setCurrentPage('edit');
                            }}>Edit</button>
                            <button onClick={() => archiveNote(note.id, note.archived)}>
                                {note.archived ? 'Unarchive' : 'Archive'}
                            </button>
                            <button onClick={() => deleteNote(note.id)}>Delete</button>
                        </div>
                    ))}
                </div>
            </div>
        );
    } else if (currentPage === 'create') {
        content = (
            <div>
                <h2>Create New Note</h2>
                <input
                    type="text"
                    placeholder="Title"
                    value={newNote.title}
                    onChange={(e) => setNewNote({ ...newNote, title: e.target.value })}
                />
                <textarea
                    placeholder="Content"
                    value={newNote.content}
                    onChange={(e) => setNewNote({ ...newNote, content: e.target.value })}
                />
                <select value={newNote.category} onChange={(e) => setNewNote({ ...newNote, category: e.target.value })}>
                    <option value="Uncategorized">Uncategorized</option>
                    <option value="Personal">Personal</option>
                    <option value="Work">Work</option>
                    <option value="Ideas">Ideas</option>
                </select>
                <button onClick={createNote}>Create Note</button>
                <button onClick={() => setCurrentPage('list')}>Cancel</button>
            </div>
        );
    } else if (currentPage === 'edit' && editingNoteId) {
        const noteToEdit = notes.find(note => note.id === editingNoteId);
        if (!noteToEdit) {
            content = <p>Note not found for editing.</p>;
        } else {
            content = (
                <div>
                    <h2>Edit Note</h2>
                    <input
                        type="text"
                        placeholder="Title"
                        value={noteToEdit.title}
                        onChange={(e) => setNotes(notes.map(note => (note.id === editingNoteId ? { ...note, title: e.target.value } : note)))}
                    />
                    <textarea
                        placeholder="Content"
                        value={noteToEdit.content}
                        onChange={(e) => setNotes(notes.map(note => (note.id === editingNoteId ? { ...note, content: e.target.value } : note)))}
                    />
                    <select
                        value={noteToEdit.category}
                        onChange={(e) => setNotes(notes.map(note => (note.id === editingNoteId ? { ...note, category: e.target.value } : note)))}
                    >
                        <option value="Uncategorized">Uncategorized</option>
                        <option value="Personal">Personal</option>
                        <option value="Work">Work</option>
                        <option value="Ideas">Ideas</option>
                    </select>
                    <button onClick={() => updateNote(editingNoteId, noteToEdit)}>Update Note</button>
                    <button onClick={() => setCurrentPage('list')}>Cancel</button>
                </div>
            );
        }
    } else {
        content = <p>Page not found.</p>;
    }

    return (
        <div className="app">
            <h1>Notes Application</h1>
            {content}
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<React.StrictMode><App /></React.StrictMode>);
