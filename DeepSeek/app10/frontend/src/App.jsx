import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [posts, setPosts] = useState([]);
  const [view, setView] = useState('home');
  const [searchQuery, setSearchQuery] = useState('');
  const [newPostContent, setNewPostContent] = useState('');

  useEffect(() => {
    fetchPosts();
  }, []);

  const fetchPosts = async () => {
    const response = await fetch('http://localhost:5179/posts');
    const data = await response.json();
    setPosts(data);
  };

  const handleLogin = async (username, password) => {
    const response = await fetch('http://localhost:5179/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (response.ok) {
      setIsLoggedIn(true);
    }
  };

  const handleLogout = async () => {
    const response = await fetch('http://localhost:5179/logout', {
      method: 'POST',
    });
    if (response.ok) {
      setIsLoggedIn(false);
      setUser(null);
    }
  };

  const handleCreatePost = async () => {
    const response = await fetch('http://localhost:5179/posts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: newPostContent }),
    });
    if (response.ok) {
      fetchPosts();
      setNewPostContent('');
    }
  };

  const handleSearch = async () => {
    const response = await fetch(`http://localhost:5179/posts/search?query=${searchQuery}`);
    const data = await response.json();
    setPosts(data);
  };

  return (
    <div className="App">
      <header>
        <h1>Microblog</h1>
        <nav>
          <button onClick={() => setView('home')}>Home</button>
          {isLoggedIn ? (
            <>
              <button onClick={() => setView('new')}>New Post</button>
              <button onClick={handleLogout}>Logout</button>
            </>
          ) : (
            <button onClick={() => setView('login')}>Login</button>
          )}
        </nav>
      </header>
      <main>
        {view === 'home' && (
          <>
            <input
              type="text"
              placeholder="Search posts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button onClick={handleSearch}>Search</button>
            {posts.map((post) => (
              <div key={post.id} className="post">
                <p>{post.content}</p>
                <span>by {post.author}</span>
              </div>
            ))}
          </>
        )}
        {view === 'login' && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleLogin(e.target.username.value, e.target.password.value);
            }}
          >
            <input type="text" name="username" placeholder="Username" required />
            <input type="password" name="password" placeholder="Password" required />
            <button type="submit">Login</button>
          </form>
        )}
        {view === 'new' && (
          <>
            <textarea
              value={newPostContent}
              onChange={(e) => setNewPostContent(e.target.value)}
              placeholder="Write your post here..."
            />
            <button onClick={handleCreatePost}>Post</button>
          </>
        )}
      </main>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
