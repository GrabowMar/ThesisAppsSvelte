import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Switch, Link } from 'react-router-dom';
import './App.css';

const App = () => {
  const [pages, setPages] = useState([]);
  const [pageContent, setPageContent] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetch('/api/pages')
      .then(response => response.json())
      .then(data => setPages(data));
  }, []);

  const fetchPage = (pageId) => {
    fetch(`/api/pages/${pageId}`)
      .then(response => response.json())
      .then(data => setPageContent(data.content));
  };

  const searchPages = () => {
    if (searchQuery) {
      fetch(`/api/search?query=${searchQuery}`)
        .then(response => response.json())
        .then(data => setPages(data));
    } else {
      fetch('/api/pages')
        .then(response => response.json())
        .then(data => setPages(data));
    }
  };

  const createPage = (title, content) => {
    fetch('/api/pages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ title, content, author_id: 1 }),
    })
      .then(response => response.json())
      .then(data => {
        setPages([...pages, { id: data.page_id, title }]);
      });
  };

  const editPage = (pageId, title, content) => {
    fetch(`/api/pages/${pageId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ title, content }),
    })
      .then(response => response.json())
      .then(data => {
        setPages(pages.map(page => (page.id === pageId ? { ...page, title } : page)));
      });
  };

  return (
    <Router>
      <div>
        <nav>
          <Link to="/">Home</Link>
          <Link to="/create">Create Page</Link>
          <input
            type="text"
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button onClick={searchPages}>Search</button>
        </nav>
        <Switch>
          <Route path="/" exact>
            <div>
              <h1>Wiki Home</h1>
              <ul>
                {pages.map(page => (
                  <li key={page.id}>
                    <Link to={`/page/${page.id}`} onClick={() => fetchPage(page.id)}>
                      {page.title}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          </Route>
          <Route path="/create">
            <div>
              <h1>Create Page</h1>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  const title = e.target.title.value;
                  const content = e.target.content.value;
                  createPage(title, content);
                }}
              >
                <input type="text" name="title" placeholder="Title" required />
                <textarea name="content" placeholder="Content" required></textarea>
                <button type="submit">Create</button>
              </form>
            </div>
          </Route>
          <Route path="/page/:id">
            <div>
              <h1>Page Content</h1>
              <div>{pageContent}</div>
            </div>
          </Route>
        </Switch>
      </div>
    </Router>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
