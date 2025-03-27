import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// API service for notes
const API_URL = 'http://localhost:5331/api';

const noteService = {
  getAllNotes: async (search = '', category = '', archived = false) => {
    try {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (category) params.append('category', category);
      params.append('archived', archived.toString());
      
      const response = await fetch(`${API_URL}/notes?${params.toString()}`);
      if (!response.ok) throw new Error('Failed to fetch notes');
      return await response.json();
    } catch (error) {
      console.error('Error fetching notes:', error);
      throw error;
    }
  },
  
  getNote: async (id) => {
    try {
      const response = await fetch(`${API_URL}/notes/${id}`);
      if (!response.ok) throw new Error('Failed to fetch note');
      return await response.json();
    } catch (error) {
      console.error(`Error fetching note ${id}:`, error);
      throw error;
    }
  },
  
  createNote: async (note) => {
    try {
      const response = await fetch(`${API_URL}/notes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(note),
      });
      if (!response.ok) throw new Error('Failed to create note');
      return await response.json();
    } catch (error) {
      console.error('Error creating note:', error);
      throw error;
    }
  },
  
  updateNote: async (id, note) => {
    try {
      const response = await fetch(`${API_URL}/notes/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(note),
      });
      if (!response.ok) throw new Error('Failed to update note');
      return await response.json();
    } catch (error) {
      console.error(`Error updating note ${id}:`, error);
      throw error;
    }
  },
  
  deleteNote: async (id) => {
    try {
      const response = await fetch(`${API_URL}/notes/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to delete note');
      return await response.json();
    } catch (error) {
      console.error(`Error deleting note ${id}:`, error);
      throw error;
    }
  },
  
  getCategories: async () => {
    try {
      const response = await fetch(`${API_URL}/categories`);
      if (!response.ok) throw new Error('Failed to fetch categories');
      return await response.json();
    } catch (error) {
      console.error('Error fetching categories:', error);
      throw error;
    }
  },
  
  createCategory: async (name) => {
    try {
      const response = await fetch(`${API_URL}/categories`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name }),
      });
      if (!response.ok) throw new Error('Failed to create category');
      return await response.json();
    } catch (error) {
      console.error('Error creating category:', error);
      throw error;
    }
  },
};

// Main App Component
function App() {
  // State variables
  const [view, setView] = useState('notes'); // 'notes', 'editor', 'archived'
  const [notes, setNotes] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedNote, setSelectedNote] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [newCategory, setNewCategory] = useState('');
  const [showCategoryForm, setShowCategoryForm] = useState(false);
  
  // Editor state
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [editCategory, setEditCategory] = useState('');
  
  // Fetch notes and categories on initial load
  useEffect(() => {
    fetchNotes();
    fetchCategories();
  }, [view, searchTerm, categoryFilter]);
  
  // Fetch notes from API
  const fetchNotes = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const isArchived = view === 'archived';
      const data = await noteService.getAllNotes(searchTerm, categoryFilter, isArchived);
      setNotes(data);
    } catch (err) {
      setError('Failed to load notes. Please try again later.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Fetch categories from API
  const fetchCategories = async () => {
    try {
      const data = await noteService.getCategories();
      setCategories(data);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };
  
  // Handle creating a new note
  const handleNewNote = () => {
    setSelectedNote(null);
    setEditTitle('');
    setEditContent('');
    setEditCategory('');
    setView('editor');
  };
  
  // Handle editing an existing note
  const handleEditNote = (note) => {
    setSelectedNote(note);
    setEditTitle(note.title);
    setEditContent(note.content);
    setEditCategory(note.category);
    setView('editor');
  };
  
  // Handle saving a note
  const handleSaveNote = async (e) => {
    e.preventDefault();
    
    if (!editTitle.trim()) {
      setError('Title cannot be empty');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      const noteData = {
        title: editTitle,
        content: editContent,
        category: editCategory,
      };
      
      let savedNote;
      if (selectedNote) {
        savedNote = await noteService.updateNote(selectedNote.id, noteData);
      } else {
        savedNote = await noteService.createNote(noteData);
      }
      
      // Reset form and return to notes view
      setView('notes');
      fetchNotes();
    } catch (err) {
      setError('Failed to save note. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Handle deleting a note
  const handleDeleteNote = async (noteId) => {
    if (!window.confirm('Are you sure you want to delete this note?')) {
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      await noteService.deleteNote(noteId);
      fetchNotes();
    } catch (err) {
      setError('Failed to delete note. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Handle archiving/unarchiving a note
  const handleArchiveToggle = async (note) => {
    setIsLoading(true);
    setError(null);
    
    try {
      await noteService.updateNote(note.id, { archived: !note.archived });
      fetchNotes();
    } catch (err) {
      setError(`Failed to ${note.archived ? 'unarchive' : 'archive'} note. Please try again.`);
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Handle adding a new category
  const handleAddCategory = async (e) => {
    e.preventDefault();
    if (!newCategory.trim()) return;
    
    try {
      await noteService.createCategory(newCategory.trim());
      setNewCategory('');
      setShowCategoryForm(false);
      fetchCategories();
    } catch (err) {
      setError('Failed to add category. Please try again.');
      console.error(err);
    }
  };
  
  // Format date for display
  const formatDate = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleString();
  };
  
  return (
    <div className="app-container">
      <header>
        <h1>Notes App</h1>
        <nav>
          <button 
            className={view === 'notes' ? 'active' : ''}
            onClick={() => setView('notes')}>
            Notes
          </button>
          <button 
            className={view === 'archived' ? 'active' : ''}
            onClick={() => setView('archived')}>
            Archived
          </button>
        </nav>
      </header>
      
      {error && <div className="error-message">{error}</div>}
      
      {view === 'notes' || view === 'archived' ? (
        <div className="notes-view">
          <div className="toolbar">
            <div className="search-filter">
              <input
                type="text"
                placeholder="Search notes..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
              <select 
                value={categoryFilter} 
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                <option value="">All Categories</option>
                {categories.map((category, index) => (
                  <option key={index} value={category}>{category}</option>
                ))}
              </select>
            </div>
            
            <div className="actions">
              {view === 'notes' && (
                <button className="primary" onClick={handleNewNote}>
                  ✚ New Note
                </button>
              )}
              
              <button onClick={() => setShowCategoryForm(!showCategoryForm)}>
                {showCategoryForm ? 'Cancel' : '✚ New Category'}
              </button>
            </div>
          </div>
          
          {showCategoryForm && (
            <form className="category-form" onSubmit={handleAddCategory}>
              <input
                type="text"
                placeholder="Category name"
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
              />
              <button type="submit">Add</button>
            </form>
          )}
          
          {isLoading ? (
            <div className="loading-spinner">Loading...</div>
          ) : notes.length === 0 ? (
            <div className="empty-state">
              <p>No {view === 'archived' ? 'archived ' : ''}notes found.</p>
              {searchTerm || categoryFilter ? (
                <p>Try adjusting your search or filter criteria.</p>
              ) : view === 'notes' ? (
                <p>Click on "New Note" to create your first note!</p>
              ) : null}
            </div>
          ) : (
            <div className="notes-grid">
              {notes.map((note) => (
                <div key={note.id} className="note-card">
                  <h3>{note.title}</h3>
                  <div className="note-meta">
                    {note.category && <span className="category">{note.category}</span>}
                    <span className="date">Updated: {formatDate(note.updated_at)}</span>
                  </div>
                  <p className="note-preview">
                    {note.content.length > 100 ? note.content.substring(0, 100) + '...' : note.content}
                  </p>
                  <div className="note-actions">
                    {view === 'notes' && (
                      <button onClick={() => handleEditNote(note)} title="Edit">
                        Edit
                      </button>
                    )}
                    <button 
                      onClick={() => handleArchiveToggle(note)}
                      title={note.archived ? 'Unarchive' : 'Archive'}
                    >
                      {note.archived ? 'Unarchive' : 'Archive'}
                    </button>
                    <button 
                      className="delete" 
                      onClick={() => handleDeleteNote(note.id)}
                      title="Delete"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : view === 'editor' ? (
        <div className="editor-view">
          <form onSubmit={handleSaveNote}>
            <input
              type="text"
              placeholder="Note Title"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              required
            />
            
            <select 
              value={editCategory} 
              onChange={(e) => setEditCategory(e.target.value)}
            >
              <option value="">Select Category (optional)</option>
              {categories.map((category, index) => (
                <option key={index} value={category}>{category}</option>
              ))}
            </select>
            
            <textarea
              placeholder="Note Content"
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              rows={10}
            />
            
            <div className="form-actions">
              <button type="button" onClick={() => setView('notes')}>Cancel</button>
              <button 
                type="submit" 
                className="primary"
                disabled={isLoading || !editTitle.trim()}
              >
                {isLoading ? 'Saving...' : selectedNote ? 'Update Note' : 'Save Note'}
              </button>
            </div>
          </form>
        </div>
      ) : null}
      
      <footer>
        <p>&copy; 2023 Notes App</p>
      </footer>
    </div>
  );
}

// Mount the app to the DOM
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

export default App;
