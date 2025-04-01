import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Navigate, useNavigate } from 'react-router-dom';
import axios from 'axios';

// Set the base URL for axios
axios.defaults.baseURL = 'http://localhost:5495';

// Authentication context
const AuthContext = React.createContext();

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [user, setUser] = useState(null);
  const [categories, setCategories] = useState([]);
  const [threads, setThreads] = useState([]);
  const [currentThread, setCurrentThread] = useState(null);
  const [comments, setComments] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const navigate = useNavigate();

  useEffect(() => {
    fetchCategories();
    if (token) {
      fetchUser();
    }
  }, [token]);

  const fetchCategories = async () => {
    try {
      const response = await axios.get('/categories');
      setCategories(response.data);
    } catch (error) {
      setError('Failed to fetch categories');
    }
  };

  const fetchUser = async () => {
    try {
      const response = await axios.get('/user', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data);
    } catch (error) {
      setError('Failed to fetch user data');
      setToken(null);
      localStorage.removeItem('token');
    }
  };

  const login = async (username, password) => {
    try {
      const response = await axios.post('/login', { username, password });
      const newToken = response.data.access_token;
      setToken(newToken);
      localStorage.setItem('token', newToken);
      navigate('/');
    } catch (error) {
      setError('Invalid username or password');
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    navigate('/login');
  };

  const register = async (username, password, email) => {
    try {
      await axios.post('/register', { username, password, email });
      navigate('/login');
    } catch (error) {
      setError('Registration failed');
    }
  };

  const fetchThreads = async (page = 1, perPage = 10, sortBy = 'created_at', sortOrder = 'desc', categoryId = null) => {
    try {
      setLoading(true);
      const response = await axios.get('/threads', {
        params: { page, per_page: perPage, sort_by: sortBy, sort_order: sortOrder, category_id: categoryId }
      });
      setThreads(response.data);
      setLoading(false);
    } catch (error) {
      setError('Failed to fetch threads');
      setLoading(false);
    }
  };

  const createThread = async (title, content, categoryId) => {
    try {
      const response = await axios.post('/threads', { title, content, category_id: categoryId }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      navigate(`/threads/${response.data.id}`);
    } catch (error) {
      setError('Failed to create thread');
    }
  };

  const fetchThread = async (threadId) => {
    try {
      const response = await axios.get(`/threads/${threadId}`);
      setCurrentThread(response.data);
    } catch (error) {
      setError('Failed to fetch thread');
    }
  };

  const fetchComments = async (threadId, page = 1, perPage = 10, sortBy = 'created_at', sortOrder = 'desc') => {
    try {
      const response = await axios.get(`/threads/${threadId}/comments`, {
        params: { page, per_page: perPage, sort_by: sortBy, sort_order: sortOrder }
      });
      setComments(response.data);
    } catch (error) {
      setError('Failed to fetch comments');
    }
  };

  const createComment = async (threadId, content) => {
    try {
      const response = await axios.post(`/threads/${threadId}/comments`, { content }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setComments(prevComments => ({
        ...prevComments,
        comments: [...prevComments.comments, response.data]
      }));
    } catch (error) {
      setError('Failed to create comment');
    }
  };

  const searchThreads = async (query, page = 1, perPage = 10) => {
    try {
      const response = await axios.get('/search', {
        params: { q: query, page, per_page: perPage }
      });
      setSearchResults(response.data);
    } catch (error) {
      setError('Failed to search threads');
    }
  };

  const authContextValue = {
    token,
    user,
    login,
    logout,
    register
  };

  return (
    <AuthContext.Provider value={authContextValue}>
      <div className="app">
        <header>
          <h1>Forum App</h1>
          {user ? (
            <div>
              <span>Welcome, {user.username}</span>
              <button onClick={logout}>Logout</button>
            </div>
          ) : (
            <div>
              <button onClick={() => navigate('/login')}>Login</button>
              <button onClick={() => navigate('/register')}>Register</button>
            </div>
          )}
        </header>
        <main>
          {error && <div className="error">{error}</div>}
          <Routes>
            <Route path="/" element={
              <Home
                categories={categories}
                threads={threads}
                fetchThreads={fetchThreads}
                createThread={createThread}
                loading={loading}
              />
            } />
            <Route path="/login" element={
              <Login login={login} />
            } />
            <Route path="/register" element={
              <Register register={register} />
            } />
            <Route path="/threads/:id" element={
              <ThreadDetail
                thread={currentThread}
                comments={comments}
                fetchThread={fetchThread}
                fetchComments={fetchComments}
                createComment={createComment}
              />
            } />
            <Route path="/search" element={
              <Search searchThreads={searchThreads} searchResults={searchResults} />
            } />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </main>
      </div>
    </AuthContext.Provider>
  );
}

function Home({ categories, threads, fetchThreads, createThread, loading }) {
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [newThreadTitle, setNewThreadTitle] = useState('');
  const [newThreadContent, setNewThreadContent] = useState('');
  const [newThreadCategory, setNewThreadCategory] = useState('');

  useEffect(() => {
    fetchThreads(1, 10, sortBy, sortOrder, selectedCategory);
  }, [selectedCategory, sortBy, sortOrder]);

  const handleCreateThread = () => {
    createThread(newThreadTitle, newThreadContent, newThreadCategory);
    setNewThreadTitle('');
    setNewThreadContent('');
    setNewThreadCategory('');
  };

  return (
    <div>
      <h2>Home</h2>
      <div>
        <select value={selectedCategory} onChange={(e) => setSelectedCategory(e.target.value)}>
          <option value="">All Categories</option>
          {categories.map(category => (
            <option key={category.id} value={category.id}>{category.name}</option>
          ))}
        </select>
        <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
          <option value="created_at">Created At</option>
          <option value="updated_at">Updated At</option>
        </select>
        <select value={sortOrder} onChange={(e) => setSortOrder(e.target.value)}>
          <option value="desc">Descending</option>
          <option value="asc">Ascending</option>
        </select>
      </div>
      <div>
        <h3>Create New Thread</h3>
        <input
          type="text"
          placeholder="Title"
          value={newThreadTitle}
          onChange={(e) => setNewThreadTitle(e.target.value)}
        />
        <textarea
          placeholder="Content"
          value={newThreadContent}
          onChange={(e) => setNewThreadContent(e.target.value)}
        />
        <select value={newThreadCategory} onChange={(e) => setNewThreadCategory(e.target.value)}>
          <option value="">Select Category</option>
          {categories.map(category => (
            <option key={category.id} value={category.id}>{category.name}</option>
          ))}
        </select>
        <button onClick={handleCreateThread}>Create Thread</button>
      </div>
      {loading ? (
        <div>Loading...</div>
      ) : (
        <div>
          {threads.threads.map(thread => (
            <div key={thread.id}>
              <h3>{thread.title}</h3>
              <p>{thread.content}</p>
              <small>Created: {new Date(thread.created_at).toLocaleString()}</small>
              <small>Updated: {new Date(thread.updated_at).toLocaleString()}</small>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Login({ login }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleLogin = () => {
    login(username, password);
  };

  return (
    <div>
      <h2>Login</h2>
      <input
        type="text"
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <button onClick={handleLogin}>Login</button>
      <button onClick={() => navigate('/register')}>Register</button>
    </div>
  );
}

function Register({ register }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const navigate = useNavigate();

  const handleRegister = () => {
    register(username, password, email);
  };

  return (
    <div>
      <h2>Register</h2>
      <input
        type="text"
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <button onClick={handleRegister}>Register</button>
      <button onClick={() => navigate('/login')}>Login</button>
    </div>
  );
}

function ThreadDetail({ thread, comments, fetchThread, fetchComments, createComment }) {
  const [newComment, setNewComment] = useState('');
  const { token } = React.useContext(AuthContext);
  const navigate = useNavigate();

  useEffect(() => {
    const threadId = window.location.pathname.split('/').pop();
    fetchThread(threadId);
    fetchComments(threadId);
  }, []);

  const handleCreateComment = () => {
    const threadId = window.location.pathname.split('/').pop();
    createComment(threadId, newComment);
    setNewComment('');
  };

  if (!thread) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <h2>{thread.title}</h2>
      <p>{thread.content}</p>
      <small>Created: {new Date(thread.created_at).toLocaleString()}</small>
      <small>Updated: {new Date(thread.updated_at).toLocaleString()}</small>
      {token && (
        <div>
          <textarea
            placeholder="Add a comment"
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
          />
          <button onClick={handleCreateComment}>Add Comment</button>
        </div>
      )}
      <h3>Comments</h3>
      {comments.comments && comments.comments.map(comment => (
        <div key={comment.id}>
          <p>{comment.content}</p>
          <small>Created: {new Date(comment.created_at).toLocaleString()}</small>
          <small>Updated: {new Date(comment.updated_at).toLocaleString()}</small>
        </div>
      ))}
      <button onClick={() => navigate('/')}>Back to Home</button>
    </div>
  );
}

function Search({ searchThreads, searchResults }) {
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(10);

  const handleSearch = () => {
    searchThreads(query, page, perPage);
  };

  return (
    <div>
      <h2>Search Threads</h2>
      <input
        type="text"
        placeholder="Search query"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <button onClick={handleSearch}>Search</button>
      <div>
        {searchResults.threads && searchResults.threads.map(thread => (
          <div key={thread.id}>
            <h3>{thread.title}</h3>
            <p>{thread.content}</p>
            <small>Created: {new Date(thread.created_at).toLocaleString()}</small>
            <small>Updated: {new Date(thread.updated_at).toLocaleString()}</small>
          </div>
        ))}
      </div>
    </div>
  );
}

// Mounting logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <Router>
    <App />
  </Router>
);
