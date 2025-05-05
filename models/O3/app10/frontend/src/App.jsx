import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// Simple multipage routing via state:
const PAGES = {
  FEED: 'feed',
  CREATE: 'create',
  PROFILE: 'profile',
};

function App() {
  // App state
  const [page, setPage] = useState(PAGES.FEED);
  const [posts, setPosts] = useState([]);
  const [error, setError] = useState('');
  const [newPost, setNewPost] = useState({ author: '', content: '' });

  // Fetch posts when feed page is active
  useEffect(() => {
    if (page === PAGES.FEED) {
      fetch('/api/posts')
        .then((res) => res.json())
        .then((data) => {
          if (data.posts) setPosts(data.posts);
          else setError("Failed to load posts.");
        })
        .catch(() => setError("Failed to fetch posts."));
    }
  }, [page]);

  // Handle new post form submission
  const handlePostSubmit = (e) => {
    e.preventDefault();
    if (!newPost.author || !newPost.content) {
      alert("Both author and content are required.");
      return;
    }
    fetch('/api/posts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newPost),
    })
      .then((res) => {
        if (!res.ok) {
          return res.json().then((data) => { throw new Error(data.error || 'Error creating post') });
        }
        return res.json();
      })
      .then((createdPost) => {
        setNewPost({ author: '', content: '' });
        // Refresh feed if needed
        if (page === PAGES.FEED) {
          setPosts([createdPost, ...posts]);
        }
        // Switch to feed page
        setPage(PAGES.FEED);
      })
      .catch((err) => alert(err.message));
  };

  // Handle like button click
  const handleLike = (postId) => {
    fetch(`/api/posts/${postId}/like`, {
      method: 'POST',
    })
      .then((res) => res.json())
      .then((data) => {
        setPosts((prevPosts) =>
          prevPosts.map((post) =>
            post.id === postId ? { ...post, likes: data.likes } : post
          )
        );
      })
      .catch(() => alert("Unable to like the post."));
  };

  // Handle comment submission
  const handleCommentSubmit = (e, postId, commentAuthor, commentContent) => {
    e.preventDefault();
    if (!commentAuthor || !commentContent) {
      alert("Both author and comment content are required.");
      return;
    }
    fetch(`/api/posts/${postId}/comment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ author: commentAuthor, content: commentContent }),
    })
      .then((res) => res.json())
      .then((data) => {
        setPosts((prevPosts) =>
          prevPosts.map((post) =>
            post.id === postId ? { ...post, comments: data.comments } : post
          )
        );
      })
      .catch(() => alert("Unable to post comment."));
  };

  // Render different pages based on the "page" state
  return (
    <div className="App">
      <header>
        <h1>Microblog System</h1>
        <nav>
          <button onClick={() => setPage(PAGES.FEED)}>Feed</button>
          <button onClick={() => setPage(PAGES.CREATE)}>Create Post</button>
          <button onClick={() => setPage(PAGES.PROFILE)}>Profile</button>
        </nav>
      </header>
      <main>
        {error && <p className="error">{error}</p>}
        {page === PAGES.FEED && (
          <section className="feed">
            <h2>Posts Feed</h2>
            {posts.length === 0 && <p>No posts yet!</p>}
            {posts.map((post) => (
              <div key={post.id} className="post">
                <p className="author"><strong>{post.author}</strong></p>
                <p className="content">{post.content}</p>
                <div className="interactions">
                  <button onClick={() => handleLike(post.id)}>Like ({post.likes})</button>
                </div>
                <div className="comments">
                  <h4>Comments:</h4>
                  {post.comments.map((com, idx) => (
                    <p key={idx}><strong>{com.author}:</strong> {com.content}</p>
                  ))}
                  <CommentForm postId={post.id} onSubmit={handleCommentSubmit} />
                </div>
              </div>
            ))}
          </section>
        )}
        {page === PAGES.CREATE && (
          <section className="create-post">
            <h2>Create a New Post</h2>
            <form onSubmit={handlePostSubmit}>
              <div>
                <label htmlFor="author">Author:</label>
                <input
                  type="text"
                  id="author"
                  value={newPost.author}
                  onChange={(e) => setNewPost({ ...newPost, author: e.target.value })}
                  required
                />
              </div>
              <div>
                <label htmlFor="content">Content:</label>
                <textarea
                  id="content"
                  value={newPost.content}
                  onChange={(e) => setNewPost({ ...newPost, content: e.target.value })}
                  required
                ></textarea>
              </div>
              <button type="submit">Post</button>
            </form>
          </section>
        )}
        {page === PAGES.PROFILE && (
          <section className="profile">
            <h2>User Profile</h2>
            <p>
              For demonstration purposes, view user info by manually entering a username in the URL or adjusting the code.
            </p>
            {/* You can add further profile management functionality here */}
          </section>
        )}
      </main>
      <footer>
        <p>&copy; {new Date().getFullYear()} Microblog System</p>
      </footer>
    </div>
  );
}

// Reusable Comment Form component
function CommentForm({ postId, onSubmit }) {
  const [commentAuthor, setCommentAuthor] = useState('');
  const [commentContent, setCommentContent] = useState('');

  const handleSubmit = (e) => {
    onSubmit(e, postId, commentAuthor, commentContent);
    setCommentAuthor('');
    setCommentContent('');
  };

  return (
    <form onSubmit={handleSubmit} className="comment-form">
      <input
        type="text"
        placeholder="Your name"
        value={commentAuthor}
        onChange={(e) => setCommentAuthor(e.target.value)}
        required
      />
      <input
        type="text"
        placeholder="Your comment"
        value={commentContent}
        onChange={(e) => setCommentContent(e.target.value)}
        required
      />
      <button type="submit">Comment</button>
    </form>
  );
}

// Mounting Logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

export default App;
