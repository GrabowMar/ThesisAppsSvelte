import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
  const [pageTitle, setPageTitle] = useState('Home');
  const [pageContent, setPageContent] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);

  useEffect(() => {
    fetchPage(pageTitle);
  }, [pageTitle]);

  const fetchPage = async (title) => {
    try {
      const response = await fetch(`http://localhost:5195/page/${title}`);
      const data = await response.json();
      setPageContent(data.content);
    } catch (error) {
      console.error('Error fetching page:', error);
    }
  };

  const savePage = async () => {
    try {
      await fetch(`http://localhost:5195/page/${pageTitle}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: pageContent }),
      });
      alert('Page saved successfully!');
    } catch (error) {
      console.error('Error saving page:', error);
    }
  };

  const handleSearch = async () => {
    try {
      const response = await fetch(`http://localhost:5195/search?q=${searchQuery}`);
      const data = await response.json();
      setSearchResults(data);
    } catch (error) {
      console.error('Error searching:', error);
    }
  };

  return (
    <div className="app">
      <h1>Wiki System</h1>
      <div className="search-bar">
        <input
          type="text"
          placeholder="Search pages..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <button onClick={handleSearch}>Search</button>
      </div>
      <div className="search-results">
        {searchResults.map((result, index) => (
          <div key={index} className="result-item" onClick={() => setPageTitle(result)}>
            {result}
          </div>
        ))}
      </div>
      <div className="page-content">
        <h2>{pageTitle}</h2>
        <textarea
          value={pageContent}
          onChange={(e) => setPageContent(e.target.value)}
          rows="10"
        />
        <button onClick={savePage}>Save</button>
      </div>
    </div>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
