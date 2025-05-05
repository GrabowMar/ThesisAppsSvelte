import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [route, setRoute] = useState('home');
  const [threads, setThreads] = useState([]);
  const [categories, setCategories] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortOrder, setSortOrder] = useState('date_desc'); // Default sorting
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loginMessage, setLoginMessage] = useState('');
  const [loggedIn, setLoggedIn] = useState(false);
  const [user, setUser] = useState(null);

  useEffect(() => {
    fetchCategories();
    if (loggedIn) {
      fetchThreads();
    }
  }, [loggedIn, sortOrder]);

  const navigate = (newRoute) => {
    setRoute(newRoute);
  };

  const fetchThreads = async () => {
    try {
      const [sortBy, order] = sortOrder.split('_'); // Split sortOrder
      const response = await fetch(`/api/threads?sort_by=${sortBy}&order=${order}`);
      if (!response.ok) {
        throw new Error('Failed to fetch threads');
      }
      const data = await response.json();
      setThreads(data);
    } catch (error) {
      console.error('Error fetching threads:', error);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await fetch('/api/categories');
      if (!response.ok) {
        throw new Error('Failed to fetch categories');
      }
      const data = await response.json();
      setCategories(data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const handleSearch = async () => {
    try {
      const response = await fetch(`/api/threads/search?query=${searchTerm}`);
      if (!response.ok) {
        throw new Error('Search failed');
      }
      const data = await response.json();
      setThreads(data); // Update threads with search results
    } catch (error) {
      console.error('Error searching threads:', error);
    }
  };

  const handleLogin = async () => {
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (response.ok) {
        setLoginMessage(data.message);
        setLoggedIn(true);
        setUser(data.username);
        navigate('home');
      } else {
        setLoginMessage(data.message);
      }
    } catch (error) {
      console.error('Login error:', error);
      setLoginMessage('An error occurred during login.');
    }
  };

  const handleLogout = () => {
    setLoggedIn(false);
    setUser(null);
    setUsername('');
    setPassword('');
    setLoginMessage('');
  };

  const renderContent = () => {
    switch (route) {
      case 'login':
        return (
          <div className="login-container">
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
            {loginMessage && <p className="login-message">{loginMessage}</p>}
          </div>
        );
      case 'home':
        if (!loggedIn) {
          return (
            <div>
              <p>Please log in to view the forum.</p>
              <button onClick={() => navigate('login')}>Go to Login</button>
            </div>
          );
        }
        return (
          <ForumHome
            threads={threads}
            categories={categories}
            searchTerm={searchTerm}
            setSearchTerm={setSearchTerm}
            handleSearch={handleSearch}
            setSortOrder={setSortOrder}
            loggedIn={loggedIn}
            onLogout={handleLogout}
            user={user}
            fetchThreads={fetchThreads}
            navigate={navigate}
          />
        );
      case 'createThread':
        return <CreateThreadForm categories={categories} fetchThreads={fetchThreads} navigate={navigate} user={user}/>;
      case 'threadDetail':
        return <ThreadDetailView />;
      default:
        return <p>Page not found</p>;
    }
  };

  return (
    <div className="app">
      <header>
        <h1>Forum Application</h1>
        {loggedIn && <button onClick={handleLogout}>Logout ({user})</button>}
      </header>
      <main>{renderContent()}</main>
      <footer>
        <p>&copy; 2024 Forum App</p>
      </footer>
    </div>
  );
}

function ForumHome({ threads, categories, searchTerm, setSearchTerm, handleSearch, setSortOrder, loggedIn, onLogout, user, fetchThreads, navigate }) {
  return (
    <div className="forum-home">
      <div className="toolbar">
        <input
          type="text"
          placeholder="Search threads..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <button onClick={handleSearch}>Search</button>
        <select onChange={(e) => setSortOrder(e.target.value)}>
          <option value="date_desc">Date (Newest First)</option>
          <option value="date_asc">Date (Oldest First)</option>
          <option value="title_asc">Title (A-Z)</option>
          <option value="title_desc">Title (Z-A)</option>
        </select>
        <button onClick={() => navigate('createThread')}>Create Thread</button>
      </div>
      <div className="thread-list">
        {threads.map((thread) => (
          <ThreadItem key={thread.id} thread={thread} fetchThreads={fetchThreads} navigate={navigate} />
        ))}
      </div>
    </div>
  );
}

function ThreadItem({ thread, fetchThreads, navigate }) {
  const [showComments, setShowComments] = useState(false);
  const [comments, setComments] = useState([]);
  const [newCommentContent, setNewCommentContent] = useState('');
  const [commentAuthor, setCommentAuthor] = useState('Anonymous');  //Default value

  useEffect(() => {
    if (showComments) {
      fetchComments();
    }
  }, [showComments]);

  const fetchComments = async () => {
    try {
      const response = await fetch(`/api/threads/${thread.id}/comments`);
      if (!response.ok) {
        throw new Error('Failed to fetch comments');
      }
      const data = await response.json();
      setComments(data);
    } catch (error) {
      console.error('Error fetching comments:', error);
    }
  };

  const handleAddComment = async () => {
    if (!newCommentContent.trim()) {
      alert('Comment cannot be empty');
      return;
    }

    try {
      const response = await fetch(`/api/threads/${thread.id}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: newCommentContent,
          author: commentAuthor, // You might want to get the actual user's name here
        }),
      });

      if (response.ok) {
        setNewCommentContent('');
        setCommentAuthor('Anonymous');
        fetchComments(); // Refresh comments after adding a new one
      } else {
        console.error('Failed to add comment');
      }
    } catch (error) {
      console.error('Error adding comment:', error);
    }
  };

    const handleDeleteThread = async () => {
        try {
            const response = await fetch(`/api/threads/${thread.id}`, {
                method: 'DELETE',
            });

            if (response.ok) {
                fetchThreads(); // Refresh threads after deleting one
            } else {
                console.error('Failed to delete thread');
            }
        } catch (error) {
            console.error('Error deleting thread:', error);
        }
    };

    return (
        <div className="thread-item">
            <h3>{thread.title}</h3>
            <p>Category: {thread.category}</p>
            <p>Author: {thread.author}</p>
            <p>{thread.content}</p>
            <p className="date">
                Created at: {new Date(thread.created_at).toLocaleString()}
            </p>
            <button onClick={() => setShowComments(!showComments)}>
                {showComments ? 'Hide Comments' : 'Show Comments'}
            </button>
            <button onClick={handleDeleteThread}>Delete Thread</button>
            {showComments && (
                <div className="comments-section">
                    <h4>Comments:</h4>
                    {comments.map((comment) => (
                        <div key={comment.id} className="comment">
                            <p>{comment.content}</p>
                            <p className="comment-author">
                                By: {comment.author} on {new Date(comment.created_at).toLocaleString()}
                            </p>
                        </div>
                    ))}
                    <div className="add-comment">
                        <textarea
                            placeholder="Add a comment..."
                            value={newCommentContent}
                            onChange={(e) => setNewCommentContent(e.target.value)}
                        />
                        <input
                            type="text"
                            placeholder="Your Name (Optional)"
                            value={commentAuthor}
                            onChange={(e) => setCommentAuthor(e.target.value)}
                        />
                        <button onClick={handleAddComment}>Add Comment</button>
                    </div>
                </div>
            )}
        </div>
    );
}

function CreateThreadForm({ categories, fetchThreads, navigate, user }) {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState(categories[0] || 'General');

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!title.trim() || !content.trim()) {
      alert('Title and content cannot be empty.');
      return;
    }

    try {
      const response = await fetch('/api/threads', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: title,
          content: content,
          category: category,
          author: user || 'Anonymous',
        }),
      });

      if (response.ok) {
        // Optionally show a success message
        alert('Thread created successfully!');
        // Refresh the thread list
        fetchThreads();
        // Navigate back to the home page
        navigate('home');
      } else {
        // Handle errors
        const errorData = await response.json();
        alert(`Failed to create thread: ${errorData.message || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error creating thread:', error);
      alert('An error occurred while creating the thread.');
    }
  };

  return (
    <div className="create-thread-form">
      <h2>Create New Thread</h2>
      <form onSubmit={handleSubmit}>
        <label htmlFor="title">Title:</label>
        <input
          type="text"
          id="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />

        <label htmlFor="content">Content:</label>
        <textarea
          id="content"
          value={content}
          onChange={(e) => setContent(e.target.value)}
        />

        <label htmlFor="category">Category:</label>
        <select
          id="category"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          {categories.map((cat) => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>

        <button type="submit">Create Thread</button>
        <button type="button" onClick={() => navigate('home')}>Cancel</button>
      </form>
    </div>
  );
}

function ThreadDetailView() {
  return (
    <div>
      <h2>Thread Detail View (Placeholder)</h2>
      <p>This is a placeholder for the thread detail view.</p>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

export default App;
