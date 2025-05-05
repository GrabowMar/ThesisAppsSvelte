import React, { useState, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import './App.css'

const App = () => {
  // State for tracking data
  const [trackingData, setTrackingData] = useState({
    electricity: 0,
    car_miles: 0,
    public_transport_miles: 0,
    meals: 0,
    waste: 0,
    notes: ''
  })
  
  // User state
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  
  // UI state
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  
  // Data state
  const [userTracks, setUserTracks] = useState([])
  const [challenges, setChallenges] = useState([])
  const [tips, setTips] = useState([])
  const [analytics, setAnalytics] = useState(null)
  
  // Form states
  const [loginData, setLoginData] = useState({ email: '', password: '' })
  const [registerData, setRegisterData] = useState({ email: '', password: '', name: '' })
  const [challengeData, setChallengeData] = useState({ title: '', description: '', category: 'general' })
  
  // Fetch current user on component mount
  useEffect(() => {
    const fetchCurrentUser = async () => {
      try {
        const response = await fetch('/api/current_user', { credentials: 'include' })
        if (response.ok) {
          const data = await response.json()
          setUser(data)
          fetchUserData(data.id)
        }
      } catch (err) {
        console.error('Error fetching user:', err)
      } finally {
        setLoading(false)
      }
    }
    
    fetchCurrentUser()
    fetchChallenges()
    fetchTips()
  }, [])
  
  const fetchUserData = async (userId) => {
    try {
      const [tracksRes, analyticsRes] = await Promise.all([
        fetch('/api/tracks', { credentials: 'include' }),
        fetch('/api/analytics', { credentials: 'include' })
      ])
      
      if (tracksRes.ok) {
        const tracksData = await tracksRes.json()
        setUserTracks(tracksData.tracks)
      }
      
      if (analyticsRes.ok) {
        const analyticsData = await analyticsRes.json()
        setAnalytics(analyticsData)
      }
    } catch (err) {
      console.error('Error fetching user data:', err)
    }
  }
  
  const fetchChallenges = async () => {
    try {
      const response = await fetch('/api/challenges')
      if (response.ok) {
        const data = await response.json()
        setChallenges(data.challenges)
      }
    } catch (err) {
      console.error('Error fetching challenges:', err)
    }
  }
  
  const fetchTips = async () => {
    try {
      const response = await fetch('/api/tips')
      if (response.ok) {
        const data = await response.json()
        setTips(data.tips)
      }
    } catch (err) {
      console.error('Error fetching tips:', err)
    }
  }
  
  // Auth handlers
  const handleLogin = async (e) => {
    e.preventDefault()
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginData),
        credentials: 'include'
      })
      
      const data = await response.json()
      if (response.ok) {
        setUser(data.user)
        setSuccess('Logged in successfully!')
        setError(null)
        setCurrentPage('dashboard')
        fetchUserData(data.user.id)
      } else {
        throw new Error(data.error || 'Login failed')
      }
    } catch (err) {
      setError(err.message)
      setSuccess(null)
    }
  }
  
  const handleRegister = async (e) => {
    e.preventDefault()
    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(registerData),
        credentials: 'include'
      })
      
      const data = await response.json()
      if (response.ok) {
        setSuccess('Account created successfully! You are now logged in.')
        setError(null)
        // Auto-login after registration
        const loginResponse = await fetch('/api/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: registerData.email,
            password: registerData.password
          }),
          credentials: 'include'
        })
        
        if (loginResponse.ok) {
          const loginData = await loginResponse.json()
          setUser(loginData.user)
          setCurrentPage('dashboard')
        }
      } else {
        throw new Error(data.error || 'Registration failed')
      }
    } catch (err) {
      setError(err.message)
      setSuccess(null)
    }
  }
  
  const handleLogout = async () => {
    try {
      const response = await fetch('/api/logout', {
        method: 'POST',
        credentials: 'include'
      })
      
      if (response.ok) {
        setUser(null)
        setUserTracks([])
        setAnalytics(null)
        setSuccess('Logged out successfully!')
        setError(null)
        setCurrentPage('login')
      }
    } catch (err) {
      setError('Error during logout')
    }
  }
  
  // Tracking handlers
  const handleTrackingChange = (e) => {
    const { name, value } = e.target
    setTrackingData(prev => ({
      ...prev,
      [name]: value !== '' ? parseFloat(value) || 0 : 0
    }))
  }
  
  const handleTrackSubmit = async (e) => {
    e.preventDefault()
    try {
      const response = await fetch('/api/track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(trackingData),
        credentials: 'include'
      })
      
      const data = await response.json()
      if (response.ok) {
        setSuccess(`Tracked successfully! Your carbon footprint for this entry: ${data.carbon_footprint} kg CO2`)
        setError(null)
        setTrackingData({
          electricity: 0,
          car_miles: 0,
          public_transport_miles: 0,
          meals: 0,
          waste: 0,
          notes: ''
        })
        fetchUserData(user.id)
      } else {
        throw new Error(data.error || 'Tracking failed')
      }
    } catch (err) {
      setError(err.message)
      setSuccess(null)
    }
  }
  
  // Challenge handlers
  const handleChallengeChange = (e) => {
    const { name, value } = e.target
    setChallengeData(prev => ({
      ...prev,
      [name]: value
    }))
  }
  
  const handleChallengeSubmit = async (e) => {
    e.preventDefault()
    try {
      const response = await fetch('/api/challenges/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(challengeData),
        credentials: 'include'
      })
      
      const data = await response.json()
      if (response.ok) {
        setSuccess('Challenge created successfully!')
        setError(null)
        setChallengeData({ title: '', description: '', category: 'general' })
        fetchChallenges()
      } else {
        throw new Error(data.error || 'Challenge creation failed')
      }
    } catch (err) {
      setError(err.message)
      setSuccess(null)
    }
  }
  
  // Render helpers
  const renderLogin = () => (
    <div className="form-container">
      <h2>Login</h2>
      <form onSubmit={handleLogin}>
        <input
          type="email"
          name="email"
          placeholder="Email"
          value={loginData.email}
          onChange={(e) => setLoginData({...loginData, email: e.target.value})}
          required
        />
        <input
          type="password"
          name="password"
          placeholder="Password"
          value={loginData.password}
          onChange={(e) => setLoginData({...loginData, password: e.target.value})}
          required
        />
        <button type="submit">Login</button>
      </form>
      <p>Don't have an account? <button onClick={() => setCurrentPage('register')}>Register</button></p>
    </div>
  )
  
  const renderRegister = () => (
    <div className="form-container">
      <h2>Register</h2>
      <form onSubmit={handleRegister}>
        <input
          type="text"
          name="name"
          placeholder="Name"
          value={registerData.name}
          onChange={(e) => setRegisterData({...registerData, name: e.target.value})}
          required
        />
        <input
          type="email"
          name="email"
          placeholder="Email"
          value={registerData.email}
          onChange={(e) => setRegisterData({...registerData, email: e.target.value})}
          required
        />
        <input
          type="password"
          name="password"
          placeholder="Password"
          value={registerData.password}
          onChange={(e) => setRegisterData({...registerData, password: e.target.value})}
          required
        />
        <button type="submit">Register</button>
      </form>
      <p>Already have an account? <button onClick={() => setCurrentPage('login')}>Login</button></p>
    </div>
  )
  
  const renderDashboard = () => (
    <div>
      <div className="stats-container">
        <div className="stat-card">
          <h3>Your Total Footprint</h3>
          <p>{analytics?.total_footprint || '0'} kg CO2</p>
        </div>
        <div className="stat-card">
          <h3>Community Average</h3>
          <p>{analytics?.community_average ? `${analytics.community_average.toFixed(2)} kg CO2` : 'No data'}</p>
        </div>
        <div className="stat-card">
          <h3>Tracking Entries</h3>
          <p>{analytics?.track_count || '0'}</p>
        </div>
      </div>
      
      <div className="track-form">
        <h2>Track Your Impact</h2>
        <form onSubmit={handleTrackSubmit}>
          <div className="form-group">
            <label>Electricity Used (kWh)</label>
            <input
              type="number"
              name="electricity"
              value={trackingData.electricity}
              onChange={handleTrackingChange}
            />
          </div>
          <div className="form-group">
            <label>Car Miles Traveled</label>
            <input
              type="number"
              name="car_miles"
              value={trackingData.car_miles}
              onChange={handleTrackingChange}
            />
          </div>
          <div className="form-group">
            <label>Public Transport Miles</label>
            <input
              type="number"
              name="public_transport_miles"
              value={trackingData.public_transport_miles}
              onChange={handleTrackingChange}
            />
          </div>
          <div className="form-group">
            <label>Meals Consumed</label>
            <input
              type="number"
              name="meals"
              value={trackingData.meals}
              onChange={handleTrackingChange}
            />
          </div>
          <div className="form-group">
            <label>Waste Produced (kg)</label>
            <input
              type="number"
              name="waste"
              value={trackingData.waste}
              onChange={handleTrackingChange}
            />
          </div>
          <div className="form-group">
            <label>Notes</label>
            <textarea
              name="notes"
              value={trackingData.notes}
              onChange={handleTrackingChange}
            />
          </div>
          <button type="submit">Submit</button>
        </form>
      </div>
    </div>
  )
  
  const renderTrackingHistory = () => (
    <div>
      <h2>Your Tracking History</h2>
      {userTracks.length > 0 ? (
        <div className="tracking-history">
          {userTracks.map((track, index) => (
            <div key={index} className="track-card">
              <p><strong>Date:</strong> {new Date(track.date).toLocaleString()}</p>
              <p><strong>Footprint:</strong> {track.carbon_footprint} kg CO2</p>
              <p><strong>Notes:</strong> {track.notes}</p>
            </div>
          ))}
        </div>
      ) : (
        <p>No tracking data yet. Start by adding your first tracking entry.</p>
      )}
    </div>
  )
  
  const renderChallenges = () => (
    <div>
      <h2>Sustainability Challenges</h2>
      <button onClick={() => setCurrentPage('create-challenge')}>Create New Challenge</button>
      
      <div className="challenges-grid">
        {challenges.map((challenge, index) => (
          <div key={index} className="challenge-card">
            <h3>{challenge.title}</h3>
            <p>{challenge.description}</p>
            <p><strong>Category:</strong> {challenge.category}</p>
            <button>Join Challenge</button>
          </div>
        ))}
      </div>
    </div>
  )
  
  const renderCreateChallenge = () => (
    <div>
      <h2>Create New Challenge</h2>
      <form onSubmit={handleChallengeSubmit}>
        <input
          type="text"
          name="title"
          placeholder="Challenge Title"
          value={challengeData.title}
          onChange={handleChallengeChange}
          required
        />
        <textarea
          name="description"
          placeholder="Description"
          value={challengeData.description}
          onChange={handleChallengeChange}
          required
        />
        <select
          name="category"
          value={challengeData.category}
          onChange={handleChallengeChange}
          required
        >
          <option value="general">General</option>
          <option value="energy">Energy</option>
          <option value="transport">Transport</option>
          <option value="food">Food</option>
          <option value="waste">Waste</option>
          <option value="water">Water</option>
        </select>
        <div className="checkbox-group">
          <input
            type="checkbox"
            id="isCommunity"
            name="is_community"
            checked={challengeData.is_community}
            onChange={() => setChallengeData(prev => ({
              ...prev,
              is_community: !prev.is_community
            }))}
          />
          <label htmlFor="isCommunity">Make this a community challenge</label>
        </div>
        <button type="submit">Create Challenge</button>
        <button type="button" onClick={() => setCurrentPage('challenges')}>Cancel</button>
      </form>
    </div>
  )
  
  const renderTips = () => (
    <div>
      <h2>Eco-Friendly Tips & Recommendations</h2>
      <div className="tips-grid">
        {tips.map((tip, index) => (
          <div key={index} className="tip-card">
            <h3>{tip.title}</h3>
            <p><strong>Category:</strong> {tip.category}</p>
          </div>
        ))}
      </div>
    </div>
  )
  
  const renderAnalytics = () => (
    <div>
      <h2>Your Sustainability Analytics</h2>
      {analytics ? (
        <div>
          <h3>Monthly Averages</h3>
          <div className="chart-container">
            {Object.entries(analytics.monthly_averages).map(([month, avg]) => (
              <div key={month} className="chart-bar">
                <div className="bar-label">{month}</div>
                <div 
                  className="bar" 
                  style={{ width: `${(avg / Math.max(...Object.values(analytics.monthly_averages))) * 100}%` }}
                >
                  {avg.toFixed(1)} kg
                </div>
              </div>
            ))}
          </div>
          
          <h3>Comparison</h3>
          {analytics.community_average && (
            <div className="comparison">
              <p>Your average: {analytics.total_footprint / Math.max(1, analytics.track_count)} kg CO2 per entry</p>
              <p>Community average: {analytics.community_average.toFixed(2)} kg CO2 per entry</p>
            </div>
          )}
        </div>
      ) : (
        <p>No analytics data yet. Start tracking to see your progress.</p>
      )}
    </div>
  )
  
  if (loading) {
    return <div className="loading">Loading...</div>
  }
  
  return (
    <div className="app">
      <header>
        <h1>Environmental Impact Tracker</h1>
        {user && (
          <div className="user-info">
            <span>Welcome, {user.name || user.email}</span>
            <button onClick={handleLogout}>Logout</button>
          </div>
        )}
      </header>
      
      {error && <div className="alert error">{error}</div>}
      {success && <div className="alert success">{success}</div>}
      
      {user ? (
        <>
          <nav>
            <button onClick={() => setCurrentPage('dashboard')}>Dashboard</button>
            <button onClick={() => setCurrentPage('tracking')}>Tracking</button>
            <button onClick={() => setCurrentPage('analytics')}>Analytics</button>
            <button onClick={() => setCurrentPage('challenges')}>Challenges</button>
            <button onClick={() => setCurrentPage('tips')}>Tips</button>
          </nav>
          
          <main>
            {currentPage === 'dashboard' && renderDashboard()}
            {currentPage === 'tracking' && renderTrackingHistory()}
            {currentPage === 'analytics' && renderAnalytics()}
            {currentPage === 'challenges' && renderChallenges()}
            {currentPage === 'create-challenge' && renderCreateChallenge()}
            {currentPage === 'tips' && renderTips()}
          </main>
        </>
      ) : (
        <main>
          {currentPage === 'login' && renderLogin()}
          {currentPage === 'register' && renderRegister()}
          {!currentPage && <button onClick={() => setCurrentPage('login')}>Login</button>}
        </main>
      )}
      
      <footer>
        <p>&copy; {new Date().getFullYear()} Environmental Impact Tracker</p>
      </footer>
    </div>
  )
}

// Mount the app
const container = document.getElementById('root')
const root = createRoot(container)
root.render(<App />)
