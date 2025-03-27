import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [posts, setPosts] = useState([]);
  const [postContent, setPostContent] = useState('');
  const [error, setError] = useState('');

  // Fetch all posts on mount
  useEffect(() => {
    fetch('/api/posts')
      .then((res) => res.json())
      .then(setPosts)
      .catch((err) => setError("Failed to fetch posts."));
  }, []);

  // Create a new post
  const createPost = () => {
    if (!postContent.trim()) {
      setError('Post content cannot be empty!');
      return;
    }
    fetch('/api/posts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: postContent, author: "Anonymous" })
    })
      .then((res) => res.json())
      .then((newPost) => {
        setPosts([newPost, ...posts]);
        setPostContent('');
      })
      .catch(() => setError("Failed to create post."));
  };

  // Like a post
  const likePost = (postId) => {
    fetch(`/api/posts/${postId}/like`, {
      method: 'POST',
    })
      .then((res) => res.json())
      .then((updatedPost) => {
        setPosts(posts.map((post) =>
          post.id === updatedPost.id ? updatedPost : post
        ));
      })
      .catch(() => setError("Failed to like post."));
  };

  return (
    <div className="App">
      <header>
        <h1>Microblog</h1>
      </header>
      {error && <div className="error">{error}</div>}
      <section className="create-post">
        <textarea
          value={postContent}
          onChange={(e) => setPostContent(e.target.value)}
          placeholder="What's on your mind?"
        ></textarea>
        <button onClick={createPost}>Post</button>
      </section>
      <section className="post-feed">
        {posts.map((post) => (
          <div key={post.id} className="post">
            <p>{post.content}</p>
            <small>By {post.author}</small>
            <div className="actions">
              <button onClick={() => likePost(post.id)}>Like ({post.likes})</button>
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}

// Mount React app to root element
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
