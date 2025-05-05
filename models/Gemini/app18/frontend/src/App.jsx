// app/frontend/src/App.jsx
import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [currentPage, setCurrentPage] = useState('home');
  const [pages, setPages] = useState([]);
  const [pageContent, setPageContent] = useState('');
  const [pageTitle, setPageTitle] = useState('');
  const [newPageName, setNewPageName] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchPages();
  }, []);

  useEffect(() => {
    if (currentPage) {
      fetchPageContent(currentPage);
    }
  }, [currentPage]);

  const fetchPages = async () => {
    try {
      const response = await fetch('/api/pages');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setPages(data);
    } catch (e) {
      setError(`Failed to fetch pages: ${e.message}`);
    }
  };


  const fetchPageContent = async (pageName) => {
    try {
      const response = await fetch(`/api/pages/${pageName}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setPageContent(data.content);
      setPageTitle(data.title);
      setHistory(data.history);
    } catch (e) {
      setError(`Failed to fetch page content: ${e.message}`);
      setPageContent('');
      setPageTitle('');
      setHistory([]);
    }
  };


  const handleCreatePage = async () => {
    if (!newPageName) {
      setError("Page name cannot be empty.");
      return;
    }
    try {
      const response = await fetch(`/api/pages/${newPageName}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title: newPageName, content: 'New page content' }),
      });

      if (!response.ok) {
        const errorData = await response.json(); // Try to parse error response
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorData.message || 'Unknown error'}`);
      }
      await fetchPages(); // Refresh the page list
      setCurrentPage(newPageName); // Navigate to the new page
      setNewPageName(''); // Clear the input
      setError('');
    } catch (e) {
      setError(`Failed to create page: ${e.message}`);
    }
  };



  const handleUpdatePage = async () => {
    try {
      const response = await fetch(`/api/pages/${currentPage}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content: pageContent }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      await fetchPageContent(currentPage);
      setError('');
    } catch (e) {
      setError(`Failed to update page: ${e.message}`);
    }
  };


  const handleDeletePage = async () => {
    try {
      const response = await fetch(`/api/pages/${currentPage}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      await fetchPages();
      setCurrentPage('home');
      setError('');
    } catch (e) {
      setError(`Failed to delete page: ${e.message}`);
    }
  };


  const handleSearch = async () => {
    try {
      const response = await fetch(`/api/search?q=${searchQuery}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setSearchResults(data);
      setError('');
    } catch (e) {
      setError(`Failed to perform search: ${e.message}`);
      setSearchResults([]);
    }
  };

    const navigateToHistory = () => {
        setCurrentPage(`${currentPage}-history`);
    };

  const renderPage = () => {
    if (currentPage.endsWith('-history')) {
        const basePageName = currentPage.replace('-history', '');
        return (
            <div>
                <h2>History for {basePageName}</h2>
                <ul>
                    {history.map((version, index) => (
                        <li key={index}>
                            {version.timestamp}: {version.content}
                        </li>
                    ))}
                    <li>
                        <button onClick={() => setCurrentPage(basePageName)}>Back to {basePageName}</button>
                    </li>
                </ul>
            </div>
        );
    }

    return (
      <div>
        <h2>{pageTitle}</h2>
        <textarea value={pageContent} onChange={(e) => setPageContent(e.target.value)} />
        <button onClick={handleUpdatePage}>Update Page</button>
        <button onClick={handleDeletePage}>Delete Page</button>
        <button onClick={navigateToHistory}>View History</button>
      </div>
    );
  };


  return (
    <div className="App">
      <h1>Wiki System</h1>

      {error && <div className="error">{error}</div>}

      <div className="navigation">
        <ul>
          {pages.map((page) => (
            <li key={page}>
              <button onClick={() => setCurrentPage(page)}>{page}</button>
            </li>
          ))}
        </ul>
        <div>
          <input
            type="text"
            placeholder="New page name"
            value={newPageName}
            onChange={(e) => setNewPageName(e.target.value)}
          />
          <button onClick={handleCreatePage}>Create Page</button>
        </div>
      </div>

      <div className="search">
        <input
          type="text"
          placeholder="Search..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <button onClick={handleSearch}>Search</button>
        {searchResults.length > 0 && (
          <ul>
            {searchResults.map((result) => (
              <li key={result.name}>
                <button onClick={() => setCurrentPage(result.name)}>{result.title}</button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="content">{renderPage()}</div>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

export default App;
