import { useState, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import './App.css'

function App() {
  const [currentPage, setCurrentPage] = useState('login')
  const [user, setUser] = useState(null)
  const [entries, setEntries] = useState([])
  const [stats, setStats] = useState(null)
  const [resources, setResources] = useState([])
  const [reminders, setReminders] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  
  // Form states
  const [loginForm, setLoginForm] = useState({ email: '', password: '' })
  const [registerForm, setRegisterForm] = useState({ email: '', password: '', name: '' })
  const [entryForm, setEntryForm] = useState({ 
    mood: 'happy', 
    stress_level: 5, 
    journal_entry: '',
    activities: [] 
  })
  
  const availableActivities = [
    'exercise', 'meditation', 'reading', 'walking', 
    'socializing', 'creative work', 'sleep'
  ]
  
  // Fetch data on user change
  useEffect(() => {
    if (user) {
      fetchEntries()
      fetchStats()
      fetchResources()
      fetchReminders()
    }
  }, [user])
  
  // API calls
  const fetchWithAuth = async (url, options = {}) => {
    const token = localStorage.getItem('authToken')
    
    if (!options.headers) {
      options.headers = {}
    }
    
    if (token) {
      options.headers['Authorization'] = `Bearer ${token}`
    }
    
    try {
      const response = await fetch(`/api${url}`, {
        ...options,
        credentials: 'include'
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.message || 'Request failed')
      }
      
      return await response.json()
    } catch (err) {
      setError(err.message)
      throw err
    }
  }
  
  const fetchEntries = async () => {
    setIsLoading(true)
    try {
      const data = await fetchWithAuth('/entries')
      setEntries(data.entries)
    } catch (err) {
      console.error('Failed to fetch entries:', err)
    } finally {
      setIsLoading(false)
    }
  }
  
  const fetchStats = async () => {
    try {
      const data = await fetchWithAuth('/entries/stats')
      setStats(data)
    } catch (err) {
      console.error('Failed to fetch stats:', err)
    }
  }
  
  const fetchResources = async () => {
    try {
      const data = await fetchWithAuth('/resources')
      setResources(data.resources)
    } catch (err) {
      console.error('Failed to fetch resources:', err)
    }
  }
  
  const fetchReminders = async () => {
    try {
      const data = await fetchWithAuth('/reminders')
      setReminders(data.reminders)
    } catch (err) {
      console.error('Failed to fetch reminders:', err)
    }
  }
  
  // Auth handlers
  const handleLogin = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(loginForm)
      })
      
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.message || 'Login failed')
      }
      
      localStorage.setItem('authToken', data.token)
      setUser(data.user)
      setCurrentPage('dashboard')
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }
  
  const handleRegister = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    
    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(registerForm)
      })
      
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.message || 'Registration failed')
      }
      
      setCurrentPage('login')
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }
  
  const handleLogout = async () => {
    try {
      await fetchWithAuth('/logout', { method: 'POST' })
      localStorage.removeItem('authToken')
      setUser(null)
      setCurrentPage('login')
      setError(null)
    } catch (err) {
      setError(err.message)
    }
  }
  
  // Entry handlers
  const handleAddEntry = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    
    try {
      const response = await fetchWithAuth('/entries', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(entryForm)
      })
      
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.message || 'Failed to add entry')
      }
      
      setEntries([...entries, data.entry])
      setEntryForm({ 
        mood: 'happy', 
        stress_level: 5, 
        journal_entry: '',
        activities: [] 
      })
      
      // Refresh stats after adding new entry
      fetchStats()
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }
  
  const toggleActivity = (activity) => {
    if (entryForm.activities.includes(activity)) {
      setEntryForm({
        ...entryForm,
        activities: entryForm.activities.filter(a => a !== activity)
      })
    } else {
      setEntryForm({
        ...entryForm,
        activities: [...entryForm.activities, activity]
      })
    }
  }
  
  // Format date for display
  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric' 
    })
  }
  
  // Page components
  function LoginPage() {
    return (
      <div className="auth-container">
        <h2>Login</h2>
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label>Email</label>
            <input 
              type="email" 
              value={loginForm.email} 
              onChange={(e) => setLoginForm({...loginForm, email: e.target.value})}
              required 
            />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input 
              type="password" 
              value={loginForm.password} 
              onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
              required 
            />
          </div>
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
          <p>
            Don't have an account?{' '}
            <a href="#" onClick={() => setCurrentPage('register')}>Register</a>
          </p>
        </form>
      </div>
    )
  }
  
  function RegisterPage() {
    return (
      <div className="auth-container">
        <h2>Register</h2>
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleRegister}>
          <div className="form-group">
            <label>Name</label>
            <input 
              type="text" 
              value={registerForm.name} 
              onChange={(e) => setRegisterForm({...registerForm, name: e.target.value})}
              required 
            />
          </div>
          <div className="form-group">
            <label>Email</label>
            <input 
              type="email" 
              value={registerForm.email} 
              onChange={(e) => setRegisterForm({...registerForm, email: e.target.value})}
              required 
            />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input 
              type="password" 
              value={registerForm.password} 
              onChange={(e) => setRegisterForm({...registerForm, password: e.target.value})}
              required 
            />
          </div>
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Registering...' : 'Register'}
          </button>
          <p>
            Already have an account?{' '}
            <a href="#" onClick={() => setCurrentPage('login')}>Login</a>
          </p>
        </form>
      </div>
    )
  }
  
  function DashboardPage() {
    return (
      <div className="dashboard">
        <header>
          <h2>Welcome, {user.name || user.email}!</h2>
          <button onClick={handleLogout} className="logout-btn">Logout</button>
        </header>
        
        <nav className="app-nav">
          <button onClick={() => setCurrentPage('dashboard')} className={currentPage === 'dashboard' ? 'active' : ''}>
            Dashboard
          </button>
          <button onClick={() => setCurrentPage('add-entry')} className={currentPage === 'add-entry' ? 'active' : ''}>
            Add Entry
          </button>
          <button onClick={() => setCurrentPage('resources')} className={currentPage === 'resources' ? 'active' : ''}>
            Resources
          </button>
        </nav>
        
        {currentPage === 'dashboard' && (
          <div className="dashboard-content">
            <div className="stats-section">
              <h3>Your Overview</h3>
              {stats ? (
                <div className="stat-cards">
                  <div className="stat-card">
                    <h4>Average Mood</h4>
                    <div className="stat-value">{stats.mood_average.toFixed(1)}/10</div>
                  </div>
                  <div className="stat-card">
                    <h4>Average Stress</h4>
                    <div className="stat-value">{stats.stress_average.toFixed(1)}/10</div>
                  </div>
                  <div className="stat-card">
                    <h4>Top Activities</h4>
                    <ul>
                      {stats.top_activities.map((activity, i) => (
                        <li key={i}>{activity}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ) : (
                <p>Loading statistics...</p>
              )}
              
              <h3>Recent Entries</h3>
              <div className="entries-list">
                {entries.length > 0 ? (
                  entries.slice(0, 5).map((entry) => (
                    <div key={entry.id} className="entry-card">
                      <div className="entry-header">
                        <span className="entry-date">{formatDate(entry.date)}</span>
                        <span className={`mood-label mood-${entry.mood.toLowerCase()}`}>
                          {entry.mood}
                        </span>
                        <span className="stress-level">
                          Stress: {entry.stress_level}/10
                        </span>
                      </div>
                      {entry.journal_entry && (
                        <p className="journal-preview">
                          {entry.journal_entry.length > 100 
                            ? `${entry.journal_entry.substring(0, 100)}...` 
                            : entry.journal_entry}
                        </p>
                      )}
                    </div>
                  ))
                ) : (
                  <p>No entries yet. Add your first entry to see statistics.</p>
                )}
              </div>
            </div>
            
            {reminders.length > 0 && (
              <div className="reminders-section">
                <h3>Upcoming Reminders</h3>
                {reminders.map((reminder, i) => (
                  <div key={i} className="reminder-card">
                    <p>{reminder.message}</p>
                    <small>Scheduled for: {new Date(reminder.time).toLocaleString()}</small>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        
        {currentPage === 'add-entry' && (
          <div className="add-entry-form">
            <h3>New Wellness Entry</h3>
            {error && <div className="error-message">{error}</div>}
            <form onSubmit={handleAddEntry}>
              <div className="form-group">
                <label>How are you feeling today?</label>
                <select 
                  value={entryForm.mood} 
                  onChange={(e) => setEntryForm({...entryForm, mood: e.target.value})}
                >
                  <option value="happy">Happy</option>
                  <option value="sad">Sad</option>
                  <option value="anxious">Anxious</option>
                  <option value="calm">Calm</option>
                  <option value="energetic">Energetic</option>
                  <option value="tired">Tired</option>
                  <option value="angry">Angry</option>
                  <option value="neutral">Neutral</option>
                </select>
              </div>
              
              <div className="form-group">
                <label>Stress Level (1-10)</label>
                <input 
                  type="range" 
                  min="1" 
                  max="10" 
                  value={entryForm.stress_level} 
                  onChange={(e) => setEntryForm({...entryForm, stress_level: parseInt(e.target.value)})}
                />
                <div className="stress-level-display">{entryForm.stress_level}</div>
              </div>
              
              <div className="form-group">
                <label>Journal Entry (optional)</label>
                <textarea 
                  value={entryForm.journal_entry} 
                  onChange={(e) => setEntryForm({...entryForm, journal_entry: e.target.value})}
                  rows="4"
                />
              </div>
              
              <div className="form-group">
                <label>Activities (select all that apply)</label>
                <div className="activities-grid">
                  {availableActivities.map((activity) => (
                    <button 
                      key={activity}
                      type="button"
                      className={`activity-btn ${entryForm.activities.includes(activity) ? 'selected' : ''}`}
                      onClick={() => toggleActivity(activity)}
                    >
                      {activity}
                    </button>
                  ))}
                </div>
              </div>
              
              <button type="submit" disabled={isLoading}>
                {isLoading ? 'Saving...' : 'Save Entry'}
              </button>
              <button 
                type="button" 
                onClick={() => setCurrentPage('dashboard')}
                className="cancel-btn"
              >
                Cancel
              </button>
            </form>
          </div>
        )}
        
        {currentPage === 'resources' && (
          <div className="resources-section">
            <h3>Professional Resources</h3>
            <div className="resource-grid">
              {resources.map((resource) => (
                <div key={resource.id} className="resource-card">
                  <h4>{resource.name}</h4>
                  <p>{resource.description}</p>
                  <div className="resource-contacts">
                    <div><strong>Phone:</strong> {resource.phone}</div>
                    <div><strong>Website:</strong> <a href={resource.website} target="_blank" rel="noopener noreferrer">{resource.website}</a></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }
  
  // Main render
  return (
    <div className="app-container">
      {!user ? (
        currentPage === 'login' ? <LoginPage /> : <RegisterPage />
      ) : (
        <DashboardPage />
      )}
    </div>
  )
}

// Mount the app
const root = createRoot(document.getElementById('root'))
root.render(<App />)
