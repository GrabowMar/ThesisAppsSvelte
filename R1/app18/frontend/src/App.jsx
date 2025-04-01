import { useState, useEffect } from 'react'
import ReactDOM from 'react-dom/client'
import axios from 'axios'
import './App.css'

function App() {
  const [view, setView] = useState('list')
  const [pages, setPages] = useState([])
  const [search, setSearch] = useState('')
  const [currentPage, setCurrentPage] = useState(null)
  const [formData, setFormData] = useState({ title: '', content: '' })
  const [error, setError] = useState('')

  // Fetch pages
  useEffect(() => {
    const fetchPages = async () => {
      try {
        const res = await axios.get(`/api/pages${search ? `?query=${search}` : ''}`)
        setPages(res.data)
      } catch (err) {
        setError('Failed to load pages')
      }
    }
    fetchPages()
  }, [search, view])

  // Navigation
  const viewPage = (page) => {
    setCurrentPage(page)
    setView('view')
  }

  // Form handling
  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      if (view === 'edit') {
        await axios.put(`/api/pages/${currentPage.id}`, formData)
      } else {
        await axios.post('/api/pages', formData)
      }
      setView('list')
      setFormData({ title: '', content: '' })
    } catch (err) {
      setError('Operation failed. Please try again.')
    }
  }

  // Render current view
  const renderView = () => {
    switch(view) {
      case 'create':
      case 'edit':
        return (
          <form onSubmit={handleSubmit} className="editor">
            <input
              value={formData.title}
              onChange={e => setFormData({...formData, title: e.target.value})}
              placeholder="Page title"
              required
            />
            <textarea
              value={formData.content}
              onChange={e => setFormData({...formData, content: e.target.value})}
              placeholder="Page content (supports simple Markdown)"
              required
              rows={15}
            />
            <div className="button-group">
              <button type="submit">Save</button>
              <button type="button" onClick={() => setView('list')}>Cancel</button>
            </div>
          </form>
        )
        
      case 'view':
        return (
          <div className="page-view">
            <h1>{currentPage.title}</h1>
            <div 
              className="content"
              dangerouslySetInnerHTML={{ __html: currentPage.content 
                .replace(/#{3,}/g, '###')
                .replace(/#{2}/g, '##')
                .replace(/#{1}/g, '#')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/\n/g, '<br/>') }}
            />
            <div className="button-group">
              <button onClick={() => {
                setFormData({ title: currentPage.title, content: currentPage.content })
                setView('edit')
              }}>Edit</button>
              <button onClick={() => setView('history')}>History</button>
              <button onClick={() => setView('list')}>Back</button>
            </div>
          </div>
        )

      case 'history':
        return (
          <div className="history-view">
            <h2>Revision History</h2>
            {currentPage.versions.slice().reverse().map((v, i) => (
              <div key={i} className="version">
                <time>{new Date(v.timestamp).toLocaleString()}</time>
                <div className="content-preview">{v.content.slice(0, 100)}...</div>
              </div>
            ))}
            <button onClick={() => setView('view')}>Back</button>
          </div>
        )

      default:
        return (
          <>
            <div className="list-header">
              <input
                type="text"
                placeholder="Search pages..."
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
              <button onClick={() => {
                setFormData({ title: '', content: '' })
                setView('create')
              }}>New Page</button>
            </div>
            <div className="page-list">
              {pages.map(page => (
                <div key={page.id} className="page-item" onClick={() => viewPage(page)}>
                  <h3>{page.title}</h3>
                  <div className="content-preview">{page.content.slice(0, 80)}...</div>
                </div>
              ))}
            </div>
          </>
        )
    }
  }

  return (
    <main className="container">
      {error && <div className="error">{error}</div>}
      {renderView()}
    </main>
  )
}

// Mounting logic
ReactDOM.createRoot(document.getElementById('root')).render(<App />)
