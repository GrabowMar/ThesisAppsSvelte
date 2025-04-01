import { onMount, useState } from 'react';
import ReactDOM from 'react-dom/client';
import { formatDistanceToNow } from 'date-fns';

// Main App Component
function App() {
  const [currentPage, setCurrentPage] = useState('login');
  const [posts, setPosts] = useState([]);
  const [user, setUser] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Auth logic
  const loginUser = async (credentials) => {
    try {
      const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
      });
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('token', data.token);
        setUser({ id: data.user_id });
        setCurrentPage('dashboard');
      }
    } catch (err) {/* Handle error */}
  };

  // Post fetching with search
  const fetchPosts = async () => {
    const url = searchQuery ? `/api/posts/search?q=${searchQuery}` : '/api/posts';
    const res = await fetch(url);
    if (res.ok) setPosts(await res.json());
  };

  onMount(() => {
    const token = localStorage.getItem('token');
    if (token) {
      // Validate token and fetch user
      setCurrentPage('dashboard');
      fetchPosts();
    }
  });

  return (
    <main>
      {currentPage === 'dashboard' && (
        <div className="dashboard">
          <nav>{/* Navigation items */}</nav>
          <input 
            type="text" 
            placeholder="Search posts..." 
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <div className="posts-grid">
            {posts.map(post => (
              <div key={post.id} className="post-card">
                <h3>{post.author}</h3>
                <p>{post.content}</p>
                <div className="post-actions">
                  <button onClick={() => handleLike(post.id)}>
                    ♥ {post.likes}
                  </button>
                  <span>{post.comment_count} comments</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      {/* Other page conditions */}
    </main>
  );
}

// Mounting
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
