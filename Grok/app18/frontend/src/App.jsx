import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
  const [pages, setPages] = useState([]);
  const [currentPage, setCurrentPage] = useState(null);
  const [newPageTitle, setNewPageTitle] = useState('');
  const [newPageContent, setNewPageContent] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPages();
  }, []);

  const fetchPages = async () => {
    try {
      const response = await fetch('/api/pages');
      if (!response.ok) throw new Error('Failed to fetch pages');
      const data = await response.json();
      setPages(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const fetchPage = async (pageId) => {
    try {
      const response = await fetch(`/api/pages/${pageId}`);
      if (!response.ok) throw new Error('Failed to fetch page');
      const data = await response.json();
      setCurrentPage(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const createPage = async () => {
    try {
      const response = await fetch('/api/pages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newPageTitle, content: newPageContent })
      });
      if (!response.ok) throw new Error('Failed to create page');
      const data = await response.json();
      setPages([...pages, data.page_id]);
      setNewPageTitle('');
      setNewPageContent('');
      fetchPage(data.page_id);
    } catch (err) {
      setError(err.message);
    }
  };

  const updatePage = async (pageId, content) => {
    try {
      const response = await fetch(`/api/pages/${pageId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
      });
      if (!response.ok) throw new Error('Failed to update page');
      const data = await response.json();
      setCurrentPage(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const fetchPageHistory = async (pageId) => {
    try {
      const response = await fetch(`/api/pages/${pageId}/history`);
      if (!response.ok) throw new Error('Failed to fetch page history');
      const data = await response.json();
      return data;
    } catch (err) {
      setError(err.message);
      return [];
    }
  };

  const search = async () => {
    try {
      const response = await fetch(`/api/search?q=${encodeURIComponent(searchQuery)}`);
      if (!response.ok) throw new Error('Failed to search');
      const data = await response.json();
      setSearchResults(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const renderPageList = () => (
    <div className="page-list">
      <h2>Wiki Pages</h2>
      <ul>
        {pages.map(pageId => (
          <li key={pageId} onClick={() => fetchPage(pageId)}>
            {pageId.replace(/_/g, ' ')}
          </li>
        ))}
      </ul>
    </div>
  );

  const renderPageView = () => (
    <div className="page-view">
      <h2>{currentPage.title}</h2>
      <div 
        className="page-content" 
        dangerouslySetInnerHTML={{__html: currentPage.content.replace(/\n/g, '<br>')}}
      />
      <textarea 
        value={currentPage.content} 
        onChange={(e) => setCurrentPage({...currentPage, content: e.target.value})}
      />
      <button onClick={() => updatePage(currentPage.title.toLowerCase().replace(/ /g, '_'), currentPage.content)}>
        Save Changes
      </button>
      <button onClick={() => setCurrentPage(null)}>Back to List</button>
      <h3>Version History</h3>
      <ul>
        {currentPage.history && currentPage.history.map((version, index) => (
          <li key={index}>
            {new Date(version.timestamp).toLocaleString()} - 
            <button onClick={() => setCurrentPage({...currentPage, content: version.content})}>
              Restore
            </button>
          </li>
        ))}
      </ul>
    </div>
  );

  const renderNewPageForm = () => (
    <div className="new-page-form">
      <h2>Create New Page</h2>
      <input 
        type="text" 
        value={newPageTitle} 
        onChange={(e) => setNewPageTitle(e.target.value)} 
        placeholder="Page Title"
      />
      <textarea 
        value={newPageContent} 
        onChange={(e) => setNewPageContent(e.target.value)} 
        placeholder="Page Content"
      />
      <button onClick={createPage}>Create Page</button>
    </div>
  );

  const renderSearch = () => (
    <div className="search">
      <input 
        type="text" 
        value={searchQuery} 
        onChange={(e) => setSearchQuery(e.target.value)} 
        placeholder="Search..."
      />
      <button onClick={search}>Search</button>
      <ul>
        {searchResults.map(result => (
          <li key={result} onClick={() => fetchPage(result)}>
            {result.replace(/_/g, ' ')}
          </li>
        ))}
      </ul>
    </div>
  );

  return (
    <div className="app">
      <h1>Wiki Application</h1>
      {error && <div className="error">{error}</div>}
      {renderSearch()}
      {currentPage ? renderPageView() : renderPageList()}
      {renderNewPageForm()}
    </div>
  );
};

// Mounting logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
