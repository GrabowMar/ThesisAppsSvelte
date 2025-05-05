import React, { useState, useEffect } from 'react'
import ReactDOM from 'react-dom/client'

const App = () => {
  const [notes, setNotes] = useState([])
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [category, setCategory] = useState('Uncategorized')
  const [searchQuery, setSearchQuery] = useState('')

  // Fetch all notes
  useEffect(() => {
    const fetchNotes = async () => {
      const response = await fetch('/api/notes')
      const data = await response.json()
      setNotes(data)
    }
    fetchNotes()
  }, [])

  // Create a note
  const handleCreateNote = async () => {
    const response = await fetch('/api/notes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, content, category }),
    })
    const newNote = await response.json()
    setNotes([...notes, newNote])
    setTitle('')
    setContent('')
    setCategory('Uncategorized')
  }

  // Search notes
  const handleSearch = async () => {
    const response = await fetch(`/api/notes/search?q=${searchQuery}`)
    const results = await response.json()
    setNotes(results)
  }

  return (
    <main>
      <h1>Notes Application</h1>
      <div>
        <input
          type="text"
          placeholder="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <textarea
          placeholder="Content"
          value={content}
          onChange={(e) => setContent(e.target.value)}
        />
        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="Uncategorized">Uncategorized</option>
          <option value="Work">Work</option>
          <option value="Personal">Personal</option>
        </select>
        <button onClick={handleCreateNote}>Create Note</button>
      </div>
      <div>
        <input
          type="text"
          placeholder="Search notes..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <button onClick={handleSearch}>Search</button>
      </div>
      <div>
        <h2>All Notes</h2>
        {notes.map((note) => (
          <div key={note.id}>
            <h3>{note.title}</h3>
            <p>{note.content}</p>
            <span>Category: {note.category}</span>
            <button onClick={() => handleArchiveNote(note.id)}>Archive</button>
          </div>
        ))}
      </div>
    </main>
  )
}

// Mounting Logic
const root = ReactDOM.createRoot(document.getElementById('root'))
root.render(<App />)
