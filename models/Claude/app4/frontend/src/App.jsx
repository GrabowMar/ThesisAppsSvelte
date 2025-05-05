// 1. Imports
import React, { useState, useEffect, useCallback, createContext, useContext } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// Context for user authentication
const AuthContext = createContext();

// 2. API Service
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5327/api';

const apiService = {
  // Helper method for making API requests
  request: async (endpoint, method = 'GET', data = null, token = null) => {
    const headers = {
      'Content-Type': 'application/json',
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
      method,
      headers,
      credentials: 'include',
    };

    if (data && (method === 'POST' || method === 'PUT')) {
      config.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(`${API_URL}${endpoint}`, config);
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.message || 'An error occurred');
      }
      
      return result;
    } catch (error) {
      console.error('API request error:', error);
      throw error;
    }
  },

  // Auth methods
  register: (userData) => apiService.request('/register', 'POST', userData),
  login: (credentials) => apiService.request('/login', 'POST', credentials),
  getProfile: (token) => apiService.request('/profile', 'GET', null, token),
  
  // Category methods
  getCategories: () => apiService.request('/categories'),
  createCategory: (categoryData, token) => apiService.request('/categories', 'POST', categoryData, token),
  
  // Post methods
  getPosts: (page = 1, perPage = 10, categoryId = null) => {
    let endpoint = `/posts?page=${page}&per_page=${perPage}`;
    if (categoryId) {
      endpoint += `&category_id=${categoryId}`;
    }
    return apiService.request(endpoint);
  },
  getPost: (postId) => apiService.request(`/posts/${postId}`),
  createPost: (postData, token) => apiService.request('/posts', 'POST', postData, token),
  updatePost: (postId, postData, token) => apiService.request(`/posts/${postId}`, 'PUT', postData, token),
  deletePost: (postId, token) => apiService.request(`/posts/${postId}`, 'DELETE', null, token),
  
  // Comment methods
  getComments: (postId) => apiService.request(`/posts/${postId}/comments`),
  addComment: (postId, commentData, token) => apiService.request(`/posts/${postId}/comments`, 'POST', commentData, token),
  deleteComment: (commentId, token) => apiService.request(`/comments/${commentId}`, 'DELETE', null, token)
};

// 3. Auth Provider Component
function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [loading, setLoading] = useState(true);

  const login = useCallback(async (credentials) => {
    try {
      const result = await apiService.login(credentials);
      setUser(result.user);
      setToken(result.token);
      localStorage.setItem('token', result.token);
      return result;
    } catch (error) {
      throw error;
    }
  }, []);

  const register = useCallback(async (userData) => {
    try {
      const result = await apiService.register(userData);
      setUser(result.user);
      setToken(result.token);
      localStorage.setItem('token', result.token);
      return result;
    } catch (error) {
      throw error;
    }
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
  }, []);

  // Load user profile if token exists
  useEffect(() => {
    const loadUser = async () => {
      if (token) {
        try {
          const { user: profile } = await apiService.getProfile(token);
          setUser(profile);
        } catch (error) {
          console.error('Failed to load user profile:', error);
          setUser(null);
          setToken(null);
          localStorage.removeItem('token');
        }
      }
      setLoading(false);
    };

    loadUser();
  }, [token]);

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, isAuthenticated: !!user, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

// Hook to use auth context
function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// 4. UI Components
function Navbar() {
  const { user, logout, isAuthenticated } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <a href="#" onClick={() => navigate('home')}>BlogApp</a>
      </div>
      
      <div className="navbar-menu-button" onClick={() => setMenuOpen(!menuOpen)}>
        <span className="material-icons">{menuOpen ? 'close' : 'menu'}</span>
      </div>
      
      <ul className={`navbar-menu ${menuOpen ? 'open' : ''}`}>
        <li><a href="#" onClick={() => navigate('home')}>Home</a></li>
        {isAuthenticated ? (
          <>
            <li><a href="#" onClick={() => navigate('new-post')}>Create Post</a></li>
            <li>
              <a href="#" className="user-menu">
                {user.username} <span className="material-icons">expand_more</span>
              </a>
              <ul className="dropdown">
                <li><a href="#" onClick={() => navigate('profile')}>Profile</a></li>
                <li><a href="#" onClick={() => navigate('my-posts')}>My Posts</a></li>
                <li><a href="#" onClick={logout}>Logout</a></li>
              </ul>
            </li>
          </>
        ) : (
          <>
            <li><a href="#" onClick={() => navigate('login')}>Login</a></li>
            <li><a href="#" onClick={() => navigate('register')}>Register</a></li>
          </>
        )}
      </ul>
    </nav>
  );
}

