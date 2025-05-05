import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// API configuration
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5325/api';

// Main app component
function App() {
  // State for page routing
  const [currentPage, setCurrentPage] = useState('form');
  const [stats, setStats] = useState(null);
  const [adminKey, setAdminKey] = useState(localStorage.getItem('admin_key') || '');
  const [isAdmin, setIsAdmin] = useState(false);
  const [feedbackList, setFeedbackList] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Navigation handler
  const navigate = (page) => {
    setCurrentPage(page);
    
    // Load data for specific pages
    if (page === 'stats') {
      fetchStats();
    } else if (page === 'admin' && adminKey) {
      fetchFeedbackList();
    }
  };

  // Fetch feedback statistics
  const fetchStats = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_URL}/feedback/stats`);
      const data = await response.json();
      
      if (data.success) {
        setStats(data.stats);
      } else {
        setError(data.errors || 'Failed to load statistics');
      }
    } catch (err) {
      setError('Network error while fetching statistics');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  // For admin: fetch all feedback
  const fetchFeedbackList = async () => {
    if (!adminKey) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_URL}/feedback`, {
        headers: {
          'X-API-Key': adminKey
        }
      });
      
      const data = await response.json();
      
      if (data.success) {
        setFeedbackList(data.feedback);
        setIsAdmin(true);
        localStorage.setItem('admin_key', adminKey);
      } else {
        setError(data.errors || 'Authentication failed');
        setIsAdmin(false);
      }
    } catch (err) {
      setError('Network error while fetching feedback');
      console.error(err);
      setIsAdmin(false);
    } finally {
      setIsLoading(false);
    }
  };

  // For admin: delete feedback
  const deleteFeedback = async (id) => {
    if (!confirm('Are you sure you want to delete this feedback?')) {
      return;
    }
    
    setIsLoading(true);
    
    try {
      const response = await fetch(`${API_URL}/feedback/${id}`, {
        method: 'DELETE',
        headers: {
          'X-API-Key': adminKey
        }
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Remove from local state
        setFeedbackList(feedbackList.filter(item => item.id !== id));
      } else {
        setError(data.errors || 'Failed to delete');
      }
    } catch (err) {
      setError('Network error while deleting');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  // Render the appropriate page based on currentPage state
  return (
    <div className="app-container">
      <header>
        <h1>Customer Feedback Portal</h1>
        <nav>
          <button 
            className={currentPage === 'form' ? 'active' : ''} 
            onClick={() => navigate('form')}
          >
            Submit Feedback
          </button>
          <button 
            className={currentPage === 'stats' ? 'active' : ''} 
            onClick={() => navigate('stats')}
          >
            View Statistics
          </button>
          <button 
            className={currentPage === 'admin' ? 'active' : ''} 
            onClick={() => navigate('admin')}
          >
            Admin Panel
          </button>
        </nav>
      </header>

      <main>
        {error && <div className="error-message">{error}</div>}
        
        {isLoading && <div className="loading">Loading...</div>}
        
        {currentPage === 'form' && <FeedbackForm apiUrl={API_URL} />}
        
        {currentPage === 'stats' && stats && (
          <StatsDisplay stats={stats} />
        )}
        
        {currentPage === 'admin' && (
          <AdminPanel 
            isAdmin={isAdmin}
            adminKey={adminKey}
            setAdminKey={setAdminKey}
            onLogin={fetchFeedbackList}
            feedbackList={feedbackList}
            onDelete={deleteFeedback}
          />
        )}
      </main>
      
      <footer>
        <p>&copy; {new Date().getFullYear()} Feedback System</p>
      </footer>
    </div>
  );
}

// FeedbackForm component
function FeedbackForm({ apiUrl }) {
  const initialFormState = {
    name: '',
    email: '',
    rating: '5',
    category: 'General',
    comment: ''
  };
  
  const [formData, setFormData] = useState(initialFormState);
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  
  // Handle form input changes
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
    
    // Clear field-specific error when user types
    if (errors[name]) {
      setErrors({
        ...errors,
        [name]: ''
      });
    }
  };
  
  // Local form validation
  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }
    
    if (!formData.rating) {
      newErrors.rating = 'Please select a rating';
    }
    
    if (!formData.comment.trim()) {
      newErrors.comment = 'Feedback comment is required';
    } else if (formData.comment.length < 10) {
      newErrors.comment = 'Comment must be at least 10 characters';
    }
    
    return newErrors;
  };
  
  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate form
    const validationErrors = validateForm();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    
    setIsSubmitting(true);
    setErrors({});
    
    try {
      const response = await fetch(`${apiUrl}/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      
      if (data.success) {
        setSubmitSuccess(true);
        setFormData(initialFormState);
        // Reset success message after 5 seconds
        setTimeout(() => {
          setSubmitSuccess(false);
        }, 5000);
      } else {
        setErrors(data.errors || { general: 'Submission failed' });
      }
    } catch (err) {
      console.error('Error submitting feedback:', err);
      setErrors({ general: 'Network error. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <div className="feedback-form-container">
      <h2>Share Your Feedback</h2>
      
      {submitSuccess && (
        <div className="success-message">
          Thank you for your feedback! It has been submitted successfully.
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="name">Name</label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="Your name"
            className={errors.name ? 'error' : ''}
            disabled={isSubmitting}
          />
          {errors.name && <div className="error-text">{errors.name}</div>}
        </div>
        
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="Your email"
            className={errors.email ? 'error' : ''}
            disabled={isSubmitting}
          />
          {errors.email && <div className="error-text">{errors.email}</div>}
        </div>
        
        <div className="form-group">
          <label htmlFor="category">Category</label>
          <select
            id="category"
            name="category"
            value={formData.category}
            onChange={handleChange}
            disabled={isSubmitting}
          >
            <option value="General">General</option>
            <option value="Product">Product</option>
            <option value="Service">Service</option>
            <option value="Website">Website</option>
            <option value="Support">Support</option>
          </select>
        </div>
        
        <div className="form-group">
          <label htmlFor="rating">Rating</label>
          <div className="rating-selector">
            {[1, 2, 3, 4, 5].map((num) => (
              <label key={num} className="rating-label">
                <input
                  type="radio"
                  name="rating"
                  value={num}
                  checked={formData.rating === num.toString()}
                  onChange={handleChange}
                  disabled={isSubmitting}
                />
                {num}
              </label>
            ))}
          </div>
          {errors.rating && <div className="error-text">{errors.rating}</div>}
        </div>
        
        <div className="form-group">
          <label htmlFor="comment">Your Feedback</label>
          <textarea
            id="comment"
            name="comment"
            value={formData.comment}
            onChange={handleChange}
            placeholder="Tell us what you think..."
            rows="5"
            className={errors.comment ? 'error' : ''}
            disabled={isSubmitting}
          ></textarea>
          {errors.comment && <div className="error-text">{errors.comment}</div>}
        </div>
        
        {errors.general && <div className="error-text general">{errors.general}</div>}
        
        <button 
          type="submit" 
          className="submit-button"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
        </button>
      </form>
    </div>
  );
}

// Stats display component
function StatsDisplay({ stats }) {
  return (
    <div className="stats-container">
      <h2>Feedback Statistics</h2>
      
      {stats.count === 0 ? (
        <p className="no-data">No feedback data available yet.</p>
      ) : (
        <>
          <div className="stats-summary">
            <div className="stat-card">
              <h3>Total Submissions</h3>
              <div className="stat-value">{stats.count}</div>
            </div>
            
            <div className="stat-card">
              <h3>Average Rating</h3>
              <div className="stat-value">{stats.avg_rating.toFixed(1)}</div>
              <div className="star-display">
                {[1, 2, 3, 4, 5].map(star => (
                  <span 
                    key={star} 
                    className={star <= stats.avg_rating ? 'star filled' : 'star'}
                  >
                    ★
                  </span>
                ))}
              </div>
            </div>
          </div>
          
          <div className="category-breakdown">
            <h3>Feedback by Category</h3>
            
            <div className="category-bars">
              {Object.entries(stats.categories).map(([category, count]) => (
                <div key={category} className="category-item">
                  <div className="category-label">{category}</div>
                  <div className="category-bar-container">
                    <div 
                      className="category-bar" 
                      style={{width: `${(count / stats.count * 100)}%`}}
                    ></div>
                  </div>
                  <div className="category-count">{count}</div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// Admin panel component
function AdminPanel({ 
  isAdmin, 
  adminKey, 
  setAdminKey, 
  onLogin, 
  feedbackList,
  onDelete
}) {
  const handleKeyChange = (e) => {
    setAdminKey(e.target.value);
  };
  
  const handleLogin = (e) => {
    e.preventDefault();
    onLogin();
  };
  
  // Format date for display
  const formatDate = (isoString) => {
    return new Date(isoString).toLocaleString();
  };
  
  return (
    <div className="admin-panel">
      <h2>Admin Panel</h2>
      
      {!isAdmin ? (
        <div className="admin-login">
          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label htmlFor="adminKey">Admin Key</label>
              <input
                type="password"
                id="adminKey"
                value={adminKey}
                onChange={handleKeyChange}
                placeholder="Enter your admin key"
              />
            </div>
            <button type="submit" className="submit-button">
              Access Admin Panel
            </button>
            <p className="note">
              Default admin key: "admin_secret_key" (In production, use a secure key)
            </p>
          </form>
        </div>
      ) : (
        <div className="feedback-management">
          <h3>Manage Feedback Entries ({feedbackList.length})</h3>
          
          {feedbackList.length === 0 ? (
            <p className="no-data">No feedback submissions found.</p>
          ) : (
            <div className="feedback-list">
              {feedbackList.map(feedback => (
                <div key={feedback.id} className="feedback-item">
                  <div className="feedback-header">
                    <div className="feedback-info">
                      <span className="feedback-name">{feedback.name}</span>
                      <span className="feedback-email">{feedback.email}</span>
                    </div>
                    <div className="feedback-meta">
                      <span className="feedback-date">{formatDate(feedback.timestamp)}</span>
                      <span className="feedback-category">{feedback.category}</span>
                      <span className="feedback-rating">
                        Rating: <strong>{feedback.rating}/5</strong>
                      </span>
                    </div>
                  </div>
                  
                  <div className="feedback-content">
                    {feedback.comment}
                  </div>
                  
                  <div className="feedback-actions">
                    <button 
                      className="delete-button" 
                      onClick={() => onDelete(feedback.id)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Mount the React application to the DOM
const rootElement = document.getElementById('root');
if (rootElement) {
  ReactDOM.createRoot(rootElement).render(<App />);
}

export default App;
