import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import axios from 'axios';
import './App.css';

function App() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [userId, setUserId] = useState(1);
  const [posts, setPosts] = useState([]);
  const [likes, setLikes] = useState([]);
  const [comments, setComments] = useState([]);

  useEffect(() => {
    axios.get('http://localhost:5019/posts')
      .then(response => {
        setPosts(response.data);
      })
      .catch(error => {
        console.log(error);
      });

    axios.get('http://localhost:5019/likes')
      .then(response => {
        setLikes(response.data);
      })
      .catch(error => {
        console.log(error);
      });

    axios.get('http://localhost:5019/comments')
      .then(response => {
        setComments(response.data);
      })
      .catch(error => {
        console.log(error);
      });
  }, []);

  const register = () => {
    axios.post('http://localhost:5019/register', {
      username: username,
      password: password
    })
      .then(response => {
        console.log(response.data);
      })
      .catch(error => {
        console.log(error);
      });
  };

  const login = () => {
    axios.post('http://localhost:5019/login', {
      username: username,
      password: password
    })
      .then(response => {
        console.log(response.data);
      })
      .catch(error => {
        console.log(error);
      });
  };

  const createPost = () => {
    axios.post('http://localhost:5019/posts', {
      title: title,
      content: content,
      user_id: userId
    })
      .then(response => {
        console.log(response.data);
      })
      .catch(error => {
        console.log(error);
      });
  };

  const updatePost = (id) => {
    axios.put(`http://localhost:5019/posts/${id}`, {
      title: title,
      content: content
    })
      .then(response => {
        console.log(response.data);
      })
      .catch(error => {
        console.log(error);
      });
  };

  const deletePost = (id) => {
    axios.delete(`http://localhost:5019/posts/${id}`)
      .then(response => {
        console.log(response.data);
      })
      .catch(error => {
        console.log(error);
      });
  };

  return (
    <Router>
      <div className="App">
        <h1>CRUD Microblog Application</h1>
        <Routes>
          <Route path="/" element={
            <div>
              <h2>Register</h2>
              <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" />
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" />
              <button onClick={register}>Register</button>
              <h2>Login</h2>
              <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" />
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" />
              <button onClick={login}>Login</button>
              <h2>Create Post</h2>
              <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Title" />
              <textarea value={content} onChange={(e) => setContent(e.target.value)} placeholder="Content" />
              <button onClick={createPost}>Create Post</button>
              <h2>Posts</h2>
              {posts.map((post) => (
                <div key={post.id}>
                  <h3>{post.title}</h3>
                  <p>{post.content}</p>
                  <button onClick={() => updatePost(post.id)}>Update</button>
                  <button onClick={() => deletePost(post.id)}>Delete</button>
                </div>
              ))}
            </div>
          } />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
