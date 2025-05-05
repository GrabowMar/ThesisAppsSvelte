import React, { useState, useEffect, useCallback } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { debounce } from 'lodash';

// Configuration
const API_URL = 'http://localhost:5355/api';

// Utility functions
const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleString();
};

// Custom React Hook for localStorage
const useLocalStorage = (key, initialValue) => {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(error);
      return initialValue;
    }
  });

  const setValue = (value) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error(error);
    }
  };

  return [storedValue, setValue];
};

// Main App Component
function App() {
  // State management
  const [currentPage, setCurrentPage] = useState('home');
  const [pages, setPages] = useState([]);
  const [currentPageData, setCurrentPageData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [editTitle, setEditTitle] = useState('');
  const [editSummary, setEditSummary] = useState('');
  const [revisions, setRevisions] = useState([]);
  const [showRevisions, setShowRevisions] = useState(false);
  const [selectedRevision, setSelectedRevision] = useState(null);
  const [user, setUser] = useLocalStorage('wikiUser', null);
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });
  const [registerForm, setRegisterForm] = useState({ username: '', password: '', email: '' });
  const [authError, setAuthError] = useState('');

  // Debounced search function
  const debouncedSearch = useCallback(
    debounce(async (query) => {
      if (query.length < 2) {
        setSearchResults([]);
        setIsSearching(false);
        return;
      }
      
      try {
        const response = await fetch(`${API_URL}/pages/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        setSearchResults(data);
      } catch (err) {
        console.error('Search error:', err);
      } finally {
        setIsSearching(false);
      }
    }, 300),
    []
  );

  // Effect for search
  useEffect(() => {
    if (searchQuery) {
      setIsSearching(true);
      debouncedSearch(searchQuery);
    } else {
      setSearchResults([]);
      setIsSearching(false);
    }
  }, [searchQuery, debouncedSearch]);

  // Fetch all pages
  const fetchPages = async () => {
    try {
      const response = await fetch(`${API_URL}/pages`);
      if (!response.ok) throw new Error('Failed to fetch pages');
      const data = await response.json();
      setPages(data);
    } catch (err) {
      console.error('Error fetching pages:', err);
      setError('Failed to load pages. Please try again later.');
    }
  };

  // Fetch a specific page
  const fetchPage = async (slug) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/pages/${slug}`);
      if (response.status === 404) {
        // Page doesn't exist yet, initialize new page
        setCurrentPageData({
          title: slug,
          content: '',
          slug,
          isNew: true
        });
        setEditMode(true);
        setEditTitle(slug);
        setEditContent('');
      } else if (!response.ok) {
        throw new Error('Failed to fetch page');
      } else {
        const data = await response.json();
        setCurrentPageData(data);
        setEditTitle(data.title);
        setEditContent(data.content);
      }
    } catch (err) {
      console.error('Error fetching page:', err);
      setError('Failed to load page. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch page revisions
  const fetchRevisions = async (slug) => {
    try {
      const response = await fetch(`${API_URL}/pages/${slug}/revisions`);
      if (!response.ok) throw new Error('Failed to fetch revisions');
      const data = await response.json();
      setRevisions(data);
    } catch (err) {
      console.error('Error fetching revisions:', err);
      setError('Failed to load revision history.');
    }
  };

  // Fetch a specific revision
  const fetchRevision = async (slug, revisionId) => {
    try {
      const response = await fetch(`${API_URL}/pages/${slug}/revisions/${revisionId}`);
      if (!response.ok) throw new Error('Failed to fetch revision');
      const data = await response.json();
      setSelectedRevision(data);
    } catch (err) {
      console.error('Error fetching revision:', err);
      setError('Failed to load revision.');
    }
  };

  // Save page (create or update)
  const savePage = async () => {
    if (!editTitle.trim()) {
      setError('Title cannot be empty');
      return;
    }

    const isNewPage = currentPageData?.isNew;
    const method = isNewPage ? 'POST' : 'PUT';
    const url = isNewPage ? 
      `${API_URL}/pages` : 
      `${API_URL}/pages/${currentPageData.slug}`;
    
    const payload = {
      title: editTitle,
      content: editContent,
      edit_summary: editSummary || (isNewPage ? 'Initial version' : 'Updated content'),
      user_id: user?.id
    };

    try {
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to save page');
      }

      const data = await response.json();
      
      // Refresh page list and fetch the updated/new page
      await fetchPages();
      
      if (isNewPage) {
        // Navigate to the newly created page
        navigateTo('page', data.page.slug);
      } else {
        // Reload current page to see changes
        await fetchPage(currentPageData.slug);
      }
      
      setEditMode(false);
    } catch (err) {
      console.error('Error saving page:', err);
      setError(err.message || 'Failed to save page. Please try again.');
    }
  };

  // Delete page
  const deletePage = async (slug) => {
    if (!window.confirm('Are you sure you want to delete this page? This action cannot be undone.')) {
      return;
    }
    
    try {
      const response = await fetch(`${API_URL}/pages/${slug}`, {
        method: 'DELETE'
      });

      if (!response.ok) throw new Error('Failed to delete page');
      
      // Refresh page list and go back to home
      await fetchPages();
      navigateTo('home');
    } catch (err) {
      console.error('Error deleting page:', err);
      setError('Failed to delete page. Please try again.');
    }
  };

  // Login handler
  const handleLogin = async (e) => {
    e.preventDefault();
    setAuthError('');
    
    if (!loginForm.username || !loginForm.password) {
      setAuthError('Username and password are required');
      return;
    }
    
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          username: loginForm.username,
          password: loginForm.password
        })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Login failed');
      }
      
      setUser(data.user);
      navigateTo('home');
    } catch (err) {
      console.error('Login error:', err);
      setAuthError(err.message || 'Login failed. Please try again.');
    }
  };

  // Register handler
  const handleRegister = async (e) => {
    e.preventDefault();
    setAuthError('');
    
    if (!registerForm.username || !registerForm.password || !registerForm.email) {
      setAuthError('All fields are required');
      return;
    }
    
    try {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          username: registerForm.username,
          password: registerForm.password,
          email: registerForm.email
        })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Registration failed');
      }
      
      // Auto-login after successful registration
      const loginResponse = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          username: registerForm.username,
          password: registerForm.password
        })
      });
      
      const loginData = await loginResponse.json();
      
      if (!loginResponse.ok) {
        throw new Error(loginData.error || 'Auto-login failed');
      }
      
      setUser(loginData.user);
      navigateTo('home');
    } catch (err) {
      console.error('Registration error:', err);
      setAuthError(err.message || 'Registration failed. Please try again.');
    }
  };

  // Logout handler
  const handleLogout = () => {
    setUser(null);
    navigateTo('home');
  };

  // Navigation handler
  const navigateTo = (page, slug = '') => {
    setCurrentPage(page);
    setError(null);
    
    if (page === 'home') {
      fetchPages();
    } else if (page === 'page' && slug) {
      fetchPage(slug);
      setShowRevisions(false);
      setSelectedRevision(null);
    } else if (page === 'create') {
      setEditMode(true);
      setEditTitle('');
      setEditContent('');
      setEditSummary('');
      setCurrentPageData({ isNew: true });
    }
    
    // Clear search when navigating
    setSearchQuery('');
    setSearchResults([]);
  };

  // Initialize app
  useEffect(() => {
    fetchPages();
  }, []);

  // Render Markdown with sanitization
  const renderMarkdown = (content) => {
    if (!content) return '';
    const html = marked(content);
    const sanitizedHtml = DOMPurify.sanitize(html);
    return { __html: sanitizedHtml };
  };

  // Toggle revisions view
  const toggleRevisions = () => {
    if (!showRevisions && currentPageData?.slug) {
      fetchRevisions(currentPageData.slug);
    }
    setShowRevisions(!showRevisions);
    setSelectedRevision(null);
  };

  // View a specific revision
  const viewRevision = (revisionId) => {
    if (currentPageData?.slug) {
      fetchRevision(currentPageData.slug, revisionId);
    }
  };

  // Render functions for different components
  const renderNavbar = () => (
    <nav className="navbar">
      <div className="nav-brand">
        <h1 onClick={() => navigateTo('home')}>Wiki App</h1>
      </div>
      <div className="search-container">
        <input 
          type="text" 
          placeholder="Search..." 
          value={searchQuery} 
          onChange={(e) => setSearchQuery(e.target.value)} 
        />
        {isSearching && <span className="search-loading">Searching...</span>}
      </div>
      <div className="nav-links">
        {user ? (
          <>
            <span>Hello, {user.username}</span>
            <button className="btn-link" onClick={handleLogout}>Logout</button>
          </>
        ) : (
          <>
            <button className="btn-link" onClick={() => navigateTo('login')}>Login</button>
            <button className="btn-link" onClick={() => navigateTo('register')}>Register</button>
          </>
        )}
      </div>
    </nav>
  );

  const renderHomePage = () => (
    <div className="home-page">
      <div className="page-header">
        <h2>Welcome to the Wiki</h2>
        <button className="btn-primary" onClick={() => navigateTo('create')}>Create New Page</button>
      </div>
      
      {error && <div className="error-message">{error}</div>}
      
      {searchQuery && (
        <div className="search-results">
          <h3>Search Results for "{searchQuery}"</h3>
          {searchResults.length === 0 ? (
            isSearching ? (
              <p>Searching...</p>
            ) : (
              <p>No results found</p>
            )
          ) : (
            <ul className="page-list">
              {searchResults.map(page => (
                <li key={page.id} className="page-item">
                  <div className="page-item-title" onClick={() => navigateTo('page', page.slug)}>
                    {page.title}
                  </div>
                  <div className="page-item-meta">
                    Last updated: {formatDate(page.updated_at)} 
                    <span className="match-type">Match: {page.match_type}</span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
      
      {!searchQuery && (
        <div className="all-pages">
          <h3>All Pages</h3>
          {pages.length === 0 ? (
            <p>No pages yet. Be the first to create one!</p>
          ) : (
            <ul className="page-list">
  {pages.map(page => (
    <li key={page.id} className="page-item">
      <div className="page-item-title" onClick={() => navigateTo('page', page.slug)}>
        {page.title}
      </div>
      <div className="page-item-meta">
        Last updated: {formatDate(page.updated_at)}
      </div>
    </li>
  ))}
</ul>
          )}
        </div>
      )}
    </div>
  );

  const renderPageView = () => {
    if (isLoading) return <div className="loading">Loading...</div>;
    if (!currentPageData && !error) return <div className="loading">Page not found</div>;
    
    return (
      <div className="page-view">
        {error && <div className="error-message">{error}</div>}
        
        {selectedRevision ? (
          <>
            <div className="page-header">
              <h2>{currentPageData.title} - Revision</h2>
              <div className="header-buttons">
                <button className="btn" onClick={() => setSelectedRevision(null)}>
                  Back to Current Version
                </button>
              </div>
            </div>
            <div className="revision-meta">
              <p>
                Revision from {formatDate(selectedRevision.created_at)} 
                {selectedRevision.user && <span> by {selectedRevision.user}</span>}
                {selectedRevision.edit_summary && <span> - {selectedRevision.edit_summary}</span>}
              </p>
            </div>
            <div 
              className="page-content"
              dangerouslySetInnerHTML={renderMarkdown(selectedRevision.content)} 
            />
          </>
        ) : editMode ? (
          <div className="page-edit">
            <div className="page-header">
              <h2>{currentPageData.isNew ? 'Create New Page' : 'Edit Page'}</h2>
            </div>
            <div className="edit-form">
              <div className="form-group">
                <label>Title:</label>
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  placeholder="Page Title"
                />
              </div>
              
              <div className="form-group">
                <label>Content (Markdown supported):</label>
                <textarea
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  rows="15"
                  placeholder="Write your content here. Markdown is supported."
                />
              </div>
              
              <div className="form-group">
                <label>Edit Summary:</label>
                <input
                  type="text"
                  value={editSummary}
                  onChange={(e) => setEditSummary(e.target.value)}
                  placeholder="Brief description of your changes"
                />
              </div>
              
              <div className="edit-preview">
                <h3>Preview:</h3>
                <div 
                  className="preview-content"
                  dangerouslySetInnerHTML={renderMarkdown(editContent)} 
                />
              </div>
              
              <div className="form-actions">
                <button className="btn-primary" onClick={savePage}>Save</button>
                <button 
                  className="btn-secondary" 
                  onClick={() => {
                    setEditMode(false);
                    if (currentPageData.isNew) {
                      navigateTo('home');
                    }
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="page-header">
              <h2>{currentPageData.title}</h2>
              <div className="header-buttons">
                <button className="btn" onClick={() => setEditMode(true)}>Edit</button>
                <button className="btn" onClick={toggleRevisions}>
                  {showRevisions ? 'Hide History' : 'View History'}
                </button>
                <button className="btn-danger" onClick={() => deletePage(currentPageData.slug)}>
                  Delete
                </button>
              </div>
            </div>
            
            <div className="page-meta">
              <p>
                Created: {formatDate(currentPageData.created_at)} | 
                Last updated: {formatDate(currentPageData.updated_at)}
              </p>
            </div>
            
            {showRevisions ? (
              <div className="revision-history">
                <h3>Revision History</h3>
                {revisions.length === 0 ? (
                  <p>No revision history available.</p>
                ) : (
                  <ul className="revision-list">
                    {revisions.map(rev => (
                      <li key={rev.id} className="revision-item">
                        <div 
                          className="revision-info" 
                          onClick={() => viewRevision(rev.id)}
                        >
                          <div className="revision-date">{formatDate(rev.created_at)}</div>
                          <div className="revision-user">{rev.user || 'Anonymous'}</div>
                          <div className="revision-summary">{rev.edit_summary || 'No summary'}</div>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ) : (
              <div 
                className="page-content"
                dangerouslySetInnerHTML={renderMarkdown(currentPageData.content)} 
              />
            )}
          </>
        )}
      </div>
    );
  };

  const renderLoginForm = () => (
    <div className="auth-page">
      <h2>Login</h2>
      {authError && <div className="error-message">{authError}</div>}
      <form onSubmit={handleLogin} className="auth-form">
        <div className="form-group">
          <label>Username:</label>
          <input 
            type="text" 
            value={loginForm.username}
            onChange={(e) => setLoginForm({...loginForm, username: e.target.value})}
            required
          />
        </div>
        <div className="form-group">
          <label>Password:</label>
          <input 
            type="password" 
            value={loginForm.password}
            onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
            required
          />
        </div>
        <div className="form-actions">
          <button type="submit" className="btn-primary">Login</button>
          <button 
            type="button" 
            className="btn-link" 
            onClick={() => navigateTo('register')}
          >
            Need an account? Register
          </button>
        </div>
      </form>
    </div>
  );

  const renderRegisterForm = () => (
    <div className="auth-page">
      <h2>Register</h2>
      {authError && <div className="error-message">{authError}</div>}
      <form onSubmit={handleRegister} className="auth-form">
        <div className="form-group">
          <label>Username:</label>
          <input 
            type="text" 
            value={registerForm.username}
            onChange={(e) => setRegisterForm({...registerForm, username: e.target.value})}
            required
          />
        </div>
        <div className="form-group">
          <label>Email:</label>
          <input 
            type="email" 
            value={registerForm.email}
            onChange={(e) => setRegisterForm({...registerForm, email: e.target.value})}
            required
          />
        </div>
        <div className="form-group">
          <label>Password:</label>
          <input 
            type="password" 
            value={registerForm.password}
            onChange={(e) => setRegisterForm({...registerForm, password: e.target.value})}
            required
          />
        </div>
        <div className="form-actions">
          <button type="submit" className="btn-primary">Register</button>
          <button 
            type="button" 
            className="btn-link"
            onClick={() => navigateTo('login')}
          >
            Already have an account? Login
          </button>
        </div>
      </form>
    </div>
  );

  // Main render function
  return (
    <div className="wiki-app">
      {renderNavbar()}
      
      <main className="main-content">
        {currentPage === 'home' && renderHomePage()}
        {currentPage === 'page' && renderPageView()}
        {currentPage === 'create' && renderPageView()}
        {currentPage === 'login' && renderLoginForm()}
        {currentPage === 'register' && renderRegisterForm()}
      </main>
      
      <footer className="footer">
        <p>&copy; {new Date().getFullYear()} Wiki Application</p>
      </footer>
    </div>
  );
}

// Mount the React application
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

export default App;