function Alert({ message, type = 'error', onClose }) {
  return (
    <div className={`alert ${type}`}>
      <span>{message}</span>
      {onClose && (
        <button onClick={onClose} className="close-button">
          <span className="material-icons">close</span>
        </button>
      )}
    </div>
  );
}

function Spinner() {
  return (
    <div className="spinner-container">
      <div className="spinner"></div>
    </div>
  );
}

function LoginForm() {
  const [credentials, setCredentials] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      await login(credentials);
      navigate('home');
    } catch (error) {
      setError(error.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setCredentials(prev => ({ ...prev, [name]: value }));
  };
  
  return (
    <div className="auth-form-container">
      <h2>Login</h2>
      {error && <Alert message={error} onClose={() => setError('')} />}
      <form onSubmit={handleSubmit} className="auth-form">
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            type="email"
            id="email"
            name="email"
            value={credentials.email}
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            name="password"
            value={credentials.password}
            onChange={handleChange}
            required
          />
        </div>
        <button type="submit" className="btn primary" disabled={loading}>
          {loading ? <Spinner /> : 'Login'}
        </button>
      </form>
      <p className="auth-link">
        Don't have an account? <a href="#" onClick={() => navigate('register')}>Register</a>
      </p>
    </div>
  );
}

function RegisterForm() {
  const [userData, setUserData] = useState({ username: '', email: '', password: '', confirmPassword: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    // Validate form
    if (userData.password !== userData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }
    
    try {
      await register({
        username: userData.username,
        email: userData.email,
        password: userData.password
      });
      navigate('home');
    } catch (error) {
      setError(error.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setUserData(prev => ({ ...prev, [name]: value }));
  };
  
  return (
    <div className="auth-form-container">
      <h2>Register</h2>
      {error && <Alert message={error} onClose={() => setError('')} />}
      <form onSubmit={handleSubmit} className="auth-form">
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            type="text"
            id="username"
            name="username"
            value={userData.username}
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            type="email"
            id="email"
            name="email"
            value={userData.email}
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            name="password"
            value={userData.password}
            onChange={handleChange}
            required
            minLength={8}
          />
                <div className="form-group">
          <label htmlFor="confirmPassword">Confirm Password</label>
          <input
            type="password"
            id="confirmPassword"
            name="confirmPassword"
            value={userData.confirmPassword}
            onChange={handleChange}
            required
          />
        </div>
        <button type="submit" className="btn primary" disabled={loading}>
          {loading ? <Spinner /> : 'Register'}
        </button>
      </form>
      <p className="auth-link">
        Already have an account? <a href="#" onClick={() => navigate('login')}>Login</a>
      </p>
    </div>
  );
}

function PostCard({ post, showFullContent = false, onDelete }) {
  const { isAuthenticated, user } = useAuth();
  const isAuthor = isAuthenticated && user && user.id === post.author.id;
  const truncatedContent = post.content.length > 150 
    ? post.content.substring(0, 150) + '...' 
    : post.content;
  
  const formattedDate = new Date(post.created_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
  
  return (
    <div className="post-card">
      <h2 className="post-title">
        {!showFullContent ? (
          <a href="#" onClick={() => navigate('post-detail', { id: post.id })}>
            {post.title}
          </a>
        ) : post.title}
      </h2>
      <div className="post-meta">
        <span>By {post.author.username}</span>
        <span>•</span>
        <span>{formattedDate}</span>
        <span>•</span>
        <span>Category: {post.category.name}</span>
      </div>
      {showFullContent ? (
        <div className="post-content markdown-content" dangerouslySetInnerHTML={{ __html: post.html_content }}></div>
      ) : (
        <p className="post-summary">{truncatedContent}</p>
      )}
      <div className="post-actions">
        {!showFullContent && (
          <a href="#" className="btn text" onClick={() => navigate('post-detail', { id: post.id })}>
            Read More <span className="material-icons">arrow_forward</span>
          </a>
        )}
        {showFullContent && isAuthor && (
          <div className="author-actions">
            <button className="btn secondary" onClick={() => navigate('edit-post', { id: post.id })}>
              Edit
            </button>
            <button className="btn danger" onClick={() => onDelete && onDelete(post.id)}>
              Delete
            </button>
          </div>
        )}
      </div>
      {!showFullContent && (
        <div className="post-footer">
          <span className="comments-count">
            <span className="material-icons">comment</span>
            {post.comments_count} comments
          </span>
        </div>
      )}
    </div>
  );
}

function PostList({ categoryId = null }) {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(categoryId);
  
  const loadPosts = useCallback(async () => {
    setLoading(true);
    setError('');
    
    try {
      const result = await apiService.getPosts(page, 5, selectedCategory);
      setPosts(result.posts);
      setTotalPages(result.pages);
    } catch (error) {
      setError('Failed to load posts. Please try again later.');
      console.error('Error loading posts:', error);
    } finally {
      setLoading(false);
    }
  }, [page, selectedCategory]);
  
  const loadCategories = useCallback(async () => {
    try {
      const result = await apiService.getCategories();
      setCategories(result.categories);
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  }, []);
  
  useEffect(() => {
    loadPosts();
  }, [loadPosts]);
  
  useEffect(() => {
    loadCategories();
  }, [loadCategories]);
  
  const handleCategoryChange = (categoryId) => {
    setSelectedCategory(categoryId);
    setPage(1);
  };
  
  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setPage(newPage);
    }
  };
  
  return (
    <div className="post-list-container">
      <div className="filter-container">
        <div className="category-filter">
          <button
            className={`category-btn ${!selectedCategory ? 'active' : ''}`}
            onClick={() => handleCategoryChange(null)}
          >
            All
          </button>
          {categories.map(category => (
            <button
              key={category.id}
              className={`category-btn ${selectedCategory === category.id ? 'active' : ''}`}
              onClick={() => handleCategoryChange(category.id)}
            >
              {category.name}
            </button>
          ))}
        </div>
      </div>
      
      {error && <Alert message={error} />}
      
      {loading ? (
        <Spinner />
      ) : posts.length === 0 ? (
        <div className="no-posts-message">
          <p>No posts found. {selectedCategory && 'Try selecting a different category.'}</p>
        </div>
      ) : (
        <div className="post-list">
          {posts.map(post => (
            <PostCard key={post.id} post={post} />
          ))}
        </div>
      )}
      
      {totalPages > 1 && (
        <div className="pagination">
          <button 
            className="btn pagination-btn" 
            disabled={page === 1}
            onClick={() => handlePageChange(page - 1)}
          >
            <span className="material-icons">navigate_before</span> Previous
          </button>
          <span className="page-info">Page {page} of {totalPages}</span>
          <button 
            className="btn pagination-btn" 
            disabled={page === totalPages}
            onClick={() => handlePageChange(page + 1)}
          >
            Next <span className="material-icons">navigate_next</span>
          </button>
        </div>
      )}
    </div>
  );
}

function CommentForm({ postId, onCommentAdded }) {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { token, isAuthenticated } = useAuth();
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!content.trim()) return;
    
    setLoading(true);
    setError('');
    
    try {
      await apiService.addComment(postId, { content }, token);
      setContent('');
      if (onCommentAdded) onCommentAdded();
    } catch (error) {
      setError('Failed to add comment. Please try again.');
      console.error('Error adding comment:', error);
    } finally {
      setLoading(false);
    }
  };
  
  if (!isAuthenticated) {
    return (
      <div className="login-to-comment">
        <p>Please <a href="#" onClick={() => navigate('login')}>login</a> to leave a comment.</p>
      </div>
    );
  }
  
  return (
    <div className="comment-form-container">
      <h3>Leave a Comment</h3>
      {error && <Alert message={error} onClose={() => setError('')} />}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Write your comment..."
            required
          ></textarea>
        </div>
        <button type="submit" className="btn primary" disabled={loading}>
          {loading ? <Spinner /> : 'Post Comment'}
        </button>
      </form>
    </div>
  );
}

function CommentList({ postId }) {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { user, token, isAuthenticated } = useAuth();
  
  const loadComments = useCallback(async () => {
    setLoading(true);
    setError('');
    
    try {
      const result = await apiService.getComments(postId);
      setComments(result.comments);
    } catch (error) {
      setError('Failed to load comments. Please try again later.');
      console.error('Error loading comments:', error);
    } finally {
      setLoading(false);
    }
  }, [postId]);
  
  useEffect(() => {
    loadComments();
  }, [loadComments]);
  
  const handleDeleteComment = async (commentId) => {
    if (!window.confirm('Are you sure you want to delete this comment?')) {
      return;
    }
    
    try {
      await apiService.deleteComment(commentId, token);
      loadComments();
    } catch (error) {
      setError('Failed to delete comment. Please try again.');
      console.error('Error deleting comment:', error);
    }
  };
  
  if (loading) return <Spinner />;
  if (error) return <Alert message={error} />;
  
  return (
    <div className="comments-section">
      <h3>Comments ({comments.length})</h3>
      
      {comments.length === 0 ? (
        <p className="no-comments">No comments yet. Be the first to comment!</p>
      ) : (
        <div className="comments-list">
          {comments.map(comment => {
            const isAuthor = isAuthenticated && user && user.id === comment.author.id;
            const formattedDate = new Date(comment.created_at).toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            });
            
            return (
              <div key={comment.id} className="comment">
                <div className="comment-header">
                  <span className="comment-author">{comment.author.username}</span>
                  <span className="comment-date">{formattedDate}</span>
                </div>
                <p className="comment-content">{comment.content}</p>
                {isAuthor && (
                  <button 
                    className="btn text danger" 
                    onClick={() => handleDeleteComment(comment.id)}
                  >
                    <span className="material-icons">delete</span> Delete
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function PostDetail({ postId }) {
  const [post, setPost] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { token } = useAuth();
  
  const loadPost = useCallback(async () => {
    setLoading(true);
    setError('');
    
    try {
      const result = await apiService.getPost(postId);
      setPost(result.post);
    } catch (error) {
      setError('Failed to load post. Please try again later.');
      console.error('Error loading post:', error);
    } finally {
      setLoading(false);
    }
  }, [postId]);
  
  useEffect(() => {
    loadPost();
  }, [loadPost]);
  
  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this post? This action cannot be undone.')) {
      return;
    }
    
    try {
      await apiService.deletePost(id, token);
      navigate('home');
    } catch (error) {
      setError('Failed to delete post. Please try again.');
      console.error('Error deleting post:', error);
    }
  };
  
  if (loading) return <Spinner />;
  if (error) return <Alert message={error} />;
  if (!post) return <Alert message="Post not found" type="warning" />;
  
  return (
    <div className="post-detail-container">
      <button className="btn text" onClick={() => navigate('home')}>
        <span className="material-icons">arrow_back</span> Back to Posts
      </button>
      <PostCard post={post} showFullContent={true} onDelete={handleDelete} />
      <div className="post-comments">
        <CommentForm postId={postId} onCommentAdded={loadPost} />
        <CommentList postId={postId} />
      </div>
    </div>
  );
}

function PostForm({ postId = null }) {
  const [formData, setFormData] = useState({ title: '', content: '', category_id: '' });
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [categories, setCategories] = useState([]);
  const { token } = useAuth();
  const isEditing = !!postId;
  
  // Load categories
  useEffect(() => {
    const loadCategories = async () => {
      try {
        const result = await apiService.getCategories();
        setCategories(result.categories);
        
        // Set default category if not editing
        if (!isEditing && result.categories.length > 0 && !formData.category_id) {
          setFormData(prev => ({ ...prev, category_id: result.categories[0].id }));
        }
      } catch (error) {
        console.error('Error loading categories:', error);
        setError('Failed to load categories. Please try again later.');
      }
    };
    
    loadCategories();
  }, [isEditing, formData.category_id]);
  
  // Load post data if editing
  useEffect(() => {
    if (isEditing) {
      const loadPost = async () => {
        setLoading(true);
        setError('');
        
        try {
          const result = await apiService.getPost(postId);
          const { title, content, category } = result.post;
          setFormData({ title, content, category_id: category.id });
        } catch (error) {
          console.error('Error loading post:', error);
          setError('Failed to load post. Please try again later.');
        } finally {
          setLoading(false);
        }
      };
      
      loadPost();
    }
  }, [isEditing, postId]);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.title.trim() || !formData.content.trim() || !formData.category_id) {
      setError('Please fill in all required fields.');
      return;
    }
    
    setSubmitting(true);
    setError('');
    
    try {
      if (isEditing) {
        await apiService.updatePost(postId, formData, token);
      } else {
        await apiService.createPost(formData, token);
      }
      
      navigate(isEditing ? `post-detail` : 'home', isEditing ? { id: postId } : {});
    } catch (error) {
      setError(`Failed to ${isEditing ? 'update' : 'create'} post. Please try again.`);
      console.error(`Error ${isEditing ? 'updating' : 'creating'} post:`, error);
    } finally {
      setSubmitting(false);
    }
  };
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };
  
  if (loading) return <Spinner />;
  
  return (
    <div className="post-form-container">
      <h2>{isEditing ? 'Edit Post' : 'Create New Post'}</h2>
      
      {error && <Alert message={error} onClose={() => setError('')} />}
      
      <form onSubmit={handleSubmit} className="post-form">
        <div className="form-group">
          <label htmlFor="title">Title</label>
          <input
            type="text"
            id="title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            placeholder="Enter post title"
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="category_id">Category</label>
          <select
            id="category_id"
            name="category_id"
            value={formData.category_id}
            onChange={handleChange}
            required
          >
            <option value="">Select a category</option>
            {categories.map(category => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </div>
        
        <div className="form-group">
          <label htmlFor="content">Content (Markdown supported)</label>
          <textarea
            id="content"
            name="content"
            value={formData.content}
            onChange={handleChange}
            placeholder="Write your post content in Markdown format..."
            required
            rows={10}
          ></textarea>
        </div>
        
        <div className="markdown-preview">
          <h3>Preview</h3>
          {formData.content && (
            <div className="preview-content">
              {formData.content}
            </div>
          )}
        </div>
        
        <div className="form-actions">
          <button type="button" className="btn secondary" onClick={() => navigate('home')}>
            Cancel
          </button>
          <button type="submit" className="btn primary" disabled={submitting}>
            {submitting ? <Spinner /> : isEditing ? 'Update Post' : 'Create Post'}
          </button>
        </div>
      </form>
    </div>
  );
}

function UserProfile() {
  const { user, token } = useAuth();
  const [userPosts, setUserPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  useEffect(() => {
    const loadUserPosts = async () => {
      setLoading(true);
      setError('');
      
      try {
        // This API endpoint is not provided but would be implemented to get posts by user id
        const result = await apiService.getPosts(1, 100);
        // Filter posts by current user
        const filteredPosts = result.posts.filter(post => post.author.id === user.id);
        setUserPosts(filteredPosts);
      } catch (error) {
        setError('Failed to load your posts. Please try again later.');
        console.error('Error loading user posts:', error);
      } finally {
        setLoading(false);
      }
    };
    
    if (token) {
      loadUserPosts();
    }
  }, [user, token]);
  
  if (!user) return <Alert message="Please login to view your profile" type="warning" />;
  
  return (
    <div className="profile-container">
      <h2>My Profile</h2>
      
      <div className="profile-card">
        <div className="profile-info">
          <h3>{user.username}</h3>
          <p>Email: {user.email}</p>
          <p>Joined: {new Date(user.created_at).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
          })}</p>
        </div>
      </div>
      
      <h3>My Posts</h3>
      {error && <Alert message={error} />}
      
      {loading ? (
        <Spinner />
      ) : userPosts.length === 0 ? (
        <div className="no-posts-message">
          <p>You haven't created any posts yet.</p>
          <button className="btn primary" onClick={() => navigate('new-post')}>
            Create Your First Post
          </button>
        </div>
      ) : (
        <div className="user-posts">
          {userPosts.map(post => (
            <PostCard key={post.id} post={post} />
          ))}
        </div>
      )}
    </div>
  );
}

function NotFound() {
  return (
    <div className="not-found">
      <h2>404 - Page Not Found</h2>
      <p>The page you are looking for does not exist.</p>
      <button className="btn primary" onClick={() => navigate('home')}>
        Back to Home
      </button>
    </div>
  );
}

// 5. Router implementation
function Router() {
  const [route, setRoute] = useState('home');
  const [params, setParams] = useState({});
  
  // Expose navigation globally
  window.navigate = (route, params = {}) => {
    setRoute(route);
    setParams(params);
    window.scrollTo(0, 0);
  };
  
  return (
    <>
      <Navbar />
      <div className="container">
        {route === 'home' && <PostList />}
        {route === 'login' && <LoginForm />}
        {route === 'register' && <RegisterForm />}
        {route === 'post-detail' && <PostDetail postId={params.id} />}
        {route === 'new-post' && <PostForm />}
        {route === 'edit-post' && <PostForm postId={params.id} />}
        {route === 'profile' && <UserProfile />}
        {route === 'my-posts' && <PostList categoryId={null} />}
        {!['home', 'login', 'register', 'post-detail', 'new-post', 'edit-post', 'profile', 'my-posts'].includes(route) && <NotFound />}
      </div>
      <footer className="footer">
        <div className="container">
          <p>&copy; {new Date().getFullYear()} BlogApp - A Flask + React Blog Platform</p>
        </div>
      </footer>
    </>
  );
}

// 7. Main App Component
function App() {
  return (
    <AuthProvider>
      <Router />
    </AuthProvider>
  );
}

// 8. Mounting Logic
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

export default App;


