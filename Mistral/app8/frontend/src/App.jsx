import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import axios from 'axios';
import './App.css';

const App = () => {
  const [categories, setCategories] = useState([]);
  const [threads, setThreads] = useState([]);
  const [comments, setComments] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);

  useEffect(() => {
    fetchCategories();
    fetchThreads();
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await axios.get('http://localhost:5095/categories');
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const fetchThreads = async () => {
    try {
      const response = await axios.get('http://localhost:5095/threads');
      setThreads(response.data);
    } catch (error) {
      console.error('Error fetching threads:', error);
    }
  };

  const fetchComments = async (threadId) => {
    try {
      const response = await axios.get(`http://localhost:5095/threads/${threadId}/comments`);
      setComments(response.data);
    } catch (error) {
      console.error('Error fetching comments:', error);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.get(`http://localhost:5095/threads/search?query=${searchQuery}`);
      setSearchResults(response.data);
    } catch (error) {
      console.error('Error searching threads:', error);
    }
  };

  const handleSort = async (sortBy) => {
    try {
      const response = await axios.get(`http://localhost:5095/threads/sort?sort_by=${sortBy}`);
      setThreads(response.data);
    } catch (error) {
      console.error('Error sorting threads:', error);
    }
  };

  return (
    <Router>
      <div className="app">
        <nav>
          <Link to="/">Home</Link>
          <Link to="/categories">Categories</Link>
          <Link to="/threads">Threads</Link>
        </nav>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/categories" element={<Categories categories={categories} />} />
          <Route path="/threads" element={<Threads threads={threads} fetchComments={fetchComments} handleSearch={handleSearch} handleSort={handleSort} searchQuery={searchQuery} setSearchQuery={setSearchQuery} searchResults={searchResults} />} />
          <Route path="/threads/:id" element={<ThreadDetails comments={comments} />} />
        </Routes>
      </div>
    </Router>
  );
};

const Home = () => <h1>Welcome to the Forum</h1>;

const Categories = ({ categories }) => (
  <div>
    <h1>Categories</h1>
    <ul>
      {categories.map(category => (
        <li key={category.id}>{category.name}</li>
      ))}
    </ul>
  </div>
);

const Threads = ({ threads, fetchComments, handleSearch, handleSort, searchQuery, setSearchQuery, searchResults }) => (
  <div>
    <h1>Threads</h1>
    <form onSubmit={handleSearch}>
      <input
        type="text"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        placeholder="Search threads..."
      />
      <button type="submit">Search</button>
    </form>
    <button onClick={() => handleSort('created_at')}>Sort by Date</button>
    <ul>
      {searchResults.length > 0
        ? searchResults.map(thread => (
            <li key={thread.id}>
              <Link to={`/threads/${thread.id}`} onClick={() => fetchComments(thread.id)}>
                {thread.title}
              </Link>
            </li>
          ))
        : threads.map(thread => (
            <li key={thread.id}>
              <Link to={`/threads/${thread.id}`} onClick={() => fetchComments(thread.id)}>
                {thread.title}
              </Link>
            </li>
          ))}
    </ul>
  </div>
);

const ThreadDetails = ({ comments }) => (
  <div>
    <h1>Thread Details</h1>
    <ul>
      {comments.map(comment => (
        <li key={comment.id}>{comment.content}</li>
      ))}
    </ul>
  </div>
);

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
