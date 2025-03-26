// App.jsx
import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import axios from 'axios';
import { Routes, Route, Link, BrowserRouter } from 'react-router-dom';

function App() {
  const [blogPosts, setBlogPosts] = useState([]);
  const [comments, setComments] = useState([]);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState('');
  const [commentContent, setCommentContent] = useState('');

  useEffect(() => {
    axios.get('/api/blog-posts')
      .then(response => {
        setBlogPosts(response.data);
      })
      .catch(error => {
        console.error(error);
      });
  }, []);

  const handleSubmit = (event) => {
    event.preventDefault();
    axios.post('/api/blog-posts', {
      title,
      content,
      category
    })
      .then(response => {
        setBlogPosts([...blogPosts, response.data]);
        setTitle('');
        setContent('');
        setCategory('');
      })
      .catch(error => {
        console.error(error);
      });
  };

  const handleCommentSubmit = (event) => {
    event.preventDefault();
    axios.post('/api/comments', {
      content: commentContent,
      blog_post_id: 1
    })
      .then(response => {
        setComments([...comments, response.data]);
        setCommentContent('');
      })
      .catch(error => {
        console.error(error);
      });
  };

  return (
    <BrowserRouter>
      <div>
        <h1>Blog Posts</h1>
        <ul>
          {blogPosts.map((blogPost) => (
            <li key={blogPost.id}>
              <Link to={`/blog-posts/${blogPost.id}`}>{blogPost.title}</Link>
            </li>
          ))}
        </ul>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Title"
          />
          <textarea
            value={content}
            onChange={(event) => setContent(event.target.value)}
            placeholder="Content"
          />
          <input
            type="text"
            value={category}
            onChange={(event) => setCategory(event.target.value)}
            placeholder="Category"
          />
          <button type="submit">Create Blog Post</button>
        </form>
        <Routes>
          <Route
            path="/blog-posts/:id"
            element={
              <div>
                <h1>Blog Post</h1>
                <p>Content: {content}</p>
                <form onSubmit={handleCommentSubmit}>
                  <textarea
                    value={commentContent}
                    onChange={(event) => setCommentContent(event.target.value)}
                    placeholder="Comment"
                  />
                  <button type="submit">Create Comment</button>
                </form>
              </div>
            }
          />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
