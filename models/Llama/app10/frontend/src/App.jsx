import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [posts, setPosts] = useState([]);
  const [comments, setComments] = useState([]);
  const [liked, setLiked] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Register user
  const handleRegister = async () => {
    try {
      const response = await axios.post('http://localhost:5019/register', {
        username: username,
        email: email,
        password: password,
      });
      console.log(response.data);
    } catch (error) {
      console.error(error);
    }
  };

  // Login user
  const handleLogin = async () => {
    try {
      const response = await axios.post('http://localhost:5019/login', {
        email: email,
        password: password,
      });
      console.log(response.data);
    } catch (error) {
      console.error(error);
    }
  };

  // Create post
  const handleCreatePost = async () => {
    try {
      const response = await axios.post('http://localhost:5019/post', {
        title: 'New Post',
        content: 'This is a new post',
        username: username,
      });
      console.log(response.data);
    } catch (error) {
      console.error(error);
    }
  };

  // Get post
  const handleGetPost = async () => {
    try {
      const response = await axios.get(`http://localhost:5019/post/1`);
      console.log(response.data);
    } catch (error) {
      console.error(error);
    }
  };

  // Create comment
  const handleCreateComment = async () => {
    try {
      const response = await axios.post('http://localhost:5019/post/1/comment', {
        content: 'New comment',
        username: username,
      });
      console.log(response.data);
    } catch (error) {
      console.error(error);
    }
  };

  // Like post
  const handleLikePost = async () => {
    try {
      const response = await axios.post('http://localhost:5019/post/1/like');
      console.log(response.data);
    } catch (error) {
      console.error(error);
    }
  };

  // Search post
  const handleSearchPost = async () => {
    try {
      const response = await axios.post('http://localhost:5019/post/1/search', {
        query: searchQuery,
      });
      console.log(response.data);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div>
      <h1>Microblog</h1>
      <form>
        <label>
          Username:
          <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} />
        </label>
        <br />
        <label>
          Email:
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <br />
        <label>
          Password:
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
        <br />
        <button type="button" onClick={handleRegister}>
          Register
        </button>
        <button type="button" onClick={handleLogin}>
          Login
        </button>
      </form>
      <button type="button" onClick={handleCreatePost}>
        Create Post
      </button>
      <button type="button" onClick={handleGetPost}>
        Get Post
      </button>
      <button type="button" onClick={handleCreateComment}>
        Create Comment
      </button>
      <button type="button" onClick={handleLikePost}>
        Like Post
      </button>
      <input
        type="search"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        placeholder="Search..."
      />
      <button type="button" onClick={handleSearchPost}>
        Search
      </button>
    </div>
  );
}

export default App;
