// 1. Imports
import React, { useState, useEffect } from 'react'
import ReactDOM from 'react-dom/client'
import './App.css'

const App = () => {
  // 2. State Management
  const [page, setPage] = useState('home')
  const [polls, setPolls] = useState({})
  const [currentPoll, setCurrentPoll] = useState(null)
  const [formData, setFormData] = useState({
    title: '',
    options: '',
    duration: ''
  })

  const backendUrl = 'http://localhost:5261/api/polls'

  // 3. Fetch Poll Data
  const fetchPoll = async (pollId) => {
    try {
      const res = await fetch(`${backendUrl}/${pollId}`)
      const poll = await res.json()
      setCurrentPoll(poll)
    } catch (error) {
      console.error('Error fetching poll:', error)
    }
  }

  // 4. Event Handlers
  const handleCreatePoll = async () => {
    const optionsArray = formData.options.split(',').map(opt => opt.trim())
    const payload = { title: formData.title, options: optionsArray, duration_minutes: parseInt(formData.duration) }

    try {
      const res = await fetch(backendUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      const data = await res.json()
      if (data.poll_id) {
        setPolls({ ...polls, [data.poll_id]: payload.title })
        setPage('home')
      }
    } catch (error) {
      console.error('Error creating poll:', error)
    }
  }

  const handleVote = async (pollId, option) => {
    try {
      await fetch(`${backendUrl}/${pollId}/vote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ option })
      })
      fetchPoll(pollId)
    } catch (error) {
      console.error('Error voting:', error)
    }
  }

  // 5. UI Components
  return (
    <div className="App">
      {page === 'home' && (
        <div>
          <h1>Polling App</h1>
          <button onClick={() => setPage('create')}>Create New Poll</button>
          <h2>Existing Polls</h2>
          {Object.entries(polls).map(([id, title]) => (
            <div key={id}>
              <h3>{title}</h3>
              <button onClick={() => { fetchPoll(id); setPage('view') }}>View Poll</button>
            </div>
          ))}
        </div>
      )}

      {page === 'create' && (
        <div>
          <h1>Create Poll</h1>
          <input type="text" placeholder="Title" onChange={(e) => setFormData({ ...formData, title: e.target.value })} />
          <input type="text" placeholder="Options (comma-separated)" onChange={(e) => setFormData({ ...formData, options: e.target.value })} />
          <input type="number" placeholder="Duration (minutes)" onChange={(e) => setFormData({ ...formData, duration: e.target.value })} />
          <button onClick={handleCreatePoll}>Create Poll</button>
        </div>
      )}

      {page === 'view' && currentPoll && (
        <div>
          <h1>{currentPoll.title}</h1>
          <p>Status: {currentPoll.status}</p>
          {currentPoll.status === 'active' ? (
            Object.keys(currentPoll.options).map(option => (
              <button key={option} onClick={() => handleVote(currentPoll.poll_id, option)}>{option}</button>
            ))
          ) : (
            <div>
              <h2>Results</h2>
              {Object.entries(currentPoll.options).map(([option, votes]) => (
                <p key={option}>{option}: {votes}</p>
              ))}
            </div>
          )}
          <button onClick={() => setPage('home')}>Back to Home</button>
        </div>
      )}
    </div>
  )
}

// Mount application
const root = ReactDOM.createRoot(document.getElementById('root'))
root.render(<App />)
