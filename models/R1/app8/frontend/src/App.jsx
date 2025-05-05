import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useParams } from 'react-router-dom';
import axios from 'axios';
import { FaSearch, FaSort, FaPlus } from 'react-icons/fa';
import './App.css';

const API_URL = 'http://localhost:5575/api';

// Main App Component
function App() {
  const [threads, setThreads] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('date');
  const [selectedCategory, setSelectedCategory] = useState('');

  useEffect(() => {
    fetchThreads();
  }, [searchTerm, sortBy, selectedCategory]);

  const fetchThreads = async () => {
    try {
      const response = await axios.get(`${API_URL}/threads`, {
        params: { search: searchTerm, sort: sortBy, category: selectedCategory }
      });
      setThreads(response.data);
    } catch (error) {
      console.error('Error fetching threads:', error);
    }
  };

  return (
    <Router>
      <div className="app-container">
        <nav className="navbar">
          <Link to="/" className="logo">Forum</Link>
          <div className="search-container">
            <input
              type="text"
              placeholder="Search threads..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <FaSearch className="search-icon" />
          </div>
          <Link to="/create" className="new-thread-btn">
            <FaPlus /> New Thread
          </Link>
        </nav>

        <div className="filters">
          <select value={selectedCategory} onChange={(e) => setSelectedCategory(e.target.value)}>
            <option value="">All Categories</option>
            {['General', 'Technology', 'Gaming', 'Art', 'Science'].map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
          <button onClick={() => setSortBy(sortBy === 'date' ? 'comments' : 'date')}>
            <FaSort /> Sort by {sortBy === 'date' ? 'Latest' : 'Popular'}
          </button>
        </div>

        <Routes>
          <Route path="/" element={<ThreadList threads={threads} />} />
          <Route path="/create" element={<CreateThread refresh={fetchThreads} />} />
          <Route path="/thread/:id" element={<ThreadDetail />} />
        </Routes>
      </div>
    </Router>
  );
}

// Component for listing threads
function ThreadList({ threads }) {
  return (
    <div className="thread-list">
      {threads.map(thread => (
        <div key={thread.id} className="thread-card">
          <div className="thread-header">
            <span className="category-tag">{thread.category}</span>
            <h3><Link to={`/thread/${thread.id}`}>{thread.title}</Link></h3>
          </div>
          <p className="thread-content">{thread.content}</p>
          <div className="thread-footer">
            <span>By {thread.author}</span>
            <span>{new Date(thread.date).toLocaleDateString()}</span>
            <span>{thread.comments.length} comments</span>
          </div>
        </div>
      ))}
    </div>
  );
}

// Create Thread Component
function CreateThread({ refresh }) {
  const [formData, setFormData] = useState({ title: '', content: '', category: 'General' });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/threads`, formData);
      refresh();
      window.location = '/';
    } catch (error) {
      alert('Error creating thread');
    }
  };

  return (
    <div className="create-thread">
      <h2>Create New Thread</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Title"
          required
          value={formData.title}
          onChange={(e) => setFormData({ ...formData, title: e.target.value })}
        />
        <textarea
          placeholder="Content"
          required
          value={formData.content}
          onChange={(e) => setFormData({ ...formData, content: e.target.value })}
        />
        <select
          value={formData.category}
          onChange={(e) => setFormData({ ...formData, category: e.target.value })}
        >
          {['General', 'Technology', 'Gaming', 'Art', 'Science'].map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
        <button type="submit">Create Thread</button>
      </form>
    </div>
  );
}

// Thread Detail Component
function ThreadDetail() {
  const { id } = useParams();
  const [thread, setThread] = useState(null);
  const [comment, setComment] = useState('');

  useEffect(() => {
    const fetchThread = async () => {
      try {
        const response = await axios.get(`${API_URL}/threads`);
        const found = response.data.find(t => t.id === id);
        setThread(found);
      } catch (error) {
        console.error('Error fetching thread:', error);
      }
    };
    fetchThread();
  }, [id]);

  const handleCommentSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/threads/${id}/comments`, { content: comment });
      setThread(prev => ({
        ...prev,
        comments: [...prev.comments, { content: comment, date: new Date().toISOString() }]
      }));
      setComment('');
    } catch (error) {
      alert('Error posting comment');
    }
  };

  if (!thread) return <div>Loading...</div>;

  return (
    <div className="thread-detail">
      <h2>{thread.title}</h2>
      <p className="thread-meta">
        {thread.author} - {new Date(thread.date).toLocaleDateString()}
      </p>
      <div className="content">{thread.content}</div>
      
      <div className="comments-section">
        <h3>Comments ({thread.comments.length})</h3>
        {thread.comments.map(comment => (
          <div key={comment.id} className="comment">
            <p>{comment.content}</p>
            <div className="comment-meta">
              <span>{comment.author}</span>
              <span>{new Date(comment.date).toLocaleDateString()}</span>
            </div>
          </div>
        ))}
        
        <form onSubmit={handleCommentSubmit}>
          <textarea
            placeholder="Add a comment..."
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            required
          />
          <button type="submit">Post Comment</button>
        </form>
      </div>
    </div>
  );
}

// Mounting Logic
function MountApp() {
  return <App />;
}

export default MountApp;

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<MountApp />);
