import { useState, useEffect } from 'react'
import ReactDOM from 'react-dom/client'
import './App.css'

function App() {
  const [files, setFiles] = useState([])
  const [selectedFile, setSelectedFile] = useState(null)
  const [currentView, setCurrentView] = useState('upload')
  const [error, setError] = useState('')
  const [previewUrl, setPreviewUrl] = useState('')

  useEffect(() => {
    if (currentView === 'list') {
      fetchFiles()
    }
  }, [currentView])

  const fetchFiles = async () => {
    try {
      const response = await fetch('/api/files')
      if (!response.ok) throw new Error('Failed to fetch files')
      const data = await response.json()
      setFiles(data)
    } catch (err) {
      setError(err.message)
    }
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!selectedFile) return

    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Upload failed')
      }

      setSelectedFile(null)
      await fetchFiles()
      setCurrentView('list')
    } catch (err) {
      setError(err.message)
    }
  }

  const handlePreview = async (filename) => {
    const previewUrl = `/api/preview/${encodeURIComponent(filename)}`
    const extension = filename.split('.').pop().toLowerCase()
    
    if (['png', 'jpg', 'jpeg', 'gif'].includes(extension)) {
      window.open(previewUrl, '_blank')
    } else {
      const response = await fetch(previewUrl)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      window.open(url, '_blank')
    }
  }

  return (
    <main>
      <nav className="navbar">
        <button onClick={() => setCurrentView('upload')}>Upload</button>
        <button onClick={() => setCurrentView('list')}>List Files</button>
      </nav>

      <div className="container">
        {error && <div className="error">{error}</div>}

        {currentView === 'upload' ? (
          <form onSubmit={handleUpload} className="upload-form">
            <input
              type="file"
              onChange={(e) => setSelectedFile(e.target.files[0])}
            />
            <button type="submit">Upload File</button>
          </form>
        ) : (
          <div className="file-list">
            <h2>Uploaded Files</h2>
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Size (KB)</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {files.map((file) => (
                  <tr key={file.name}>
                    <td>{file.name}</td>
                    <td>{(file.size / 1024).toFixed(2)}</td>
                    <td>
                      <button onClick={() => handlePreview(file.name)}>
                        Preview
                      </button>
                      <a
                        href={`/api/download/${encodeURIComponent(file.name)}`}
                        download
                      >
                        <button>Download</button>
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  )
}

// Mounting logic
const root = ReactDOM.createRoot(document.getElementById('root'))
root.render(<App />)

export default App
