import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import axios from 'axios';

// Set the base URL for axios
axios.defaults.baseURL = 'http://localhost:5499';

// Authentication context
const AuthContext = React.createContext();

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [user, setUser] = useState(null);
  const [posts, setPosts] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUserProfile();
      fetchPosts();
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);

  const login = async (username, password) => {
    try {
      const response = await axios.post('/login', { username, password });
      const newToken = response.data.access_token;
      localStorage.setItem('token', newToken);
      setToken(newToken);
      fetchUserProfile();
    } catch (error) {
      setError('Invalid username or password');
    }
  };

  const register = async (username, password) => {
    try {
      await axios.post('/register', { username, password });
      alert('Registration successful. Please log in.');
    } catch (error) {
      setError(error.response.data.error);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const fetchUserProfile = async () => {
    try {
      const response = await axios.get('/profile');
      setUser(response.data);
    } catch (error) {
      setError('Failed to fetch user profile');
    }
  };

  const fetchPosts = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get('/posts');
      setPosts(response.data);
    } catch (error) {
      setError('Failed to fetch posts');
    } finally {
      setIsLoading(false);
    }
  };

  const createPost = async (content) => {
    try {
      await axios.post('/posts', { content });
      fetchPosts();
    } catch (error) {
      setError('Failed to create post');
    }
  };

  const updatePost = async (postId, content) => {
    try {
      await axios.put(`/posts/${postId}`, { content });
      fetchPosts();
    } catch (error) {
      setError('Failed to update post');
    }
  };

  const deletePost = async (postId) => {
    try {
      await axios.delete(`/posts/${postId}`);
      fetchPosts();
    } catch (error) {
      setError('Failed to delete post');
    }
  };

  const likePost = async (postId) => {
    try {
      await axios.post(`/posts/${postId}/like`);
      fetchPosts();
    } catch (error) {
      setError('Failed to like post');
    }
  };

  const commentPost = async (postId, content) => {
    try {
      await axios.post(`/posts/${postId}/comment`, { content });
      fetchPosts();
    } catch (error) {
      setError('Failed to comment on post');
    }
  };

  const searchPosts = async (query) => {
    try {
      const response = await axios.get('/search', { params: { q: query } });
      setSearchResults(response.data);
    } catch (error) {
      setError('Failed to search posts');
    }
  };

  const updateProfile = async (username) => {
    try {
      await axios.put('/profile', { username });
      fetchUserProfile();
    } catch (error) {
      setError('Failed to update profile');
    }
  };

  const PrivateRoute = ({ children }) => {
    return token ? children : <Navigate to="/login" />;
  };

  return (
    <AuthContext.Provider value={{ token, user, login, logout, register }}>
      <Router>
        <div className="app">
          <nav>
            <ul>
              <li><a href="/">Home</a></li>
              {token && <li><a href="/profile">Profile</a></li>}
              {token ? (
                <li><button onClick={logout}>Logout</button></li>
              ) : (
                <>
                  <li><a href="/login">Login</a></li>
                  <li><a href="/register">Register</a></li>
                </>
              )}
            </ul>
          </nav>

          <Routes>
            <Route path="/login" element={
              <LoginPage login={login} error={error} setError={setError} />
            } />
            <Route path="/register" element={
              <RegisterPage register={register} error={error} setError={setError} />
            } />
            <Route path="/" element={
              <PrivateRoute>
                <HomePage 
                  posts={posts} 
                  isLoading={isLoading} 
                  error={error} 
                  createPost={createPost} 
                  likePost={likePost} 
                  commentPost={commentPost} 
                />
              </PrivateRoute>
            } />
            <Route path="/profile" element={
              <PrivateRoute>
                <ProfilePage 
                  user={user} 
                  error={error} 
                  updateProfile={updateProfile} 
                />
              </PrivateRoute>
            } />
            <Route path="/search" element={
              <PrivateRoute>
                <SearchPage 
                  searchPosts={searchPosts} 
                  searchResults={searchResults} 
                  error={error} 
                />
              </PrivateRoute>
            } />
            <Route path="/post/:postId" element={
              <PrivateRoute>
                <PostDetailPage 
                  posts={posts} 
                  updatePost={updatePost} 
                  deletePost={deletePost} 
                  likePost={likePost} 
                  commentPost={commentPost} 
                  error={error} 
                />
              </PrivateRoute>
            } />
          </Routes>
        </div>
      </Router>
    </AuthContext.Provider>
  );
}

function LoginPage({ login, error, setError }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    login(username, password);
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Login</h2>
      {error && <p className="error">{error}</p>}
      <input 
        type="text" 
        placeholder="Username" 
        value={username} 
        onChange={(e) => setUsername(e.target.value)} 
        required 
      />
      <input 
        type="password" 
        placeholder="Password" 
        value={password} 
        onChange={(e) => setPassword(e.target.value)} 
        required 
      />
      <button type="submit">Login</button>
    </form>
  );
}

function RegisterPage({ register, error, setError }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    register(username, password);
    setError(null);
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Register</h2>
      {error && <p className="error">{error}</p>}
      <input 
        type="text" 
        placeholder="Username" 
        value={username} 
        onChange={(e) => setUsername(e.target.value)} 
        required 
      />
      <input 
        type="password" 
        placeholder="Password" 
        value={password} 
        onChange={(e) => setPassword(e.target.value)} 
        required 
      />
      <button type="submit">Register</button>
    </form>
  );
}

