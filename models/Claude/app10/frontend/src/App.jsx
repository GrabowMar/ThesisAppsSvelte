import React, { useState, useEffect, createContext, useContext } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// Context for user authentication
const AuthContext = createContext();

function App() {
  // Application state
  const [page, setPage] = useState('home'); // 'home', 'login', 'register', 'profile', 'post', 'edit-profile'
  const [auth, setAuth] = useState({
    isAuthenticated: false,
    token: localStorage.getItem('token') || null,
    user: JSON.parse(localStorage.getItem('user')) || null
  });
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPost, setCurrentPost] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [pagination, setPagination] = useState({
    page: 1,
    pages: 1,
    total: 0
  });

  // Store auth data in local storage when it changes
  useEffect(() => {
    if (auth.token) {
      localStorage.setItem('token', auth.token);
      localStorage.setItem('user', JSON.stringify(auth.user));
    } else {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }
  }, [auth]);

  // Load posts on mount and when pagination changes
  useEffect(() => {
    if (page === 'home') {
      fetchPosts(pagination.page);
    }
  }, [page, pagination.page]);

  // API Base URL
  const API_URL = 'http://localhost:5339/api';

  // Authentication functions
  const login = async (email, password) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Login failed');
      }

      const data = await response.json();
      setAuth({
        isAuthenticated: true,
        token: data.token,
        user: data.user
      });
      setPage('home');
      return { success: true };
    } catch (err) {
      setError(err.message);
      return { success: false, message: err.message };
    } finally {
      setLoading(false);
    }
  };

  const register = async (username, email, password) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, email, password })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Registration failed');
      }

      const data = await response.json();
      setAuth({
        isAuthenticated: true,
        token: data.token,
        user: data.user
      });
      setPage('home');
      return { success: true };
    } catch (err) {
      setError(err.message);
      return { success: false, message: err.message };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setAuth({
      isAuthenticated: false,
      token: null,
      user: null
    });
    setPage('home');
  };

  // Post CRUD operations
  const fetchPosts = async (page = 1) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/posts?page=${page}&per_page=10`, {
        headers: auth.token ? {
          'Authorization': `Bearer ${auth.token}`
        } : {}
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch posts');
      }
      
      const data = await response.json();
      setPosts(data.posts);
      setPagination({
        page: data.page,
        pages: data.pages,
        total: data.total
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchPostDetails = async (postId) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/posts/${postId}`, {
        headers: auth.token ? {
          'Authorization': `Bearer ${auth.token}`
        } : {}
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch post details');
      }
      
      const post = await response.json();
      setCurrentPost(post);
      return post;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const createPost = async (content) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/posts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${auth.token}`
        },
        body: JSON.stringify({ content })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to create post');
      }
      
      const newPost = await response.json();
      setPosts(prevPosts => [newPost, ...prevPosts]);
      return { success: true, post: newPost };
    } catch (err) {
      setError(err.message);
      return { success: false, message: err.message };
    } finally {
      setLoading(false);
    }
  };

  const updatePost = async (postId, content) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/posts/${postId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${auth.token}`
        },
        body: JSON.stringify({ content })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to update post');
      }
      
      const updatedPost = await response.json();
      setPosts(prevPosts => 
        prevPosts.map(post => 
          post.id === postId ? { ...post, content: updatedPost.content } : post
        )
      );
      
      if (currentPost && currentPost.id === postId) {
        setCurrentPost({
          ...currentPost,
          content: updatedPost.content
        });
      }
      
      return { success: true };
    } catch (err) {
      setError(err.message);
      return { success: false, message: err.message };
    } finally {
      setLoading(false);
    }
  };

  const deletePost = async (postId) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/posts/${postId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${auth.token}`
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to delete post');
      }
      
      setPosts(prevPosts => prevPosts.filter(post => post.id !== postId));
      
      if (currentPost && currentPost.id === postId) {
        setCurrentPost(null);
        setPage('home');
      }
      
      return { success: true };
    } catch (err) {
      setError(err.message);
      return { success: false, message: err.message };
    } finally {
      setLoading(false);
    }
  };

  // Post interactions
  const likePost = async (postId) => {
    if (!auth.isAuthenticated) {
      setPage('login');
      return { success: false, message: 'Please login to like posts' };
    }
    
    try {
      const response = await fetch(`${API_URL}/posts/${postId}/like`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${auth.token}`
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to like post');
      }
      
      const data = await response.json();
      
      // Update posts state with new like count
      setPosts(prevPosts => 
        prevPosts.map(post => 
          post.id === postId 
            ? { ...post, like_count: data.like_count, user_liked: true } 
            : post
        )
      );
      
      // Update current post if we're viewing it
      if (currentPost && currentPost.id === postId) {
        setCurrentPost({
          ...currentPost,
          like_count: data.like_count
        });
      }
      
      return { success: true };
    } catch (err) {
      setError(err.message);
      return { success: false, message: err.message };
    }
  };

  const unlikePost = async (postId) => {
    try {
      const response = await fetch(`${API_URL}/posts/${postId}/like`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${auth.token}`
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to unlike post');
      }
      
      const data = await response.json();
      
      // Update posts state with new like count
      setPosts(prevPosts => 
        prevPosts.map(post => 
          post.id === postId 
            ? { ...post, like_count: data.like_count, user_liked: false } 
            : post
        )
      );
      
      // Update current post if we're viewing it
      if (currentPost && currentPost.id === postId) {
        setCurrentPost({
          ...currentPost,
          like_count: data.like_count
        });
      }      return { success: true };
    } catch (err) {
      setError(err.message);
      return { success: false, message: err.message };
    }
  };

  const addComment = async (postId, content) => {
    if (!auth.isAuthenticated) {
      setPage('login');
      return { success: false, message: 'Please login to comment' };
    }
    
    try {
      const response = await fetch(`${API_URL}/posts/${postId}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${auth.token}`
        },
        body: JSON.stringify({ content })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to add comment');
      }
      
      const newComment = await response.json();
      
      // Update posts state with new comment count
      setPosts(prevPosts => 
        prevPosts.map(post => 
          post.id === postId 
            ? { ...post, comment_count: post.comment_count + 1 } 
            : post
        )
      );
      
      // Update current post if we're viewing it
      if (currentPost && currentPost.id === postId) {
        setCurrentPost({
          ...currentPost,
          comments: [newComment, ...currentPost.comments],
          comment_count: (currentPost.comment_count || 0) + 1
        });
      }
      
      return { success: true, comment: newComment };
    } catch (err) {
      setError(err.message);
      return { success: false, message: err.message };
    }
  };

  const deleteComment = async (commentId) => {
    try {
      const response = await fetch(`${API_URL}/comments/${commentId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${auth.token}`
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to delete comment');
      }
      
      // If viewing a post, update its comments
      if (currentPost) {
        const updatedComments = currentPost.comments.filter(
          comment => comment.id !== commentId
        );
        
        setCurrentPost({
          ...currentPost,
          comments: updatedComments,
          comment_count: currentPost.comment_count - 1
        });

        // Also update in posts list if present
        setPosts(prevPosts => 
          prevPosts.map(post => 
            post.id === currentPost.id 
              ? { ...post, comment_count: post.comment_count - 1 } 
              : post
          )
        );
      }
      
      return { success: true };
    } catch (err) {
      setError(err.message);
      return { success: false, message: err.message };
    }
  };

  // Profile operations
  const fetchProfile = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/profile`, {
        headers: {
          'Authorization': `Bearer ${auth.token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch profile');
      }
      
      const profile = await response.json();
      // Update auth user with latest profile data
      setAuth(prev => ({
        ...prev,
        user: { ...prev.user, ...profile }
      }));
      
      return profile;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const fetchUserProfile = async (username) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/profile/${username}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch user profile');
      }
      
      return await response.json();
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const updateProfile = async (userData) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${auth.token}`
        },
        body: JSON.stringify(userData)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to update profile');
      }
      
      const updatedUser = await response.json();
      setAuth(prev => ({
        ...prev,
        user: updatedUser
      }));
      
      return { success: true };
    } catch (err) {
      setError(err.message);
      return { success: false, message: err.message };
    } finally {
      setLoading(false);
    }
  };

  // Search functionality
  const searchPosts = async (query, page = 1) => {
    if (!query.trim()) return;
    
    try {
      setLoading(true);
      const response = await fetch(
        `${API_URL}/posts/search?q=${encodeURIComponent(query)}&page=${page}`,
        {
          headers: auth.token ? { 'Authorization': `Bearer ${auth.token}` } : {}
        }
      );
      
      if (!response.ok) {
        throw new Error('Search failed');
      }
      
      const data = await response.json();
      setSearchResults(data.posts);
      setPagination({
        page: data.page,
        pages: data.pages,
        total: data.total
      });
      
      return data.posts;
    } catch (err) {
      setError(err.message);
      return [];
    } finally {
      setLoading(false);
    }
  };

  // Navigate to post details
  const viewPost = async (postId) => {
    const post = await fetchPostDetails(postId);
    if (post) {
      setPage('post');
    }
  };

  // Components
  const Navbar = () => (
    <nav className="navbar">
      <div className="navbar-brand" onClick={() => setPage('home')}>
        Microblog
      </div>
      <div className="search-container">
        <input
          type="text"
          placeholder="Search posts..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              searchPosts(searchQuery);
              setPage('search');
            }
          }}
        />
        <button 
          onClick={() => {
            searchPosts(searchQuery);
            setPage('search');
          }}
          className="search-button"
        >
          Search
        </button>
      </div>
      <div className="navbar-menu">
        {auth.isAuthenticated ? (
          <>
            <span
              className="navbar-item"
              onClick={() => setPage('profile')}
            >
              Profile
            </span>
            <span
              className="navbar-item logout"
              onClick={logout}
            >
              Logout
            </span>
          </>
        ) : (
          <>
            <span
              className="navbar-item"
              onClick={() => setPage('login')}
            >
              Login
            </span>
            <span
              className="navbar-item"
              onClick={() => setPage('register')}
            >
              Register
            </span>
          </>
        )}
      </div>
    </nav>
  );

  const LoginForm = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [formError, setFormError] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async (e) => {
      e.preventDefault();
      setFormError('');
      setIsSubmitting(true);
      
      if (!email || !password) {
        setFormError('Email and password are required');
        setIsSubmitting(false);
        return;
      }
      
      const result = await login(email, password);
      if (!result.success) {
        setFormError(result.message);
      }
      setIsSubmitting(false);
    };

    return (
      <div className="auth-container">
        <h2>Login</h2>
        {formError && <div className="error-message">{formError}</div>}
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
            {isSubmitting ? 'Logging in...' : 'Login'}
          </button>
        </form>
        <p className="auth-switch">
          Don't have an account? <span onClick={() => setPage('register')}>Register</span>
        </p>
      </div>
    );
  };

  const RegisterForm = () => {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [formError, setFormError] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const validateForm = () => {
      if (!username || !email || !password || !confirmPassword) {
        setFormError('All fields are required');
        return false;
      }
      
      if (password !== confirmPassword) {
        setFormError('Passwords do not match');
        return false;
      }
      
      if (password.length < 6) {
        setFormError('Password must be at least 6 characters');
        return false;
      }
      
      if (username.length < 3) {
        setFormError('Username must be at least 3 characters');
        return false;
      }
      
      return true;
    };

    const handleSubmit = async (e) => {
      e.preventDefault();
      setFormError('');
      
      if (!validateForm()) return;
      
      setIsSubmitting(true);
      const result = await register(username, email, password);
      if (!result.success) {
        setFormError(result.message);
      }
      setIsSubmitting(false);
    };

    return (
      <div className="auth-container">
        <h2>Register</h2>
        {formError && <div className="error-message">{formError}</div>}
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label>Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>Confirm Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
            {isSubmitting ? 'Registering...' : 'Register'}
          </button>
        </form>
        <p className="auth-switch">
          Already have an account? <span onClick={() => setPage('login')}>Login</span>
        </p>
      </div>
    );
  };

  const PostItem = ({ post, onViewPost }) => {
    const formattedDate = new Date(post.created_at).toLocaleString();
    
    return (
      <div className="post-item" onClick={() => onViewPost(post.id)}>
        <div className="post-header">
          <span className="post-author">{post.author.username}</span>
          <span className="post-date">{formattedDate}</span>
        </div>
        <div className="post-content">{post.content}</div>
        <div className="post-footer">
          <div className="post-stats">
            <span className="post-likes">
              <i className={`fa fa-heart${post.user_liked ? '' : '-o'}`}></i> {post.like_count}
            </span>
            <span className="post-comments">
              <i className="fa fa-comment-o"></i> {post.comment_count}
            </span>
          </div>
        </div>
      </div>
    );
  };

  const NewPostForm = () => {
    const [content, setContent] = useState('');
    const [error, setError] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async (e) => {
      e.preventDefault();
      setError('');
      
      if (!content.trim()) {
        setError('Post content is required');
        return;
      }
      
      if (content.length > 280) {
        setError('Post must be 280 characters or less');
        return;
      }
      
      setIsSubmitting(true);
      const result = await createPost(content);
      
      if (result.success) {
        setContent('');
      } else {
        setError(result.message);
      }
      
      setIsSubmitting(false);
    };

    if (!auth.isAuthenticated) {
      return (
        <div className="new-post-prompt">
          Please <span onClick={() => setPage('login')}>login</span> to create posts
        </div>
      );
    }

    return (
      <div className="new-post-container">
        <h3>Create a Post</h3>
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleSubmit} className="new-post-form">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="What's on your mind?"
            maxLength="280"
          />
          <div className="char-counter">
            {content.length}/280
          </div>
          <button 
            type="submit" 
            className="btn btn-primary" 
            disabled={isSubmitting || !content.trim()}
          >
            {isSubmitting ? 'Posting...' : 'Post'}
          </button>
        </form>
      </div>
    );
  };

  const PostsList = ({ posts, onViewPost }) => {
    if (posts.length === 0) {
      return <div className="no-posts">No posts to display</div>;
    }
    
    return (
      <div className="posts-list">
        {posts.map(post => (
          <PostItem 
            key={post.id} 
            post={post} 
            onViewPost={onViewPost}
          />
        ))}
      </div>
    );
  };

  const Pagination = ({ current, total, onPageChange }) => {
    if (total <= 1) return null;
    
    const pages = [];
    const maxPages = 5;
    
    let startPage = Math.max(1, current - Math.floor(maxPages / 2));
    const endPage = Math.min(total, startPage + maxPages - 1);
    
    startPage = Math.max(1, endPage - maxPages + 1);
    
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }
    
    return (
      <div className="pagination">
        <button 
          onClick={() => onPageChange(current - 1)}
          disabled={current === 1}
          className="pagination-btn"
        >
          &laquo; Prev
        </button>
        
        {startPage > 1 && (
          <>
            <button onClick={() => onPageChange(1)} className="pagination-btn">1</button>
            {startPage > 2 && <span className="pagination-ellipsis">...</span>}
          </>
        )}
        
        {pages.map(page => (
          <button
            key={page}
            onClick={() => onPageChange(page)}
            className={`pagination-btn ${page === current ? 'active' : ''}`}
          >
            {page}
          </button>
        ))}
        
        {endPage < total && (
          <>
            {endPage < total - 1 && <span className="pagination-ellipsis">...</span>}
            <button onClick={() => onPageChange(total)} className="pagination-btn">{total}</button>
          </>
        )}
        
        <button 
          onClick={() => onPageChange(current + 1)}
          disabled={current === total}
          className="pagination-btn"
        >
          Next &raquo;
        </button>
      </div>
    );
  };

  const PostDetailView = () => {
    const [comment, setComment] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [commentError, setCommentError] = useState('');

    if (!currentPost) {
      return <div className="loading">Loading post...</div>;
    }

    const formattedDate = new Date(currentPost.created_at).toLocaleString();

    const handleLike = async () => {
      if (auth.isAuthenticated) {
        // Optimistically update UI
        const isLiked = currentPost.user_liked;
        
        setCurrentPost({
          ...currentPost,
          user_liked: !isLiked,
          like_count: isLiked 
            ? currentPost.like_count - 1 
            : currentPost.like_count + 1
        });
        
        if (isLiked) {
          await unlikePost(currentPost.id);
        } else {
          await likePost(currentPost.id);
        }
      } else {
        setPage('login');
      }
    };

    const handleComment = async (e) => {
      e.preventDefault();
      setCommentError('');
      
      if (!comment.trim()) {
        setCommentError('Comment cannot be empty');
        return;
      }
      
      if (comment.length > 140) {
        setCommentError('Comment must be 140 characters or less');
        return;
      }
      
      setIsSubmitting(true);
      const result = await addComment(currentPost.id, comment);
      
      if (result.success) {
        setComment('');
      } else {
        setCommentError(result.message);
      }
      
      setIsSubmitting(false);
    };

    const handleDeletePost = async () => {
      if (window.confirm('Are you sure you want to delete this post?')) {
        const result = await deletePost(currentPost.id);
        if (result.success) {
          setPage('home');
        }
      }
    };

    const handleDeleteComment = async (commentId) => {
      if (window.confirm('Are you sure you want to delete this comment?')) {
        await deleteComment(commentId);
      }
    };

    return (
      <div className="post-detail">
        <div className="post-header">
          <span className="post-author">{currentPost.author.username}</span>
          <span className="post-date">{formattedDate}</span>
        </div>
        
        <div className="post-content">{currentPost.content}</div>
        
        <div className="post-actions">
          <button 
            className={`like-button ${currentPost.user_liked ? 'liked' : ''}`}
            onClick={handleLike}
          >
            <i className={`fa fa-heart${currentPost.user_liked ? '' : '-o'}`}></i>
            {currentPost.like_count} Like{currentPost.like_count !== 1 ? 's' : ''}
          </button>
          
          {auth.isAuthenticated && currentPost.author.id === auth.user.id && (
            <div className="post-owner-actions">
              <button 
                className="edit-button"
                onClick={() => {
                  setPage('edit-post');
                }}
              >
                Edit
              </button>
              <button 
                className="delete-button"
                onClick={handleDeletePost}
              >
                Delete
              </button>
            </div>
          )}
        </div>
        
        {auth.isAuthenticated && (
          <div className="comment-form-container">
            <h3>Add a Comment</h3>
            {commentError && <div className="error-message">{commentError}</div>}
            <form onSubmit={handleComment} className="comment-form">
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Write your comment..."
                maxLength="140"
              />
              <div className="char-counter">
                {comment.length}/140
              </div>
              <button 
                type="submit" 
                className="btn btn-primary" 
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Posting...' : 'Comment'}
              </button>
            </form>
          </div>
        )}
        
        <div className="comments-section">
          <h3>Comments ({currentPost.comments ? currentPost.comments.length : 0})</h3>
          {currentPost.comments && currentPost.comments.length > 0 ? (
            <div className="comments-list">
              {currentPost.comments.map(comment => (
                <div key={comment.id} className="comment-item">
                  <div className="comment-header">
                    <span className="comment-author">{comment.author.username}</span>
                    <span className="comment-date">
                      {new Date(comment.created_at).toLocaleString()}
                    </span>
                  </div>
                  <div className="comment-content">{comment.content}</div>
                  {auth.isAuthenticated && auth.user.id === comment.author.id && (
                    <button 
                      className="delete-comment-btn"
                      onClick={() => handleDeleteComment(comment.id)}
                    >
                      Delete
                    </button>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="no-comments">No comments yet</div>
          )}
        </div>
      </div>
    );
  };

  const EditPostForm = () => {
    const [content, setContent] = useState(currentPost ? currentPost.content : '');
    const [error, setError] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
      if (currentPost) {
        setContent(currentPost.content);
      }
    }, [currentPost]);

    if (!currentPost) {
      return <div className="loading">Loading post...</div>;
    }

    const handleSubmit = async (e) => {
      e.preventDefault();
      setError('');
      
      if (!content.trim()) {
        setError('Post content is required');
        return;
      }
      
      if (content.length > 280) {
        setError('Post must be 280 characters or less');
        return;
      }
      
      setIsSubmitting(true);
      const result = await updatePost(currentPost.id, content);
      
      if (result.success) {
        setPage('post');
      } else {
        setError(result.message);
      }
      
      setIsSubmitting(false);
    };

    return (
      <div className="edit-post-container">
        <h2>Edit Post</h2>
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleSubmit} className="edit-post-form">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Update your post..."
            maxLength="280"
          />
          <div className="char-counter">
            {content.length}/280
          </div>
          <div className="form-buttons">
            <button 
              type="button" 
              className="btn btn-secondary" 
              onClick={() => setPage('post')}
            >
              Cancel
            </button>
            <button 
              type="submit" 
              className="btn btn-primary" 
              disabled={isSubmitting || !content.trim()}
            >
              {isSubmitting ? 'Updating...' : 'Update Post'}
            </button>
          </div>
        </form>
      </div>
    );
  };

  const ProfileView = () => {
    const [profileData, setProfileData] = useState(null);
    const [userPosts, setUserPosts] = useState([]);
    const [isEditing, setIsEditing] = useState(false);
    const [bio, setBio] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [formError, setFormError] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
      const loadProfile = async () => {
        const data = await fetchProfile();
        if (data) {
          setProfileData(data);
          setBio(data.bio || '');
          setEmail(data.email || '');
        }
        
        // Fetch user's posts
        const response = await fetch(`${API_URL}/profile/${auth.user.username}`);
        if (response.ok) {
          const userData = await response.json();
          setUserPosts(userData.posts || []);
        }
      };
      
      loadProfile();
    }, []);

    const handleSubmit = async (e) => {
      e.preventDefault();
      setFormError('');
      
      const userData = { bio, email };
      if (password) userData.password = password;
      
      setIsSubmitting(true);
      const result = await updateProfile(userData);
      
      if (result.success) {
        setIsEditing(false);
        setPassword('');
      } else {
        setFormError(result.message);
      }
      
      setIsSubmitting(false);
    };

    if (!profileData) {
      return <div className="loading">Loading profile...</div>;
    }

    return (
      <div className="profile-container">
        <div className="profile-header">
          <h2>Profile</h2>
          {!isEditing && (
            <button 
              className="edit-profile-btn"
              onClick={() => setIsEditing(true)}
            >
              Edit Profile
            </button>
          )}
        </div>
        
        {isEditing ? (
          <div className="profile-edit">
            {formError && <div className="error-message">{formError}</div>}
            <form onSubmit={handleSubmit} className="profile-form">
              <div className="form-group">
                <label>Username</label>
                <input
                  type="text"
                  value={auth.user.username}
                  disabled
                />
                <p className="field-note">Username cannot be changed</p>
              </div>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>Bio</label>
                <textarea
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                  placeholder="Tell us about yourself"
                  maxLength="200"
                />
                <div className="char-counter">
                  {bio.length}/200
                </div>
              </div>
              <div className="form-group">
                <label>New Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Leave blank to keep current password"
                />
              </div>
              <div className="form-buttons">
                <button 
                  type="button" 
                  className="btn btn-secondary" 
                  onClick={() => {
                    setIsEditing(false);
                    setBio(profileData?.bio || '');
                    setEmail(profileData?.email || '');
                    setPassword('');
                  }}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="btn btn-primary" 
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        ) : (
          <div className="profile-details">
            <div className="profile-info">
              <p><strong>Username:</strong> {auth.user.username}</p>
              <p><strong>Email:</strong> {auth.user.email}</p>
              <p><strong>Bio:</strong> {auth.user.bio || 'No bio yet'}</p>
              <p><strong>Member since:</strong> {new Date(profileData.created_at).toLocaleDateString()}</p>
            </div>
            
            <div className="user-posts">
              <h3>Your Posts</h3>
              {userPosts.length > 0 ? (
                userPosts.map(post => (
                  <div key={post.id} className="user-post-item" onClick={() => viewPost(post.id)}>
                    <div className="post-content">{post.content}</div>
                    <div className="post-meta">
                      <span>{new Date(post.created_at).toLocaleString()}</span>
                      <div className="post-stats">
                        <span className="post-likes">
                          <i className="fa fa-heart-o"></i> {post.like_count}
                        </span>
                        <span className="post-comments">
                          <i className="fa fa-comment-o"></i> {post.comment_count}
                        </span>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="no-posts">You haven't created any posts yet</div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  const HomePage = () => (
    <div className="home-container">
      <NewPostForm />
      <h2>Latest Posts</h2>
      {loading ? (
        <div className="loading">Loading posts...</div>
      ) : error ? (
        <div className="error-message">{error}</div>
      ) : (
        <>
          <PostsList posts={posts} onView


