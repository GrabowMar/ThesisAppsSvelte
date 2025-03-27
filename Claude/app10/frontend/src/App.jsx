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
      }
