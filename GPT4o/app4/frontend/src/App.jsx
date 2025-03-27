import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [user, setUser] = useState(null); // User state
  const [view, setView] = useState('login'); // Page state
  const [posts, setPosts] = useState([]); // Blog posts state

  // Handle Login/Register
  const handleAuth = async (endpoint, data) => {
    try {
      const res = await fetch(`/api/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      const result = await res.json();
      if (res.ok) {
        setUser(result.email);
        setView('dashboard');
      } else {
        alert(result.error);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Fetch Posts
  useEffect(() => {
    async function fetchPosts() {
      const res = await fetch('/api/posts');
      const { posts } = await res.json();
      setPosts(posts);
    }
    if (user) fetchPosts();
  }, [user]);

  const renderLogin = () => (
    <div className="auth-form">
      <h2>Login</h2>
      <button onClick={() => setView('register')}>Switch to Register</button>
      <AuthForm onSubmit={(data) => handleAuth('login', data)} />
    </div>
  );

  const renderDashboard = () => (
    <div>
      <h1>Welcome, {user}</h1>
      <PostList posts={posts} />
    </div>
  );

  return <main>{user ? renderDashboard() : renderLogin()}</main>;
}

// Reusable Components
const AuthForm = ({ onSubmit }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({ email, password });
      }}
    >
      <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <button type="submit">Submit</button>
    </form>
  );
};

const PostList = ({ posts }) => (
  <div>
    {posts.map((post) => (
      <div key={post.id}>
        <h3>{post.title}</h3>
        <p>{post.content}</p>
      </div>
    ))}
  </div>
);

// Mount React
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