function HomePage({ posts, isLoading, error, createPost, likePost, commentPost }) {
  const [newPostContent, setNewPostContent] = useState('');
  const [commentContent, setCommentContent] = useState({});

  const handleCreatePost = (e) => {
    e.preventDefault();
    createPost(newPostContent);
    setNewPostContent('');
  };

  const handleLike = (postId) => {
    likePost(postId);
  };

  const handleComment = (postId, e) => {
    e.preventDefault();
    commentPost(postId, commentContent[postId]);
    setCommentContent({ ...commentContent, [postId]: '' });
  };

  if (isLoading) return <p>Loading posts...</p>;
  if (error) return <p className="error">Error: {error}</p>;

  return (
    <div>
      <h2>Home</h2>
      <form onSubmit={handleCreatePost}>
        <textarea 
          value={newPostContent} 
          onChange={(e) => setNewPostContent(e.target.value)} 
          placeholder="What's on your mind?" 
          required 
        />
        <button type="submit">Post</button>
      </form>
      {posts.map(post => (
        <div key={post.id} className="post">
          <h3>{post.author}</h3>
          <p>{post.content}</p>
          <p>Likes: {post.likes}</p>
          <p>Comments: {post.comments}</p>
          <button onClick={() => handleLike(post.id)}>Like</button>
          <form onSubmit={(e) => handleComment(post.id, e)}>
            <input 
              type="text" 
              value={commentContent[post.id] || ''} 
              onChange={(e) => setCommentContent({ ...commentContent, [post.id]: e.target.value })} 
              placeholder="Add a comment" 
              required 
            />
            <button type="submit">Comment</button>
          </form>
          <a href={`/post/${post.id}`}>View Details</a>
        </div>
      ))}
    </div>
  );
}

function ProfilePage({ user, error, updateProfile }) {
  const [newUsername, setNewUsername] = useState('');

  const handleUpdateProfile = (e) => {
    e.preventDefault();
    updateProfile(newUsername);
    setNewUsername('');
  };

  if (error) return <p className="error">Error: {error}</p>;

  return (
    <div>
      <h2>Profile</h2>
      {user && (
        <>
          <p>Username: {user.username}</p>
          <p>Posts: {user.posts}</p>
          <form onSubmit={handleUpdateProfile}>
            <input 
              type="text" 
              value={newUsername} 
              onChange={(e) => setNewUsername(e.target.value)} 
              placeholder="New username" 
              required 
            />
            <button type="submit">Update Profile</button>
          </form>
        </>
      )}
    </div>
  );
}

function SearchPage({ searchPosts, searchResults, error }) {
  const [query, setQuery] = useState('');

  const handleSearch = (e) => {
    e.preventDefault();
    searchPosts(query);
  };

  if (error) return <p className="error">Error: {error}</p>;

  return (
    <div>
      <h2>Search</h2>
      <form onSubmit={handleSearch}>
        <input 
          type="text" 
          value={query} 
          onChange={(e) => setQuery(e.target.value)} 
          placeholder="Search posts" 
          required 
        />
        <button type="submit">Search</button>
      </form>
      {searchResults.map(post => (
        <div key={post.id} className="post">
          <h3>{post.author}</h3>
          <p>{post.content}</p>
          <p>Likes: {post.likes}</p>
          <p>Comments: {post.comments}</p>
          <a href={`/post/${post.id}`}>View Details</a>
        </div>
      ))}
    </div>
  );
}

function PostDetailPage({ posts, updatePost, deletePost, likePost, commentPost, error }) {
  const { postId } = useParams();
  const post = posts.find(p => p.id === parseInt(postId));

  const [editContent, setEditContent] = useState('');
  const [commentContent, setCommentContent] = useState('');

  const handleUpdatePost = (e) => {
    e.preventDefault();
    updatePost(postId, editContent);
    setEditContent('');
  };

  const handleDeletePost = () => {
    deletePost(postId);
  };

  const handleLike = () => {
    likePost(postId);
  };

  const handleComment = (e) => {
    e.preventDefault();
    commentPost(postId, commentContent);
    setCommentContent('');
  };

  if (!post) return <p>Post not found</p>;
  if (error) return <p className="error">Error: {error}</p>;

  return (
    <div>
      <h2>Post Details</h2>
      <h3>{post.author}</h3>
      <p>{post.content}</p>
      <p>Likes: {post.likes}</p>
      <p>Comments: {post.comments.length}</p>
      <button onClick={handleLike}>Like</button>
      <form onSubmit={handleComment}>
        <input 
          type="text" 
          value={commentContent} 
          onChange={(e) => setCommentContent(e.target.value)} 
          placeholder="Add a comment" 
          required 
        />
        <button type="submit">Comment</button>
      </form>
      {post.comments.map(comment => (
        <div key={comment.id} className="comment">
          <p>{comment.author}: {comment.content}</p>
        </div>
      ))}
      {post.user_id === user.id && (
        <>
          <form onSubmit={handleUpdatePost}>
            <textarea 
              value={editContent} 
              onChange={(e) => setEditContent(e.target.value)} 
              placeholder="Edit post" 
              required 
            />
            <button type="submit">Update Post</button>
          </form>
          <button onClick={handleDeletePost}>Delete Post</button>
        </>
      )}
    </div>
  );
}

// Mounting logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

export default App;
